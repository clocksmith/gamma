// The one write every arm shares on ERPNext, and the database read that says
// whether it committed (clocksmith/deco#88). DRAFT, outside the frozen runner hash.
//
// The write: signed in as the approver, the route's confirmation reference is
// typed into the Terms of a draft Purchase Order and the order is saved. The
// control selectors are the repair recorded in the Gate 4 receipt. No arm chooses
// them and no arm performs the write: an arm says "write" or "stop".
//
// As on OpenProject, whether the write landed is decided by the row and nothing
// else: it is read until its modified time moves or `settleMs` passes, and once
// more after a pause.
import { execFileSync } from 'node:child_process';

// From receipts/gate4-erpnext-5arm-live-receipt.json, realUiUpgradeBreakVerified.liveRepairedV15_20DeskAction.
export const FROZEN_REPAIR_15_20 = Object.freeze({
  tabSelector: 'a#purchase-order-terms_tab-tab',
  editorSelector: 'div.frappe-control[data-fieldname="terms"] .ql-editor[contenteditable="true"]',
  saveSelector: 'button.primary-action[data-label="Save"]',
  sourceReceiptSha256: 'c04d6fc53667a400c248b8e5ff982da4ed20b9dcd23fa950319d4db3e6c6bf92',
});

/** Row state straight from MariaDB. The password stays inside the database container's environment. */
export function readOrderRow({ mariadbContainer, database }, name) {
  const safe = String(name);
  if (!/^[A-Za-z0-9_-]{1,64}$/.test(safe)) throw Error('order name holds a character that is not allowed');
  const sql = `SELECT JSON_OBJECT('modified', DATE_FORMAT(modified, '%Y-%m-%d %H:%i:%s.%f'), 'docstatus', docstatus, `
    + `'totalQty', total_qty, 'termsLength', CHAR_LENGTH(IFNULL(terms, '')), `
    + `'versionCount', (SELECT COUNT(*) FROM tabVersion WHERE ref_doctype='Purchase Order' AND docname='${safe}')) `
    + `FROM \`tabPurchase Order\` WHERE name='${safe}';`;
  const out = execFileSync('docker', ['exec', '-e', `SQL=${sql}`, '-e', `DBNAME=${database}`, mariadbContainer, 'sh', '-c',
    'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" "$DBNAME" -Nre "$SQL"'], { encoding: 'utf8', timeout: 10000 }).trim();
  if (!out) throw Error(`order ${safe} not found`);
  const row = JSON.parse(out);
  return { modified: row.modified, docstatus: Number(row.docstatus), totalQty: Number(row.totalQty), termsLength: Number(row.termsLength), versionCount: Number(row.versionCount) };
}

/** Whether the order's Terms hold the reference, read from the database. */
export function orderHoldsReference({ mariadbContainer, database }, name, reference) {
  if (!/^[A-Za-z0-9_-]{1,64}$/.test(String(name)) || !/^[A-Z0-9-]{4,24}$/.test(String(reference))) throw Error('name or reference holds a character that is not allowed');
  const sql = `SELECT INSTR(IFNULL(terms, ''), '${reference}') > 0 FROM \`tabPurchase Order\` WHERE name='${name}';`;
  return execFileSync('docker', ['exec', '-e', `SQL=${sql}`, '-e', `DBNAME=${database}`, mariadbContainer, 'sh', '-c',
    'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" "$DBNAME" -Nre "$SQL"'], { encoding: 'utf8', timeout: 10000 }).trim() === '1';
}

export async function loginDesk(context, baseUrl, username, password) {
  const page = await context.newPage();
  await page.goto(`${baseUrl}/login`, { waitUntil: 'domcontentloaded' });
  await page.fill('#login_email', username);
  await page.fill('#login_password', password);
  await Promise.all([page.waitForURL(u => u.pathname.startsWith('/app'), { timeout: 30000 }), page.click('.btn-login')]);
  return page;
}

async function enter(page, baseUrl, route, repair) {
  const first = { direct: null, 'order-list': `${baseUrl}/app/purchase-order`, 'buying-workspace': `${baseUrl}/app/buying`, 'more-info-tab': null }[route.entryBranch];
  if (first === undefined) throw Error(`unknown entry branch ${route.entryBranch}`);
  if (first) await page.goto(first, { waitUntil: 'domcontentloaded' });
  await page.goto(`${baseUrl}/app/purchase-order/${encodeURIComponent(route.name)}`, { waitUntil: 'domcontentloaded' });
  await page.locator(repair.tabSelector).first().waitFor({ state: 'visible', timeout: 30000 });
  if (route.entryBranch === 'more-info-tab') {
    await page.locator('a#purchase-order-more_info_tab-tab').first().click();
    await page.waitForTimeout(150);
  }
}

/**
 * Types the route's reference into the order's Terms and saves. `db` is
 * { mariadbContainer, database }. Returns the server's answer to the save and the
 * row before and after; `committed` is true only when the row's modified time moved.
 */
export async function executeTermsWrite(page, { baseUrl, db, route, repair = FROZEN_REPAIR_15_20, settleMs = 8000 }) {
  const started = Date.now();
  const before = readOrderRow(db, route.name);
  let httpStatus = null;
  let error = null;
  const onResponse = response => {
    if (response.request().method() === 'GET') return;
    if (new URL(response.url()).pathname.endsWith('frappe.desk.form.save.savedocs')) httpStatus = response.status();
  };
  try {
    await enter(page, baseUrl, route, repair);
    await page.locator(repair.tabSelector).first().click();
    const editor = page.locator(repair.editorSelector).first();
    await editor.waitFor({ state: 'visible', timeout: 10000 });
    await editor.click();
    await page.keyboard.type(route.reference);
    page.on('response', onResponse);
    await page.locator(repair.saveSelector).first().click();
    const deadline = Date.now() + settleMs;
    while (Date.now() < deadline && readOrderRow(db, route.name).modified === before.modified) await page.waitForTimeout(100);
    await page.waitForTimeout(400);
    // A refusal leaves a dialog open; close it so that the next route starts from a clean page.
    await page.keyboard.press('Escape').catch(() => {});
  } catch (caught) {
    error = String(caught?.message ?? caught).split('\n')[0].slice(0, 240);
  } finally {
    page.off('response', onResponse);
  }
  const after = readOrderRow(db, route.name);
  return Object.freeze({
    httpStatus, before, after,
    committed: after.modified !== before.modified,
    effectMatches: orderHoldsReference(db, route.name, route.reference),
    wallMs: Date.now() - started, error,
  });
}
