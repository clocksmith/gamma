#!/usr/bin/env node
// Real-Chromium + Stateful SQLite 2x2 Mechanism Ablation & Live-Lookahead Benchmark
// for Gammatron x Fawn (Rung 4 & Rung 5 mechanism proof, $0 model spend).
//
// Scope & honesty boundary:
//   - Exercises real headless Chromium (`playwright-core`) executing `branchExpression()`
//     from `src/client/branch-verifier.js` and `evaluateLiveLookahead()` from
//     `src/client/live-lookahead.js` against a real `node:http` + `node:sqlite`
//     two-application (`work-packages`, `purchase-orders`) `v1 -> v2` server.
//   - Evaluates n = 100 independent invalid cases (50 Row A server-only conflict traps +
//     50 Row B client-side v1->v2 payload/validation/dirty-field traps; <= 50 per app)
//     and V = 100 distinct valid cases (50 clean v1 reuse + 50 v2 UI/serializer drift
//     repair cases holding unsaved in-memory JS closure state).
//   - On macOS, isolated branch previews execute in network-blocked in-page contexts
//     emitting Fawn's exact `Page.fawnBranchStatus` wire format while proving zero
//     server requests escape during preview (`serverPreviewMutations === 0`); native
//     Linux copy-on-write renderer `fork()` remains separately qualified on Fawn's host.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { dirname, join, resolve } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import { branchExpression, verifyBranches } from '../../src/client/branch-verifier.js';
import { evaluateLiveLookahead, extractMinimalReadRoles } from '../../src/client/live-lookahead.js';
import { checkRepairBoundary, collectObservedFacts, learnRepairBoundary } from '../../src/client/repair-boundary.js';

const HERE = dirname(fileURLToPath(import.meta.url));

function findBrowserExecutable() {
  if (process.env.BRANCH_VERIFIER_BROWSER && existsSync(process.env.BRANCH_VERIFIER_BROWSER)) {
    return process.env.BRANCH_VERIFIER_BROWSER;
  }
  const candidates = [
    `${process.env.HOME}/Library/Caches/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-mac-arm64/chrome-headless-shell`,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
  ];
  return candidates.find(p => existsSync(p)) ?? null;
}

const clopperPearson95Upper = (wrong, n) => {
  if (n <= 0 || wrong >= n) return 1;
  if (wrong <= 0) return 1 - (0.05 ** (1 / n));
  const logChoose = (nn, kk) => {
    let s = 0;
    for (let i = 1; i <= kk; i += 1) s += Math.log(nn - kk + i) - Math.log(i);
    return s;
  };
  const cdf = p => {
    let total = 0;
    for (let i = 0; i <= wrong; i += 1) {
      total += Math.exp(logChoose(n, i) + i * Math.log(p) + (n - i) * Math.log1p(-p));
    }
    return total;
  };
  let lo = 0;
  let hi = 1;
  for (let it = 0; it < 100; it += 1) {
    const mid = 0.5 * (lo + hi);
    if (cdf(mid) > 0.05) lo = mid;
    else hi = mid;
  }
  return hi;
};

const opBind = label => `opbind-v1:${createHash('sha256').update(label).digest('hex')}`;

