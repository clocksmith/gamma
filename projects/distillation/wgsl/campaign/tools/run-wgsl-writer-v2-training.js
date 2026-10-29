#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { runLoraPipeline } from '../src/experimental/training/lora-pipeline.js';
import { loadTrainingWorkloadCapsule } from '../src/experimental/training/workloads.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v2-training-policy.json';

function parseArgs(argv) {
  const args = { policyPath: DEFAULT_POLICY, seed: null };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--seed') args.seed = Number(argv[++index]);
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.policyPath) throw new Error('--policy requires a value.');
  if (!Number.isInteger(args.seed)) throw new Error('--seed requires an integer.');
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
  return actual;
}

function requireInternalHash(value, hashField, label) {
  const core = { ...value };
  const expected = core[hashField];
  delete core[hashField];
  const actual = sha256Value(core);
  if (expected !== actual) {
    throw new Error(`${label} internal ${hashField} mismatch: expected ${expected}, got ${actual}.`);
  }
}

async function assertRunRootUnused(runRoot) {
  const statusPath = path.join(runRoot, 'training-status.json');
  try {
    const status = await readJson(statusPath);
    if (status?.decision === 'training_complete') {
      throw new Error(`Writer v2 seed already completed: ${statusPath}`);
    }
    throw new Error(`Writer v2 run root already contains status: ${statusPath}`);
  } catch (error) {
    if (error?.code === 'ENOENT') return;
    throw error;
  }
}

async function verifyAdmission(policy) {
  const qualification = await readJson(policy.admission.referenceQualification.path);
  const corpusManifest = await readJson(policy.admission.corpusManifest.path);
  const registry = await readJson(policy.admission.workloadRegistry.path);
  await Promise.all([
    requireFileHash(
      policy.admission.corpusPolicy.path,
      policy.admission.corpusPolicy.sha256,
      'writer corpus policy'
    ),
    requireFileHash(
      policy.admission.corpusManifest.path,
      policy.admission.corpusManifest.sha256,
      'writer corpus manifest'
    ),
    requireFileHash(
      policy.admission.referenceQualification.path,
      policy.admission.referenceQualification.sha256,
      'writer reference qualification'
    ),
    requireFileHash(
      policy.admission.workloadRegistry.path,
      policy.admission.workloadRegistry.sha256,
      'training workload registry'
    ),
    requireFileHash(policy.dataset.path, policy.dataset.sha256, 'writer training dataset'),
  ]);
  requireInternalHash(corpusManifest, 'manifestSha256', 'writer corpus manifest');
  requireInternalHash(qualification, 'receiptHash', 'writer reference qualification');
  if (qualification.decision !== policy.admission.referenceQualification.requiredDecision
    || qualification.trainingAdmission !== true) {
    throw new Error('Writer v2 reference qualification does not admit training.');
  }
  if (registry.registryHash !== policy.admission.workloadRegistry.registryHash) {
    throw new Error('Training workload registry internal hash mismatch.');
  }
  if (corpusManifest.roles?.training?.rows !== policy.dataset.rows
    || corpusManifest.roles?.training?.semanticFamilyCount !== policy.dataset.semanticFamilies
    || corpusManifest.roles?.training?.datasetSha256 !== policy.dataset.sha256) {
    throw new Error('Writer v2 training dataset is not bound to the admitted corpus.');
  }
}

function validateResult(result, policy, workloadBinding) {
  const metrics = result.metrics || {};
  if (metrics.datasetRows !== policy.dataset.rows
    || metrics.distinctRowsVisited !== policy.dataset.rows
    || metrics.steps !== policy.trainer.training.steps
    || metrics.rowOrder !== policy.dataset.rowOrder) {
    throw new Error(`Writer v2 seed ${workloadBinding.seed} row-consumption receipt failed.`);
  }
  if (!Array.isArray(result.exports) || result.exports.length !== 1) {
    throw new Error(`Writer v2 seed ${workloadBinding.seed} requires exactly one final export.`);
  }
  const exported = result.exports[0];
  if (exported.checkpointId !== `checkpoint-${String(policy.trainer.training.steps).padStart(6, '0')}`
    || exported.manifest?.checksum !== exported.weightsSha256) {
    throw new Error(`Writer v2 seed ${workloadBinding.seed} export identity failed.`);
  }
  return exported;
}

