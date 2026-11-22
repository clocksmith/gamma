#!/usr/bin/env node
// Host contract sufficiency, integration-cost, and Direct Write-API benchmark (#88, Item 2).
// Exercises real headless Chrome (`createPlaywrightAdapter`) + `WorkspaceService` against a real
// loopback HTTP + normalized `node:sqlite` backend with three separate tables:
//   1. `formulary_orders` (target record with `order_version`)
//   2. `clinical_approvals` (separate approval entity with `approval_version` — updates here do NOT
//      bump `formulary_orders.order_version`, exposing why single-record ETags are insufficient)
//   3. `effect_journal` (durable server idempotency log keyed by `externalIdempotencyKey`)
//
// Measures exact non-comment server integration LOC (testing the "~20 lines" hypothesis), extra
// SQLite predicate reads, end-to-end latency, race/dedup outcomes across contract regimes,
// unavailable-predicate fallback, and a supported Direct REST Write-API baseline.

import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { fileURLToPath } from 'node:url';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import {
  AttestedSkillBook,
  createAttestedSkillPlanner,
  recordAttestedSkillTeaching,
} from '../../src/client/attested-skill.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { SuffixIndex } from '../../src/client/suffix-eligibility.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';
import { loadServiceConfig } from '../../src/config.js';
import { WorkspaceService } from '../../src/service.js';

const LIMITS = Object.freeze({ maxNodes: 96, maxEdges: 96, maxSteps: 32 });
const CLIENT_CONFIG = Object.freeze({ maxTurns: 16, maxInputBytes: 60000 });

// --- Modular reference host handlers (measured directly for non-comment LOC) ---

function hostBooleanAttest(db, counters, { account, orderId, skipped }) {
  counters.sqlReads += 2;
  const order = db.prepare('SELECT account_scope, indication FROM formulary_orders WHERE order_id = ?').get(orderId);
  const approval = db.prepare('SELECT decision FROM clinical_approvals WHERE order_id = ?').get(orderId);
  if (!order || order.account_scope !== account) {
    return skipped.map(() => false);
  }
  return skipped.map(step => {
    if (step.slot === 'orderId' || step.locator?.[1] === 'Load Order') return true;
    if (step.slot === 'indication' || step.locator?.[1] === 'Save Indication') {
      return Boolean(order.indication) && approval?.decision === 'approved';
    }
    return false;
  });
}

function hostVersionedAttest(db, counters, { account, orderId, skipped, unavailableApproval = false }) {
  counters.sqlReads += 2;
  const order = db.prepare(
    'SELECT account_scope, indication, order_version FROM formulary_orders WHERE order_id = ?',
  ).get(orderId);
  if (!order) {
    return skipped.map((_, i) => ({
      holds: false, account, record: orderId, predicate: `step-${i}`, version: 0,
    }));
  }
  const approval = unavailableApproval
    ? null
    : db.prepare('SELECT approval_id, decision, approval_version FROM clinical_approvals WHERE order_id = ?').get(orderId);
  return skipped.map((step, i) => {
    if (unavailableApproval && (step.slot === 'indication' || step.locator?.[1] === 'Save Indication')) {
      return { status: 'unavailable', predicate: 'clinical-approval', reason: 'external-id-service-no-read-api' };
    }
    if (step.slot === 'orderId' || step.locator?.[1] === 'Load Order') {
      return {
        holds: true,
        account: order.account_scope,
        record: orderId,
        predicate: 'order-exists',
        version: order.order_version,
      };
    }
    if (step.slot === 'indication' || step.locator?.[1] === 'Save Indication') {
      return {
        holds: Boolean(order.indication) && approval?.decision === 'approved',
        account: order.account_scope,
        record: approval?.approval_id ?? orderId,
        predicate: 'approval-active',
        version: approval?.approval_version ?? 0,
      };
    }
    return { holds: false, account: order.account_scope, record: orderId, predicate: `step-${i}`, version: 0 };
  });
}

function hostAtomicMultiPredicateCommit(db, counters, { account, orderId, doseTier, rationale, predicateVersions }) {
  db.exec('BEGIN IMMEDIATE');
  try {
    counters.sqlReads += 2;
    const order = db.prepare(
      'SELECT account_scope, order_version FROM formulary_orders WHERE order_id = ?',
    ).get(orderId);
    const approval = db.prepare(
      'SELECT approval_id, decision, approval_version FROM clinical_approvals WHERE order_id = ?',
    ).get(orderId);
    if (!order || order.account_scope !== account) throw Error('wrong-account-or-missing-order');
    if (!Array.isArray(predicateVersions) || predicateVersions.length === 0) {
      throw Error('missing-predicate-versions');
    }
    for (const pv of predicateVersions) {
      if (pv.predicate === 'order-exists' && order.order_version !== pv.version) {
        throw Error('stale-order-version');
      }
      if (pv.predicate === 'approval-active'
        && (approval?.approval_id !== pv.record || approval?.approval_version !== pv.version || approval?.decision !== 'approved')) {
        throw Error('stale-or-revoked-approval-version');
      }
    }
    if (approval?.decision !== 'approved') throw Error('approval-not-active');
    db.prepare(
      'UPDATE formulary_orders SET dose_tier = ?, rationale = ?, order_version = order_version + 1, status = ? WHERE order_id = ?',
    ).run(doseTier, rationale, 'review-ready', orderId);
    counters.commits += 1;
    if (approval?.decision !== 'approved') counters.forbiddenCommits += 1;
    db.exec('COMMIT');
    return { ok: true, orderVersion: order.order_version + 1 };
  } catch (err) {
    db.exec('ROLLBACK');
    throw err;
  }
}

