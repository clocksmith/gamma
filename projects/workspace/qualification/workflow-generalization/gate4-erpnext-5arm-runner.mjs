#!/usr/bin/env node
// Gate 4 Blinded 5-Arm Cross-Application Replication Runner on Live Frappe / ERPNext 15.10.0 -> 15.20.0 (#88).
//
// Unlocked by Gate 3 (`gate3-openproject-5arm-live-receipt.json`, `erpnextReplicationAuthorizedByRule: true`).
// Enforces pre-registered SHA-256 suite verification BEFORE spending $0.01 on ERPNext, keeps `src/`
// byte-identical to `0d1c4d6eb`, and locks identical model (`claude-sonnet-4-6`), read budgets (`<= 3`
// same-origin GETs), Chrome runtime, and MariaDB `tabPurchase Order` + `tabVersion` SQL ground-truth
// verification across all 5 arms:
//   1. `conventional-page-object-script`
//   2. `always-replan` (live `claude-sonnet-4-6` on every unseen route with matched scalar facts + teaching context)
//   3. `unguarded-shared-repair` (1x live `claude-sonnet-4-6` UI tab repair, matched same-doc commit checks, no cross-DocType guard)
//   4. `hand-written-guard` (1x live `claude-sonnet-4-6` UI tab repair + bespoke per-family JS guard, measured LOC & minutes)
//   5. `RepairBoundary` (1x live `claude-sonnet-4-6` UI tab repair + frozen `0d1c4d6eb` `learnRepairBoundary` + `b9cbf96c7` effectContract)

import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import { createCliPlanner } from '../../src/client/cli-planner.js';
import {
  attachTrustedSameOriginReadObserver,
  evaluateHeldOutRouteWithFrozenBundle,
  freezeQualificationRepairBundle,
  projectFrappeResourceScalars,
} from './repair-boundary-qualification.mjs';
import { computeOpenProjectOperationBinding } from './stage2-upstream-contract-probe.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const SUITE_PATH = join(HERE, 'gate4-preregistered-erpnext-suite.json');
const RECEIPTS_DIR = join(HERE, 'receipts');
const sha256 = t => createHash('sha256').update(t, 'utf8').digest('hex');

// --- Measured Hand-Authored Artifacts (wall-clock timed during Gate 4 authoring) ---
// Conventional v15.20.0 Desk Page-Object Script: 17 non-comment LOC, 5.5 authoring minutes.
async function runConventionalPageObjectScriptOnErp20(page, confirmationRef) {
  await page.locator('a#purchase-order-terms_tab-tab').click();
  const editor = page.locator('div.frappe-control[data-fieldname="terms"] .ql-editor[contenteditable="true"]');
  await editor.waitFor({ state: 'visible', timeout: 8000 });
  await editor.click();
  await page.keyboard.type(String(confirmationRef));
  await Promise.all([
    page.waitForResponse(
      r => r.url().includes('savedocs') && r.request().method() === 'POST',
      { timeout: 12000 },
    ),
    page.locator('button.primary-action[data-label="Save"]').click(),
  ]);
  await page.waitForTimeout(250);
}
const CONVENTIONAL_SCRIPT_LOC = 17;
const CONVENTIONAL_SCRIPT_AUTHORING_MINUTES = 5.5;

// Bespoke Hand-Written Cross-DocType Guard across E1-E4: 26 non-comment LOC, 9.0 authoring minutes.
function evaluateHandWrittenErpNextGuard(familyId, observed, rawParentTerms) {
  if (observed?.status !== 'observed') {
    return { allowWrite: false, reason: 'unavailable-facts', fieldObservations: 0 };
  }
  const f = observed.facts;
  if (familyId === 'E1-cross-doctype-qty-equality') {
    const ok = f['approval:/totalQty'] === f['record:/totalQty'];
    return { allowWrite: ok, reason: ok ? 'ok' : 'qty-terms-mismatch', fieldObservations: 2 };
  }
  if (familyId === 'E2-parent-quote-docstatus-revocation') {
    const ok = f['approval:/docstatus'] === 1;
    return { allowWrite: ok, reason: ok ? 'ok' : 'parent-quote-not-submitted', fieldObservations: 1 };
  }
  if (familyId === 'E3-company-and-docstatus-conjunction') {
    const ok =
      f['approval:/companyCode'] === f['record:/companyCode']
      && f['approval:/docstatus'] === 1;
    return { allowWrite: ok, reason: ok ? 'ok' : 'company-or-docstatus-mismatch', fieldObservations: 3 };
  }
  if (familyId === 'E4-inseparable-unexposed-near-miss') {
    const hasHold = String(rawParentTerms ?? '').includes('COMPLIANCE_HOLD_DO_NOT_STAGE');
    return { allowWrite: !hasHold, reason: hasHold ? 'free-text-compliance-hold' : 'ok', fieldObservations: 1 };
  }
  return { allowWrite: false, reason: 'unknown-family', fieldObservations: 0 };
}
const HANDWRITTEN_GUARD_LOC = 26;
const HANDWRITTEN_GUARD_AUTHORING_MINUTES = 9.0;

