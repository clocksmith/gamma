import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import test from 'node:test';
import { chromium } from 'playwright-core';
import { guardWrites } from '../../src/request-guard.js';

// Runs the request guard over real CDP Fetch when REQUEST_GUARD_BROWSER names a Chrome or Chromium
// binary. One page, served by an in-process server that counts the PATCH requests reaching it.
const executablePath = process.env.REQUEST_GUARD_BROWSER;
const PAGE = `<!doctype html><title>save</title><button id=save>Save</button><script>
window.lockVersion = 7; window.sent = [];
document.querySelector('#save').onclick = () => fetch('/api/items/42', { method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ lockVersion: window.lockVersion, estimatedTime: 'PT56H' }) })
  .then(response => window.sent.push(response.status), error => window.sent.push(error.name));
</script>`;

test('a stale lockVersion never reaches the server; the approved one arrives once', { skip: !executablePath, timeout: 90000 }, async () => {
  const received = [];
  const server = createServer((req, res) => {
    if (req.method === 'PATCH' && req.url === '/api/items/42') {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => { received.push(JSON.parse(body)); res.writeHead(204).end(); });
      return;
    }
    if (req.method === 'GET' && req.url === '/') { res.writeHead(200, { 'Content-Type': 'text/html' }).end(PAGE); return; }
    res.writeHead(404).end();
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const rule = { method: 'PATCH', url: `${origin}/api/items/42`, fields: { estimatedTime: 'PT56H' }, versionPath: 'lockVersion' };
  const browser = await chromium.launch({ executablePath, args: ['--headless=new'], timeout: 30000 });
  try {
    const page = await browser.newPage();
    await page.goto(origin, { timeout: 15000 });
    const cdp = await page.context().newCDPSession(page);
    const session = {
      send: (method, params) => cdp.send(method, params),
      subscribe: listener => {
        const handler = params => listener('Fetch.requestPaused', params);
        cdp.on('Fetch.requestPaused', handler);
        return () => cdp.off('Fetch.requestPaused', handler);
      },
    };
    const click = (times = 1) => page.evaluate(n => { for (let i = 0; i < n; i++) document.querySelector('#save').click(); }, times);
    const guarded = (run, settleMs = 200) => guardWrites(session, { rule, version: 7, windowMs: 5000, settleMs }, run);
    const settled = count => page.waitForFunction(n => window.sent.length >= n, count, { timeout: 10000 });

    // The page holds version 6: blocked in the browser, the server sees nothing.
    await page.evaluate(() => { window.lockVersion = 6; });
    const stale = await guarded(() => click());
    await settled(1);
    assert.deepEqual(stale.requestGuard.blocked.map(entry => entry.reason), ['request-version-mismatch']);
    assert.equal(stale.requestGuard.admitted, 0);
    assert.equal(received.length, 0);
    assert.equal(await page.evaluate(() => window.sent[0]), 'TypeError');

    // The approved version: exactly one arrives.
    await page.evaluate(() => { window.lockVersion = 7; });
    const fresh = await guarded(() => click());
    await settled(2);
    assert.equal(fresh.requestGuard.admitted, 1);
    assert.deepEqual(fresh.requestGuard.blocked, []);
    assert.deepEqual(received, [{ lockVersion: 7, estimatedTime: 'PT56H' }]);

    // Two saves under one approval: the second is blocked.
    const twice = await guarded(() => click(2), 500);
    await settled(4);
    assert.equal(twice.requestGuard.admitted, 1);
    assert.deepEqual(twice.requestGuard.blocked.map(entry => [entry.reason, entry.detail]), [['unexpected-write', 'second write']]);
    assert.equal(received.length, 2);

    // Fetch was disabled afterwards: an unguarded request is no longer held.
    await click();
    await settled(5);
    assert.equal(received.length, 3);
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
});
