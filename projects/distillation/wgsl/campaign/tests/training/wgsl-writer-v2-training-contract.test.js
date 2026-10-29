import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

import { loadTrainingWorkloadCapsule } from '../../src/experimental/training/workloads.js';
import { buildWriterSeedWorkload } from '../../tools/materialize-wgsl-writer-v2-seed-workloads.js';
import { runWgslWriterV2Training } from '../../tools/run-wgsl-writer-v2-training.js';

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'));
}

function sha256File(filePath) {
  return createHash('sha256').update(readFileSync(filePath)).digest('hex');
}

function sha256Value(value) {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}

function assertInternalHash(value, field) {
  const core = { ...value };
  const expected = core[field];
  delete core[field];
  assert.equal(sha256Value(core), expected);
}

const policyPath = 'tools/policies/wgsl-writer-v2-training-policy.json';
const policy = readJson(policyPath);
const corpusManifest = readJson(policy.admission.corpusManifest.path);
const qualification = readJson(policy.admission.referenceQualification.path);
const registry = readJson(policy.admission.workloadRegistry.path);

assert.equal(policy.policyId, 'doppler-wgsl-writer-v2-training');
assert.equal(policy.status, 'frozen_before_training');
assert.equal(policy.dataset.rows, 720);
assert.equal(policy.dataset.semanticFamilies, 15);
assert.equal(policy.dataset.rowConsumption, 'each_row_exactly_once_per_seed');
assert.deepEqual(policy.trainer.executionOrder, [11, 29, 47]);
assert.equal(policy.trainer.parallelSeedsAllowed, false);
assert.equal(policy.generation.maxTokensDerivation.holdoutOutcomesUsed, false);
assert.equal(policy.generation.maxTokensDerivation.maximumTargetTokensIncludingEos, 263);
assert.equal(policy.generation.maxTokens, 384);
assert.equal(policy.evaluation.checkpointSelection.submissionsPerCandidate, 1);
assert.equal(policy.evaluation.seedConfirmation.openAfterCheckpointSelection, true);
assert.equal(policy.evaluation.promotion.status, 'external_custody_required');
assert.equal(policy.authority.promotion, false);
assert.equal(policy.authority.generalWgslWriterClaim, false);

for (const binding of [
  policy.admission.corpusPolicy,
  policy.admission.corpusManifest,
  policy.admission.referenceQualification,
  policy.admission.workloadRegistry,
  policy.dataset,
]) {
  assert.equal(sha256File(binding.path), binding.sha256, binding.path);
}
assertInternalHash(corpusManifest, 'manifestSha256');
assertInternalHash(qualification, 'receiptHash');
assert.equal(qualification.decision, 'reference_corpus_qualified');
assert.equal(qualification.trainingAdmission, true);
assert.equal(registry.registryHash, policy.admission.workloadRegistry.registryHash);
assert.equal(corpusManifest.roles.training.datasetSha256, policy.dataset.sha256);
assert.equal(corpusManifest.roles.training.rows, policy.dataset.rows);
assert.equal(
  corpusManifest.roles.training.semanticFamilyCount,
  policy.dataset.semanticFamilies
);

const template = readJson(policy.workloads[0].path);
for (const binding of policy.workloads) {
  assert.equal(sha256File(binding.path), binding.sha256, binding.path);
  const loaded = await loadTrainingWorkloadCapsule(binding.path);
  assert.equal(loaded.workload.seed, binding.seed);
  assert.equal(loaded.workload.datasetPath, policy.dataset.path);
  assert.equal(loaded.workload.training.steps, policy.trainer.training.steps);
  assert.equal(loaded.workload.training.accumSteps, 8);
  assert.equal(loaded.workload.pipeline.rowOrder, policy.dataset.rowOrder);
  assert.equal(loaded.workload.pipeline.adapter.rank, 32);
  assert.equal(loaded.workload.pipeline.export.select, 'final');
  const registryEntry = registry.workloads.find((entry) => entry.id === loaded.workload.id);
  assert.ok(registryEntry, loaded.workload.id);
  assert.equal(registryEntry.sha256, binding.sha256);
}
assert.deepEqual(
  buildWriterSeedWorkload(template, 29),
  readJson(policy.workloads.find((entry) => entry.seed === 29).path)
);
assert.deepEqual(
  buildWriterSeedWorkload(template, 47),
  readJson(policy.workloads.find((entry) => entry.seed === 47).path)
);

await assert.rejects(
  runWgslWriterV2Training({ policyPath, seed: 13 }),
  /seed is not frozen/
);

console.log('wgsl-writer-v2-training-contract.test: ok');
