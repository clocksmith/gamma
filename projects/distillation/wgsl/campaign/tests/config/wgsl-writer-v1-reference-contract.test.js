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

const receiptPath =
  'reports/training/wgsl-writer/doppler-wgsl-writer-v1/mechanics/reference.json';
const receipt = readJson(receiptPath);
const policy = readJson(receipt.policy.path);
const manifest = readJson(receipt.taskManifest.path);
const core = { ...receipt };
delete core.receiptHash;

assert.equal(
  sha256File(receiptPath),
  'a9ccfbefebce8827669dfb08a515699f8ae57e4902bf81d9edb88366099b99ab'
);
assert.equal(receipt.receiptHash, hashWgslSemanticEvidenceValue(core));
assert.equal(receipt.schema, 'doppler.wgsl-writer-semantic-dispatch-receipt/v1');
assert.equal(receipt.experimentId, 'doppler-wgsl-writer-v1');
assert.equal(receipt.evaluationRole, 'mechanics_qualification_only');
assert.equal(receipt.mode, 'reference');
assert.equal(receipt.decision, 'reference_mechanics_passed');
assert.equal(sha256File(receipt.policy.path), receipt.policy.sha256);
assert.equal(receipt.policy.sha256, sha256File('tools/policies/wgsl-writer-v1-policy.json'));
assert.equal(sha256File(receipt.taskManifest.path), receipt.taskManifest.sha256);
assert.equal(receipt.taskManifest.sha256, policy.mechanics.taskManifest.sha256);
assert.equal(manifest.populationAuthority, 'none');
assert.equal(receipt.summary.taskCount, 3);
assert.equal(receipt.summary.responseContractPasses, 3);
assert.equal(receipt.summary.compilationPasses, 3);
assert.equal(receipt.summary.dispatchVariantCount, 9);
assert.equal(receipt.summary.dispatchVariantPasses, 9);
assert.equal(receipt.summary.historicalRegressionPasses, 3);
assert.equal(receipt.summary.semanticTaskPasses, 3);
assert.ok(receipt.tasks.every((task) => task.responseContractPass));
assert.ok(receipt.evaluatedTasks.every((task) => task.pass));
assert.equal(receipt.mechanicsQualificationAuthority, true);
assert.equal(receipt.selectionAuthority, false);
assert.equal(receipt.confirmationAuthority, false);
assert.equal(receipt.promotionAuthority, false);
assert.equal(receipt.completeShaderWritingEstablished, false);
assert.equal(receipt.productizationAllowed, false);

console.log('wgsl-writer-v1-reference-contract.test: ok');