/** Creates the two-app SQLite database + HTTP server. */
function createTwoAppServer() {
  const db = new DatabaseSync(':memory:');
  db.exec(`
    CREATE TABLE approvals (
      id INTEGER PRIMARY KEY,
      project_code INTEGER NOT NULL,
      status_code INTEGER NOT NULL,
      approved_hours INTEGER NOT NULL,
      readable INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE work_packages (
      id INTEGER PRIMARY KEY,
      approval_id INTEGER NOT NULL,
      project_code INTEGER NOT NULL,
      estimated_hours INTEGER NOT NULL,
      surcharge_hours INTEGER NOT NULL DEFAULT 0,
      archived INTEGER NOT NULL DEFAULT 0,
      expected_closure_nonce TEXT NOT NULL,
      committed_nonce TEXT,
      lock_version INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE quotations (
      name TEXT PRIMARY KEY,
      company_code INTEGER NOT NULL,
      docstatus INTEGER NOT NULL,
      total_qty INTEGER NOT NULL,
      readable INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE purchase_orders (
      name TEXT PRIMARY KEY,
      quotation_name TEXT NOT NULL,
      company_code INTEGER NOT NULL,
      docstatus INTEGER NOT NULL,
      total_qty INTEGER NOT NULL,
      terms TEXT NOT NULL DEFAULT '',
      surcharge_fee INTEGER NOT NULL DEFAULT 0,
      archived INTEGER NOT NULL DEFAULT 0,
      expected_closure_nonce TEXT NOT NULL,
      committed_nonce TEXT,
      lock_version INTEGER NOT NULL DEFAULT 1
    );
  `);

  let previewPhaseActive = false;
  let serverPreviewMutations = 0;

  const renderPageHtml = ({ app, id, targetVal, variant }) => {
    const endpoint = app === 'work-packages' ? `/api/wp/${id}/save` : `/api/po/${id}/confirm`;
    const archiveEndpoint = app === 'work-packages' ? `/api/wp/${id}/archive` : `/api/po/${id}/archive`;
    const fieldName = app === 'work-packages' ? 'hours' : 'reference';

    // Closure holds an unsaved in-memory draft checksum initialized only when `initLiveEdit(nonce)` runs;
    // a stock tab reload loses this closure value and reverts to 'UNINITIALIZED_AFTER_RELOAD'.
    return `<!doctype html>
<html><head><meta charset="utf-8"><title>${app}:${id}</title></head>
<body>
  <form id="edit-form" onsubmit="return false;">
    <input id="main-field" name="${fieldName}" value="${String(targetVal)}">
    <input id="extra-surcharge" name="surcharge" value="0">
    <input type="hidden" id="csrf-token" name="csrf" value="tok-1">
    <output id="status-box" role="status">Ready</output>
  </form>
  <script>
    (() => {
      let closureNonce = 'UNINITIALIZED_AFTER_RELOAD';
      window.__setLiveUnsavedClosure = n => { closureNonce = n; };
      const variant = ${JSON.stringify(variant)};
      const endpoint = ${JSON.stringify(endpoint)};
      const archiveEndpoint = ${JSON.stringify(archiveEndpoint)};
      const fieldName = ${JSON.stringify(fieldName)};
      const targetVal = ${JSON.stringify(targetVal)};

      const sendPayload = (url, method, payload) => fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      // Candidate 1 (stored v1 reuse action)
      window.runStoredV1 = () => {
        const el = document.getElementById('main-field');
        el.value = String(targetVal);
        if (variant === 'v1-clean') {
          return sendPayload(endpoint, 'POST', { [fieldName]: targetVal, nonce: closureNonce });
        }
        if (variant === 'v2-ui-renamed') {
          // v1 button/handler became a no-op in v2 UI!
          return Promise.resolve('noop');
        }
        if (variant === 'v2-legacy-serializer') {
          // v1 path injects deprecated surcharge field on v2, whereas v2-repair sends clean payload
          return sendPayload(endpoint, 'POST', { [fieldName]: targetVal, nonce: closureNonce, surcharge: 99 });
        }
        if (variant === 'trap-hidden-surcharge') {
          return sendPayload(endpoint, 'POST', { [fieldName]: targetVal, nonce: closureNonce, surcharge: 250 });
        }
        if (variant === 'trap-wrong-method') {
          return sendPayload(endpoint, 'PUT', { [fieldName]: targetVal, nonce: closureNonce });
        }
        if (variant === 'trap-wrong-endpoint') {
          return sendPayload(archiveEndpoint, 'POST', { [fieldName]: targetVal, nonce: closureNonce });
        }
        if (variant === 'trap-client-alert') {
          const alertEl = document.createElement('div');
          alertEl.setAttribute('role', 'alert');
          alertEl.textContent = 'Client validation blocked unverified amount';
          document.body.appendChild(alertEl);
          return sendPayload(endpoint, 'POST', { [fieldName]: targetVal, nonce: closureNonce, surcharge: 50 });
        }
        if (variant === 'trap-dirty-field') {
          document.getElementById('extra-surcharge').value = '777';
          return sendPayload(endpoint, 'POST', { [fieldName]: targetVal, nonce: closureNonce, surcharge: 777 });
        }
        return Promise.resolve('unknown');
      };

      // Candidate 2 (ranked top-1 repair action for v2 UI / serializer drift)
      window.runRepairV2 = () => {
        const el = document.getElementById('main-field');
        el.value = String(targetVal);
        if (variant === 'v2-ui-renamed' || variant === 'v2-legacy-serializer' || variant === 'v1-clean') {
          return sendPayload(endpoint, 'POST', { [fieldName]: targetVal, nonce: closureNonce });
        }
        // On genuine broken client traps (Row B), v2 repair also hits the broken page validation/trap
        return window.runStoredV1();
      };

      // Candidates 3..8 (additional candidate actions in the 8-branch search pool)
      for (let k = 3; k <= 8; k++) {
        window['runAltCandidate' + k] = () => Promise.resolve('noop-' + k);
      }
    })();
  </script>
</body></html>`;
  };

  const server = createServer(async (req, res) => {
    let raw = '';
    for await (const chunk of req) raw += chunk;
    const body = raw ? JSON.parse(raw) : {};
    const send = (code, obj) => {
      res.statusCode = code;
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify(obj));
    };
    const url = new URL(req.url, 'http://127.0.0.1');

    if (req.method === 'GET' && url.pathname === '/page') {
      res.statusCode = 200;
      res.setHeader('Content-Type', 'text/html; charset=utf-8');
      res.end(renderPageHtml({
        app: url.searchParams.get('app'),
        id: url.searchParams.get('id'),
        targetVal: url.searchParams.get('app') === 'work-packages'
          ? Number(url.searchParams.get('val'))
          : url.searchParams.get('val'),
        variant: url.searchParams.get('variant'),
      }));
      return;
    }

    // Read endpoints (authoritative server facts + 3 unreferenced noise endpoints per app)
    const wpRead = url.pathname.match(/^\/api\/wp\/(\d+)\/(record|approval|audit_log|team_stats|history)$/);
    if (req.method === 'GET' && wpRead) {
      const id = Number(wpRead[1]);
      const role = wpRead[2];
      const wp = db.prepare('SELECT * FROM work_packages WHERE id = ?').get(id);
      if (!wp) return send(404, { error: 'not-found' });
      if (role === 'record') {
        return send(200, { projectCode: wp.project_code, lockVersion: wp.lock_version });
      }
      if (role === 'approval') {
        const ap = db.prepare('SELECT * FROM approvals WHERE id = ?').get(wp.approval_id);
        if (!ap?.readable) return send(403, { error: 'restricted-project' });
        return send(200, {
          projectCode: ap.project_code,
          statusCode: ap.status_code,
          estimatedTime: `PT${ap.approved_hours}H`,
        });
      }
      // Noise roles: legitimate scalar endpoints not needed by minimal guard
      return send(200, { entryCount: (id * 7 + role.length) % 19 + 1, metricCode: 100 });
    }

    const poRead = url.pathname.match(/^\/api\/po\/([^/]+)\/(order|quotation|audit_log|vendor_stats|history)$/);
    if (req.method === 'GET' && poRead) {
      const name = decodeURIComponent(poRead[1]);
      const role = poRead[2];
      const po = db.prepare('SELECT * FROM purchase_orders WHERE name = ?').get(name);
      if (!po) return send(404, { error: 'not-found' });
      if (role === 'order') {
        return send(200, { companyCode: po.company_code, docstatus: po.docstatus, totalQty: po.total_qty });
      }
      if (role === 'quotation') {
        const sq = db.prepare('SELECT * FROM quotations WHERE name = ?').get(po.quotation_name);
        if (!sq?.readable) return send(403, { error: 'restricted-quotation' });
        return send(200, { companyCode: sq.company_code, docstatus: sq.docstatus, totalQty: sq.total_qty });
      }
      return send(200, { entryCount: (name.length * 5 + role.length) % 17 + 1, metricCode: 200 });
    }

    // Mutation endpoints (server accepts mutations just like OpenProject & ERPNext!)
    if (previewPhaseActive) serverPreviewMutations += 1;

    const wpWrite = url.pathname.match(/^\/api\/wp\/(\d+)\/(save|archive)$/);
    if (wpWrite) {
      const id = Number(wpWrite[1]);
      const op = wpWrite[2];
      if (op === 'archive') {
        db.prepare('UPDATE work_packages SET archived = 1, lock_version = lock_version + 1 WHERE id = ?').run(id);
        return send(200, { ok: true });
      }
      db.prepare(`
        UPDATE work_packages
        SET estimated_hours = ?, surcharge_hours = ?, committed_nonce = ?, lock_version = lock_version + 1
        WHERE id = ?
      `).run(Number(body.hours ?? 0), Number(body.surcharge ?? 0), String(body.nonce ?? ''), id);
      return send(200, { ok: true });
    }

    const poWrite = url.pathname.match(/^\/api\/po\/([^/]+)\/(confirm|archive)$/);
    if (poWrite) {
      const name = decodeURIComponent(poWrite[1]);
      const op = poWrite[2];
      if (op === 'archive') {
        db.prepare('UPDATE purchase_orders SET archived = 1, lock_version = lock_version + 1 WHERE name = ?').run(name);
        return send(200, { ok: true });
      }
      db.prepare(`
        UPDATE purchase_orders
        SET terms = ?, surcharge_fee = ?, committed_nonce = ?, lock_version = lock_version + 1
        WHERE name = ?
      `).run(String(body.reference ?? ''), Number(body.surcharge ?? 0), String(body.nonce ?? ''), name);
      return send(200, { ok: true });
    }

    send(404, { error: 'unknown' });
  });

  return {
    db,
    server,
    setPreviewPhase(flag) { previewPhaseActive = flag; },
    getPreviewMutations: () => serverPreviewMutations,
  };
}

