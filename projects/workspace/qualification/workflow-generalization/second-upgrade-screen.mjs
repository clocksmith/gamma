#!/usr/bin/env node
// Screens stock OpenProject releases against the evaluator's rule for a second
// upgrade that bites (second-upgrade-drift-rule.md, clocksmith/deco#88).
// Scripted probes only: no model call, no arm, no sealed case. It reads the
// frozen three-arm files and changes none of them.
//
//   node second-upgrade-screen.mjs --receipt FILE --releases 14.1.0-slim,14.2.0-slim,...
//
// Per release, in the order given: pull the image, bring up 14.0.0 -> release
// with the frozen bring-up script, run the four checks, tear down, delete the
// leftover volumes and the release's image, append to the receipt. Stops at the
// first release that meets all four. Needs the OpenProject ports.
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
if (!option('--receipt') || !releases.length) { console.error('usage: second-upgrade-screen.mjs --receipt FILE --releases tag,tag,...'); process.exit(2); }

const sh = (file, argv = [], options = {}) => execFileSync(file, argv, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], ...options });
const short = error => String(error?.stderr || error?.message || error).trim().split('\n').slice(-2).join(' | ').slice(0, 400);
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
  try {
    sh(join(HERE, 'bringup', 'openproject-down.sh'));
    sh(join(HERE, 'bringup', 'openproject-up.sh'), [FIRST_UPGRADE_TARGET, tag], { timeout: 20 * 60 * 1000 });
  } catch (error) {
    entry.checks.casesStillMeanWhatTheySay = { met: false, detail: `the frozen bring-up or seeder failed on this release: ${short(error)}` };
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
    const repeats = [];
    let page = null;
    try { page = await login(context, rel.url, state.username, state.password); } catch (error) { repeats.push({ committed: false, error: `sign-in failed: ${short(error)}` }); }
    for (let n = 1; page && n <= REPEATS; n += 1) {
      const route = await build('valid', n);
      const r = await executeWorkWrite(page, { baseUrl: rel.url, pgUrl: rel.pgUrl, route, repair: FROZEN_REPAIR_14_0 });
      repeats.push({ committed: r.committed, effectMatches: r.effectMatches, httpStatus: r.httpStatus, error: r.error });
    }
    const committed = repeats.filter(r => r.committed).length;
    entry.checks.oldWorkflowFailsOnAValidCase = { met: page ? committed === 0 : true, oldWriteCommitted: `${committed} of ${page ? REPEATS : 0}`, repeats };
  } finally { await browser.close(); }

  // Check 2: the task is still possible. The same write through API v3 as the approver.
  const reference = [];
  for (let n = 1; n <= REPEATS; n += 1) reference.push(await apiWrite(await build('valid', `r${n}`)));
  entry.checks.taskStillPossible = { met: reference.every(r => r.committed && Number(r.hours[1]) === 56), repeats: reference };

  // Check 3: a look-alike still needs the arm to stop. An always-write control on the on-hold look-alike.
  const control = [];
  for (let n = 1; n <= REPEATS; n += 1) control.push(await apiWrite(await build('hold', `c${n}`)));
  entry.checks.lookAlikeStillNeedsTheArmToStop = { met: control.every(r => r.committed), lookAlike: 'approval on hold', repeats: control };

  entry.bites = Object.values(entry.checks).every(c => c.met) && Object.keys(entry.checks).length === 4;
  return entry;
}

for (const tag of releases) {
  if (receipt.screened.some(e => e.tag === tag)) { console.log(`${tag}: already screened`); continue; }
  let entry;
  try { entry = await screen(tag); } catch (error) { entry = { release: tag.replace('-slim', ''), tag, application: 'openproject', checks: {}, bites: false, note: `screening failed: ${short(error)}` }; }
  entry.endedAt = new Date().toISOString();
  cleanUp(tag);
  receipt.screened.push(entry);
  save();
  const mark = key => (entry.checks[key] ? (entry.checks[key].met ? 'met' : 'NOT met') : 'not run');
  console.log(`${tag}: old write fails ${mark('oldWorkflowFailsOnAValidCase')} | task possible ${mark('taskStillPossible')} | look-alike commits ${mark('lookAlikeStillNeedsTheArmToStop')} | cases mean ${mark('casesStillMeanWhatTheySay')}${entry.bites ? ' => BITES' : ''}${entry.note ? ` (${entry.note})` : ''}`);
  if (entry.bites) { receipt.firstReleaseThatBites = entry.release; save(); console.log(`first release that bites: ${entry.release}`); break; }
}
console.log('SCREEN_DONE');
