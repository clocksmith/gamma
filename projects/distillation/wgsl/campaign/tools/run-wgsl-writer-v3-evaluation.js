#!/usr/bin/env node

import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';
import { createWgslAuthorBrowserExecutor } from './lib/wgsl-author-browser-executor.js';
import { buildWgslAuthorExecutionPlan } from './lib/wgsl-author-execution-plan.js';
import { parseWgslAuthorPackageResponse } from './lib/wgsl-author-package.js';
import { evaluateWgslWriterV3Oracle } from './lib/wgsl-writer-v3-oracles.js';
import { evaluateWgslWriterV3Quality } from './lib/wgsl-writer-v3-quality.js';
import { buildGammaProcessEnv } from './trainers/gamma-wgsl-trainer.js';

const execFileAsync = promisify(execFile);
const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v3-training-policy.json';
const REFERENCE_RUNNER = 'tools/wgsl-writer-peft-reference.py';
const ROLE_KEYS = Object.freeze({
  calibration: 'calibration',
  'checkpoint-selection': 'checkpoint_selection',
  'seed-confirmation': 'seed_confirmation',
});

function parseArgs(argv) {
  const args = { policyPath: DEFAULT_POLICY, role: '', outputRoot: '' };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--role') args.role = argv[++index] || '';
    else if (token === '--out-root') args.outputRoot = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!ROLE_KEYS[args.role]) {
    throw new Error('--role must be calibration, checkpoint-selection, or seed-confirmation.');
  }
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

function initializationAdapter(policy, initializationId) {
  if (initializationId === 'v2_seed47_adapter') {
    return {
      id: initializationId,
      path: policy.initialization.v2AdapterPath,
    };
  }
  return policy.initialization.adapters?.find((entry) => entry.id === initializationId) || null;
}

function baselineCandidates(policy) {
  if (!Array.isArray(policy.evaluation.baselineCandidates)) {
    return [{
      id: 'unchanged-v2',
      path: policy.initialization.v2AdapterPath,
    }];
  }
  const candidates = policy.evaluation.baselineCandidates.map((entry) => {
    const adapter = initializationAdapter(policy, entry.initialization);
    if (!adapter?.path) {
      throw new Error(`WGSL writer v3 baseline initialization is not bound: ${entry.initialization}.`);
    }
    return { id: entry.id, path: adapter.path };
  });
  if (candidates.length === 0) {
    throw new Error('WGSL writer v3 evaluation requires at least one bound adapter baseline.');
  }
  return candidates;
}

export function requireDisclosedOutputBudget(policy, corpusPolicy) {
  const promptContract = corpusPolicy.promptContract;
  const outputTokenBudget = Number(promptContract?.outputTokenBudget);
  if (promptContract?.includesExplicitOutputTokenBudget !== true
    || promptContract?.hardStopDisclosed !== true
    || !Number.isSafeInteger(outputTokenBudget)
    || outputTokenBudget < 1) {
    throw new Error('WGSL writer v3 evaluation requires a prompt-disclosed hard output-token budget.');
  }
  if (policy.evaluation?.generation?.maxNewTokens !== outputTokenBudget) {
    throw new Error(
      `WGSL writer v3 evaluation maxNewTokens must match the disclosed prompt budget: ${outputTokenBudget}.`
    );
  }
  return outputTokenBudget;
}

async function candidateFromStatus(policy, lane, seed, candidateId = lane.id) {
  const root = path.resolve(
    policy.artifactRoot
      ? path.join(policy.artifactRoot, 'training')
      : 'reports/training/wgsl-writer/doppler-wgsl-writer-v3/training',
    `${lane.id}-seed${seed}`
  );
  const statusPath = path.join(root, 'training-status.json');
  const status = await readJson(statusPath);
  if (status.decision !== 'training_complete'
    || status.laneId !== lane.id
    || status.seed !== seed) {
    throw new Error(`${lane.id} seed ${seed} training is incomplete.`);
  }
  return {
    id: candidateId,
    path: status.adapter.path,
    capabilityAuthority: lane.capabilityAuthority,
    statusPath,
    statusSha256: await sha256File(statusPath),
  };
}

