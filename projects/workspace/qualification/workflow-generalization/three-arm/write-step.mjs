// The one write every arm shares on OpenProject, and the database read that
// says whether it committed (clocksmith/deco#88, same-model three-arm test).
//
// The write is the Work field of a work package, saved through the page as the
// approver. The control selectors are the frozen repair from the Gate 3 receipt:
// no arm chooses them, and no arm executes the write itself. An arm only says
// "write" or "stop"; this file does the rest and reads the row before and after.
import { execFileSync } from 'node:child_process';

// From receipts/gate3-openproject-5arm-live-receipt.json, realUiUpgradeBreakVerified.liveRepairedV14ModalAction.
export const FROZEN_REPAIR_14_0 = Object.freeze({
  openSelector: 'span[role="button"][aria-label^="Work "]',
  inputSelector: 'input#work_package_estimated_hours',
  saveSelector: 'button[type="submit"]:has-text("Save")',
  sourceReceiptSha256: '400e07c7df25eed642d006aeaa5ce008ee27d50937e2c76140bc504b94cc586d',
});

const PG_CONTAINER = 'gammatron-op-pg15';

/** Row state straight from PostgreSQL, so a result never rests on what the page or the API reports. */
export function readWorkPackageRow(pgUrl, workPackageId) {
  const database = new URL(pgUrl).pathname.slice(1);
  const user = new URL(pgUrl).username;
  const id = Number(workPackageId);
  if (!Number.isSafeInteger(id)) throw Error('workPackageId must be an integer');
  const sql = `SELECT json_build_object('lockVersion', wp.lock_version, 'estimatedHours', wp.estimated_hours, `
    + `'remainingHours', wp.remaining_hours, 'statusId', wp.status_id, 'journalCount', `
    + `(SELECT COUNT(*) FROM journals j WHERE j.journable_type = 'WorkPackage' AND j.journable_id = wp.id))::text `
    + `FROM work_packages wp WHERE wp.id = ${id};`;
  const out = execFileSync('docker', ['exec', PG_CONTAINER, 'psql', '-U', user, '-d', database, '-Atc', sql],
    { encoding: 'utf8', timeout: 10000 }).trim();
  if (!out) throw Error(`work package ${id} not found`);
  return JSON.parse(out);
}

export async function login(context, baseUrl, username, password) {
  const page = await context.newPage();
  await page.goto(`${baseUrl}/login`, { waitUntil: 'domcontentloaded' });
  await page.fill('#login-form input[name="username"]', username);
  await page.fill('#login-form input[name="password"]', password);
  await Promise.all([
    page.waitForURL(u => !u.pathname.includes('/login')),
    page.click('#login-form input[type="submit"], #login-form button[type="submit"]'),
  ]);
  return page;
}

async function enter(page, baseUrl, { project, workPackageId, entryBranch }, repair) {
  const first = {
    direct: null,
    'project-table': `${baseUrl}/projects/${project}/work_packages`,
    'project-overview': `${baseUrl}/projects/${project}`,
    'relations-tab': `${baseUrl}/projects/${project}/work_packages/${workPackageId}/relations`,
  }[entryBranch];
  if (first === undefined) throw Error(`unknown entry branch ${entryBranch}`);
  if (first) await page.goto(first, { waitUntil: 'domcontentloaded' });
  await page.goto(`${baseUrl}/projects/${project}/work_packages/${workPackageId}/activity`, { waitUntil: 'domcontentloaded' });
  await page.locator(repair.openSelector).waitFor({ state: 'visible', timeout: 20000 });
}

/** Whether the Work field holds exactly the hours asked. Later releases show the value with a unit, as in "56h". */
export function fieldHoldsHours(held, workHours) {
  const text = String(held ?? '').replace(/\s+/g, '');
  return /^\d+(?:\.\d+)?h?$/.test(text) && Number(text.replace(/h$/, '')) === Number(workHours);
}

/**
 * Sets Work to `workHours` through the page and saves. Returns what the server
 * answered and the row before and after.
 *
 * Whether the write landed is decided by the row, never by a response: the row
 * is read until its version moves or `settleMs` passes, and once more after a
 * short pause. `httpStatus` is the last answer to a request on this work package
 * other than the form check, or null.
 *
 * Two faults of an earlier version are closed here. Both were seen only in the
 * first write after the application had started, and the second also on 14.0.0.
 *  - When it opens, the dialog checks the form with the server. A save sent before
 *    that answer arrived could be answered 200 and change nothing. The step now
 *    waits for the answer before it types.
 *  - The hours typed could be joined to the value the field already held, so that
 *    8 and 56 became 856 and 856 hours were stored. The step now reads the field
 *    back after typing, retypes if it does not hold exactly the hours asked, and
 *    does not press Save at all if it still does not: no write is better than a
 *    write of the wrong value.
 */
export async function executeWorkWrite(page, { baseUrl, pgUrl, route, repair = FROZEN_REPAIR_14_0, settleMs = 8000 }) {
  const started = Date.now();
  const before = readWorkPackageRow(pgUrl, route.workPackageId);
  let httpStatus = null;
  let error = null;
  let fieldHeld = null;
  const onThisWorkPackage = url => new URL(url).pathname.includes(`/work_packages/${route.workPackageId}`);
  const onResponse = response => {
    if (response.request().method() === 'GET') return;
    if (!onThisWorkPackage(response.url()) || new URL(response.url()).pathname.endsWith('/form')) return;
    httpStatus = response.status();
  };
  try {
    await enter(page, baseUrl, route, repair);
    const formChecked = page.waitForResponse(
      r => r.request().method() === 'POST' && onThisWorkPackage(r.url()) && new URL(r.url()).pathname.endsWith('/form'),
      { timeout: 5000 },
    ).catch(() => null);
    await page.locator(repair.openSelector).click();
    const input = page.locator(repair.inputSelector);
    await input.waitFor({ state: 'visible', timeout: 10000 });
    await formChecked;
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      await page.waitForTimeout(150);
      await input.fill('');
      await input.fill(String(route.workHours));
      await page.waitForTimeout(150);
      fieldHeld = await input.inputValue();
      if (fieldHoldsHours(fieldHeld, route.workHours)) break;
    }
    if (!fieldHoldsHours(fieldHeld, route.workHours)) {
      throw Error(`the Work field held "${String(fieldHeld).slice(0, 24)}" instead of ${route.workHours}; Save was not pressed`);
    }
    page.on('response', onResponse);
    await page.locator(repair.saveSelector).click();
    const deadline = Date.now() + settleMs;
    while (Date.now() < deadline && readWorkPackageRow(pgUrl, route.workPackageId).lockVersion === before.lockVersion) {
      await page.waitForTimeout(100);
    }
    await page.waitForTimeout(400);
  } catch (caught) {
    error = String(caught?.message ?? caught).split('\n')[0].slice(0, 240);
  } finally {
    page.off('response', onResponse);
  }
  const after = readWorkPackageRow(pgUrl, route.workPackageId);
  return Object.freeze({
    httpStatus,
    before,
    after,
    committed: after.lockVersion !== before.lockVersion,
    effectMatches: Number(after.estimatedHours) === Number(route.workHours),
    fieldHeldBeforeSave: fieldHeld,
    wallMs: Date.now() - started,
    error,
  });
}
