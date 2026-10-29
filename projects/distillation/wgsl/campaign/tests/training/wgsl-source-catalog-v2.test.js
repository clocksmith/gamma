import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

import { sha256BytesHex } from '../../src/utils/sha256.js';
import { loadWgslSourceCatalog } from '../../tools/lib/wgsl-repair-corpus.js';

const v1Bytes = new Uint8Array(await readFile('tools/data/wgsl-training-source-catalog-v1.json'));
const v2 = JSON.parse(await readFile('tools/data/wgsl-training-source-catalog-v2.json', 'utf8'));
const loadedV2 = await loadWgslSourceCatalog(
  'tools/data/wgsl-training-source-catalog-v2.json'
);

assert.equal(
  await sha256BytesHex(v1Bytes),
  'ff99b6f2597f65be601cd48b668a1fae3d943de180eb3b4f7b95f50af4af161e',
  'The corpus-v1 source inventory must remain byte-stable.'
);
assert.equal(v2.catalogId, 'wgsl-ml-kernel-sources-v2');
assert.equal(loadedV2.catalog.catalogId, v2.catalogId);
assert.deepEqual(
  v2.sources.filter((source) => source.allowTraining).map((source) => source.id),
  ['doppler', 'zero-tvm']
);

const mlc = v2.sources.find((source) => source.id === 'mlc-web-llm');
assert.ok(mlc);
assert.equal(mlc.revision, '21314560fe1e44f379c3415f1077362769ac5c94');
assert.equal(mlc.license, 'Apache-2.0');
assert.equal(mlc.parserKind, 'compiler_reference');
assert.equal(mlc.role, 'reference_only');
assert.equal(mlc.allowTraining, false);
assert.match(mlc.notes, /pinned MLC\/TVM build/);

console.log('wgsl-source-catalog-v2.test: ok');
