import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

import {
  buildGoldStudentCandidate,
  buildOuroborosFailureSignals,
  buildStudentPromotionReport,
  buildStudentReplaySummary,
  buildStudentTrainingDatasets,
  evaluateStudentCandidate,
  loadStudentCodeExperimentContracts,
  parseStudentCandidateOutput,
  renderStudentTaskPrompt,
  selectStudentHoldoutTasks,
  verifyStudentCodeExperimentContracts,
} from '../../tools/lib/student-code-experiment.js';

const report = await verifyStudentCodeExperimentContracts();
assert.equal(report.ok, true, report.errors.join('\n'));
assert.deepEqual(report.labelTasks, { javascript: 6, wgsl: 6 });
assert.equal(report.holdoutTasks, 4);

const contracts = await loadStudentCodeExperimentContracts();
for (const harnessFile of [
  'src/config/kernels/kernel-ref-digests.js',
  'src/experimental/training/optimizer.js',
  'src/gpu/kernels/backward/matmul_backward.wgsl',
  'src/gpu/kernels/backward/utils.js',
  'src/memory/buffer-pool.js',
]) {
  assert.equal(
    contracts.policy.harnessFiles.includes(harnessFile),
    true,
    `student experiment must pin ${harnessFile}`
  );
}
function assertTrainingDatasets(trainingDatasets) {
  assert.deepEqual(trainingDatasets.eligibleAcceptedLaneCounts, { javascript: 6, wgsl: 4 });
  assert.equal(trainingDatasets.acceptedLabelCount, 10);
  assert.equal(trainingDatasets.datasets.javascript.sourceRowCount, 6);
  assert.equal(trainingDatasets.datasets.javascript.materializedRowCount, 12);
  assert.equal(trainingDatasets.datasets.wgsl.sourceRowCount, 4);
  assert.equal(trainingDatasets.datasets.wgsl.materializedRowCount, 8);
  assert.deepEqual(trainingDatasets.datasets.mixed.laneCounts, { javascript: 4, wgsl: 4 });
  assert.equal(trainingDatasets.datasets.mixed.materializedRowCount, 16);
}

const teacherRunRoot = 'reports/training/teacher-qualification/doppler-js-wgsl-2026-07-11-v4';
test('retained teacher labels reproduce the historical training dataset', {
  skip: existsSync(join(teacherRunRoot, 'run-contract.json'))
    ? false : `Local evidence unavailable: ${teacherRunRoot}`,
}, async () => {
  assertTrainingDatasets(await buildStudentTrainingDatasets({ contracts, teacherRunRoot }));
});

test('synthetic teacher receipts enforce admission, balancing and provenance', async () => {
  const fixtureRoot = await mkdtemp(join(tmpdir(), 'doppler-student-label-fixture-'));
  const fixtureContract = {
    taskBankHash: contracts.host.taskBankArtifact.hash,
    policyHash: contracts.host.policyArtifact.hash,
  };
  const counts = { javascript: 0, wgsl: 0 };
  const receipts = contracts.host.taskBank.tasks.filter((entry) => entry.split === 'label')
    .map((entry) => ({
      passed: ++counts[entry.lane] <= (entry.lane === 'javascript' ? 6 : 4),
      task: { id: entry.id, lane: entry.lane, split: entry.split },
      sessionId: `synthetic-${entry.id}`,
      teacherModelId: 'synthetic-test-only',
      provider: 'synthetic-test-only',
      ...fixtureContract,
      policyViolationCount: 0,
      checks: { exactSourceRecovery: true, validationCommandsPassed: true, changedPathsAllowed: true },
    }));
  try {
    const contractPath = join(fixtureRoot, 'run-contract.json');
    await writeFile(contractPath, JSON.stringify(fixtureContract));
    await writeFile(join(fixtureRoot, 'receipts.json'), JSON.stringify(receipts));
    assertTrainingDatasets(await buildStudentTrainingDatasets({ contracts, teacherRunRoot: fixtureRoot }));
    await writeFile(contractPath, JSON.stringify({ ...fixtureContract, taskBankHash: 'wrong' }));
    await assert.rejects(buildStudentTrainingDatasets({ contracts, teacherRunRoot: fixtureRoot }), /task bank hash/);
    await writeFile(contractPath, JSON.stringify({ ...fixtureContract, policyHash: 'wrong' }));
    await assert.rejects(buildStudentTrainingDatasets({ contracts, teacherRunRoot: fixtureRoot }), /policy hash/);
    await writeFile(contractPath, JSON.stringify(fixtureContract));
    await writeFile(join(fixtureRoot, 'receipts.json'), JSON.stringify(
      receipts.map((receipt) => ({ ...receipt, policyViolationCount: 1 }))
    ));
    await assert.rejects(buildStudentTrainingDatasets({ contracts, teacherRunRoot: fixtureRoot }), /accepted label in every lane/);
  } finally {
    await rm(fixtureRoot, { recursive: true, force: true });
  }
});

