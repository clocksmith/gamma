import assert from 'node:assert/strict';

import { summarizeV12Results } from '../../tools/finalize-wgsl-v12-results.js';

const seeds = [11, 29, 47];
const lanes = ['anchor', 'external20', 'random20'];
const hash = (character) => character.repeat(64);
const policy = {
  policyId: 'v12',
  model: { modelId: 'qwen', revision: hash('a') },
  sampling: { groupSize: 8 },
  splits: {
    'public-test': {
      short: { rows: 90, datasetSha256: hash('1') },
      long: { rows: 10, datasetSha256: hash('2') },
    },
  },
  selection: {
    seeds,
    lanes,
    primaryMetric: 'pass_at_1',
    successRule: 'frozen',
  },
};

function receipt(seed, lane, passAt1, longPassAt1) {
  return {
    artifactType: 'wgsl_stratified_evaluation',
    policyId: 'v12',
    seed,
    lane,
    split: 'public-test',
    policyHash: hash(String((seed + lane.length) % 10)),
    referencePolicyHash: hash('f'),
    overall: {
      groupCount: 100,
      sampleCount: 800,
      passingSamples: Math.round(passAt1 * 800),
      samplePassRate: passAt1,
      passingTasksAt1: Math.round(passAt1 * 100),
      passAt1,
      passingTasksAtK: Math.round(passAt1 * 100),
      passAtK: passAt1,
      blockedSamples: 0,
    },
    strata: {
      short: {
        rows: 90,
        datasetSha256: hash('1'),
        verification: { passAt1 },
      },
      long: {
        rows: 10,
        datasetSha256: hash('2'),
        verification: { passAt1: longPassAt1 },
      },
    },
  };
}

function trainingExport(seed, lane, policyHash) {
  return {
    workloadId: `v12-${lane}-seed${seed}`,
    workloadSha256: hash('3'),
    configHash: hash('4'),
    datasetHash: hash('5'),
    baseModelId: 'qwen-bf16',
    checkpointStep: 1200,
    weightsSha256: hash('6'),
    metrics: {
      datasetRows: 1200,
      distinctRowsVisited: 1200,
      steps: 1200,
      rowOrder: 'seed_hash_sorted_v1',
      rowOrderSha256: hash('7'),
      loss: 0.01,
      meanLoss: 0.02,
    },
    manifest: {
      metadata: {
        receipts: [{
          policyHash,
          runtime: {
            deviceName: 'Radeon',
            dtype: 'bfloat16',
            hipVersion: '7',
            torchVersion: '2',
            transformersVersion: '5',
          },
        }],
      },
    },
  };
}

function comparison(referencePassAt1, candidatePassAt1, referenceOnly, candidateOnly) {
  return {
    reference: { passAt1: referencePassAt1 },
    candidate: { passAt1: candidatePassAt1 },
    effects: {
      passAt1: candidatePassAt1 - referencePassAt1,
      passAtK: candidatePassAt1 - referencePassAt1,
    },
    paired: {
      passAt1: {
        referenceOnly,
        candidateOnly,
        exactMcNemarP: 0.5,
      },
    },
  };
}

const publicReceipts = {};
const trainingExports = {};
const comparisons = {};
for (const seed of seeds) {
  publicReceipts[seed] = {
    anchor: receipt(seed, 'anchor', 0.9, 0.4),
    external20: receipt(seed, 'external20', 0.95, 0.7),
    random20: receipt(seed, 'random20', 0.92, 0.5),
  };
  trainingExports[seed] = {};
  for (const lane of lanes) {
    trainingExports[seed][lane] = trainingExport(
      seed,
      lane,
      publicReceipts[seed][lane].policyHash
    );
  }
  comparisons[seed] = {
    anchor: comparison(0.9, 0.95, 1, 6),
    random20: comparison(0.92, 0.95, 2, 5),
  };
}

const result = summarizeV12Results({
  policy,
  design: {
    experimentId: 'doppler-wgsl-repair-v12',
    hypothesis: 'targeted replacement helps',
  },
  diagnosticDecision: {
    status: 'candidate_selected',
    selectedLane: 'external20',
    publicEvaluationAllowed: true,
    checks: { passed: true },
    aggregate: {},
    inputs: Array.from({ length: 9 }, () => ({})),
  },
  publicReceipts,
  trainingExports,
  comparisons,
  artifacts: { policy: {}, design: {}, diagnosticDecision: {} },
  recordedAt: '2026-07-13',
});

assert.equal(result.status, 'seed_confirmed_compiler_curation');
assert.equal(result.sameR.detailedStage, 'seed_confirmed');
assert.equal(result.sameR.registerStatus, 'mechanics_proven');
assert.equal(result.training.completedRuns, 9);
assert.equal(result.publicEvaluation.frozenRuleReplay.status, 'passed');
assert.ok(Math.abs(
  result.publicEvaluation.effects.external20VsAnchorMeanPassAt1 - 0.05
) < 1e-12);
assert.ok(Math.abs(
  result.publicEvaluation.effects.external20VsRandom20MeanPassAt1 - 0.03
) < 1e-12);
assert.equal(result.publicEvaluation.multiplicity.significantTestIds.length, 0);
assert.equal(result.evidenceBoundary.semanticKernelSuiteCompleted, false);
assert.equal(result.evidenceBoundary.promoted, false);

const mismatched = structuredClone(trainingExports);
mismatched[29].external20.metrics.steps = 1199;
assert.throws(() => summarizeV12Results({
  policy,
  design: { experimentId: 'v12', hypothesis: 'test' },
  diagnosticDecision: {
    status: 'candidate_selected',
    selectedLane: 'external20',
    publicEvaluationAllowed: true,
    inputs: Array.from({ length: 9 }, () => ({})),
  },
  publicReceipts,
  trainingExports: mismatched,
  comparisons,
  artifacts: {},
  recordedAt: '2026-07-13',
}), /Training completion contract mismatch/);

console.log('wgsl-v12-final-results.test: ok');
