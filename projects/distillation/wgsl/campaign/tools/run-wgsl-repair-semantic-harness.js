#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import {
  evaluateWgslSemanticTaskEvidence,
  hashWgslSemanticEvidenceValue,
} from '../src/tooling/wgsl-repair-semantic-gate.js';
import { createWgslBrowserVerifier } from './lib/wgsl-browser-verifier.js';
import {
  runWgslSemanticTaskManifest,
  summarizeWgslSemanticTaskEvidence,
} from './lib/wgsl-semantic-harness.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-repair-v13-semantic-policy.json';
const DEFAULT_TASK_MANIFEST = 'tools/data/wgsl-repair-v13-semantic-task-qualification.json';
const DEFAULT_HISTORICAL_MANIFEST = 'tools/data/wgsl-repair-v13-historical-regressions.json';

function parseArgs(argv) {
  const args = {
    policyPath: DEFAULT_POLICY,
    taskManifestPath: DEFAULT_TASK_MANIFEST,
    historicalManifestPath: DEFAULT_HISTORICAL_MANIFEST,
    mode: 'reference',
    completionsPath: '',
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--task-manifest') args.taskManifestPath = argv[++index] || '';
    else if (token === '--historical-regressions') {
      args.historicalManifestPath = argv[++index] || '';
    } else if (token === '--mode') args.mode = argv[++index] || '';
    else if (token === '--completions') args.completionsPath = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!['reference', 'candidate'].includes(args.mode)) {
    throw new Error('--mode must be reference or candidate.');
  }
  if (args.mode === 'candidate' && !args.completionsPath) {
    throw new Error('--completions is required in candidate mode.');
  }
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(path.resolve(filePath), 'utf8'));
}

async function sha256File(filePath) {
  const bytes = await fs.readFile(path.resolve(filePath));
  return createHash('sha256').update(bytes).digest('hex');
}

async function requireFileHash(filePath, expectedSha256, label) {
  const actual = await sha256File(filePath);
  if (actual !== expectedSha256) {
    throw new Error(`${label} SHA-256 mismatch: expected ${expectedSha256}, got ${actual}.`);
  }
  return actual;
}

async function verifyHistoricalManifest(manifest) {
  if (manifest?.schema !== 'doppler.wgsl-repair-semantic-historical-regressions/v1'
    || !Array.isArray(manifest.cases)
    || manifest.cases.length === 0) {
    throw new Error('Historical regression manifest is invalid.');
  }
  for (const entry of manifest.cases) {
    await requireFileHash(
      entry.originStatusPath,
      entry.originStatusSha256,
      `${entry.id} origin status`
    );
    await requireFileHash(
      entry.regressionTestPath,
      entry.regressionTestSha256,
      `${entry.id} regression test`
    );
  }
}

async function loadTaskSources(manifest) {
  const sources = {};
  for (const task of manifest.tasks || []) {
    await requireFileHash(task.sourcePath, task.sourceSha256, `${task.taskId} source`);
    sources[task.taskId] = (await fs.readFile(path.resolve(task.sourcePath), 'utf8')).trim();
  }
  return sources;
}

export async function runWgslRepairSemanticHarness(args) {
  const [policy, manifest, historicalManifest] = await Promise.all([
    readJson(args.policyPath),
    readJson(args.taskManifestPath),
    readJson(args.historicalManifestPath),
  ]);
  await verifyHistoricalManifest(historicalManifest);
  const sources = await loadTaskSources(manifest);
  const completionDocument = args.mode === 'candidate'
    ? await readJson(args.completionsPath)
    : null;
  if (args.mode === 'candidate') {
    const taskManifestSha256 = await sha256File(args.taskManifestPath);
    if (completionDocument?.schema !== 'doppler.wgsl-repair-seed-candidate-completions/v1'
      || completionDocument?.population?.path !== args.taskManifestPath
      || completionDocument?.population?.sha256 !== taskManifestSha256) {
      throw new Error('Candidate completions do not bind the requested task manifest.');
    }
  }
  const verifier = await createWgslBrowserVerifier({
    requiredFeatures: [],
    progressEvery: 3,
  });
  try {
    const tasks = await runWgslSemanticTaskManifest({
      manifest,
      sources,
      mode: args.mode,
      completions: completionDocument?.completions,
      verifier,
    });
    const evaluatedTasks = tasks.map((task) => evaluateWgslSemanticTaskEvidence(policy, task));
    const allTasksPass = evaluatedTasks.every((task) => task.pass);
    const core = {
      schema: 'doppler.wgsl-repair-semantic-dispatch-receipt/v1',
      experimentId: 'doppler-wgsl-repair-v13',
      evaluationRole: manifest.role,
      mode: args.mode,
      candidate: args.mode === 'reference'
        ? { kind: 'reference_control', selectionAuthority: false }
        : completionDocument.candidate,
      candidateCompletions: args.mode === 'candidate'
        ? {
          path: args.completionsPath,
          sha256: await sha256File(args.completionsPath),
          receiptHash: completionDocument.receiptHash,
        }
        : null,
      policy: {
        path: args.policyPath,
        sha256: await sha256File(args.policyPath),
      },
      taskManifest: {
        path: args.taskManifestPath,
        sha256: await sha256File(args.taskManifestPath),
        cpuOracleRevision: manifest.cpuOracleRevision,
      },
      historicalRegressions: {
        path: args.historicalManifestPath,
        sha256: await sha256File(args.historicalManifestPath),
        caseIds: historicalManifest.cases.map((entry) => entry.id),
      },
      runtime: {
        backend: 'chromium_webgpu',
        deviceInfo: verifier.deviceInfo,
        browserArgs: verifier.browserArgs,
        runtimeSha256: hashWgslSemanticEvidenceValue({
          deviceInfo: verifier.deviceInfo,
          browserArgs: verifier.browserArgs,
        }),
      },
      tasks,
      evaluatedTasks,
      summary: summarizeWgslSemanticTaskEvidence(tasks),
      decision: allTasksPass
        ? args.mode === 'reference'
          ? 'reference_mechanics_passed'
          : 'candidate_tasks_passed'
        : args.mode === 'reference'
          ? 'reference_mechanics_failed'
          : 'candidate_tasks_failed',
      selectionAuthority: false,
      promotionAuthority: false,
      claimBoundary: args.mode === 'reference'
        ? manifest.claimBoundary
        : 'Candidate evidence is limited to the declared frozen population role. It has no seed-confirmation, promotion, semantic-claim, or productization authority.',
    };
    return { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
  } finally {
    await verifier.close();
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const receipt = await runWgslRepairSemanticHarness(args);
  process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
  if (!receipt.decision.endsWith('_passed')) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