const task = selectStudentHoldoutTasks(contracts, ['javascript'])[0];
const prompt = await renderStudentTaskPrompt(contracts, task);
for (const mutation of task.mutations) {
  assert.equal(prompt.includes(mutation.replace), true);
  assert.equal(prompt.includes(mutation.find), false);
}

const gold = buildGoldStudentCandidate(task);
const parsedGold = parseStudentCandidateOutput(JSON.stringify(gold));
assert.equal(parsedGold.schemaValid, true);
assert.deepEqual(parsedGold.candidate, gold);
assert.deepEqual(parsedGold.violations, []);

const wrapped = parseStudentCandidateOutput(`\`\`\`json\n${JSON.stringify(gold)}\n\`\`\``);
assert.equal(wrapped.schemaValid, true);
assert.deepEqual(wrapped.violations.map((violation) => violation.code), ['output_wrapper']);

const constructive = await evaluateStudentCandidate({
  contracts,
  task,
  rawOutput: JSON.stringify(gold),
  variant: 'baseline',
  repetition: 1,
  prompt,
});
assert.equal(constructive.passed, true);
assert.equal(constructive.checks.patchApplicable, true);
assert.equal(constructive.checks.exactSourceRecovery, true);
assert.equal(constructive.checks.validationPassed, true);
assert.equal(constructive.policyViolationCount, 0);

function syntheticRow(variant, lane, repetition, passed) {
  return {
    variant,
    repetition,
    task: { id: `${lane}-holdout`, lane, split: 'student_holdout' },
    outputHash: `${variant}-${lane}-stable`,
    passed,
    checks: {
      patchApplicable: passed,
      exactSourceRecovery: passed,
      validationPassed: passed,
    },
    policyViolationCount: passed ? 0 : 1,
    policyViolations: passed ? [] : [{ code: 'invalid_json', detail: 'observed' }],
    applyErrors: [],
    performance: {
      generationDurationMs: 10,
      completionTokens: 2,
    },
  };
}

const rows = [];
for (let repetition = 1; repetition <= 3; repetition += 1) {
  rows.push(syntheticRow('baseline', 'javascript', repetition, false));
  rows.push(syntheticRow('baseline', 'wgsl', repetition, false));
  rows.push(syntheticRow('javascript', 'javascript', repetition, true));
  rows.push(syntheticRow('wgsl', 'wgsl', repetition, true));
}
const summaries = {
  baseline: buildStudentReplaySummary('baseline', rows),
  javascript: buildStudentReplaySummary('javascript', rows),
  wgsl: buildStudentReplaySummary('wgsl', rows),
};
const promotion = buildStudentPromotionReport(contracts.policy, summaries);
assert.equal(promotion.controlProven, true);
assert.equal(promotion.candidates.specialized.eligible, true);
assert.equal(promotion.candidates.mixed.eligible, false);
assert.equal(
  promotion.challengers.every((challenger) => challenger.status === 'eligible_for_external_trainer'),
  true
);

const failureSignals = buildOuroborosFailureSignals(rows, contracts.policy.policyId);
assert.equal(failureSignals.length, 2);
for (const signal of failureSignals) {
  assert.equal('taskId' in signal, false);
  assert.equal('path' in signal, false);
  assert.equal('prompt' in signal, false);
  assert.equal('output' in signal, false);
  assert.equal('completion' in signal, false);
}

console.log('student-code-experiment.test: ok');
