#!/usr/bin/env node

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import { runLoraPipeline } from '../src/experimental/training/lora-pipeline.js';
import {
  buildTrainingPolicyCheckpoint,
  buildTrainingPolicyUpdate,
} from '../src/experimental/training/policy-artifacts.js';
import { hashVerifierGuidedArtifact } from '../src/experimental/training/wgsl-repair.js';
import { loadTrainingWorkloadCapsule } from '../src/experimental/training/workloads.js';
import { sha256BytesHex, sha256Hex } from '../src/utils/sha256.js';
import {
  deriveWgslTrainingRows,
  readJsonlFile,
  verifyRawWgslRollouts,
  writeDerivedWgslTrainingRows,
  writeVerifiedWgslRollouts,
} from './lib/wgsl-rollout-verifier.js';
import { runGammaWgslRequest } from './trainers/gamma-wgsl-trainer.js';

const PROTOCOL = 'gamma_wgsl_trainer_json_v1';
const DEFAULT_POLICY = 'tools/policies/wgsl-repair-v9-policy.json';
const DEFAULT_WORKLOAD = 'src/experimental/training/workload-capsules/lora-doppler-wgsl-qwen35-9b-v9.json';
const DEFAULT_CORPUS_ROOT = 'reports/training/wgsl-repair/doppler-wgsl-repair-v9/corpus-v1';
const DEFAULT_RUN_ROOT = 'reports/training/wgsl-repair/doppler-wgsl-repair-v9/experiment';

function parseArgs(argv) {
  const parsed = {
    phase: 'preflight',
    policy: DEFAULT_POLICY,
    workload: DEFAULT_WORKLOAD,
    corpusRoot: DEFAULT_CORPUS_ROOT,
    runRoot: DEFAULT_RUN_ROOT,
    adapter: null,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    const value = argv[index + 1];
    if (!value) throw new Error(`${token} requires a value.`);
    if (token === '--phase') parsed.phase = value;
    else if (token === '--policy') parsed.policy = value;
    else if (token === '--workload') parsed.workload = value;
    else if (token === '--corpus-root') parsed.corpusRoot = value;
    else if (token === '--run-root') parsed.runRoot = value;
    else if (token === '--adapter') parsed.adapter = value;
    else throw new Error(`Unknown argument: ${token}`);
    index += 1;
  }
  return parsed;
}

async function readJson(path) {
  return JSON.parse(await readFile(resolve(path), 'utf8'));
}

async function hashFile(path) {
  return sha256BytesHex(new Uint8Array(await readFile(resolve(path))));
}

function modelRequest(policy) {
  const model = policy.models.primary;
  const localPath = String(process.env.GAMMA_WGSL_MODEL_PATH || '').trim();
  return {
    modelId: model.modelId,
    revision: model.revision || process.env.GAMMA_WGSL_MODEL_REVISION || 'main',
    ...(localPath ? { localPath } : {}),
  };
}

function commonTraining(policy) {
  return {
    dtype: policy.trainer.dtype,
    gradientCheckpointing: policy.trainer.gradientCheckpointing,
    maxLength: policy.trainer.sequenceLength,
  };
}

const ROLLOUT_TASK_FILES = Object.freeze({
  diagnostic: 'diagnostic.jsonl',
  'public-test': 'public-test.jsonl',
});

export function resolveWgslRolloutTaskPath(corpusRoot, rolloutMethod) {
  const taskSet = rolloutMethod?.taskSet ?? 'public-test';
  const filename = ROLLOUT_TASK_FILES[taskSet];
  if (!filename) {
    throw new Error('methods.rollout.taskSet must be diagnostic or public-test.');
  }
  return join(corpusRoot, filename);
}

export function buildWgslRolloutSampling(policy) {
  const {
    taskSet,
    taskSetRows,
    taskSetSha256,
    evaluationTaskSet,
    evaluationTaskSetRows,
    evaluationTaskSetSha256,
    ...sampling
  } = policy.methods.rollout;
  return {
    ...sampling,
    groupSize: policy.methods.rlvr.groupSize,
  };
}

