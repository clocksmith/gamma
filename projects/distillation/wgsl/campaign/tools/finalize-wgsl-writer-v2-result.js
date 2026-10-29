#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';

const EXPERIMENT_ID = 'doppler-wgsl-writer-v2';
const RESULT_DATE = '2026-07-14';
const ROOT = `reports/training/wgsl-writer/${EXPERIMENT_ID}`;
const POLICY_PATH = 'tools/policies/wgsl-writer-v2-training-policy.json';
const PARITY_POLICY_PATH = 'tools/policies/wgsl-writer-v2-parity-policy.json';
const RESULT_PATH = `docs/status/wgsl-writer-v2-result-${RESULT_DATE}.json`;
const INVALID_ATTEMPT_ROOT = `${ROOT}/attempts/checkpoint-selection-nonfinite-json-invalid`;
const BLOCKED_TRAINING_PATH = `${ROOT}/attempts/seed11-transformers-4.57.6-blocked/training-status.json`;

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(path.resolve(filePath), 'utf8'));
}

async function sha256File(filePath) {
  return createHash('sha256').update(await fs.readFile(path.resolve(filePath))).digest('hex');
}

async function fileIdentity(filePath) {
  const resolved = path.resolve(filePath);
  const stats = await fs.stat(resolved);
  return {
    path: path.relative(process.cwd(), resolved),
    sha256: await sha256File(resolved),
    bytes: stats.size,
  };
}

async function requireFileHash(filePath, expectedSha256, label) {
  const actual = await sha256File(filePath);
  if (actual !== expectedSha256) {
    throw new Error(`${label} SHA-256 mismatch: expected ${expectedSha256}, got ${actual}.`);
  }
}

function requireSemanticHash(value, label) {
  const core = { ...value };
  const expected = core.receiptHash;
  delete core.receiptHash;
  if (expected !== hashWgslSemanticEvidenceValue(core)) {
    throw new Error(`${label} internal receipt hash mismatch.`);
  }
}

function requireTrainingHash(value, label) {
  const core = { ...value };
  const expected = core.receiptHash;
  delete core.receiptHash;
  const actual = createHash('sha256').update(JSON.stringify(core)).digest('hex');
  if (expected !== actual) throw new Error(`${label} internal receipt hash mismatch.`);
}

async function requireAbsent(filePath) {
  try {
    await fs.access(path.resolve(filePath));
  } catch (error) {
    if (error?.code === 'ENOENT') return;
    throw error;
  }
  throw new Error(`WGSL writer v2 result is already sealed: ${filePath}`);
}

async function loadSemanticReceipt(filePath, label) {
  const receipt = await readJson(filePath);
  requireSemanticHash(receipt, label);
  return receipt;
}

async function loadEvaluationBatch(role, policySha256) {
  const batchPath = `${ROOT}/evaluation/${role}/evaluation.json`;
  const batch = await loadSemanticReceipt(batchPath, `${role} evaluation batch`);
  if (batch.decision !== 'evaluation_complete' || batch.policy?.sha256 !== policySha256) {
    throw new Error(`${role} evaluation batch is not complete under the frozen policy.`);
  }
  for (const candidate of batch.candidates) {
    await requireFileHash(candidate.path, candidate.sha256, `${role} seed ${candidate.seed}`);
    const receipt = await loadSemanticReceipt(
      candidate.path,
      `${role} seed ${candidate.seed} semantic receipt`
    );
    if (receipt.candidate?.seed !== candidate.seed
      || receipt.receiptHash !== candidate.receiptHash) {
      throw new Error(`${role} seed ${candidate.seed} binding mismatch.`);
    }
  }
  await requireFileHash(batch.reference.path, batch.reference.sha256, `${role} PEFT reference`);
  return { path: batchPath, batch };
}

async function loadTrainingStatuses(policy) {
  const statuses = [];
  for (const workload of policy.workloads) {
    const statusPath = `${workload.runRoot}/training-status.json`;
    const status = await readJson(statusPath);
    requireTrainingHash(status, `seed ${workload.seed} training status`);
    if (status.decision !== 'training_complete'
      || status.seed !== workload.seed
      || status.metrics?.steps !== policy.dataset.rows
      || status.metrics?.distinctRowsVisited !== policy.dataset.rows) {
      throw new Error(`Seed ${workload.seed} training is not complete under the frozen policy.`);
    }
    await Promise.all([
      requireFileHash(status.export.manifestPath, status.export.manifestSha256,
        `seed ${workload.seed} Doppler manifest`),
      requireFileHash(status.export.weightsPath, status.export.weightsSha256,
        `seed ${workload.seed} Doppler weights`),
    ]);
    const peftWeightsPath = path.join(
      status.gammaReceipt.adapterPath,
      'adapter_model.safetensors'
    );
    statuses.push({
      statusPath,
      status,
      peftWeights: await fileIdentity(peftWeightsPath),
    });
  }
  return statuses;
}