async function trainedCandidates(policy, role) {
  if (role === 'seed-confirmation') {
    const selection = await readJson(
      policy.evaluation.selectionReceiptPath
        || 'reports/training/wgsl-writer/doppler-wgsl-writer-v3/evaluation/selection/selected-lane.json'
    );
    if (selection.decision !== 'lane_selected') {
      throw new Error('WGSL writer v3 seed confirmation has no selected lane.');
    }
    const lane = policy.lanes.find((entry) => entry.id === selection.selected.candidateId);
    return Promise.all(policy.evaluation.confirmationSeeds.map((seed) => (
      candidateFromStatus(policy, lane, seed, `${lane.id}-seed${seed}`)
    )));
  }
  const candidates = [];
  for (const lane of policy.lanes) {
    candidates.push(await candidateFromStatus(policy, lane, lane.screeningSeed));
  }
  return candidates;
}

async function runReference(options) {
  try {
    return await readJson(options.outputPath);
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }
  const python = path.resolve(
    process.env.GAMMA_WGSL_PYTHON
      || path.join(process.cwd(), '..', 'gamma', '.venv_rocm', 'bin', 'python')
  );
  const args = [
    path.resolve(REFERENCE_RUNNER),
    '--model', options.modelPath,
    '--model-revision', options.policy.model.revision,
    '--dataset', path.resolve(options.datasetPath),
    '--dtype', options.policy.trainer.dtype,
    '--max-new-tokens', String(options.policy.evaluation.generation.maxNewTokens),
    '--evaluation-role', options.role,
    '--experiment-id', options.policy.experimentId,
    '--out', path.resolve(options.outputPath),
    '--adapter', `0=${path.resolve(options.baselines[0].path)}`,
    '--base-candidate', 'unchanged-base',
  ];
  for (const baseline of options.baselines) {
    args.push('--candidate', `${baseline.id}=${path.resolve(baseline.path)}`);
  }
  for (const candidate of options.candidates) {
    args.push('--candidate', `${candidate.id}=${path.resolve(candidate.path)}`);
  }
  const result = await execFileAsync(python, args, {
    cwd: process.cwd(),
    env: buildGammaProcessEnv(),
    encoding: 'utf8',
    maxBuffer: 32 * 1024 * 1024,
  });
  await Promise.all([
    fs.writeFile(`${options.outputPath}.stdout.log`, result.stdout || '', 'utf8'),
    fs.writeFile(`${options.outputPath}.stderr.log`, result.stderr || '', 'utf8'),
  ]);
  return readJson(options.outputPath);
}

function summarizeReplay(runs) {
  const hashes = runs.map((run) => run.outputSha256);
  return {
    runs: runs.length,
    outputsMatch: hashes.length > 0 && new Set(hashes).size === 1,
    pass: runs.length === 2
      && runs.every((run) => run.pass)
      && new Set(hashes).size === 1,
  };
}

