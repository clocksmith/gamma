import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

import {
  CAMPAIGN_REGISTRY_PATH,
  buildCampaignPolicySchemaReport,
} from '../../tools/check-wgsl-campaign-policy-schemas.js';
import { hashWgslSemanticEvidenceValue } from '../../src/tooling/wgsl-repair-semantic-gate.js';
import { resolveQualificationOutputPath } from '../../tools/qualify-wgsl-writer-v3-corpus.js';
import { requireDisclosedOutputBudget } from '../../tools/run-wgsl-writer-v3-evaluation.js';

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'));
}

function sha256File(filePath) {
  return createHash('sha256').update(readFileSync(filePath)).digest('hex');
}

const policyPath = 'tools/policies/wgsl-writer-v3-campaign-policy.json';
const policy = readJson(policyPath);
const catalog = readJson(policy.mechanics.capabilityCatalog.path);
const packageSchema = readJson(policy.mechanics.responseSchema.path);
const predecessor = readJson(policy.predecessor.result.path);
const qualification = readJson(policy.mechanics.referenceQualification.receipt.path);
const reconciliation = readJson(policy.reconciliation.receipt.path);
const diversityPolicy = readJson('tools/policies/wgsl-writer-v3-corpus-diversity-policy.json');
const diversityTrainingPolicy = readJson(
  'tools/policies/wgsl-writer-v3-diversity-training-policy.json'
);
const semanticCorpusPolicy = readJson(
  'tools/policies/wgsl-writer-v3-explicit-semantic-corpus-policy.json'
);
const semanticCatalog = readJson(semanticCorpusPolicy.corpus.capabilityCatalog.path);
const semanticTrainingPolicy = readJson(
  'tools/policies/wgsl-writer-v3-explicit-semantic-training-policy.json'
);
const budgetCorpusPolicy = readJson(
  'tools/policies/wgsl-writer-v3-explicit-output-budget-corpus-policy.json'
);
const budgetTrainingPolicy = readJson(
  'tools/policies/wgsl-writer-v3-explicit-budget-training-policy.json'
);

assert.equal(policy.policyId, 'doppler-wgsl-writer-v3-general-authoring');
assert.equal(policy.status, 'developmental_policies_reconciled_prospective_materialization_blocked');
assert.equal(policy.targetCapability, catalog.targetCapability);
assert.equal(catalog.responseContract, 'doppler.wgsl-author-package/v1');
assert.equal(packageSchema.properties.schema.const, catalog.responseContract);
assert.equal(packageSchema.additionalProperties, false);
assert.equal(packageSchema.required.includes('requirements'), true);
assert.equal(packageSchema.required.includes('passes'), true);

for (const binding of [
  policy.predecessor.result,
  policy.mechanics.responseSchema,
  policy.mechanics.packageValidator,
  policy.mechanics.executionPlanner,
  policy.mechanics.formatCatalog,
  policy.mechanics.capabilityCatalog,
  policy.mechanics.browserExecutor,
  policy.mechanics.referenceQualification.library,
  policy.mechanics.referenceQualification.harness,
  policy.mechanics.referenceQualification.manifest,
  policy.mechanics.referenceQualification.receipt,
  policy.reconciliation.receipt,
]) {
  assert.equal(sha256File(binding.path), binding.sha256, binding.path);
}

assert.equal(predecessor.experimentId, 'doppler-wgsl-writer-v2');
assert.equal(predecessor.parity.selectedSeed, policy.predecessor.selectedSeed);
assert.equal(predecessor.parity.decision, 'selected_adapter_parity_passed');
assert.equal(predecessor.generalWgslWriterClaim, false);
assert.equal(predecessor.productizationAllowed, false);
assert.equal(policy.predecessor.initializationMayBeTested, true);
assert.equal(policy.predecessor.capabilityClaimTransfers, false);
assert.equal(policy.predecessor.weightsPublished, false);
assert.equal(policy.reconciliation.laterPoliciesRole, 'development');
assert.equal(policy.reconciliation.historicalGatePreserved, true);
assert.equal(policy.reconciliation.prospectiveCampaignRequired, true);
assert.equal(reconciliation.resolution.prospectiveCampaignRequired, true);
assert.equal(reconciliation.resolution.laterPolicyRole, 'development');
for (const laterPolicy of reconciliation.laterPolicies) {
  assert.equal(laterPolicy.missingReferences.length > 0, true, laterPolicy.policyId);
    for (const missingPath of laterPolicy.missingReferences) {
      const recordedPolicy = readJson(laterPolicy.path);
      assert.ok(Object.values(recordedPolicy.admission).some((entry) => entry?.path === missingPath), missingPath);
      // Absence was observed at reconciliation, not promised for all later checkouts.
    }
}

