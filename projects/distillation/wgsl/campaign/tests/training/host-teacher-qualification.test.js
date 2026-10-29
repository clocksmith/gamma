import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';

import { evaluateHostTeacherSession } from '../../tools/lib/host-teacher-evaluator.js';
import { loadHostTeacherContracts } from '../../tools/lib/host-teacher-contracts.js';
import { createHostTeacherWorkspace } from '../../tools/lib/host-teacher-workspace.js';
import { buildHostTeacherContractReport } from '../../tools/verify-host-teacher-contracts.js';

const report = await buildHostTeacherContractReport();
assert.equal(report.ok, true, report.errors.join('\n'));
assert.equal(report.tasks, 22);

const contracts = await loadHostTeacherContracts();
const task = contracts.taskBank.tasks.find(
  (candidate) => candidate.id === 'js-qualification-agent-eval-record-gate'
);
assert.ok(task);
const workspaceState = await createHostTeacherWorkspace(contracts, task);
try {
  const original = workspaceState.originals.get(task.allowedChangedPaths[0]);
  await writeFile(
    `${workspaceState.workspace}/${task.allowedChangedPaths[0]}`,
    original.content,
    'utf8'
  );
  const evaluation = await evaluateHostTeacherSession({
    policy: contracts.policy,
    task,
    workspaceState,
    providerRun: {
      process: { code: 0, signal: null },
      eventParseErrors: [],
      commands: [],
      finalOutput: {
        taskId: task.id,
        summary: 'Restored the fail-closed object-record check.',
        changedFiles: task.allowedChangedPaths,
        verification: ['text-pair-tests passed'],
        residualRisks: [],
      },
    },
  });
  assert.equal(evaluation.passed, true);
  assert.equal(evaluation.checks.exactSourceRecovery, true);
  assert.equal(evaluation.checks.validationCommandsPassed, true);
  assert.deepEqual(evaluation.actualChangedPaths, task.allowedChangedPaths);
} finally {
  await workspaceState.cleanup();
}

console.log('host-teacher-qualification.test: ok');
