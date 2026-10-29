import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

import { hashWgslSemanticEvidenceValue } from '../../src/tooling/wgsl-repair-semantic-gate.js';

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'));
}

function sha256File(filePath) {
  return createHash('sha256').update(readFileSync(filePath)).digest('hex');
}

const policy = readJson('tools/policies/wgsl-writer-v1-diagnostic-policy.json');
const basePolicy = readJson(policy.predecessor.basePolicy.path);
const reference = readJson(policy.predecessor.referenceReceipt.path);
const referenceCore = { ...reference };
delete referenceCore.receiptHash;

assert.equal(policy.policyId, 'doppler-wgsl-writer-v1-zero-shot-diagnostic');
assert.equal(policy.status, 'frozen_before_candidate_inference');
assert.equal(sha256File(policy.predecessor.basePolicy.path), policy.predecessor.basePolicy.sha256);
assert.equal(
  sha256File(policy.predecessor.referenceReceipt.path),
  policy.predecessor.referenceReceipt.sha256
);
assert.equal(reference.receiptHash, hashWgslSemanticEvidenceValue(referenceCore));
assert.equal(reference.decision, policy.predecessor.referenceReceipt.requiredDecision);
assert.equal(reference.mode, 'reference');
assert.equal(reference.selectionAuthority, false);
assert.equal(reference.promotionAuthority, false);
assert.equal(sha256File(policy.population.path), policy.population.sha256);
assert.equal(policy.population.sha256, basePolicy.mechanics.taskManifest.sha256);
assert.equal(policy.population.populationAuthority, 'none');
assert.equal(sha256File(policy.candidateRunner.path), policy.candidateRunner.sha256);
assert.equal(sha256File(policy.semanticHarness.path), policy.semanticHarness.sha256);
assert.deepEqual(policy.candidateIds, basePolicy.candidateInitializations.map((entry) => entry.id));
assert.deepEqual(policy.executionOrder, policy.candidateIds);
assert.equal(policy.decisionRule.submissionsPerCandidate, 1);
assert.equal(policy.decisionRule.identicalPrompts, true);
assert.equal(policy.decisionRule.identicalGeneration, true);
assert.equal(policy.decisionRule.retryAllowed, false);
assert.equal(policy.decisionRule.selectionAllowed, false);
assert.equal(policy.decisionRule.confirmationAllowed, false);
assert.equal(policy.decisionRule.promotionAllowed, false);
assert.equal(policy.authority.visibleZeroShotDiagnostic, true);
assert.equal(policy.authority.calibration, false);
assert.equal(policy.authority.checkpointSelection, false);
assert.equal(policy.authority.seedConfirmation, false);
assert.equal(policy.authority.promotion, false);
assert.equal(policy.authority.productization, false);

console.log('wgsl-writer-v1-diagnostic-contract.test: ok');