function hostIdempotentJournalWrap(db, counters, { idempotencyKey, account, orderId }, mutateFn) {
  if (idempotencyKey) {
    counters.sqlReads += 1;
    const prior = db.prepare(
      'SELECT committed_seq, response_json FROM effect_journal WHERE idempotency_key = ?',
    ).get(idempotencyKey);
    if (prior) {
      counters.deduplicatedRetries += 1;
      return { ...JSON.parse(prior.response_json), deduplicated: true, serverSeq: prior.committed_seq };
    }
  }
  const response = mutateFn();
  if (idempotencyKey) {
    const seq = (db.prepare('SELECT COALESCE(MAX(committed_seq), 0) AS m FROM effect_journal').get().m ?? 0) + 1;
    db.prepare(
      'INSERT INTO effect_journal (idempotency_key, account_scope, order_id, committed_seq, response_json) VALUES (?, ?, ?, ?, ?)',
    ).run(idempotencyKey, account, orderId, seq, JSON.stringify(response));
    return { ...response, deduplicated: false, serverSeq: seq };
  }
  return response;
}

function hostVerifyJournalKey(db, counters, idempotencyKey) {
  counters.sqlReads += 1;
  const row = db.prepare('SELECT committed_seq FROM effect_journal WHERE idempotency_key = ?').get(idempotencyKey);
  return row ? { committed: true, serverSeq: row.committed_seq } : { committed: false };
}

function hostDirectWriteApi(db, counters, body, idempotencyKey) {
  return hostIdempotentJournalWrap(
    db,
    counters,
    { idempotencyKey, account: body.account, orderId: body.orderId },
    () => {
      db.exec('BEGIN IMMEDIATE');
      try {
        counters.sqlReads += 2;
        const order = db.prepare(
          'SELECT account_scope, indication, order_version FROM formulary_orders WHERE order_id = ?',
        ).get(body.orderId);
        const approval = db.prepare(
          'SELECT decision, approval_version FROM clinical_approvals WHERE order_id = ?',
        ).get(body.orderId);
        if (!order || order.account_scope !== body.account) throw Error('unauthorized-account');
        if (!order.indication || approval?.decision !== 'approved') throw Error('prerequisite-unmet');
        db.prepare(
          'UPDATE formulary_orders SET dose_tier = ?, rationale = ?, order_version = order_version + 1, status = ? WHERE order_id = ?',
        ).run(body.doseTier, body.rationale, 'review-ready', body.orderId);
        counters.commits += 1;
        db.exec('COMMIT');
        return { ok: true, orderId: body.orderId, status: 'review-ready', orderVersion: order.order_version + 1 };
      } catch (err) {
        db.exec('ROLLBACK');
        throw err;
      }
    },
  );
}

function countNonCommentLoc(fn) {
  const lines = fn.toString().split('\n');
  // Strip outer function declaration and closing brace so we measure handler body + SQL statements cleanly,
  // or keep full function declaration — keeping full function declaration is strictly conservative!
  return lines.filter(raw => {
    const s = raw.trim();
    return s.length > 0 && !s.startsWith('//') && !s.startsWith('/*') && !s.startsWith('*');
  }).length;
}

function createSqliteHarnessDb() {
  const db = new DatabaseSync(':memory:');
  db.exec(`
    CREATE TABLE formulary_orders (
      order_id TEXT PRIMARY KEY,
      account_scope TEXT NOT NULL,
      indication TEXT NOT NULL DEFAULT '',
      dose_tier TEXT NOT NULL DEFAULT '',
      rationale TEXT NOT NULL DEFAULT '',
      order_version INTEGER NOT NULL DEFAULT 1,
      status TEXT NOT NULL DEFAULT 'draft'
    );
    CREATE TABLE clinical_approvals (
      approval_id TEXT PRIMARY KEY,
      order_id TEXT NOT NULL,
      account_scope TEXT NOT NULL,
      decision TEXT NOT NULL,
      approval_version INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE effect_journal (
      idempotency_key TEXT PRIMARY KEY,
      account_scope TEXT NOT NULL,
      order_id TEXT NOT NULL,
      committed_seq INTEGER NOT NULL,
      response_json TEXT NOT NULL
    );
  `);
  return db;
}

function seedOrder(db, {
  orderId = 'ORD-7001',
  account = 'rx-north',
  indication = '',
  approvalId = 'APP-7001',
  decision = 'approved',
} = {}) {
  db.prepare('DELETE FROM formulary_orders WHERE order_id = ?').run(orderId);
  db.prepare('DELETE FROM clinical_approvals WHERE order_id = ?').run(orderId);
  db.prepare(
    'INSERT INTO formulary_orders (order_id, account_scope, indication, dose_tier, rationale, order_version, status) VALUES (?, ?, ?, ?, ?, 1, ?)',
  ).run(orderId, account, indication, '', '', indication ? 'indication-saved' : 'draft');
  db.prepare(
    'INSERT INTO clinical_approvals (approval_id, order_id, account_scope, decision, approval_version) VALUES (?, ?, ?, ?, 1)',
  ).run(approvalId, orderId, account, decision);
}

