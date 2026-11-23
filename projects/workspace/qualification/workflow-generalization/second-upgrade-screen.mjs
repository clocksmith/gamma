#!/usr/bin/env node
// Screens stock OpenProject releases against the evaluator's rule for a second
// upgrade that bites (second-upgrade-drift-rule.md, clocksmith/deco#88).
// Scripted probes only: no model call, no arm, no sealed case. It reads the
// frozen three-arm files and changes none of them.
//
//   node second-upgrade-screen.mjs --receipt FILE --releases 14.1.0-slim,14.2.0-slim,...
//   node second-upgrade-screen.mjs --receipt FILE --releases 16.2.0-slim --reference '{"openSelector":…,"inputSelector":…,"saveSelector":…}'
//
// Per release, in the order given (amendment 1 of the rule): pull the image,
// bring up 14.0.0 -> release with the frozen bring-up script, run check 4 and
// then check 1. Checks 2 and 3 are needed only when check 1 is met, and they
// must go through the page, as the arms' writes do, with whatever selectors
// that release needs. Those selectors have to be written by looking at the
// release, so the screen stops at the first release that meets check 1 and
// reports it; it is then rerun for that release with --reference. A write
// through the API is recorded as an extra fact, never as check 2.
// Tears down, deletes leftover volumes and the release's image, appends to the
// receipt. Needs the OpenProject ports.
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import { durationHours, openProjectRequester, provisionRecipe, readState } from './three-arm/provision.mjs';
import { executeWorkWrite, FROZEN_REPAIR_14_0, login, readWorkPackageRow } from './three-arm/write-step.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const FIRST_UPGRADE_TARGET = '14.0.0-slim';
const REPEATS = 3;
const FAMILY = 'example-approval-hours-match';
const recipe = (routeId, approvalHours, status, workHours) => ({
  routeId, familyId: FAMILY, entryBranch: 'direct',
  setup: [
    { as: 'approver', method: 'POST', path: '/api/v3/projects/stage2-qual-proj/work_packages',
      body: { subject: 'Approval {tag}', estimatedTime: `PT${approvalHours}H` }, save: { approval: 'id' } },
    { as: 'approver', method: 'PATCH', path: '/api/v3/work_packages/{approval}', body: { _links: { status: { href: status } } } },
    { as: 'author', method: 'POST', path: '/api/v3/projects/stage2-qual-proj/work_packages',
      body: { subject: 'Order {tag}', estimatedTime: 'PT8H', _links: { parent: { href: '/api/v3/work_packages/{approval}' } } }, save: { order: 'id' } },
  ],
  target: { workPackage: '{order}', project: 'stage2-qual-proj' }, write: { workHours },
});
// The public example family: valid when the approval above the order is approved for the same hours.
const ROUTES = {
  valid: { recipe: () => recipe('screen-valid', 56, '{status.approved}', 56), valid: true },
  hold: { recipe: () => recipe('screen-lookalike-hold', 56, '{status.hold}', 56), valid: false },
  hours: { recipe: () => recipe('screen-lookalike-hours', 32, '{status.approved}', 56), valid: false },
};

const args = process.argv.slice(2);
const option = name => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
const receiptFile = resolve(option('--receipt') ?? '');
const releases = (option('--releases') ?? '').split(',').filter(Boolean);
const reference = option('--reference') ? JSON.parse(option('--reference')) : null;
if (!option('--receipt') || !releases.length) { console.error('usage: second-upgrade-screen.mjs --receipt FILE --releases tag,tag,...'); process.exit(2); }

const sh = (file, argv = [], options = {}) => execFileSync(file, argv, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], ...options });
const short = error => String(error?.stderr || error?.message || error).trim().split('\n').slice(-2).join(' | ').replaceAll(HERE, '.').slice(0, 400);
const receipt = existsSync(receiptFile) ? JSON.parse(readFileSync(receiptFile, 'utf8')) : {};
receipt.screened ??= [];
const save = () => writeFileSync(receiptFile, JSON.stringify(receipt, null, 1) + '\n');

