import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

import { buildSeedWorkload } from '../../tools/materialize-wgsl-v12-seed-workloads.js';

const template = {
  id: 'lora-doppler-wgsl-qwen35-9b-v12-anchor',
  description: 'anchor',
  claimBoundary: 'control',
  seed: 11,
  datasetId: 'dataset',
  lora: {
    export: {
      id: 'doppler-wgsl-qwen35-9b-v12-anchor',
      name: 'Anchor',
    },
  },
};

{
  const workload = buildSeedWorkload(template, 'anchor', 29);
  assert.equal(workload.id, 'lora-doppler-wgsl-qwen35-9b-v12-anchor-seed29');
  assert.equal(workload.seed, 29);
  assert.equal(workload.datasetId, 'dataset');
  assert.equal(workload.lora.export.id, 'doppler-wgsl-qwen35-9b-v12-anchor-seed29');
  assert.equal(workload.lora.export.name, 'Anchor Seed 29');
  assert.equal(template.seed, 11);
}

assert.throws(
  () => buildSeedWorkload(template, 'anchor', 13),
  /Unsupported V12 replication seed/
);

for (const lane of ['anchor', 'external20', 'random20']) {
  const root = 'src/experimental/training/workload-capsules';
  const source = JSON.parse(await readFile(
    `${root}/lora-doppler-wgsl-qwen35-9b-v12-${lane}.json`,
    'utf8'
  ));
  for (const seed of [29, 47]) {
    const generated = JSON.parse(await readFile(
      `${root}/lora-doppler-wgsl-qwen35-9b-v12-${lane}-seed${seed}.json`,
      'utf8'
    ));
    assert.deepEqual(generated, buildSeedWorkload(source, lane, seed));
  }
}

console.log('wgsl-v12-seed-workloads.test: ok');