function renderHtml(screen, order, approval) {
  const statusBanner = `<output id="order-status" role="status">Approval: ${approval?.decision ?? 'unknown'}</output>`;
  if (screen === 'lookup') {
    return `<!doctype html><html><head><title>Formulary Lookup</title></head><body>
      ${statusBanner}
      <form id="f-lookup" onsubmit="return false">
        <label for="order-id">Order Number</label>
        <input id="order-id" name="orderId" type="text" value="" />
        <button id="btn-load" type="button" onclick="fetch('/ui/load',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({orderId:document.getElementById('order-id').value})}).then(()=>location.assign('/screen/indication?orderId='+encodeURIComponent(document.getElementById('order-id').value)))">Load Order</button>
      </form>
    </body></html>`;
  }
  if (screen === 'indication') {
    return `<!doctype html><html><head><title>Clinical Indication</title></head><body>
      ${statusBanner}
      <form id="f-indication" onsubmit="return false">
        <label for="indication">Clinical Indication</label>
        <input id="indication" name="indication" type="text" value="${order?.indication ?? ''}" />
        <button id="btn-save-ind" type="button" onclick="fetch('/ui/indication',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({orderId:'${order?.order_id ?? ''}',indication:document.getElementById('indication').value})}).then(()=>location.assign('/screen/dosing?orderId=${order?.order_id ?? ''}'))">Save Indication</button>
      </form>
    </body></html>`;
  }
  if (screen === 'dosing') {
    return `<!doctype html><html><head><title>Dosing & Rationale</title></head><body>
      ${statusBanner}
      <form id="f-dosing" onsubmit="return false">
        <label for="dose-tier">Renal Dose Tier</label>
        <input id="dose-tier" name="doseTier" type="text" value="${order?.dose_tier ?? ''}" />
        <label for="rationale">Stewardship Rationale</label>
        <input id="rationale" name="rationale" type="text" value="${order?.rationale ?? ''}" />
        <button id="btn-stage-review" type="button" onclick="window.__commitDosing('${order?.order_id ?? ''}')">Stage Override Review</button>
      </form>
      <script>
        window.__commitDosing = async function(orderId) {
          const headers = { 'content-type': 'application/json' };
          if (window.__nextIdempotencyKey) headers['idempotency-key'] = window.__nextIdempotencyKey;
          if (window.__nextWriteMode) headers['x-write-mode'] = window.__nextWriteMode;
          if (window.__nextWriteVersion !== undefined) headers['x-write-version'] = String(window.__nextWriteVersion);
          if (window.__nextPredicateVersions) headers['x-predicate-versions'] = JSON.stringify(window.__nextPredicateVersions);
          const res = await fetch('/ui/commit-dosing', {
            method: 'POST',
            headers,
            body: JSON.stringify({
              orderId,
              doseTier: document.getElementById('dose-tier').value,
              rationale: document.getElementById('rationale').value,
            }),
          });
          if (!res.ok) throw new Error('commit-rejected:' + res.status);
          location.assign('/screen/review?orderId=' + encodeURIComponent(orderId));
        };
      </script>
    </body></html>`;
  }
  return `<!doctype html><html><head><title>Override Review</title></head><body>
    <output id="review-summary" role="status">${order?.order_id ?? ''}|${order?.dose_tier ?? ''}|${order?.rationale ?? ''}</output>
  </body></html>`;
}

async function startSqliteHttpServer(db, counters, faultControl) {
  const readJson = req => new Promise((resolveBody, rejectBody) => {
    let raw = '';
    req.on('data', chunk => { raw += chunk; });
    req.on('end', () => { try { resolveBody(raw ? JSON.parse(raw) : {}); } catch (e) { rejectBody(e); } });
  });

  const server = createServer(async (req, res) => {
    const url = new URL(req.url, 'http://127.0.0.1');
    if (req.method === 'GET' && url.pathname.startsWith('/screen/')) {
      const screen = url.pathname.replace('/screen/', '');
      const orderId = url.searchParams.get('orderId') ?? 'ORD-7001';
      const order = db.prepare('SELECT * FROM formulary_orders WHERE order_id = ?').get(orderId);
      const approval = db.prepare('SELECT * FROM clinical_approvals WHERE order_id = ?').get(orderId);
      res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      res.end(renderHtml(screen, order, approval));
      return;
    }
    if (req.method === 'POST' && url.pathname === '/ui/load') {
      await readJson(req);
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ ok: true }));
      return;
    }
    if (req.method === 'POST' && url.pathname === '/ui/indication') {
      const body = await readJson(req);
      db.prepare('UPDATE formulary_orders SET indication = ?, status = ? WHERE order_id = ?')
        .run(body.indication, 'indication-saved', body.orderId);
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ ok: true }));
      return;
    }
    if (req.method === 'POST' && url.pathname === '/ui/commit-dosing') {
      const body = await readJson(req);
      const mode = req.headers['x-write-mode'] ?? 'atomic-multi-predicate';
      const idemKey = req.headers['idempotency-key'] ?? null;
      const writeVersion = req.headers['x-write-version'] !== undefined ? Number(req.headers['x-write-version']) : null;
      const predicateVersions = req.headers['x-predicate-versions']
        ? JSON.parse(req.headers['x-predicate-versions'])
        : null;
      try {
        const out = hostIdempotentJournalWrap(
          db,
          counters,
          { idempotencyKey: idemKey, account: 'rx-north', orderId: body.orderId },
          () => {
            if (mode === 'atomic-multi-predicate') {
              return hostAtomicMultiPredicateCommit(db, counters, {
                account: 'rx-north',
                orderId: body.orderId,
                doseTier: body.doseTier,
                rationale: body.rationale,
                predicateVersions,
              });
            }
            if (mode === 'single-record-etag') {
              counters.sqlReads += 1;
              const order = db.prepare('SELECT order_version FROM formulary_orders WHERE order_id = ?').get(body.orderId);
              const approval = db.prepare('SELECT decision FROM clinical_approvals WHERE order_id = ?').get(body.orderId);
              if (!order || order.order_version !== writeVersion) throw Error('stale-single-etag');
              db.prepare(
                'UPDATE formulary_orders SET dose_tier = ?, rationale = ?, order_version = order_version + 1, status = ? WHERE order_id = ?',
              ).run(body.doseTier, body.rationale, 'review-ready', body.orderId);
              counters.commits += 1;
              if (approval?.decision !== 'approved') counters.forbiddenCommits += 1;
              return { ok: true, orderVersion: order.order_version + 1 };
            }
            // Unversioned write
            const approval = db.prepare('SELECT decision FROM clinical_approvals WHERE order_id = ?').get(body.orderId);
            db.prepare(
              'UPDATE formulary_orders SET dose_tier = ?, rationale = ?, order_version = order_version + 1, status = ? WHERE order_id = ?',
            ).run(body.doseTier, body.rationale, 'review-ready', body.orderId);
            counters.commits += 1;
            if (approval?.decision !== 'approved') counters.forbiddenCommits += 1;
            return { ok: true };
          },
        );
        if (faultControl.dropNextCommitResponse) {
          faultControl.dropNextCommitResponse = false;
          res.writeHead(502, { 'content-type': 'application/json', connection: 'close' });
          res.end(JSON.stringify({ ok: false, error: 'gateway-ack-lost-after-commit' }));
          return;
        }
        res.writeHead(200, { 'content-type': 'application/json' });
        res.end(JSON.stringify(out));
      } catch (err) {
        res.writeHead(409, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: err.message }));
      }
      return;
    }
    if (req.method === 'POST' && url.pathname === '/api/v1/formulary-overrides') {
      const body = await readJson(req);
      const idemKey = req.headers['idempotency-key'] ?? null;
      try {
        const out = hostDirectWriteApi(db, counters, body, idemKey);
        res.writeHead(200, { 'content-type': 'application/json' });
        res.end(JSON.stringify(out));
      } catch (err) {
        res.writeHead(409, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: err.message }));
      }
      return;
    }
    res.writeHead(404);
    res.end('not found');
  });

  await new Promise(resolveListen => server.listen(0, '127.0.0.1', resolveListen));
  const { port } = server.address();
  return { server, origin: `http://127.0.0.1:${port}` };
}

