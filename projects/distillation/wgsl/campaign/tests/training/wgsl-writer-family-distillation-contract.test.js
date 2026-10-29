import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const ROOT = path.resolve('.');
const POLICY_PATH = path.join(ROOT, 'tools/policies/wgsl-writer-family-distillation-policy.json');

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function sha256(filePath) {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

const policy = readJson(POLICY_PATH);
assert.equal(policy.policyId, 'doppler-wgsl-writer-family-distillation-v1');
assert.equal(policy.teacher.tokenizerSha256, policy.students[0].tokenizerSha256);
assert.equal(policy.students[0].trainingSnapshotProvisioned, true);
assert.equal(policy.students[1].trainingSnapshotProvisioned, false);
assert.ok(policy.students[1].blocker.includes('SafeTensors'));

const transportBinding = policy.sourceAdapterSet.transportRequest;
const transportRequestPath = path.join(ROOT, transportBinding.path);
test('retained family-distillation transport and adapter byte custody', {
  skip: fs.existsSync(transportRequestPath) ? false : `Local evidence unavailable: ${transportBinding.path}`,
}, () => {
  assert.equal(sha256(transportRequestPath), transportBinding.sha256);
  const transportRequest = readJson(transportRequestPath);
  assert.equal(transportRequest.action, 'transport');
  const sourceAdapterRequestPath = transportRequest.sourceAdapterSet?.requestPath
    ? path.resolve(transportRequest.sourceAdapterSet.requestPath)
    : transportRequestPath;
  if (transportRequest.sourceAdapterSet?.requestPath) {
    assert.equal(sha256(sourceAdapterRequestPath), transportRequest.sourceAdapterSet.requestSha256);
  }
  const sourceAdapterRequest = readJson(sourceAdapterRequestPath);
  assert.equal(sourceAdapterRequest.sourceAdapters.length, policy.sourceAdapterSet.includedAdapters);
  assert.equal(
    sourceAdapterRequest.sourceAdapters.reduce((sum, adapter) => sum + adapter.weight, 0),
    1,
  );
  assert.ok(sourceAdapterRequest.sourceAdapters.every((adapter) => !adapter.id.includes('control')));
  for (const adapter of sourceAdapterRequest.sourceAdapters) {
    assert.equal(sha256(path.join(adapter.path, 'adapter_config.json')), adapter.configSha256);
    assert.equal(sha256(path.join(adapter.path, 'adapter_model.safetensors')), adapter.weightsSha256);
  }
});

assert.deepEqual(policy.arms.map((arm) => arm.id), [
  'lwsc-v2-sft',
  'llm-neo',
  'delta-kd',
  'sequence-kd',
]);
for (const arm of policy.arms) {
  assert.equal(arm.dopplerExportPath.endsWith('/doppler-export'), true);
  assert.equal(arm.dopplerExportPath.includes('/checkpoint/'), false);
}
assert.equal(policy.fairness.rank, 32);
assert.equal(policy.fairness.microsteps, policy.dataset.rows);
assert.equal(
  policy.fairness.optimizerUpdates,
  policy.fairness.microsteps / policy.fairness.gradientAccumulationSteps,
);
assert.equal(policy.dataset.outputTokenBudget, policy.evaluation.generation.maxNewTokens);
assert.equal(policy.evaluation.surface, 'chromium_webgpu');
assert.equal(policy.evaluation.backend, 'vulkan');

console.log('wgsl-writer-family-distillation-contract.test: ok');
