import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, open, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createLocalDocumentBroker, DOCUMENT_SELECTION_BROKER_V1 } from '../../src/surfaces/local-document-broker.js';

const dir = await mkdtemp(join(tmpdir(), 'gamma-owner-selection-'));
const firstPath = join(dir, 'first.txt'), secondPath = join(dir, 'second.txt');
await writeFile(firstPath, 'first');
await writeFile(secondPath, 'second');
const digest = text => createHash('sha256').update(text).digest('hex');
const selections = [], released = [];
let chooserCalls = 0;
async function choose(path, label) {
  const handle = await open(path, 'r');
  return { handle, async release() { await handle.close(); released.push(label); } };
}
const broker = createLocalDocumentBroker({ async selectFile() {
  chooserCalls++;
  return (selections.shift() ?? (() => null))();
} });

try {
  assert.equal(broker.version, DOCUMENT_SELECTION_BROKER_V1);
  assert.deepEqual(Object.keys(broker.observer).sort(), ['observe', 'reconcile']);
  assert.deepEqual(await broker.observer.observe(firstPath), { status: 'unknown', reason: 'selection-unavailable' });
  assert.equal(chooserCalls, 0, 'observer operations cannot open the owner selector');

  selections.push(() => choose(firstPath, 'first'));
  const first = await broker.owner.select();
  assert.equal(first.status, 'selected');
  assert.deepEqual(Object.keys(first).sort(), ['documentId', 'previousReleased', 'status']);
  assert.notEqual(first.documentId, firstPath);
  const observing = await broker.observer.observe(first.documentId);
  assert.equal(observing.sha256, digest('first'));
  assert.deepEqual(await broker.observer.reconcile(first.documentId, {
    sha256: digest('first'), byteLength: 5,
  }), { status: 'expected-state-observed', observation: observing });
  assert.deepEqual(await broker.observer.reconcile(first.documentId, {
    sha256: digest('first'), byteLength: 5, path: firstPath,
  }), { status: 'unknown', reason: 'invalid-document-expectation' });
  assert.deepEqual(await broker.owner.select(), { status: 'cancelled' });
  assert.equal((await broker.observer.observe(first.documentId)).status, 'observed');

  selections.push(() => choose(secondPath, 'second'));
  const second = await broker.owner.select();
  assert.equal(second.previousReleased, true);
  assert.deepEqual(released, ['first']);
  assert.notEqual(first.documentId, second.documentId);
  assert.equal((await broker.observer.observe(first.documentId)).status, 'unknown');
  assert.equal((await broker.observer.observe(second.documentId)).sha256, digest('second'));
  assert.deepEqual(await broker.owner.revoke(), { status: 'revoked', released: true });
  assert.equal((await broker.observer.observe(second.documentId)).status, 'unknown');
  assert.deepEqual(released, ['first', 'second']);

  let selected;
  const waiting = new Promise(resolve => { selected = resolve; });
  selections.push(() => waiting);
  const pending = broker.owner.select();
  assert.deepEqual(await broker.owner.select(), { status: 'unknown', reason: 'selection-in-progress' });
  assert.deepEqual(await broker.owner.close(), { status: 'closed', released: true });
  selected(await choose(firstPath, 'late'));
  assert.deepEqual(await pending, { status: 'unknown', reason: 'selection-ended' });
  assert.deepEqual(released, ['first', 'second', 'late']);
  assert.deepEqual(await broker.owner.select(), { status: 'unknown', reason: 'selection-broker-closed' });
} finally {
  await broker.owner.close();
  await rm(dir, { recursive: true, force: true });
}
console.log('ok: local owner selection and opaque observer tokens, cancel/replacement/revoke/close, late descriptor release, no GUI');
