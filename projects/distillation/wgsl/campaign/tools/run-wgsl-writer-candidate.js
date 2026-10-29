#!/usr/bin/env node

import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { activateLoRAFromTrainingOutputForPipeline } from '../src/client/runtime/lora.js';
import { getRuntimeConfig, setRuntimeConfig } from '../src/config/runtime.js';
import { destroyDevice, resetDeviceState } from '../src/gpu/device.js';
import { applyRuntimeProfile } from '../src/inference/browser-harness-runtime-helpers.js';
import { initializeInference } from '../src/inference/test-harness.js';
import { destroyBufferPool } from '../src/memory/buffer-pool.js';
import { installNodeFileFetchShim } from '../src/tooling/node-file-fetch.js';
import { bootstrapNodeWebGPU } from '../src/tooling/node-webgpu.js';
import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';
import { buildWgslWriterPrompt } from './lib/wgsl-writer-semantic-harness.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v1-diagnostic-policy.json';

function parseArgs(argv) {
  const args = {
    policyPath: DEFAULT_POLICY,
    modelDir: '',
    candidateId: '',
    outputPath: '',
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--model-dir') args.modelDir = argv[++index] || '';
    else if (token === '--candidate') args.candidateId = argv[++index] || '';
    else if (token === '--out') args.outputPath = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.modelDir) throw new Error('--model-dir is required.');
  if (!args.candidateId) throw new Error('--candidate is required.');
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

function requireInternalReceiptHash(receipt, label) {
  const core = { ...receipt };
  delete core.receiptHash;
  if (receipt?.receiptHash !== hashWgslSemanticEvidenceValue(core)) {
    throw new Error(`${label} internal receipt hash mismatch.`);
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

export async function runWgslWriterCandidate(args) {
  const policy = await readJson(args.policyPath);
  if (policy?.policyId !== 'doppler-wgsl-writer-v1-zero-shot-diagnostic') {
    throw new Error('WGSL writer candidate: unsupported policy.');
  }
  const [basePolicy, referenceReceipt] = await Promise.all([
    readJson(policy.predecessor.basePolicy.path),
    readJson(policy.predecessor.referenceReceipt.path),
  ]);
  const candidate = basePolicy.candidateInitializations.find((entry) => (
    entry.id === args.candidateId && policy.candidateIds.includes(entry.id)
  ));
  if (!candidate) throw new Error(`WGSL writer candidate is not frozen: ${args.candidateId}.`);
  requireInternalReceiptHash(referenceReceipt, 'writer reference receipt');
  if (basePolicy.policyId !== 'doppler-wgsl-writer-v1'
    || referenceReceipt.decision !== policy.predecessor.referenceReceipt.requiredDecision
    || referenceReceipt.mode !== 'reference'
    || referenceReceipt.mechanicsQualificationAuthority !== true
    || referenceReceipt.selectionAuthority !== false
    || referenceReceipt.promotionAuthority !== false) {
    throw new Error('WGSL writer candidate: predecessor admission failed.');
  }
  const bindings = [
    requireFileHash(
      policy.predecessor.basePolicy.path,
      policy.predecessor.basePolicy.sha256,
      'writer base policy'
    ),
    requireFileHash(
      policy.predecessor.referenceReceipt.path,
      policy.predecessor.referenceReceipt.sha256,
      'writer reference receipt'
    ),
    requireFileHash(
      policy.population.path,
      policy.population.sha256,
      'writer mechanics population'
    ),
    requireFileHash(
      policy.candidateRunner.path,
      policy.candidateRunner.sha256,
      'writer candidate runner'
    ),
    requireFileHash(
      policy.semanticHarness.path,
      policy.semanticHarness.sha256,
      'writer semantic harness'
    ),
    requireFileHash(
      basePolicy.runtime.artifactStatusPath,
      basePolicy.runtime.artifactStatusSha256,
      'writer model artifact status'
    ),
    requireFileHash(
      basePolicy.runtime.conversionConfigPath,
      basePolicy.runtime.conversionConfigSha256,
      'writer model conversion config'
    ),
    requireFileHash(
      basePolicy.runtime.adapterPortabilityReceiptPath,
      basePolicy.runtime.adapterPortabilityReceiptSha256,
      'writer adapter portability receipt'
    ),
    requireFileHash(
      path.join(args.modelDir, 'manifest.json'),
      basePolicy.runtime.modelManifestSha256,
      'writer model manifest'
    ),
  ];
  if (candidate.adapterManifestPath) {
    bindings.push(
      requireFileHash(
        candidate.adapterManifestPath,
        candidate.adapterManifestSha256,
        'writer candidate adapter manifest'
      ),
      requireFileHash(
        candidate.adapterWeightsPath,
        candidate.adapterWeightsSha256,
        'writer candidate adapter weights'
      ),
      requireFileHash(
        candidate.predecessorReceiptPath,
        candidate.predecessorReceiptSha256,
        'writer candidate predecessor receipt'
      )
    );
  }
  await Promise.all(bindings);
  const manifest = await readJson(policy.population.path);
  const prompts = [];
  for (const task of manifest.tasks || []) {
    await requireFileHash(
      task.referenceShaderPath,
      task.referenceShaderSha256,
      `${task.taskId} reference shader`
    );
    const referenceShader = (await fs.readFile(
      path.resolve(task.referenceShaderPath),
      'utf8'
    )).trim();
    prompts.push({
      task,
      referenceShader,
      prompt: buildWgslWriterPrompt(task, basePolicy.promptContract),
    });
  }

  installNodeFileFetchShim();
  const originalRuntime = cloneValue(getRuntimeConfig());
  let harness = null;
  let bootstrap = null;
  try {
    await applyRuntimeProfile(basePolicy.runtime.runtimeProfile);
    const runtimeConfig = cloneValue(getRuntimeConfig());
    bootstrap = await bootstrapNodeWebGPU();
    if (!bootstrap?.ok) {
      throw new Error(`WebGPU bootstrap failed: ${bootstrap?.detail || 'unknown error'}`);
    }
    harness = await initializeInference(pathToFileURL(path.resolve(args.modelDir)).href, {
      modelId: basePolicy.runtime.modelId,
      runtime: { runtimeConfig },
    });
    let activation = {
      requested: false,
      activated: false,
      adapterManifestPath: null,
      adapterManifestSha256: null,
      adapterWeightsSha256: null,
    };
    if (candidate.adapterManifestPath) {
      const activated = await activateLoRAFromTrainingOutputForPipeline(harness.pipeline, {
        adapterManifestPath: candidate.adapterManifestPath,
      });
      if (activated.activated !== true) {
        throw new Error(`Adapter activation failed: ${activated.reason || 'unknown reason'}.`);
      }
      activation = {
        requested: true,
        activated: true,
        adapterManifestPath: candidate.adapterManifestPath,
        adapterManifestSha256: candidate.adapterManifestSha256,
        adapterWeightsSha256: candidate.adapterWeightsSha256,
      };
    }
    const completions = {};
    const tasks = [];
    for (const [index, entry] of prompts.entries()) {
      console.error(
        `[wgsl-writer-candidate] ${candidate.id} task ${index + 1}/${prompts.length}`
      );
      const generated = await generateCompletion(
        harness.pipeline,
        entry.prompt,
        basePolicy.generation
      );
      completions[entry.task.taskId] = generated.output;
      tasks.push({
        taskId: entry.task.taskId,
        prompt: entry.prompt,
        promptSha256: hashWgslSemanticEvidenceValue(entry.prompt),
        completion: generated.output,
        completionSha256: hashWgslSemanticEvidenceValue(generated.output),
        completionCharacterCount: generated.output.length,
        exactReferenceCompletion: generated.output === entry.referenceShader,
        generation: generated,
      });
    }
    const core = {
      schema: 'doppler.wgsl-writer-completions/v1',
      experimentId: 'doppler-wgsl-writer-v1',
      evaluationRole: 'visible_zero_shot_diagnostic',
      policy: { path: args.policyPath, sha256: await sha256File(args.policyPath) },
      population: policy.population,
      referenceReceipt: policy.predecessor.referenceReceipt,
      candidate,
      runtime: {
        dopplerCommit: gitHead(),
        modelId: basePolicy.runtime.modelId,
        modelManifestSha256: basePolicy.runtime.modelManifestSha256,
        runtimeProfile: basePolicy.runtime.runtimeProfile,
        provider: bootstrap.provider ?? null,
        capabilities: harness.capabilities,
        activation,
      },
      generation: basePolicy.generation,
      promptContract: basePolicy.promptContract,
      submission: {
        ordinalForCandidate: 1,
        retryPerformed: false,
        promptOrSamplerChangedAfterFreeze: false,
      },
      completions,
      tasks,
      diagnosticAuthority: true,
      selectionAuthority: false,
      confirmationAuthority: false,
      promotionAuthority: false,
      productizationAllowed: false,
      claimBoundary: 'Zero-shot output on visible mechanics-only tasks. This receipt may diagnose transfer from repair to full-shader generation but cannot select, confirm, promote, or productize a writer.',
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
  const receipt = await runWgslWriterCandidate(args);
  const json = `${JSON.stringify(receipt, null, 2)}\n`;
  if (args.outputPath) {
    const outputPath = path.resolve(args.outputPath);
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, json, 'utf8');
    console.error(`[wgsl-writer-candidate] wrote ${args.outputPath}`);
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
