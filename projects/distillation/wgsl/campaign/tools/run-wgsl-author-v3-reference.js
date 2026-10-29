#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';
import { createWgslAuthorBrowserExecutor } from './lib/wgsl-author-browser-executor.js';
import {
  evaluateWgslAuthorReferenceOracle,
  materializeWgslAuthorReferenceTask,
  validateWgslAuthorReferenceManifest,
} from './lib/wgsl-author-reference.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v3-campaign-policy.json';

function parseArgs(argv) {
  const args = { policyPath: DEFAULT_POLICY, outputPath: '' };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--out') args.outputPath = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.policyPath) throw new Error('--policy requires a path.');
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(path.resolve(filePath), 'utf8'));
}

async function sha256File(filePath) {
  return createHash('sha256').update(await fs.readFile(path.resolve(filePath))).digest('hex');
}

async function requireBinding(binding, label) {
  const actual = await sha256File(binding.path);
  if (actual !== binding.sha256) {
    throw new Error(`${label} SHA-256 mismatch: expected ${binding.sha256}, got ${actual}.`);
  }
  return actual;
}

function evaluateOracleSafely(oracle, execution) {
  try {
    return evaluateWgslAuthorReferenceOracle(oracle, execution);
  } catch (error) {
    return {
      pass: false,
      kind: oracle?.kind || null,
      resourceId: oracle?.resourceId || null,
      error: error?.message || String(error),
    };
  }
}

function summarizeDeterministicReplay(runs, requiredRuns) {
  const outputHashes = runs.map((run) => run.outputSha256);
  const executedPasses = runs.map((run) => JSON.stringify(
    run.execution?.executedPassIds || []
  ));
  const outputsMatch = new Set(outputHashes).size === 1;
  const executedPassesMatch = new Set(executedPasses).size === 1;
  return {
    requiredRuns,
    completedRuns: runs.length,
    outputHashes,
    outputsMatch,
    executedPassesMatch,
    pass: runs.length === requiredRuns
      && runs.every((run) => run.pass)
      && outputsMatch
      && executedPassesMatch,
  };
}