export async function evaluateCompletion(options) {
  const generation = {
    stopReason: options.completionTask.stopReason,
    completionTokens: options.completionTask.completionTokenIds.length,
    outputTokenBudget: options.outputTokenBudget,
    hardStopDisclosed: true,
  };
  const parsed = parseWgslAuthorPackageResponse(options.completion, options.task.contract);
  if (!parsed.ok) {
    return {
      taskId: options.task.taskId,
      generation,
      responseContractPass: false,
      responseContractViolations: parsed.violations,
      quality: { pass: false, violations: ['response_contract_failed'] },
      runs: [],
      deterministicReplay: { runs: 0, outputsMatch: false, pass: false },
      pass: false,
    };
  }
  const quality = evaluateWgslWriterV3Quality(
    { packageValue: parsed.value },
    options.family
  );
  let plan;
  try {
    plan = buildWgslAuthorExecutionPlan(parsed.value, {
      ...options.task.contract,
      formats: options.formatCatalog.formats,
      availableFeatures: options.runtime.requiredFeatures,
      limits: options.runtime.requiredLimits,
      allocationLimits: options.runtime.allocationLimits,
    }, options.task.context);
  } catch (error) {
    return {
      taskId: options.task.taskId,
      generation,
      responseContractPass: true,
      responseContractViolations: [],
      quality,
      planError: error?.message || String(error),
      runs: [],
      deterministicReplay: { runs: 0, outputsMatch: false, pass: false },
      pass: false,
    };
  }
  const runs = [];
  for (let runIndex = 0; runIndex < 2; runIndex += 1) {
    let execution = null;
    let executionError = null;
    try {
      execution = await options.executor.execute(plan, {
        id: `${options.candidateId}-${options.task.taskId}-run-${runIndex + 1}`,
      });
    } catch (error) {
      executionError = error?.message || String(error);
    }
    let oracle;
    try {
      oracle = evaluateWgslWriterV3Oracle(options.task.oracle, execution);
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
  const deterministicReplay = summarizeReplay(runs);
  return {
    taskId: options.task.taskId,
    generation,
    responseContractPass: true,
    responseContractViolations: [],
    packageSha256: hashWgslSemanticEvidenceValue(parsed.value),
    quality,
    runs,
    deterministicReplay,
    pass: quality.pass && deterministicReplay.pass,
  };
}

export function candidateSummary(tasks, completionTasks) {
  const count = tasks.length;
  return {
    taskCount: count,
    semanticPasses: tasks.filter((task) => task.pass).length,
    semanticPassRate: tasks.filter((task) => task.pass).length / count,
    responseContractPasses: tasks.filter((task) => task.responseContractPass).length,
    qualityPasses: tasks.filter((task) => task.quality.pass).length,
    compilePasses: tasks.filter((task) => task.runs.length > 0
      && task.runs.every((run) => run.execution?.compilation?.every((entry) => entry.passed))).length,
    deterministicReplayPasses: tasks.filter((task) => task.deterministicReplay.pass).length,
    lengthStops: tasks.filter((task) => task.generation.stopReason === 'length').length,
    meanResponseCharacters: completionTasks.reduce(
      (sum, task) => sum + Number(task.completionCharacterCount),
      0
    ) / count,
  };
}

export async function runWgslWriterV3Evaluation(args) {
  const policy = await readJson(args.policyPath);
  await Promise.all(Object.entries(policy.admission).map(([label, binding]) => (
    requireFileHash(binding.path, binding.sha256, `evaluation admission ${label}`)
  )));
  const corpusManifest = await readJson(policy.admission.corpusManifest.path);
  if (corpusManifest.policy.path !== policy.admission.corpusPolicy.path
    || corpusManifest.policy.sha256 !== policy.admission.corpusPolicy.sha256) {
    throw new Error('WGSL writer v3 corpus manifest does not bind the admitted corpus policy.');
  }
  await requireFileHash(
    corpusManifest.capabilityCatalog.path,
    corpusManifest.capabilityCatalog.sha256,
    'evaluation capability catalog'
  );
  const corpusPolicy = await readJson(corpusManifest.policy.path);
  const outputTokenBudget = requireDisclosedOutputBudget(policy, corpusPolicy);
  const roleKey = ROLE_KEYS[args.role];
  const role = corpusManifest.roles[roleKey];
  const taskManifest = await readJson(role.taskManifestPath);
  const catalog = await readJson(corpusManifest.capabilityCatalog.path);
  const families = new Map(catalog.families.map((family) => [family.id, family]));
  const formatCatalog = await readJson('tools/data/wgsl-author-format-catalog.json');
  const candidates = await trainedCandidates(policy, args.role);
  const outputRoot = path.resolve(
    args.outputRoot
      || path.join(
        policy.artifactRoot || 'reports/training/wgsl-writer/doppler-wgsl-writer-v3',
        'evaluation',
        args.role
      )
  );
  await fs.mkdir(outputRoot, { recursive: true });
  const referencePath = path.join(outputRoot, 'peft-reference.json');
  const modelPath = path.resolve(String(process.env.GAMMA_WGSL_MODEL_PATH || '').trim());
  if (!String(process.env.GAMMA_WGSL_MODEL_PATH || '').trim()) {
    throw new Error('GAMMA_WGSL_MODEL_PATH is required.');
  }
  const reference = await runReference({
    outputPath: referencePath,
    modelPath,
    datasetPath: role.datasetPath,
    baselines: baselineCandidates(policy),
    candidates,
    role: roleKey,
    policy,
  });
  const runtime = corpusPolicy.runtime;
  const executor = await createWgslAuthorBrowserExecutor({
    browserArgs: runtime.browserArgs,
    headless: runtime.headless,
    requiredBackend: runtime.requiredBackend,
    requiredVendor: runtime.requiredVendor,
    requiredFeatures: runtime.requiredFeatures,
    requiredLimits: runtime.requiredLimits,
    powerPreference: runtime.powerPreference,
    executionTimeoutMs: runtime.executionTimeoutMs,
  });
  const receipts = [];
  let sessionCleanup;
  try {
    for (const candidate of reference.candidates) {
      const tasks = [];
      const completionTasks = new Map(candidate.tasks.map((task) => [task.taskId, task]));
      for (const task of taskManifest.tasks) {
        const completionTask = completionTasks.get(task.taskId);
        if (!completionTask) {
          throw new Error(`${candidate.candidateId} is missing completion receipt ${task.taskId}.`);
        }
        tasks.push(await evaluateCompletion({
          candidateId: candidate.candidateId,
          completion: candidate.completions[task.taskId],
          completionTask,
          outputTokenBudget,
          task,
          family: families.get(task.semanticFamilyId),
          formatCatalog,
          runtime,
          executor,
        }));
      }
      receipts.push({
        candidateId: candidate.candidateId,
        adapterPath: candidate.adapterPath,
        adapterTreeSha256: candidate.adapterTreeSha256,
        capabilityAuthority: candidates.find((entry) => entry.id === candidate.candidateId)
          ?.capabilityAuthority ?? false,
        tasks,
        summary: candidateSummary(tasks, candidate.tasks),
      });
    }
  } finally {
    sessionCleanup = await executor.close();
  }
  const core = {
    schema: 'doppler.wgsl-writer-v3-evaluation/v1',
    experimentId: policy.experimentId,
    evaluationRole: roleKey,
    policy: { path: args.policyPath, sha256: await sha256File(args.policyPath) },
    population: {
      path: role.taskManifestPath,
      sha256: await sha256File(role.taskManifestPath),
      datasetPath: role.datasetPath,
      datasetSha256: role.datasetSha256,
      rows: role.rows,
    },
    reference: { path: referencePath, sha256: await sha256File(referencePath) },
    runtime: { identity: executor.runtimeIdentity, sessionCleanup },
    candidates: receipts,
    decision: 'evaluation_complete',
    selectionAuthority: args.role === 'checkpoint-selection',
    confirmationAuthority: args.role === 'seed-confirmation',
    promotionAuthority: false,
    generalWgslWriterClaim: false,
    claimBoundary: policy.claimBoundary,
  };
  const receipt = { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
  const receiptPath = path.join(outputRoot, 'evaluation.json');
  await fs.writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return { receiptPath, receipt };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const result = await runWgslWriterV3Evaluation(args);
  process.stdout.write(`${JSON.stringify({
    receiptPath: result.receiptPath,
    candidates: result.receipt.candidates.map((candidate) => ({
      candidateId: candidate.candidateId,
      summary: candidate.summary,
    })),
    receiptHash: result.receipt.receiptHash,
  }, null, 2)}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
