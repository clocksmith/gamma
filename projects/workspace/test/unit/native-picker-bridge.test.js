import assert from 'node:assert/strict';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { createNativePicker } from '../../src/client/native-picker.js';
import { startWorkspaceServer } from '../../src/client/server.js';

const root = await mkdtemp(join(tmpdir(), 'gamma-picker-'));
const executable = join(root, 'fixture');
const evidence = { status: 'observed', byteLength: 4, sha256: 'a'.repeat(64) };
const config = { host: '127.0.0.1', port: 0, maxBodyBytes: 1024 };
const controller = { status: () => ({ ready: true }) };
let enabled, disabled;
try {
  const fixture = async (data, prefix = '') => {
    const script = `#!/bin/sh\n${prefix}\nprintf '%s\\n' '${JSON.stringify(data)}'\n`;
    await writeFile(executable, script, { mode: 0o700 });
    return createNativePicker({ executable, sha256: createHash('sha256').update(script).digest('hex') });
  };
  const pick = await fixture(evidence, 'test "$#" -eq 0 || exit 1; test -z "${GAMMA_SECRET:-}" || exit 1');
  process.env.GAMMA_SECRET = 'not-inherited';
  enabled = await startWorkspaceServer({ controller, config, nativePicker: pick });
  disabled = await startWorkspaceServer({ controller, config });
  function request(server, path, data, cookie = '', origin = server.origin) {
    return fetch(server.origin + path, { method: 'POST',
      headers: { origin, cookie, 'content-type': 'application/json' }, body: JSON.stringify(data) });
  }
  async function login(server) {
    return (await request(server, '/api/session', { token: new URL(server.loginUrl).hash.slice(1) }))
      .headers.get('set-cookie').split(';')[0];
  }
  const cookie = await login(enabled);
  assert.equal((await request(enabled, '/api/native-document', {})).status, 401);
  assert.equal((await request(enabled, '/api/native-document', {}, cookie, 'https://elsewhere.invalid')).status, 403);
  assert.equal((await request(enabled, '/api/native-document', { path: '/not-accepted' }, cookie)).status, 400);
  assert.equal((await request(disabled, '/api/native-document', {}, await login(disabled))).status, 404);
  assert.deepEqual(await request(enabled, '/api/native-document', {}, cookie).then(r => r.json()), evidence);
  await fixture({ ...evidence, path: '/not-disclosed' });
  assert.deepEqual(await pick(), { status: 'selection-unavailable' }, 'changed executable not launched');
  const extra = await fixture({ ...evidence, path: '/not-disclosed' });
  assert.deepEqual(await extra(), { status: 'selection-unavailable' }, 'unexpected response fields not disclosed');
  const delayed = await fixture(evidence, 'exec /bin/sleep 20');
  const abort = new AbortController();
  const pending = delayed({ signal: abort.signal });
  assert.deepEqual(await delayed(), { status: 'selection-unavailable' }, 'single pending native dialog');
  abort.abort();
  assert.deepEqual(await pending, { status: 'selection-unavailable' });
} finally {
  delete process.env.GAMMA_SECRET;
  await enabled?.close();
  await disabled?.close();
  await rm(root, { recursive: true, force: true });
}
console.log('ok: opt-in native picker, same-origin auth, no path input, pinned child, evidence-only output, and cancellation');
