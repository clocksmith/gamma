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

// A merge form posted as multipart/form-data (as Forgejo's is), once as a native form submission and
// once through fetch with FormData; the server counts the POSTs that reach it.
const MERGE_PAGE = `<!doctype html><title>merge</title>
<form id=merge method=post action=/pulls/7/merge enctype=multipart/form-data>
<input type=hidden name=_csrf value=token-1><input type=hidden name=head_commit_id value=abc123>
<input name=do value=merge><input name=merge_title_field value="Merge pull request #7"></form><script>
window.sent = [];
window.post = extra => { const body = new FormData(document.querySelector('#merge')); extra?.(body);
  return fetch('/pulls/7/merge', { method: 'POST', body }).then(r => window.sent.push(r.status), e => window.sent.push(e.name)); };
</script>`;

test('a multipart merge passes only when it matches the approval', { skip: !executablePath, timeout: 90000 }, async () => {
  const received = [];
  const server = createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/pulls/7/merge') {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => { received.push(body); res.writeHead(200, { 'Content-Type': 'text/html' }).end('<title>merged</title>'); });
      return;
    }
    if (req.method === 'GET' && req.url === '/') { res.writeHead(200, { 'Content-Type': 'text/html' }).end(MERGE_PAGE); return; }
    res.writeHead(404).end();
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const rule = { method: 'POST', url: `${origin}/pulls/7/merge`, versionPath: 'head_commit_id',
    fields: { do: 'merge', merge_title_field: 'Merge pull request #7' }, allowPaths: ['_csrf'] };
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
    const guarded = run => guardWrites(session, { rule, version: 'abc123', windowMs: 5000, settleMs: 200 }, run);
    const settled = count => page.waitForFunction(n => window.sent.length >= n, count, { timeout: 10000 });

    // An extra field and a file part are failed in the browser; the server sees neither.
    const extra = await guarded(() => page.evaluate(() => window.post(body => body.append('delete_branch_after_merge', 'on'))));
    await settled(1);
    assert.deepEqual(extra.requestGuard.blocked.map(entry => entry.reason), ['request-payload-mismatch']);
    const file = await guarded(() => page.evaluate(() => window.post(body => body.append('attachment', new File(['x'], 'a.bin')))));
    await settled(2);
    assert.deepEqual(file.requestGuard.blocked.map(entry => entry.reason), ['request-payload-mismatch']);
    assert.deepEqual(await page.evaluate(() => window.sent), ['TypeError', 'TypeError']);
    assert.equal(received.length, 0);

    // The native form submission matching the approval arrives once.
    const merged = await guarded(async () => {
      await Promise.all([page.waitForURL(`${origin}/pulls/7/merge`, { timeout: 10000 }), page.evaluate(() => document.querySelector('#merge').submit())]);
    });
    assert.equal(merged.requestGuard.admitted, 1);
    assert.deepEqual(merged.requestGuard.blocked, []);
    assert.equal(received.length, 1);
    assert.match(received[0], /name="do"\r\n\r\nmerge\r\n/);
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
});
