import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import {
  evaluateNumericAgreement,
  evaluateWgslSemanticReadiness,
  evaluateWgslSemanticReadinessV2,
  evaluateWgslSemanticTaskEvidence,
  hashWgslSemanticEvidenceValue,
} from '../../src/tooling/wgsl-repair-semantic-gate.js';

const policy = JSON.parse(readFileSync('tools/policies/wgsl-repair-v13-semantic-policy.json', 'utf8'));
const preservationReceipt = JSON.parse(readFileSync(
  'docs/status/wgsl-repair-v12-adapter-preservation-verification-2026-07-13.json',
  'utf8'
));
const evidenceState = JSON.parse(readFileSync(
  'tools/data/wgsl-repair-v13-semantic-evidence-state.json',
  'utf8'
));
const adapterPortabilityReceipt = JSON.parse(readFileSync(
  evidenceState.adapterPortability.path,
  'utf8'
));
const selectionReceipt = JSON.parse(readFileSync(
  evidenceState.candidate.selectionReceiptPath,
  'utf8'
));
const seedConfirmationReceipt = JSON.parse(readFileSync(
  evidenceState.seedConfirmation.receiptPath,
  'utf8'
));

const withinTolerance = evaluateNumericAgreement(
  [1, 2, 3],
  [1.000001, 2.00001, 2.99999],
  policy.taskContract.numericalAgreement.tiers.float32
);
assert.equal(withinTolerance.pass, true);
const outsideTolerance = evaluateNumericAgreement(
  [1],
  [1.1],
  policy.taskContract.numericalAgreement.tiers.float32
);
assert.equal(outsideTolerance.pass, false);
const nonFiniteMismatch = evaluateNumericAgreement(
  [1],
  [Number.NaN],
  policy.taskContract.numericalAgreement.tiers.float32
);
assert.equal(nonFiniteMismatch.pass, false);
assert.equal(nonFiniteMismatch.mismatches[0].reason, 'nonfinite_mismatch');

function variant(shapeId, shapeClass, workgroupId) {
  const inputs = { inputValues: [0.5, 1.5, 2.5] };
  const expected = [1, 2, 3];
  const actual = [1.000001, 2.00001, 2.99999];
  return {
    shapeId,
    shapeClass,
    workgroupId,
    dispatch: { status: 'pass', backend: 'chromium_webgpu' },
    oracle: {
      inputs,
      inputSha256: hashWgslSemanticEvidenceValue(inputs),
      expected,
      expectedSha256: hashWgslSemanticEvidenceValue(expected),
      actual,
      actualSha256: hashWgslSemanticEvidenceValue(actual),
      tolerance: policy.taskContract.numericalAgreement.tiers.float32,
    },
    bufferBounds: {
      prefixCanaryIntact: true,
      suffixCanaryIntact: true,
      readOnlyBuffersUnchanged: true,
      outputPaddingUnchanged: true,
      validationErrorsAbsent: true,
    },
    metamorphic: [
      { id: 'input_permutation_equivariance', status: 'pass' },
      { id: 'tiling_equivalence', status: 'pass' },
    ],
  };
}

const passingEvidence = {
  taskId: 'semantic-unit-task',
  responseContractPass: true,
  compilation: { status: 'pass' },
  variants: [
    variant('shape-nominal', 'nominal', 'wg-64'),
    variant('shape-tail', 'non_workgroup_multiple', 'wg-128'),
    variant('shape-boundary', 'boundary_or_tail', 'wg-64'),
  ],
  historicalRegressionsPass: true,
  historicalRegressionResults: [
    { id: 'logical-elements-not-padded-storage', status: 'pass' },
  ],
};
const passed = evaluateWgslSemanticTaskEvidence(policy, passingEvidence);
assert.equal(passed.pass, true);
assert.equal(passed.distinctShapeCount, 3);
assert.equal(passed.distinctWorkgroupCount, 2);

const corrupted = structuredClone(passingEvidence);
corrupted.variants[1].oracle.actual[0] = 99;
corrupted.variants[1].oracle.actualSha256 = hashWgslSemanticEvidenceValue(
  corrupted.variants[1].oracle.actual
);
corrupted.variants[2].bufferBounds.suffixCanaryIntact = false;
const failed = evaluateWgslSemanticTaskEvidence(policy, corrupted);
assert.equal(failed.pass, false);
assert.ok(failed.blockers.includes('cpu_oracle_mismatch'));
assert.ok(failed.blockers.includes('buffer_canary_corruption'));

const compileFailure = structuredClone(passingEvidence);
compileFailure.compilation.status = 'fail';
assert.ok(
  evaluateWgslSemanticTaskEvidence(policy, compileFailure).blockers.includes('compilation_failure')
);

