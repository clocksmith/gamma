import assert from 'node:assert/strict';

import { summarizeGrpoLearningSignal } from '../../tools/run-wgsl-repair-experiment.js';

const zero = summarizeGrpoLearningSignal([
  { samples: [{ advantage: 0 }, { advantage: 0 }] },
  { samples: [{ advantage: 0 }, { advantage: 0 }] },
]);
assert.deepEqual(zero, {
  groupCount: 2,
  sampleCount: 4,
  varyingGroups: 0,
  nonzeroAdvantages: 0,
  hasLearningSignal: false,
  constructiveVaryingGroups: 0,
  exactOnlyVaryingGroups: 0,
  otherVaryingGroups: 0,
  unclassifiedVaryingGroups: 0,
  hasConstructiveLearningSignal: false,
});

const varying = summarizeGrpoLearningSignal([
  { samples: [{ advantage: -1 }, { advantage: 1 }] },
  { samples: [{ advantage: 0 }, { advantage: 0 }] },
]);
assert.equal(varying.varyingGroups, 1);
assert.equal(varying.nonzeroAdvantages, 2);
assert.equal(varying.hasLearningSignal, true);
assert.equal(varying.unclassifiedVaryingGroups, 1);

function reward({ compile, exact }) {
  return {
    reduction: { scalarReward: compile ? 1 + (exact ? 0.05 : 0) : 0, blocked: false },
    components: [
      { id: 'contract_pass', normalizedValue: 1 },
      { id: 'policy_pass', normalizedValue: 1 },
      { id: 'compile_pass', normalizedValue: compile ? 1 : 0 },
      { id: 'regression_pass', normalizedValue: compile ? 1 : 0 },
      { id: 'exact_reference_match', normalizedValue: exact ? 1 : 0 },
    ],
  };
}

const classified = summarizeGrpoLearningSignal([
  {
    samples: [
      { advantage: -1, rewardVector: reward({ compile: false, exact: false }) },
      { advantage: 1, rewardVector: reward({ compile: true, exact: true }) },
    ],
  },
  {
    samples: [
      { advantage: -1, rewardVector: reward({ compile: true, exact: false }) },
      { advantage: 1, rewardVector: reward({ compile: true, exact: true }) },
    ],
  },
]);
assert.equal(classified.constructiveVaryingGroups, 1);
assert.equal(classified.exactOnlyVaryingGroups, 1);
assert.equal(classified.hasConstructiveLearningSignal, true);

assert.throws(
  () => summarizeGrpoLearningSignal([{ samples: [{ advantage: 0 }] }]),
  /at least two samples/
);

console.log('wgsl-experiment-signal-gates.test: ok');
