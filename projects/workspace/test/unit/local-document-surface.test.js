import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { appendFile, mkdtemp, open, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { bindSelectedLocalDocument, LOCAL_DOCUMENT_SURFACE_V1 } from '../../src/surfaces/local-document.js';

const dir = await mkdtemp(join(tmpdir(), 'gamma-selected-document-'));
const path = join(dir, 'fixture.txt');
const fixture = Buffer.alloc(140 * 1024, 65); // crosses multiple bounded reads
await writeFile(path, fixture);
const handle = await open(path, 'r');
const digest = bytes => createHash('sha256').update(bytes).digest('hex');

try {
  const documentId = 'local:fixture';
  const surface = await bindSelectedLocalDocument({ documentId, handle });
  assert.equal(surface.surfaceVersion, LOCAL_DOCUMENT_SURFACE_V1);
  assert.equal(Object.hasOwn(surface, 'execute'), false);
  assert.equal(Object.hasOwn(surface, 'write'), false);
  const observed = await surface.observe();
  assert.deepEqual(observed, { status: 'observed', documentId, byteLength: fixture.length,
    sha256: digest(fixture), revision: observed.revision });
  assert.match(observed.revision, /^[a-f0-9]{64}$/);
  const expected = { documentId, byteLength: fixture.length, sha256: digest(fixture) };
  assert.deepEqual(await surface.reconcile(expected), { status: 'expected-state-observed', observation: observed });
  assert.deepEqual(await surface.reconcile({ ...expected, documentId: 'local:other' }),
    { status: 'unknown', reason: 'invalid-document-expectation' });
  assert.deepEqual(await surface.reconcile({ ...expected, sha256: digest('wrong') }),
    { status: 'unknown', reason: 'expected-state-not-observed' });

  let reads = 0;
  const bounded = await bindSelectedLocalDocument({ documentId, maxBytes: 1, handle: {
    stat: options => handle.stat(options),
    read: (...args) => { reads++; return handle.read(...args); },
  } });
  assert.deepEqual(await bounded.observe(), { status: 'unknown', reason: 'byte-limit-exceeded' });
  assert.equal(reads, 0);

  const racing = await bindSelectedLocalDocument({ documentId, handle: {
    stat: options => handle.stat(options),
    async read(...args) {
      const result = await handle.read(...args);
      if (reads++ === 0) await appendFile(path, 'fixture writer');
      return result;
    },
  } });
  assert.deepEqual(await racing.observe(), { status: 'unknown', reason: 'document-changed' });
  assert.deepEqual(await surface.reconcile(expected), { status: 'unknown', reason: 'expected-state-not-observed' });

  let releaseRead;
  let noteRead;
  const waiting = new Promise(resolve => { releaseRead = resolve; });
  const entered = new Promise(resolve => { noteRead = resolve; });
  const revoking = await bindSelectedLocalDocument({ documentId, handle: {
    stat: options => handle.stat(options),
    async read(...args) { noteRead(); await waiting; return handle.read(...args); },
  } });
  const inFlight = revoking.observe();
  await entered;
  revoking.detach();
  releaseRead();
  assert.deepEqual(await inFlight, { status: 'unknown', reason: 'selection-detached' });
  assert.deepEqual(await revoking.observe(), { status: 'unknown', reason: 'selection-detached' });
  assert.equal((await handle.stat()).isFile(), true, 'detaching a borrowed handle must not close it');

  await handle.close();
  assert.deepEqual(await surface.observe(), { status: 'unknown', reason: 'document-unavailable' });
} finally {
  await handle.close();
  await rm(dir, { recursive: true, force: true });
}
console.log('ok: selected native document observation, reconciliation, limits, racing write and detach, no dispatch');
