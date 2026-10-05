import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { releaseBaseUrl, releaseResourceUrl } from '../tasks/release-browser-urls.mjs';

test('release browser requests retain a deployment subpath, with or without trailing slash', async () => {
  const requests = [];
  const server = createServer((req, res) => {
    requests.push(req.url);
    if (!req.url.startsWith('/mandate-2038/')) return res.writeHead(404).end();
    res.end('release resource');
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try {
    const origin = `http://127.0.0.1:${server.address().port}`;
    for (const suffix of ['/mandate-2038', '/mandate-2038/']) {
      const base = releaseBaseUrl(`${origin}${suffix}?ignored=yes#section`);
      assert.equal(base, `${origin}/mandate-2038/`);
      for (const path of ['release-identity.json?release=0.21.4', '/web/index.html', 'docs/core-rules.html', 'docs/world-and-institutions.html']) {
        assert.equal((await fetch(releaseResourceUrl(base, path))).status, 200);
      }
    }
    assert.deepEqual(requests, Array(2).fill([
      '/mandate-2038/release-identity.json?release=0.21.4',
      '/mandate-2038/web/index.html', '/mandate-2038/docs/core-rules.html',
      '/mandate-2038/docs/world-and-institutions.html'
    ]).flat());
  } finally {
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
  }
});

test('root deployments work and release-relative paths cannot escape', () => {
  assert.equal(releaseResourceUrl('https://example.test', 'web/index.html'), 'https://example.test/web/index.html');
  assert.throws(() => releaseResourceUrl('https://example.test/mandate-2038/', '../private.html'), /escapes/);
  assert.throws(() => releaseBaseUrl('file:///tmp/game'), /HTTP/);
});