export async function runWgslAuthorV3Reference(args) {
  const policy = await readJson(args.policyPath);
  if (policy?.policyId !== 'doppler-wgsl-writer-v3-general-authoring'
    || policy?.status !== 'mechanics_implemented_reference_qualification_blocked'
    || policy?.mechanics?.referenceQualification?.status !== 'not_run'
    || policy?.authority?.training !== false
    || policy?.authority?.promotion !== false) {
    throw new Error('WGSL author v3 reference runner requires the blocked v3 campaign policy.');
  }
  const bindings = [
    ['response schema', policy.mechanics.responseSchema],
    ['package validator', policy.mechanics.packageValidator],
    ['execution planner', policy.mechanics.executionPlanner],
    ['format catalog', policy.mechanics.formatCatalog],
    ['capability catalog', policy.mechanics.capabilityCatalog],
    ['browser executor', policy.mechanics.browserExecutor],
    ['reference library', policy.mechanics.referenceQualification.library],
    ['reference harness', policy.mechanics.referenceQualification.harness],
    ['reference manifest', policy.mechanics.referenceQualification.manifest],
  ];
  await Promise.all(bindings.map(([label, binding]) => requireBinding(binding, label)));
  const manifest = validateWgslAuthorReferenceManifest(
    await readJson(policy.mechanics.referenceQualification.manifest.path)
  );
  if (manifest.experimentId !== policy.experimentId
    || manifest.formatCatalog.path !== policy.mechanics.formatCatalog.path
    || manifest.formatCatalog.sha256 !== policy.mechanics.formatCatalog.sha256) {
    throw new Error('WGSL author reference manifest is not bound to the campaign.');
  }
  const formatCatalog = await readJson(manifest.formatCatalog.path);
  const materialized = [];
  for (const task of manifest.tasks) {
    materialized.push(await materializeWgslAuthorReferenceTask(
      task,
      manifest,
      formatCatalog
    ));
  }
  const executor = await createWgslAuthorBrowserExecutor({
    browserArgs: manifest.runtime.browserArgs,
    headless: manifest.runtime.headless,
    requiredBackend: manifest.runtime.requiredBackend,
    requiredVendor: manifest.runtime.requiredVendor,
    requiredFeatures: manifest.runtime.requiredFeatures,
    requiredLimits: manifest.runtime.requiredLimits,
    powerPreference: manifest.runtime.powerPreference,
    executionTimeoutMs: manifest.runtime.executionTimeoutMs,
  });
  const tasks = [];
  let sessionCleanup = null;
  try {
    for (const task of materialized) {
      const runs = [];
      for (let runIndex = 0; runIndex < manifest.runtime.replayCount; runIndex += 1) {
        let execution = null;
        let executionError = null;
        try {
          execution = await executor.execute(task.plan, {
            id: `${task.taskId}-run-${runIndex + 1}`,
          });
        } catch (error) {
          executionError = error?.message || String(error);
        }
        const oracle = evaluateOracleSafely(task.oracle, execution);
        runs.push({
          run: runIndex + 1,
          execution,
          executionError,
          outputSha256: hashWgslSemanticEvidenceValue(execution?.outputs || null),
          oracle,
          pass: executionError === null
            && execution?.passed === true
            && oracle.pass === true,
        });
      }
      const deterministicReplay = summarizeDeterministicReplay(
        runs,
        manifest.runtime.replayCount
      );
      tasks.push({
        taskId: task.taskId,
        pipelineKind: task.pipelineKind,
        objective: task.objective,
        sourceBindings: task.sourceBindings,
        packageSha256: task.packageSha256,
        planSha256: task.planSha256,
        runs,
        deterministicReplay,
        pass: deterministicReplay.pass,
      });
    }
  } finally {
    sessionCleanup = await executor.close();
  }
  const passedTasks = tasks.filter((task) => task.pass).length;
  const allTasksPass = passedTasks === tasks.length && sessionCleanup?.passed === true;
  const core = {
    schema: 'doppler.wgsl-author-reference-qualification/v1',
    createdAtUtc: new Date().toISOString(),
    experimentId: policy.experimentId,
    evaluationRole: manifest.role,
    policy: {
      path: args.policyPath,
      sha256: await sha256File(args.policyPath),
    },
    manifest: policy.mechanics.referenceQualification.manifest,
    runtime: {
      backend: 'chromium_webgpu',
      identity: executor.runtimeIdentity,
      executionTimeoutMs: executor.executionTimeoutMs,
      replayCount: manifest.runtime.replayCount,
      sessionCleanup,
    },
    tasks,
    summary: {
      tasks: tasks.length,
      runs: tasks.reduce((count, task) => count + task.runs.length, 0),
      passedTasks,
      failedTasks: tasks.length - passedTasks,
      computeTasks: tasks.filter((task) => task.pipelineKind === 'compute').length,
      renderTasks: tasks.filter((task) => task.pipelineKind === 'render').length,
      multiPassTasks: tasks.filter((task) => task.pipelineKind === 'multi_pass').length,
      deterministicReplayPassed: tasks.every((task) => task.deterministicReplay.pass),
      cleanupPassed: sessionCleanup?.passed === true
        && tasks.every((task) => task.runs.every((run) => run.execution?.cleanup?.passed === true)),
    },
    decision: allTasksPass
      ? 'reference_package_mechanics_qualified'
      : 'reference_package_mechanics_failed',
    mechanicsQualificationAuthority: allTasksPass,
    corpusMaterializationAuthority: false,
    trainingAuthority: false,
    selectionAuthority: false,
    confirmationAuthority: false,
    promotionAuthority: false,
    generalWgslWriterClaim: false,
    productizationAllowed: false,
    claimBoundary: 'A passing receipt qualifies visible compute, procedural-render, indexed-render, multi-pass, deterministic replay, tracked GPU-resource cleanup, readback, and oracle mechanics only on the bound Chromium WebGPU identity. It is not model capability, corpus, training, selection, confirmation, promotion, or product evidence.',
  };
  return { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const receipt = await runWgslAuthorV3Reference(args);
  const json = `${JSON.stringify(receipt, null, 2)}\n`;
  if (args.outputPath) {
    const outputPath = path.resolve(args.outputPath);
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, json, 'utf8');
    console.error(`[wgsl-author-reference] wrote ${args.outputPath}`);
  } else {
    process.stdout.write(json);
  }
  if (receipt.decision !== 'reference_package_mechanics_qualified') process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}

export { evaluateOracleSafely, summarizeDeterministicReplay };
