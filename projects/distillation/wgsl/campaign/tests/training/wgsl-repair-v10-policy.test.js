import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import test from 'node:test';

import { sha256BytesHex } from '../../src/utils/sha256.js';

const v9 = JSON.parse(await readFile('tools/policies/wgsl-repair-v9-policy.json', 'utf8'));
const v10 = JSON.parse(await readFile('tools/policies/wgsl-repair-v10-policy.json', 'utf8'));
const derivation = v10.methods.rollout.maxTokensDerivation;

assert.equal(v10.policyId, 'doppler-wgsl-repair-v10');
assert.equal(v10.status, 'frozen');
assert.equal(v10.models.primary.modelId, 'Qwen/Qwen3.5-9B');
assert.equal(v10.models.primary.revision, 'c202236235762e1c871ad0ccb60c8ee5ba337b9a');
assert.equal(v10.methods.sft.evaluationCheckpoint.parentPolicyId, v9.policyId);
assert.equal(
  v10.methods.sft.evaluationCheckpoint.policyHash,
  'fcba6cbbfee3b52de597be8df7400ae601f6fdbc15989946da543cb299eebc87'
);
assert.equal(v10.methods.rollout.maxTokens, 64);
assert.equal(derivation.maximumTargetTokensIncludingEos, 41);
assert.equal(derivation.marginTokens, 23);
assert.equal(
  derivation.maximumTargetTokensIncludingEos + derivation.marginTokens,
  v10.methods.rollout.maxTokens
);
assert.equal(derivation.holdoutOutcomesUsed, false);
assert.equal(derivation.sourceRows, 1200);
test('retained V10 token-budget derivation bytes match their frozen digest', {
  skip: existsSync(derivation.sourcePath) ? false : `Local evidence unavailable: ${derivation.sourcePath}`,
}, async () => {
  const sourceBytes = new Uint8Array(await readFile(derivation.sourcePath));
  assert.equal(await sha256BytesHex(sourceBytes), derivation.sourceSha256);
});
assert.equal(v10.verifier.protocolRevision, 2);
assert.equal(v10.verifier.browser.compilationTimeoutMs, 10000);
assert.equal(v10.verifier.browser.progressEvery, 100);
assert.equal(v10.verifier.priorBlockedAttempt.groupCount, 299);
assert.equal(v10.verifier.priorBlockedAttempt.sampleCount, 2392);
assert.equal(v10.verifier.priorBlockedAttempt.scoreArtifactsWritten, false);
assert.equal(
  v10.verifier.priorBlockedAttempt.rawRolloutSha256,
  'd0b3569ff54fafbf55c2bf1190325263c8caa35ad30e05d9471bcbd6df5af813'
);

const comparableV9 = structuredClone(v9);
const comparableV10 = structuredClone(v10);
comparableV10.policyId = comparableV9.policyId;
comparableV10.claimBoundary = comparableV9.claimBoundary;
delete comparableV10.methods.sft.evaluationCheckpoint;
delete comparableV10.methods.rollout.maxTokensDerivation;
comparableV10.methods.rollout.maxTokens = comparableV9.methods.rollout.maxTokens;
delete comparableV10.verifier.protocolRevision;
delete comparableV10.verifier.compilationFailurePolicy;
delete comparableV10.verifier.sessionResetPolicy;
delete comparableV10.verifier.priorBlockedAttempt;
delete comparableV10.verifier.browser.compilationTimeoutMs;
delete comparableV10.verifier.browser.progressEvery;
assert.deepEqual(
  comparableV10,
  comparableV9,
  'V10 may change only the declared checkpoint, rollout ceiling, and fail-closed verifier revision.'
);

console.log('wgsl-repair-v10-policy.test: ok');