function evaluationSummary(entry) {
  return {
    seed: entry.seed,
    semanticPasses: entry.summary.semanticPasses,
    taskCount: entry.summary.taskCount,
    semanticPassRate: entry.summary.semanticPassRate,
    compilePasses: entry.summary.compilePasses,
    compilePassRate: entry.summary.compilePassRate,
    responseContractPasses: entry.summary.responseContractPasses,
    responseContractPassRate: entry.summary.responseContractPassRate,
    policyViolationTasks: entry.summary.policyViolationTasks,
    meanShaderCharacterCount: entry.summary.meanShaderCharacterCount,
  };
}

async function mechanicsAmendment(canonicalSelectionBatch) {
  const invalidBatchPath = `${INVALID_ATTEMPT_ROOT}/evaluation.json`;
  const invalidBatch = await loadSemanticReceipt(
    invalidBatchPath,
    'serialization-invalid checkpoint-selection batch'
  );
  const invalidSummaries = invalidBatch.candidates.map(evaluationSummary);
  const canonicalSummaries = canonicalSelectionBatch.candidates.map(evaluationSummary);
  if (JSON.stringify(invalidSummaries) !== JSON.stringify(canonicalSummaries)) {
    throw new Error('Checkpoint-selection mechanics repair changed candidate outcomes.');
  }
  const archivedFiles = [];
  for (const name of [
    'evaluation.json',
    'seed11.semantic.json',
    'seed29.semantic.json',
    'seed47.semantic.json',
  ]) {
    archivedFiles.push(await fileIdentity(`${INVALID_ATTEMPT_ROOT}/${name}`));
  }
  return {
    status: 'repaired_without_model_resubmission',
    failure: 'nonfinite_numeric_error_hashed_as_sentinel_but_serialized_as_null',
    discoveryPoint: 'frozen_seed_ranker_internal_hash_validation',
    modelSubmissionReused: true,
    semanticVerifierRerun: true,
    candidateOutcomesChanged: false,
    exactReference: canonicalSelectionBatch.reference,
    archivedFiles,
  };
}

