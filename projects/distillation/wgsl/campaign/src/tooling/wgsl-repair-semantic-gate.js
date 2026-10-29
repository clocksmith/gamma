import { isPlainObject } from '../formats/plain-object.js';
import { sha256Hex } from '../formats/sha256.js';
import { stableSortObject } from '../formats/stable-sort-object.js';

export const WGSL_REPAIR_SEMANTIC_READINESS_SCHEMA_ID =
  'doppler.wgsl-repair-semantic-readiness/v1';
export const WGSL_REPAIR_SEMANTIC_READINESS_V2_SCHEMA_ID =
  'doppler.wgsl-repair-semantic-readiness/v2';

const V13_POLICY_ID = 'doppler-wgsl-repair-v13-semantic-evaluation';
const V12_PORTABILITY_SCHEMA_ID =
  'doppler.wgsl-repair-v12-adapter-portability-status/v1';
const EXPECTED_EXTERNAL20_SEEDS = Object.freeze([11, 29, 47]);

function stableJson(value) {
  return JSON.stringify(stableSortObject(value));
}

function hashStableJson(value) {
  return sha256Hex(stableJson(value));
}

export function normalizeWgslSemanticEvidenceValue(value) {
  if (typeof value === 'number') {
    if (Number.isNaN(value)) return { nonFinite: 'nan' };
    if (value === Number.POSITIVE_INFINITY) return { nonFinite: 'positive_infinity' };
    if (value === Number.NEGATIVE_INFINITY) return { nonFinite: 'negative_infinity' };
    if (Object.is(value, -0)) return { finite: 'negative_zero' };
  }
  if (Array.isArray(value)) return value.map(normalizeWgslSemanticEvidenceValue);
  if (isPlainObject(value)) {
    return Object.fromEntries(Object.entries(value).map(([key, entry]) => (
      [key, normalizeWgslSemanticEvidenceValue(entry)]
    )));
  }
  return value;
}

export function hashWgslSemanticEvidenceValue(value) {
  return hashStableJson(normalizeWgslSemanticEvidenceValue(value));
}

function finiteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

function nonFiniteMatches(expected, actual) {
  if (Number.isNaN(expected)) return Number.isNaN(actual);
  if (expected === Number.POSITIVE_INFINITY) return actual === Number.POSITIVE_INFINITY;
  if (expected === Number.NEGATIVE_INFINITY) return actual === Number.NEGATIVE_INFINITY;
  return false;
}

export function evaluateNumericAgreement(expectedValues, actualValues, tolerance) {
  const expected = Array.from(expectedValues || []);
  const actual = Array.from(actualValues || []);
  const mode = tolerance?.mode;
  const absTolerance = Number(tolerance?.absTolerance);
  const relTolerance = Number(tolerance?.relTolerance);
  const mismatches = [];
  let maxAbsError = 0;
  let maxRelError = 0;
  if (expected.length !== actual.length) {
    return {
      pass: false,
      expectedElements: expected.length,
      actualElements: actual.length,
      mismatchCount: Math.max(expected.length, actual.length),
      maxAbsError: null,
      maxRelError: null,
      mismatches: [{ index: -1, reason: 'length_mismatch' }],
    };
  }
  if (!['exact', 'numeric'].includes(mode)) {
    throw new Error('WGSL semantic verifier: tolerance.mode must be exact or numeric.');
  }
  if (!finiteNumber(absTolerance) || absTolerance < 0 || !finiteNumber(relTolerance) || relTolerance < 0) {
    throw new Error('WGSL semantic verifier: tolerances must be finite non-negative numbers.');
  }
  for (let index = 0; index < expected.length; index += 1) {
    const reference = expected[index];
    const observed = actual[index];
    if (!finiteNumber(reference) || !finiteNumber(observed)) {
      if (!nonFiniteMatches(reference, observed)) {
        mismatches.push({ index, reason: 'nonfinite_mismatch', expected: reference, actual: observed });
      }
      continue;
    }
    const absError = Math.abs(observed - reference);
    const relError = absError / Math.max(Math.abs(reference), Number.MIN_VALUE);
    maxAbsError = Math.max(maxAbsError, absError);
    maxRelError = Math.max(maxRelError, relError);
    const pass = mode === 'exact'
      ? Object.is(observed, reference) || observed === reference
      : absError <= absTolerance + relTolerance * Math.abs(reference);
    if (!pass) {
      mismatches.push({
        index,
        reason: 'numeric_mismatch',
        expected: reference,
        actual: observed,
        absError,
        relError,
      });
    }
  }
  return {
    pass: mismatches.length === 0,
    expectedElements: expected.length,
    actualElements: actual.length,
    mismatchCount: mismatches.length,
    maxAbsError,
    maxRelError,
    mismatches: mismatches.slice(0, 16),
  };
}

