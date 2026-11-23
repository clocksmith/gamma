#!/usr/bin/env node
// Screens stock ERPNext releases against the evaluator's rule for a second upgrade
// that bites (second-upgrade-drift-rule.md with its amendments, clocksmith/deco#88).
// Scripted probes only: no model call, no arm, no sealed case. Derived from
// second-upgrade-screen.mjs; it reads the draft ERPNext files and changes none.
//
//   node second-upgrade-screen-erpnext.mjs --receipt FILE --releases v15.50.0,v15.60.0,...
//
// Per release, in the order given: pull the image, bring up v15.20.0 -> release with
// the bring-up script, run check 4 and then check 1. Checks 2 and 3 are needed only
// when check 1 is met and must go through the page with selectors written for that
// release, so the screen stops at the first release that meets check 1. Tears down
// and deletes the release's image. Needs the ERPNext ports.
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import { erpRequester, provisionErpRecipe, readErpState } from './three-arm-erpnext/erp-app.mjs';
import { executeTermsWrite, FROZEN_REPAIR_15_20, loginDesk } from './three-arm-erpnext/erp-write-step.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const FIRST_UPGRADE_TARGET = 'v15.20.0';
const IMAGE = 'frappe/erpnext';
const PLATFORM = 'linux/amd64';
const REPEATS = 3;
const FAMILY = 'example-quotation-covers-order';
let serial = 0;
const recipe = (routeId, quotationQty, submit, orderQty) => ({
  routeId, familyId: FAMILY, entryBranch: 'direct',
  setup: [
    { as: 'approver', method: 'POST', path: '/api/resource/Supplier%20Quotation',
      body: { company: 'Stage2 Qual Corp', supplier: 'Stage2 Approved Vendor', transaction_date: '2026-02-01', items: [{ item_code: 'STAGE2-UNIT', qty: quotationQty, rate: 100 }] },
      save: { quotation: 'data.name', quotationDoc: 'data' } },
    ...(submit ? [{ as: 'approver', method: 'POST', path: '/api/method/frappe.client.submit', body: { doc: '{quotationDoc}' } }] : []),
    { as: 'author', method: 'POST', path: '/api/resource/Purchase%20Order',
      body: { company: 'Stage2 Qual Corp', supplier: 'Stage2 Approved Vendor', transaction_date: '2026-02-01', schedule_date: '2026-02-15',
        items: [{ item_code: 'STAGE2-UNIT', qty: orderQty, rate: 100, schedule_date: '2026-02-15', supplier_quotation: '{quotation}' }] }, save: { order: 'data.name' } },
  ],
  target: { doctype: 'Purchase Order', name: '{order}' }, write: { reference: `SCRN-${String(serial += 1).padStart(4, '0')}` },
});
// The public ERPNext example family: valid when the quotation behind the order is submitted and for the same quantity.
const ROUTES = {
  valid: { recipe: () => recipe('screen-valid', 12, true, 12), valid: true },
  draft: { recipe: () => recipe('screen-lookalike-draft', 12, false, 12), valid: false },
  quantity: { recipe: () => recipe('screen-lookalike-quantity', 5, true, 12), valid: false },
};

const args = process.argv.slice(2);
const option = name => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
const receiptFile = resolve(option('--receipt') ?? '');
const releases = (option('--releases') ?? '').split(',').filter(Boolean);
const reference = option('--reference') ? JSON.parse(option('--reference')) : null;
// Amendment 2: a separate screening seeder may be used where the frozen one cannot build the records.
// The folder holds a byte-identical copy of the frozen bring-up script beside the screening seeder.
const screeningBringUp = option('--screening-bringup') ? resolve(option('--screening-bringup')) : null;
if (!option('--receipt') || !releases.length) { console.error('usage: second-upgrade-screen-erpnext.mjs --receipt FILE --releases tag,tag,...'); process.exit(2); }

const sh = (file, argv = [], options = {}) => execFileSync(file, argv, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], ...options });
const short = error => String(error?.stderr || error?.message || error).trim().split('\n').slice(-2).join(' | ').replaceAll(HERE, '.').slice(0, 400);
const receipt = existsSync(receiptFile) ? JSON.parse(readFileSync(receiptFile, 'utf8')) : {};
receipt.screened ??= [];
const save = () => writeFileSync(receiptFile, JSON.stringify(receipt, null, 1) + '\n');

function cleanUp(tag) {
  try { sh(join(HERE, 'bringup', 'erpnext-down.sh')); } catch { /* nothing to remove */ }
  // Containers are removed without their anonymous volumes; clear those, and only those.
  const dangling = sh('docker', ['volume', 'ls', '-qf', 'dangling=true']).split('\n').filter(name => /^[0-9a-f]{64}$/.test(name));
  for (let i = 0; i < dangling.length; i += 40) { try { sh('docker', ['volume', 'rm', ...dangling.slice(i, i + 40)]); } catch { /* in use */ } }
  if (![FIRST_UPGRADE_TARGET, 'v15.10.0'].includes(tag)) { try { sh('docker', ['rmi', `${IMAGE}:${tag}`]); } catch { /* not present */ } }
}

