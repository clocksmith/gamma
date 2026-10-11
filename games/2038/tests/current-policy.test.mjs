import test from 'node:test';
import assert from 'node:assert/strict';
import {fixture, profiles} from './helpers/smaller-game.mjs';
import {WeightedPlayerPolicy} from '../lab/policies/weighted-policy.js';

test('research/deploy treatment consumes the current Org observation', async () => {
  const match = fixture();
  const packet = match.packet(0, 'select', match.legalActionSelections(0));
  const policy = new WeightedPlayerPolicy(profiles[0], {selection:'greedy', treatment:'research_deploy_plan_v1'});
  const result = await policy.decide(packet);
  assert.ok(packet.legalDecisions.some(d => d.decisionId === result.decision.decisionId));
});

for (const playerCount of [2,3,4,5]) test(`current treatment finishes ${playerCount}-player games without fallbacks`, async () => {
  const match = fixture({playerCount, seed:`org-plan:${playerCount}`});
  const policies = match.players.map((_, i) => new WeightedPlayerPolicy(profiles[i % profiles.length], {selection:'greedy', treatment:'research_deploy_plan_v1'}));
  const result = await match.play(policies);
  assert.equal(match.complete, true);
  for (const row of result.standings) {
    assert.equal(row.metrics.policyFallbacks, 0);
    assert.ok(Number.isFinite(row.score));
  }
});