function allTrue(value, keys) {
  return isPlainObject(value) && keys.every((key) => value[key] === true);
}

export function evaluateWgslSemanticTaskEvidence(policy, evidence) {
  if (!isPlainObject(policy) || !isPlainObject(evidence)) {
    throw new Error('WGSL semantic verifier: policy and evidence must be objects.');
  }
  const blockers = new Set();
  if (evidence.responseContractPass !== true) blockers.add('response_contract_violation');
  if (evidence.compilation?.status !== 'pass') blockers.add('compilation_failure');
  const variants = Array.isArray(evidence.variants) ? evidence.variants : [];
  const shapeClasses = new Set(variants.map((variant) => variant.shapeClass));
  const shapeIds = new Set(variants.map((variant) => variant.shapeId));
  const workgroupIds = new Set(variants.map((variant) => variant.workgroupId));
  const shapeContract = policy.taskContract.shapeVariation;
  if (shapeIds.size < shapeContract.minimumDistinctShapesPerTask) {
    blockers.add('shape_variant_failure');
  }
  for (const required of shapeContract.requiredClasses) {
    if (!shapeClasses.has(required)) blockers.add('shape_variant_failure');
  }
  if (workgroupIds.size < policy.taskContract.workgroupVariation.minimumSemanticallyValidVariantsPerTask) {
    blockers.add('workgroup_variant_failure');
  }
  const allowedMetamorphic = new Set(policy.taskContract.metamorphic.allowedRelations);
  const passedMetamorphic = new Set();
  const variantResults = [];
  for (const variant of variants) {
    if (variant.dispatch?.status !== 'pass' || variant.dispatch?.backend !== 'chromium_webgpu') {
      blockers.add('dispatch_failure');
    }
    const numeric = evaluateNumericAgreement(
      variant.oracle?.expected,
      variant.oracle?.actual,
      variant.oracle?.tolerance
    );
    const hashBindingPass = typeof variant.oracle?.inputSha256 === 'string'
      && variant.oracle.inputSha256 === hashWgslSemanticEvidenceValue(variant.oracle.inputs)
      && typeof variant.oracle?.expectedSha256 === 'string'
      && variant.oracle.expectedSha256
        === hashWgslSemanticEvidenceValue(Array.from(variant.oracle?.expected || []))
      && typeof variant.oracle?.actualSha256 === 'string'
      && variant.oracle.actualSha256
        === hashWgslSemanticEvidenceValue(Array.from(variant.oracle?.actual || []));
    if (!numeric.pass || !hashBindingPass) {
      const hasNonFinite = numeric.mismatches.some((entry) => entry.reason === 'nonfinite_mismatch');
      blockers.add(hasNonFinite ? 'nonfinite_mismatch' : 'cpu_oracle_mismatch');
    }
    const boundsPass = allTrue(variant.bufferBounds, [
      'prefixCanaryIntact',
      'suffixCanaryIntact',
      'readOnlyBuffersUnchanged',
      'outputPaddingUnchanged',
      'validationErrorsAbsent',
    ]);
    if (!boundsPass) {
      if (variant.bufferBounds?.prefixCanaryIntact !== true
        || variant.bufferBounds?.suffixCanaryIntact !== true) {
        blockers.add('buffer_canary_corruption');
      }
      if (variant.bufferBounds?.readOnlyBuffersUnchanged !== true) {
        blockers.add('read_only_buffer_mutation');
      }
      if (variant.bufferBounds?.outputPaddingUnchanged !== true) {
        blockers.add('output_padding_mutation');
      }
      if (variant.bufferBounds?.validationErrorsAbsent !== true) blockers.add('dispatch_failure');
    }
    for (const relation of variant.metamorphic || []) {
      if (allowedMetamorphic.has(relation.id) && relation.status === 'pass') {
        passedMetamorphic.add(relation.id);
      } else {
        blockers.add('metamorphic_failure');
      }
    }
    variantResults.push({
      shapeId: variant.shapeId,
      shapeClass: variant.shapeClass,
      workgroupId: variant.workgroupId,
      dispatchPass: variant.dispatch?.status === 'pass',
      numeric,
      hashBindingPass,
      boundsPass,
    });
  }
  if (passedMetamorphic.size < policy.taskContract.metamorphic.minimumApplicableRelationsPerTask) {
    blockers.add('metamorphic_failure');
  }
  const historicalRegressionResults = Array.isArray(evidence.historicalRegressionResults)
    ? evidence.historicalRegressionResults
    : [];
  if (evidence.historicalRegressionsPass !== true
    || historicalRegressionResults.length === 0
    || historicalRegressionResults.some((entry) => entry?.status !== 'pass')) {
    blockers.add('historical_regression');
  }
  const resultCore = {
    taskId: evidence.taskId || null,
    pass: blockers.size === 0,
    variants: variantResults,
    distinctShapeCount: shapeIds.size,
    distinctWorkgroupCount: workgroupIds.size,
    passedMetamorphicRelations: [...passedMetamorphic].sort(),
    blockers: [...blockers].sort(),
  };
  return { ...resultCore, resultHash: hashStableJson(resultCore) };
}

