import assert from 'node:assert/strict';

import {
  applyWgslRepairResponse,
  buildTrainingPromotionDecision,
  buildTrainingRolloutGroup,
  buildWgslRepairTask,
  buildWgslRewardVector,
  computeGroupRelativeAdvantages,
  createWgslRepairMutations,
  deriveDpoPreferencePairs,
  deriveReferenceAnchoredDpoPairs,
  hashVerifierGuidedArtifact,
  parseReplacementOnlyResponse,
  selectRejectionSamples,
  validateVerifierGuidedArtifact,
} from '../../src/experimental/training/wgsl-repair.js';
import {
  buildTrainingPolicyCheckpoint,
  buildTrainingPolicyUpdate,
} from '../../src/experimental/training/policy-artifacts.js';

const shader = `
struct Uniforms { size: u32, }
@group(0) @binding(0) var<uniform> uniforms: Uniforms;
@group(0) @binding(1) var<storage, read_write> output: array<f32>;
@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) global_id: vec3<u32>) {
  let index = global_id.x;
  if (index >= uniforms.size) { return; }
  output[index] = f32(index);
}
`.trim();

const mutations = createWgslRepairMutations(shader);
assert.ok(mutations.length >= 7, `expected broad mutation coverage, got ${mutations.length}`);
assert.equal(new Set(mutations.map((mutation) => mutation.operator)).size, mutations.length);

const mutation = mutations.find((entry) => entry.operator === 'identifier_reference');
assert.ok(mutation);
const task = buildWgslRepairTask({
  sourceId: 'doppler',
  sourcePath: 'src/gpu/kernels/fixture.wgsl',
  revision: 'a'.repeat(40),
  license: 'Apache-2.0',
  source: shader,
}, mutation);
assert.match(task.taskId, /^wgsl-[a-f0-9]{20}$/);
assert.match(task.prompt, /Return only the replacement WGSL/);
assert.equal(task.completion, mutation.originalSpan);

const applied = applyWgslRepairResponse(task, task.completion);
assert.equal(applied.ok, true);
assert.equal(applied.candidateSource, shader);
assert.deepEqual(
  parseReplacementOnlyResponse('```wgsl\nlet x = 1u;\n```').violations,
  ['markdown_fence']
);

const groupStats = computeGroupRelativeAdvantages([-1, 1]);
assert.equal(groupStats.mean, 0);
assert.deepEqual(groupStats.advantages, [-1, 1]);
assert.deepEqual(computeGroupRelativeAdvantages([1, 1]).advantages, [0, 0]);

const verifierBundleHash = 'b'.repeat(64);
function reward(sampleId, compilePass) {
  return buildWgslRewardVector({
    taskId: task.taskId,
    sampleId,
    verifierBundleHash,
    contractPass: true,
    policyPass: true,
    compilePass,
    regressionPass: compilePass,
    exactReferenceMatch: compilePass,
    claimBoundary: 'Training signal only.',
  });
}

const rolloutGroup = buildTrainingRolloutGroup({
  workloadId: 'wgsl-v9-fixture',
  groupId: `${task.taskId}-group-1`,
  taskId: task.taskId,
  datasetHash: 'c'.repeat(64),
  policyHash: 'd'.repeat(64),
  referencePolicyHash: 'e'.repeat(64),
  verifierBundleHash,
  runtimeHash: 'f'.repeat(64),
  advantageEpsilon: 1e-6,
  sampling: {
    seed: 11,
    temperature: 0.8,
    topP: 0.95,
    maxTokens: 256,
  },
  samples: [
    {
      sampleId: 'sample-bad',
      prompt: task.prompt,
      completion: mutation.mutatedSpan,
      tokenIds: [1, 2],
      completionMask: [0, 1],
      policyTokenLogprobs: [-0.2],
      referenceTokenLogprobs: [-0.3],
      stopReason: 'eos',
      rewardVector: reward('sample-bad', false),
    },
    {
      sampleId: 'sample-good',
      prompt: task.prompt,
      completion: task.completion,
      tokenIds: [1, 3],
      completionMask: [0, 1],
      policyTokenLogprobs: [-0.1],
      referenceTokenLogprobs: [-0.2],
      stopReason: 'eos',
      rewardVector: reward('sample-good', true),
    },
  ],
  claimBoundary: 'Training signal only.',
});

validateVerifierGuidedArtifact(rolloutGroup);
assert.equal(rolloutGroup.rolloutPurpose, 'training');
assert.match(hashVerifierGuidedArtifact(rolloutGroup), /^[a-f0-9]{64}$/);
assert.deepEqual(rolloutGroup.samples.map((sample) => sample.advantage), [-1, 1]);

