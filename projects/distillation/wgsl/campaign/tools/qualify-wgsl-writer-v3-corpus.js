#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';
import { createWgslAuthorBrowserExecutor } from './lib/wgsl-author-browser-executor.js';
import { buildWgslAuthorExecutionPlan } from './lib/wgsl-author-execution-plan.js';
import { evaluateWgslWriterV3Oracle } from './lib/wgsl-writer-v3-oracles.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v3-corpus-policy.json';
const POLICY_IDS = new Set([
  'doppler-wgsl-writer-v3-corpus',
  'doppler-wgsl-writer-v3-corpus-diversity-repair',
  'doppler-wgsl-writer-v3-explicit-semantic-repair',
  'doppler-wgsl-writer-v3-explicit-output-budget',
]);

function parseArgs(argv) {
  const args = { policyPath: DEFAULT_POLICY, outputPath: '' };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--out') args.outputPath = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.policyPath) throw new Error('--policy requires a value.');
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(path.resolve(filePath), 'utf8'));
}

async function sha256File(filePath) {
  return createHash('sha256').update(await fs.readFile(path.resolve(filePath))).digest('hex');
}

async function requireFileHash(filePath, expectedSha256, label) {
  const actual = await sha256File(filePath);
  if (actual !== expectedSha256) {
    throw new Error(`${label} SHA-256 mismatch: expected ${expectedSha256}, got ${actual}.`);
  }
}

function requireInternalHash(value, field, label) {
  const core = { ...value };
  const expected = core[field];
  delete core[field];
  const actual = createHash('sha256').update(JSON.stringify(core)).digest('hex');
  if (actual !== expected) throw new Error(`${label} internal ${field} mismatch.`);
}

function summarizeReplay(runs, requiredRuns) {
  const outputHashes = runs.map((run) => run.outputSha256);
  const executedPasses = runs.map((run) => JSON.stringify(run.execution?.executedPassIds || []));
  return {
    requiredRuns,
    completedRuns: runs.length,
    outputHashes,
    outputsMatch: new Set(outputHashes).size === 1,
    executedPassesMatch: new Set(executedPasses).size === 1,
    pass: runs.length === requiredRuns
      && runs.every((run) => run.pass)
      && new Set(outputHashes).size === 1
      && new Set(executedPasses).size === 1,
  };
}

export function resolveQualificationOutputPath(policy, requestedOutputPath = '') {
  if (requestedOutputPath) return requestedOutputPath;
  if (typeof policy?.corpus?.outputRoot !== 'string' || !policy.corpus.outputRoot) {
    throw new Error('WGSL writer v3 qualification requires corpus.outputRoot.');
  }
  return path.join(policy.corpus.outputRoot, 'reference-qualification.json');
}

