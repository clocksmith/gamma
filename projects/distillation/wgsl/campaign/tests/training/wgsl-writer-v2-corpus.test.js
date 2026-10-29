import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { parseCompleteWgslResponse } from '../../tools/lib/wgsl-writer-semantic-harness.js';
import {
  checkWgslWriterCorpus,
  materializeWgslWriterCorpus,
  validateWgslWriterBlueprintCatalog,
} from '../../tools/lib/wgsl-writer-corpus.js';

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'));
}

function sha256File(filePath) {
  return createHash('sha256').update(readFileSync(filePath)).digest('hex');
}

const policyPath = 'tools/policies/wgsl-writer-v2-corpus-policy.json';
const policy = readJson(policyPath);
const catalog = readJson(policy.corpus.blueprintCatalog.path);

assert.equal(policy.policyId, 'doppler-wgsl-writer-v2-corpus');
assert.equal(policy.status, 'frozen_before_materialization_and_training');
assert.equal(policy.capability, catalog.taskScope);
assert.equal(policy.authority.promotion, false);
assert.equal(policy.authority.generalWgslWriterClaim, false);
assert.equal(
  sha256File(policy.corpus.blueprintCatalog.path),
  policy.corpus.blueprintCatalog.sha256
);
for (const binding of [
  policy.predecessor.mechanicsPolicy,
  policy.predecessor.referenceReceipt,
  policy.predecessor.zeroShotResult,
]) {
  assert.equal(sha256File(binding.path), binding.sha256, binding.path);
}

validateWgslWriterBlueprintCatalog(catalog);
assert.equal(catalog.blueprints.length, 21);
assert.deepEqual(catalog.excludedOracleIds, ['add_f32', 'affine_f32', 'clamp_f32']);
assert.equal(new Set(catalog.blueprints.map((entry) => entry.id)).size, 21);
assert.equal(new Set(catalog.blueprints.map((entry) => entry.oracleId)).size, 21);

const materialized = materializeWgslWriterCorpus({
  repoRoot: resolve('.'),
  outputRoot: resolve(policy.corpus.outputRoot),
  catalog,
  policy,
  policyPath,
  policySha256: sha256File(policyPath),
});
await checkWgslWriterCorpus(materialized);

assert.deepEqual(
  Object.fromEntries(Object.entries(materialized.rowsByRole).map(([role, rows]) => [
    role,
    rows.length,
  ])),
  {
    training: 720,
    calibration: 16,
    checkpoint_selection: 16,
    seed_confirmation: 16,
  }
);
assert.deepEqual(
  Object.fromEntries(Object.entries(materialized.manifest.roles).map(([role, entry]) => [
    role,
    entry.semanticFamilyCount,
  ])),
  {
    training: 15,
    calibration: 2,
    checkpoint_selection: 2,
    seed_confirmation: 2,
  }
);
assert.deepEqual(materialized.manifest.isolation.semanticFamilyOverlaps, []);
assert.equal(materialized.manifest.isolation.duplicateRowIds, 0);
assert.equal(materialized.manifest.isolation.duplicatePrompts, 0);
assert.equal(
  materialized.manifest.isolation.visibleMechanicsPopulationUsedForTraining,
  false
);
assert.equal(materialized.manifest.promotion.status, 'external_custody_required');
assert.equal(materialized.manifest.promotion.rows, 0);
assert.equal(materialized.qualificationManifest.tasks.length, 63);

const promptHashes = new Set();
const taskIds = new Set();
for (const [role, tasks] of Object.entries(materialized.tasksByRole)) {
  for (const task of tasks) {
    assert.equal(task.populationRole, role);
    assert.equal(taskIds.has(task.taskId), false, task.taskId);
    taskIds.add(task.taskId);
    const parsed = parseCompleteWgslResponse(
      task.referenceShader,
      readJson(policy.predecessor.mechanicsPolicy.path).taskContract.responseEnvelope,
      task.interfaceContract
    );
    assert.equal(parsed.ok, true, task.taskId);
    assert.match(task.referenceShader, /\[[a-z][a-z0-9_]*\]/);
    assert.equal(task.variants.length, 3);
  }
  for (const row of materialized.rowsByRole[role]) {
    assert.equal(promptHashes.has(row.promptSha256), false, row.rowId);
    promptHashes.add(row.promptSha256);
    assert.equal(row.populationRole, role);
    assert.equal(row.taskContract, 'complete_wgsl_compute_shader_only_v1');
    assert.equal(row.sourceLicense, 'Apache-2.0');
    assert.equal(row.sourceLineage, 'doppler_owned_parametric_blueprint');
  }
}

const duplicateCatalog = structuredClone(catalog);
duplicateCatalog.blueprints[1].oracleId = duplicateCatalog.blueprints[0].oracleId;
assert.throws(
  () => validateWgslWriterBlueprintCatalog(duplicateCatalog),
  /Duplicate WGSL writer oracle/
);
const excludedCatalog = structuredClone(catalog);
excludedCatalog.blueprints[0].oracleId = 'add_f32';
assert.throws(
  () => validateWgslWriterBlueprintCatalog(excludedCatalog),
  /Excluded writer oracle was assigned/
);

console.log('wgsl-writer-v2-corpus.test: ok');