export async function validateWgslRolloutTaskContract(corpusRoot, rolloutMethod) {
  const taskPath = resolveWgslRolloutTaskPath(corpusRoot, rolloutMethod);
  const expectedRows = rolloutMethod?.taskSetRows;
  const expectedHash = rolloutMethod?.taskSetSha256;
  if (expectedRows === undefined && expectedHash === undefined) return taskPath;
  if (!Number.isInteger(expectedRows) || expectedRows < 1) {
    throw new Error('methods.rollout.taskSetRows must be an integer >= 1.');
  }
  if (typeof expectedHash !== 'string' || !/^[a-f0-9]{64}$/.test(expectedHash)) {
    throw new Error('methods.rollout.taskSetSha256 must be a SHA-256 digest.');
  }
  const bytes = new Uint8Array(await readFile(taskPath));
  const actualHash = await sha256BytesHex(bytes);
  if (actualHash !== expectedHash) {
    throw new Error(`rollout task-set hash mismatch: expected ${expectedHash}, got ${actualHash}`);
  }
  const rows = new TextDecoder().decode(bytes).trim().split('\n').filter(Boolean).length;
  if (rows !== expectedRows) {
    throw new Error(`rollout task-set row mismatch: expected ${expectedRows}, got ${rows}`);
  }
  return taskPath;
}

async function writeStatus(runRoot, status) {
  const path = join(runRoot, 'experiment-status.json');
  await mkdir(runRoot, { recursive: true });
  await writeFile(path, `${JSON.stringify(status, null, 2)}\n`, 'utf8');
  return path;
}

async function runPreflight(context) {
  const outputRoot = join(context.runRoot, 'gamma', 'preflight');
  const request = {
    protocol: PROTOCOL,
    action: 'preflight',
    runId: `${context.policy.policyId}-preflight`,
    outputRoot,
    model: modelRequest(context.policy),
    training: commonTraining(context.policy),
  };
  const executed = await runGammaWgslRequest(request, {
    runRoot: outputRoot,
    prefix: 'primary',
  });
  const result = executed.response.result;
  const referencePolicyHash = sha256Hex(JSON.stringify({
    modelId: request.model.modelId,
    revision: request.model.revision,
    modelConfigSha256: result.modelConfigSha256,
  }));
  return {
    phase: 'preflight',
    response: executed.response,
    referencePolicyHash,
    receiptPaths: executed.paths,
  };
}

async function runSft(context) {
  const loadedWorkload = await loadTrainingWorkloadCapsule(context.workloadPath);
  const result = await runLoraPipeline({
    loadedWorkload,
    runRoot: join(context.runRoot, 'sft'),
  });
  const checkpoint = JSON.parse(await readFile(result.checkpointArtifacts[0].checkpointPath, 'utf8'));
  const gammaReceipt = checkpoint.receipts?.find((receipt) => receipt.protocol === PROTOCOL);
  if (!gammaReceipt?.adapterPath || !gammaReceipt?.policyHash) {
    throw new Error('SFT checkpoint is missing the Gamma adapter receipt.');
  }
  return {
    phase: 'sft',
    result,
    adapterPath: gammaReceipt.adapterPath,
    policyHash: gammaReceipt.policyHash,
    gammaReceipt,
  };
}

async function runRollout(context, adapterPath) {
  if (!adapterPath) throw new Error('rollout requires --adapter or an SFT result.');
  const taskPath = await validateWgslRolloutTaskContract(
    context.corpusRoot,
    context.policy.methods.rollout
  );
  const outputRoot = join(context.runRoot, 'gamma', 'rollout');
  const request = {
    protocol: PROTOCOL,
    action: 'rollout',
    runId: `${context.policy.policyId}-rollout`,
    outputRoot,
    model: modelRequest(context.policy),
    adapterPath: resolve(adapterPath),
    datasetPath: taskPath,
    sampling: buildWgslRolloutSampling(context.policy),
    training: commonTraining(context.policy),
  };
  const executed = await runGammaWgslRequest(request, { runRoot: outputRoot, prefix: 'rollout' });
  return {
    phase: 'rollout',
    response: executed.response,
    adapterPath: resolve(adapterPath),
    policyHash: executed.response.result.policyHash,
    rawRolloutPath: executed.response.result.rolloutPath,
    receiptPaths: executed.paths,
  };
}

