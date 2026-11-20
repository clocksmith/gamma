import assert from 'node:assert/strict';
import { mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { UploadStore, checkUploadTarget, validateUploadParams } from '../../src/uploads.js';
import { loadServiceConfig, validateServiceConfig } from '../../src/config.js';
import { evaluateConditions, validateConditions } from '../../src/conditions.js';

const root = mkdtempSync(join(tmpdir(), 'fawn-upload-limits-'));
const config = loadServiceConfig();
const limits = { maxFilesPerAction: 2, maxFileBytes: 8, maxStagedBytes: 12, maxNameBytes: 32 };
const store = new UploadStore(root, limits);
const file = { name: 'safe.txt', base64: Buffer.from('abcd').toString('base64') };
try {
  for (const files of [[], [{ ...file, name: '../outside' }], [{ ...file, name: '..' }],
    [{ ...file, path: '/arbitrary/path' }], [{ ...file, base64: '!!!!' }], [{ ...file, base64: 'Zh==' }],
    [{ ...file, base64: Buffer.alloc(9).toString('base64') }], [file, file, file]]) {
    assert.throws(() => store.stage(files), error => error.code === 'invalid-command');
    assert.deepEqual(readdirSync(root), [], 'Invalid selection writes no partial file');
  }
  const [a, b] = store.stage([file, file]);
  assert.notEqual(a.fileId, b.fileId);
  assert.equal(readFileSync(store.resolve({ uploadFiles: [a] }, [a.fileId])[0].path).toString(), 'abcd');
  assert.throws(() => store.resolve({ uploadFiles: [a] }, [b.fileId]), /not authorized/);
  assert.throws(() => store.stage([{ ...file, base64: Buffer.alloc(5).toString('base64') }]), /budget exhausted/);
  writeFileSync(join(root, a.fileId, a.name), 'wxyz');
  assert.throws(() => store.resolve({ uploadFiles: [a] }, [a.fileId]), /bytes changed/);
  const input = { tag: 'input', inputType: 'file', multiple: false, disabled: false, accept: '.txt' };
  checkUploadTarget(input, [a]);
  assert.throws(() => checkUploadTarget(input, [a, b]), /multiplicity/);
  assert.throws(() => checkUploadTarget({ ...input, disabled: true }, [a]), /enabled/);
  assert.throws(() => checkUploadTarget({ ...input, accept: '.pdf' }, [a]), /extensions/);
  for (const params of [{ fileIds: [] }, { fileIds: [a.fileId, a.fileId] }, { fileIds: [a.fileId], path: '/outside' }]) {
    assert.throws(() => validateUploadParams(params, config), /approved fileIds/);
  }
  const condition = { kind: 'input-files-equal', selector: '#file', files: [{ name: 'safe.txt', byteLength: 4 }] };
  validateConditions([condition], config.conditionKinds, 'completion');
  assert.throws(() => validateConditions([{ ...condition, files: [{ name: 'safe.txt', byteLength: -1 }] }], config.conditionKinds, 'completion'), /byte lengths/);
  const probe = { element: async () => ({ count: 1, inputType: 'file', files: condition.files }) };
  assert.equal((await evaluateConditions([condition], probe)).allEstablished, true);
  assert.equal((await evaluateConditions([{ ...condition, files: [] }], probe)).allEstablished, false);
  assert.throws(() => validateServiceConfig({ ...config, uploads: { ...limits, maxFileBytes: 0 } }), /positive safe integer/);
  for (const schemaVersion of [3, 4]) {
    const legacy = { ...config, schemaVersion, actionKinds: config.actionKinds.filter(kind => kind !== 'upload') };
    delete legacy.uploads;
    assert.doesNotThrow(() => validateServiceConfig(legacy));
  }
  store.retireUnused(new Set([b.fileId]));
  assert.deepEqual(readdirSync(root), [b.fileId]);
  console.log('ok: upload authorization payloads, bounds, exact snapshots, target constraints, retirement and legacy config');
} finally { rmSync(root, { recursive: true, force: true }); }
