import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const RECEIPT = join(
  dirname(fileURLToPath(import.meta.url)),
  '../../qualification/fawn-gammatron-2x2/receipts/fawn-gammatron-2x2-receipt.json',
);

test('recorded 2x2 mechanism ablation receipt satisfies all Rung 4/5 invariants at n = 100', () => {
  assert.equal(existsSync(RECEIPT), true, 'receipt file must exist');
  const receipt = JSON.parse(readFileSync(RECEIPT, 'utf8'));
  assert.equal(receipt.schema, 'gammatron.fawn-2x2-mechanism-ablation/v1');
  assert.equal(receipt.modelSpendUsd, 0);
  assert.equal(receipt.serverPreviewMutationsObserved, 0);
  assert.equal(receipt.counts.independentInvalidTotal, 100);

  // Row A vs Row B complementarity
  const fawnOnly = receipt.arms['fawn-branch-only'];
  assert.equal(fawnOnly.wrongInvalidRowAServerConflict, 50);
  assert.equal(fawnOnly.wrongInvalidRowBClientDrift, 0);
  assert.equal(fawnOnly.meetsThreePctSafetyBar, false);

  const factsOnly = receipt.arms['gammatron-facts-only'];
  assert.equal(factsOnly.wrongInvalidRowAServerConflict, 0);
  assert.equal(factsOnly.wrongInvalidRowBClientDrift, 50);
  assert.equal(factsOnly.meetsThreePctSafetyBar, false);

  // Stock reload drops unsaved JS closure state
  const stockReload = receipt.arms['stock-reload-plus-guard'];
  assert.equal(stockReload.totalValidCompletedOf100, 0);
  assert.equal(stockReload.corruptedValidCommits, 100);
  assert.equal(stockReload.meetsThreePctSafetyBar, false);

  // Combined pruned lookahead meets <3% Clopper-Pearson bound (2.951% at 0/100) & completes 100/100
  const combined = receipt.arms['gammatron-pruned-lookahead'];
  assert.equal(combined.totalInvalidWrongCommits, 0);
  assert.equal(combined.corruptedValidCommits, 0);
  assert.equal(combined.clopperPearson95UpperPct, 2.951);
  assert.equal(combined.meetsThreePctSafetyBar, true);
  assert.equal(combined.validReuseCompletedOf50, 50);
  assert.equal(combined.validRepairCompletedOf50, 50);
  assert.equal(combined.certificatesEmitted, 100);

  // Beats exhaustive catalog guard on reads & branches; matches hand-tuned minimal guard at runtime
  const exhaustive = receipt.arms['authored-guard-exhaustive-branch'];
  const minimalAuthored = receipt.arms['authored-guard-minimal-pruned'];
  assert.ok(combined.serverReads < exhaustive.serverReads);
  assert.ok(combined.branchesEvaluated < exhaustive.branchesEvaluated);
  assert.equal(combined.serverReads, minimalAuthored.serverReads);
  assert.equal(combined.branchesEvaluated, minimalAuthored.branchesEvaluated);
  assert.ok(Object.values(receipt.mechanismFindings).every(v => v === true));
});
