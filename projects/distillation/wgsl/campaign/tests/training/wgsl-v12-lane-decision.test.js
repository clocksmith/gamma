import assert from 'node:assert/strict';

import { decideLaneMatrix } from '../../tools/decide-wgsl-v12-lanes.js';

const policy = {
  policyId: 'v12',
  selection: {
    seeds: [11, 29, 47],
    lanes: ['anchor', 'external20', 'random20'],
    successRule: 'frozen',
  },
};

function receipt(seed, lane, passAt1, longPassAt1) {
  return {
    seed,
    lane,
    split: 'diagnostic',
    policyHash: `${seed}-${lane}`,
    overall: {
      passAt1,
      passAtK: passAt1 + 0.01,
      samplePassRate: passAt1 - 0.01,
    },
    strata: {
      short: { verification: { passAt1 } },
      long: { verification: { passAt1: longPassAt1 } },
    },
  };
}

function matrix(externalValues) {
  const result = {};
  for (const [index, seed] of policy.selection.seeds.entries()) {
    result[seed] = {
      anchor: receipt(seed, 'anchor', 0.8, 0.2),
      external20: receipt(seed, 'external20', externalValues[index], 0.3),
      random20: receipt(seed, 'random20', 0.82, 0.25),
    };
  }
  return result;
}

{
  const decision = decideLaneMatrix(matrix([0.85, 0.86, 0.87]), policy);
  assert.equal(decision.status, 'candidate_selected');
  assert.equal(decision.selectedLane, 'external20');
  assert.equal(decision.publicEvaluationAllowed, true);
}

{
  const decision = decideLaneMatrix(matrix([0.85, 0.79, 0.87]), policy);
  assert.equal(decision.status, 'hypothesis_rejected');
  assert.equal(decision.selectedLane, null);
  assert.equal(decision.publicEvaluationAllowed, false);
}

console.log('wgsl-v12-lane-decision.test: ok');