const selected = selectRejectionSamples([rolloutGroup]);
assert.equal(selected.length, 1);
assert.equal(selected[0].sampleId, 'sample-good');
const pairs = deriveDpoPreferencePairs([rolloutGroup], { minimumRewardGap: 0.5 });
assert.equal(pairs.length, 1);
assert.equal(pairs[0].chosenSampleId, 'sample-good');
assert.equal(pairs[0].rejectedSampleId, 'sample-bad');

const allFailGroup = buildTrainingRolloutGroup({
  workloadId: 'wgsl-v9-reference-anchor-fixture',
  groupId: `${task.taskId}-all-fail-group-1`,
  taskId: task.taskId,
  datasetHash: 'c'.repeat(64),
  policyHash: 'd'.repeat(64),
  referencePolicyHash: 'e'.repeat(64),
  verifierBundleHash,
  runtimeHash: 'f'.repeat(64),
  advantageEpsilon: 1e-6,
  sampling: rolloutGroup.sampling,
  samples: [
    {
      ...rolloutGroup.samples[0],
      sampleId: 'all-fail-sample-1',
      completion: mutation.mutatedSpan,
      rewardVector: reward('all-fail-sample-1', false),
    },
    {
      ...rolloutGroup.samples[0],
      sampleId: 'all-fail-sample-2',
      completion: mutation.mutatedSpan,
      rewardVector: reward('all-fail-sample-2', false),
    },
  ],
  claimBoundary: 'Reference-anchor fixture only.',
});
const anchoredPairs = deriveReferenceAnchoredDpoPairs([allFailGroup], [{
  ...task,
  verification: { cleanCompilePassed: true, mutantCompileFailed: true },
}]);
assert.equal(anchoredPairs.length, 1);
assert.equal(anchoredPairs[0].chosen, task.span.reference);
assert.equal(anchoredPairs[0].rejected, mutation.mutatedSpan);
assert.equal(anchoredPairs[0].rejectedModeCount, 2);
assert.equal(deriveReferenceAnchoredDpoPairs([rolloutGroup], [{
  ...task,
  verification: { cleanCompilePassed: true, mutantCompileFailed: true },
}]).length, 0);

const promote = buildTrainingPromotionDecision({
  workloadId: 'wgsl-v9-fixture',
  decisionId: 'wgsl-v9-fixture-decision',
  candidatePolicyHash: 'f'.repeat(64),
  promotionVerifierSplitHash: '1'.repeat(64),
  gates: [
    { id: 'three_seeds', passed: true, evidence: { seeds: [11, 29, 47] } },
    { id: 'zero_policy_violations', passed: true, evidence: { violations: 0 } },
  ],
  claimBoundary: 'Fixture promotion only.',
});
assert.equal(promote.decision, 'promote');

const blocked = buildTrainingPromotionDecision({
  workloadId: 'wgsl-v9-fixture',
  decisionId: 'wgsl-v9-fixture-blocked',
  candidatePolicyHash: 'f'.repeat(64),
  promotionVerifierSplitHash: '1'.repeat(64),
  gates: [{ id: 'sealed_eval', passed: false, evidence: null }],
  claimBoundary: 'Fixture promotion only.',
});
assert.equal(blocked.decision, 'blocked');

const update = buildTrainingPolicyUpdate({
  workloadId: 'wgsl-v9-fixture',
  updateId: 'wgsl-v9-fixture-update',
  inputPolicyHash: '2'.repeat(64),
  outputPolicyHash: '3'.repeat(64),
  parentRolloutHashes: [hashVerifierGuidedArtifact(rolloutGroup)],
  objective: { id: 'grpo_clipped_kl_v1' },
  metrics: { loss: 0.25 },
  claimBoundary: 'Fixture update only.',
});
const updateHash = hashVerifierGuidedArtifact(update);
const checkpoint = buildTrainingPolicyCheckpoint({
  workloadId: 'wgsl-v9-fixture',
  checkpointId: 'wgsl-v9-fixture-checkpoint',
  policyHash: '3'.repeat(64),
  datasetHash: '4'.repeat(64),
  parentArtifactHashes: [updateHash],
  adapterPath: '/tmp/fixture-adapter',
  checkpointStep: 1,
  metrics: { loss: 0.25 },
  claimBoundary: 'Fixture checkpoint only.',
});
assert.equal(checkpoint.policyHash, '3'.repeat(64));

console.log('wgsl-repair-contract.test: ok');
