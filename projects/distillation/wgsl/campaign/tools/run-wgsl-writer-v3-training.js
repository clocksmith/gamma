#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';
import { runGammaWgslRequest } from './trainers/gamma-wgsl-trainer.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v3-training-policy.json';
const POLICY_IDS = new Set([
  'doppler-wgsl-writer-v3-training',
  'doppler-wgsl-writer-v3-diversity-repair-training',
  'doppler-wgsl-writer-v3-explicit-semantic-training',
  'doppler-wgsl-writer-v3-explicit-budget-training',
]);

function parseArgs(argv) {
  const args = { policyPath: DEFAULT_POLICY, laneId: '', seed: 47 };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--lane') args.laneId = argv[++index] || '';
    else if (token === '--seed') args.seed = Number(argv[++index]);
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.policyPath || !args.laneId || !Number.isSafeInteger(args.seed)) {
    throw new Error('--policy, --lane, and integer --seed are required.');
  }
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(path.resolve(filePath), 'utf8'));
}

async function sha256File(filePath) {
  return createHash('sha256').update(await fs.readFile(path.resolve(filePath))).digest('hex');
}

function sha256Value(value) {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
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
  if (hashWgslSemanticEvidenceValue(core) !== expected) {
    throw new Error(`${label} internal hash mismatch.`);
  }
}

async function requireAdmission(policy) {
  await Promise.all(Object.entries(policy.admission).map(([label, binding]) => (
    requireFileHash(binding.path, binding.sha256, `training admission ${label}`)
  )));
  const qualification = await readJson(policy.admission.referenceQualification.path);
  requireInternalHash(qualification, 'receiptHash', 'reference qualification');
  if (qualification.decision !== 'reference_corpus_qualified'
    || qualification.trainingAdmission !== true
    || qualification.summary.semanticFamilies !== 20) {
    throw new Error('WGSL writer v3 reference qualification does not admit training.');
  }
}

async function requireModel(policy, modelPath) {
  await Promise.all([
    requireFileHash(path.join(modelPath, 'config.json'), policy.model.configSha256, 'base config'),
    requireFileHash(path.join(modelPath, 'tokenizer.json'), policy.model.tokenizerSha256, 'tokenizer'),
  ]);
}

async function requireInitialization(policy, lane) {
  if (lane.initialization === 'base') return null;
  let adapter;
  if (lane.initialization === 'v2_seed47_adapter') {
    adapter = {
      path: policy.initialization.v2AdapterPath,
      configSha256: policy.initialization.v2AdapterConfigSha256,
      weightsSha256: policy.initialization.v2AdapterWeightsSha256,
    };
  } else {
    adapter = policy.initialization.adapters?.find((entry) => entry.id === lane.initialization);
  }
  if (!adapter?.path) {
    throw new Error(`WGSL writer v3 initialization is not bound: ${lane.initialization}.`);
  }
  const adapterPath = adapter.path;
  await Promise.all([
    requireFileHash(
      path.join(adapterPath, 'adapter_config.json'),
      adapter.configSha256,
      `${lane.initialization} config`
    ),
    requireFileHash(
      path.join(adapterPath, 'adapter_model.safetensors'),
      adapter.weightsSha256,
      `${lane.initialization} weights`
    ),
    ...(adapter.sourceTrainingStatus ? [requireFileHash(
      adapter.sourceTrainingStatus.path,
      adapter.sourceTrainingStatus.sha256,
      `${lane.initialization} source training status`
    )] : []),
  ]);
  if (adapter.sourceTrainingStatus) {
    const status = await readJson(adapter.sourceTrainingStatus.path);
    if (status.decision !== 'training_complete'
      || path.resolve(status.adapter?.path || '') !== path.resolve(adapterPath)
      || status.adapter?.configSha256 !== adapter.configSha256
      || status.adapter?.weightsSha256 !== adapter.weightsSha256) {
      throw new Error(`${lane.initialization} source training receipt does not bind the adapter.`);
    }
  }
  return path.resolve(adapterPath);
}

async function requireUnusedStatus(statusPath) {
  try {
    await fs.access(statusPath);
  } catch (error) {
    if (error?.code === 'ENOENT') return;
    throw error;
  }
  throw new Error(`WGSL writer v3 training status already exists: ${statusPath}`);
}

async function requireConfirmationAdmission(policy, lane, seed) {
  if (seed === lane.screeningSeed) return 'screening';
  if (!policy.evaluation.confirmationSeeds.includes(seed)) {
    throw new Error(`WGSL writer v3 seed is not frozen: ${seed}.`);
  }
  const selectionPath = path.resolve(
    policy.evaluation.selectionReceiptPath
      || 'reports/training/wgsl-writer/doppler-wgsl-writer-v3/evaluation/selection/selected-lane.json'
  );
  const selection = await readJson(selectionPath);
  const core = { ...selection };
  const expected = core.receiptHash;
  delete core.receiptHash;
  if (hashWgslSemanticEvidenceValue(core) !== expected
    || selection.decision !== 'lane_selected'
    || selection.seedConfirmationAuthority !== true
    || selection.selected?.candidateId !== lane.id) {
    throw new Error('WGSL writer v3 confirmation is not admitted for this lane.');
  }
  return 'seed_confirmation';
}