export function evaluateWgslSemanticReadiness(options = {}) {
  const policy = options.policy;
  if (!isPlainObject(policy) || policy.policyId !== V13_POLICY_ID) {
    throw new Error('WGSL semantic readiness: unsupported policy.');
  }
  const blockers = new Set(Array.isArray(policy.blockers) ? policy.blockers : []);
  if (options.predecessorVerified !== true) blockers.add('v12_predecessor_identity_verification_failed');
  if (options.preservationReceipt?.decision !== 'complete') {
    blockers.add('v12_adapter_external_preservation_incomplete');
  }
  const populationBlockerIds = {
    calibration: 'calibration',
    checkpointSelection: 'checkpoint_selection',
    seedConfirmation: 'seed_confirmation',
    promotion: 'promotion',
  };
  for (const [role, population] of Object.entries(policy.populations)) {
    if (role === 'overlapPolicy') continue;
    if (population.status !== 'frozen' || !population.manifestPath || !population.populationHash) {
      blockers.add(`semantic_${populationBlockerIds[role] || role}_population_unmaterialized`);
    }
  }
  if (policy.candidate.seedSelectionStatus !== 'selected'
    || !policy.candidate.adapterSha256
    || !policy.candidate.adapterPath) {
    blockers.add('external20_seed_checkpoint_not_selected');
  }
  if (!policy.candidate.trainerToDopplerParityReceipt) {
    blockers.add('trainer_to_doppler_adapter_parity_absent');
  }
  if (!policy.taskContract.cpuOracle.implementationRevision) {
    blockers.add('cpu_oracle_implementation_revision_absent');
  }
  if (!policy.taskContract.historicalRegressions.manifestPath
    || !policy.taskContract.historicalRegressions.manifestSha256) {
    blockers.add('historical_regression_manifest_absent');
  }
  const taskEvidence = Array.isArray(options.taskEvidence)
    ? options.taskEvidence.map((entry) => evaluateWgslSemanticTaskEvidence(policy, entry))
    : [];
  if (taskEvidence.length === 0) blockers.add('semantic_dispatch_evidence_absent');
  if (taskEvidence.some((entry) => !entry.pass)) blockers.add('semantic_task_failure');

  const executionPrerequisiteBlockers = [...blockers].filter(
    (blocker) => !['semantic_dispatch_evidence_absent', 'semantic_task_failure'].includes(blocker)
  );
  const semanticEvaluationAllowed = executionPrerequisiteBlockers.length === 0
    && policy.status !== 'frozen_requirements_populations_unmaterialized';
  const semanticClaimAllowed = semanticEvaluationAllowed
    && taskEvidence.length > 0
    && taskEvidence.every((entry) => entry.pass)
    && blockers.size === 0;
  const wgslDoctorAllowed = semanticClaimAllowed && policy.productization.wgslDoctorAllowed === true;
  const core = {
    schema: WGSL_REPAIR_SEMANTIC_READINESS_SCHEMA_ID,
    policyId: policy.policyId,
    policyStatus: policy.status,
    predecessorVerified: options.predecessorVerified === true,
    preservationDecision: options.preservationReceipt?.decision ?? null,
    candidate: policy.candidate,
    taskEvidence,
    admission: {
      semanticEvaluationAllowed,
      semanticClaimAllowed,
      wgslDoctorAllowed,
      autonomousShaderAuthorAllowed: false,
    },
    decision: wgslDoctorAllowed
      ? 'wgsl_doctor_allowed'
      : semanticClaimAllowed
        ? 'semantic_claim_allowed'
        : semanticEvaluationAllowed
          ? 'semantic_evaluation_allowed'
          : 'blocked',
    blockers: [...blockers].sort(),
  };
  return { ...core, receiptHash: hashStableJson(core) };
}

