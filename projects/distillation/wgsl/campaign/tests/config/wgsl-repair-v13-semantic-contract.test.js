import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import {
  evaluateWgslSemanticReadiness,
  evaluateWgslSemanticReadinessV2,
} from '../../src/tooling/wgsl-repair-semantic-gate.js';

const policy = JSON.parse(readFileSync('tools/policies/wgsl-repair-v13-semantic-policy.json', 'utf8'));
const preservation = JSON.parse(readFileSync(
  policy.predecessor.preservationVerificationPath,
  'utf8'
));
const committed = JSON.parse(readFileSync(
  'docs/status/wgsl-repair-v13-semantic-readiness-2026-07-13.json',
  'utf8'
));
const replayed = evaluateWgslSemanticReadiness({
  policy,
  predecessorVerified: true,
  preservationReceipt: preservation,
  taskEvidence: [],
});

assert.deepEqual(replayed, committed);
assert.equal(policy.status, 'frozen_requirements_populations_unmaterialized');
assert.equal(policy.taskContract.actualDispatchRequired, true);
assert.equal(policy.taskContract.cpuOracle.required, true);
assert.equal(policy.taskContract.shapeVariation.minimumDistinctShapesPerTask, 3);
assert.equal(policy.taskContract.workgroupVariation.minimumSemanticallyValidVariantsPerTask, 2);
assert.equal(policy.taskContract.bufferBounds.prefixCanaryElements, 16);
assert.equal(policy.taskContract.bufferBounds.suffixCanaryElements, 16);
assert.equal(policy.taskContract.metamorphic.minimumApplicableRelationsPerTask, 2);
assert.equal(policy.taskContract.historicalRegressions.required, true);
assert.equal(policy.metrics.primary, 'semantic_task_pass_at_1');
assert.equal(committed.decision, 'blocked');
assert.equal(committed.admission.wgslDoctorAllowed, false);
assert.equal(committed.admission.autonomousShaderAuthorAllowed, false);

const evidenceState = JSON.parse(readFileSync(
  'tools/data/wgsl-repair-v13-semantic-evidence-state-preselection-2026-07-14.json',
  'utf8'
));
const adapterPortability = JSON.parse(readFileSync(
  evidenceState.adapterPortability.path,
  'utf8'
));
const referenceMechanics = JSON.parse(readFileSync(
  'docs/status/wgsl-repair-v13-reference-mechanics-2026-07-14.json',
  'utf8'
));
const current = JSON.parse(readFileSync(
  'docs/status/wgsl-repair-v13-semantic-readiness-2026-07-14.json',
  'utf8'
));
const replayedCurrent = evaluateWgslSemanticReadinessV2({
  policy,
  evidenceState,
  policyVerified: true,
  predecessorVerified: true,
  preservationReceipt: preservation,
  adapterPortabilityReceipt: adapterPortability,
  adapterPortabilityReceiptVerified: true,
  populationVerification: {
    calibration: true,
    checkpointSelection: true,
    seedConfirmation: false,
    promotion: false,
  },
  selectionReceiptVerified: false,
  implementationVerification: {
    taskManifest: true,
    historicalRegressionManifest: true,
  },
  taskEvidence: referenceMechanics.tasks,
});
assert.deepEqual(replayedCurrent, current);
assert.equal(current.adapterPortability.pass, true);
assert.equal(current.phaseAdmission.calibrationAllowed, true);
assert.equal(current.phaseAdmission.checkpointSelectionAllowed, true);
assert.equal(current.phaseAdmission.seedConfirmationAllowed, false);
assert.equal(current.admission.semanticClaimAllowed, false);
assert.equal(current.admission.wgslDoctorAllowed, false);
assert.ok(!current.blockers.includes('trainer_to_doppler_adapter_parity_absent'));
assert.ok(current.blockers.includes('external20_seed_checkpoint_not_selected'));