const expectedRoleCounts = {
  training: 8,
  calibration: 4,
  checkpoint_selection: 4,
  seed_confirmation: 4,
};
const roleIds = new Map();
const allIds = new Set();
for (const [role, count] of Object.entries(expectedRoleCounts)) {
  const families = catalog.families.filter((family) => family.populationRole === role);
  assert.equal(families.length, count, role);
  assert.equal(catalog.populationRoles[role].familyPlanCount, count, role);
  assert.equal(catalog.populationRoles[role].materialized, false, role);
  roleIds.set(role, new Set(families.map((family) => family.id)));
  const pipelineKinds = new Set(families.map((family) => family.pipelineKind));
  assert.equal(pipelineKinds.has('compute'), true, `${role}: compute`);
  assert.equal(pipelineKinds.has('render'), true, `${role}: render`);
  assert.equal(pipelineKinds.has('multi_pass'), true, `${role}: multi_pass`);
  for (const family of families) {
    assert.equal(allIds.has(family.id), false, family.id);
    allIds.add(family.id);
    assert.equal(family.verification.compilation, true, family.id);
    assert.equal(family.verification.actualExecution, true, family.id);
    assert.equal(family.verification.bufferBounds, true, family.id);
    assert.equal(family.verification.metamorphic, true, family.id);
    assert.equal(family.verification.historicalRegressions, true, family.id);
    assert.equal(family.verification.requiredVariations.length >= 2, true, family.id);
  }
}
for (const [leftRole, leftIds] of roleIds.entries()) {
  for (const [rightRole, rightIds] of roleIds.entries()) {
    if (leftRole >= rightRole) continue;
    assert.deepEqual(
      [...leftIds].filter((id) => rightIds.has(id)),
      [],
      `${leftRole}/${rightRole}`
    );
  }
}

assert.equal(semanticCatalog.families.length, catalog.families.length);
for (const family of semanticCatalog.families) {
  assert.equal(family.semanticContract.resourceLayouts.length > 0, true, family.id);
  assert.equal(family.semanticContract.operation.length > 0, true, family.id);
  assert.equal(family.semanticContract.passGraph.length > 0, true, family.id);
}
assert.equal(
  resolveQualificationOutputPath(budgetCorpusPolicy),
  `${budgetCorpusPolicy.corpus.outputRoot}/reference-qualification.json`
);
assert.equal(
  resolveQualificationOutputPath(budgetCorpusPolicy, 'reports/explicit.json'),
  'reports/explicit.json'
);
assert.throws(
  () => requireDisclosedOutputBudget(semanticTrainingPolicy, semanticCorpusPolicy),
  /prompt-disclosed hard output-token budget/
);
assert.equal(
  requireDisclosedOutputBudget(budgetTrainingPolicy, budgetCorpusPolicy),
  1280
);
assert.throws(
  () => requireDisclosedOutputBudget(
    {
      ...budgetTrainingPolicy,
      evaluation: {
        ...budgetTrainingPolicy.evaluation,
        generation: {
          ...budgetTrainingPolicy.evaluation.generation,
          maxNewTokens: 1279,
        },
      },
    },
    budgetCorpusPolicy
  ),
  /must match the disclosed prompt budget: 1280/
);

assert.equal(
  semanticTrainingPolicy.repairEvidence.failureClass,
  'prompt_semantic_contract_underspecified'
);
assert.equal(semanticTrainingPolicy.repairEvidence.hiddenOracleFieldsRemoved, true);
assert.equal(semanticTrainingPolicy.repairEvidence.selectionGateChanged, false);
assert.equal(semanticTrainingPolicy.evaluation.minimumSelectionSemanticPassRate, 0.5);
assert.equal(semanticTrainingPolicy.evaluation.minimumConfirmationMeanSemanticPassRate, 0.75);
assert.equal(semanticTrainingPolicy.trainer.sequenceLength, 3072);

assert.equal(budgetTrainingPolicy.repairEvidence.failureClass, 'hidden_output_token_budget');
assert.equal(budgetTrainingPolicy.repairEvidence.outputTokenBudget, 1280);
assert.equal(budgetTrainingPolicy.repairEvidence.hardStopDisclosed, true);
assert.equal(budgetTrainingPolicy.repairEvidence.abortedBeforeReceipt, true);
assert.equal(budgetTrainingPolicy.repairEvidence.selectionGateChanged, false);
assert.equal(budgetTrainingPolicy.evaluation.generation.maxNewTokens, 1280);
assert.equal(budgetTrainingPolicy.evaluation.minimumSelectionSemanticPassRate, 0.5);
assert.equal(budgetTrainingPolicy.evaluation.minimumConfirmationMeanSemanticPassRate, 0.75);

