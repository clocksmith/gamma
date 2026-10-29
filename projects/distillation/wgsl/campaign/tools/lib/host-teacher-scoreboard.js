import { readFile, writeFile } from 'node:fs/promises';
import { join, relative } from 'node:path';

import { serializeTeacherTraceTextPairs } from '../../src/experimental/training/datasets/teacher-traces.js';
import { HOST_TEACHER_LANES } from './host-teacher-contracts.js';

function scoreQualificationReceipts(receipts, providerId, lane, policy) {
  const rows = receipts.filter((receipt) => (
    receipt.provider === providerId
    && receipt.task.lane === lane
    && receipt.task.split === 'qualification'
  ));
  const passedTasks = rows.filter((receipt) => receipt.passed).length;
  const policyViolationCount = rows.reduce(
    (total, receipt) => total + receipt.policyViolationCount,
    0
  );
  const passRate = rows.length > 0 ? passedTasks / rows.length : 0;
  return {
    provider: providerId,
    teacherModelId: rows[0]?.teacherModelId || null,
    lane,
    attemptedTasks: rows.length,
    passedTasks,
    passRate,
    policyViolationCount,
    qualified: rows.length > 0
      && passRate >= policy.evaluation.minPassRateByLane[lane]
      && policyViolationCount <= policy.evaluation.maxPolicyViolations,
  };
}

export function buildHostTeacherScoreboard(
  receipts,
  policy,
  providerIds,
  lanes = HOST_TEACHER_LANES
) {
  const scores = [];
  for (const providerId of providerIds) {
    for (const lane of lanes) {
      scores.push(scoreQualificationReceipts(receipts, providerId, lane, policy));
    }
  }
  const selectedByLane = {};
  for (const lane of lanes) {
    const candidates = scores
      .filter((score) => score.lane === lane && score.qualified)
      .sort((left, right) => (
        right.passRate - left.passRate
        || left.policyViolationCount - right.policyViolationCount
        || policy.evaluation.providerTieBreakOrder.indexOf(left.provider)
          - policy.evaluation.providerTieBreakOrder.indexOf(right.provider)
        || left.teacherModelId.localeCompare(right.teacherModelId)
      ));
    selectedByLane[lane] = candidates[0]
      ? {
        provider: candidates[0].provider,
        teacherModelId: candidates[0].teacherModelId,
        passRate: candidates[0].passRate,
        policyViolationCount: candidates[0].policyViolationCount,
      }
      : null;
  }
  return {
    schemaVersion: 1,
    source: 'doppler',
    policyId: policy.policyId,
    scores,
    selectedByLane,
  };
}

export function renderHostTeacherScoreboard(scoreboard) {
  const lines = [
    '# Doppler host teacher qualification',
    '',
    '| Provider | Model | Lane | Passed | Rate | Violations | Qualified |',
    '| --- | --- | --- | ---: | ---: | ---: | --- |',
  ];
  for (const score of scoreboard.scores) {
    lines.push(
      `| ${score.provider} | ${score.teacherModelId || 'n/a'} | ${score.lane} | `
      + `${score.passedTasks}/${score.attemptedTasks} | ${score.passRate.toFixed(3)} | `
      + `${score.policyViolationCount} | ${score.qualified ? 'yes' : 'no'} |`
    );
  }
  lines.push('', '## Selected teachers', '');
  for (const lane of Object.keys(scoreboard.selectedByLane)) {
    const selected = scoreboard.selectedByLane[lane];
    lines.push(selected
      ? `- ${lane}: ${selected.provider} / ${selected.teacherModelId}`
      : `- ${lane}: no machine-qualified teacher`);
  }
  return `${lines.join('\n')}\n`;
}

export async function exportQualifiedLabelTraces(options) {
  const {
    receipts,
    runRoot,
    root,
    policy,
    taskBank,
  } = options;
  const rows = [];
  for (const receipt of receipts) {
    if (!receipt.passed || receipt.task.split !== 'label') continue;
    const sessionRoot = join(runRoot, 'sessions', receipt.sessionId);
    // Session artifacts are immutable inputs to the exported lineage row.
    // eslint-disable-next-line no-await-in-loop
    const [prompt, completion] = await Promise.all([
      readFile(join(sessionRoot, 'prompt.txt'), 'utf8'),
      readFile(join(sessionRoot, 'repair.patch'), 'utf8'),
    ]);
    rows.push({
      id: `qualified-${receipt.sessionId}`,
      prompt: prompt.trim(),
      completion,
      teacherModelId: receipt.teacherModelId,
      studentBaseModelId: taskBank.studentBaseModelId,
      domain: receipt.task.lane === 'wgsl' ? 'doppler-wgsl' : 'doppler-javascript',
      taskKind: 'code_repair',
      policyId: policy.policyId,
      sourcePolicyId: policy.policyId,
      sourceFiles: receipt.task.sourceFiles,
      generationParams: {
        provider: receipt.provider,
        providerVersion: receipt.providerVersion,
      },
      provenance: {
        evidenceClass: 'constructive_machine_replay',
        qualificationReceipt: relative(root, join(sessionRoot, 'receipt.json')).replaceAll('\\', '/'),
        baseRevision: receipt.baseRevision,
        policyHash: receipt.policyHash,
        receiptSchemaHash: receipt.receiptSchemaHash,
        harnessHash: receipt.harnessHash,
        taskBankHash: receipt.taskBankHash,
        promptHash: receipt.promptHash,
        patchHash: receipt.patchHash,
      },
    });
  }
  const serialized = serializeTeacherTraceTextPairs(rows);
  const tracePath = join(runRoot, 'qualified-teacher-traces.jsonl');
  const textPairPath = join(runRoot, 'qualified-text-pairs.jsonl');
  await Promise.all([
    writeFile(tracePath, serialized, 'utf8'),
    writeFile(textPairPath, serialized, 'utf8'),
  ]);
  return {
    rows: rows.length,
    tracePath,
    textPairPath,
  };
}
