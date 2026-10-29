import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

import {
  buildStratumRequest,
  summarizeStrata,
} from '../../tools/run-wgsl-v12-evaluation.js';

const policy = {
  policyId: 'v12',
  model: { modelId: 'model', revision: 'revision' },
  trainer: {
    protocol: 'gamma_wgsl_trainer_json_v1',
    dtype: 'bfloat16',
    gradientCheckpointing: true,
    maxLength: 2048,
  },
  sampling: {
    groupSize: 8,
    temperature: 0.8,
    topP: 0.95,
    baseSeed: 100,
    longSeedOffset: 1000,
  },
};

const entry = {
  datasetPath: 'tasks.jsonl',
  maxTokens: 640,
  maximumTrainingTargetTokensIncludingEos: 619,
  marginTokens: 21,
};

{
  const request = buildStratumRequest({
    policy,
    entry,
    adapterPath: '/adapter',
    lane: 'external20',
    seed: 29,
    split: 'diagnostic',
    stratum: 'long',
    outputRoot: '/output',
  });
  assert.equal(request.runId, 'v12-external20-seed29-diagnostic-long');
  assert.equal(request.sampling.seed, 1100);
  assert.equal(request.sampling.maxTokens, 640);
  assert.equal(request.sampling.maxTokensDerivation.holdoutOutcomesUsed, false);
  assert.equal(request.generation.captureLogprobs, false);
}

{
  const receipt = (groups, samples, pass1, passK, passing) => ({
    groupCount: groups,
    sampleCount: samples,
    passingSamples: passing,
    passingTasksAt1: pass1,
    passingTasksAtK: passK,
    exactReferenceSamples: passing - 1,
    blockedSamples: 1,
  });
  const summary = summarizeStrata({
    short: { verification: receipt(90, 720, 80, 85, 650) },
    long: { verification: receipt(10, 80, 4, 6, 30) },
  });
  assert.equal(summary.groupCount, 100);
  assert.equal(summary.sampleCount, 800);
  assert.equal(summary.passAt1, 0.84);
  assert.equal(summary.passAtK, 0.91);
  assert.equal(summary.samplePassRate, 0.85);
  assert.equal(summary.blockedSamples, 2);
}

{
  const frozen = JSON.parse(await readFile(
    'tools/policies/wgsl-repair-v12-evaluation-policy.json',
    'utf8'
  ));
  const design = JSON.parse(await readFile(
    'docs/status/wgsl-repair-v12-design-2026-07-12.json',
    'utf8'
  ));
  assert.deepEqual(frozen.selection.seeds, [11, 29, 47]);
  assert.deepEqual(frozen.selection.lanes, ['anchor', 'external20', 'random20']);
  for (const [splitId, split] of Object.entries(frozen.splits)) {
    const designSplit = design.lengthStrata[
      splitId === 'public-test' ? 'publicTest' : splitId
    ];
    for (const [stratum, stratumEntry] of Object.entries(split)) {
      assert.equal(stratumEntry.rows, designSplit[`${stratum}Rows`]);
      assert.equal(stratumEntry.datasetSha256, designSplit[`${stratum}Sha256`]);
      assert.equal(stratumEntry.maxTokens, stratum === 'short' ? 64 : 640);
    }
  }
}

console.log('wgsl-v12-evaluation.test: ok');
