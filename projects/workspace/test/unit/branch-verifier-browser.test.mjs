import assert from 'node:assert/strict';
import test from 'node:test';
import { chromium } from 'playwright-core';
import { branchExpression } from '../../src/client/branch-verifier.js';

// Runs the page-side observation in a real browser when BRANCH_VERIFIER_BROWSER names a Chromium binary.
const executablePath = process.env.BRANCH_VERIFIER_BROWSER;
const manyInputs = Array.from({ length: 150 }, (_, index) => `<input name="f${index}" value="0">`).join('');
const html = `<!doctype html><title>t</title><form><input name=hours value=8><input type=hidden name=terms value=old>${manyInputs}</form>
<iframe srcdoc="<!doctype html><input name=draft value=a><div role=status>Ready</div>"></iframe>`;

test('observes the page in a real browser', { skip: !executablePath }, async () => {
  const browser = await chromium.launch({ executablePath, args: ['--headless=new'] });
  try {
    const page = await browser.newPage();
    const run = async (setup, action) => {
      await page.setContent(html);
      await page.frameLocator('iframe').locator('input').waitFor({ state: 'attached' });
      await page.evaluate(setup);
      return page.evaluate(branchExpression(action));
    };
    const field = name => `document.querySelector('[name=${name}]')`;

    const microtask = await run('0', `void Promise.resolve().then(() => { const a = document.createElement('div'); a.role = 'alert'; a.textContent = 'Late'; document.body.append(a); })`);
    assert.deepEqual(microtask.before.alerts, []);
    assert.deepEqual(microtask.after.alerts, ['Late']);

    assert.equal((await run('0', `Promise.reject(new DOMException('no', 'NotAllowedError'))`)).thrown, 'NotAllowedError');

    const late = await run('0', `${field('f120')}.value = '9'`);
    assert.deepEqual(late.after.dirty, ['f120']);
    assert.equal(late.after.truncated, false);
    const overflow = await run('0', `document.querySelectorAll('form input:not([type=hidden])').forEach(input => { input.value = 'x'; })`);
    assert.equal(overflow.after.truncated, true);

    assert.deepEqual((await run('0', `${field('terms')}.value = 'new'`)).after.dirty, ['terms']);
    assert.deepEqual((await run('0', '0')).after.dirty, []);

    const eight = await run('0', `${field('hours')}.value = '12'`);
    const eightHundred = await run('0', `${field('hours')}.value = '800'`);
    assert.deepEqual(eight.after.dirty, eightHundred.after.dirty);
    assert.notDeepEqual(eight.after.values, eightHundred.after.values);

    const framed = await run('0', `document.querySelector('iframe').contentDocument.querySelector('input').value = 'b'`);
    assert.deepEqual(framed.after.dirty, ['frame0/draft']);
    assert.deepEqual(framed.after.statuses, ['Ready']);
  } finally { await browser.close(); }
});
