import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

import { selectWgslRepairV13Seed } from '../../tools/select-wgsl-repair-v13-seed.js';

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'));
}

function sha256File(filePath) {
  // Frozen experiment receipts bind the pre-migration conversion configuration.
  if (filePath.startsWith('src/config/conversion/')) filePath = `tests/fixtures/pre-capsule/${filePath}`;
  return createHash('sha256').update(readFileSync(filePath)).digest('hex');
}

const policyPath = 'tools/policies/wgsl-repair-v13-seed-selection-policy.json';
const policy = readJson(policyPath);
const state = readJson('tools/data/wgsl-repair-v13-semantic-evidence-state.json');
const mechanics = readJson('tools/data/wgsl-repair-v13-semantic-task-qualification.json');
const calibration = readJson(policy.populations.calibration.path);
const checkpointSelection = readJson(policy.populations.checkpointSelection.path);
const preservation = readJson('docs/status/wgsl-repair-v12-adapter-preservation-2026-07-13.json');
const preservedBySeed = new Map(preservation.artifacts.map((artifact) => [artifact.seed, artifact]));

assert.equal(policy.status, 'frozen_before_candidate_evaluation');
assert.equal(policy.eligibleLane, 'external20');
assert.deepEqual(policy.eligibleCandidates.map((entry) => entry.seed), [11, 29, 47]);
assert.equal(policy.promptContract.contextCharactersPerSide, 600);
assert.equal(policy.promptContract.useChatTemplate, false);
assert.equal(policy.generation.temperature, 0);
assert.equal(policy.generation.topK, 1);
assert.deepEqual(policy.ranking.lexicographicOrder, [
  'semantic_task_pass_count_desc',
  'compile_pass_count_desc',
  'semantic_variant_pass_count_desc',
  'exact_reference_completion_count_desc',
  'seed_asc',
]);

assert.equal(sha256File(policy.populations.calibration.path), policy.populations.calibration.sha256);
assert.equal(
  sha256File(policy.populations.checkpointSelection.path),
  policy.populations.checkpointSelection.sha256
);
assert.equal(
  sha256File(policy.predecessor.adapterPortabilityReceiptPath),
  policy.predecessor.adapterPortabilityReceiptSha256
);
assert.equal(
  sha256File(policy.runtime.artifactStatusPath),
  policy.runtime.artifactStatusSha256
);
assert.equal(
  sha256File(policy.runtime.conversionConfigPath),
  policy.runtime.conversionConfigSha256
);
for (const candidate of policy.eligibleCandidates) {
  assert.equal(sha256File(candidate.adapterManifestPath), candidate.adapterManifestSha256);
  const preserved = preservedBySeed.get(candidate.seed);
  assert.ok(preserved, `missing preserved adapter identity for seed ${candidate.seed}`);
  assert.equal(preserved.localPath, candidate.adapterWeightsPath);
  assert.equal(preserved.sha256, candidate.adapterWeightsSha256);
  assert.equal(preserved.externalVerification?.observedSha256, candidate.adapterWeightsSha256);
  assert.equal(preserved.externalVerification?.ok, true);
}
assert.equal(preservation.externalPreservation.status, 'complete');

assert.equal(calibration.role, 'calibration');
assert.equal(calibration.populationAuthority, 'prompt_and_harness_calibration_only');
assert.equal(checkpointSelection.role, 'checkpoint_selection');
assert.equal(checkpointSelection.populationAuthority, 'external20_seed_selection_only');
assert.equal(state.populations.calibration.status, 'frozen');
assert.equal(state.populations.calibration.populationHash, policy.populations.calibration.sha256);
assert.equal(state.populations.checkpointSelection.status, 'frozen');
assert.equal(
  state.populations.checkpointSelection.populationHash,
  policy.populations.checkpointSelection.sha256
);
assert.equal(state.populations.seedConfirmation.status, 'frozen');
assert.equal(
  sha256File(state.populations.seedConfirmation.manifestPath),
  state.populations.seedConfirmation.populationHash
);
assert.equal(state.populations.promotion.status, 'unmaterialized');
assert.equal(state.candidate.seedSelectionStatus, 'selected');
assert.equal(state.candidate.selectedSeed, 29);
assert.equal(preservedBySeed.get(29).sha256, state.candidate.adapterSha256);
assert.equal(
  sha256File(state.candidate.selectionReceiptPath),
  state.candidate.selectionReceiptSha256
);

const manifests = [mechanics, calibration, checkpointSelection];
const familyRoles = new Map();
const sourceRoles = new Map();
const inputSeedRoles = new Map();
for (const manifest of manifests) {
  for (const task of manifest.tasks) {
    assert.ok(!familyRoles.has(task.kernelFamilyId), `${task.kernelFamilyId} overlaps roles`);
    assert.ok(!sourceRoles.has(task.sourcePath), `${task.sourcePath} overlaps roles`);
    assert.ok(!inputSeedRoles.has(task.inputSeed), `${task.inputSeed} overlaps roles`);
    familyRoles.set(task.kernelFamilyId, manifest.role);
    sourceRoles.set(task.sourcePath, manifest.role);
    inputSeedRoles.set(task.inputSeed, manifest.role);
    assert.equal(sha256File(task.sourcePath), task.sourceSha256);
    const source = readFileSync(task.sourcePath, 'utf8').trim();
    assert.equal(source.split(task.brokenSpan).length - 1, 1);
    assert.equal(source.includes(task.referenceSpan), false);
    assert.equal(task.variants.length, 3);
    assert.equal(new Set(task.variants.map((variant) => variant.workgroupId)).size, 2);
  }
}

const selectionReceipt = readJson(state.candidate.selectionReceiptPath);
const replayedSelection = await selectWgslRepairV13Seed({
  policyPath,
  receiptPaths: [11, 29, 47].map((seed) => (
    `reports/training/wgsl-repair/doppler-wgsl-repair-v13/checkpoint-selection/seed${seed}.semantic.json`
  )),
});
assert.deepEqual(replayedSelection, selectionReceipt);
assert.equal(selectionReceipt.selected.seed, 29);
assert.deepEqual(
  selectionReceipt.rankedCandidates.map((entry) => entry.seed),
  [29, 11, 47]
);
assert.equal(selectionReceipt.seedConfirmationSatisfied, false);
assert.equal(selectionReceipt.promotionAuthority, false);

console.log('wgsl-repair-v13-seed-selection-contract.test: ok');
