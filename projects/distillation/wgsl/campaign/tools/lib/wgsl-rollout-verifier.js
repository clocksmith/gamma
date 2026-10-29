import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';

import {
  applyWgslRepairResponse,
  buildTrainingRolloutGroup,
  buildWgslRewardVector,
  deriveDpoPreferencePairs,
  deriveReferenceAnchoredDpoPairs,
  hashVerifierGuidedArtifact,
  selectRejectionSamples,
  validateVerifierGuidedArtifact,
} from '../../src/experimental/training/wgsl-repair.js';
import { sha256Hex } from '../../src/utils/sha256.js';
import { createWgslBrowserVerifier } from './wgsl-browser-verifier.js';

function isObject(value) {
  return value != null && typeof value === 'object' && !Array.isArray(value);
}

function requireString(value, label) {
  const normalized = typeof value === 'string' ? value.trim() : '';
  if (!normalized) throw new Error(`${label} is required.`);
  return normalized;
}

function requireHash(value, label) {
  const normalized = requireString(value, label);
  if (!/^[a-f0-9]{64}$/.test(normalized)) {
    throw new Error(`${label} must be a SHA-256 digest.`);
  }
  return normalized;
}

function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`;
  if (isObject(value)) {
    return `{${Object.keys(value).sort().map((key) => (
      `${JSON.stringify(key)}:${stableJson(value[key])}`
    )).join(',')}}`;
  }
  return JSON.stringify(value);
}

export function parseJsonl(text, label = 'JSONL') {
  const rows = [];
  for (const [index, line] of String(text).split(/\r?\n/).entries()) {
    if (!line.trim()) continue;
    const row = JSON.parse(line);
    if (!isObject(row)) throw new Error(`${label}:${index + 1} must be an object.`);
    rows.push(row);
  }
  if (rows.length === 0) throw new Error(`${label} contains no rows.`);
  return rows;
}

function toJsonl(rows) {
  return `${rows.map((row) => JSON.stringify(row)).join('\n')}\n`;
}

function taskIdOf(task) {
  return requireString(task.taskId || task.id || task.rowId, 'task.taskId');
}

function sampleIdOf(sample, taskId, index) {
  return String(sample.sampleId || `${taskId}-sample-${index + 1}`);
}

function buildVerifierReport(input) {
  const artifact = {
    artifactType: 'training_verifier_report',
    schemaVersion: 1,
    workloadId: input.workloadId,
    reportId: `${input.sampleId}-verifier`,
    taskId: input.taskId,
    sampleId: input.sampleId,
    datasetHash: input.datasetHash,
    policyHash: input.policyHash,
    runtimeHash: input.runtimeHash,
    kernelHash: input.kernelHash,
    verifierBundleHash: input.verifierBundleHash,
    verifierRole: input.rolloutPurpose,
    rawChecks: input.rawChecks,
    rewardVector: input.rewardVector,
    claimBoundary: input.rolloutPurpose === 'training'
      ? 'Training reward only; not a promotion evaluation.'
      : 'Evaluation verifier report only; not optimizer input or promotion evidence.',
  };
  return validateVerifierGuidedArtifact(artifact);
}

export async function verifyRawWgslRollouts(options) {
  const policy = options.policy;
  const tasks = options.tasks;
  const rawGroups = options.rawGroups;
  if (!isObject(policy?.verifier) || !Array.isArray(tasks) || !Array.isArray(rawGroups)) {
    throw new Error('verifyRawWgslRollouts requires policy, tasks, and rawGroups.');
  }
  const taskMap = new Map(tasks.map((task) => [taskIdOf(task), task]));
  const datasetHash = requireHash(options.datasetHash, 'datasetHash');
  const policyHash = requireHash(options.policyHash, 'policyHash');
  const referencePolicyHash = requireHash(options.referencePolicyHash, 'referencePolicyHash');
  const expectedGroupSize = Number.isInteger(options.expectedGroupSize)
    ? options.expectedGroupSize
    : policy.methods.rlvr.groupSize;
  if (expectedGroupSize < 2) {
    throw new Error('expectedGroupSize must be an integer >= 2.');
  }
  const rolloutPurpose = String(options.rolloutPurpose || 'training').trim().toLowerCase();
  if (!['training', 'evaluation'].includes(rolloutPurpose)) {
    throw new Error('rolloutPurpose must be training or evaluation.');
  }
  const verifierBundleHash = sha256Hex(stableJson(policy.verifier));
  const ownsVerifier = !options.verifier;
  const verifier = options.verifier || await createWgslBrowserVerifier(policy.verifier.browser);
  try {
    const candidates = [];
    for (const group of rawGroups) {
      const taskId = requireString(group.taskId, 'raw rollout group.taskId');
      const task = taskMap.get(taskId);
      if (!task) throw new Error(`Raw rollout references unknown task: ${taskId}`);
      if (!Array.isArray(group.samples) || group.samples.length !== expectedGroupSize) {
        throw new Error(
          `Raw rollout ${group.groupId || taskId} must contain ${expectedGroupSize} samples.`
        );
      }
      for (const [index, sample] of group.samples.entries()) {
        const sampleId = sampleIdOf(sample, taskId, index);
        const applied = applyWgslRepairResponse(task, sample.completion);
        candidates.push({
          task,
          group,
          sample,
          sampleId,
          applied,
        });
      }
    }
    const compileResults = await verifier.compile(candidates.map((candidate) => ({
      id: candidate.sampleId,
      code: candidate.applied.candidateSource,
    })));
    const compileById = new Map(compileResults.map((result) => [result.id, result]));
    const runtimeHash = sha256Hex(stableJson({
      deviceInfo: verifier.deviceInfo,
      browserArgs: verifier.browserArgs,
    }));
    const reports = [];
    const sampleById = new Map();
    for (const candidate of candidates) {
      const compile = compileById.get(candidate.sampleId);
      if (!compile) throw new Error(`Missing compile result for ${candidate.sampleId}.`);
      const exactReferenceMatch = candidate.sample.completion === candidate.task.span.reference;
      const rewardVector = buildWgslRewardVector({
        taskId: taskIdOf(candidate.task),
        sampleId: candidate.sampleId,
        verifierBundleHash,
        contractPass: candidate.applied.ok,
        policyPass: candidate.applied.violations.length === 0,
        compilePass: compile.passed,
        regressionPass: compile.passed,
        exactReferenceMatch,
        contractEvidence: { violations: candidate.applied.violations },
        policyEvidence: { violations: candidate.applied.violations },
        compileEvidence: compile,
        regressionEvidence: {
          mutationOperator: candidate.task.mutation?.operator || null,
          mutantCompileFailed: candidate.task.verification?.mutantCompileFailed === true,
          candidateCompilePassed: compile.passed,
        },
        referenceEvidence: {
          exactReferenceMatch,
          referenceSourceSha256: candidate.task.sourceSha256,
          candidateSourceSha256: candidate.applied.candidateSha256,
        },
        claimBoundary: rolloutPurpose === 'training'
          ? 'Training signal only; not a promotion evaluation.'
          : 'Evaluation metric only; not optimizer input or promotion evidence.',
      });
      const report = buildVerifierReport({
        workloadId: options.workloadId,
        taskId: taskIdOf(candidate.task),
        sampleId: candidate.sampleId,
        datasetHash,
        policyHash,
        runtimeHash,
        kernelHash: candidate.task.sourceSha256,
        verifierBundleHash,
        rolloutPurpose,
        rawChecks: [
          { id: 'response_contract', passed: candidate.applied.ok, evidence: candidate.applied.violations },
          { id: 'shader_module_compilation', passed: compile.passed, evidence: compile.messages },
          { id: 'mutation_regression', passed: compile.passed, evidence: candidate.task.mutation },
        ],
        rewardVector,
      });
      reports.push(report);
      sampleById.set(candidate.sampleId, {
        ...candidate.sample,
        sampleId: candidate.sampleId,
        rewardVector,
        verifierReportHash: hashVerifierGuidedArtifact(report),
      });
    }
    const groups = rawGroups.map((rawGroup) => {
      const taskId = requireString(rawGroup.taskId, 'raw rollout group.taskId');
      return buildTrainingRolloutGroup({
        workloadId: options.workloadId,
        groupId: requireString(rawGroup.groupId, 'raw rollout group.groupId'),
        taskId,
        datasetHash,
        policyHash,
        referencePolicyHash,
        verifierBundleHash,
        runtimeHash,
        rolloutPurpose,
        advantageEpsilon: policy.methods.rlvr.advantageEpsilon,
        sampling: rawGroup.sampling,
        samples: rawGroup.samples.map((sample, index) => {
          const sampleId = sampleIdOf(sample, taskId, index);
          return sampleById.get(sampleId);
        }),
        claimBoundary: rolloutPurpose === 'training'
          ? 'On-policy training signal only; not a promotion evaluation.'
          : 'Evaluation-only sampled compiler evidence; not optimizer input or promotion evidence.',
      });
    });
    const passingTasksAt1 = groups.filter((group) => (
      group.samples[0].rewardVector.reduction.scalarReward > 0
    )).length;
    const passingTasksAtK = groups.filter((group) => (
      group.samples.some((sample) => sample.rewardVector.reduction.scalarReward > 0)
    )).length;
    const exactReferenceSamples = reports.filter((report) => (
      report.rewardVector.components.some((component) => (
        component.id === 'exact_reference_match' && component.normalizedValue === 1
      ))
    )).length;
    return {
      groups,
      reports,
      receipt: {
        artifactType: 'wgsl_rollout_verification_manifest',
        schemaVersion: 1,
        workloadId: options.workloadId,
        datasetHash,
        policyHash,
        referencePolicyHash,
        verifierBundleHash,
        runtimeHash,
        rolloutPurpose,
        deviceInfo: verifier.deviceInfo,
        groupCount: groups.length,
        expectedGroupSize,
        sampleCount: reports.length,
        passingSamples: reports.filter((report) => (
          report.rewardVector.reduction.scalarReward > 0
        )).length,
        passingTasksAt1,
        passingTasksAtK,
        passAt1: passingTasksAt1 / groups.length,
        passAtK: passingTasksAtK / groups.length,
        exactReferenceSamples,
        blockedSamples: reports.filter((report) => (
          report.rewardVector.reduction.blocked === true
        )).length,
        groupHashes: groups.map(hashVerifierGuidedArtifact),
        reportHashes: reports.map(hashVerifierGuidedArtifact),
        claimBoundary: rolloutPurpose === 'training'
          ? 'Training verifier receipt only; not a capability claim.'
          : 'Evaluation-only compiler receipt; not optimizer input, semantic correctness, or promotion evidence.',
      },
    };
  } finally {
    if (ownsVerifier) await verifier.close();
  }
}

export async function writeVerifiedWgslRollouts(outputRoot, verified) {
  const root = resolve(outputRoot);
  const groupsDir = join(root, 'rollout-groups');
  const reportsDir = join(root, 'verifier-reports');
  await Promise.all([mkdir(groupsDir, { recursive: true }), mkdir(reportsDir, { recursive: true })]);
  for (const group of verified.groups) {
    await writeFile(
      join(groupsDir, `${group.groupId}.json`),
      `${JSON.stringify(group, null, 2)}\n`,
      'utf8'
    );
  }
  for (const report of verified.reports) {
    await writeFile(
      join(reportsDir, `${report.reportId}.json`),
      `${JSON.stringify(report, null, 2)}\n`,
      'utf8'
    );
  }
  await Promise.all([
    writeFile(join(root, 'rollout-groups.jsonl'), toJsonl(verified.groups), 'utf8'),
    writeFile(join(root, 'verifier-reports.jsonl'), toJsonl(verified.reports), 'utf8'),
    writeFile(
      join(root, 'verification-manifest.json'),
      `${JSON.stringify(verified.receipt, null, 2)}\n`,
      'utf8'
    ),
  ]);
  return root;
}

export function deriveWgslTrainingRows(groups, policy, tasks = null) {
  const rejectionRows = selectRejectionSamples(groups);
  const dpoRows = deriveDpoPreferencePairs(groups, {
    minimumRewardGap: policy.methods.dpo.minimumRewardGap,
  });
  const referenceAnchoredDpoRows = tasks
    ? deriveReferenceAnchoredDpoPairs(groups, tasks)
    : [];
  return {
    rejectionRows,
    dpoRows,
    referenceAnchoredDpoRows,
    receipt: {
      artifactType: 'wgsl_rollout_derived_dataset_manifest',
      schemaVersion: 1,
      groupCount: groups.length,
      rejectionRows: rejectionRows.length,
      dpoRows: dpoRows.length,
      referenceAnchoredDpoRows: referenceAnchoredDpoRows.length,
      rolloutGroupHashes: groups.map(hashVerifierGuidedArtifact),
      rejectionDatasetHash: sha256Hex(stableJson(rejectionRows)),
      dpoDatasetHash: sha256Hex(stableJson(dpoRows)),
      referenceAnchoredDpoDatasetHash: sha256Hex(stableJson(referenceAnchoredDpoRows)),
      claimBoundary: 'Derived training datasets only; no optimizer or capability claim.',
    },
  };
}

export async function writeDerivedWgslTrainingRows(outputRoot, derived) {
  const root = resolve(outputRoot);
  await mkdir(root, { recursive: true });
  await Promise.all([
    writeFile(join(root, 'rejection-sft.jsonl'), toJsonl(derived.rejectionRows), 'utf8'),
    writeFile(join(root, 'dpo-pairs.jsonl'), toJsonl(derived.dpoRows), 'utf8'),
    writeFile(
      join(root, 'reference-anchored-dpo-pairs.jsonl'),
      toJsonl(derived.referenceAnchoredDpoRows),
      'utf8'
    ),
    writeFile(
      join(root, 'derived-dataset-manifest.json'),
      `${JSON.stringify(derived.receipt, null, 2)}\n`,
      'utf8'
    ),
  ]);
  return root;
}

export async function readJsonlFile(path, label) {
  return parseJsonl(await readFile(resolve(path), 'utf8'), label || path);
}
