#!/usr/bin/env node

import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import process from 'node:process';
import { pathToFileURL } from 'node:url';

import {
  HOST_TEACHER_LANES,
  loadHostTeacherContracts,
  selectHostTeacherTasks,
} from './lib/host-teacher-contracts.js';
import { requireHostCommandVersion } from './lib/host-teacher-process.js';
import {
  buildHostTeacherScoreboard,
  exportQualifiedLabelTraces,
  renderHostTeacherScoreboard,
} from './lib/host-teacher-scoreboard.js';
import { runHostTeacherSession } from './lib/host-teacher-session.js';

function parseTeacher(value) {
  const separator = value.indexOf('=');
  if (separator <= 0 || separator === value.length - 1) {
    throw new Error('--teacher requires provider=model-id.');
  }
  return {
    providerId: value.slice(0, separator),
    modelId: value.slice(separator + 1),
  };
}

function parseArgs(argv) {
  const options = {
    teachers: [],
    lanes: [],
    taskIds: [],
    withLabels: false,
    keepWorkspaces: false,
    json: false,
    runRoot: null,
    policyPath: null,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--teacher') {
      options.teachers.push(parseTeacher(String(argv[index + 1] || '')));
      index += 1;
      continue;
    }
    if (arg.startsWith('--teacher=')) {
      options.teachers.push(parseTeacher(arg.slice('--teacher='.length)));
      continue;
    }
    if (arg === '--lane') {
      options.lanes.push(String(argv[index + 1] || ''));
      index += 1;
      continue;
    }
    if (arg.startsWith('--lane=')) {
      options.lanes.push(arg.slice('--lane='.length));
      continue;
    }
    if (arg === '--task') {
      options.taskIds.push(String(argv[index + 1] || ''));
      index += 1;
      continue;
    }
    if (arg === '--run-root') {
      options.runRoot = String(argv[index + 1] || '');
      index += 1;
      continue;
    }
    if (arg === '--policy') {
      options.policyPath = String(argv[index + 1] || '');
      index += 1;
      continue;
    }
    if (arg === '--with-labels') {
      options.withLabels = true;
      continue;
    }
    if (arg === '--keep-workspaces') {
      options.keepWorkspaces = true;
      continue;
    }
    if (arg === '--json') {
      options.json = true;
      continue;
    }
    throw new Error(`Unknown argument: ${arg}`);
  }
  return options;
}

function resolveTeachers(options, contracts) {
  const teachers = [...options.teachers];
  if (teachers.length === 0) {
    for (const [providerId, provider] of Object.entries(contracts.policy.providers)) {
      const modelId = String(process.env[provider.modelEnvironmentVariable] || '').trim();
      if (modelId) teachers.push({ providerId, modelId });
    }
  }
  if (teachers.length === 0) {
    throw new Error(
      'No teachers configured. Pass --teacher claude=<model-id> and/or --teacher codex=<model-id>.'
    );
  }
  const seen = new Set();
  for (const teacher of teachers) {
    if (!contracts.policy.providers[teacher.providerId]) {
      throw new Error(`Unknown host teacher provider "${teacher.providerId}".`);
    }
    if (seen.has(teacher.providerId)) {
      throw new Error(`Configure host teacher provider ${teacher.providerId} only once.`);
    }
    seen.add(teacher.providerId);
  }
  return teachers;
}

function defaultRunRoot(root) {
  const timestamp = new Date().toISOString().replaceAll(':', '-');
  return resolve(root, 'reports', 'training', 'teacher-qualification', timestamp);
}

async function writeJson(path, value) {
  await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

async function runSessions(options) {
  const contracts = await loadHostTeacherContracts({
    policyPath: options.policyPath || undefined,
  });
  const teachers = resolveTeachers(options, contracts);
  const lanes = options.lanes.length > 0 ? options.lanes : HOST_TEACHER_LANES;
  const runRoot = options.runRoot ? resolve(options.runRoot) : defaultRunRoot(contracts.root);
  await mkdir(runRoot, { recursive: true });

  const providerVersions = {};
  for (const teacher of teachers) {
    const provider = contracts.policy.providers[teacher.providerId];
    // Version probes are deliberately completed before any task mutation.
    // eslint-disable-next-line no-await-in-loop
    providerVersions[teacher.providerId] = await requireHostCommandVersion(
      provider.command,
      provider.versionArgs
    );
  }
  const runContract = {
    schemaVersion: 1,
    source: 'doppler',
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
    lanes,
    qualificationTaskIds: options.taskIds,
    withLabels: options.withLabels,
    teachers: teachers.map((teacher) => ({
      ...teacher,
      providerVersion: providerVersions[teacher.providerId],
    })),
  };
  await writeJson(resolve(runRoot, 'run-contract.json'), runContract);

  const receipts = [];
  const qualificationTasks = selectHostTeacherTasks(contracts.taskBank, {
    lanes,
    splits: ['qualification'],
    taskIds: options.taskIds.length > 0 ? options.taskIds : undefined,
  });
  for (const teacher of teachers) {
    for (const task of qualificationTasks) {
      console.error(`[host-teacher] provider=${teacher.providerId} lane=${task.lane} task=${task.id}`);
      // Host sessions are isolated and intentionally serialized for reproducible receipts.
      // eslint-disable-next-line no-await-in-loop
      const session = await runHostTeacherSession({
        contracts,
        providerId: teacher.providerId,
        modelId: teacher.modelId,
        providerVersion: providerVersions[teacher.providerId],
        task,
        runRoot,
        keepWorkspace: options.keepWorkspaces,
      });
      receipts.push(session.receipt);
    }
  }

  const providerIds = teachers.map((teacher) => teacher.providerId);
  const scoreboard = buildHostTeacherScoreboard(
    receipts,
    contracts.policy,
    providerIds,
    lanes
  );
  if (options.withLabels) {
    for (const lane of lanes) {
      const selected = scoreboard.selectedByLane[lane];
      if (!selected) {
        throw new Error(`${lane}: no teacher crossed the machine qualification threshold.`);
      }
      const labelTasks = selectHostTeacherTasks(contracts.taskBank, {
        lanes: [lane],
        splits: ['label'],
      });
      for (const task of labelTasks) {
        console.error(`[host-label] provider=${selected.provider} lane=${lane} task=${task.id}`);
        // eslint-disable-next-line no-await-in-loop
        const session = await runHostTeacherSession({
          contracts,
          providerId: selected.provider,
          modelId: selected.teacherModelId,
          providerVersion: providerVersions[selected.provider],
          task,
          runRoot,
          keepWorkspace: options.keepWorkspaces,
        });
        receipts.push(session.receipt);
      }
    }
  }

  const exportReport = await exportQualifiedLabelTraces({
    receipts,
    runRoot,
    root: contracts.root,
    policy: contracts.policy,
    taskBank: contracts.taskBank,
  });
  const report = {
    ...scoreboard,
    runRoot,
    receiptCount: receipts.length,
    labelExport: exportReport,
  };
  await Promise.all([
    writeJson(resolve(runRoot, 'scoreboard.json'), report),
    writeFile(resolve(runRoot, 'scoreboard.md'), renderHostTeacherScoreboard(scoreboard), 'utf8'),
    writeJson(resolve(runRoot, 'receipts.json'), receipts),
  ]);
  return report;
}

export async function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  const report = await runSessions(options);
  if (options.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log(renderHostTeacherScoreboard(report));
    console.log(`Receipts: ${report.runRoot}`);
  }
  if (Object.values(report.selectedByLane).some((selection) => selection === null)) {
    process.exitCode = 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}