function populationReady(population, verified) {
  return population?.status === 'frozen'
    && typeof population.manifestPath === 'string'
    && population.manifestPath.length > 0
    && typeof population.populationHash === 'string'
    && population.populationHash.length === 64
    && verified === true;
}

function evaluateCandidateSelection(candidate, receipt, receiptVerified) {
  const pass = candidate?.seedSelectionStatus === 'selected'
    && EXPECTED_EXTERNAL20_SEEDS.includes(candidate.selectedSeed)
    && typeof candidate.adapterPath === 'string'
    && candidate.adapterPath.length > 0
    && typeof candidate.adapterSha256 === 'string'
    && candidate.adapterSha256.length === 64
    && typeof candidate.selectionReceiptPath === 'string'
    && candidate.selectionReceiptPath.length > 0
    && typeof candidate.selectionReceiptSha256 === 'string'
    && candidate.selectionReceiptSha256.length === 64
    && receiptVerified === true
    && receipt?.schema === 'doppler.wgsl-repair-v13-seed-selection/v1'
    && receipt?.experimentId === 'doppler-wgsl-repair-v13'
    && receipt?.decision === 'selected_for_seed_confirmation'
    && receipt?.selected?.lane === 'external20'
    && receipt?.selected?.seed === candidate.selectedSeed
    && receipt?.selected?.adapterPath === candidate.adapterPath
    && receipt?.selected?.adapterSha256 === candidate.adapterSha256
    && receipt?.seedConfirmationSatisfied === false
    && receipt?.promotionAuthority === false;
  return {
    receiptVerified: receiptVerified === true,
    decision: receipt?.decision ?? null,
    selectedSeed: receipt?.selected?.seed ?? null,
    pass,
  };
}

function evaluateAdapterPortability(receipt, receiptVerified) {
  const adapters = Array.isArray(receipt?.frozenParityGate?.adapters)
    ? receipt.frozenParityGate.adapters
    : [];
  const adapterPassBySeed = Object.fromEntries(EXPECTED_EXTERNAL20_SEEDS.map((seed) => {
    const adapter = adapters.find((entry) => entry?.seed === seed);
    return [String(seed), adapter?.pass === true];
  }));
  const pass = receiptVerified === true
    && receipt?.schema === V12_PORTABILITY_SCHEMA_ID
    && receipt?.experimentId === 'doppler-wgsl-repair-v12'
    && receipt?.lane === 'external20'
    && receipt?.preservation?.decision === 'complete'
    && receipt?.frozenParityGate?.decision === 'diagnostic_import_parity_passed'
    && receipt?.frozenParityGate?.base?.pass === true
    && EXPECTED_EXTERNAL20_SEEDS.every((seed) => adapterPassBySeed[String(seed)] === true)
    && receipt?.v13Admission?.trainerToDopplerParitySatisfied === true;
  return {
    receiptVerified: receiptVerified === true,
    schema: receipt?.schema ?? null,
    experimentId: receipt?.experimentId ?? null,
    lane: receipt?.lane ?? null,
    decision: receipt?.frozenParityGate?.decision ?? null,
    basePass: receipt?.frozenParityGate?.base?.pass === true,
    adapterPassBySeed,
    pass,
  };
}

