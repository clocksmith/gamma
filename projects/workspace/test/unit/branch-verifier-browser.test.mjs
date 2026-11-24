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

test('records what the page tried to send in a real browser', { skip: !executablePath }, async () => {
  const browser = await chromium.launch({ executablePath, args: ['--headless=new'] });
  try {
    const page = await browser.newPage();
    await page.route('https://app.test/**', route => route.fulfill({ status: 204, body: '' }));
    const form = `<!doctype html><iframe name=sink></iframe><form id=f method=post action="https://app.test/save" target=sink>
      <input name=hours value=8><input type=hidden name=csrf value=x><button id=go name=op value=save>Save</button></form>`;
    const run = async action => {
      await page.goto('about:blank');
      await page.setContent(form);
      await page.evaluate(() => { window.fetch = () => Promise.reject(new DOMException('no', 'NotAllowedError')); });
      return page.evaluate(branchExpression(action));
    };
    const names = entry => entry.body.fields.map(field => field[0]);

    const submitted = await run(`document.querySelector('[name=hours]').value = '12', document.querySelector('#go').click()`);
    assert.equal(submitted.intents.length, 1);
    assert.equal(submitted.intents[0].api, 'form');
    assert.equal(submitted.intents[0].method, 'POST');
    assert.equal(submitted.intents[0].url, 'https://app.test/save');
    assert.deepEqual(names(submitted.intents[0]), ['csrf', 'hours', 'op']);
    assert.ok(!JSON.stringify(submitted).includes('"12"'), 'field values leave the branch only as digests');

    const prevented = await run(`document.querySelector('#f').addEventListener('submit', event => event.preventDefault()), document.querySelector('#go').click()`);
    assert.deepEqual(prevented.intents, []);

    const json = await run(`fetch('/api/items/7', { method: 'PATCH', body: JSON.stringify({ hours: 12, note: 'x' }) })`);
    assert.equal(json.thrown, 'NotAllowedError');
    assert.equal(json.intents[0].method, 'PATCH');
    assert.equal(json.intents[0].body.kind, 'json');
    assert.deepEqual(names(json.intents[0]), ['hours', 'note']);

    const xhr = await run(`(() => { const request = new XMLHttpRequest(); request.open('POST', 'https://app.test/x'); request.send(new URLSearchParams({ a: '1' })); })()`);
    assert.equal(xhr.intents[0].api, 'xhr');
    assert.equal(xhr.intents[0].body.kind, 'urlencoded');
    const beacon = await run(`navigator.sendBeacon('https://app.test/b', 'a=1&b=2')`);
    assert.equal(beacon.intents[0].api, 'beacon');
    assert.deepEqual(names(beacon.intents[0]), ['a', 'b']);
    const blob = await run(`fetch('https://app.test/u', { method: 'POST', body: new Blob(['x']) })`);
    assert.equal(blob.intents[0].body.kind, 'opaque');
  } finally { await browser.close(); }
});
