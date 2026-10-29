import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

import {
  buildWgslRepairV13ConfirmationPopulation,
} from '../../tools/materialize-wgsl-repair-v13-confirmation.js';

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'));
}

function sha256(value) {
  return createHash('sha256').update(value).digest('hex');
}

function sha256File(filePath) {
  return sha256(readFileSync(filePath));
}

const policy = readJson(
  'tools/policies/wgsl-repair-v13-confirmation-materialization-policy.json'
);
const catalog = readJson(policy.catalog.path);
const priorManifests = [
  'tools/data/wgsl-repair-v13-semantic-task-qualification.json',
  'tools/data/wgsl-repair-v13-semantic-calibration.json',
  'tools/data/wgsl-repair-v13-semantic-checkpoint-selection.json',
].map(readJson);

assert.equal(policy.status, 'frozen_before_population_materialization');
assert.equal(policy.selection.taskCount, 8);
assert.equal(policy.catalog.eligibleBlueprintCount, 12);
assert.equal(policy.authority.candidateInferenceBeforePopulationFreeze, false);
assert.equal(policy.authority.seedConfirmation, true);
assert.equal(policy.authority.promotion, false);
assert.equal(policy.authority.wgslDoctor, false);
assert.equal(policy.authority.completeShaderWriting, false);
assert.equal(sha256File(policy.generator.path), policy.generator.sha256);
assert.equal(sha256File(policy.catalog.path), policy.catalog.sha256);
assert.equal(
  sha256File(policy.oracleImplementation.path),
  policy.oracleImplementation.sha256
);

const freezeCommit = 'a'.repeat(40);
const first = buildWgslRepairV13ConfirmationPopulation({
  policy,
  catalog,
  freezeCommit,
});
const replay = buildWgslRepairV13ConfirmationPopulation({
  policy,
  catalog,
  freezeCommit,
});
assert.deepEqual(replay, first);
assert.equal(first.manifest.role, 'seed_confirmation');
assert.equal(first.manifest.tasks.length, policy.selection.taskCount);
assert.equal(first.manifest.materialization.freezeCommit, freezeCommit);
assert.equal(first.manifest.materialization.eligibleBlueprintCount, catalog.blueprints.length);
assert.equal(new Set(first.manifest.materialization.selectedBlueprintIds).size, 8);
const selectedBlueprints = new Map(catalog.blueprints.map((entry) => [entry.id, entry]));
assert.equal(first.manifest.tasks.filter((task) => (
  selectedBlueprints.get(task.taskId.replace('v13-confirmation-', '')).arity === 'unary'
)).length, 4);
assert.equal(first.manifest.tasks.filter((task) => (
  selectedBlueprints.get(task.taskId.replace('v13-confirmation-', '')).arity === 'binary'
)).length, 4);
assert.equal(first.manifest.tasks.filter((task) => Object.keys(task.parameters).length > 0).length, 4);
assert.equal(first.manifest.tasks.filter((task) => Object.keys(task.parameters).length === 0).length, 4);

const priorTaskIds = new Set();
const priorFamilies = new Set();
const priorOracles = new Set();
const priorSources = new Set();
const priorInputSeeds = new Set();
for (const manifest of priorManifests) {
  for (const task of manifest.tasks) {
    priorTaskIds.add(task.taskId);
    priorFamilies.add(task.kernelFamilyId);
    priorOracles.add(task.oracleId);
    priorSources.add(task.sourcePath);
    priorInputSeeds.add(task.inputSeed);
  }
}

for (const task of first.manifest.tasks) {
  const blueprintId = task.taskId.replace('v13-confirmation-', '');
  const blueprint = selectedBlueprints.get(blueprintId);
  assert.ok(blueprint, `missing blueprint for ${task.taskId}`);
  assert.ok(!priorTaskIds.has(task.taskId));
  assert.ok(!priorFamilies.has(task.kernelFamilyId));
  assert.ok(!priorOracles.has(task.oracleId));
  assert.ok(!priorSources.has(task.sourcePath));
  assert.ok(!priorInputSeeds.has(task.inputSeed));
  const source = first.sources[task.sourcePath];
  assert.equal(typeof source, 'string');
  assert.equal(sha256(source), task.sourceSha256);
  assert.equal(source.split(task.brokenSpan).length - 1, 1);
  assert.equal(source.includes(task.referenceSpan), false);
  assert.deepEqual(
    task.variants.map((variant) => variant.shapeClass),
    ['nominal', 'non_workgroup_multiple', 'boundary_or_tail']
  );
  assert.equal(new Set(task.variants.map((variant) => variant.workgroupId)).size, 2);
  if (blueprint.parameter == null) {
    assert.deepEqual(task.parameters, {});
  } else {
    assert.ok(blueprint.parameter.values.includes(task.parameters[blueprint.parameter.name]));
  }
}

console.log('wgsl-repair-v13-confirmation-materialization-contract.test: ok');