function evaluateSeedConfirmation(state, receipt, receiptVerified, candidate, population) {
  if (!state) return null;
  const expectedDecision = state.status === 'passed'
    ? 'seed_confirmation_passed'
    : 'seed_confirmation_rejected';
  const pass = state.status === 'passed'
    && receiptVerified === true
    && receipt?.schema === 'doppler.wgsl-repair-v13-seed-confirmation-result/v1'
    && receipt?.experimentId === 'doppler-wgsl-repair-v13'
    && receipt?.decision === expectedDecision
    && receipt?.seedConfirmationSatisfied === true
    && receipt?.candidate?.seed === candidate?.selectedSeed
    && receipt?.candidate?.adapterWeightsSha256 === candidate?.adapterSha256
    && receipt?.population?.sha256 === state.populationHash
    && population?.populationHash === state.populationHash
    && receipt?.promotionAuthority === false
    && receipt?.wgslDoctorAllowed === false
    && receipt?.completeShaderWritingEstablished === false;
  return {
    receiptVerified: receiptVerified === true,
    status: state.status,
    decision: receipt?.decision ?? null,
    selectedSeed: receipt?.candidate?.seed ?? null,
    pass,
  };
}

function implementationReady(implementation, verification) {
  const taskManifestReady = typeof implementation?.taskManifestPath === 'string'
    && implementation.taskManifestPath.length > 0
    && typeof implementation.taskManifestSha256 === 'string'
    && implementation.taskManifestSha256.length === 64
    && verification?.taskManifest === true;
  const cpuOracleReady = typeof implementation?.cpuOracleRevision === 'string'
    && implementation.cpuOracleRevision.length > 0;
  const historicalRegressionsReady =
    typeof implementation?.historicalRegressionManifestPath === 'string'
    && implementation.historicalRegressionManifestPath.length > 0
    && typeof implementation.historicalRegressionManifestSha256 === 'string'
    && implementation.historicalRegressionManifestSha256.length === 64
    && verification?.historicalRegressionManifest === true;
  return { taskManifestReady, cpuOracleReady, historicalRegressionsReady };
}

