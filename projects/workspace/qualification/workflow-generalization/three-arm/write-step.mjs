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

/**
 * Sets Work to `workHours` through the page and saves. Returns what the server
 * answered and the row before and after. `committed` is true only when the row
 * version moved; `effectMatches` when the stored hours equal what was asked.
 */
export async function executeWorkWrite(page, { baseUrl, pgUrl, route, repair = FROZEN_REPAIR_14_0 }) {
  const started = Date.now();
  const before = readWorkPackageRow(pgUrl, route.workPackageId);
  let httpStatus = null;
  let error = null;
  try {
    await enter(page, baseUrl, route, repair);
    await page.locator(repair.openSelector).click();
    const input = page.locator(repair.inputSelector);
    await input.waitFor({ state: 'visible', timeout: 10000 });
    await input.fill(String(route.workHours));
    const [response] = await Promise.all([
      page.waitForResponse(
        r => r.url().includes(`/work_packages/${route.workPackageId}`) && ['PATCH', 'POST', 'PUT'].includes(r.request().method()),
        { timeout: 15000 },
      ),
      page.locator(repair.saveSelector).click(),
    ]);
    httpStatus = response.status();
    await page.waitForTimeout(400);
  } catch (caught) {
    error = String(caught?.message ?? caught).split('\n')[0].slice(0, 240);
  }
  const after = readWorkPackageRow(pgUrl, route.workPackageId);
  return Object.freeze({
    httpStatus,
    before,
    after,
    committed: after.lockVersion !== before.lockVersion,
    effectMatches: Number(after.estimatedHours) === Number(route.workHours),
    wallMs: Date.now() - started,
    error,
  });
}
