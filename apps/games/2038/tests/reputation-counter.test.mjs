import test from 'node:test';
import assert from 'node:assert/strict';
import {ReputationCounter, blocksFor, interval, playObserved}
  from '../evidence/studies/2026-10-11-reputation-counter.mjs';
import {createPlayerPolicy} from '../lab/policies/policy-factory.js';
import {rosterFor} from '../evidence/studies/2026-10-11-capacity-counterplay.mjs';
import {fixture, profiles, json} from './helpers/smaller-game.mjs';

test('simple counter selects reachable Influence at the printed review threshold', async () => {
  const m = fixture({playerCount: 4});
  const parent = createPlayerPolicy(profiles.find(p => p.id === 'market_maximalist'), 'greedy');
  for (const reputation of [0, 1]) {
    m.players[0].reputation = reputation;
    const packet = m.packet(0, 'select', m.legalActionSelections(0));
    const policy = new ReputationCounter(parent);
    const response = await policy.decide(packet);
    assert.equal(response.decision.decisionId, 'select_influence');
    assert.equal(policy.decisions.length, 1);
    assert.deepEqual(packet.observation.self, m.publicObservation(0).self);
  }
});

test('counter preserves ordinary choices above threshold, when blocked and during resolution', async () => {
  const m = fixture({playerCount: 4});
  const parent = createPlayerPolicy(profiles.find(p => p.id === 'market_maximalist'), 'weighted');
  const counter = new ReputationCounter(parent);
  for (const scenario of ['above', 'blocked', 'resolution']) {
    m.players[0].reputation = scenario === 'above' ? 2 : 0;
    const ds = scenario === 'resolution' ? m.legalResolutions(0, 'influence') : m.legalActionSelections(0);
    if (scenario === 'blocked') ds.find(d => d.actionId === 'influence').consequences.resolvableWithoutTrade = false;
    const packet = m.packet(0, scenario, ds);
    assert.deepEqual(await counter.decide(packet), await parent.decide(packet));
  }
  assert.equal(counter.decisions.length, 0);
});

test('new fixed allocation rotates seats and institutions on separate seeds', () => {
  for (const n of [3, 4, 5]) {
    const bs = blocksFor('confirmation', n, 'greedy', n === 4 ? 16 : 4);
    assert.equal(bs.length, {3: 144, 4: 768, 5: 240}[n]);
    assert.equal(new Set(bs.map(b => b.seed)).size, bs.length);
    assert.ok(bs.every(b => b.seed.startsWith('reputation-counter-') && b.responderSeat !== b.seat));
  }
  assert.throws(() => interval([]));
  assert.throws(() => interval([Infinity]));
  assert.throws(() => interval([2]));
  assert.ok(interval(Array(768).fill(0)).lower < 0);
});

test('observing production, placement and review never changes ordinary game outcomes', async () => {
  const input = Object.fromEntries(await Promise.all(['game-config', 'factions', 'headlines', 'projects', 'mandates']
    .map(async n => [n, await json(n)])));
  const capacity = profiles.find(p => p.id === 'power_broker');
  const rivals = profiles.filter(p => p.id !== capacity.id);
  for (const count of [3, 4, 5]) {
    const block = blocksFor('test', count, 'greedy', 1)[0];
    const roster = rosterFor(block, capacity, rivals, rivals.find(p => p.id === 'market_maximalist'));
    const ordinary = await playObserved(input, block, roster, false, 'batch', false);
    const observed = await playObserved(input, block, roster, false);
    assert.deepEqual(observed.outcome, ordinary.outcome);
    assert.equal(observed.trace.production.length, 4);
    assert.equal(observed.trace.reviews.length, 4);
    assert.ok(observed.trace.production.every(p => p.players.length === count));
  }
});
