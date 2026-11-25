// Reads what the NocoDB grid shows for the "When" cells, in a browser whose time zone is fixed.
// usage: PLAYWRIGHT_MODULE=/path/to/node_modules/playwright NC_PASSWORD=... \
//        node page_read.cjs <base url> <email> <project id> <table title> <time zone> [screenshot.png]
// Prints one JSON object on stdout. The password comes from the environment and is never printed.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const [base, email, projectId, tableTitle, timeZone, shot] = process.argv.slice(2);
  const browser = await chromium.launch();
  const out = { time_zone_requested: timeZone };
  try {
    const context = await browser.newContext({ timezoneId: timeZone, locale: 'en-US', viewport: { width: 1500, height: 900 } });
    const page = await context.newPage();
    page.setDefaultTimeout(120000);
    await page.goto(base + '/dashboard/#/signin', { waitUntil: 'networkidle' });
    out.browser_time_zone = await page.evaluate(() => Intl.DateTimeFormat().resolvedOptions().timeZone);
    out.browser_utc_offset_minutes_on_2023_06_01 = await page.evaluate(() => new Date('2023-06-01T12:00:00Z').getTimezoneOffset());
    await page.fill('[data-testid="nc-form-signin__email"]', email);
    await page.fill('[data-testid="nc-form-signin__password"]', process.env.NC_PASSWORD);
    await page.click('[data-testid="nc-form-signin__submit"]');
    await page.waitForFunction(() => !location.hash.includes('signin'));
    await page.goto(base + '/dashboard/#/nc/' + projectId, { waitUntil: 'networkidle' });
    const item = page.locator('[data-testid="tree-view-table-' + tableTitle + '"]').first();
    await item.waitFor({ state: 'visible' });
    await item.click();
    const cells = page.locator('[data-testid^="cell-When-"]');
    await cells.first().waitFor({ state: 'visible' });
    await page.waitForTimeout(1500);
    out.url = page.url().replace(base, '');
    // The grid renders a date-time cell as a read-only input, so the shown text is the input's value.
    out.when_cells = await cells.evaluateAll(els => els.map(e => ({
      testid: e.getAttribute('data-testid'),
      shown: (e.innerText.trim() || Array.from(e.querySelectorAll('input')).map(i => i.value).join(' ')).trim(),
    })));
    out.title_cells = await page.locator('[data-testid^="cell-Title-"]').evaluateAll(els => els.map(e => e.innerText.trim()));
    if (shot) await page.screenshot({ path: shot });
    out.ok = true;
  } catch (err) {
    out.ok = false;
    out.error = String(err && err.message || err).slice(0, 500);
  }
  await browser.close();
  console.log(JSON.stringify(out));
})();