export async function finalizeWgslWriterV2Result(outputPath = RESULT_PATH) {
  await requireAbsent(outputPath);
  const [policy, parityPolicy] = await Promise.all([
    readJson(POLICY_PATH),
    readJson(PARITY_POLICY_PATH),
  ]);
  const policySha256 = await sha256File(POLICY_PATH);
  if (policy.experimentId !== EXPERIMENT_ID
    || parityPolicy.experimentId !== EXPERIMENT_ID
    || parityPolicy.predecessor.trainingPolicy.sha256 !== policySha256) {
    throw new Error('WGSL writer v2 finalization policy mismatch.');
  }
  const statuses = await loadTrainingStatuses(policy);
  const blockedTraining = await readJson(BLOCKED_TRAINING_PATH);
  requireTrainingHash(blockedTraining, 'dependency-blocked seed 11 training attempt');
  if (blockedTraining.decision !== 'blocked' || blockedTraining.capabilityEvidence !== false) {
    throw new Error('Dependency-blocked seed 11 attempt was not preserved fail-closed.');
  }
  const [calibration, checkpointSelection, seedConfirmation] = await Promise.all([
    loadEvaluationBatch('calibration', policySha256),
    loadEvaluationBatch('checkpoint-selection', policySha256),
    loadEvaluationBatch('seed-confirmation', policySha256),
  ]);
  const selectionPath = `${ROOT}/evaluation/selection/selected-seed.json`;
  const confirmationPath = `${ROOT}/evaluation/confirmation.json`;
  const parityPath = `${ROOT}/evaluation/parity/parity.json`;
  const [selection, confirmation, parity] = await Promise.all([
    loadSemanticReceipt(selectionPath, 'writer seed selection'),
    loadSemanticReceipt(confirmationPath, 'writer seed confirmation'),
    loadSemanticReceipt(parityPath, 'writer selected-adapter parity'),
  ]);
  if (selection.decision !== 'seed_selected'
    || confirmation.decision !== 'seed_confirmation_passed'
    || parity.decision !== 'selected_adapter_parity_passed'
    || confirmation.selectedAdapter?.seed !== selection.selected?.seed
    || parity.selection?.selectedSeed !== selection.selected?.seed) {
    throw new Error('WGSL writer v2 terminal gate chain is incomplete.');
  }
  const amendment = await mechanicsAmendment(checkpointSelection.batch);
  const core = {
    schema: 'doppler.wgsl-writer-v2-result/v1',
    experimentId: EXPERIMENT_ID,
    resultDate: RESULT_DATE,
    scope: {
      capability: 'complete_1d_elementwise_f32_wgsl_from_specification_and_interface_contract',
      generalWgslWriter: false,
      naturalLanguageToArbitraryShader: false,
      productCliAuthorized: false,
    },
    policies: {
      training: { path: POLICY_PATH, sha256: policySha256 },
      parity: { path: PARITY_POLICY_PATH, sha256: await sha256File(PARITY_POLICY_PATH) },
      corpus: policy.admission.corpusPolicy,
    },
    sourceModel: {
      id: policy.model.modelId,
      revision: policy.model.revision,
      transformersConfigSha256: parityPolicy.sourceModel.configSha256,
      tokenizerSha256: parityPolicy.sourceModel.tokenizerSha256,
      dopplerBaseArtifact: parityPolicy.dopplerBaseArtifact,
    },
    executorQualification: {
      blockedAttempt: {
        receipt: await fileIdentity(BLOCKED_TRAINING_PATH),
        receiptHash: blockedTraining.receiptHash,
        decision: blockedTraining.decision,
        error: blockedTraining.error,
        capabilityEvidence: false,
      },
      admittedRuntime: statuses[0].status.gammaReceipt.runtime,
      dependencyFailureReusedAsTrainingLineage: false,
    },
    training: {
      rowsPerSeed: policy.dataset.rows,
      semanticFamilies: policy.dataset.semanticFamilies,
      rowConsumption: policy.dataset.rowConsumption,
      seeds: statuses.map(({ statusPath, status, peftWeights }) => ({
        seed: status.seed,
        status: {
          path: statusPath,
          sha256: null,
          receiptHash: status.receiptHash,
        },
        steps: status.metrics.steps,
        distinctRowsVisited: status.metrics.distinctRowsVisited,
        finalLoss: status.metrics.loss,
        meanLoss: status.metrics.meanLoss,
        rowOrderSha256: status.metrics.rowOrderSha256,
        peft: {
          treeSha256: status.gammaReceipt.policyHash,
          weights: peftWeights,
        },
        dopplerExport: {
          manifest: {
            path: path.relative(process.cwd(), status.export.manifestPath),
            sha256: status.export.manifestSha256,
          },
          weights: {
            path: path.relative(process.cwd(), status.export.weightsPath),
            sha256: status.export.weightsSha256,
            bytes: status.export.weightsSize,
          },
        },
      })),
    },
    evaluation: {
      calibration: {
        receipt: await fileIdentity(calibration.path),
        selectionAuthority: false,
        candidates: calibration.batch.candidates.map(evaluationSummary),
      },
      checkpointSelection: {
        receipt: await fileIdentity(checkpointSelection.path),
        metric: selection.metric,
        tieBreakers: selection.tieBreakers,
        candidates: checkpointSelection.batch.candidates.map(evaluationSummary),
        selectedSeed: selection.selected.seed,
        selectionReceipt: await fileIdentity(selectionPath),
      },
      seedConfirmation: {
        receipt: await fileIdentity(seedConfirmation.path),
        candidates: seedConfirmation.batch.candidates.map(evaluationSummary),
        thresholds: confirmation.thresholds,
        result: confirmation.result,
        confirmationReceipt: await fileIdentity(confirmationPath),
      },
    },
    parity: {
      receipt: await fileIdentity(parityPath),
      selectedSeed: parity.selection.selectedSeed,
      identities: parity.identities,
      base: parity.base,
      adapter: parity.adapter,
      decision: parity.decision,
    },
    mechanicsAmendment: amendment,
    artifactAvailability: {
      adapterWeightsStoredInGit: false,
      adapterWeightsAvailableOnThisMachine: true,
      immutableExternalUrls: [],
      preservationRequiredBeforeMachineRetirement: true,
    },
    externalPromotion: {
      populationMaterialized: false,
      externalCustodianAssigned: false,
      oneUseSubmissionPerformed: false,
      passed: false,
    },
    decision: 'seed_confirmed_and_doppler_parity_passed_external_promotion_blocked',
    capabilityEvidence: true,
    seedConfirmationSatisfied: true,
    dopplerParitySatisfied: true,
    promotionAuthority: false,
    generalWgslWriterClaim: false,
    productizationAllowed: false,
    claimBoundary: policy.claimBoundary,
  };
  for (const seed of core.training.seeds) {
    seed.status.sha256 = await sha256File(seed.status.path);
  }
  const receipt = { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
  await fs.mkdir(path.dirname(path.resolve(outputPath)), { recursive: true });
  await fs.writeFile(path.resolve(outputPath), `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return { ok: true, outputPath, receipt };
}

async function main() {
  process.stdout.write(`${JSON.stringify(await finalizeWgslWriterV2Result(), null, 2)}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
