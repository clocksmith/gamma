import test from 'node:test';
import assert from 'node:assert/strict';
import {isDeepStrictEqual} from 'node:util';
import {selectTraces, captureGame} from '../evidence/studies/2026-10-11-plan-traces.mjs';
import {playGame, leagueBlocks} from '../evidence/studies/2026-10-11-seat-diversity.mjs';
import {json, profiles} from './helpers/smaller-game.mjs';

test('trace selection is deterministic, success-conditioned, deduplicated and reports missing cells', () => {
  const league = ['a', 'b'].map(seed => ({block: {seed, mode: 'fixed'}, result: {players: [
    {profileId: 'p', factionId: 'f', winCredit: 1}, {profileId: 'q', factionId: 'g', winCredit: 0}]}}));
  const selected = selectTraces(league, [{id: 'p'}, {id: 'q'}], [{id: 'f'}, {id: 'g'}]);
  assert.equal(selected.games.length, 1); assert.equal(selected.missing.length, 7);
  assert.deepEqual(selected, selectTraces(league, [{id: 'p'}, {id: 'q'}], [{id: 'f'}, {id: 'g'}]));
  assert.deepEqual(selected.games[0].cells, [{profileId: 'p', factionId: 'f', mode: 'fixed'}]);
});

test('complete trace capture preserves both policy backends and all archived outcome fields', async () => {
  const input = Object.fromEntries(await Promise.all(['game-config', 'factions', 'headlines', 'projects', 'mandates']
    .map(async n => [n, await json(n)])));
  const roster = profiles.slice(0, 4);
  for (const backend of ['greedy', 'weighted']) {
    const b = leagueBlocks(backend, true)[0], block = {...b, seed: `${b.seed}:trace-test`};
    const ordinary = await playGame(input, block, roster, backend);
    const captured = await captureGame(input, block, roster, backend);
    assert.ok(isDeepStrictEqual(captured.outcome, ordinary));
    assert.equal(captured.decisions.filter(d => d.stage === 'select').length, 48);
    assert.equal(captured.observed.production.length, 4); assert.equal(captured.observed.reviews.length, 4);
    assert.equal(captured.finalState.complete, true); assert.ok(captured.result.replay.length > 48);
    assert.ok(captured.decisions.filter(d => d.stage === 'select').every(d => d.resolutions && d.weights.length));
  }
});