function gammaRequest(policy, lane, seed, modelPath, adapterPath, outputRoot) {
  return {
    protocol: policy.trainer.protocol,
    action: policy.trainer.action,
    runId: `${policy.experimentId}-${lane.id}-seed${seed}`,
    outputRoot,
    model: {
      modelId: policy.model.modelId,
      revision: policy.model.revision,
      localPath: modelPath,
    },
    policyMode: 'adapter',
    ...(adapterPath ? { adapterPath } : {}),
    adapter: {
      rank: policy.trainer.adapter.rank,
      alpha: policy.trainer.adapter.alpha,
      dropout: policy.trainer.adapter.dropout,
      targetModules: policy.trainer.adapter.targetModules,
    },
    datasetPath: path.resolve(lane.dataset.path),
    training: {
      dtype: policy.trainer.dtype,
      gradientCheckpointing: true,
      steps: policy.trainer.training.steps,
      gradientAccumulationSteps: policy.trainer.training.gradientAccumulationSteps,
      maxLength: policy.trainer.sequenceLength,
      learningRate: policy.trainer.training.learningRate,
      weightDecay: policy.trainer.training.weightDecay,
      maxGradNorm: policy.trainer.training.maxGradNorm,
      seed,
      rowOrder: policy.trainer.training.rowOrder,
    },
  };
}

export async function runWgslWriterV3Training(args) {
  const policy = await readJson(args.policyPath);
  if (!POLICY_IDS.has(policy.policyId)
    || policy.status !== 'frozen_before_training') {
    throw new Error('WGSL writer v3 training requires the frozen training policy.');
  }
  const lane = policy.lanes.find((entry) => entry.id === args.laneId);
  if (!lane) throw new Error(`WGSL writer v3 training lane is not frozen: ${args.laneId}.`);
  const phase = await requireConfirmationAdmission(policy, lane, args.seed);
  const modelPath = path.resolve(String(process.env.GAMMA_WGSL_MODEL_PATH || '').trim());
  if (!String(process.env.GAMMA_WGSL_MODEL_PATH || '').trim()) {
    throw new Error('GAMMA_WGSL_MODEL_PATH is required.');
  }
  const runRoot = path.resolve(
    policy.artifactRoot
      ? path.join(policy.artifactRoot, 'training')
      : 'reports/training/wgsl-writer/doppler-wgsl-writer-v3/training',
    `${lane.id}-seed${args.seed}`
  );
  const statusPath = path.join(runRoot, 'training-status.json');
  await requireUnusedStatus(statusPath);
  await Promise.all([
    requireAdmission(policy),
    requireModel(policy, modelPath),
    requireFileHash(lane.dataset.path, lane.dataset.sha256, `${lane.id} dataset`),
  ]);
  const adapterPath = await requireInitialization(policy, lane);
  const request = gammaRequest(
    policy,
    lane,
    args.seed,
    modelPath,
    adapterPath,
    path.join(runRoot, 'checkpoint')
  );
  const startedAtUtc = new Date().toISOString();
  const startedNs = process.hrtime.bigint();
  const { response, paths } = await runGammaWgslRequest(request, {
    runRoot,
    prefix: 'training',
  });
  const elapsedSeconds = Number(process.hrtime.bigint() - startedNs) / 1e9;
  const result = response.result;
  if (result.metrics?.steps !== policy.trainer.training.steps
    || result.metrics?.datasetRows !== lane.dataset.rows
    || result.metrics?.distinctRowsVisited !== lane.dataset.rows) {
    throw new Error(`${lane.id} row-consumption receipt failed.`);
  }
  const core = {
    schema: 'doppler.wgsl-writer-v3-training-status/v1',
    experimentId: policy.experimentId,
    laneId: lane.id,
    seed: args.seed,
    phase,
    startedAtUtc,
    completedAtUtc: new Date().toISOString(),
    elapsedSeconds,
    policy: { path: args.policyPath, sha256: await sha256File(args.policyPath) },
    dataset: lane.dataset,
    initialization: {
      kind: lane.initialization,
      adapterPath,
      capabilityEvidenceTransfers: false,
    },
    request: { path: paths.requestPath, sha256: await sha256File(paths.requestPath) },
    response: { path: paths.responsePath, sha256: await sha256File(paths.responsePath) },
    runtime: response.runtime,
    metrics: result.metrics,
    adapter: {
      path: result.adapterPath,
      treeSha256: result.policyHash,
      configSha256: await sha256File(path.join(result.adapterPath, 'adapter_config.json')),
      weightsSha256: await sha256File(path.join(result.adapterPath, 'adapter_model.safetensors')),
    },
    decision: 'training_complete',
    capabilityAuthority: lane.capabilityAuthority,
    selectionAuthority: false,
    confirmationAuthority: false,
    promotionAuthority: false,
    claimBoundary: 'Training completion proves matched optimizer execution, row consumption, and adapter identity only. Disjoint executable-package evaluation decides capability.',
  };
  const status = { ...core, receiptHash: sha256Value(core) };
  await fs.writeFile(statusPath, `${JSON.stringify(status, null, 2)}\n`, 'utf8');
  return { statusPath, status };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const result = await runWgslWriterV3Training(args);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