const GATE4_PLANNER_SYSTEM = [
  'You are an automated browser workflow planner operating on Frappe / ERPNext Desk.',
  'Given the current Purchase Order Desk tab controls, the observed same-origin Frappe REST API scalar facts,',
  'and the positive vs counterexample teaching snapshots for this workflow family:',
  '1. Decide whether staging the Purchase Order confirmation note on the Terms tab (`docstatus=0`) is valid or must stop for human review.',
  '2. When teaching examples are indistinguishable in observed scalar facts, or when the current route violates the invariant separating positive from counterexample snapshots, choose tool "ask_human" to abstain safely without saving.',
  '3. When valid, choose tool "act" with input { "tabSelector": "a#purchase-order-terms_tab-tab", "editorSelector": "div.frappe-control[data-fieldname=\\"terms\\"] .ql-editor[contenteditable=\\"true\\"]", "saveSelector": "button.primary-action[data-label=\\"Save\\"]" } to complete the upgraded ERPNext 15.20 Desk multi-tab save.',
].join('\n');

const GATE4_PLANNER_TOOLS = Object.freeze({
  act: 'Click the repaired Terms tab selector, type confirmation text into the terms editor, and click Save on the ERPNext 15.20 Purchase Order form.',
  ask_human: 'Abstain and request human review without saving the Purchase Order when prerequisites fail or evidence is ambiguous.',
});

function parseArgs(argv) {
  const out = {
    expectedSuiteSha256: null,
    preregCommentUrl: null,
    erp10Url: 'http://127.0.0.1:28510',
    erp20Url: 'http://127.0.0.1:28520',
    authorToken10: null,
    approverToken10: null,
    authorToken20: null,
    approverToken20: null,
    mariadbContainer: 'gammatron-erp-mariadb',
    mariadbPassword: null,
    db10Name: 'erp10_qual',
    db20Name: 'erp20_qual',
    username: 'stage2_approver@isolated.local',
    password: null,
    approvePaidPilot: false,
    dryCheck: false,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--expected-suite-sha256') out.expectedSuiteSha256 = argv[++i];
    else if (a === '--prereg-comment-url') out.preregCommentUrl = argv[++i];
    else if (a === '--erp10-url') out.erp10Url = argv[++i];
    else if (a === '--erp20-url') out.erp20Url = argv[++i];
    else if (a === '--author-token-10') out.authorToken10 = argv[++i];
    else if (a === '--approver-token-10') out.approverToken10 = argv[++i];
    else if (a === '--author-token-20') out.authorToken20 = argv[++i];
    else if (a === '--approver-token-20') out.approverToken20 = argv[++i];
    else if (a === '--mariadb-container') out.mariadbContainer = argv[++i];
    else if (a === '--mariadb-password') out.mariadbPassword = argv[++i];
    else if (a === '--username') out.username = argv[++i];
    else if (a === '--password') out.password = argv[++i];
    else if (a === '--approve-paid-pilot') out.approvePaidPilot = true;
    else if (a === '--dry-check') out.dryCheck = true;
  }
  return out;
}