const readiness = evaluateWgslSemanticReadiness({
  policy,
  predecessorVerified: true,
  preservationReceipt,
  taskEvidence: [],
});
assert.equal(readiness.decision, 'blocked');
assert.equal(readiness.admission.semanticEvaluationAllowed, false);
assert.equal(readiness.admission.semanticClaimAllowed, false);
assert.equal(readiness.admission.wgslDoctorAllowed, false);
assert.equal(readiness.admission.autonomousShaderAuthorAllowed, false);
assert.equal(readiness.preservationDecision, 'complete');
assert.ok(!readiness.blockers.includes('v12_adapter_external_preservation_incomplete'));
assert.ok(readiness.blockers.includes('semantic_dispatch_evidence_absent'));

const readinessV2 = evaluateWgslSemanticReadinessV2({
  policy,
  evidenceState,
  policyVerified: true,
  predecessorVerified: true,
  preservationReceipt,
  adapterPortabilityReceipt,
  adapterPortabilityReceiptVerified: true,
  populationVerification: {},
  selectionReceiptVerified: false,
  implementationVerification: {},
  taskEvidence: [],
});
assert.equal(readinessV2.schema, 'doppler.wgsl-repair-semantic-readiness/v2');
assert.equal(readinessV2.adapterPortability.pass, true);
assert.equal(readinessV2.decision, 'blocked');
assert.equal(readinessV2.phaseAdmission.calibrationAllowed, false);
assert.ok(!readinessV2.blockers.includes('trainer_to_doppler_adapter_parity_absent'));
assert.ok(!readinessV2.blockers.includes('trainer_to_doppler_parity_failure'));
assert.ok(readinessV2.blockers.includes('semantic_task_manifest_absent'));

const tamperedPortability = structuredClone(adapterPortabilityReceipt);
tamperedPortability.frozenParityGate.adapters[0].pass = false;
const tamperedV2 = evaluateWgslSemanticReadinessV2({
  policy,
  evidenceState,
  policyVerified: true,
  predecessorVerified: true,
  preservationReceipt,
  adapterPortabilityReceipt: tamperedPortability,
  adapterPortabilityReceiptVerified: true,
  populationVerification: {},
  selectionReceiptVerified: false,
  implementationVerification: {},
  taskEvidence: [],
});
assert.equal(tamperedV2.adapterPortability.pass, false);
assert.ok(tamperedV2.blockers.includes('trainer_to_doppler_parity_failure'));

const postConfirmationV2 = evaluateWgslSemanticReadinessV2({
  policy,
  evidenceState,
  policyVerified: true,
  predecessorVerified: true,
  preservationReceipt,
  adapterPortabilityReceipt,
  adapterPortabilityReceiptVerified: true,
  populationVerification: {
    calibration: true,
    checkpointSelection: true,
    seedConfirmation: true,
    promotion: false,
  },
  selectionReceipt,
  selectionReceiptVerified: true,
  seedConfirmationReceipt,
  seedConfirmationReceiptVerified: true,
  implementationVerification: {
    taskManifest: true,
    historicalRegressionManifest: true,
  },
  taskEvidence: [passingEvidence],
});
assert.equal(postConfirmationV2.seedConfirmation.pass, true);
assert.equal(postConfirmationV2.phaseAdmission.seedConfirmationAllowed, true);
assert.equal(postConfirmationV2.phaseAdmission.promotionEvaluationAllowed, false);
assert.deepEqual(postConfirmationV2.blockers, ['semantic_promotion_population_unmaterialized']);

const tamperedSeedConfirmation = structuredClone(seedConfirmationReceipt);
tamperedSeedConfirmation.candidate.seed = 47;
const tamperedConfirmationV2 = evaluateWgslSemanticReadinessV2({
  policy,
  evidenceState,
  policyVerified: true,
  predecessorVerified: true,
  preservationReceipt,
  adapterPortabilityReceipt,
  adapterPortabilityReceiptVerified: true,
  populationVerification: {
    calibration: true,
    checkpointSelection: true,
    seedConfirmation: true,
    promotion: false,
  },
  selectionReceipt,
  selectionReceiptVerified: true,
  seedConfirmationReceipt: tamperedSeedConfirmation,
  seedConfirmationReceiptVerified: true,
  implementationVerification: {
    taskManifest: true,
    historicalRegressionManifest: true,
  },
  taskEvidence: [passingEvidence],
});
assert.equal(tamperedConfirmationV2.seedConfirmation.pass, false);
assert.ok(tamperedConfirmationV2.blockers.includes(
  'semantic_seed_confirmation_evidence_invalid'
));

console.log('wgsl-repair-semantic-gate.test: ok');
