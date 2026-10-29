#!/usr/bin/env node

import process from 'node:process';
import { pathToFileURL } from 'node:url';

import {
  HOST_TEACHER_LANES,
  HOST_TEACHER_SPLITS,
  loadHostTeacherContracts,
} from './lib/host-teacher-contracts.js';
import { runHostProcess } from './lib/host-teacher-process.js';

const MINIMUM_TASKS_BY_SPLIT = Object.freeze({
  qualification: 3,
  label: 3,
  student_holdout: 2,
});
const REQUIRED_HARNESS_FILES = Object.freeze([
  'tools/lib/host-teacher-contracts.js',
  'tools/lib/host-teacher-evaluator.js',
  'tools/lib/host-teacher-process.js',
  'tools/lib/host-teacher-provider.js',
  'tools/lib/host-teacher-scoreboard.js',
  'tools/lib/host-teacher-session.js',
  'tools/lib/host-teacher-workspace.js',
  'tools/qualify-code-teachers.js',
]);

function countOccurrences(source, needle) {
  let count = 0;
  let offset = 0;
  while (offset <= source.length - needle.length) {
    const found = source.indexOf(needle, offset);
    if (found === -1) break;
    count += 1;
    offset = found + needle.length;
  }
  return count;
}

function pathHasPrefix(path, prefix) {
  return path === prefix || path.startsWith(`${prefix}/`);
}

async function readRevisionFile(root, revision, path) {
  return runHostProcess('git', ['show', `${revision}:${path}`], { cwd: root });
}

export async function buildHostTeacherContractReport(options = {}) {
  const contracts = await loadHostTeacherContracts(options);
  const errors = [];
  const revisionCheck = await runHostProcess(
    'git',
    ['cat-file', '-e', `${contracts.taskBank.baseRevision}^{commit}`],
    { cwd: contracts.root }
  );
  if (revisionCheck.code !== 0) {
    errors.push(`base revision does not resolve: ${contracts.taskBank.baseRevision}`);
  }
  const ancestorCheck = await runHostProcess(
    'git',
    ['merge-base', '--is-ancestor', contracts.taskBank.baseRevision, 'HEAD'],
    { cwd: contracts.root }
  );
  if (ancestorCheck.code !== 0) {
    errors.push(`base revision is not an ancestor of HEAD: ${contracts.taskBank.baseRevision}`);
  }

  if (!contracts.policy.snapshot.excludedPaths.some((prefix) => (
    pathHasPrefix(contracts.policy.taskBankPath, prefix)
  ))) {
    errors.push('task bank path must be excluded from teacher snapshots');
  }
  for (const pattern of contracts.policy.evaluation.forbiddenCommandPatterns) {
    try {
      new RegExp(pattern, 'i');
    } catch (error) {
      errors.push(`invalid forbidden command pattern ${JSON.stringify(pattern)}: ${error.message}`);
    }
  }
  for (const path of REQUIRED_HARNESS_FILES) {
    if (!contracts.policy.harnessFiles.includes(path)) {
      errors.push(`policy harnessFiles must include ${path}`);
    }
  }
  if (
    contracts.outputSchema?.type !== 'object'
    || contracts.outputSchema?.additionalProperties !== false
  ) {
    errors.push('host teacher output schema must be a closed object schema');
  }
  if (
    contracts.receiptSchema?.type !== 'object'
    || contracts.receiptSchema?.additionalProperties !== false
  ) {
    errors.push('host teacher receipt schema must be a closed object schema');
  }

  const revisionFiles = new Map();
  for (const task of contracts.taskBank.tasks) {
    for (const sourcePath of task.sourceFiles) {
      const cacheKey = `${contracts.taskBank.baseRevision}:${sourcePath}`;
      if (!revisionFiles.has(cacheKey)) {
        // Pinned source reads prove that task fixtures are not borrowing the working tree.
        // eslint-disable-next-line no-await-in-loop
        revisionFiles.set(
          cacheKey,
          await readRevisionFile(contracts.root, contracts.taskBank.baseRevision, sourcePath)
        );
      }
      if (revisionFiles.get(cacheKey).code !== 0) {
        errors.push(`${task.id}: source file is absent at the base revision: ${sourcePath}`);
      }
    }
    for (const mutation of task.mutations) {
      const cacheKey = `${contracts.taskBank.baseRevision}:${mutation.path}`;
      const source = revisionFiles.get(cacheKey);
      if (!source || source.code !== 0) continue;
      const occurrences = countOccurrences(source.stdout, mutation.find);
      if (occurrences !== mutation.occurrences) {
        errors.push(
          `${task.id}: ${mutation.path} expected ${mutation.occurrences} mutation occurrence(s), found ${occurrences}`
        );
      }
    }
  }

  for (const lane of HOST_TEACHER_LANES) {
    const pathOwners = new Map();
    for (const split of HOST_TEACHER_SPLITS) {
      const tasks = contracts.taskBank.tasks.filter((task) => (
        task.lane === lane && task.split === split
      ));
      if (tasks.length < MINIMUM_TASKS_BY_SPLIT[split]) {
        errors.push(
          `${lane}/${split} requires at least ${MINIMUM_TASKS_BY_SPLIT[split]} tasks, found ${tasks.length}`
        );
      }
      for (const task of tasks) {
        for (const path of task.allowedChangedPaths) {
          const previousSplit = pathOwners.get(path);
          if (previousSplit && previousSplit !== split) {
            errors.push(`${lane}: ${path} crosses ${previousSplit} and ${split} splits`);
          }
          pathOwners.set(path, split);
        }
      }
    }
  }

  return {
    ok: errors.length === 0,
    policyId: contracts.policy.policyId,
    policyHash: contracts.policyArtifact.hash,
    taskBankId: contracts.taskBank.bankId,
    taskBankHash: contracts.taskBankArtifact.hash,
    harnessHash: contracts.harnessHash,
    baseRevision: contracts.taskBank.baseRevision,
    tasks: contracts.taskBank.tasks.length,
    errors,
  };
}

export async function main(argv = process.argv.slice(2)) {
  const json = argv.includes('--json');
  const unsupported = argv.filter((arg) => arg !== '--json');
  if (unsupported.length > 0) {
    throw new Error(`Unknown argument: ${unsupported[0]}`);
  }
  const report = await buildHostTeacherContractReport();
  if (json) {
    console.log(JSON.stringify(report, null, 2));
  } else if (report.ok) {
    console.log(
      `host-teacher-contracts: ok (${report.tasks} tasks, base ${report.baseRevision})`
    );
  } else {
    for (const error of report.errors) console.error(`host-teacher-contracts: ${error}`);
  }
  if (!report.ok) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}
