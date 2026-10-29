import { mkdir, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';

import { sha256Hex } from '../../src/utils/sha256.js';
import { evaluateHostTeacherSession } from './host-teacher-evaluator.js';
import { runHostTeacherProvider } from './host-teacher-provider.js';
import { createHostTeacherWorkspace } from './host-teacher-workspace.js';

async function writeJson(path, value) {
  await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

export async function runHostTeacherSession(options) {
  const {
    contracts,
    providerId,
    modelId,
    providerVersion,
    task,
    runRoot,
    keepWorkspace = false,
  } = options;
  const provider = contracts.policy.providers[providerId];
  if (!provider) {
    throw new Error(`Unknown host teacher provider "${providerId}".`);
  }
  if (!modelId) {
    throw new Error(`Host teacher provider ${providerId} requires an explicit model id.`);
  }
  const sessionId = `${providerId}--${task.id}`;
  const sessionRoot = resolve(runRoot, 'sessions', sessionId);
  await mkdir(sessionRoot, { recursive: true });
  const outputPath = join(sessionRoot, 'final-output.json');
  const workspaceState = await createHostTeacherWorkspace(contracts, task);
  let receipt;
  try {
    const providerRun = await runHostTeacherProvider({
      providerId,
      provider,
      modelId,
      workspace: workspaceState.workspace,
      outputPath,
      schemaPath: contracts.outputSchemaArtifact.absolutePath,
      schemaJson: contracts.outputSchemaArtifact.raw,
      task,
    });
    const evaluation = await evaluateHostTeacherSession({
      policy: contracts.policy,
      task,
      workspaceState,
      providerRun,
    });
    receipt = {
      schemaVersion: 1,
      source: 'doppler',
      receiptKind: 'host_teacher_machine_qualification',
      sessionId,
      policyId: contracts.policy.policyId,
      policyHash: contracts.policyArtifact.hash,
      receiptSchemaHash: contracts.receiptSchemaArtifact.hash,
      harnessHash: contracts.harnessHash,
      harnessFiles: contracts.harnessFiles,
      harnessRuntime: {
        nodeVersion: process.version,
        platform: process.platform,
        architecture: process.arch,
      },
      taskBankId: contracts.taskBank.bankId,
      taskBankHash: contracts.taskBankArtifact.hash,
      baseRevision: contracts.taskBank.baseRevision,
      mutatedBaselineRevision: workspaceState.baselineRevision,
      provider: providerId,
      providerVersion,
      teacherModelId: modelId,
      task: {
        id: task.id,
        lane: task.lane,
        split: task.split,
        sourceFiles: task.sourceFiles,
        allowedChangedPaths: task.allowedChangedPaths,
      },
      promptHash: sha256Hex(providerRun.prompt),
      providerProcess: {
        command: provider.command,
        argsHash: sha256Hex(JSON.stringify(providerRun.args)),
        code: providerRun.process.code,
        signal: providerRun.process.signal,
        stdoutHash: sha256Hex(providerRun.process.stdout),
        stderrHash: sha256Hex(providerRun.process.stderr),
      },
      eventCount: providerRun.events.length,
      eventParseErrors: providerRun.eventParseErrors,
      auditedCommands: providerRun.commands,
      passed: evaluation.passed,
      checks: evaluation.checks,
      policyViolationCount: evaluation.policyViolationCount,
      actualChangedPaths: evaluation.actualChangedPaths,
      unauthorizedPaths: evaluation.unauthorizedPaths,
      forbiddenChangedPaths: evaluation.forbiddenChangedPaths,
      forbiddenCommands: evaluation.forbiddenCommands,
      exactRecovery: evaluation.exactRecovery,
      validationCommands: evaluation.validationCommands.map((validation) => ({
        id: validation.id,
        command: validation.command,
        args: validation.args,
        code: validation.code,
        signal: validation.signal,
        stdoutHash: validation.stdoutHash,
        stderrHash: validation.stderrHash,
        passed: validation.passed,
      })),
      finalOutput: evaluation.finalOutput,
      finalOutputError: evaluation.finalOutputError,
      patchHash: evaluation.patchHash,
      patchBytes: Buffer.byteLength(evaluation.patch),
      workspacePath: keepWorkspace ? workspaceState.workspace : null,
    };
    await Promise.all([
      writeFile(join(sessionRoot, 'prompt.txt'), `${providerRun.prompt}\n`, 'utf8'),
      writeFile(join(sessionRoot, 'events.jsonl'), providerRun.process.stdout, 'utf8'),
      writeFile(join(sessionRoot, 'stderr.txt'), providerRun.process.stderr, 'utf8'),
      writeFile(join(sessionRoot, 'repair.patch'), evaluation.patch, 'utf8'),
      writeJson(join(sessionRoot, 'receipt.json'), receipt),
      writeJson(join(sessionRoot, 'validation-output.json'), evaluation.validationCommands),
    ]);
  } finally {
    if (!keepWorkspace) await workspaceState.cleanup();
  }
  return {
    receipt,
    sessionRoot,
  };
}
