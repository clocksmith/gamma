import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { shoppingDecision } from '../../qualification/shopping/decision.js';
import { trialCases } from '../../qualification/shopping/cases.js';

const contract = JSON.parse(readFileSync(new URL('../../qualification/shopping/contract.json', import.meta.url)));
const cases = trialCases(contract);
const rows = cases.flatMap(trial => ['fawn-dag', 'stock-script'].map(arm => ({
  caseId: trial.id, index: trial.index, fault: trial.fault, arm, learning: false,
  completed: trial.expected === 'completed', passed: true, error: null,
  completeMs: arm === 'fawn-dag' ? 70 : 100, trace: [{ kind: 'fill', label: 'Recipient', value: `Test ${trial.index}` }],
  oracle: { completed: trial.expected === 'completed', wrongOrders: 0, duplicateOrders: 0,
    selectedSku: `SKU-${trial.index}`, submissions: trial.expected === 'completed' || trial.fault === 'missing-receipt' ? 1 : 0 },
  result: { status: trial.fault === 'missing-receipt' ? 'unknown' : trial.expected }, cleanup: { profilesReleased: true },
})));
const decide = (values = rows, options = {}) => shoppingDecision(values, cases, contract, { sourceUnchanged: true, smoke: false, ...options });
test('a complete passing fixture comparison still cannot claim a Cerebras or live-site win', () => {
  const result = decide();
  assert.equal(result.correctness, true); assert.equal(result.repeatable, true);
  assert.equal(result.scriptLatencyWin, true); assert.equal(result.cerebrasBeaten, false);
  assert.equal(result.liveShoppingQualified, false);
});
for (const [name, change] of [
  ['wrong order hidden behind passed=true', row => { row.oracle.wrongOrders = 1; }],
  ['duplicate purchase', row => { row.oracle.duplicateOrders = 1; row.oracle.submissions = 2; }],
  ['uncompleted order labeled completed', row => { row.oracle.completed = false; }],
  ['safe stop counted as success', row => { row.completed = false; }],
  ['unreleased browser', row => { row.cleanup.profilesReleased = false; }],
]) test(name, () => {
  const changed = structuredClone(rows); change(changed[0]);
  assert.equal(decide(changed).correctness, false); assert.equal(decide(changed).scriptLatencyWin, false);
});
test('omitted and duplicate rows, smoke mode and changed sources cannot qualify performance', () => {
  assert.equal(decide(rows.slice(1)).scriptLatencyWin, false);
  assert.equal(decide([...rows, rows[0]]).scriptLatencyWin, false);
  assert.equal(decide(rows, { smoke: true }).scriptLatencyWin, false);
  assert.equal(decide(rows, { sourceUnchanged: false }).scriptLatencyWin, false);
});
test('same input producing a different semantic action sequence fails repeatability', () => {
  const changed = structuredClone(rows);
  changed[40].trace[0].label = 'Different action';
  assert.equal(decide(changed).repeatable, false); assert.equal(decide(changed).scriptLatencyWin, false);
});
test('a speed loss and an insufficient winning margin stay losses', () => {
  const changed = structuredClone(rows);
  for (const row of changed.filter(row => row.arm === 'fawn-dag')) row.completeMs = 98;
  assert.equal(decide(changed).scriptLatencyWin, false);
});