/**
 * Generates:
 *   - Equal training contrast examples (k = 6 per app: 2 valid + 4 invalid)
 *   - 100 unseen independent invalid cases (50 Row A server-conflict + 50 Row B client-drift)
 *   - 100 unseen valid cases (50 clean v1 reuse + 50 v2 UI/serializer drift repair)
 */
function buildBenchmarkDataset(db) {
  let wpId = 1;
  let apId = 1;
  let poSeq = 1;

  const insertWp = ({ apProject, apStatus, apHours, readable = 1, wpProject, targetHours, variant, label, kind, failureId = null, toctouCancel = false }) => {
    const aid = apId++;
    const wid = wpId++;
    const nonce = `live-wp-nonce-${wid}`;
    db.prepare('INSERT INTO approvals (id, project_code, status_code, approved_hours, readable) VALUES (?, ?, ?, ?, ?)')
      .run(aid, apProject, apStatus, apHours, readable);
    db.prepare('INSERT INTO work_packages (id, approval_id, project_code, estimated_hours, expected_closure_nonce) VALUES (?, ?, ?, ?, ?)')
      .run(wid, aid, wpProject, 4, nonce);
    return {
      caseId: `wp-${wid}`,
      app: 'work-packages',
      recordKey: wid,
      approvalKey: aid,
      targetVal: targetHours,
      nonce,
      variant,
      valid: label === 'valid',
      kind,
      failureId,
      toctouCancel,
    };
  };

  const insertPo = ({ sqCompany, sqStatus, sqQty, readable = 1, poCompany, poQty, ref, variant, label, kind, failureId = null, toctouCancel = false }) => {
    const seq = poSeq++;
    const sqName = `SQ-${seq}`;
    const poName = `PO-${seq}`;
    const nonce = `live-po-nonce-${seq}`;
    db.prepare('INSERT INTO quotations (name, company_code, docstatus, total_qty, readable) VALUES (?, ?, ?, ?, ?)')
      .run(sqName, sqCompany, sqStatus, sqQty, readable);
    db.prepare('INSERT INTO purchase_orders (name, quotation_name, company_code, docstatus, total_qty, expected_closure_nonce) VALUES (?, ?, ?, 0, ?, ?)')
      .run(poName, sqName, poCompany, poQty, nonce);
    return {
      caseId: `po-${seq}`,
      app: 'purchase-orders',
      recordKey: poName,
      quotationKey: sqName,
      targetVal: ref,
      nonce,
      variant,
      valid: label === 'valid',
      kind,
      failureId,
      toctouCancel,
    };
  };

  // Equal training contrast set (never evaluated in holdout)
  const training = {
    'work-packages': [
      insertWp({ apProject: 10, apStatus: 16, apHours: 12, wpProject: 10, targetHours: 12, variant: 'v1-clean', label: 'valid', kind: 'train' }),
      insertWp({ apProject: 20, apStatus: 16, apHours: 24, wpProject: 20, targetHours: 24, variant: 'v1-clean', label: 'valid', kind: 'train' }),
      insertWp({ apProject: 10, apStatus: 17, apHours: 12, wpProject: 10, targetHours: 12, variant: 'v1-clean', label: 'invalid', kind: 'train', failureId: 'tr-wp-1' }),
      insertWp({ apProject: 10, apStatus: 16, apHours: 8, wpProject: 10, targetHours: 12, variant: 'v1-clean', label: 'invalid', kind: 'train', failureId: 'tr-wp-2' }),
      insertWp({ apProject: 99, apStatus: 16, apHours: 12, wpProject: 10, targetHours: 12, variant: 'v1-clean', label: 'invalid', kind: 'train', failureId: 'tr-wp-3' }),
    ],
    'purchase-orders': [
      insertPo({ sqCompany: 101, sqStatus: 1, sqQty: 10, poCompany: 101, poQty: 10, ref: 'CONF-T001', variant: 'v1-clean', label: 'valid', kind: 'train' }),
      insertPo({ sqCompany: 102, sqStatus: 1, sqQty: 25, poCompany: 102, poQty: 25, ref: 'CONF-T002', variant: 'v1-clean', label: 'valid', kind: 'train' }),
      insertPo({ sqCompany: 101, sqStatus: 0, sqQty: 10, poCompany: 101, poQty: 10, ref: 'CONF-T003', variant: 'v1-clean', label: 'invalid', kind: 'train', failureId: 'tr-po-1' }),
      insertPo({ sqCompany: 101, sqStatus: 1, sqQty: 6, poCompany: 101, poQty: 10, ref: 'CONF-T004', variant: 'v1-clean', label: 'invalid', kind: 'train', failureId: 'tr-po-2' }),
      insertPo({ sqCompany: 103, sqStatus: 1, sqQty: 10, poCompany: 101, poQty: 10, ref: 'CONF-T005', variant: 'v1-clean', label: 'invalid', kind: 'train', failureId: 'tr-po-3' }),
    ],
  };

  const holdout = [];

  // Row A: 50 independent server-only conflict traps (25 work-packages + 25 purchase-orders)
  for (let i = 0; i < 25; i += 1) {
    const mode = i % 5;
    holdout.push(insertWp({
      apProject: mode === 2 ? 77 : 10,
      apStatus: mode === 0 ? 17 : mode === 4 ? 16 : 16,
      apHours: mode === 1 ? 6 : 16,
      readable: mode === 3 ? 0 : 1,
      wpProject: 10,
      targetHours: 16,
      variant: 'v1-clean',
      label: 'invalid',
      kind: 'row-a-server-conflict',
      failureId: `rowA-wp-${i}`,
      toctouCancel: mode === 4,
    }));
  }
  for (let i = 0; i < 25; i += 1) {
    const mode = i % 5;
    holdout.push(insertPo({
      sqCompany: mode === 2 ? 103 : 101,
      sqStatus: mode === 0 ? 0 : 1,
      sqQty: mode === 1 ? 4 : 15,
      readable: mode === 3 ? 0 : 1,
      poCompany: 101,
      poQty: 15,
      ref: `CONF-A${String(i).padStart(3, '0')}`,
      variant: 'v1-clean',
      label: 'invalid',
      kind: 'row-a-server-conflict',
      failureId: `rowA-po-${i}`,
      toctouCancel: mode === 4,
    }));
  }

  // Row B: 50 independent client-side v1->v2 payload/validation/dirty-field traps (25 WP + 25 PO)
  const trapVariants = [
    'trap-hidden-surcharge',
    'trap-wrong-method',
    'trap-wrong-endpoint',
    'trap-client-alert',
    'trap-dirty-field',
  ];
  for (let i = 0; i < 25; i += 1) {
    holdout.push(insertWp({
      apProject: 10, apStatus: 16, apHours: 20, wpProject: 10, targetHours: 20,
      variant: trapVariants[i % trapVariants.length],
      label: 'invalid',
      kind: 'row-b-client-drift-trap',
      failureId: `rowB-wp-${i}`,
    }));
  }
  for (let i = 0; i < 25; i += 1) {
    holdout.push(insertPo({
      sqCompany: 101, sqStatus: 1, sqQty: 20, poCompany: 101, poQty: 20,
      ref: `CONF-B${String(i).padStart(3, '0')}`,
      variant: trapVariants[i % trapVariants.length],
      label: 'invalid',
      kind: 'row-b-client-drift-trap',
      failureId: `rowB-po-${i}`,
    }));
  }

  // Valid set: 50 clean v1 reuse (25 WP + 25 PO) + 50 v2 UI/serializer repair (25 WP + 25 PO)
  for (let i = 0; i < 25; i += 1) {
    holdout.push(insertWp({
      apProject: 10, apStatus: 16, apHours: 12 + (i % 6), wpProject: 10, targetHours: 12 + (i % 6),
      variant: 'v1-clean', label: 'valid', kind: 'valid-v1-reuse',
    }));
    holdout.push(insertPo({
      sqCompany: 101, sqStatus: 1, sqQty: 10 + i, poCompany: 101, poQty: 10 + i,
      ref: `CONF-V${String(i).padStart(3, '0')}`,
      variant: 'v1-clean', label: 'valid', kind: 'valid-v1-reuse',
    }));
  }
  for (let i = 0; i < 25; i += 1) {
    const v2 = i % 2 === 0 ? 'v2-ui-renamed' : 'v2-legacy-serializer';
    holdout.push(insertWp({
      apProject: 20, apStatus: 16, apHours: 18 + (i % 5), wpProject: 20, targetHours: 18 + (i % 5),
      variant: v2, label: 'valid', kind: 'valid-v2-repair',
    }));
    holdout.push(insertPo({
      sqCompany: 102, sqStatus: 1, sqQty: 30 + i, poCompany: 102, poQty: 30 + i,
      ref: `CONF-R${String(i).padStart(3, '0')}`,
      variant: v2, label: 'valid', kind: 'valid-v2-repair',
    }));
  }

  return { training, holdout };
}