async function runBaseRollout(context, referencePolicyHash) {
  if (!referencePolicyHash) throw new Error('base rollout requires a preflight policy hash.');
  const taskPath = await validateWgslRolloutTaskContract(
    context.corpusRoot,
    context.policy.methods.rollout
  );
  const outputRoot = join(context.runRoot, 'gamma', 'base-rollout');
  const request = {
    protocol: PROTOCOL,
    action: 'rollout',
    runId: `${context.policy.policyId}-base-rollout`,
    outputRoot,
    model: modelRequest(context.policy),
    policyMode: 'base',
    policyHash: referencePolicyHash,
    datasetPath: taskPath,
    sampling: buildWgslRolloutSampling(context.policy),
    training: commonTraining(context.policy),
  };
  const executed = await runGammaWgslRequest(request, {
    runRoot: outputRoot,
    prefix: 'base-rollout',
  });
  return {
    phase: 'base-rollout',
    response: executed.response,
    adapterPath: null,
    policyHash: executed.response.result.policyHash,
    rawRolloutPath: executed.response.result.rolloutPath,
    receiptPaths: executed.paths,
  };
}

async function runVerify(context, rollout, referencePolicyHash, options = {}) {
  if (!rollout?.rawRolloutPath || !rollout?.policyHash || !referencePolicyHash) {
    throw new Error('verify requires rollout and reference-policy receipts.');
  }
  const taskPath = await validateWgslRolloutTaskContract(
    context.corpusRoot,
    context.policy.methods.rollout
  );
  const [tasks, rawGroups, datasetHash] = await Promise.all([
    readJsonlFile(taskPath, 'WGSL rollout tasks'),
    readJsonlFile(rollout.rawRolloutPath, 'raw WGSL rollouts'),
    hashFile(taskPath),
  ]);
  const verified = await verifyRawWgslRollouts({
    policy: context.policy,
    tasks,
    rawGroups,
    workloadId: options.workloadId || `${context.policy.policyId}-rlvr`,
    datasetHash,
    policyHash: rollout.policyHash,
    referencePolicyHash,
    expectedGroupSize: context.policy.methods.rlvr.groupSize,
  });
  const outputRoot = await writeVerifiedWgslRollouts(
    join(context.runRoot, options.outputDir || 'verified-rollouts'),
    verified
  );
  return {
    phase: options.phase || 'verify',
    outputRoot,
    groupsPath: join(outputRoot, 'rollout-groups.jsonl'),
    receipt: verified.receipt,
  };
}

async function runDerive(context, groupsPath) {
  if (!groupsPath) throw new Error('derive requires verified rollout groups.');
  const taskPath = await validateWgslRolloutTaskContract(
    context.corpusRoot,
    context.policy.methods.rollout
  );
  const [groups, tasks] = await Promise.all([
    readJsonlFile(groupsPath, 'verified WGSL rollout groups'),
    readJsonlFile(taskPath, 'WGSL rollout tasks'),
  ]);
  const derived = deriveWgslTrainingRows(groups, context.policy, tasks);
  const outputRoot = await writeDerivedWgslTrainingRows(
    join(context.runRoot, 'derived-training'),
    derived
  );
  return {
    phase: 'derive',
    outputRoot,
    rejectionPath: join(outputRoot, 'rejection-sft.jsonl'),
    dpoPath: join(outputRoot, 'dpo-pairs.jsonl'),
    referenceAnchoredDpoPath: join(outputRoot, 'reference-anchored-dpo-pairs.jsonl'),
    receipt: derived.receipt,
  };
}

function optimizerTraining(policy, method) {
  return {
    ...commonTraining(policy),
    ...method.training,
    seed: policy.trainer.seeds[0],
  };
}

