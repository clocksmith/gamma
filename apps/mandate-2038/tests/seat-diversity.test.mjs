import test from 'node:test';
import assert from 'node:assert/strict';
import {seatBlocks, leagueBlocks, boundedInterval, comparableSets, playGame}
  from '../evidence/studies/2026-10-11-seat-diversity.mjs';
import {profiles, json} from './helpers/smaller-game.mjs';

test('seat blocks balance every institution over every seat without breaking seed pairing', () => {
  for (const count of [3, 4, 5]) {
    const bs = seatBlocks('greedy', count);
    assert.equal(bs.length, 600);
    assert.equal(new Set(bs.map(b => b.seed)).size, 600);
    assert.equal(new Set(bs.map(b => b.subset)).size, {3: 20, 4: 15, 5: 6}[count]);
    for (const b of bs) for (const institution of b.institutions)
      for (let seat = 0; seat < count; seat++) assert.equal(b.rotations.filter(r => r[seat] === institution).length, 1);
    const smoke = new Set(seatBlocks('greedy', count, true).map(b => b.seed));
    assert.ok(bs.every(b => !smoke.has(b.seed)));
  }
});

test('league uses independent seeds and crosses policy rotations with institution rotations', () => {
  const bs = leagueBlocks('weighted');
  assert.equal(bs.length, 960); assert.equal(new Set(bs.map(b => b.seed)).size, 960);
  for (const subset of new Set(bs.map(b => b.subset)))
    for (const mode of ['fixed', 'variable']) for (let repeat = 0; repeat < 2; repeat++) {
      const group = bs.filter(b => b.subset === subset && b.mode === mode && b.repeat === repeat);
      assert.equal(group.length, 16);
      for (let policy = 0; policy < 4; policy++) for (let seat = 0; seat < 4; seat++) {
        const cells = group.filter(b => (seat + b.policyRotation) % 4 === policy);
        assert.equal(new Set(cells.map(b => b.institutions[seat])).size, 4);
      }
    }
});

test('bounds scale actual sample variance, retain zero-variance uncertainty and reject invalid samples', () => {
  assert.throws(() => boundedInterval([], 'seat'));
  assert.throws(() => boundedInterval([0, 0], 'unknown'));
  assert.throws(() => boundedInterval([0, NaN], 'seat'));
  const flat = boundedInterval(Array(600).fill(0), 'seat');
  assert.equal(flat.variance, 0); assert.ok(flat.radius > 0 && flat.radius < 0.1);
  const variable = boundedInterval(Array.from({length: 600}, (_, i) => i % 2 ? 0.5 : -0.5), 'seat');
  assert.ok(variable.radius > flat.radius);
  const signal = boundedInterval(Array(600).fill(0.2), 'seat');
  assert.ok(signal.lower > 0.10);
  assert.deepEqual(comparableSets(['a', 'b', 'c'], [{left: 'a', right: 'b', comparable: true},
    {left: 'b', right: 'c', comparable: true}]), [['a', 'b'], ['b', 'c']]);
});

test('identical-policy games retain ordinary rich/batch execution and reconciled scores', async () => {
  const input = Object.fromEntries(await Promise.all(['game-config', 'factions', 'headlines', 'projects', 'mandates']
    .map(async n => [n, await json(n)])));
  const p = profiles.find(p => p.id === 'power_broker');
  for (const count of [3, 4, 5]) {
    const b = seatBlocks('greedy', count, true)[0];
    const block = {...b, seed: `${b.seed}:test-only`}, roster = Array(count).fill(p);
    const batch = await playGame(input, block, roster, 'greedy');
    assert.deepEqual(batch, await playGame(input, block, roster, 'greedy', 'rich'));
    assert.equal(batch.players.reduce((s, p) => s + p.winCredit, 0), 1);
    assert.ok(batch.players.every(p => p.profileId === roster[0].id));
  }
});