export async function runAblation({ outReceiptPath = null } = {}) {
  const executablePath = findBrowserExecutable();
  if (!executablePath) throw Error('No local Chromium/Chrome binary found for real-browser 2x2 ablation');

  const appServer = createTwoAppServer();
  await new Promise(done => appServer.server.listen(0, '127.0.0.1', done));
  const origin = `http://127.0.0.1:${appServer.server.address().port}`;
  const browser = await chromium.launch({ executablePath, args: ['--headless=new'] });

  try {
    const { training, holdout } = buildBenchmarkDataset(appServer.db);
    const ALL_ROLES = {
      'work-packages': ['record', 'approval', 'audit_log', 'team_stats', 'history'],
      'purchase-orders': ['order', 'quotation', 'audit_log', 'vendor_stats', 'history'],
    };

    const fetchRoles = async (item, roles) => {
      const responses = [];
      let reads = 0;
      if (item.app === 'work-packages') {
        responses.push({
          sameOrigin: true, method: 'GET', transport: 'fetch', status: 200,
          sourceRole: 'intent', json: { estimatedTime: `PT${item.targetVal}H` },
        });
      }
      for (const role of roles) {
        reads += 1;
        const path = item.app === 'work-packages'
          ? `/api/wp/${item.recordKey}/${role}`
          : `/api/po/${encodeURIComponent(item.recordKey)}/${role}`;
        const r = await fetch(origin + path);
        if (r.status >= 200 && r.status < 300) {
          responses.push({
            sameOrigin: true, method: 'GET', transport: 'fetch', status: r.status,
            sourceRole: role, json: await r.json(),
          });
        }
      }
      return { reads, responses };
    };

    // Teach `learnRepairBoundary` on both apps from the 5-example contrast release over ALL 5 discovery roles!
    const bindings = {
      'work-packages': opBind('work-packages-save-hours'),
      'purchase-orders': opBind('purchase-orders-confirm-ref'),
    };
    const learnedBoundaries = {};
    for (const app of ['work-packages', 'purchase-orders']) {
      const pos = [];
      const neg = [];
      for (const ex of training[app]) {
        const { responses } = await fetchRoles(ex, ALL_ROLES[app]);
        const obs = collectObservedFacts(responses);
        (ex.valid ? pos : neg).push(obs);
      }
      const learned = learnRepairBoundary({ positive: pos, negative: neg, intendedEffect: bindings[app] });
      assert.equal(learned.status, 'learned', `failed to learn boundary on ${app}: ${learned.reason}`);
      learnedBoundaries[app] = learned;
    }

    // Coding-agent / authored guard: (a) catalog-wide check over all 5 roles, (b) minimal hand-tuned 2-role check
    const checkGuardWithRoles = async (item, roles) => {
      const { reads, responses } = await fetchRoles(item, roles);
      const byRole = Object.fromEntries(responses.map(r => [r.sourceRole, r.json]));
      if (item.app === 'work-packages') {
        const ok = byRole.record && byRole.approval
          && byRole.approval.statusCode === 16
          && byRole.approval.estimatedTime === `PT${item.targetVal}H`
          && byRole.approval.projectCode === byRole.record.projectCode;
        return { holds: Boolean(ok), reads };
      }
      const ok = byRole.order && byRole.quotation
        && byRole.quotation.docstatus === 1
        && byRole.quotation.totalQty === byRole.order.totalQty
        && byRole.quotation.companyCode === byRole.order.companyCode;
      return { holds: Boolean(ok), reads };
    };
    const authoredGuardCheck = item => checkGuardWithRoles(item, ALL_ROLES[item.app]);
    const authoredMinimalGuardCheck = item => checkGuardWithRoles(
      item,
      item.app === 'work-packages' ? ['record', 'approval'] : ['order', 'quotation'],
    );

    const snapshotDb = item => item.app === 'work-packages'
      ? { ...appServer.db.prepare('SELECT * FROM work_packages WHERE id = ?').get(item.recordKey) }
      : { ...appServer.db.prepare('SELECT * FROM purchase_orders WHERE name = ?').get(item.recordKey) };

    const restoreDb = (item, snap) => {
      if (item.app === 'work-packages') {
        appServer.db.prepare(`
          UPDATE work_packages
          SET estimated_hours = ?, surcharge_hours = ?, archived = ?, committed_nonce = ?, lock_version = ?
          WHERE id = ?
        `).run(snap.estimated_hours, snap.surcharge_hours, snap.archived, snap.committed_nonce, snap.lock_version, item.recordKey);
        if (item.toctouCancel) {
          appServer.db.prepare('UPDATE approvals SET status_code = 16 WHERE id = ?').run(item.approvalKey);
        }
      } else {
        appServer.db.prepare(`
          UPDATE purchase_orders
          SET terms = ?, surcharge_fee = ?, archived = ?, committed_nonce = ?, lock_version = ?
          WHERE name = ?
        `).run(snap.terms, snap.surcharge_fee, snap.archived, snap.committed_nonce, snap.lock_version, item.recordKey);
        if (item.toctouCancel) {
          appServer.db.prepare('UPDATE quotations SET docstatus = 1 WHERE name = ?').run(item.quotationKey);
        }
      }
    };

    const checkDbOutcome = (item, before, after) => {
      const committed = after.lock_version !== before.lock_version;
      if (!committed) return { committed: false, cleanValidEffect: false };
      if (item.app === 'work-packages') {
        const clean = after.archived === 0
          && after.surcharge_hours === 0
          && after.estimated_hours === item.targetVal
          && after.committed_nonce === item.nonce;
        return { committed: true, cleanValidEffect: clean };
      }
      const clean = after.archived === 0
        && after.surcharge_fee === 0
        && after.terms === item.targetVal
        && after.committed_nonce === item.nonce;
      return { committed: true, cleanValidEffect: clean };
    };

    const candidateSpecsFor = item => {
      const targetUrl = item.app === 'work-packages'
        ? `${origin}/api/wp/${item.recordKey}/save`
        : `${origin}/api/po/${item.recordKey}/confirm`;
      const field = item.app === 'work-packages' ? 'hours' : 'reference';
      const expect = { attempt: 'fetch', target: targetUrl, method: 'POST', bodyFields: [field, 'nonce'] };
      const base = [
        { id: 'v1-reuse', kind: 'reuse', action: 'window.runStoredV1()', expect, fields: [field] },
        { id: 'v2-repair', kind: 'repair', action: 'window.runRepairV2()', expect, fields: [field] },
      ];
      for (let k = 3; k <= 8; k += 1) {
        base.push({ id: `alt-${k}`, kind: 'repair', action: `window.runAltCandidate${k}()`, expect, fields: [field] });
      }
      return base;
    };

    // Reuse one Chromium context with isolated pages for speed and determinism
    const context = await browser.newContext();
    const page = await context.newPage();

    /**
     * Simulates Fawn's zero-egress live-state branch execution (`Page.fawnBranchStatus`) vs
     * stock browser reload preview (`reloadMode: true` reloads the URL, losing live JS closure state).
     */
    const executeBranchPreviews = async (item, { controlExpression, candidates }, { reloadMode = false } = {}) => {
      const pageUrl = `${origin}/page?app=${item.app}&id=${encodeURIComponent(item.recordKey)}&val=${encodeURIComponent(item.targetVal)}&variant=${item.variant}`;
      const runSingle = async expr => {
        await page.goto(pageUrl);
        if (!reloadMode) {
          // Live state reached by user before branching: closure holds unsaved nonce!
          await page.evaluate(n => window.__setLiveUnsavedClosure(n), item.nonce);
        }
        appServer.setPreviewPhase(true);
        try {
          // Block all network egress inside the branch and record browser-level attempts,
          // matching Fawn's `Page.fawnBranchStatus` contract (`north-star.md` §5).
          const rawLine = await page.evaluate(async wrappedExpr => {
            const attempts = [];
            const origFetch = window.fetch;
            window.fetch = function (input, init) {
              const rawTarget = typeof input === 'string' ? input : input.url;
              const resolved = new URL(rawTarget, document.baseURI).href;
              attempts.push({ attempt: 'fetch', target: resolved });
              return Promise.reject(new DOMException('Blocked in branch', 'NotAllowedError'));
            };
            try {
              const val = await (0, eval)(wrappedExpr);
              return ['finished', ...attempts.map(a => JSON.stringify(a)), JSON.stringify({ ok: true, value: val })].join('\n');
            } catch (err) {
              return ['finished', ...attempts.map(a => JSON.stringify(a)), JSON.stringify({ ok: false, value: String(err) })].join('\n');
            } finally {
              window.fetch = origFetch;
            }
          }, expr);
          return rawLine;
        } finally {
          appServer.setPreviewPhase(false);
        }
      };

      const control = await runSingle(controlExpression);
      const outCandidates = [];
      for (const c of candidates) {
        outCandidates.push({ id: c.id, text: await runSingle(c.expression) });
      }
      // If item has a TOCTOU mid-preview server cancellation, trigger it right after branch preview!
      if (item.toctouCancel) {
        if (item.app === 'work-packages') {
          appServer.db.prepare('UPDATE approvals SET status_code = 17 WHERE id = ?').run(item.approvalKey);
        } else {
          appServer.db.prepare('UPDATE quotations SET docstatus = 2 WHERE name = ?').run(item.quotationKey);
        }
      }
      return { control, candidates: outCandidates, branchesRun: 1 + candidates.length };
    };

    /** Executes the chosen live action on the real page with network enabled. */
    const commitChosenActionOnLivePage = async (item, winnerId, { reloadMode = false } = {}) => {
      const pageUrl = `${origin}/page?app=${item.app}&id=${encodeURIComponent(item.recordKey)}&val=${encodeURIComponent(item.targetVal)}&variant=${item.variant}`;
      await page.goto(pageUrl);
      if (!reloadMode) {
        await page.evaluate(n => window.__setLiveUnsavedClosure(n), item.nonce);
      }
      const fn = winnerId === 'v2-repair' ? 'runRepairV2' : 'runStoredV1';
      await page.evaluate(async name => { await window[name](); }, fn);
    };

    const ARMS = [
      'blind-replay',
      'fawn-branch-only',
      'gammatron-facts-only',
      'stock-reload-plus-guard',
      'authored-guard-exhaustive-branch',
      'authored-guard-minimal-pruned',
      'gammatron-pruned-lookahead',
    ];

    const resultsByArm = {};
    for (const arm of ARMS) {
      const t0 = Date.now();
      let serverReads = 0;
      let branchesEvaluated = 0;
      let wrongInvalidRowA = 0;
      let wrongInvalidRowB = 0;
      let corruptedValidCommits = 0;
      let validReuseCompleted = 0;
      let validRepairCompleted = 0;
      let certificatesEmitted = 0;

      for (const item of holdout) {
        const snap = snapshotDb(item);
        try {
          const specs = candidateSpecsFor(item);
          let winnerId = null;
          let reloadCommit = false;

          if (arm === 'blind-replay') {
            winnerId = 'v1-reuse';
          } else if (arm === 'fawn-branch-only') {
            const preview = await executeBranchPreviews(item, {
              controlExpression: branchExpression('0'),
              candidates: specs.map(s => ({ id: s.id, expression: branchExpression(s.action) })),
            });
            branchesEvaluated += preview.branchesRun;
            const byId = new Map(preview.candidates.map(c => [c.id, c.text]));
            const verified = verifyBranches({
              control: preview.control,
              candidates: specs.map(s => ({ ...s, text: byId.get(s.id) })),
            });
            if (verified.decision === 'eligible') winnerId = verified.winner;
          } else if (arm === 'gammatron-facts-only') {
            const boundary = learnedBoundaries[item.app];
            const roles = extractMinimalReadRoles(boundary);
            const pre = await fetchRoles(item, roles);
            serverReads += pre.reads;
            if (item.toctouCancel) {
              if (item.app === 'work-packages') appServer.db.prepare('UPDATE approvals SET status_code = 17 WHERE id = ?').run(item.approvalKey);
              else appServer.db.prepare('UPDATE quotations SET docstatus = 2 WHERE name = ?').run(item.quotationKey);
            }
            const post = await fetchRoles(item, roles);
            serverReads += post.reads;
            const check = checkRepairBoundary(boundary, collectObservedFacts(post.responses), bindings[item.app]);
            if (check.status === 'eligible-for-review') winnerId = 'v1-reuse';
          } else if (arm === 'stock-reload-plus-guard') {
            const pre = await authoredGuardCheck(item);
            serverReads += pre.reads;
            if (pre.holds) {
              const preview = await executeBranchPreviews(item, {
                controlExpression: branchExpression('0'),
                candidates: specs.slice(0, 2).map(s => ({ id: s.id, expression: branchExpression(s.action) })),
              }, { reloadMode: true });
              branchesEvaluated += preview.branchesRun;
              const byId = new Map(preview.candidates.map(c => [c.id, c.text]));
              const verified = verifyBranches({
                control: preview.control,
                candidates: specs.slice(0, 2).map(s => ({ ...s, text: byId.get(s.id) })),
              });
              const post = await authoredGuardCheck(item);
              serverReads += post.reads;
              if (verified.decision === 'eligible' && post.holds) {
                winnerId = verified.winner;
                reloadCommit = true;
              }
            }
          } else if (arm === 'authored-guard-exhaustive-branch' || arm === 'authored-guard-minimal-pruned') {
            const guardFn = arm === 'authored-guard-minimal-pruned' ? authoredMinimalGuardCheck : authoredGuardCheck;
            const candidateSlice = arm === 'authored-guard-minimal-pruned' ? specs.slice(0, 2) : specs;
            const pre = await guardFn(item);
            serverReads += pre.reads;
            if (pre.holds) {
              const preview = await executeBranchPreviews(item, {
                controlExpression: branchExpression('0'),
                candidates: candidateSlice.map(s => ({ id: s.id, expression: branchExpression(s.action) })),
              });
              branchesEvaluated += preview.branchesRun;
              const byId = new Map(preview.candidates.map(c => [c.id, c.text]));
              const verified = verifyBranches({
                control: preview.control,
                candidates: candidateSlice.map(s => ({ ...s, text: byId.get(s.id) })),
              });
              if (verified.decision === 'eligible') {
                const post = await guardFn(item);
                serverReads += post.reads;
                if (post.holds) winnerId = verified.winner;
              }
            }
          } else if (arm === 'gammatron-pruned-lookahead') {
            const cert = await evaluateLiveLookahead({
              boundary: learnedBoundaries[item.app],
              intendedEffect: bindings[item.app],
              candidates: specs,
              pruneTopK: 2,
              readServerRoles: roles => fetchRoles(item, roles),
              runBranches: req => executeBranchPreviews(item, req),
            });
            serverReads += cert.serverReads;
            branchesEvaluated += cert.branchesRun;
            if (cert.decision === 'reuse' || cert.decision === 'repair') {
              certificatesEmitted += 1;
              winnerId = cert.winnerId;
            }
          }

          if (winnerId !== null) {
            await commitChosenActionOnLivePage(item, winnerId, { reloadMode: reloadCommit });
          }

          const after = snapshotDb(item);
          const { committed, cleanValidEffect } = checkDbOutcome(item, snap, after);

          if (!item.valid) {
            if (committed) {
              if (item.kind === 'row-a-server-conflict') wrongInvalidRowA += 1;
              else wrongInvalidRowB += 1;
            }
          } else if (committed && cleanValidEffect) {
            if (item.kind === 'valid-v1-reuse') validReuseCompleted += 1;
            else validRepairCompleted += 1;
          } else if (committed && !cleanValidEffect) {
            corruptedValidCommits += 1;
          }
        } finally {
          restoreDb(item, snap);
        }
      }

      const totalInvalidWrong = wrongInvalidRowA + wrongInvalidRowB;
      const upper95 = clopperPearson95Upper(totalInvalidWrong, 100);
      resultsByArm[arm] = {
        arm,
        independentInvalidCases: 100,
        wrongInvalidRowAServerConflict: wrongInvalidRowA,
        wrongInvalidRowBClientDrift: wrongInvalidRowB,
        totalInvalidWrongCommits: totalInvalidWrong,
        corruptedValidCommits,
        clopperPearson95Upper: Number(upper95.toFixed(6)),
        clopperPearson95UpperPct: Number((upper95 * 100).toFixed(3)),
        meetsThreePctSafetyBar: upper95 < 0.03 && corruptedValidCommits === 0,
        validReuseCompletedOf50: validReuseCompleted,
        validRepairCompletedOf50: validRepairCompleted,
        totalValidCompletedOf100: validReuseCompleted + validRepairCompleted,
        serverReads,
        branchesEvaluated,
        certificatesEmitted,
        wallMs: Date.now() - t0,
      };
    }

    await context.close();
    assert.equal(appServer.getPreviewMutations(), 0, 'zero server mutations may occur during branch previews');

    const receipt = {
      schema: 'gammatron.fawn-2x2-mechanism-ablation/v1',
      recordedAt: new Date().toISOString(),
      modelSpendUsd: 0,
      browserVersion: browser.version(),
      scopeNote: 'Real headless Chromium + node:sqlite two-application (work-packages, purchase-orders) v1->v2 mechanism ablation. Branch previews run with network egress blocked in Page.fawnBranchStatus wire format (0 preview mutations reached SQLite); Linux CoW renderer fork() remains separately qualified on Fawn host.',
      learnedMinimalRoles: {
        'work-packages': extractMinimalReadRoles(learnedBoundaries['work-packages']),
        'purchase-orders': extractMinimalReadRoles(learnedBoundaries['purchase-orders']),
      },
      discoveryCatalogRoles: ALL_ROLES,
      counts: {
        independentInvalidTotal: 100,
        rowAServerConflictInvalid: 50,
        rowBClientDriftInvalid: 50,
        validV1Reuse: 50,
        validV2Repair: 50,
      },
      serverPreviewMutationsObserved: appServer.getPreviewMutations(),
      arms: resultsByArm,
      mechanismFindings: {
        fawnAloneFailsServerConflicts: resultsByArm['fawn-branch-only'].wrongInvalidRowAServerConflict === 50
          && resultsByArm['fawn-branch-only'].wrongInvalidRowBClientDrift === 0,
        gammatronAloneFailsClientPayloadDrift: resultsByArm['gammatron-facts-only'].wrongInvalidRowAServerConflict === 0
          && resultsByArm['gammatron-facts-only'].wrongInvalidRowBClientDrift === 50,
        stockReloadLosesUnsavedClosureState: resultsByArm['stock-reload-plus-guard'].totalValidCompletedOf100 === 0
          && resultsByArm['stock-reload-plus-guard'].corruptedValidCommits === 100,
        combinedLookaheadMeetsSafetyAndCompletesAll: resultsByArm['gammatron-pruned-lookahead'].totalInvalidWrongCommits === 0
          && resultsByArm['gammatron-pruned-lookahead'].corruptedValidCommits === 0
          && resultsByArm['gammatron-pruned-lookahead'].totalValidCompletedOf100 === 100,
        prunedLookaheadBeatsExhaustiveAuthoredOnReadsAndBranches:
          resultsByArm['gammatron-pruned-lookahead'].serverReads < resultsByArm['authored-guard-exhaustive-branch'].serverReads
          && resultsByArm['gammatron-pruned-lookahead'].branchesEvaluated < resultsByArm['authored-guard-exhaustive-branch'].branchesEvaluated,
        learnedMatchesHandTunedMinimalPrunedAtRuntime:
          resultsByArm['gammatron-pruned-lookahead'].serverReads === resultsByArm['authored-guard-minimal-pruned'].serverReads
          && resultsByArm['gammatron-pruned-lookahead'].branchesEvaluated === resultsByArm['authored-guard-minimal-pruned'].branchesEvaluated
          && resultsByArm['gammatron-pruned-lookahead'].totalValidCompletedOf100 === resultsByArm['authored-guard-minimal-pruned'].totalValidCompletedOf100,
      },
    };

    if (outReceiptPath) {
      mkdirSync(dirname(resolve(outReceiptPath)), { recursive: true });
      writeFileSync(resolve(outReceiptPath), `${JSON.stringify(receipt, null, 2)}\n`);
    }
    return receipt;
  } finally {
    await browser.close();
    appServer.server.close();
    appServer.db.close();
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const outIdx = process.argv.indexOf('--out');
  const outPath = outIdx >= 0 ? process.argv[outIdx + 1] : join(HERE, 'receipts', 'fawn-gammatron-2x2-receipt.json');
  const receipt = await runAblation({ outReceiptPath: outPath });
  console.log(JSON.stringify(receipt, null, 2));
}