export function summarizeGrpoLearningSignal(groups) {
  if (!Array.isArray(groups) || groups.length === 0) {
    throw new Error('GRPO signal analysis requires rollout groups.');
  }
  let sampleCount = 0;
  let nonzeroAdvantages = 0;
  let varyingGroups = 0;
  let constructiveVaryingGroups = 0;
  let exactOnlyVaryingGroups = 0;
  let otherVaryingGroups = 0;
  let unclassifiedVaryingGroups = 0;
  for (const group of groups) {
    if (!Array.isArray(group?.samples) || group.samples.length < 2) {
      throw new Error('GRPO signal analysis requires at least two samples per group.');
    }
    const groupNonzero = group.samples.filter((sample) => (
      Number.isFinite(sample?.advantage) && Math.abs(sample.advantage) > 0
    )).length;
    sampleCount += group.samples.length;
    nonzeroAdvantages += groupNonzero;
    if (groupNonzero > 0) {
      varyingGroups += 1;
      const classified = group.samples.every((sample) => (
        sample?.rewardVector?.reduction
        && Array.isArray(sample.rewardVector.components)
      ));
      if (!classified) {
        unclassifiedVaryingGroups += 1;
        continue;
      }
      const componentValue = (sample, id) => sample.rewardVector.components.find(
        (component) => component.id === id
      )?.normalizedValue;
      const constructiveSignatures = new Set(group.samples.map((sample) => JSON.stringify([
        sample.rewardVector.reduction.blocked === true,
        componentValue(sample, 'contract_pass'),
        componentValue(sample, 'policy_pass'),
        componentValue(sample, 'compile_pass'),
        componentValue(sample, 'regression_pass'),
      ])));
      const exactValues = new Set(group.samples.map((sample) => (
        componentValue(sample, 'exact_reference_match')
      )));
      if (constructiveSignatures.size > 1) constructiveVaryingGroups += 1;
      else if (exactValues.size > 1) exactOnlyVaryingGroups += 1;
      else otherVaryingGroups += 1;
    }
  }
  return {
    groupCount: groups.length,
    sampleCount,
    varyingGroups,
    nonzeroAdvantages,
    hasLearningSignal: nonzeroAdvantages > 0,
    constructiveVaryingGroups,
    exactOnlyVaryingGroups,
    otherVaryingGroups,
    unclassifiedVaryingGroups,
    hasConstructiveLearningSignal: constructiveVaryingGroups > 0,
  };
}

async function runDpo(context, adapterPath, dpoPath) {
  if (!adapterPath || !dpoPath) throw new Error('dpo requires an SFT adapter and DPO pairs.');
  const method = context.policy.methods.dpo;
  const outputRoot = join(context.runRoot, 'gamma', 'dpo');
  const derivedManifest = await readJson(
    join(context.runRoot, 'derived-training', 'derived-dataset-manifest.json')
  );
  if (!Number.isInteger(derivedManifest.dpoRows) || derivedManifest.dpoRows < 0) {
    throw new Error('derived training manifest requires a non-negative integer dpoRows.');
  }
  if (derivedManifest.dpoRows === 0) {
    return {
      phase: 'dpo',
      status: 'skipped_no_preference_pairs',
      adapterPath: resolve(adapterPath),
      derivedManifest,
      claimBoundary: 'No verifier reward gap exists; no DPO optimizer update was run.',
    };
  }
  const request = {
    protocol: PROTOCOL,
    action: 'dpo',
    runId: `${context.policy.policyId}-dpo`,
    outputRoot,
    model: modelRequest(context.policy),
    adapterPath: resolve(adapterPath),
    datasetPath: resolve(dpoPath),
    training: {
      ...optimizerTraining(context.policy, method),
      beta: method.beta,
    },
  };
  const executed = await runGammaWgslRequest(request, { runRoot: outputRoot, prefix: 'dpo' });
  const result = executed.response.result;
  const update = buildTrainingPolicyUpdate({
    workloadId: request.runId,
    updateId: `${request.runId}-update`,
    inputPolicyHash: result.inputPolicyHash,
    outputPolicyHash: result.policyHash,
    parentRolloutHashes: derivedManifest.rolloutGroupHashes,
    objective: {
      id: 'dpo_v1',
      formula: '-logsigmoid(beta * ((policy_chosen-policy_rejected) - (reference_chosen-reference_rejected)))',
      beta: method.beta,
    },
    metrics: result.metrics,
    runtime: executed.response.runtime,
    receiptPaths: executed.paths,
    claimBoundary: 'DPO mechanics only; not a promotion evaluation.',
  });
  const updateHash = hashVerifierGuidedArtifact(update);
  const checkpoint = buildTrainingPolicyCheckpoint({
    workloadId: request.runId,
    checkpointId: `${request.runId}-checkpoint-${result.checkpointStep}`,
    policyHash: result.policyHash,
    datasetHash: await hashFile(dpoPath),
    parentArtifactHashes: [updateHash],
    adapterPath: result.adapterPath,
    checkpointStep: result.checkpointStep,
    metrics: result.metrics,
    claimBoundary: 'DPO checkpoint mechanics only; not a promotion candidate.',
  });
  await Promise.all([
    writeFile(join(outputRoot, 'training-policy-update.json'), `${JSON.stringify(update, null, 2)}\n`, 'utf8'),
    writeFile(join(outputRoot, 'training-policy-checkpoint.json'), `${JSON.stringify(checkpoint, null, 2)}\n`, 'utf8'),
  ]);
  return {
    phase: 'dpo',
    response: executed.response,
    receiptPaths: executed.paths,
    update,
    checkpoint,
  };
}