function cleanUp(tag) {
  try { sh(join(HERE, 'bringup', 'openproject-down.sh')); } catch { /* nothing to remove */ }
  // Containers are removed without their anonymous volumes; clear those, and only those.
  const dangling = sh('docker', ['volume', 'ls', '-qf', 'dangling=true']).split('\n').filter(name => /^[0-9a-f]{64}$/.test(name));
  for (let i = 0; i < dangling.length; i += 40) { try { sh('docker', ['volume', 'rm', ...dangling.slice(i, i + 40)]); } catch { /* in use */ } }
  if (tag !== FIRST_UPGRADE_TARGET) { try { sh('docker', ['rmi', `openproject/openproject:${tag}`]); } catch { /* not present */ } }
}

async function screen(tag) {
  const entry = { release: tag.replace('-slim', ''), tag, application: 'openproject', pair: `${FIRST_UPGRADE_TARGET.replace('-slim', '')}->${tag.replace('-slim', '')}`,
    startedAt: new Date().toISOString(), image: null, checks: {}, bites: false, note: null };
  try {
    sh('docker', ['pull', '-q', `openproject/openproject:${tag}`], { timeout: 30 * 60 * 1000 });
    entry.image = sh('docker', ['inspect', '--format', '{{index .RepoDigests 0}}', `openproject/openproject:${tag}`]).trim();
  } catch (error) { entry.note = `image could not be pulled: ${short(error)}`; return entry; }
  // The frozen bring-up can lose a race with PostgreSQL's first start (it asks for the databases while the
  // server is restarting after its own initialisation). That says nothing about the release, so the bring-up is
  // tried up to three times and every failure is kept with its reason.
  const bringUpFailures = [];
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      sh(join(HERE, 'bringup', 'openproject-down.sh'));
      sh(join(HERE, 'bringup', 'openproject-up.sh'), [FIRST_UPGRADE_TARGET, tag], { timeout: 20 * 60 * 1000 });
      break;
    } catch (error) {
      bringUpFailures.push(`attempt ${attempt}: ${short(error)} ${String(error?.stdout ?? '').trim().split('\n').slice(-1)[0].replaceAll(HERE, '.').slice(0, 200)}`);
    }
  }
  if (bringUpFailures.length) entry.bringUpFailures = bringUpFailures;
  if (bringUpFailures.length === 3) {
    entry.checks.casesStillMeanWhatTheySay = { met: false, detail: 'the frozen bring-up or seeder failed on this release three times' };
    entry.note = 'checks 1 to 3 not run: no seeded instance';
    return entry;
  }
  const state = readState();
  const rel = state.new;
  const request = openProjectRequester(rel);
  const build = (key, n) => provisionRecipe(ROUTES[key].recipe(), { request, seed: rel.seed, tag: `${key}${n}` });
  const liveLabel = async route => {
    const order = await request('approver', 'GET', `/api/v3/work_packages/${route.workPackageId}`);
    const parent = order.body?._links?.parent?.href;
    const approval = parent ? await request('approver', 'GET', parent) : null;
    return Boolean(approval?.body) && approval.body._links?.status?.href === rel.seed.approvedStatusHref && durationHours(approval.body.estimatedTime) === route.workHours;
  };
  const apiWrite = async route => {
    const path = `/api/v3/work_packages/${route.workPackageId}`;
    const before = readWorkPackageRow(rel.pgUrl, route.workPackageId);
    const current = await request('approver', 'GET', path);
    const answer = await request('approver', 'PATCH', path, { lockVersion: current.body.lockVersion, estimatedTime: `PT${route.workHours}H` });
    const after = readWorkPackageRow(rel.pgUrl, route.workPackageId);
    return { httpStatus: answer.status, committed: after.lockVersion !== before.lockVersion, hours: [before.estimatedHours, after.estimatedHours] };
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
    try { page = await login(context, rel.url, state.username, state.password); } catch (error) { signIn = `sign-in with the recorded steps failed: ${short(error)}`; }
    const pageWrites = async (key, repair, prefix) => {
      const repeats = [];
      for (let n = 1; page && n <= REPEATS; n += 1) {
        const r = await executeWorkWrite(page, { baseUrl: rel.url, pgUrl: rel.pgUrl, route: await build(key, `${prefix}${n}`), repair });
        repeats.push({ committed: r.committed, effectMatches: r.effectMatches, httpStatus: r.httpStatus, error: r.error });
      }
      return repeats;
    };
    const old = await pageWrites('valid', FROZEN_REPAIR_14_0, 'o');
    const committed = old.filter(r => r.committed).length;
    entry.checks.oldWorkflowFailsOnAValidCase = { met: committed === 0, oldWriteCommitted: `${committed} of ${old.length}`, signIn, repeats: old };

    if (!entry.checks.oldWorkflowFailsOnAValidCase.met) {
      entry.checks.taskStillPossible = { met: null, detail: 'not needed: check 1 is not met' };
      entry.checks.lookAlikeStillNeedsTheArmToStop = { met: null, detail: 'not needed: check 1 is not met' };
      return entry;
    }
    // Extra facts, not checks: the same write through API v3 as the approver.
    const viaApi = [];
    for (const key of ['valid', 'hold']) for (let n = 1; n <= REPEATS; n += 1) viaApi.push({ route: key, ...(await apiWrite(await build(key, `a${n}`))) });
    entry.extraFacts = { writeThroughApiV3: viaApi };
    if (!reference) {
      entry.note = 'check 1 is met. Checks 2 and 3 need a page route written for this release: rerun this release with --reference.';
      entry.pendingReferenceRoute = true;
      return entry;
    }
    // Check 2: the task is still possible, through the page, with the selectors this release needs.
    const possible = await pageWrites('valid', reference, 'r');
    entry.checks.taskStillPossible = { met: possible.length === REPEATS && possible.every(r => r.committed && r.effectMatches), referenceSelectors: reference, repeats: possible };
    // Check 3: a look-alike still needs the arm to stop. The same page route on the on-hold look-alike.
    const control = await pageWrites('hold', reference, 'c');
    entry.checks.lookAlikeStillNeedsTheArmToStop = { met: control.length === REPEATS && control.every(r => r.committed), lookAlike: 'approval on hold', repeats: control };
  } finally { await browser.close(); }

  entry.bites = ['casesStillMeanWhatTheySay', 'oldWorkflowFailsOnAValidCase', 'taskStillPossible', 'lookAlikeStillNeedsTheArmToStop'].every(k => entry.checks[k]?.met === true);
  return entry;
}

