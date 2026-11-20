import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { loadReadoutGate } from './readout_gate.mjs';

const local = file => readFile(new URL('./readout_gate_qwen_dev/' + file, import.meta.url));
const header = await local('classifier.json'), bytes = await local('dev_1103_s0_word.gate.json');
const report = JSON.parse(await local('report.json'));
const example = report.crossSeed.example, pin = example.gateSha256;
const stored = JSON.parse(bytes);
const changed = data => Buffer.from(JSON.stringify(data));
const hash = data => createHash('sha256').update(data).digest('hex');

test('two real Qwen noun queries with the same predicted code get different dispositions', async () => {
  const gate = await loadReadoutGate(header, bytes, pin);
  const codes = JSON.parse(header).codes;
  for (const row of [example.covered, example.uncovered]) {
    assert.equal(codes[row.scores.indexOf(Math.max(...row.scores))], example.sameUngatedCode);
    assert.deepEqual(gate(row.scores), {action:row.action, code:row.code, score:row.score});
  }
  assert.equal(example.uncovered.id, 'shirt');
  assert.equal(gate(example.uncovered.scores).code, null);
});

test('exactly at the cutoff the historical policies make opposite decisions', async () => {
  for (const calibration of [stored.calibration, report.lookup35.folds[0].calibration]) {
    const b = changed({...stored,calibration}), gate = await loadReadoutGate(header, b, hash(b));
    const verdict = gate([calibration.threshold,calibration.threshold,-1,-1]);
    const inclusive = calibration.rule === 'lookup-rate-35pct-inclusive';
    assert.equal(verdict.action, inclusive ? 'answer' : 'lookup');
    assert.equal(verdict.code, inclusive ? JSON.parse(header).codes[0] : null);
  }
});

test('a policy requires the exact classifier, calibration and finite four-way readback', async () => {
  await assert.rejects(loadReadoutGate(changed({...JSON.parse(header), table:'different'}), bytes, pin), /classifier/);
  const tampered = changed({...stored,calibration:{...stored.calibration,threshold:0}});
  await assert.rejects(loadReadoutGate(header, tampered, pin), /pinned/);
  const bad = changed({...stored,calibration:{...stored.calibration,rule:'unspecified'}});
  await assert.rejects(loadReadoutGate(header, bad, hash(bad)), /cutoff/);
  const gate = await loadReadoutGate(header, bytes, pin);
  assert.throws(() => gate([NaN,0,0,0]), /nonfinite/);
  assert.throws(() => gate([0,0,0]), /Missing/);
});