export function evaluateWgslSemanticReadinessV2(options = {}) {
  const policy = options.policy;
  const state = options.evidenceState;
  if (!isPlainObject(policy) || policy.policyId !== V13_POLICY_ID) {
    throw new Error('WGSL semantic readiness v2: unsupported policy.');
  }
  if (!isPlainObject(state)
    || state.experimentId !== 'doppler-wgsl-repair-v13'
    || !isPlainObject(state.candidate)
    || !isPlainObject(state.populations)
    || !isPlainObject(state.implementation)) {
    throw new Error('WGSL semantic readiness v2: invalid evidence state.');
  }

  const blockers = new Set();
  if (options.policyVerified !== true) blockers.add('semantic_policy_identity_verification_failed');
  if (options.predecessorVerified !== true) blockers.add('v12_predecessor_identity_verification_failed');
  if (options.preservationReceipt?.decision !== 'complete') {
    blockers.add('v12_adapter_external_preservation_incomplete');
  }

  const adapterPortability = evaluateAdapterPortability(
    options.adapterPortabilityReceipt,
    options.adapterPortabilityReceiptVerified
  );
  if (!options.adapterPortabilityReceipt) {
    blockers.add('trainer_to_doppler_adapter_parity_absent');
  } else if (!adapterPortability.pass) {
    blockers.add('trainer_to_doppler_parity_failure');
  }

  const populationBlockerIds = {
    calibration: 'calibration',
    checkpointSelection: 'checkpoint_selection',
    seedConfirmation: 'seed_confirmation',
    promotion: 'promotion',
  };
  const populationReadiness = {};
  for (const [role, blockerId] of Object.entries(populationBlockerIds)) {
    const population = state.populations[role];
    const verified = options.populationVerification?.[role] === true;
    const ready = populationReady(population, verified);
    populationReadiness[role] = ready;
    if (!ready) {
      const suffix = population?.status === 'frozen'
        ? 'identity_verification_failed'
        : 'unmaterialized';
      blockers.add(`semantic_${blockerId}_population_${suffix}`);
    }
  }

  const candidateSelection = evaluateCandidateSelection(
    state.candidate,
    options.selectionReceipt,
    options.selectionReceiptVerified
  );
  const selectedCandidateReady = candidateSelection.pass;
  if (!selectedCandidateReady) blockers.add('external20_seed_checkpoint_not_selected');
  if (state.candidate?.seedSelectionStatus === 'selected'
    && adapterPortability.adapterPassBySeed[String(state.candidate.selectedSeed)] !== true) {
    blockers.add('trainer_to_doppler_parity_failure');
  }

  const seedConfirmation = evaluateSeedConfirmation(
    state.seedConfirmation,
    options.seedConfirmationReceipt,
    options.seedConfirmationReceiptVerified,
    state.candidate,
    state.populations.seedConfirmation
  );
  if (state.seedConfirmation && !seedConfirmation.pass) {
    blockers.add(state.seedConfirmation.status === 'failed'
      ? 'semantic_seed_confirmation_failed'
      : 'semantic_seed_confirmation_evidence_invalid');
  }

  const implementation = implementationReady(
    state.implementation,
    options.implementationVerification
  );
  if (!implementation.taskManifestReady) blockers.add('semantic_task_manifest_absent');
  if (!implementation.cpuOracleReady) blockers.add('cpu_oracle_implementation_revision_absent');
  if (!implementation.historicalRegressionsReady) {
    blockers.add('historical_regression_manifest_absent');
  }

  const taskEvidence = Array.isArray(options.taskEvidence)
    ? options.taskEvidence.map((entry) => evaluateWgslSemanticTaskEvidence(policy, entry))
    : [];
  if (taskEvidence.length === 0) blockers.add('semantic_dispatch_evidence_absent');
  if (taskEvidence.some((entry) => !entry.pass)) blockers.add('semantic_task_failure');

  const baseImplementationAllowed = options.policyVerified === true
    && options.predecessorVerified === true
    && options.preservationReceipt?.decision === 'complete'
    && adapterPortability.pass
    && implementation.taskManifestReady
    && implementation.cpuOracleReady
    && implementation.historicalRegressionsReady;
  const phaseAdmission = {
    calibrationAllowed: baseImplementationAllowed && populationReadiness.calibration,
    checkpointSelectionAllowed: baseImplementationAllowed
      && populationReadiness.calibration
      && populationReadiness.checkpointSelection,
    seedConfirmationAllowed: baseImplementationAllowed
      && selectedCandidateReady
      && populationReadiness.seedConfirmation,
    promotionEvaluationAllowed: baseImplementationAllowed
      && selectedCandidateReady
      && (state.seedConfirmation == null || seedConfirmation?.pass === true)
      && Object.values(populationReadiness).every(Boolean),
  };
  const semanticEvaluationAllowed = Object.values(phaseAdmission).some(Boolean);
  const semanticClaimAllowed = phaseAdmission.promotionEvaluationAllowed
    && taskEvidence.length > 0
    && taskEvidence.every((entry) => entry.pass)
    && blockers.size === 0;
  const wgslDoctorAllowed = semanticClaimAllowed && policy.productization.wgslDoctorAllowed === true;
  const core = {
    schema: WGSL_REPAIR_SEMANTIC_READINESS_V2_SCHEMA_ID,
    experimentId: state.experimentId,
    policyId: policy.policyId,
    policyStatus: policy.status,
    policyBinding: state.policy,
    predecessorVerified: options.predecessorVerified === true,
    preservationDecision: options.preservationReceipt?.decision ?? null,
    adapterPortabilityBinding: state.adapterPortability,
    adapterPortability,
    candidate: state.candidate,
    ...(state.candidate.seedSelectionStatus === 'selected' ? { candidateSelection } : {}),
    ...(seedConfirmation ? { seedConfirmation } : {}),
    populations: state.populations,
    implementation: state.implementation,
    taskEvidence,
    phaseAdmission,
    admission: {
      semanticEvaluationAllowed,
      semanticClaimAllowed,
      wgslDoctorAllowed,
      autonomousShaderAuthorAllowed: false,
    },
    decision: wgslDoctorAllowed
      ? 'wgsl_doctor_allowed'
      : semanticClaimAllowed
        ? 'semantic_claim_allowed'
        : semanticEvaluationAllowed
          ? 'semantic_evaluation_allowed'
          : 'blocked',
    declaredHistoricalBlockers: Array.isArray(policy.blockers) ? [...policy.blockers].sort() : [],
    blockers: [...blockers].sort(),
    claimBoundary: state.claimBoundary,
  };
  return { ...core, receiptHash: hashStableJson(core) };
}