async function runGrpo(context, adapterPath, groupsPath) {
  if (!adapterPath || !groupsPath) throw new Error('grpo requires an SFT adapter and rollout groups.');
  const method = context.policy.methods.rlvr;
  const outputRoot = join(context.runRoot, 'gamma', 'grpo');
  const groups = await readJsonlFile(groupsPath, 'GRPO rollout groups');
  const signal = summarizeGrpoLearningSignal(groups);
  if (!signal.hasLearningSignal) {
    return {
      phase: 'grpo',
      status: 'skipped_zero_advantages',
      adapterPath: resolve(adapterPath),
      signal,
      zeroVariancePolicy: method.zeroVariancePolicy,
      claimBoundary: 'All verifier groups have zero variance; no GRPO optimizer update was run.',
    };
  }
  const request = {
    protocol: PROTOCOL,
    action: 'grpo_update',
    runId: `${context.policy.policyId}-grpo`,
    outputRoot,
    model: modelRequest(context.policy),
    adapterPath: resolve(adapterPath),
    datasetPath: resolve(groupsPath),
    training: {
      ...optimizerTraining(context.policy, method),
      clipLower: method.clipLower,
      clipUpper: method.clipUpper,
      klCoefficient: method.klCoefficient,
      updatesPerRolloutBatch: method.updatesPerRolloutBatch,
      maximumStalePolicyUpdates: method.maximumStalePolicyUpdates,
    },
  };
  const executed = await runGammaWgslRequest(request, { runRoot: outputRoot, prefix: 'grpo' });
  const result = executed.response.result;
  const parentRolloutHashes = groups.map(hashVerifierGuidedArtifact);
  const update = buildTrainingPolicyUpdate({
    workloadId: request.runId,
    updateId: `${request.runId}-update`,
    inputPolicyHash: result.inputPolicyHash,
    outputPolicyHash: result.policyHash,
    parentRolloutHashes,
    objective: {
      id: 'grpo_clipped_kl_v1',
      formula: '-mean(min(ratio*A, clip(ratio, 1-lower, 1+upper)*A) - beta*KL)',
      clipLower: method.clipLower,
      clipUpper: method.clipUpper,
      klCoefficient: method.klCoefficient,
      advantageFormula: method.advantageFormula,
      zeroVariancePolicy: method.zeroVariancePolicy,
      updatesPerRolloutBatch: method.updatesPerRolloutBatch,
      maximumStalePolicyUpdates: method.maximumStalePolicyUpdates,
    },
    metrics: {
      ...result.metrics,
      learningSignal: signal,
    },
    runtime: executed.response.runtime,
    receiptPaths: executed.paths,
    claimBoundary: 'GRPO RLVR mechanics only; not a promotion evaluation.',
  });
  const updateHash = hashVerifierGuidedArtifact(update);
  const checkpoint = buildTrainingPolicyCheckpoint({
    workloadId: request.runId,
    checkpointId: `${request.runId}-checkpoint-${result.checkpointStep}`,
    policyHash: result.policyHash,
    datasetHash: await hashFile(groupsPath),
    parentArtifactHashes: [updateHash],
    adapterPath: result.adapterPath,
    checkpointStep: result.checkpointStep,
    metrics: {
      ...result.metrics,
      learningSignal: signal,
    },
    claimBoundary: 'GRPO RLVR checkpoint mechanics only; not a promotion candidate.',
  });
  await Promise.all([
    writeFile(join(outputRoot, 'training-policy-update.json'), `${JSON.stringify(update, null, 2)}\n`, 'utf8'),
    writeFile(join(outputRoot, 'training-policy-checkpoint.json'), `${JSON.stringify(checkpoint, null, 2)}\n`, 'utf8'),
  ]);
  return {
    phase: 'grpo',
    response: executed.response,
    receiptPaths: executed.paths,
    signal,
    update,
    checkpoint,
  };
}