for (const tag of releases) {
  const earlier = receipt.screened.find(e => e.tag === tag);
  if (earlier && !(earlier.pendingReferenceRoute && reference)) { console.log(`${tag}: already screened`); continue; }
  let entry;
  try { entry = await screen(tag); } catch (error) { entry = { release: tag.replace('-slim', ''), tag, application: 'openproject', checks: {}, bites: false, note: `screening failed: ${short(error)}` }; }
  entry.endedAt = new Date().toISOString();
  cleanUp(tag);
  if (earlier) { entry.supersedes = 'the entry for this release that was waiting for a reference route'; receipt.screened.splice(receipt.screened.indexOf(earlier), 1, entry); } else receipt.screened.push(entry);
  save();
  const mark = key => (entry.checks[key] ? (entry.checks[key].met === null ? 'not needed' : entry.checks[key].met ? 'met' : 'NOT met') : 'not run');
  console.log(`${tag}: old write fails ${mark('oldWorkflowFailsOnAValidCase')} | task possible ${mark('taskStillPossible')} | look-alike commits ${mark('lookAlikeStillNeedsTheArmToStop')} | cases mean ${mark('casesStillMeanWhatTheySay')}${entry.bites ? ' => BITES' : ''}${entry.note ? ` (${entry.note})` : ''}`);
  if (entry.bites) { receipt.firstReleaseThatBites = entry.release; save(); console.log(`first release that bites: ${entry.release}`); break; }
  if (entry.pendingReferenceRoute) { console.log(`stopped at ${entry.release}: check 1 is met; a reference page route is needed before checks 2 and 3`); break; }
}
console.log('SCREEN_DONE');