assert.equal(catalog.promotion.materialized, false);
assert.equal(catalog.promotion.promotionAllowed, false);
assert.equal(catalog.promotion.naturalSpecificationsRequired, true);
assert.equal(catalog.promotion.familyDisjointFromAllDevelopmentRoles, true);
assert.equal(catalog.blockers.includes('package_executor_not_reference_qualified'), false);
assert.equal(catalog.blockers.includes('capability_tasks_and_oracles_not_materialized'), true);

assert.deepEqual(policy.authority, {
  corpusMaterialization: false,
  training: false,
  checkpointSelection: false,
  seedConfirmation: false,
  promotion: false,
  generalWgslWriterClaim: false,
  productization: false,
});
assert.equal(policy.mechanics.browserExecutor.status, 'reference_qualified');
assert.equal(policy.mechanics.referenceQualification.status, 'qualified');
assert.equal(qualification.decision, 'reference_package_mechanics_qualified');
assert.equal(qualification.summary.tasks, 4);
assert.equal(qualification.summary.runs, 8);
assert.equal(qualification.summary.passedTasks, 4);
assert.equal(qualification.summary.failedTasks, 0);
assert.equal(qualification.summary.deterministicReplayPassed, true);
assert.equal(qualification.summary.cleanupPassed, true);
assert.equal(qualification.runtime.identity.gpuBackend.detected, 'vulkan');
assert.equal(qualification.runtime.identity.webgpuAdapter.vendor, 'amd');
assert.equal(qualification.runtime.sessionCleanup.passed, true);
const { receiptHash, ...qualificationCore } = qualification;
assert.equal(hashWgslSemanticEvidenceValue(qualificationCore), receiptHash);
assert.equal(qualification.generalWgslWriterClaim, false);
assert.equal(qualification.productizationAllowed, false);
assert.equal(
  policy.blockers.includes('executable_package_browser_runner_is_not_reference_qualified'),
  false
);
assert.equal(
  policy.blockers.includes('executable_capability_tasks_cpu_and_raster_oracles_are_not_materialized'),
  true
);
assert.equal(policy.populationPlan.developmentRolesMaterialized, false);
assert.equal(policy.populationPlan.externalPromotion.materialized, false);
assert.equal(policy.training.allowed, false);
assert.equal(policy.training.workloadsFrozen, false);

assert.equal(diversityTrainingPolicy.repairEvidence.uniqueTrainingCompletionsBefore, 8);
assert.equal(diversityTrainingPolicy.repairEvidence.uniqueTrainingCompletionsAfter, 192);
assert.equal(diversityTrainingPolicy.repairEvidence.selectionGateChanged, false);
assert.equal(diversityTrainingPolicy.evaluation.minimumSelectionSemanticPassRate, 0.5);
assert.equal(diversityTrainingPolicy.evaluation.minimumConfirmationMeanSemanticPassRate, 0.75);

// The campaign's policy-to-schema bindings moved from Doppler's registry with it.
const registryReport = await buildCampaignPolicySchemaReport();
assert.equal(registryReport.ok, true, registryReport.errors.join('\n'));
const schemaRegistry = readJson(CAMPAIGN_REGISTRY_PATH);
assert.equal(
  schemaRegistry.policies.some((entry) => entry.id === 'wgsl-writer-v3-campaign-policy'),
  true
);
assert.equal(
  schemaRegistry.policies.some((entry) => entry.id === 'wgsl-writer-v3-corpus-diversity-policy'),
  true
);
assert.equal(
  schemaRegistry.policies.some((entry) => entry.id === 'wgsl-writer-v3-diversity-training-policy'),
  true
);
assert.equal(
  schemaRegistry.policies.some(
    (entry) => entry.id === 'wgsl-writer-v3-explicit-semantic-corpus-policy'
  ),
  true
);
assert.equal(
  schemaRegistry.policies.some(
    (entry) => entry.id === 'wgsl-writer-v3-explicit-output-budget-corpus-policy'
  ),
  true
);
assert.equal(
  schemaRegistry.policies.some(
    (entry) => entry.id === 'wgsl-writer-v3-explicit-semantic-training-policy'
  ),
  true
);
assert.equal(
  schemaRegistry.policies.some(
    (entry) => entry.id === 'wgsl-writer-v3-explicit-budget-training-policy'
  ),
  true
);

console.log('wgsl-writer-v3-contract.test: ok');