export async function runExperiment(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const context = {
    policy: await readJson(args.policy),
    policyPath: resolve(args.policy),
    workloadPath: resolve(args.workload),
    corpusRoot: resolve(args.corpusRoot),
    runRoot: resolve(args.runRoot),
  };
  await mkdir(context.runRoot, { recursive: true });
  const phases = [];
  let adapterPath = args.adapter ? resolve(args.adapter) : null;
  let referencePolicyHash = null;
  let rollout = null;
  let verified = null;
  let derived = null;
  const selected = args.phase;
  if (selected === 'preflight' || selected === 'baseline' || selected === 'all') {
    const result = await runPreflight(context);
    phases.push(result);
    referencePolicyHash = result.referencePolicyHash;
  }
  if (selected === 'baseline' || selected === 'all') {
    const baseRollout = await runBaseRollout(context, referencePolicyHash);
    phases.push(baseRollout);
    phases.push(await runVerify(context, baseRollout, referencePolicyHash, {
      phase: 'base-verify',
      workloadId: `${context.policy.policyId}-base-eval`,
      outputDir: 'verified-base-rollouts',
    }));
  }
  if (selected === 'sft' || selected === 'all') {
    const result = await runSft(context);
    phases.push(result);
    adapterPath = result.adapterPath;
  }
  if (selected === 'rollout' || selected === 'all') {
    rollout = await runRollout(context, adapterPath);
    phases.push(rollout);
  }
  if (selected === 'verify' || selected === 'all') {
    if (selected === 'verify') {
      throw new Error('Standalone verify uses tools/run-wgsl-repair-rollouts.js with explicit hashes.');
    }
    verified = await runVerify(context, rollout, referencePolicyHash);
    phases.push(verified);
  }
  if (selected === 'derive' || selected === 'all') {
    if (selected === 'derive') {
      throw new Error('Standalone derive uses tools/run-wgsl-repair-rollouts.js with an explicit group path.');
    }
    derived = await runDerive(context, verified.groupsPath);
    phases.push(derived);
  }
  if (selected === 'dpo' || selected === 'all') {
    if (selected === 'dpo') {
      derived = {
        dpoPath: join(context.runRoot, 'derived-training', 'dpo-pairs.jsonl'),
      };
    }
    phases.push(await runDpo(context, adapterPath, derived.dpoPath));
  }
  if (selected === 'grpo' || selected === 'all') {
    if (selected === 'grpo') {
      verified = {
        groupsPath: join(context.runRoot, 'verified-rollouts', 'rollout-groups.jsonl'),
      };
    }
    phases.push(await runGrpo(context, adapterPath, verified.groupsPath));
  }
  if (phases.length === 0) {
    throw new Error('--phase must be preflight, baseline, sft, rollout, verify, derive, dpo, grpo, or all.');
  }
  const status = {
    artifactType: 'wgsl_repair_experiment_status',
    schemaVersion: 1,
    policyId: context.policy.policyId,
    status: selected === 'all' ? 'mechanics_proven' : 'harness_ready',
    completedPhases: phases.map((phase) => phase.phase),
    phases,
    claimBoundary: 'Optimizer execution only; no sealed capability or promotion claim.',
  };
  const statusPath = await writeStatus(context.runRoot, status);
  return { ok: true, statusPath, status };
}

export async function main(argv = process.argv.slice(2)) {
  try {
    const result = await runExperiment(argv);
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    const args = parseArgs(argv);
    const runRoot = resolve(args.runRoot);
    const status = {
      artifactType: 'wgsl_repair_experiment_status',
      schemaVersion: 1,
      status: 'blocked',
      failedPhase: args.phase,
      error: error?.message || String(error),
      trainerResponse: error?.response || null,
      receiptPaths: error?.paths || null,
      claimBoundary: 'Blocked execution is not training or capability evidence.',
    };
    const statusPath = await writeStatus(runRoot, status);
    console.error(JSON.stringify({ ok: false, statusPath, status }, null, 2));
    process.exitCode = 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