export async function runHostContractBenchmark(outPath = null) {
  const locAudit = {
    hypothesisTested: '20 non-comment LOC',
    booleanAttestOnlyLoc: countNonCommentLoc(hostBooleanAttest),
    versionedAttestLoc: countNonCommentLoc(hostVersionedAttest),
    atomicMultiPredicateCommitLoc: countNonCommentLoc(hostAtomicMultiPredicateCommit),
    idempotentJournalLoc: countNonCommentLoc(hostIdempotentJournalWrap) + countNonCommentLoc(hostVerifyJournalKey),
    directWriteApiHandlerLoc: countNonCommentLoc(hostDirectWriteApi),
  };
  locAudit.fullUiContractTotalLoc = locAudit.versionedAttestLoc
    + locAudit.atomicMultiPredicateCommitLoc
    + locAudit.idempotentJournalLoc;
  locAudit.directApiWithJournalTotalLoc = locAudit.directWriteApiHandlerLoc + locAudit.idempotentJournalLoc;
  locAudit.twentyLineHypothesisHoldsForFullContract = locAudit.fullUiContractTotalLoc <= 20;

  const db = createSqliteHarnessDb();
  const counters = { sqlReads: 0, commits: 0, forbiddenCommits: 0, deduplicatedRetries: 0 };
  const resetCounters = () => {
    counters.sqlReads = 0;
    counters.commits = 0;
    counters.forbiddenCommits = 0;
    counters.deduplicatedRetries = 0;
  };
  const faultControl = { dropNextCommitResponse: false };
  const { server, origin } = await startSqliteHttpServer(db, counters, faultControl);

  const root = mkdtempSync(join(tmpdir(), 'host-contract-bench-'));
  mkdirSync(join(root, 'store'), { recursive: true });
  mkdirSync(join(root, 'service'), { recursive: true });
  const store = new InvestigationStore(join(root, 'store'));
  const serviceConfig = loadServiceConfig(undefined, { browserChannel: 'chrome', headless: true });

  let activeWriteMode = 'atomic-multi-predicate';
  let activeUnavailableApproval = false;
  let revokeApprovalAfterCheck = false;
  let bumpOrderAfterCheck = false;
  let adapterRef = null;

  const service = await WorkspaceService.open({
    stateDir: join(root, 'service'),
    config: serviceConfig,
    hooks: {
      afterDispatchStarted: req => {
        if (req.kind === 'click' && req.target?.selector === '#btn-stage-review') {
          if (revokeApprovalAfterCheck) {
            // Separate approval entity revoked WITHOUT bumping formulary_orders.order_version!
            db.prepare(
              'UPDATE clinical_approvals SET decision = ?, approval_version = approval_version + 1 WHERE order_id = ?',
            ).run('revoked', faultControl.currentOrderId);
          }
          if (bumpOrderAfterCheck) {
            db.prepare(
              'UPDATE formulary_orders SET order_version = order_version + 1 WHERE order_id = ?',
            ).run(faultControl.currentOrderId);
          }
        }
      },
    },
    assertPrerequisite: async ({ url, predicateVersions }) => {
      const orderId = new URL(url).searchParams.get('orderId') ?? faultControl.currentOrderId;
      counters.sqlReads += 2;
      const order = db.prepare('SELECT order_version FROM formulary_orders WHERE order_id = ?').get(orderId);
      const approval = db.prepare(
        'SELECT approval_id, decision, approval_version FROM clinical_approvals WHERE order_id = ?',
      ).get(orderId);
      if (approval?.decision !== 'approved') return { ok: false, reason: 'approval-not-active' };
      if (activeWriteMode === 'unversioned-dom') return { ok: true };
      if (activeWriteMode === 'single-record-etag') {
        return { ok: true, writeVersion: order.order_version };
      }
      return {
        ok: true,
        writeVersion: order.order_version,
        predicateVersions: [
          ...(predicateVersions ?? []),
          { account: 'rx-north', record: orderId, predicate: 'order-exists', version: order.order_version },
          { account: 'rx-north', record: approval.approval_id, predicate: 'approval-active', version: approval.approval_version },
        ],
      };
    },
    requirePrerequisiteCheck: true,
    requireConditionalWrite: false,
    verifyExternalIdempotency: async ({ externalIdempotencyKey }) =>
      hostVerifyJournalKey(db, counters, externalIdempotencyKey),
    createAdapter: opts => {
      const rawAdapter = createPlaywrightAdapter(opts);
      const origExec = rawAdapter.execute.bind(rawAdapter);
      rawAdapter.supportsConditionalWrites = true;
      rawAdapter.supportsMultiPredicateWrites = true;
      rawAdapter.execute = async (wsId, request, uploads) => {
        if (request.kind === 'click' && request.target?.selector === '#btn-stage-review') {
          const page = rawAdapter._page(wsId, 'main');
          const mode = activeWriteMode;
          const wv = request.writeVersion ?? null;
          const pv = request.predicateVersions ?? null;
          const ik = request.effect?.externalIdempotencyKey ?? null;
          await page.evaluate(({ mode: m, wv: w, pv: p, ik: k }) => {
            window.__nextWriteMode = m;
            window.__nextWriteVersion = w ?? undefined;
            window.__nextPredicateVersions = p ?? null;
            window.__nextIdempotencyKey = k ?? null;
          }, { mode, wv, pv, ik });
          const execRes = await origExec(wsId, request, uploads);
          if (faultControl.throwLostAckAfterClick) {
            // Wait briefly for the in-page fetch to commit on loopback SQLite before simulating lost ack.
            for (let i = 0; i < 40 && counters.commits === 0; i += 1) {
              await new Promise(r => setTimeout(r, 10));
            }
            faultControl.throwLostAckAfterClick = false;
            throw Error('Lost acknowledgment after server commit');
          }
          return execRes;
        }
        return origExec(wsId, request, uploads);
      };
      adapterRef = rawAdapter;
      return rawAdapter;
    },
  });

  const observationLocators = [
    ['status', 'Approval: approved', 'output', ''],
    ['status', 'Approval: revoked', 'output', ''],
    ['textbox', 'Order Number', 'input', 'text'],
    ['button', 'Load Order', 'button', ''],
    ['textbox', 'Clinical Indication', 'input', 'text'],
    ['button', 'Save Indication', 'button', ''],
    ['textbox', 'Renal Dose Tier', 'input', 'text'],
    ['textbox', 'Stewardship Rationale', 'input', 'text'],
    ['button', 'Stage Override Review', 'button', ''],
  ];
  const intermediateClicks = [
    ['button', 'Load Order', 'button', ''],
    ['button', 'Save Indication', 'button', ''],
    ['button', 'Stage Override Review', 'button', ''],
  ];

  function makeStubPlanner() {
    return {
      identity: { model: 'sqlite-chrome-stub' },
      async next({ observation }) {
        if (observation.elements.some(e => e.role === 'status' && e.label?.includes('revoked'))) {
          return { tool: 'ask_human', input: { reason: 'approval-revoked-on-page' } };
        }
        const pairs = [
          ['Order Number', 'orderId'],
          ['Clinical Indication', 'indication'],
          ['Renal Dose Tier', 'doseTier'],
          ['Stewardship Rationale', 'rationale'],
        ];
        for (const [label, slot] of pairs) {
          const el = observation.elements.find(e => e.label === label);
          if (el && !el.value) return { tool: 'act', input: { kind: 'fill', handle: el.handle, slot } };
        }
        const btn = observation.elements.find(e => e.role === 'button');
        if (btn) return { tool: 'act', input: { kind: 'click', handle: btn.handle } };
        return { tool: 'finish', input: { summary: 'review-ready' } };
      },
    };
  }

  function stepCompletionAndEffect(ordId) {
    return ({ kind, locator }) => {
      if (kind !== 'click') return null;
      if (locator[1] === 'Load Order') {
        return { completion: { completedWhen: [{ kind: 'element-present', selector: '#indication' }] } };
      }
      if (locator[1] === 'Save Indication') {
        return { completion: { completedWhen: [{ kind: 'element-present', selector: '#dose-tier' }] } };
      }
      if (locator[1] === 'Stage Override Review') {
        return {
          effect: { external: true, effectKey: `commit-${ordId}`, externalIdempotencyKey: `idem-${ordId}` },
          completion: { completedWhen: [{ kind: 'element-present', selector: '#review-summary' }] },
        };
      }
      return null;
    };
  }

  let wsSeq = 0;
  async function openBrowserWorkspace(startUrl) {
    const workspaceId = `hc-${++wsSeq}`;
    const admin = { workspaceId, ...(await service.createWorkspace({ workspaceId, scopedReads: true })) };
    await service.grantAuthorization({
      ...admin,
      grantId: 'g-rx',
      ownerId: 'agent',
      intents: ['rx:override'],
      actionKinds: ['navigate', 'fill', 'click'],
      targetOrigins: [origin],
      pageIds: ['main'],
      readRegions: null,
    });
    const owner = { workspaceId, ...(await service.assignOwner({ ...admin, ownerId: 'agent' })) };
    const obs0 = await service.observe(owner);
    const nav = await (await service.submitAction({
      ...owner,
      actionId: randomUUID(),
      authorizedIntent: 'rx:override',
      observationVersion: obs0.observationVersion,
      kind: 'navigate',
      target: { url: startUrl },
    })).result;
    assert.equal(nav.outcome, 'completed');
    return { workspaceId, admin, owner };
  }

  const results = { locAudit, scenarios: {} };

  try {
    // Teach once across all 3 UI arms on ORD-TEACH-1 from Screen 1 (/screen/lookup).
    const teachInputs = {
      orderId: 'ORD-TEACH-1',
      indication: 'bacteremia-mrsa',
      doseTier: 'renal-crcl-45',
      rationale: 'vancomycin-mic-2',
    };
    const dag = new TraceDag(LIMITS);
    const index = new SuffixIndex();
    const book = new AttestedSkillBook();

    {
      seedOrder(db, { orderId: 'ORD-TEACH-1', indication: '', approvalId: 'APP-T1' });
      faultControl.currentOrderId = 'ORD-TEACH-1';
      const { owner } = await openBrowserWorkspace(`${origin}/screen/lookup?orderId=ORD-TEACH-1`);
      store.create({ id: 'teach-graph', goal: 'Stage formulary override' });
      const resG = await runWorkflow({
        dag, mode: 'learn', service, owner, pageId: 'main',
        intent: 'rx:override', template: 'rx:sqlite:v1', goal: 'Stage formulary override',
        accountScope: 'rx-north', recordId: 'ORD-TEACH-1', inputs: teachInputs,
        intermediateClicks, observationLocators: null, includeFormState: true,
        learnRepairs: false, reconvergeMidRepair: false, planner: makeStubPlanner(),
        suffixIndex: index,
        effectForStep: stepCompletionAndEffect('ORD-TEACH-1'),
        task: 'Stage formulary override', config: CLIENT_CONFIG, store, projectId: 'teach-graph',
        verifyReview: async () => {
          const row = db.prepare('SELECT status, dose_tier, rationale FROM formulary_orders WHERE order_id = ?').get('ORD-TEACH-1');
          return { completed: row?.status === 'review-ready' && row.dose_tier === teachInputs.doseTier };
        },
        signal: new AbortController().signal,
      });
      assert.equal(resG.completed, true, `teach-graph failed: ${resG.detail}`);

      seedOrder(db, { orderId: 'ORD-TEACH-2', indication: '', approvalId: 'APP-T2' });
      faultControl.currentOrderId = 'ORD-TEACH-2';
      const teachInputs2 = { ...teachInputs, orderId: 'ORD-TEACH-2' };
      const ws2 = await openBrowserWorkspace(`${origin}/screen/lookup?orderId=ORD-TEACH-2`);
      const rec = recordAttestedSkillTeaching(makeStubPlanner(), { book, accountScope: 'rx-north' });
      store.create({ id: 'teach-skill', goal: 'Stage formulary override' });
      const resS = await runWorkflow({
        dag: new TraceDag(LIMITS), mode: 'learn', service, owner: ws2.owner, pageId: 'main',
        intent: 'rx:override', template: 'rx:sqlite:v1', goal: 'Stage formulary override',
        accountScope: 'rx-north', recordId: 'ORD-TEACH-2', inputs: teachInputs2,
        intermediateClicks, observationLocators: null, includeFormState: true,
        learnRepairs: false, reconvergeMidRepair: false, planner: rec.planner,
        effectForStep: stepCompletionAndEffect('ORD-TEACH-2'),
        task: 'Stage formulary override', config: CLIENT_CONFIG, store, projectId: 'teach-skill',
        verifyReview: async () => {
          const row = db.prepare('SELECT status FROM formulary_orders WHERE order_id = ?').get('ORD-TEACH-2');
          return { completed: row?.status === 'review-ready' };
        },
        signal: new AbortController().signal,
      });
      assert.equal(resS.completed, true);
      rec.commitVerified(await service.observe({ ...ws2.owner, includeFormState: true }), teachInputs2);
    }

    // S1: Mid-entry at /screen/dosing across 3 UI arms + Direct REST Write-API baseline
    const s1 = {};
    for (const arm of ['attested-linear-skill', 'attested-checkpointed-skill', 'gammatron-graph']) {
      const ordId = `ORD-S1-${arm}`;
      const appId = `APP-S1-${arm}`;
      seedOrder(db, { orderId: ordId, indication: 'pneumonia-vre', approvalId: appId, decision: 'approved' });
      faultControl.currentOrderId = ordId;
      activeWriteMode = 'atomic-multi-predicate';
      activeUnavailableApproval = false;
      revokeApprovalAfterCheck = false;
      bumpOrderAfterCheck = false;
      resetCounters();

      const { owner } = await openBrowserWorkspace(`${origin}/screen/dosing?orderId=${encodeURIComponent(ordId)}`);
      const runInputs = { orderId: ordId, indication: 'pneumonia-vre', doseTier: 'renal-crcl-30', rationale: 'linezolid-stepdown' };
      let turns = 0;
      const baseStub = makeStubPlanner();
      const countedStub = { identity: baseStub.identity, next: (...a) => { turns += 1; return baseStub.next(...a); } };
      const attestFn = async ({ skipped }) => hostVersionedAttest(db, counters, {
        account: 'rx-north',
        orderId: ordId,
        skipped,
      });
      const isSkill = arm !== 'gammatron-graph';
      const skillWrap = isSkill
        ? createAttestedSkillPlanner({
            book: AttestedSkillBook.restore(book.export()),
            planner: countedStub,
            allowSafeJumps: arm === 'attested-checkpointed-skill',
            attestPrerequisites: attestFn,
            recordId: null, // predicates span orderId + approvalId under same accountScope
          })
        : null;
      const pid = `s1-${arm}`;
      store.create({ id: pid, goal: 'Stage formulary override' });
      const t0 = performance.now();
      const res = await runWorkflow({
        dag: arm === 'gammatron-graph' ? TraceDag.restore(dag.export(), LIMITS) : new TraceDag(LIMITS),
        mode: arm === 'gammatron-graph' ? 'reuse' : 'fresh',
        service, owner, pageId: 'main',
        intent: 'rx:override', template: 'rx:sqlite:v1', goal: 'Stage formulary override',
        accountScope: 'rx-north', inputs: runInputs,
        intermediateClicks, observationLocators: null, includeFormState: true,
        learnRepairs: false, reconvergeMidRepair: arm === 'gammatron-graph',
        planner: skillWrap ?? countedStub,
        suffixIndex: arm === 'gammatron-graph' ? SuffixIndex.restore(index.export()).freeze() : null,
        crossScreenRule: arm === 'gammatron-graph',
        attestPrerequisites: attestFn,
        requireConditionalWrite: true,
        requireMultiPredicateWrite: true,
        effectForStep: ({ kind, locator }) => (kind === 'click' && locator[1] === 'Stage Override Review'
          ? {
              effect: { external: true, effectKey: `commit-${ordId}`, externalIdempotencyKey: `idem-${ordId}` },
              completion: { completedWhen: [{ kind: 'element-present', selector: '#review-summary' }] },
            }
          : null),
        task: 'Stage formulary override', config: CLIENT_CONFIG, store, projectId: pid,
        verifyReview: async () => {
          const row = db.prepare('SELECT status, dose_tier, rationale FROM formulary_orders WHERE order_id = ?').get(ordId);
          return { completed: row?.status === 'review-ready' && row.dose_tier === runInputs.doseTier };
        },
        signal: new AbortController().signal,
      });
      const latencyMs = Number((performance.now() - t0).toFixed(2));
      assert.equal(res.completed, true, `${arm} failed S1: ${res.detail}`);
      s1[arm] = {
        completed: res.completed,
        plannerTurns: turns,
        latencyMs,
        sqlPredicateReads: counters.sqlReads,
        commits: counters.commits,
        forbiddenCommits: counters.forbiddenCommits,
      };
    }

    // Direct REST Write-API baseline on the exact same task:
    {
      const ordId = 'ORD-S1-DIRECT-API';
      seedOrder(db, { orderId: ordId, indication: 'pneumonia-vre', approvalId: 'APP-S1-API', decision: 'approved' });
      resetCounters();
      const t0 = performance.now();
      const resp = await fetch(`${origin}/api/v1/formulary-overrides`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', 'idempotency-key': `idem-${ordId}` },
        body: JSON.stringify({
          account: 'rx-north',
          orderId: ordId,
          doseTier: 'renal-crcl-30',
          rationale: 'linezolid-stepdown',
        }),
      });
      const json = await resp.json();
      const latencyMs = Number((performance.now() - t0).toFixed(2));
      assert.equal(resp.status, 200);
      assert.equal(json.ok, true);
      s1['direct-write-api'] = {
        completed: true,
        plannerTurns: 0,
        latencyMs,
        sqlPredicateReads: counters.sqlReads,
        commits: counters.commits,
        forbiddenCommits: 0,
      };
    }
    results.scenarios.validMidEntryAndDirectApi = s1;

    // S2: Concurrent separate-table approval revocation after #checkLiveDispatch:
    //     single-record-etag commits forbidden write vs. atomic-multi-predicate aborts (0 forbidden)!
    const s2 = {};
    for (const mode of ['single-record-etag', 'atomic-multi-predicate']) {
      const ordId = `ORD-S2-${mode}`;
      seedOrder(db, { orderId: ordId, indication: 'meningitis', approvalId: `APP-S2-${mode}`, decision: 'approved' });
      faultControl.currentOrderId = ordId;
      activeWriteMode = mode;
      adapterRef.supportsMultiPredicateWrites = mode === 'atomic-multi-predicate';
      revokeApprovalAfterCheck = true;
      bumpOrderAfterCheck = false;
      resetCounters();

      const { owner } = await openBrowserWorkspace(`${origin}/screen/dosing?orderId=${encodeURIComponent(ordId)}`);
      const runInputs = { orderId: ordId, indication: 'meningitis', doseTier: 'high-dose', rationale: 'cns-penetration' };
      const attestFn = async ({ skipped }) => hostVersionedAttest(db, counters, {
        account: 'rx-north',
        orderId: ordId,
        skipped,
      });
      const pid = `s2-${mode}`;
      store.create({ id: pid, goal: 'Stage formulary override' });
      const res = await runWorkflow({
        dag: TraceDag.restore(dag.export(), LIMITS),
        mode: 'reuse',
        service, owner, pageId: 'main',
        intent: 'rx:override', template: 'rx:sqlite:v1', goal: 'Stage formulary override',
        accountScope: 'rx-north', inputs: runInputs,
        intermediateClicks, observationLocators: null, includeFormState: true,
        learnRepairs: false, reconvergeMidRepair: true,
        planner: makeStubPlanner(),
        suffixIndex: SuffixIndex.restore(index.export()).freeze(),
        crossScreenRule: true,
        attestPrerequisites: attestFn,
        requireConditionalWrite: true,
        requireMultiPredicateWrite: mode === 'atomic-multi-predicate',
        effectForStep: ({ kind, locator }) => (kind === 'click' && locator[1] === 'Stage Override Review'
          ? {
              effect: { external: true, effectKey: `commit-${ordId}`, externalIdempotencyKey: `idem-${ordId}` },
              completion: { completedWhen: [{ kind: 'element-present', selector: '#review-summary' }] },
            }
          : null),
        task: 'Stage formulary override', config: CLIENT_CONFIG, store, projectId: pid,
        verifyReview: async () => ({ completed: false }),
        signal: new AbortController().signal,
      });
      s2[mode] = {
        workflowCompleted: res.completed,
        commits: counters.commits,
        forbiddenCommits: counters.forbiddenCommits,
      };
    }
    assert.equal(s2['single-record-etag'].forbiddenCommits, 1, 'Single ETag must expose separate-table approval race');
    assert.equal(s2['atomic-multi-predicate'].forbiddenCommits, 0, 'Atomic multi-predicate must block separate-table race');
    results.scenarios.separateEntityApprovalRevocationRace = s2;

    // S3: Lost response AFTER SQLite commit -> server-journal reconciliation + deduplicated retry!
    {
      const ordId = 'ORD-S3-LOST-ACK';
      seedOrder(db, { orderId: ordId, indication: 'endocarditis', approvalId: 'APP-S3', decision: 'approved' });
      faultControl.currentOrderId = ordId;
      faultControl.dropNextCommitResponse = true;
      faultControl.throwLostAckAfterClick = true;
      activeWriteMode = 'atomic-multi-predicate';
      adapterRef.supportsMultiPredicateWrites = true;
      revokeApprovalAfterCheck = false;
      bumpOrderAfterCheck = false;
      resetCounters();

      const { owner, admin } = await openBrowserWorkspace(`${origin}/screen/dosing?orderId=${encodeURIComponent(ordId)}`);
      const runInputs = { orderId: ordId, indication: 'endocarditis', doseTier: 'q12h', rationale: 'bactericidal' };
      const attestFn = async ({ skipped }) => hostVersionedAttest(db, counters, {
        account: 'rx-north',
        orderId: ordId,
        skipped,
      });
      store.create({ id: 's3-lost-ack', goal: 'Stage formulary override' });
      const res = await runWorkflow({
        dag: TraceDag.restore(dag.export(), LIMITS),
        mode: 'reuse',
        service, owner, pageId: 'main',
        intent: 'rx:override', template: 'rx:sqlite:v1', goal: 'Stage formulary override',
        accountScope: 'rx-north', inputs: runInputs,
        intermediateClicks, observationLocators: null, includeFormState: true,
        learnRepairs: false, reconvergeMidRepair: true,
        planner: makeStubPlanner(),
        suffixIndex: SuffixIndex.restore(index.export()).freeze(),
        crossScreenRule: true,
        attestPrerequisites: attestFn,
        requireConditionalWrite: true,
        requireMultiPredicateWrite: true,
        effectForStep: ({ kind, locator }) => (kind === 'click' && locator[1] === 'Stage Override Review'
          ? {
              effect: { external: true, effectKey: `commit-${ordId}`, externalIdempotencyKey: `idem-${ordId}` },
              completion: { completedWhen: [{ kind: 'element-present', selector: '#review-summary' }] },
            }
          : null),
        task: 'Stage formulary override', config: CLIENT_CONFIG, store, projectId: 's3-lost-ack',
        verifyReview: async () => ({ completed: false }),
        signal: new AbortController().signal,
      });
      assert.equal(res.completed, false, 'Dropped ack must halt workflow before completion');
      assert.equal(counters.commits, 1, 'Server committed exactly once before dropping ack');

      const inspected = await service.inspect(admin);
      const uncertainAction = inspected.actions.find(a => a.isUncertain);
      assert.ok(uncertainAction, 'Dropped-ack action must be marked uncertain in WorkspaceService journal');

      const reconciled = await service.reconcile({
        ...owner,
        actionId: uncertainAction.actionId,
        method: 'external-idempotency',
      });
      assert.equal(reconciled.isUncertain, false, 'Server journal verified commit without duplicate resubmission');

      // Also verify direct duplicate retry against the server journal with the same idempotency key:
      const dupResp = await fetch(`${origin}/api/v1/formulary-overrides`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', 'idempotency-key': `idem-${ordId}` },
        body: JSON.stringify({
          account: 'rx-north',
          orderId: ordId,
          doseTier: 'q12h',
          rationale: 'bactericidal',
        }),
      });
      const dupJson = await dupResp.json();
      assert.equal(dupJson.deduplicated, true);
      assert.equal(counters.commits, 1, 'Duplicate retry reusing externalIdempotencyKey produced 0 additional commits');
      assert.equal(counters.deduplicatedRetries, 1);

      results.scenarios.lostAckServerJournalDeduplication = {
        haltedOnUncertainAck: !res.completed,
        resolvedViaServerJournal: !reconciled.isUncertain,
        totalSqliteCommits: counters.commits,
        duplicateCommits: 0,
        deduplicatedRetries: counters.deduplicatedRetries,
      };
    }

    // S4: Partial-contract host (`unavailable` predicate + unversioned DOM writes) reported separately:
    {
      const ordId = 'ORD-S4-PARTIAL';
      seedOrder(db, { orderId: ordId, indication: 'osteomyelitis', approvalId: 'APP-S4', decision: 'approved' });
      faultControl.currentOrderId = ordId;
      activeWriteMode = 'unversioned-dom';
      adapterRef.supportsConditionalWrites = false;
      adapterRef.supportsMultiPredicateWrites = false;
      activeUnavailableApproval = true;
      revokeApprovalAfterCheck = false;
      bumpOrderAfterCheck = false;
      resetCounters();

      const { owner, admin } = await openBrowserWorkspace(`${origin}/screen/dosing?orderId=${encodeURIComponent(ordId)}`);
      const runInputs = { orderId: ordId, indication: 'osteomyelitis', doseTier: 'q24h', rationale: 'bone-penetration' };
      let turns = 0;
      const baseStub = makeStubPlanner();
      const countedStub = { identity: baseStub.identity, next: (...a) => { turns += 1; return baseStub.next(...a); } };
      const attestFn = async ({ skipped }) => hostVersionedAttest(db, counters, {
        account: 'rx-north',
        orderId: ordId,
        skipped,
        unavailableApproval: true,
      });
      store.create({ id: 's4-partial', goal: 'Stage formulary override' });
      const res = await runWorkflow({
        dag: TraceDag.restore(dag.export(), LIMITS),
        mode: 'reuse',
        service, owner, pageId: 'main',
        intent: 'rx:override', template: 'rx:sqlite:v1', goal: 'Stage formulary override',
        accountScope: 'rx-north', inputs: runInputs,
        intermediateClicks, observationLocators: null, includeFormState: true,
        learnRepairs: false, reconvergeMidRepair: false,
        planner: countedStub,
        suffixIndex: SuffixIndex.restore(index.export()).freeze(),
        crossScreenRule: true,
        attestPrerequisites: attestFn,
        requireConditionalWrite: false,
        requireMultiPredicateWrite: false,
        effectForStep: stepCompletionAndEffect(ordId),
        task: 'Stage formulary override', config: CLIENT_CONFIG, store, projectId: 's4-partial',
        verifyReview: async () => {
          const row = db.prepare('SELECT status FROM formulary_orders WHERE order_id = ?').get(ordId);
          return { completed: row?.status === 'review-ready' };
        },
        signal: new AbortController().signal,
      });
      const inspected = await service.inspect(admin);
      const raceDisclosedCount = inspected.actions.filter(
        a => a.kind !== 'navigate' && a.evidence?.unconditionalWriteRaceWindow === true,
      ).length;
      assert.equal(res.completed, true);
      assert.equal((res.suffix?.certified ?? 0), 0, 'Unavailable predicate must refuse automated jump');
      assert.ok((res.unavailablePredicates?.length ?? 0) >= 1, 'Unavailable predicate must be reported');
      assert.ok(raceDisclosedCount >= 1, 'Unversioned DOM write must disclose unconditionalWriteRaceWindow');

      results.scenarios.partialContractUnavailableAndUnversioned = {
        completedViaPlannerFallback: res.completed,
        plannerTurns: turns,
        automatedCertifications: res.suffix?.certified ?? 0,
        unavailablePredicatesReported: res.unavailablePredicates?.length ?? 0,
        unconditionalWriteRaceWindowActions: raceDisclosedCount,
      };
    }
  } finally {
    store.close();
    await service.close();
    await new Promise(resolveClose => server.close(resolveClose));
    db.close();
    rmSync(root, { recursive: true, force: true });
  }

  const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../../../..');
  const git = (...args) => execFileSync('git', args, { cwd: repo, encoding: 'utf8' }).trim();
  const receipt = {
    schema: 'host-contract-benchmark/v1',
    source: {
      commit: git('rev-parse', 'HEAD'),
      dirty: Boolean(git('status', '--porcelain', '--ignore-submodules=all')),
    },
    ...results,
  };
  if (outPath) writeFileSync(resolve(outPath), JSON.stringify(receipt, null, 2) + '\n');
  return receipt;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const outArg = process.argv[2] ?? null;
  const receipt = await runHostContractBenchmark(outArg);
  console.log(JSON.stringify(receipt, null, 2));
}
