import assert from 'node:assert/strict';

import { combineStratumComparisons } from '../../tools/compare-wgsl-stratified-rollouts.js';

function comparison(datasetHash, tasks, referencePass1, candidatePass1) {
  const samples = tasks * 8;
  const summary = (passingTasksAt1) => ({
    taskCount: tasks,
    groupSize: 8,
    sampleCount: samples,
    passingSamples: passingTasksAt1 * 8,
    samplePassRate: passingTasksAt1 / tasks,
    passingTasksAt1,
    passAt1: passingTasksAt1 / tasks,
    passingTasksAtK: passingTasksAt1,
    passAtK: passingTasksAt1 / tasks,
    exactReferenceSamples: passingTasksAt1 * 8,
    blockedSamples: 0,
  });
  const paired = (candidateOnly) => ({
    bothPass: referencePass1,
    bothFail: tasks - referencePass1 - candidateOnly,
    referenceOnly: 0,
    candidateOnly,
  });
  return {
    datasetHash,
    referencePolicyHash: 'a'.repeat(64),
    candidatePolicyHash: 'b'.repeat(64),
    anchorPolicyHash: 'c'.repeat(64),
    verifierBundleHash: 'd'.repeat(64),
    runtimeHash: 'e'.repeat(64),
    sampling: { maxTokens: tasks === 90 ? 64 : 640 },
    reference: summary(referencePass1),
    candidate: summary(candidatePass1),
    paired: {
      samples: paired((candidatePass1 - referencePass1) * 8),
      passAt1: paired(candidatePass1 - referencePass1),
      passAtK: paired(candidatePass1 - referencePass1),
    },
  };
}

const result = combineStratumComparisons({
  short: comparison('1'.repeat(64), 90, 70, 80),
  long: comparison('2'.repeat(64), 10, 2, 4),
});

assert.equal(result.reference.taskCount, 100);
assert.equal(result.reference.passAt1, 0.72);
assert.equal(result.candidate.passAt1, 0.84);
assert.equal(result.effects.passAt1, 0.12);
assert.equal(result.paired.passAt1.referenceOnly, 0);
assert.equal(result.paired.passAt1.candidateOnly, 12);
assert.equal(result.samplingByStratum.short.maxTokens, 64);
assert.equal(result.samplingByStratum.long.maxTokens, 640);

console.log('wgsl-stratified-comparison.test: ok');
