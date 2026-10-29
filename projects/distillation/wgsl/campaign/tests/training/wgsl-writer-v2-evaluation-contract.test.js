import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

import {
  hashWgslSemanticEvidenceValue,
  normalizeWgslSemanticEvidenceValue,
} from '../../src/tooling/wgsl-repair-semantic-gate.js';
import { evaluateWriterSeedConfirmation } from '../../tools/finalize-wgsl-writer-v2-confirmation.js';
import { summarizeWriterCandidate } from '../../tools/run-wgsl-writer-v2-evaluation.js';
import { rankWriterCandidates } from '../../tools/select-wgsl-writer-v2-seed.js';

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'));
}

function sha256File(filePath) {
  return createHash('sha256').update(readFileSync(filePath)).digest('hex');
}

const policy = readJson('tools/policies/wgsl-writer-v2-training-policy.json');
const corpusManifest = readJson(policy.admission.corpusManifest.path);
const parityPolicy = readJson('tools/policies/wgsl-writer-v2-parity-policy.json');

assert.equal(parityPolicy.status, 'frozen_before_checkpoint_selection');
assert.equal(
  sha256File(parityPolicy.predecessor.trainingPolicy.path),
  parityPolicy.predecessor.trainingPolicy.sha256
);
assert.equal(sha256File(parityPolicy.probe.datasetPath), parityPolicy.probe.datasetSha256);
assert.equal(parityPolicy.probe.generation.mode, 'greedy');
assert.equal(parityPolicy.probe.generation.maxNewTokens, policy.generation.maxTokens);
assert.equal(parityPolicy.authority.selectedAdapterOnly, true);
assert.equal(parityPolicy.authority.promotion, false);

for (const [policyKey, corpusKey] of [
  ['calibration', 'calibration'],
  ['checkpointSelection', 'checkpoint_selection'],
  ['seedConfirmation', 'seed_confirmation'],
]) {
  const population = policy.evaluation[policyKey];
  const role = corpusManifest.roles[corpusKey];
  assert.equal(population.populationPath, role.taskManifestPath);
  assert.equal(population.rows, role.rows);
  assert.equal(
    sha256File(role.taskManifestPath),
    corpusManifest.fileBindings[role.taskManifestPath].sha256
  );
  assert.equal(sha256File(role.datasetPath), role.datasetSha256);
}

const tasks = [
  {
    taskId: 'task-1',
    responseContractPass: true,
    responseContractViolations: [],
    compilation: { status: 'pass' },
  },
  {
    taskId: 'task-2',
    responseContractPass: false,
    responseContractViolations: ['markdown_fence'],
    compilation: { status: 'fail' },
  },
];
const summary = summarizeWriterCandidate(
  tasks,
  [{ pass: true }, { pass: false }],
  { 'task-1': 'abcd', 'task-2': '123456' }
);
assert.deepEqual(summary, {
  taskCount: 2,
  semanticPasses: 1,
  semanticPassRate: 0.5,
  compilePasses: 1,
  compilePassRate: 0.5,
  responseContractPasses: 1,
  responseContractPassRate: 0.5,
  meanShaderCharacterCount: 5,
  policyViolationTasks: 1,
  policyViolationRate: 0.5,
});

const ranked = rankWriterCandidates([
  {
    seed: 47,
    summary: {
      semanticPassRate: 0.75,
      compilePassRate: 1,
      responseContractPassRate: 1,
      meanShaderCharacterCount: 600,
    },
  },
  {
    seed: 29,
    summary: {
      semanticPassRate: 0.75,
      compilePassRate: 1,
      responseContractPassRate: 1,
      meanShaderCharacterCount: 590,
    },
  },
  {
    seed: 11,
    summary: {
      semanticPassRate: 0.875,
      compilePassRate: 0.875,
      responseContractPassRate: 0.875,
      meanShaderCharacterCount: 620,
    },
  },
]);
assert.deepEqual(ranked.map((entry) => entry.seed), [11, 29, 47]);
assert.deepEqual(ranked.map((entry) => entry.rank), [1, 2, 3]);

const confirmation = evaluateWriterSeedConfirmation([
  { seed: 11, semanticPassRate: 0.875, submissionOrdinal: 1 },
  { seed: 29, semanticPassRate: 0.75, submissionOrdinal: 1 },
  { seed: 47, semanticPassRate: 0.625, submissionOrdinal: 1 },
], policy.evaluation.seedConfirmation);
assert.equal(confirmation.pass, true);
assert.deepEqual(confirmation.confirmedSeeds, [11, 29, 47]);
assert.equal(confirmation.meanSemanticPassRate, 0.75);

const failedConfirmation = evaluateWriterSeedConfirmation([
  { seed: 11, semanticPassRate: 0.875, submissionOrdinal: 1 },
  { seed: 29, semanticPassRate: 0.375, submissionOrdinal: 1 },
  { seed: 47, semanticPassRate: 0.375, submissionOrdinal: 1 },
], policy.evaluation.seedConfirmation);
assert.equal(failedConfirmation.pass, false);
assert.deepEqual(failedConfirmation.confirmedSeeds, [11]);

const nonFiniteEvidence = normalizeWgslSemanticEvidenceValue({
  maxRelativeError: Number.POSITIVE_INFINITY,
  mismatch: { relativeError: Number.NaN },
});
const persistedNonFiniteEvidence = JSON.parse(JSON.stringify(nonFiniteEvidence));
assert.deepEqual(persistedNonFiniteEvidence, {
  maxRelativeError: { nonFinite: 'positive_infinity' },
  mismatch: { relativeError: { nonFinite: 'nan' } },
});
assert.equal(
  hashWgslSemanticEvidenceValue(nonFiniteEvidence),
  hashWgslSemanticEvidenceValue(persistedNonFiniteEvidence)
);

console.log('wgsl-writer-v2-evaluation-contract.test: ok');
