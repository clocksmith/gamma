import assert from 'node:assert/strict';

import {
  buildWgslRepairTask,
  createWgslRepairMutations,
} from '../../src/experimental/training/wgsl-repair.js';
import {
  deriveWgslTrainingRows,
  verifyRawWgslRollouts,
} from '../../tools/lib/wgsl-rollout-verifier.js';

const source = `
@group(0) @binding(0) var<storage, read_write> output: array<f32>;
@compute @workgroup_size(1)
fn main(@builtin(global_invocation_id) id: vec3<u32>) {
  let index = id.x;
  output[index] = f32(index);
}
`.trim();
const mutation = createWgslRepairMutations(source).find((entry) => (
  entry.operator === 'identifier_reference'
));
const task = buildWgslRepairTask({
  sourceId: 'doppler',
  sourcePath: 'src/gpu/kernels/rollout_fixture.wgsl',
  revision: 'a'.repeat(40),
  license: 'Apache-2.0',
  source,
}, mutation);
task.verification = { mutantCompileFailed: true };

const policy = {
  methods: {
    rlvr: { groupSize: 8, advantageEpsilon: 1e-6 },
    dpo: { minimumRewardGap: 0.5 },
  },
  verifier: {
    browser: {},
    bundleId: 'fixture',
  },
};
const rawGroups = [{
  taskId: task.taskId,
  groupId: `${task.taskId}-group-1`,
  sampling: { seed: 11, temperature: 0.8, topP: 0.95, maxTokens: 64 },
  samples: [
    {
      sampleId: 'bad',
      prompt: task.prompt,
      completion: ' ',
      tokenIds: [1, 2],
      completionMask: [0, 1],
      policyTokenLogprobs: [-0.4],
      referenceTokenLogprobs: [-0.5],
      stopReason: 'eos',
    },
    {
      sampleId: 'good',
      prompt: task.prompt,
      completion: task.completion,
      tokenIds: [1, 3],
      completionMask: [0, 1],
      policyTokenLogprobs: [-0.2],
      referenceTokenLogprobs: [-0.3],
      stopReason: 'eos',
    },
  ],
}];

const verifier = {
  deviceInfo: { vendor: 'fixture', architecture: 'fixture' },
  browserArgs: ['--fixture'],
  async compile(entries) {
    return entries.map((entry) => ({
      id: entry.id,
      sourceSha256: '0'.repeat(64),
      passed: entry.code === source,
      messages: entry.code === source ? [] : [{ type: 'error', message: 'fixture error' }],
      errorCount: entry.code === source ? 0 : 1,
    }));
  },
};

const verified = await verifyRawWgslRollouts({
  policy,
  tasks: [task],
  rawGroups,
  verifier,
  workloadId: 'wgsl-rollout-fixture',
  datasetHash: '1'.repeat(64),
  policyHash: '2'.repeat(64),
  referencePolicyHash: '3'.repeat(64),
  expectedGroupSize: 2,
});
assert.equal(verified.groups.length, 1);
assert.equal(verified.reports.length, 2);
assert.equal(verified.receipt.passingSamples, 1);
assert.equal(verified.receipt.passingTasksAt1, 0);
assert.equal(verified.receipt.passingTasksAtK, 1);
assert.equal(verified.receipt.passAt1, 0);
assert.equal(verified.receipt.passAtK, 1);
assert.equal(verified.receipt.exactReferenceSamples, 1);
assert.equal(verified.receipt.blockedSamples, 1);
assert.equal(verified.receipt.expectedGroupSize, 2);
assert.deepEqual(verified.groups[0].samples.map((sample) => sample.advantage), [-1, 1]);
assert.equal(verified.groups[0].rolloutPurpose, 'training');

const derived = deriveWgslTrainingRows(verified.groups, policy);
assert.equal(derived.rejectionRows.length, 1);
assert.equal(derived.rejectionRows[0].sampleId, 'good');
assert.equal(derived.dpoRows.length, 1);
assert.equal(derived.dpoRows[0].chosenSampleId, 'good');
assert.equal(derived.dpoRows[0].rejectedSampleId, 'bad');
assert.equal(derived.referenceAnchoredDpoRows.length, 0);

const evaluationGroups = rawGroups.map((group) => ({
  ...group,
  samples: group.samples.map(({ policyTokenLogprobs, referenceTokenLogprobs, ...sample }) => sample),
}));
const evaluated = await verifyRawWgslRollouts({
  policy,
  tasks: [task],
  rawGroups: evaluationGroups,
  verifier,
  workloadId: 'wgsl-evaluation-fixture',
  datasetHash: '1'.repeat(64),
  policyHash: '2'.repeat(64),
  referencePolicyHash: '3'.repeat(64),
  expectedGroupSize: 2,
  rolloutPurpose: 'evaluation',
});
assert.equal(evaluated.groups[0].rolloutPurpose, 'evaluation');
assert.equal(evaluated.receipt.rolloutPurpose, 'evaluation');
assert.equal('policyTokenLogprobs' in evaluated.groups[0].samples[0], false);
assert.throws(
  () => deriveWgslTrainingRows(evaluated.groups, policy),
  /Evaluation-only rollout groups cannot produce optimizer training rows/
);

console.log('wgsl-rollout-verifier.test: ok');
