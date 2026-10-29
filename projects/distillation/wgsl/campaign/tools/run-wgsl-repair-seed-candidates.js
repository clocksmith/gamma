#!/usr/bin/env node

import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { getRuntimeConfig, setRuntimeConfig } from '../src/config/runtime.js';
import { activateLoRAFromTrainingOutputForPipeline } from '../src/client/runtime/lora.js';
import { destroyDevice, resetDeviceState } from '../src/gpu/device.js';
import { initializeInference } from '../src/inference/test-harness.js';
import { applyRuntimeProfile } from '../src/inference/browser-harness-runtime-helpers.js';
import { destroyBufferPool } from '../src/memory/buffer-pool.js';
import { installNodeFileFetchShim } from '../src/tooling/node-file-fetch.js';
import { bootstrapNodeWebGPU } from '../src/tooling/node-webgpu.js';
import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-repair-v13-seed-selection-policy.json';

function parseArgs(argv) {
  const args = {
    policyPath: DEFAULT_POLICY,
    modelDir: '',
    seed: null,
    outputPath: '',
    populationRole: 'checkpointSelection',
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--model-dir') args.modelDir = argv[++index] || '';
    else if (token === '--seed') args.seed = Number(argv[++index]);
    else if (token === '--out') args.outputPath = argv[++index] || '';
    else if (token === '--population-role') args.populationRole = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.modelDir) throw new Error('--model-dir is required.');
  if (![11, 29, 47].includes(args.seed)) throw new Error('--seed must be 11, 29, or 47.');
  if (!['calibration', 'checkpointSelection', 'seedConfirmation', 'promotion']
    .includes(args.populationRole)) {
    throw new Error('--population-role is invalid.');
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
}

function gitHead() {
  try {
    return execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
  } catch {
    return null;
  }
}

function cloneValue(value) {
  return typeof structuredClone === 'function'
    ? structuredClone(value)
    : JSON.parse(JSON.stringify(value));
}

function buildPrompt(task, source, contextCharacters) {
  const start = source.indexOf(task.brokenSpan);
  if (start < 0 || source.indexOf(task.brokenSpan, start + 1) >= 0) {
    throw new Error(`${task.taskId}: broken span must occur exactly once.`);
  }
  const end = start + task.brokenSpan.length;
  return [
    'Repair one harness-owned WGSL span.',
    'Return only the replacement WGSL for <broken_span>; no Markdown fence, diff, or explanation.',
    `Source: ${task.sourcePath}@${task.sourceSha256}`,
    `Mutation class: ${task.mutationClass}`,
    '<context_before>',
    source.slice(Math.max(0, start - contextCharacters), start),
    '</context_before>',
    '<broken_span>',
    task.brokenSpan,
    '</broken_span>',
    '<context_after>',
    source.slice(end, Math.min(source.length, end + contextCharacters)),
    '</context_after>',
  ].join('\n');
}

async function generateCompletion(pipeline, prompt, generation) {
  pipeline.reset();
  const tokenIds = [];
  const chunks = [];
  for await (const chunk of pipeline.generate(prompt, {
    ...generation,
    useChatTemplate: false,
    benchmark: false,
    onToken(tokenId) {
      tokenIds.push(tokenId);
    },
  })) {
    chunks.push(String(chunk));
  }
  const outputRaw = chunks.join('');
  const stats = pipeline.getStats?.() || {};
  return {
    outputRaw,
    output: outputRaw.trim(),
    tokenIds,
    stopReason: stats.stopReason ?? null,
    stopTokenId: stats.stopTokenId ?? null,
    stats: {
      firstTokenMs: stats.firstTokenMs ?? stats.ttftMs ?? null,
      prefillMs: stats.prefillMs ?? stats.prefillTimeMs ?? null,
      decodeMs: stats.decodeMs ?? stats.decodeTimeMs ?? null,
      totalMs: stats.totalMs ?? stats.totalTimeMs ?? null,
    },
  };
}

export async function runWgslRepairSeedCandidates(args) {
  const policy = await readJson(args.policyPath);
  const candidate = policy.eligibleCandidates.find((entry) => entry.seed === args.seed);
  if (!candidate) throw new Error(`Seed ${args.seed} is not eligible.`);
  const population = policy.populations?.[args.populationRole];
  if (!population?.path || !population?.sha256) {
    throw new Error(`Population role is not frozen in the policy: ${args.populationRole}.`);
  }
  const optionalBindings = [];
  if (policy.selectionReceipt?.path && policy.selectionReceipt?.sha256) {
    optionalBindings.push(requireFileHash(
      policy.selectionReceipt.path,
      policy.selectionReceipt.sha256,
      'selected-candidate receipt'
    ));
  }
  if (policy.materialization?.policyPath && policy.materialization?.policySha256) {
    optionalBindings.push(requireFileHash(
      policy.materialization.policyPath,
      policy.materialization.policySha256,
      'population materialization policy'
    ));
  }
  if (policy.candidateRunner?.path && policy.candidateRunner?.sha256) {
    optionalBindings.push(requireFileHash(
      policy.candidateRunner.path,
      policy.candidateRunner.sha256,
      'candidate generation runner'
    ));
  }
  await Promise.all([
    ...optionalBindings,
    requireFileHash(population.path, population.sha256, `${args.populationRole} population`),
    requireFileHash(
      policy.predecessor.adapterPortabilityReceiptPath,
      policy.predecessor.adapterPortabilityReceiptSha256,
      'adapter portability receipt'
    ),
    requireFileHash(
      policy.runtime.artifactStatusPath,
      policy.runtime.artifactStatusSha256,
      'model artifact status'
    ),
    requireFileHash(
      policy.runtime.conversionConfigPath,
      policy.runtime.conversionConfigSha256,
      'conversion config'
    ),
    requireFileHash(candidate.adapterManifestPath, candidate.adapterManifestSha256, 'adapter manifest'),
    requireFileHash(candidate.adapterWeightsPath, candidate.adapterWeightsSha256, 'adapter weights'),
    requireFileHash(
      path.join(args.modelDir, 'manifest.json'),
      policy.runtime.modelManifestSha256,
      'model manifest'
    ),
  ]);
  const manifest = await readJson(population.path);
  const prompts = [];
  for (const task of manifest.tasks) {
    await requireFileHash(task.sourcePath, task.sourceSha256, `${task.taskId} source`);
    const source = (await fs.readFile(path.resolve(task.sourcePath), 'utf8')).trim();
    const prompt = buildPrompt(
      task,
      source,
      policy.promptContract.contextCharactersPerSide
    );
    prompts.push({ task, prompt });
  }

  installNodeFileFetchShim();
  const originalRuntime = cloneValue(getRuntimeConfig());
  let harness = null;
  let bootstrap = null;
  try {
    await applyRuntimeProfile(policy.runtime.runtimeProfile);
    const runtimeConfig = cloneValue(getRuntimeConfig());
    bootstrap = await bootstrapNodeWebGPU();
    if (!bootstrap?.ok) {
      throw new Error(`WebGPU bootstrap failed: ${bootstrap?.detail || 'unknown error'}`);
    }
    harness = await initializeInference(pathToFileURL(path.resolve(args.modelDir)).href, {
      modelId: policy.runtime.modelId,
      runtime: { runtimeConfig },
    });
    const activation = await activateLoRAFromTrainingOutputForPipeline(harness.pipeline, {
      adapterManifestPath: candidate.adapterManifestPath,
    });
    if (activation.activated !== true) {
      throw new Error(`Adapter activation failed: ${activation.reason || 'unknown reason'}.`);
    }
    const tasks = [];
    const completions = {};
    for (const [index, { task, prompt }] of prompts.entries()) {
      console.error(`[wgsl-seed-candidates] seed ${args.seed} task ${index + 1}/${prompts.length}`);
      const generation = await generateCompletion(harness.pipeline, prompt, policy.generation);
      completions[task.taskId] = generation.output;
      tasks.push({
        taskId: task.taskId,
        prompt,
        promptSha256: hashWgslSemanticEvidenceValue(prompt),
        completion: generation.output,
        completionSha256: hashWgslSemanticEvidenceValue(generation.output),
        exactReferenceCompletion: generation.output === task.referenceSpan,
        generation,
      });
    }
    const core = {
      schema: 'doppler.wgsl-repair-seed-candidate-completions/v1',
      experimentId: 'doppler-wgsl-repair-v13',
      evaluationRole: manifest.role,
      policy: { path: args.policyPath, sha256: await sha256File(args.policyPath) },
      population,
      candidate: {
        lane: policy.eligibleLane,
        seed: candidate.seed,
        adapterManifestPath: candidate.adapterManifestPath,
        adapterManifestSha256: candidate.adapterManifestSha256,
        adapterWeightsPath: candidate.adapterWeightsPath,
        adapterWeightsSha256: candidate.adapterWeightsSha256,
      },
      runtime: {
        dopplerCommit: gitHead(),
        modelId: policy.runtime.modelId,
        modelManifestSha256: policy.runtime.modelManifestSha256,
        runtimeProfile: policy.runtime.runtimeProfile,
        provider: bootstrap.provider ?? null,
        capabilities: harness.capabilities,
      },
      generation: policy.generation,
      promptContract: policy.promptContract,
      completions,
      tasks,
      selectionAuthority: false,
      promotionAuthority: false,
      claimBoundary: manifest.role === 'checkpoint_selection'
        ? 'Deterministic Doppler candidate completions on the frozen checkpoint-selection population. Semantic dispatch evaluation and the frozen ranking policy must run before a seed can be selected.'
        : `Deterministic Doppler candidate completions on the frozen ${manifest.role} population. This receipt has no authority beyond that declared role.`,
    };
    return { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
  } finally {
    try {
      await harness?.pipeline?.unload?.();
    } catch {
      // Best-effort cleanup for an internal experiment tool.
    }
    try {
      harness?.pipeline?.releaseGPUResources?.();
    } catch {
      // Best-effort cleanup for an internal experiment tool.
    }
    try {
      destroyBufferPool();
    } finally {
      try {
        destroyDevice();
      } finally {
        resetDeviceState();
      }
    }
    setRuntimeConfig(originalRuntime);
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const receipt = await runWgslRepairSeedCandidates(args);
  const json = `${JSON.stringify(receipt, null, 2)}\n`;
  if (args.outputPath) {
    const outputPath = path.resolve(args.outputPath);
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, json, 'utf8');
    console.error(`[wgsl-seed-candidates] wrote ${args.outputPath}`);
  } else {
    process.stdout.write(json);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