export async function qualifyWgslWriterV3Corpus(args) {
  const policy = await readJson(args.policyPath);
  if (!POLICY_IDS.has(policy.policyId)
    || policy.status !== 'frozen_before_materialization') {
    throw new Error('WGSL writer v3 qualification requires the frozen corpus policy.');
  }
  const corpusManifestPath = path.join(policy.corpus.outputRoot, 'corpus-manifest.json');
  const outputPath = resolveQualificationOutputPath(policy, args.outputPath);
  const corpusManifest = await readJson(corpusManifestPath);
  requireInternalHash(corpusManifest, 'manifestSha256', 'WGSL writer v3 corpus manifest');
  await Promise.all([
    requireFileHash(args.policyPath, corpusManifest.policy.sha256, 'corpus policy'),
    requireFileHash(
      policy.corpus.capabilityCatalog.path,
      policy.corpus.capabilityCatalog.sha256,
      'capability catalog'
    ),
    ...Object.entries(corpusManifest.fileBindings).map(([filePath, binding]) => (
      requireFileHash(filePath, binding.sha256, `corpus file ${filePath}`)
    )),
  ]);
  if (corpusManifest.isolation.semanticFamilyOverlaps.length !== 0
    || corpusManifest.isolation.duplicateRowIds !== 0
    || corpusManifest.isolation.duplicatePrompts !== 0
    || corpusManifest.quality.allReferencePackagesPass !== true) {
    throw new Error('WGSL writer v3 corpus isolation or quality admission failed.');
  }
  const taskManifestPath = corpusManifest.referenceQualification.taskManifestPath;
  const taskManifest = await readJson(taskManifestPath);
  const formatCatalog = await readJson('tools/data/wgsl-author-format-catalog.json');
  const executor = await createWgslAuthorBrowserExecutor({
    browserArgs: policy.runtime.browserArgs,
    headless: policy.runtime.headless,
    requiredBackend: policy.runtime.requiredBackend,
    requiredVendor: policy.runtime.requiredVendor,
    requiredFeatures: policy.runtime.requiredFeatures,
    requiredLimits: policy.runtime.requiredLimits,
    powerPreference: policy.runtime.powerPreference,
    executionTimeoutMs: policy.runtime.executionTimeoutMs,
  });
  const tasks = [];
  let sessionCleanup = null;
  try {
    for (const task of taskManifest.tasks) {
      const plan = buildWgslAuthorExecutionPlan(task.packageValue, {
        ...task.contract,
        formats: formatCatalog.formats,
        availableFeatures: policy.runtime.requiredFeatures,
        limits: policy.runtime.requiredLimits,
        allocationLimits: policy.runtime.allocationLimits,
      }, task.context);
      const runs = [];
      for (let runIndex = 0; runIndex < policy.referenceQualification.replayCount; runIndex += 1) {
        let execution = null;
        let executionError = null;
        try {
          execution = await executor.execute(plan, {
            id: `${task.taskId}-run-${runIndex + 1}`,
          });
        } catch (error) {
          executionError = error?.message || String(error);
        }
        let oracle;
        try {
          oracle = evaluateWgslWriterV3Oracle(task.oracle, execution);
        } catch (error) {
          oracle = { pass: false, error: error?.message || String(error) };
        }
        runs.push({
          run: runIndex + 1,
          execution,
          executionError,
          oracle,
          outputSha256: hashWgslSemanticEvidenceValue(execution?.outputs || null),
          pass: executionError === null && execution?.passed === true && oracle.pass === true,
        });
      }
      const deterministicReplay = summarizeReplay(
        runs,
        policy.referenceQualification.replayCount
      );
      tasks.push({
        taskId: task.taskId,
        semanticFamilyId: task.semanticFamilyId,
        populationRole: task.populationRole,
        pipelineKind: task.pipelineKind,
        packageSha256: task.packageSha256,
        oracleSha256: task.oracleSha256,
        quality: task.quality,
        runs,
        deterministicReplay,
        pass: task.quality.pass === true && deterministicReplay.pass,
      });
    }
  } finally {
    sessionCleanup = await executor.close();
  }
  const passedTasks = tasks.filter((task) => task.pass).length;
  const families = new Set(tasks.map((task) => task.semanticFamilyId));
  const allPass = passedTasks === tasks.length
    && families.size === 20
    && sessionCleanup?.passed === true;
  const core = {
    schema: 'doppler.wgsl-writer-v3-corpus-qualification/v1',
    createdAtUtc: new Date().toISOString(),
    experimentId: policy.experimentId,
    policy: { path: args.policyPath, sha256: await sha256File(args.policyPath) },
    corpusManifest: {
      path: corpusManifestPath,
      sha256: await sha256File(corpusManifestPath),
      internalManifestSha256: corpusManifest.manifestSha256,
      corpusSha256: corpusManifest.corpusSha256,
    },
    taskManifest: { path: taskManifestPath, sha256: await sha256File(taskManifestPath) },
    runtime: {
      backend: 'chromium_webgpu',
      identity: executor.runtimeIdentity,
      replayCount: policy.referenceQualification.replayCount,
      sessionCleanup,
    },
    tasks,
    summary: {
      tasks: tasks.length,
      runs: tasks.reduce((sum, task) => sum + task.runs.length, 0),
      semanticFamilies: families.size,
      passedTasks,
      failedTasks: tasks.length - passedTasks,
      computeTasks: tasks.filter((task) => task.pipelineKind === 'compute').length,
      renderTasks: tasks.filter((task) => task.pipelineKind === 'render').length,
      multiPassTasks: tasks.filter((task) => task.pipelineKind === 'multi_pass').length,
      deterministicReplayPassed: tasks.every((task) => task.deterministicReplay.pass),
      qualityPassed: tasks.every((task) => task.quality.pass),
      cleanupPassed: sessionCleanup?.passed === true
        && tasks.every((task) => task.runs.every((run) => run.execution?.cleanup?.passed === true)),
    },
    decision: allPass ? 'reference_corpus_qualified' : 'reference_corpus_rejected',
    corpusMaterializationAuthority: allPass,
    trainingAdmission: allPass,
    selectionAuthority: false,
    confirmationAuthority: false,
    promotionAuthority: false,
    generalWgslWriterClaim: false,
    productizationAllowed: false,
    claimBoundary: 'A pass admits the 20-family development corpus to training by proving its human-authored packages, quality gates, dispatches/draws, CPU/raster oracles, deterministic replay, and cleanup on the bound Chromium WebGPU identity. It contains no model capability or external promotion evidence.',
  };
  return {
    receipt: { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) },
    outputPath,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const result = await qualifyWgslWriterV3Corpus(args);
  const { receipt, outputPath } = result;
  await fs.mkdir(path.dirname(path.resolve(outputPath)), { recursive: true });
  await fs.writeFile(path.resolve(outputPath), `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  process.stdout.write(`${JSON.stringify({
    decision: receipt.decision,
    summary: receipt.summary,
    runtime: receipt.runtime.identity,
    receiptHash: receipt.receiptHash,
    outputPath,
  }, null, 2)}\n`);
  if (!receipt.trainingAdmission) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
