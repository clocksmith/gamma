#!/usr/bin/env node

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import { sha256BytesHex, sha256Hex } from '../src/utils/sha256.js';
import {
  readJsonlFile,
  verifyRawWgslRollouts,
  writeVerifiedWgslRollouts,
} from './lib/wgsl-rollout-verifier.js';
import { runGammaWgslRequest } from './trainers/gamma-wgsl-trainer.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-repair-v12-evaluation-policy.json';
const STRATA = Object.freeze(['short', 'long']);

function parseArgs(argv) {
  const args = { policy: DEFAULT_POLICY };
  for (let index = 0; index < argv.length; index += 2) {
    const token = argv[index];
    const value = argv[index + 1];
    if (!token?.startsWith('--') || !value) throw new Error(`${token} requires a value.`);
    args[token.slice(2)] = value;
  }
  for (const field of ['adapter', 'lane', 'seed', 'split', 'run-root']) {
    if (!args[field]) throw new Error(`--${field} is required.`);
  }
  return args;
}

function requireObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} must be an object.`);
  }
  return value;
}

function requireHash(value, label) {
  const normalized = String(value || '').trim();
  if (!/^[a-f0-9]{64}$/.test(normalized)) throw new Error(`${label} must be SHA-256.`);
  return normalized;
}

function modelRequest(policy) {
  const localPath = String(process.env.GAMMA_WGSL_MODEL_PATH || '').trim();
  return {
    modelId: policy.model.modelId,
    revision: policy.model.revision,
    ...(localPath ? { localPath } : {}),
  };
}

export function buildStratumRequest({ policy, entry, adapterPath, lane, seed, split, stratum, outputRoot }) {
  const sampling = requireObject(policy.sampling, 'policy.sampling');
  const stratumSeed = sampling.baseSeed + (stratum === 'long' ? sampling.longSeedOffset : 0);
  return {
    protocol: policy.trainer.protocol,
    action: 'rollout',
    runId: `${policy.policyId}-${lane}-seed${seed}-${split}-${stratum}`,
    outputRoot,
    model: modelRequest(policy),
    adapterPath,
    datasetPath: resolve(entry.datasetPath),
    sampling: {
      groupSize: sampling.groupSize,
      temperature: sampling.temperature,
      topP: sampling.topP,
      maxTokens: entry.maxTokens,
      seed: stratumSeed,
      maxTokensDerivation: {
        source: 'v12_external20_training_targets',
        maximumTargetTokensIncludingEos: entry.maximumTrainingTargetTokensIncludingEos,
        marginTokens: entry.marginTokens,
        holdoutOutcomesUsed: false,
      },
    },
    generation: {
      captureLogprobs: false,
    },
    training: {
      dtype: policy.trainer.dtype,
      gradientCheckpointing: policy.trainer.gradientCheckpointing,
      maxLength: policy.trainer.maxLength,
    },
  };
}

export function summarizeStrata(strata) {
  const receipts = Object.values(strata).map((entry) => entry.verification);
  const sum = (field) => receipts.reduce((total, receipt) => total + receipt[field], 0);
  const groupCount = sum('groupCount');
  const sampleCount = sum('sampleCount');
  const passingTasksAt1 = sum('passingTasksAt1');
  const passingTasksAtK = sum('passingTasksAtK');
  const passingSamples = sum('passingSamples');
  return {
    groupCount,
    sampleCount,
    passingSamples,
    samplePassRate: passingSamples / sampleCount,
    passingTasksAt1,
    passAt1: passingTasksAt1 / groupCount,
    passingTasksAtK,
    passAtK: passingTasksAtK / groupCount,
    exactReferenceSamples: sum('exactReferenceSamples'),
    blockedSamples: sum('blockedSamples'),
  };
}

async function readJson(path) {
  return JSON.parse(await readFile(resolve(path), 'utf8'));
}

async function fileSha256(path) {
  return sha256BytesHex(new Uint8Array(await readFile(path)));
}

async function validateDataset(entry, tasks) {
  if (tasks.length !== entry.rows) {
    throw new Error(`${entry.datasetPath} has ${tasks.length} rows; expected ${entry.rows}.`);
  }
  const actual = await fileSha256(resolve(entry.datasetPath));
  if (actual !== entry.datasetSha256) {
    throw new Error(`${entry.datasetPath} SHA-256 mismatch.`);
  }
}

function relativePath(path) {
  return relative(process.cwd(), path).replace(/\\/g, '/');
}

export async function runEvaluation(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const policy = await readJson(args.policy);
  const split = requireObject(policy.splits?.[args.split], `policy.splits.${args.split}`);
  const seed = Number(args.seed);
  if (!policy.selection.lanes.includes(args.lane)) throw new Error(`Unknown lane: ${args.lane}`);
  if (!policy.selection.seeds.includes(seed)) throw new Error(`Unknown seed: ${args.seed}`);
  const verifierPolicy = await readJson(policy.verifierPolicyPath);
  const runRoot = resolve(args['run-root']);
  const adapterPath = resolve(args.adapter);
  const strata = {};
  let policyHash = null;
  for (const stratum of STRATA) {
    const entry = requireObject(split[stratum], `${args.split}.${stratum}`);
    requireHash(entry.datasetSha256, `${args.split}.${stratum}.datasetSha256`);
    const tasks = await readJsonlFile(entry.datasetPath, `${args.split} ${stratum} tasks`);
    await validateDataset(entry, tasks);
    const outputRoot = join(runRoot, args.split, stratum, 'gamma', 'rollout');
    const request = buildStratumRequest({
      policy,
      entry,
      adapterPath,
      lane: args.lane,
      seed,
      split: args.split,
      stratum,
      outputRoot,
    });
    const executed = await runGammaWgslRequest(request, {
      runRoot: outputRoot,
      prefix: 'rollout',
    });
    const currentPolicyHash = requireHash(executed.response.result.policyHash, 'policyHash');
    if (policyHash && currentPolicyHash !== policyHash) {
      throw new Error('Short and long rollouts resolved different policy hashes.');
    }
    policyHash = currentPolicyHash;
    const rawPath = resolve(executed.response.result.rolloutPath);
    const rawGroups = await readJsonlFile(rawPath, `${args.split} ${stratum} rollouts`);
    const verified = await verifyRawWgslRollouts({
      policy: verifierPolicy,
      tasks,
      rawGroups,
      workloadId: request.runId,
      datasetHash: entry.datasetSha256,
      policyHash,
      referencePolicyHash: policy.referencePolicyHash,
      expectedGroupSize: policy.sampling.groupSize,
      rolloutPurpose: 'evaluation',
    });
    const verifiedRoot = join(runRoot, args.split, stratum, 'verified-rollouts');
    await writeVerifiedWgslRollouts(verifiedRoot, verified);
    const verificationPath = join(verifiedRoot, 'verification-manifest.json');
    strata[stratum] = {
      datasetPath: relativePath(resolve(entry.datasetPath)),
      datasetSha256: entry.datasetSha256,
      rows: entry.rows,
      maxTokens: entry.maxTokens,
      samplingSeed: request.sampling.seed,
      rolloutTokens: executed.response.result.metrics.rolloutTokens,
      resumedGroups: executed.response.result.metrics.resumedGroups,
      rawRolloutPath: relativePath(rawPath),
      rawRolloutSha256: await fileSha256(rawPath),
      rolloutResponsePath: relativePath(executed.paths.responsePath),
      rolloutResponseSha256: await fileSha256(executed.paths.responsePath),
      verifiedGroupsPath: relativePath(join(verifiedRoot, 'rollout-groups.jsonl')),
      verifiedGroupsSha256: await fileSha256(join(verifiedRoot, 'rollout-groups.jsonl')),
      verificationPath: relativePath(verificationPath),
      verificationSha256: await fileSha256(verificationPath),
      verification: verified.receipt,
    };
  }
  const verifierHashes = new Set(Object.values(strata).map((entry) => (
    `${entry.verification.verifierBundleHash}:${entry.verification.runtimeHash}`
  )));
  if (verifierHashes.size !== 1) throw new Error('Strata used different verifier runtimes.');
  const receipt = {
    artifactType: 'wgsl_stratified_evaluation',
    schemaVersion: 1,
    policyId: policy.policyId,
    lane: args.lane,
    seed,
    split: args.split,
    model: policy.model,
    policyHash,
    referencePolicyHash: policy.referencePolicyHash,
    adapterPath: relativePath(adapterPath),
    stratifiedDatasetHash: sha256Hex(JSON.stringify(STRATA.map((stratum) => ({
      id: stratum,
      sha256: strata[stratum].datasetSha256,
    })))),
    strata,
    overall: summarizeStrata(strata),
    selectionPolicy: policy.selection,
    claimBoundary: args.split === 'diagnostic'
      ? 'Diagnostic compiler-repair evidence for data-lane selection; not public or promotion evidence.'
      : 'Public compiler-repair evidence only; not semantic-kernel or promotion evidence.',
  };
  const receiptPath = join(runRoot, args.split, 'stratified-evaluation.json');
  await mkdir(dirname(receiptPath), { recursive: true });
  await writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return { ok: true, receiptPath, receipt };
}

export async function main(argv = process.argv.slice(2)) {
  console.log(JSON.stringify(await runEvaluation(argv), null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}
