#!/usr/bin/env node

import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

function parseArgs(argv) {
  const args = { dataset: '', teacher: '', out: '', receipt: '' };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--dataset') args.dataset = argv[++index] || '';
    else if (token === '--teacher') args.teacher = argv[++index] || '';
    else if (token === '--out') args.out = argv[++index] || '';
    else if (token === '--receipt') args.receipt = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  for (const [key, value] of Object.entries(args)) {
    if (!value) throw new Error(`--${key} is required`);
  }
  return args;
}

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

async function sha256File(filePath) {
  return sha256(await fs.readFile(filePath));
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

async function readJsonl(filePath) {
  return (await fs.readFile(filePath, 'utf8')).split('\n')
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line));
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.keys(value).sort().map((key) => [key, canonicalize(value[key])])
    );
  }
  return value;
}

function canonicalPackage(value) {
  try {
    return JSON.stringify(canonicalize(JSON.parse(value)));
  } catch {
    return null;
  }
}

export async function materializeSequenceKd(options) {
  const datasetPath = path.resolve(options.dataset);
  const teacherPath = path.resolve(options.teacher);
  const outputPath = path.resolve(options.out);
  const receiptPath = path.resolve(options.receipt);
  const rows = await readJsonl(datasetPath);
  const teacher = await readJson(teacherPath);
  const candidate = teacher.candidates?.[0];
  if (!candidate || !Array.isArray(candidate.tasks)) {
    throw new Error('Teacher reference contains no candidate tasks.');
  }
  const teacherTasks = new Map(candidate.tasks.map((task) => [task.taskId, task]));
  const admitted = [];
  const rejected = [];
  for (const row of rows) {
    const taskId = row.taskId || row.rowId || row.id;
    const task = teacherTasks.get(taskId);
    const teacherCanonical = task ? canonicalPackage(task.completion) : null;
    const oracleCanonical = canonicalPackage(row.completion);
    const pass = teacherCanonical !== null
      && oracleCanonical !== null
      && teacherCanonical === oracleCanonical;
    if (!pass) {
      rejected.push({
        taskId,
        reason: task ? 'teacher_package_differs_from_reference_oracle' : 'teacher_task_missing',
      });
      continue;
    }
    admitted.push({
      schema: 'doppler.wgsl-writer-sequence-kd-row/v1',
      rowId: taskId,
      taskId,
      prompt: row.prompt,
      promptSha256: sha256(row.prompt),
      completion: task.completion,
      completionSha256: sha256(task.completion),
      teacherModelId: teacher.model?.modelId || null,
      teacherModelRevision: teacher.model?.revision || null,
      teacherAdapterTreeSha256: candidate.adapterTreeSha256,
      oracle: 'canonical_reference_package_equality_v1',
    });
  }
  if (admitted.length === 0) {
    throw new Error('Teacher produced zero canonical reference-equal packages; sequence KD is not admitted.');
  }
  const output = `${admitted.map((row) => JSON.stringify(row)).join('\n')}\n`;
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, output, 'utf8');
  const receipt = {
    schema: 'doppler.wgsl-writer-sequence-kd-materialization/v1',
    datasetPath,
    datasetSha256: await sha256File(datasetPath),
    teacherPath,
    teacherSha256: await sha256File(teacherPath),
    outputPath,
    outputSha256: sha256(output),
    sourceRows: rows.length,
    admittedRows: admitted.length,
    rejectedRows: rejected.length,
    oracle: 'canonical_reference_package_equality_v1',
    rejected,
    claimBoundary: 'Canonical teacher/reference package equality admits sequence-training rows; student Chromium execution remains required.',
  };
  await fs.mkdir(path.dirname(receiptPath), { recursive: true });
  await fs.writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return receipt;
}

export async function main(argv = process.argv.slice(2)) {
  const receipt = await materializeSequenceKd(parseArgs(argv));
  console.log(JSON.stringify(receipt, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}
