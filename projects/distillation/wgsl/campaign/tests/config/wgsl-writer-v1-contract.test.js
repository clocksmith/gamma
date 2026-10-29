import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

import {
  buildWgslWriterPrompt,
  parseCompleteWgslResponse,
} from '../../tools/lib/wgsl-writer-semantic-harness.js';

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'));
}

function sha256File(filePath) {
  // Frozen experiment receipts bind the pre-migration conversion configuration.
  if (filePath.startsWith('src/config/conversion/')) filePath = `tests/fixtures/pre-capsule/${filePath}`;
  return createHash('sha256').update(readFileSync(filePath)).digest('hex');
}

const policyPath = 'tools/policies/wgsl-writer-v1-policy.json';
const policy = readJson(policyPath);
const manifest = readJson(policy.mechanics.taskManifest.path);

assert.equal(policy.policyId, 'doppler-wgsl-writer-v1');
assert.equal(policy.status, 'frozen_mechanics_before_reference_execution');
assert.equal(policy.claimInheritance.repairEvidenceTransfers, false);
assert.equal(policy.claimInheritance.v13MayBeTestedOnlyAsInitialization, true);
assert.equal(policy.mechanics.populationAuthority, 'none');
assert.equal(policy.mechanics.referenceExecution.status, 'not_run_at_policy_freeze');
assert.equal(policy.mechanics.referenceExecution.mustCommitBeforeCandidateInference, true);
assert.equal(policy.authority.mechanicsQualification, true);
assert.equal(policy.authority.candidateEvaluation, false);
assert.equal(policy.authority.checkpointSelection, false);
assert.equal(policy.authority.seedConfirmation, false);
assert.equal(policy.authority.promotion, false);
assert.equal(policy.authority.productization, false);

for (const binding of [
  policy.mechanics.taskManifest,
  policy.implementation.semanticHarness,
  policy.implementation.semanticLibrary,
  policy.implementation.repairSemanticLibrary,
  policy.implementation.browserVerifier,
  policy.implementation.historicalRegressions,
]) {
  assert.equal(sha256File(binding.path), binding.sha256, binding.path);
}
for (const binding of [
  [policy.runtime.artifactStatusPath, policy.runtime.artifactStatusSha256],
  [policy.runtime.conversionConfigPath, policy.runtime.conversionConfigSha256],
  [
    policy.runtime.adapterPortabilityReceiptPath,
    policy.runtime.adapterPortabilityReceiptSha256,
  ],
]) {
  assert.equal(sha256File(binding[0]), binding[1], binding[0]);
}

assert.equal(manifest.schema, 'doppler.wgsl-writer-task-manifest/v1');
assert.equal(manifest.experimentId, 'doppler-wgsl-writer-v1');
assert.equal(manifest.role, 'mechanics_qualification_only');
assert.equal(manifest.populationAuthority, 'none');
assert.equal(manifest.tasks.length, 3);
assert.equal(new Set(manifest.tasks.map((task) => task.kernelFamilyId)).size, 3);
assert.equal(new Set(manifest.tasks.map((task) => task.inputSeed)).size, 3);
for (const task of manifest.tasks) {
  assert.equal(sha256File(task.referenceShaderPath), task.referenceShaderSha256);
  assert.equal(task.interfaceContract.entryPoint, 'main');
  assert.equal(task.interfaceContract.stage, 'compute');
  assert.equal(task.variants.length, 3);
  assert.deepEqual(
    [...new Set(task.variants.map((variant) => variant.shapeClass))].sort(),
    ['boundary_or_tail', 'nominal', 'non_workgroup_multiple']
  );
  assert.equal(new Set(task.variants.map((variant) => variant.workgroupId)).size, 2);
  const reference = readFileSync(task.referenceShaderPath, 'utf8');
  const parsed = parseCompleteWgslResponse(
    reference,
    policy.taskContract.responseEnvelope,
    task.interfaceContract
  );
  assert.equal(parsed.ok, true, task.taskId);
  const prompt = buildWgslWriterPrompt(task, policy.promptContract);
  assert.ok(prompt.includes(task.specification));
  assert.ok(prompt.includes(JSON.stringify(task.interfaceContract, null, 2)));
  assert.ok(prompt.includes('Return only the complete WGSL source'));
}

const fenced = parseCompleteWgslResponse(
  '```wgsl\n@compute @workgroup_size(1) fn main() {}\n```',
  policy.taskContract.responseEnvelope,
  manifest.tasks[0].interfaceContract
);
assert.equal(fenced.ok, false);
assert.ok(fenced.violations.includes('markdown_fence'));
assert.ok(fenced.violations.includes('required_override_absent:WORKGROUP_SIZE'));

const candidateIds = policy.candidateInitializations.map((candidate) => candidate.id);
assert.deepEqual(candidateIds, [
  'qwen35-9b-f16-base',
  'v13-seed29-repair-initialization',
]);
const repairInitialization = policy.candidateInitializations[1];
assert.equal(
  sha256File(repairInitialization.predecessorReceiptPath),
  repairInitialization.predecessorReceiptSha256
);
assert.equal(repairInitialization.kind, 'repair_adapter_initialization');

console.log('wgsl-writer-v1-contract.test: ok');
