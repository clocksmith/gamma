import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

import { hashWgslSemanticEvidenceValue } from '../../src/tooling/wgsl-repair-semantic-gate.js';

const RESULT_PATH = 'docs/status/wgsl-writer-v2-result-2026-07-14.json';

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'));
}

function sha256File(filePath) {
  return createHash('sha256').update(readFileSync(filePath)).digest('hex');
}

const result = readJson(RESULT_PATH);
const resultCore = { ...result };
delete resultCore.receiptHash;

assert.equal(result.receiptHash, hashWgslSemanticEvidenceValue(resultCore));
assert.equal(
  result.decision,
  'seed_confirmed_and_doppler_parity_passed_external_promotion_blocked'
);
assert.equal(result.scope.generalWgslWriter, false);
assert.equal(result.scope.productCliAuthorized, false);
assert.deepEqual(result.training.seeds.map((entry) => entry.seed), [11, 29, 47]);
for (const seed of result.training.seeds) {
  assert.equal(seed.steps, 720);
  assert.equal(seed.distinctRowsVisited, 720);
  assert.equal(sha256File(seed.status.path), seed.status.sha256);
}

assert.deepEqual(
  result.evaluation.checkpointSelection.candidates.map((entry) => entry.semanticPasses),
  [9, 10, 11]
);
assert.equal(result.evaluation.checkpointSelection.selectedSeed, 47);
assert.equal(result.evaluation.seedConfirmation.result.pass, true);
assert.equal(result.evaluation.seedConfirmation.result.confirmedSeedCount, 3);
assert.equal(result.evaluation.seedConfirmation.result.meanSemanticPassRate, 46 / 48);
assert.equal(result.parity.selectedSeed, 47);
assert.equal(result.parity.identities.pass, true);
assert.equal(result.parity.adapter.pass, true);
assert.equal(result.parity.adapter.completionTokens.exact, true);
assert.equal(result.parity.adapter.completionTokens.referenceCount, 247);
assert.equal(result.mechanicsAmendment.modelSubmissionReused, true);
assert.equal(result.mechanicsAmendment.candidateOutcomesChanged, false);
assert.equal(result.externalPromotion.populationMaterialized, false);
assert.equal(result.promotionAuthority, false);
assert.equal(result.productizationAllowed, false);

for (const identity of [
  result.evaluation.calibration.receipt,
  result.evaluation.checkpointSelection.receipt,
  result.evaluation.seedConfirmation.receipt,
  result.evaluation.checkpointSelection.selectionReceipt,
  result.evaluation.seedConfirmation.confirmationReceipt,
  result.parity.receipt,
]) {
  assert.equal(sha256File(identity.path), identity.sha256);
}

console.log('wgsl-writer-v2-result.test: ok');
