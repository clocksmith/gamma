import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

import {
  finalizeWgslRepairV13SeedConfirmation,
} from '../../tools/finalize-wgsl-repair-v13-seed-confirmation.js';

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'));
}

function sha256File(filePath) {
  // Frozen experiment receipts bind the pre-migration conversion configuration.
  if (filePath.startsWith('src/config/conversion/')) filePath = `tests/fixtures/pre-capsule/${filePath}`;
  return createHash('sha256').update(readFileSync(filePath)).digest('hex');
}

const policyPath = 'tools/policies/wgsl-repair-v13-seed-confirmation-policy.json';
const policy = readJson(policyPath);
const manifest = readJson(policy.populations.seedConfirmation.path);
const selection = readJson(policy.selectionReceipt.path);
const reference = readJson(
  'docs/status/wgsl-repair-v13-seed-confirmation-reference-2026-07-14.json'
);
const resultPath = 'docs/status/wgsl-repair-v13-seed-confirmation-result-2026-07-14.json';
const result = readJson(resultPath);
const catalog = readJson('tools/data/wgsl-repair-v13-confirmation-blueprints.json');
const blueprintById = new Map(catalog.blueprints.map((entry) => [entry.id, entry]));

assert.equal(policy.status, 'frozen_before_candidate_inference');
assert.equal(policy.eligibleLane, 'external20');
assert.deepEqual(policy.eligibleCandidates.map((entry) => entry.seed), [29]);
assert.equal(policy.selectionReceipt.selectedSeed, 29);
assert.equal(sha256File(policy.selectionReceipt.path), policy.selectionReceipt.sha256);
assert.equal(selection.selected.seed, 29);
assert.equal(selection.decision, policy.selectionReceipt.requiredDecision);
assert.equal(sha256File(policy.materialization.policyPath), policy.materialization.policySha256);
assert.equal(sha256File(policy.candidateRunner.path), policy.candidateRunner.sha256);
assert.equal(sha256File(policy.semanticHarness.path), policy.semanticHarness.sha256);
assert.equal(
  sha256File(policy.predecessor.adapterPortabilityReceiptPath),
  policy.predecessor.adapterPortabilityReceiptSha256
);
assert.equal(sha256File(policy.runtime.artifactStatusPath), policy.runtime.artifactStatusSha256);
assert.equal(sha256File(policy.runtime.conversionConfigPath), policy.runtime.conversionConfigSha256);
assert.equal(
  sha256File(policy.eligibleCandidates[0].adapterManifestPath),
  policy.eligibleCandidates[0].adapterManifestSha256
);
assert.equal(sha256File(policy.populations.seedConfirmation.path), policy.populations.seedConfirmation.sha256);

assert.equal(manifest.role, 'seed_confirmation');
assert.equal(manifest.populationAuthority, 'selected_external20_seed_confirmation_only');
assert.equal(manifest.materialization.freezeCommit, policy.materialization.freezeCommit);
assert.equal(manifest.materialization.algorithm, policy.materialization.algorithm);
assert.equal(manifest.materialization.candidateInferenceBeforeFreeze, false);
assert.equal(manifest.tasks.length, policy.decisionRule.requiredSemanticTaskPasses);
assert.equal(policy.decisionRule.submissionCount, 1);
assert.equal(policy.decisionRule.requiredCompilationPasses, manifest.tasks.length);
assert.equal(policy.decisionRule.requiredSemanticVariantPasses, manifest.tasks.length * 3);
assert.equal(policy.decisionRule.requiredResponseContractPasses, manifest.tasks.length);
assert.equal(policy.decisionRule.requiredHistoricalRegressionPasses, manifest.tasks.length);
assert.equal(policy.authority.seedConfirmation, true);
assert.equal(policy.authority.promotion, false);
assert.equal(policy.authority.wgslDoctor, false);
assert.equal(policy.authority.completeShaderWriting, false);

const priorManifests = [
  'tools/data/wgsl-repair-v13-semantic-task-qualification.json',
  'tools/data/wgsl-repair-v13-semantic-calibration.json',
  'tools/data/wgsl-repair-v13-semantic-checkpoint-selection.json',
].map(readJson);
const prior = {
  taskId: new Set(),
  kernelFamilyId: new Set(),
  oracleId: new Set(),
  sourcePath: new Set(),
  inputSeed: new Set(),
};
for (const priorManifest of priorManifests) {
  for (const task of priorManifest.tasks) {
    for (const field of Object.keys(prior)) prior[field].add(task[field]);
  }
}

let unary = 0;
let binary = 0;
let parameterized = 0;
for (const task of manifest.tasks) {
  const blueprintId = task.taskId.replace('v13-confirmation-', '');
  const blueprint = blueprintById.get(blueprintId);
  assert.ok(blueprint, `missing blueprint for ${task.taskId}`);
  if (blueprint.arity === 'unary') unary += 1;
  else binary += 1;
  if (Object.keys(task.parameters).length > 0) parameterized += 1;
  for (const field of Object.keys(prior)) {
    assert.ok(!prior[field].has(task[field]), `${task.taskId} overlaps prior ${field}`);
  }
  assert.equal(sha256File(task.sourcePath), task.sourceSha256);
  const source = readFileSync(task.sourcePath, 'utf8');
  assert.equal(source.split(task.brokenSpan).length - 1, 1);
  assert.equal(source.includes(task.referenceSpan), false);
  assert.equal(task.variants.length, 3);
  assert.equal(new Set(task.variants.map((variant) => variant.workgroupId)).size, 2);
}
assert.equal(unary, 4);
assert.equal(binary, 4);
assert.equal(parameterized, 4);
assert.equal(manifest.tasks.length - parameterized, 4);

assert.equal(reference.decision, 'reference_mechanics_passed');
assert.equal(reference.mode, 'reference');
assert.equal(reference.evaluationRole, 'seed_confirmation');
assert.equal(reference.taskManifest.sha256, policy.populations.seedConfirmation.sha256);
assert.equal(reference.summary.taskCount, manifest.tasks.length);
assert.equal(reference.summary.compilationPasses, manifest.tasks.length);
assert.equal(reference.summary.dispatchVariantPasses, manifest.tasks.length * 3);
assert.equal(reference.summary.historicalRegressionPasses, manifest.tasks.length);
assert.ok(reference.evaluatedTasks.every((task) => task.pass === true));

const replayedResult = await finalizeWgslRepairV13SeedConfirmation({
  policyPath,
  referencePath: result.referenceReceipt.path,
  completionsPath: result.completionReceipt.path,
  semanticPath: result.semanticReceipt.path,
});
assert.deepEqual(replayedResult, result);
assert.equal(result.decision, 'seed_confirmation_passed');
assert.equal(result.seedConfirmationSatisfied, true);
assert.equal(result.metrics.semanticTaskPasses, 8);
assert.equal(result.metrics.semanticVariantPasses, 24);
assert.equal(result.metrics.exactReferenceCompletionCount, 7);
assert.equal(result.promotionAuthority, false);
assert.equal(result.wgslDoctorAllowed, false);
assert.equal(result.completeShaderWritingEstablished, false);

console.log('wgsl-repair-v13-seed-confirmation-contract.test: ok');