export async function runWgslWriterV2Training(args) {
  const policy = await readJson(args.policyPath);
  if (policy?.policyId !== 'doppler-wgsl-writer-v2-training'
    || policy?.status !== 'frozen_before_training') {
    throw new Error('Writer v2 training requires the frozen training policy.');
  }
  const workloadBinding = policy.workloads.find((entry) => entry.seed === args.seed);
  if (!workloadBinding) throw new Error(`Writer v2 seed is not frozen: ${args.seed}`);
  await verifyAdmission(policy);
  await requireFileHash(
    workloadBinding.path,
    workloadBinding.sha256,
    `writer seed ${args.seed} workload`
  );
  await assertRunRootUnused(workloadBinding.runRoot);
  const loadedWorkload = await loadTrainingWorkloadCapsule(workloadBinding.path);
  if (loadedWorkload.workload.seed !== args.seed
    || loadedWorkload.workload.datasetPath !== policy.dataset.path
    || loadedWorkload.workloadSha256 !== workloadBinding.sha256) {
    throw new Error(`Writer v2 seed ${args.seed} workload contract mismatch.`);
  }
  const result = await runLoraPipeline({
    loadedWorkload,
    runRoot: path.join(workloadBinding.runRoot, 'sft'),
  });
  const exported = validateResult(result, policy, workloadBinding);
  const core = {
    schema: 'doppler.wgsl-writer-training-status/v1',
    experimentId: policy.experimentId,
    seed: args.seed,
    policy: {
      path: args.policyPath,
      sha256: await sha256File(args.policyPath),
    },
    workload: {
      path: workloadBinding.path,
      sha256: workloadBinding.sha256,
    },
    dataset: policy.dataset,
    metrics: result.metrics,
    checkpoint: result.lastCheckpoint,
    export: {
      checkpointId: exported.checkpointId,
      manifestPath: exported.manifestPath,
      manifestSha256: await sha256File(exported.manifestPath),
      weightsPath: exported.weightsPath,
      weightsSha256: exported.weightsSha256,
      weightsSize: exported.manifest.weightsSize,
      runtimeManifestPath: exported.runtimeManifestPath,
      exportPath: exported.exportPath,
    },
    gammaReceipt: exported.manifest.metadata.receipts[0],
    decision: 'training_complete',
    capabilityEvidence: false,
    selectionAuthority: false,
    confirmationAuthority: false,
    promotionAuthority: false,
    claimBoundary: 'Training completion establishes exact row consumption, optimizer execution, and adapter identity for one frozen writer-v2 seed. Capability requires disjoint semantic evaluation.',
  };
  return { ...core, receiptHash: sha256Value(core) };
}

async function writeStatus(runRoot, value) {
  const statusPath = path.join(runRoot, 'training-status.json');
  await fs.mkdir(path.dirname(statusPath), { recursive: true });
  await fs.writeFile(statusPath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
  return statusPath;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const policy = await readJson(args.policyPath);
  const workloadBinding = policy.workloads?.find((entry) => entry.seed === args.seed);
  if (!workloadBinding) throw new Error(`Writer v2 seed is not frozen: ${args.seed}`);
  try {
    const status = await runWgslWriterV2Training(args);
    const statusPath = await writeStatus(workloadBinding.runRoot, status);
    process.stdout.write(`${JSON.stringify({ ok: true, statusPath, status }, null, 2)}\n`);
  } catch (error) {
    const blocked = {
      schema: 'doppler.wgsl-writer-training-status/v1',
      experimentId: policy.experimentId,
      seed: args.seed,
      decision: 'blocked',
      error: error?.message || String(error),
      capabilityEvidence: false,
      selectionAuthority: false,
      confirmationAuthority: false,
      promotionAuthority: false,
      claimBoundary: 'A blocked training attempt is not optimizer or capability evidence.',
    };
    const statusPath = await writeStatus(workloadBinding.runRoot, {
      ...blocked,
      receiptHash: sha256Value(blocked),
    });
    console.error(JSON.stringify({ ok: false, statusPath, status: blocked }, null, 2));
    process.exitCode = 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