const postSelectionState = JSON.parse(readFileSync(
  'tools/data/wgsl-repair-v13-semantic-evidence-state-postselection-2026-07-14.json',
  'utf8'
));
const selectionReceipt = JSON.parse(readFileSync(
  postSelectionState.candidate.selectionReceiptPath,
  'utf8'
));
const postSelection = JSON.parse(readFileSync(
  'docs/status/wgsl-repair-v13-semantic-readiness-post-selection-2026-07-14.json',
  'utf8'
));
const replayedPostSelection = evaluateWgslSemanticReadinessV2({
  policy,
  evidenceState: postSelectionState,
  policyVerified: true,
  predecessorVerified: true,
  preservationReceipt: preservation,
  adapterPortabilityReceipt: adapterPortability,
  adapterPortabilityReceiptVerified: true,
  populationVerification: {
    calibration: true,
    checkpointSelection: true,
    seedConfirmation: false,
    promotion: false,
  },
  selectionReceipt,
  selectionReceiptVerified: true,
  implementationVerification: {
    taskManifest: true,
    historicalRegressionManifest: true,
  },
  taskEvidence: referenceMechanics.tasks,
});
assert.deepEqual(replayedPostSelection, postSelection);
assert.equal(postSelection.candidateSelection.pass, true);
assert.equal(postSelection.candidate.selectedSeed, 29);
assert.ok(!postSelection.blockers.includes('external20_seed_checkpoint_not_selected'));
assert.ok(postSelection.blockers.includes('semantic_seed_confirmation_population_unmaterialized'));
assert.ok(postSelection.blockers.includes('semantic_promotion_population_unmaterialized'));
assert.equal(postSelection.admission.semanticClaimAllowed, false);
assert.equal(postSelection.admission.wgslDoctorAllowed, false);

const preConfirmationState = JSON.parse(readFileSync(
  'tools/data/wgsl-repair-v13-semantic-evidence-state-preconfirmation-2026-07-14.json',
  'utf8'
));
const preConfirmation = JSON.parse(readFileSync(
  'docs/status/wgsl-repair-v13-semantic-readiness-pre-confirmation-2026-07-14.json',
  'utf8'
));
const replayedPreConfirmation = evaluateWgslSemanticReadinessV2({
  policy,
  evidenceState: preConfirmationState,
  policyVerified: true,
  predecessorVerified: true,
  preservationReceipt: preservation,
  adapterPortabilityReceipt: adapterPortability,
  adapterPortabilityReceiptVerified: true,
  populationVerification: {
    calibration: true,
    checkpointSelection: true,
    seedConfirmation: true,
    promotion: false,
  },
  selectionReceipt,
  selectionReceiptVerified: true,
  implementationVerification: {
    taskManifest: true,
    historicalRegressionManifest: true,
  },
  taskEvidence: referenceMechanics.tasks,
});
assert.deepEqual(replayedPreConfirmation, preConfirmation);
assert.equal(preConfirmation.phaseAdmission.seedConfirmationAllowed, true);
assert.equal(preConfirmation.phaseAdmission.promotionEvaluationAllowed, false);
assert.deepEqual(preConfirmation.blockers, ['semantic_promotion_population_unmaterialized']);
assert.equal(preConfirmation.admission.semanticClaimAllowed, false);
assert.equal(preConfirmation.admission.wgslDoctorAllowed, false);

const latestState = JSON.parse(readFileSync(
  'tools/data/wgsl-repair-v13-semantic-evidence-state.json',
  'utf8'
));
const seedConfirmationReceipt = JSON.parse(readFileSync(
  latestState.seedConfirmation.receiptPath,
  'utf8'
));
const seedConfirmationSemantic = JSON.parse(readFileSync(
  seedConfirmationReceipt.semanticReceipt.path,
  'utf8'
));
const postConfirmation = JSON.parse(readFileSync(
  'docs/status/wgsl-repair-v13-semantic-readiness-post-confirmation-2026-07-14.json',
  'utf8'
));
const replayedPostConfirmation = evaluateWgslSemanticReadinessV2({
  policy,
  evidenceState: latestState,
  policyVerified: true,
  predecessorVerified: true,
  preservationReceipt: preservation,
  adapterPortabilityReceipt: adapterPortability,
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
  taskEvidence: seedConfirmationSemantic.tasks,
});
assert.deepEqual(replayedPostConfirmation, postConfirmation);
assert.equal(postConfirmation.seedConfirmation.pass, true);
assert.equal(postConfirmation.seedConfirmation.selectedSeed, 29);
assert.equal(postConfirmation.taskEvidence.length, 8);
assert.ok(postConfirmation.taskEvidence.every((task) => task.pass === true));
assert.deepEqual(postConfirmation.blockers, ['semantic_promotion_population_unmaterialized']);
assert.equal(postConfirmation.admission.semanticClaimAllowed, false);
assert.equal(postConfirmation.admission.wgslDoctorAllowed, false);

console.log('wgsl-repair-v13-semantic-contract.test: ok');
