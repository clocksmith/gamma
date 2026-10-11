import test from 'node:test';
import assert from 'node:assert/strict';
import {makeBlocks, rosterFor, candidatesFor, pairedInterval, playBlock, assertOutcome}
  from '../evidence/studies/2026-10-11-capacity-counterplay.mjs';
import {json, fixture, profiles} from './helpers/smaller-game.mjs';

test('confirmation rotates focal institutions and seats with disjoint training seeds', () => {
  const confirmation = makeBlocks('confirmation', 4, 'greedy', 16);
  const training = new Set(makeBlocks('response', 4, 'greedy', 1).map(b => b.seed));
  assert.equal(confirmation.length, 768);
  assert.equal(new Set(confirmation.map(b => b.seed)).size, 768);
  assert.ok(confirmation.every(b => !training.has(b.seed) && b.responderSeat !== b.seat));
  for (let f = 0; f < 6; f++) for (let s = 0; s < 4; s++)
    assert.equal(confirmation.filter(b => b.faction === f && b.seat === s).length, 32);
  assert.ok(makeBlocks('confirmation', 4, 'weighted', 16).every(b => !confirmation.some(g => g.seed === b.seed)));
});

test('paired response changes one policy while preserving all roster identities', () => {
  const capacity = profiles.find(p => p.id === 'power_broker');
  const rivals = profiles.filter(p => p.id !== capacity.id);
  const parent = rivals[2];
  const response = candidatesFor(parent, 'response', 'greedy')[1];
  for (const b of makeBlocks('confirmation', 5, 'greedy', 1)) {
    const baseline = rosterFor(b, capacity, rivals, parent);
    const counter = rosterFor(b, capacity, rivals, response);
    assert.deepEqual(counter.map(p => p.id), baseline.map(p => p.id));
    assert.equal(new Set(counter.map(p => p.id)).size, b.count);
    assert.equal(counter[b.responderSeat], response);
    baseline.forEach((p, s) => {if (s !== b.responderSeat) assert.equal(counter[s], p);});
  }
});

test('paired bounds retain uncertainty and reject empty or invalid evidence', () => {
  assert.throws(() => pairedInterval([]));
  assert.throws(() => pairedInterval([NaN]));
  assert.throws(() => pairedInterval([1.1]));
  const inconclusive = pairedInterval([1, -1, 0, 0]);
  assert.equal(inconclusive.mean, 0);
  assert.equal(inconclusive.lower, -1);
  assert.equal(inconclusive.upper, 1);
  const positive = pairedInterval(Array(768).fill(0.2));
  assert.ok(positive.lower > 0.04 && positive.lower < 0.2);
});

test('study uses equivalent rich/batch legal execution and detects invalid outcomes', async () => {
  const input = Object.fromEntries(await Promise.all(['game-config', 'factions', 'headlines', 'projects', 'mandates']
    .map(async n => [n, await json(n)])));
  const capacity = profiles.find(p => p.id === 'power_broker');
  const b = makeBlocks('test-only', 4, 'greedy', 1)[0];
  const roster = rosterFor(b, capacity, profiles.filter(p => p.id !== capacity.id));
  const batch = await playBlock(input, b, roster);
  const rich = await playBlock(input, b, roster, 'rich');
  assert.deepEqual(batch, rich);
  assert.equal(batch.players.reduce((sum, p) => sum + p.winCredit, 0), 1);
  const incomplete = fixture({playerCount: 4});
  assert.throws(() => assertOutcome(incomplete, incomplete.result()), /Incomplete/);
});