async function screen(tag) {
  const entry = { release: tag, tag, application: 'erpnext', pair: `${FIRST_UPGRADE_TARGET}->${tag}`,
    startedAt: new Date().toISOString(), image: null, checks: {}, bites: false, note: null };
  try {
    sh('docker', ['pull', '-q', '--platform', PLATFORM, `${IMAGE}:${tag}`], { timeout: 60 * 60 * 1000 });
    entry.image = sh('docker', ['inspect', '--format', '{{index .RepoDigests 0}}', `${IMAGE}:${tag}`]).trim();
  } catch (error) { entry.note = `image could not be pulled: ${short(error)}`; return entry; }
  // The frozen bring-up can lose a race with PostgreSQL's first start (it asks for the databases while the
  // server is restarting after its own initialisation). That says nothing about the release, so a failure that
  // never reached the candidate is retried; one that reached the candidate is tried twice in all.
  const bringUp = dir => {
    const failures = [];
    let reachedCandidate = 0;
    for (let attempt = 1; attempt <= 4 && reachedCandidate < 2; attempt += 1) {
      try {
        sh(join(HERE, 'bringup', 'erpnext-down.sh'));
        sh(join(dir, 'erpnext-up.sh'), [FIRST_UPGRADE_TARGET, tag], { timeout: 40 * 60 * 1000 });
        return { ok: true, failures };
      } catch (error) {
        const out = String(error?.stdout ?? '');
        const atCandidate = out.includes('[gammatron-erp-new] creating site');
        if (atCandidate) reachedCandidate += 1;
        failures.push(`attempt ${attempt}: ${atCandidate ? 'failed after the candidate release was reached' : 'failed before the candidate release was reached'}; ${short(error)}`);
      }
    }
    return { ok: false, failures };
  };
  const frozen = bringUp(join(HERE, 'bringup'));
  if (frozen.failures.length) entry.bringUpFailuresWithFrozenSeeder = frozen.failures;
  if (!frozen.ok) {
    entry.withFrozenSeeder = { casesStillMeanWhatTheySay: { met: false, detail: 'the frozen bring-up or seeder failed on this release' } };
    if (!screeningBringUp) {
      entry.checks.casesStillMeanWhatTheySay = entry.withFrozenSeeder.casesStillMeanWhatTheySay;
      entry.note = 'checks 1 to 3 not run: no seeded instance';
      return entry;
    }
    const adapted = bringUp(screeningBringUp);
    if (adapted.failures.length) entry.bringUpFailuresWithScreeningSeeder = adapted.failures;
    if (!adapted.ok) {
      entry.checks.casesStillMeanWhatTheySay = { met: false, detail: 'the screening seeder also failed on this release' };
      entry.note = 'a further set-up change would be needed on this release: stopped to ask, as amendment 2 requires';
      entry.stopAndAsk = true;
      return entry;
    }
    entry.screenedWithScreeningSeeder = true;
  }
  const state = readErpState();
  const rel = state.new;
  const db = { mariadbContainer: state.mariadbContainer, database: rel.database };
  const request = erpRequester(rel);
  const build = (key, n) => provisionErpRecipe(ROUTES[key].recipe(), { request, tag: `${key}${n}` });
  const documentPath = (doctype, name) => `/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`;
  const liveLabel = async route => {
    const order = (await request('approver', 'GET', documentPath('Purchase Order', route.name))).body?.data;
    const quotationName = order?.items?.[0]?.supplier_quotation;
    const quotation = quotationName ? (await request('approver', 'GET', documentPath('Supplier Quotation', quotationName))).body?.data : null;
    return Boolean(quotation) && quotation.docstatus === 1 && quotation.total_qty === order.total_qty;
  };

  // Check 4: the cases still mean what they say.
  try {
    const labels = [];
    for (const key of Object.keys(ROUTES)) {
      const route = await build(key, 0);
      labels.push({ route: key, intended: ROUTES[key].valid, live: await liveLabel(route) });
    }
    entry.checks.casesStillMeanWhatTheySay = { met: labels.every(l => l.intended === l.live), labels };
  } catch (error) { entry.checks.casesStillMeanWhatTheySay = { met: false, detail: short(error) }; entry.note = 'checks 1 to 3 not run: the public routes could not be built'; return entry; }

  // Check 1: the old workflow fails on a valid case. Met only if the recorded page write commits in 0 of 3.
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    let page = null;
    let signIn = null;
    try { page = await loginDesk(context, rel.url, state.username, state.password); } catch (error) { signIn = `sign-in with the recorded steps failed: ${short(error)}`; }
    const pageWrites = async (key, repair, prefix) => {
      const repeats = [];
      for (let n = 1; page && n <= REPEATS; n += 1) {
        const route = await build(key, `${prefix}${n}`);
        const r = await executeTermsWrite(page, { baseUrl: rel.url, db, route, repair });
        // What was asked and what is stored, so that a write of the wrong value is not read as a clean commit.
        repeats.push({ committed: r.committed, effectMatches: r.effectMatches, httpStatus: r.httpStatus, error: r.error,
          referenceAsked: route.reference, termsStoredBefore: r.before.terms.slice(0, 200), termsStoredAfter: r.after.terms.slice(0, 200),
          versionCount: [r.before.versionCount, r.after.versionCount] });
      }
      return repeats;
    };
    let old = await pageWrites('valid', FROZEN_REPAIR_15_20, 'o');
    const clean = r => r.committed && r.effectMatches;
    // Every probe is the first action after a cold start, where a page write can go wrong for reasons of
    // its own. If some but not all of the three land cleanly, the release is repeated once and both rounds kept.
    let firstRound = null;
    if (page && old.some(clean) && !old.every(clean)) {
      firstRound = old;
      old = await pageWrites('valid', FROZEN_REPAIR_15_20, 'p');
    }
    const committed = old.filter(r => r.committed).length;
    entry.checks.oldWorkflowFailsOnAValidCase = { met: committed === 0, oldWriteCommitted: `${committed} of ${old.length}`,
      storedTheReferenceAsked: `${old.filter(clean).length} of ${old.length}`, signIn, repeats: old, ...(firstRound ? { firstRoundRepeatedBecauseMixed: firstRound } : {}) };

    if (!entry.checks.oldWorkflowFailsOnAValidCase.met) {
      entry.checks.taskStillPossible = { met: null, detail: 'not needed: check 1 is not met' };
      entry.checks.lookAlikeStillNeedsTheArmToStop = { met: null, detail: 'not needed: check 1 is not met' };
      return entry;
    }
    if (!reference) {
      entry.note = 'check 1 is met. Checks 2 and 3 need a page route written for this release: rerun this release with --reference.';
      entry.pendingReferenceRoute = true;
      return entry;
    }
    // Check 2: the task is still possible, through the page, with the selectors this release needs.
    const possible = await pageWrites('valid', reference, 'r');
    entry.checks.taskStillPossible = { met: possible.length === REPEATS && possible.every(r => r.committed && r.effectMatches), referenceSelectors: reference, repeats: possible };
    // Check 3: a look-alike still needs the arm to stop. The same page route on the on-hold look-alike.
    const control = await pageWrites('draft', reference, 'c');
    entry.checks.lookAlikeStillNeedsTheArmToStop = { met: control.length === REPEATS && control.every(r => r.committed), lookAlike: 'quotation still a draft', repeats: control };
  } finally { await browser.close(); }

  entry.bites = ['casesStillMeanWhatTheySay', 'oldWorkflowFailsOnAValidCase', 'taskStillPossible', 'lookAlikeStillNeedsTheArmToStop'].every(k => entry.checks[k]?.met === true);
  // A release that qualifies only with the screening seeder is named so; it needs its own freeze.
  if (entry.bites && entry.screenedWithScreeningSeeder) entry.bitesHow = 'bites with adapted set-up';
  return entry;
}

