import { readFile } from 'node:fs/promises';

import { sha256Hex } from '../../src/utils/sha256.js';
import { validateTeacherFinalOutput, resolveRepoPath } from './host-teacher-contracts.js';
import { runHostProcess } from './host-teacher-process.js';
import { readWorkspacePatch, readWorkspaceStatus } from './host-teacher-workspace.js';

function sameStringSet(left, right) {
  if (left.length !== right.length) return false;
  const rightSet = new Set(right);
  return left.every((value) => rightSet.has(value));
}

function pathHasPrefix(path, prefix) {
  return path === prefix || path.startsWith(`${prefix}/`);
}

async function runValidationCommands(workspace, commands) {
  const results = [];
  for (const validation of commands) {
    // Validation order is part of the task contract.
    // eslint-disable-next-line no-await-in-loop
    const processResult = await runHostProcess(validation.command, validation.args, { cwd: workspace });
    results.push({
      id: validation.id,
      command: validation.command,
      args: validation.args,
      code: processResult.code,
      signal: processResult.signal,
      stdoutHash: sha256Hex(processResult.stdout),
      stderrHash: sha256Hex(processResult.stderr),
      stdout: processResult.stdout,
      stderr: processResult.stderr,
      passed: processResult.code === 0 && !processResult.signal,
    });
  }
  return results;
}

async function evaluateExactRecovery(workspace, originals) {
  const checks = [];
  for (const [path, original] of originals) {
    try {
      // Source recovery is intentionally independent from the teacher's final response.
      // eslint-disable-next-line no-await-in-loop
      const content = await readFile(resolveRepoPath(workspace, path), 'utf8');
      const observedHash = sha256Hex(content);
      checks.push({
        path,
        expectedHash: original.hash,
        mutatedHash: original.mutatedHash,
        observedHash,
        passed: observedHash === original.hash,
      });
    } catch (error) {
      checks.push({
        path,
        expectedHash: original.hash,
        mutatedHash: original.mutatedHash,
        observedHash: null,
        passed: false,
        error: error.message,
      });
    }
  }
  return checks;
}

export async function evaluateHostTeacherSession(options) {
  const {
    policy,
    task,
    workspaceState,
    providerRun,
  } = options;
  const actualChangedPaths = await readWorkspaceStatus(workspaceState.workspace);
  const patch = await readWorkspacePatch(workspaceState.workspace);
  const exactRecovery = await evaluateExactRecovery(
    workspaceState.workspace,
    workspaceState.originals
  );
  const validationCommands = await runValidationCommands(
    workspaceState.workspace,
    task.validationCommands
  );

  let finalOutput = null;
  let finalOutputError = null;
  try {
    finalOutput = validateTeacherFinalOutput(providerRun.finalOutput, task);
  } catch (error) {
    finalOutputError = error.message;
  }

  const unauthorizedPaths = actualChangedPaths.filter(
    (path) => !task.allowedChangedPaths.includes(path)
  );
  const forbiddenChangedPaths = actualChangedPaths.filter((path) => (
    policy.evaluation.forbiddenChangedPathPrefixes.some((prefix) => pathHasPrefix(path, prefix))
  ));
  const forbiddenCommands = [];
  for (const command of providerRun.commands) {
    for (const pattern of policy.evaluation.forbiddenCommandPatterns) {
      if (new RegExp(pattern, 'i').test(command)) {
        forbiddenCommands.push({ command, pattern });
      }
    }
  }
  const declaredChangedFilesMatch = finalOutput
    ? sameStringSet(finalOutput.changedFiles, actualChangedPaths)
    : false;

  const checks = {
    providerExitedSuccessfully: providerRun.process.code === 0 && !providerRun.process.signal,
    eventStreamParsed: providerRun.eventParseErrors.length === 0,
    finalOutputValid: finalOutputError === null,
    declaredChangedFilesMatch,
    patchPresent: patch.trim().length > 0,
    changedPathsAllowed: unauthorizedPaths.length === 0,
    forbiddenChangedPathsAbsent: forbiddenChangedPaths.length === 0,
    forbiddenCommandsAbsent: forbiddenCommands.length === 0,
    exactSourceRecovery: exactRecovery.every((entry) => entry.passed),
    validationCommandsPassed: validationCommands.every((entry) => entry.passed),
  };
  const policyViolationCount = (
    unauthorizedPaths.length
    + forbiddenChangedPaths.length
    + forbiddenCommands.length
  );
  const requiredCheckValues = Object.entries(checks)
    .filter(([key]) => policy.evaluation.requireExactSourceRecovery || key !== 'exactSourceRecovery')
    .map(([, value]) => value);
  const passed = requiredCheckValues.every(Boolean)
    && policyViolationCount <= policy.evaluation.maxPolicyViolations;

  return {
    passed,
    checks,
    policyViolationCount,
    actualChangedPaths,
    unauthorizedPaths,
    forbiddenChangedPaths,
    forbiddenCommands,
    exactRecovery,
    validationCommands,
    finalOutput,
    finalOutputError,
    patch,
    patchHash: sha256Hex(patch),
  };
}