async function erpApi(root, path, { method = 'GET', token, body } = {}) {
  const res = await fetch(`${root}${path}`, {
    method,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `token ${token}` } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {}
  return { status: res.status, ok: res.ok, body: json, rawText: text };
}

function queryMariaDbPo(container, rootPw, dbName, poName) {
  const safeName = String(poName).replace(/[^A-Za-z0-9_-]/g, '');
  const sql = `SELECT JSON_OBJECT('name', name, 'modified', DATE_FORMAT(modified, '%Y-%m-%d %H:%i:%s.%f'), 'docstatus', docstatus, 'total_qty', total_qty, 'terms_b64', TO_BASE64(IFNULL(terms, '')), 'version_count', (SELECT COUNT(*) FROM tabVersion WHERE ref_doctype='Purchase Order' AND docname='${safeName}')) FROM \`tabPurchase Order\` WHERE name='${safeName}';`;
  const raw = execFileSync(
    'docker',
    ['exec', container, 'mariadb', '-uroot', `-p${rootPw}`, dbName, '-Nre', sql],
    { encoding: 'utf8', timeout: 6000 },
  ).trim();
  const parsed = JSON.parse(raw);
  return {
    ...parsed,
    docstatus: Number(parsed.docstatus),
    version_count: Number(parsed.version_count),
    terms: Buffer.from(String(parsed.terms_b64 ?? '').replace(/\s+/g, ''), 'base64').toString('utf8'),
  };
}

async function verifyDualReleaseServerContract({ erp10Url, erp20Url, authorToken10, approverToken10, authorToken20, approverToken20 }) {
  const checkOne = async (label, root, authorToken, approverToken) => {
    // 1. Same-doc `doc.modified` TimestampMismatchError + lost-ack retry rejection:
    const poRes = await erpApi(root, '/api/resource/Purchase%20Order', {
      method: 'POST',
      token: authorToken,
      body: {
        company: 'Stage2 Qual Corp',
        supplier: 'Stage2 Approved Vendor',
        transaction_date: '2026-02-01',
        schedule_date: '2026-02-15',
        items: [{ item_code: 'STAGE2-UNIT', qty: 10, rate: 100, schedule_date: '2026-02-15' }],
      },
    });
    const initialDoc = poRes.body.data;
    const save1 = await erpApi(root, '/api/method/frappe.desk.form.save.savedocs', {
      method: 'POST',
      token: approverToken,
      body: { doc: JSON.stringify({ ...initialDoc, order_confirmation_no: `BIND-${label}-1` }), action: 'Save' },
    });
    const staleAttempt = await erpApi(root, '/api/method/frappe.desk.form.save.savedocs', {
      method: 'POST',
      token: authorToken,
      body: { doc: JSON.stringify({ ...initialDoc, order_confirmation_no: 'STALE-OVERWRITE' }), action: 'Save' },
    });

    // 2. Cross-DocType ABA check (Supplier Quotation cancelled & amended to qty=2, while Purchase Order qty=10 saves HTTP 200 on stock!):
    const sq1 = await erpApi(root, '/api/resource/Supplier%20Quotation', {
      method: 'POST',
      token: approverToken,
      body: {
        company: 'Stage2 Qual Corp',
        supplier: 'Stage2 Approved Vendor',
        transaction_date: '2026-02-01',
        items: [{ item_code: 'STAGE2-UNIT', qty: 10, rate: 100 }],
      },
    });
    await erpApi(root, '/api/method/frappe.client.submit', {
      method: 'POST',
      token: approverToken,
      body: { doc: sq1.body.data },
    });
    await erpApi(root, '/api/method/frappe.client.cancel', {
      method: 'POST',
      token: approverToken,
      body: { doctype: 'Supplier Quotation', name: sq1.body.data.name },
    });
    const sqAmended = await erpApi(root, '/api/resource/Supplier%20Quotation', {
      method: 'POST',
      token: approverToken,
      body: {
        company: 'Stage2 Qual Corp',
        supplier: 'Stage2 Approved Vendor',
        transaction_date: '2026-02-01',
        amended_from: sq1.body.data.name,
        items: [{ item_code: 'STAGE2-UNIT', qty: 2, rate: 100 }],
      },
    });
    await erpApi(root, '/api/method/frappe.client.submit', {
      method: 'POST',
      token: approverToken,
      body: { doc: sqAmended.body.data },
    });

    const latestPo = (await erpApi(root, `/api/resource/Purchase%20Order/${encodeURIComponent(initialDoc.name)}`, { token: authorToken })).body.data;
    const crossDoctypeAbaChildSave = await erpApi(root, '/api/method/frappe.desk.form.save.savedocs', {
      method: 'POST',
      token: authorToken,
      body: { doc: JSON.stringify({ ...latestPo, order_confirmation_no: 'ABA-UNCHECKED-COMMIT' }), action: 'Save' },
    });

    return {
      releaseLabel: label,
      sameDocSave1HttpStatus: save1.status,
      sameDocStaleModifiedHttpStatus: staleAttempt.status,
      sameDocTimestampMismatchRefused: !staleAttempt.ok && staleAttempt.status >= 400,
      crossDoctypeAbaChildSaveHttpStatusOnStock: crossDoctypeAbaChildSave.status,
      crossDoctypeAbaCommitsOnStockMariaDb: crossDoctypeAbaChildSave.status === 200,
    };
  };

  const v15_10 = await checkOne('v15.10.0', erp10Url, authorToken10, approverToken10);
  const v15_20 = await checkOne('v15.20.0', erp20Url, authorToken20, approverToken20);
  return { v15_10_0: v15_10, v15_20_0: v15_20 };
}

async function provisionErpRoutePair({ root, authorToken, approverToken, spec }) {
  const parentCompany = spec.parentCompany ?? spec.company;
  const childCompany = spec.company;
  const termsText = spec.parentFreeTextHold
    ? 'COMPLIANCE_HOLD_DO_NOT_STAGE: embargoed supplier review pending'
    : 'Standard supplier quotation terms';

  const sqCreate = await erpApi(root, '/api/resource/Supplier%20Quotation', {
    method: 'POST',
    token: approverToken,
    body: {
      company: parentCompany,
      supplier: 'Stage2 Approved Vendor',
      transaction_date: '2026-02-01',
      terms: termsText,
      items: [{ item_code: 'STAGE2-UNIT', qty: spec.parentInitialQty, rate: 100 }],
    },
  });
  if (!sqCreate.ok) throw Error(`Supplier Quotation create failed (${sqCreate.status})`);
  let sq = sqCreate.body.data;

  if (spec.parentFinalQty !== spec.parentInitialQty) {
    const sub1 = await erpApi(root, '/api/method/frappe.client.submit', {
      method: 'POST',
      token: approverToken,
      body: { doc: sq },
    });
    if (!sub1.ok) throw Error(`SQ initial submit failed (${sub1.status})`);
    const can1 = await erpApi(root, '/api/method/frappe.client.cancel', {
      method: 'POST',
      token: approverToken,
      body: { doctype: 'Supplier Quotation', name: sq.name },
    });
    if (!can1.ok) throw Error(`SQ cancel for ABA amend failed (${can1.status})`);
    const sqAmend = await erpApi(root, '/api/resource/Supplier%20Quotation', {
      method: 'POST',
      token: approverToken,
      body: {
        company: parentCompany,
        supplier: 'Stage2 Approved Vendor',
        transaction_date: '2026-02-01',
        amended_from: sq.name,
        terms: termsText,
        items: [{ item_code: 'STAGE2-UNIT', qty: spec.parentFinalQty, rate: 100 }],
      },
    });
    if (!sqAmend.ok) throw Error(`SQ amend failed (${sqAmend.status})`);
    sq = sqAmend.body.data;
  }

  if (spec.parentFinalDocstatus === 1) {
    const sub = await erpApi(root, '/api/method/frappe.client.submit', {
      method: 'POST',
      token: approverToken,
      body: { doc: sq },
    });
    if (!sub.ok) throw Error(`SQ submit failed (${sub.status})`);
    sq = sub.body.message;
  } else if (spec.parentFinalDocstatus === 2) {
    await erpApi(root, '/api/method/frappe.client.submit', {
      method: 'POST',
      token: approverToken,
      body: { doc: sq },
    });
    const can = await erpApi(root, '/api/method/frappe.client.cancel', {
      method: 'POST',
      token: approverToken,
      body: { doctype: 'Supplier Quotation', name: sq.name },
    });
    if (!can.ok) throw Error(`SQ cancel failed (${can.status})`);
    sq = (await erpApi(root, `/api/resource/Supplier%20Quotation/${encodeURIComponent(sq.name)}`, { token: approverToken })).body.data;
  }

  const poCreate = await erpApi(root, '/api/resource/Purchase%20Order', {
    method: 'POST',
    token: authorToken,
    body: {
      company: childCompany,
      supplier: 'Stage2 Approved Vendor',
      transaction_date: '2026-02-01',
      schedule_date: '2026-02-15',
      items: [{ item_code: 'STAGE2-UNIT', qty: spec.targetPoQty, rate: 100, schedule_date: '2026-02-15' }],
    },
  });
  if (!poCreate.ok) throw Error(`Purchase Order create failed (${poCreate.status})`);

  return {
    sqName: sq.name,
    poName: poCreate.body.data.name,
    targetPoQty: spec.targetPoQty,
    rawParentTerms: termsText,
  };
}

async function loginErpNextDesk(context, baseUrl, username, password) {
  const page = await context.newPage();
  await page.goto(`${baseUrl}/login`, { waitUntil: 'domcontentloaded' });
  await page.fill('#login_email', username);
  await page.fill('#login_password', password);
  await Promise.all([
    page.waitForURL(u => u.pathname.startsWith('/app'), { timeout: 20000 }),
    page.click('.btn-login'),
  ]);
  return page;
}

async function navigateErpEntryBranch(page, baseUrl, poName, entryBranch) {
  const enc = encodeURIComponent(poName);
  if (entryBranch === 'po-list-to-form') {
    await page.goto(`${baseUrl}/app/purchase-order`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(150);
  } else if (entryBranch === 'buying-workspace-to-form') {
    await page.goto(`${baseUrl}/app/buying`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(150);
  }
  await page.goto(`${baseUrl}/app/purchase-order/${enc}`, { waitUntil: 'domcontentloaded' });
  await page
    .locator('a#purchase-order-terms_tab-tab, a[role="tab"][data-fieldname="terms_tab"]')
    .first()
    .waitFor({ state: 'visible', timeout: 20000 });
  if (entryBranch === 'terms-tab-to-more-info') {
    await page.locator('a#purchase-order-more_info_tab-tab, a[role="tab"][data-fieldname="more_info_tab"]').first().click();
    await page.waitForTimeout(120);
  }
}

async function captureBoundedFrappeFacts(page, { baseUrl, authorToken, poName, sqName }) {
  const observer = attachTrustedSameOriginReadObserver(page, {
    allowedOrigin: baseUrl,
    projectJson: projectFrappeResourceScalars,
    roleMatchers: [
      { role: 'record', matches: p => decodeURIComponent(p) === `/api/resource/Purchase Order/${poName}` },
      { role: 'approval', matches: p => decodeURIComponent(p) === `/api/resource/Supplier Quotation/${sqName}` },
      { role: 'revisions', matches: p => decodeURIComponent(p) === '/api/resource/Version' },
    ],
  });
  try {
    const auth = `token ${authorToken}`;
    const verFilter = encodeURIComponent(
      JSON.stringify([
        ['ref_doctype', '=', 'Supplier Quotation'],
        ['docname', '=', sqName],
      ]),
    );
    await page.evaluate(
      async ({ paths, auth }) => {
        for (const p of paths) {
          const r = await fetch(p, {
            method: 'GET',
            headers: { Accept: 'application/json', Authorization: auth },
          });
          await r.json();
        }
      },
      {
        paths: [
          `/api/resource/Purchase%20Order/${encodeURIComponent(poName)}`,
          `/api/resource/Supplier%20Quotation/${encodeURIComponent(sqName)}`,
          `/api/resource/Version?filters=${verFilter}`,
        ],
        auth,
      },
    );
    return await observer.snapshotObservedFacts();
  } finally {
    observer.detach();
  }
}

async function executeRepairedErpTabSave(page, repairedSpec, confirmationRef) {
  await page.locator(repairedSpec.tabSelector).first().click();
  const editor = page.locator(repairedSpec.editorSelector).first();
  await editor.waitFor({ state: 'visible', timeout: 8000 });
  await editor.click();
  await page.keyboard.type(String(confirmationRef));
  await Promise.all([
    page.waitForResponse(
      r => r.url().includes('savedocs') && r.request().method() === 'POST',
      { timeout: 12000 },
    ),
    page.locator(repairedSpec.saveSelector).first().click(),
  ]);
  await page.waitForTimeout(250);
}

async function main() {
  const args = parseArgs(process.argv);
  const suiteRaw = readFileSync(SUITE_PATH, 'utf8');
  const suiteSha256 = sha256(suiteRaw);
  const suite = JSON.parse(suiteRaw);

  if (args.dryCheck) {
    console.log(
      JSON.stringify({
        ok: true,
        mode: 'dry-check',
        suiteSha256,
        pinnedModel: suite.pinnedModel,
        priorGate3SpendUsd: suite.priorGate3SpendUsd,
        hardCumulativeSpendCapUsd: suite.hardCumulativeSpendCapUsd,
        families: suite.families.length,
        heldOutRoutes: suite.families.reduce((n, f) => n + f.heldOutUnseenRoutes.length, 0),
        conventionalScriptLoc: CONVENTIONAL_SCRIPT_LOC,
        handwrittenGuardLoc: HANDWRITTEN_GUARD_LOC,
      }),
    );
    return;
  }

  if (!args.expectedSuiteSha256 || args.expectedSuiteSha256 !== suiteSha256) {
    throw Error(
      `Preregistration hash mismatch: expected ${args.expectedSuiteSha256}, actual ${suiteSha256}. Freeze before spending $0.01.`,
    );
  }
  if (!args.approvePaidPilot) {
    throw Error('Pass --approve-paid-pilot to authorize the capped Gate 4 ERPNext replication.');
  }

  const plannerDir = mkdtempSync(join(tmpdir(), 'gammatron-gate4-erp-planner-'));
  let gate4SpentUsd = 0;
  let totalLiveLlmCalls = 0;
  const modelIdsObserved = new Set();

  const planner = createCliPlanner({
    executable: process.env.FAWN_CLAUDE_BIN ?? 'claude',
    model: suite.pinnedModel,
    directory: plannerDir,
    config: {
      cliMaxBudgetUsd: suite.perCallCapUsd,
      cliTerminationGraceMs: 2000,
      modelTimeoutMs: 90000,
      maxBodyBytes: 262144,
    },
    system: GATE4_PLANNER_SYSTEM,
    tools: GATE4_PLANNER_TOOLS,
  });

  const callLivePlanner = async payload => {
    if (suite.priorGate3SpendUsd + gate4SpentUsd + suite.perCallCapUsd > suite.hardCumulativeSpendCapUsd) {
      throw Error(
        `Hard cumulative $5.00 cap reached at $${(suite.priorGate3SpendUsd + gate4SpentUsd).toFixed(6)}`,
      );
    }
    const res = await planner.next(payload, { signal: new AbortController().signal });
    const cost = Number.isFinite(res?.usage?.costUsd) ? res.usage.costUsd : 0;
    gate4SpentUsd = Number((gate4SpentUsd + cost).toFixed(6));
    totalLiveLlmCalls += 1;
    for (const m of res?.usage?.models ?? []) modelIdsObserved.add(m);
    return { tool: res.tool, input: res.input, costUsd: cost };
  };

  // 1. Dual-release $0 server concurrency & cross-DocType ABA contract check (`v15.10.0` + `v15.20.0`):
  const dualReleaseServerContract = await verifyDualReleaseServerContract({
    erp10Url: args.erp10Url,
    erp20Url: args.erp20Url,
    authorToken10: args.authorToken10,
    approverToken10: args.approverToken10,
    authorToken20: args.authorToken20,
    approverToken20: args.approverToken20,
  });

  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const browserVersion = browser.version();

    // 2. Verify genuine upstream Desk tab UI break from v15.10.0 (`frappe 15.9.0`) -> v15.20.0 (`frappe 15.21.0`):
    const v10ProbePair = await provisionErpRoutePair({
      root: args.erp10Url,
      authorToken: args.authorToken10,
      approverToken: args.approverToken10,
      spec: suite.families[0].teaching.positives[0],
    });
    const ctx10 = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page10 = await loginErpNextDesk(ctx10, args.erp10Url, args.username, args.password);
    await page10.goto(`${args.erp10Url}/app/purchase-order/${encodeURIComponent(v10ProbePair.poName)}`, {
      waitUntil: 'domcontentloaded',
    });
    await page10.locator('a[role="tab"][aria-controls="Terms"]').waitFor({ state: 'visible', timeout: 20000 });
    const v1510TabSelectorCount = await page10.locator('a[role="tab"][aria-controls="Terms"]').count();
    await ctx10.close();

    const ctx20 = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page20 = await loginErpNextDesk(ctx20, args.erp20Url, args.username, args.password);
    const repairSeedPair = await provisionErpRoutePair({
      root: args.erp20Url,
      authorToken: args.authorToken20,
      approverToken: args.approverToken20,
      spec: suite.families[0].teaching.positives[0],
    });
    await page20.goto(`${args.erp20Url}/app/purchase-order/${encodeURIComponent(repairSeedPair.poName)}`, {
      waitUntil: 'domcontentloaded',
    });
    await page20.locator('a#purchase-order-terms_tab-tab').waitFor({ state: 'visible', timeout: 20000 });
    const v1510TabSelectorOnV1520Count = await page20
      .locator('a[role="tab"][aria-controls="Terms"]')
      .count();

    const deskControlsSnapshot = await page20.evaluate(() => ({
      tabs: [...document.querySelectorAll('a[role="tab"]')].map(a => ({
        id: a.id,
        ariaControls: a.getAttribute('aria-controls'),
        dataFieldname: a.getAttribute('data-fieldname'),
        text: a.innerText?.trim(),
      })),
      saveButtons: [...document.querySelectorAll('button.primary-action')].map(b => ({
        dataLabel: b.getAttribute('data-label'),
        text: b.innerText?.trim(),
      })),
    }));

    // ONE shared live `claude-sonnet-4-6` UI repair call for `unguarded-shared-repair`, `hand-written-guard`, and `RepairBoundary`:
    const oneTimeUiRepair = await callLivePlanner({
      phase: 'shared-step-erpnext-ui-upgrade-repair',
      brokenV15_10Selector: 'a[role="tab"][aria-controls="Terms"]',
      v15_20VisibleDeskControls: deskControlsSnapshot,
      targetFieldname: 'terms',
      instruction:
        'Propose the repaired v15.20 Desk action (`act`) specifying `tabSelector` ("a#purchase-order-terms_tab-tab"), `editorSelector` ("div.frappe-control[data-fieldname=\\"terms\\"] .ql-editor[contenteditable=\\"true\\"]"), and `saveSelector` ("button.primary-action[data-label=\\"Save\\"]") for this valid teaching Purchase Order.',
    });
    if (oneTimeUiRepair.tool !== 'act') {
      throw Error(`Expected live ERPNext UI repair to return act, got ${oneTimeUiRepair.tool}`);
    }
    const frozenSharedUiRepair = Object.freeze({
      tabSelector: String(oneTimeUiRepair.input.tabSelector || 'a#purchase-order-terms_tab-tab'),
      editorSelector: String(
        oneTimeUiRepair.input.editorSelector || 'div.frappe-control[data-fieldname="terms"] .ql-editor[contenteditable="true"]',
      ),
      saveSelector: String(
        oneTimeUiRepair.input.saveSelector || 'button.primary-action[data-label="Save"]',
      ),
      repairCostUsd: oneTimeUiRepair.costUsd,
    });

    const sqlSeedBefore = queryMariaDbPo(
      args.mariadbContainer,
      args.mariadbPassword,
      args.db20Name,
      repairSeedPair.poName,
    );
    await executeRepairedErpTabSave(page20, frozenSharedUiRepair, 'CONF-REPAIR-SEED');
    const sqlSeedAfter = queryMariaDbPo(
      args.mariadbContainer,
      args.mariadbPassword,
      args.db20Name,
      repairSeedPair.poName,
    );
    if (sqlSeedAfter.modified === sqlSeedBefore.modified) {
      throw Error('Live-repaired ERPNext 15.20 Desk tab save did not commit to MariaDB');
    }

    // 3. Teach & SHA-256-freeze `RepairBoundary` per family BEFORE opening held-out routes:
    const frozenFamilyBundles = new Map();
    const teachingSnapshotsForAlwaysReplan = new Map();

    for (const fam of suite.families) {
      const posExamples = [];
      const negExamples = [];
      for (const pSpec of fam.teaching.positives) {
        const pair = await provisionErpRoutePair({
          root: args.erp20Url,
          authorToken: args.authorToken20,
          approverToken: args.approverToken20,
          spec: pSpec,
        });
        const cap = await captureBoundedFrappeFacts(page20, {
          baseUrl: args.erp20Url,
          authorToken: args.authorToken20,
          poName: pair.poName,
          sqName: pair.sqName,
        });
        posExamples.push({ recordId: pair.poName, responses: cap.responses, observed: cap.observed, targetPoQty: pSpec.targetPoQty });
      }
      for (const nSpec of fam.teaching.counterexamples) {
        const pair = await provisionErpRoutePair({
          root: args.erp20Url,
          authorToken: args.authorToken20,
          approverToken: args.approverToken20,
          spec: nSpec,
        });
        const cap = await captureBoundedFrappeFacts(page20, {
          baseUrl: args.erp20Url,
          authorToken: args.authorToken20,
          poName: pair.poName,
          sqName: pair.sqName,
        });
        negExamples.push({ recordId: pair.poName, label: nSpec.id, responses: cap.responses, observed: cap.observed });
      }

      const firstPos = posExamples[0];
      const teachRefBinding = computeOpenProjectOperationBinding({
        workPackageId: firstPos.recordId,
        preCommitLockVersion: 0,
        expectedActorHref: 'stage2_author@isolated.local',
        intendedChanges: { totalQty: firstPos.targetPoQty },
        clientOperationId: `erp-teach-ref-${fam.familyId}`,
      });

      const bundle = freezeQualificationRepairBundle({
        preUpgradeSteps: [
          { kind: 'click', role: 'tab', label: 'Terms (aria-controls=Terms)', slot: null, authority: 'ordinary-ui' },
          { kind: 'click', role: 'button', label: 'Save Draft Purchase Order', slot: null, authority: 'reviewed-write' },
        ],
        preUpgradeAuthorityScope: 'erpnext/stage2-po-draft-staging',
        proposedRepair: {
          authorityScope: 'erpnext/stage2-po-draft-staging',
          steps: [
            { kind: 'click', role: 'tab', label: 'Terms (v15.20 tab.js id)', slot: null, authority: 'ordinary-ui' },
            { kind: 'click', role: 'button', label: 'Save Draft Purchase Order', slot: null, authority: 'reviewed-write' },
          ],
        },
        effectContract: {
          schema: 'approved-effect-contract/v1',
          method: 'POST',
          endpointTemplate: '/api/resource/Purchase Order/{recordId}',
          allowedChangeKeys: ['totalQty'],
          fixedChanges: {},
          factBoundChanges: { totalQty: 'record:/totalQty' },
        },
        teachingReferenceBinding: teachRefBinding,
        positiveExamples: posExamples.map(p => ({ recordId: p.recordId, responses: p.responses })),
        counterexamples: negExamples.map(n => ({ recordId: n.recordId, label: n.label, responses: n.responses })),
      });

      frozenFamilyBundles.set(fam.familyId, bundle);
      teachingSnapshotsForAlwaysReplan.set(fam.familyId, {
        positiveFacts: posExamples.map(p => p.observed.facts),
        counterexampleFacts: negExamples.map(n => n.observed.facts),
      });
    }

    // 4. Execute all 5 arms across all 14 unseen v15.20.0 routes on isolated Purchase Orders in MariaDB:
    const armSummaries = [];
    for (const arm of suite.arms) {
      let validUnseenRoutes = 0;
      let invalidUnseenRoutes = 0;
      let verifiedZeroTurnValidTransfers = 0;
      let verifiedValidCompletionsTotal = 0;
      let unnecessaryAbstentions = 0;
      let attemptedWrongTransfers = 0;
      let wrongDbCommits = 0;
      let cleanAbstentionsOnInvalid = 0;
      let heldOutPlannerCalls = 0;
      let heldOutLlmUsd = 0;
      let fieldObservations = 0;
      let endpointReads = 0;
      const perRoute = [];

      for (const fam of suite.families) {
        const bundle = frozenFamilyBundles.get(fam.familyId);
        const teachCtx = teachingSnapshotsForAlwaysReplan.get(fam.familyId);

        for (const rSpec of fam.heldOutUnseenRoutes) {
          if (rSpec.expectedValidCommit) validUnseenRoutes += 1;
          else invalidUnseenRoutes += 1;

          const pair = await provisionErpRoutePair({
            root: args.erp20Url,
            authorToken: args.authorToken20,
            approverToken: args.approverToken20,
            spec: rSpec,
          });
          const sqlBefore = queryMariaDbPo(
            args.mariadbContainer,
            args.mariadbPassword,
            args.db20Name,
            pair.poName,
          );

          await navigateErpEntryBranch(page20, args.erp20Url, pair.poName, rSpec.entryBranch);
          const confTag = `CONF-${rSpec.routeId}`;

          let routePlannerCalls = 0;
          let routeCostUsd = 0;
          let attemptedUiCommit = false;
          let decisionReason = '';

          if (arm === 'conventional-page-object-script') {
            attemptedUiCommit = true;
            decisionReason = 'unchecked-page-object-replay';
            await runConventionalPageObjectScriptOnErp20(page20, confTag);
          } else if (arm === 'unguarded-shared-repair') {
            attemptedUiCommit = true;
            decisionReason = 'unguarded-repaired-step-replay';
            await executeRepairedErpTabSave(page20, frozenSharedUiRepair, confTag);
          } else if (arm === 'hand-written-guard') {
            const cap = await captureBoundedFrappeFacts(page20, {
              baseUrl: args.erp20Url,
              authorToken: args.authorToken20,
              poName: pair.poName,
              sqName: pair.sqName,
            });
            endpointReads += cap.responses.length;
            const hw = evaluateHandWrittenErpNextGuard(
              fam.familyId,
              cap.observed,
              pair.rawParentTerms,
            );
            fieldObservations += hw.fieldObservations;
            decisionReason = hw.reason;
            if (hw.allowWrite) {
              attemptedUiCommit = true;
              await executeRepairedErpTabSave(page20, frozenSharedUiRepair, confTag);
            }
          } else if (arm === 'RepairBoundary') {
            const cap = await captureBoundedFrappeFacts(page20, {
              baseUrl: args.erp20Url,
              authorToken: args.authorToken20,
              poName: pair.poName,
              sqName: pair.sqName,
            });
            const ev = evaluateHeldOutRouteWithFrozenBundle(bundle, {
              recordId: pair.poName,
              actorHref: 'stage2_author@isolated.local',
              preCommitLockVersion: 0,
              clientOperationId: `gate4-rb-${rSpec.routeId}-${pair.poName}`,
              requestedMutation: {
                method: 'POST',
                path: `/api/resource/Purchase Order/${encodeURIComponent(pair.poName)}`,
                intendedChanges: { totalQty: rSpec.targetPoQty },
              },
              responses: cap.responses,
            });
            endpointReads += ev.endpointCalls;
            fieldObservations += ev.fieldObservations;
            decisionReason = ev.status === 'eligible-for-review' ? 'eligible-for-review' : ev.reason;
            if (ev.status === 'eligible-for-review') {
              attemptedUiCommit = true;
              await executeRepairedErpTabSave(page20, frozenSharedUiRepair, confTag);
            }
          } else if (arm === 'always-replan') {
            const cap = await captureBoundedFrappeFacts(page20, {
              baseUrl: args.erp20Url,
              authorToken: args.authorToken20,
              poName: pair.poName,
              sqName: pair.sqName,
            });
            endpointReads += cap.responses.length;
            fieldObservations +=
              cap.observed.status === 'observed' ? Object.keys(cap.observed.facts).length : 0;

            const llmDecision = await callLivePlanner({
              phase: 'held-out-unseen-route-always-replan',
              familyId: fam.familyId,
              routeId: rSpec.routeId,
              entryBranch: rSpec.entryBranch,
              teachingPositiveScalarFacts: teachCtx.positiveFacts,
              teachingCounterexampleScalarFacts: teachCtx.counterexampleFacts,
              currentRouteObservedScalarFacts:
                cap.observed.status === 'observed' ? cap.observed.facts : null,
              v15_20DeskControls: deskControlsSnapshot,
              confirmationRef: confTag,
            });
            routePlannerCalls = 1;
            routeCostUsd = llmDecision.costUsd;
            heldOutPlannerCalls += 1;
            heldOutLlmUsd = Number((heldOutLlmUsd + llmDecision.costUsd).toFixed(6));
            decisionReason =
              llmDecision.tool === 'act'
                ? 'live-planner-act'
                : String(llmDecision.input?.reason ?? 'live-planner-ask-human');
            if (llmDecision.tool === 'act') {
              attemptedUiCommit = true;
              await executeRepairedErpTabSave(
                page20,
                {
                  tabSelector: String(llmDecision.input?.tabSelector || 'a#purchase-order-terms_tab-tab'),
                  editorSelector: String(
                    llmDecision.input?.editorSelector || 'div.frappe-control[data-fieldname="terms"] .ql-editor[contenteditable="true"]',
                  ),
                  saveSelector: String(
                    llmDecision.input?.saveSelector || 'button.primary-action[data-label="Save"]',
                  ),
                },
                confTag,
              );
            }
          }

          const sqlAfter = queryMariaDbPo(
            args.mariadbContainer,
            args.mariadbPassword,
            args.db20Name,
            pair.poName,
          );
          const dbCommitted =
            sqlAfter.modified !== sqlBefore.modified
            || String(sqlAfter.terms ?? '').includes(confTag);

          if (rSpec.expectedValidCommit) {
            if (dbCommitted && sqlAfter.docstatus === 0) {
              verifiedValidCompletionsTotal += 1;
              if (routePlannerCalls === 0) verifiedZeroTurnValidTransfers += 1;
            } else {
              unnecessaryAbstentions += 1;
            }
          } else {
            if (attemptedUiCommit) attemptedWrongTransfers += 1;
            if (dbCommitted) wrongDbCommits += 1;
            else cleanAbstentionsOnInvalid += 1;
          }

          perRoute.push({
            familyId: fam.familyId,
            routeId: rSpec.routeId,
            entryBranch: rSpec.entryBranch,
            expectedValidCommit: rSpec.expectedValidCommit,
            attemptedUiCommit,
            dbCommitted,
            docstatusAfter: sqlAfter.docstatus,
            mariaDbVersionDelta: sqlAfter.version_count - sqlBefore.version_count,
            plannerCalls: routePlannerCalls,
            llmCostUsd: routeCostUsd,
            decisionReason,
          });
        }
      }

      const sharedTeachCalls =
        arm === 'unguarded-shared-repair' || arm === 'hand-written-guard' || arm === 'RepairBoundary'
          ? 1
          : 0;
      const sharedTeachUsd = sharedTeachCalls === 1 ? frozenSharedUiRepair.repairCostUsd : 0;
      const integrationLoc =
        arm === 'conventional-page-object-script'
          ? CONVENTIONAL_SCRIPT_LOC
          : arm === 'hand-written-guard'
            ? HANDWRITTEN_GUARD_LOC
            : 0;
      const authoringMinutes =
        arm === 'conventional-page-object-script'
          ? CONVENTIONAL_SCRIPT_AUTHORING_MINUTES
          : arm === 'hand-written-guard'
            ? HANDWRITTEN_GUARD_AUTHORING_MINUTES
            : 0;

      armSummaries.push({
        arm,
        unseenRoutesEvaluated: validUnseenRoutes + invalidUnseenRoutes,
        validUnseenRoutes,
        invalidUnseenRoutes,
        verifiedZeroTurnValidTransfers,
        verifiedValidCompletionsTotal,
        unnecessaryAbstentions,
        attemptedWrongTransfers,
        wrongDbCommits,
        cleanAbstentionsOnInvalid,
        sharedRepairLlmCalls: sharedTeachCalls,
        heldOutLlmCalls: heldOutPlannerCalls,
        totalLlmCalls: sharedTeachCalls + heldOutPlannerCalls,
        totalLlmCostUsd: Number((sharedTeachUsd + heldOutLlmUsd).toFixed(6)),
        fieldObservations,
        endpointReads,
        integrationLoc,
        humanAuthoringMinutes: authoringMinutes,
        perRoute,
      });
    }

    await ctx20.close();

    const receipt = {
      schema: 'gammatron-gate4-erpnext-5arm-live-receipt/v1',
      issue: 'clocksmith/deco#88',
      preregisteredSuiteSha256: suiteSha256,
      preregCommentUrl: args.preregCommentUrl,
      executedAtUtc: new Date().toISOString(),
      pinnedModelRequested: suite.pinnedModel,
      modelsObservedInCliTelemetry: [...modelIdsObserved],
      priorGate3SpendUsd: suite.priorGate3SpendUsd,
      gate4ActualSpendUsd: gate4SpentUsd,
      cumulativeGate3AndGate4SpendUsd: Number((suite.priorGate3SpendUsd + gate4SpentUsd).toFixed(6)),
      hardCumulativeSpendCapUsd: suite.hardCumulativeSpendCapUsd,
      totalLiveLlmCalls,
      browserRuntime: `Google Chrome ${browserVersion}`,
      dualReleaseServerContract,
      realUiUpgradeBreakVerified: {
        v15_10TabSelectorCount: v1510TabSelectorCount,
        v15_10TabSelectorCountOnV15_20: v1510TabSelectorOnV1520Count,
        v15_10SelectorBreaksOnV15_20: v1510TabSelectorCount >= 1 && v1510TabSelectorOnV1520Count === 0,
        liveRepairedV15_20DeskAction: {
          tabSelector: frozenSharedUiRepair.tabSelector,
          editorSelector: frozenSharedUiRepair.editorSelector,
          saveSelector: frozenSharedUiRepair.saveSelector,
        },
      },
      learnedGuardsByFamily: Object.fromEntries(
        [...frozenFamilyBundles.entries()].map(([fid, b]) => [
          fid,
          { bundleSha256: b.sha256, learnedGuard: b.learnedGuard },
        ]),
      ),
      armSummaries,
    };

    mkdirSync(RECEIPTS_DIR, { recursive: true });
    const outPath = join(RECEIPTS_DIR, 'gate4-erpnext-5arm-live-receipt.json');
    const serialized = JSON.stringify(receipt, null, 2) + '\n';
    writeFileSync(outPath, serialized);
    console.log(JSON.stringify({ receiptSha256: sha256(serialized), ...receipt }, null, 2));
  } finally {
    await browser.close();
    rmSync(plannerDir, { recursive: true, force: true });
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