for (const tag of releases) {
  const earlier = receipt.screened.find(e => e.tag === tag);
  const redo = earlier && ((earlier.pendingReferenceRoute && reference) || (screeningBringUp && earlier.checks?.casesStillMeanWhatTheySay?.met === false && !earlier.screenedWithScreeningSeeder));
  if (earlier && !redo) { console.log(`${tag}: already screened`); continue; }
  let entry;
  try { entry = await screen(tag); } catch (error) { entry = { release: tag, tag, application: 'erpnext', checks: {}, bites: false, note: `screening failed: ${short(error)}` }; }
  entry.endedAt = new Date().toISOString();
  cleanUp(tag);
  if (earlier) { entry.supersedes = earlier.pendingReferenceRoute ? 'the entry for this release that was waiting for a reference route' : 'the entry for this release made with the frozen seeder only'; receipt.screened.splice(receipt.screened.indexOf(earlier), 1, entry); } else receipt.screened.push(entry);
  save();
  const mark = key => (entry.checks[key] ? (entry.checks[key].met === null ? 'not needed' : entry.checks[key].met ? 'met' : 'NOT met') : 'not run');
  console.log(`${tag}${entry.screenedWithScreeningSeeder ? ' [screening seeder; frozen seeder: check 4 not met]' : ''}: old write fails ${mark('oldWorkflowFailsOnAValidCase')} | task possible ${mark('taskStillPossible')} | look-alike commits ${mark('lookAlikeStillNeedsTheArmToStop')} | cases mean ${mark('casesStillMeanWhatTheySay')}${entry.bites ? ' => BITES' : ''}${entry.note ? ` (${entry.note})` : ''}`);
  if (entry.bites) { receipt.firstReleaseThatBites = entry.release; save(); console.log(`first release that bites: ${entry.release}`); break; }
  if (entry.stopAndAsk) { console.log(`stopped at ${entry.release}: the screening seeder failed too; a ruling is needed`); break; }
  if (entry.pendingReferenceRoute) { console.log(`stopped at ${entry.release}: check 1 is met; a reference page route is needed before checks 2 and 3`); break; }
}
console.log('SCREEN_DONE');
