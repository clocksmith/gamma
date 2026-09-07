import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import { createInteractiveGame } from '../lab/runtime/create-interactive-game.js';

const mCategory = (m, id) => m.board.find(t => t.instanceId === id).category;
async function setup(count = 3) {
  const { match } = await createInteractiveGame({ playerCount: count, factionId: 'coalition_lab', seed: 'infrastructure-progression' }, () => {});
  await match.beginRound([]);
  for (const p of match.players) Object.assign(p, { runway: 10, compute: 8, capability: 7, scrutiny: 0, facilities: [{ id: `s${p.seat}-facility-1`, tileId: p.pieces[0].tileId, category: mCategory(match, p.pieces[0].tileId) }] });
  return match;
}
const choices = (m, seat, id) => m.legalResolutions(seat, 'build').filter(c => c.parameters.project?.id === id);
const alone = (m, seat, id) => choices(m, seat, id).find(c => !c.parameters.facility);

test('project references and runtime honor II / III / IV and later availability', async () => {
  const data = JSON.parse(await readFile(new URL('../dist/runtime/projects.json', import.meta.url)));
  assert.deepEqual(data.projects.map(p => [p.id, p.unlockedRound]), [['mega_cluster', 2], ['fusion_demonstrator', 3], ['quantum', 4]]);
  for (const era of [1, 2, 3, 4]) {
    const m = await setup(); m.round = era;
    assert.equal(Boolean(alone(m, 0, 'fusion_demonstrator')), era >= 3);
    assert.equal(Boolean(alone(m, 0, 'quantum')), era === 4);
  }
});

test('Quantum is independent, once per institution, capped, scored immediately and publicly recorded', async () => {
  for (const count of [2, 3, 4, 5]) {
    const m = await setup(count); m.round = 4;
    for (const p of m.players) {
      m.synchronizePublicMandate(p, 'test');
      const before = m.currentScore(p);
      const plan = alone(m, p.seat, 'quantum'); assert.ok(plan);
      m.applyBuild(p.seat, plan);
      assert.equal(p.runway, 6); assert.equal(p.compute, 6);
      assert.equal(p.capability, 9); assert.equal(p.scrutiny, 1);
      assert.equal(p.quantumCompleted, true);
      assert.ok(m.currentScore(p) > before, 'crossed Capability threshold scores immediately');
      assert.equal(choices(m, p.seat, 'quantum').length, 0);
      assert.throws(() => m.applyBuild(p.seat, plan), /no longer legal/);
      assert.equal(p.capability, 9);
      assert.equal(m.snapshot().players[p.seat].quantumCompleted, true);
      assert.equal(p.generators.length, 0); assert.equal(p.megaClusters.length, 0);
    }
    assert.equal(m.fusionBuiltBy, null);
  }
  const m = await setup(); m.round = 4; m.players[0].capability = 11;
  m.applyBuild(0, alone(m, 0, 'quantum'));
  assert.equal(m.players[0].capability, 12);
});

test('Quantum rejects unaffordable or disconnected plans and revalidates without partial payment', async () => {
  for (const resource of ['runway', 'compute']) {
    const m = await setup(); m.round = 4;
    m.players[0][resource] = resource === 'runway' ? 3 : 1;
    assert.equal(choices(m, 0, 'quantum').length, 0);
  }
  const m = await setup(); m.round = 4; const p = m.players[0];
  const plan = alone(m, 0, 'quantum'); assert.ok(plan);
  p.facilities = []; p.generators = [];
  assert.throws(() => m.applyBuild(0, plan), /no longer legal/);
  assert.equal(p.runway, 10); assert.equal(p.compute, 8); assert.equal(p.quantumCompleted, false);
});

test('Build can place a Facility then Quantum at that connected host with combined payment', async () => {
  const m = await setup(); m.round = 4; const p = m.players[0];
  const tile = m.board.find(t => t.id === 'grid_reactor');
  p.generators.push({ id: 'power', tileId: tile.instanceId, sourceId: 'emergency_infrastructure' });
  const plan = choices(m, 0, 'quantum').find(c => c.parameters.facility && c.parameters.destinationId === tile.instanceId);
  assert.ok(plan); const count = p.facilities.length;
  m.applyBuild(0, plan);
  assert.equal(p.facilities.length, count + 1);
  assert.equal(p.runway, 10 - plan.parameters.actualRunwayCost);
  assert.equal(p.quantumCompleted, true);
});


test('Quantum completion persists across Audit and disconnected hosts cannot qualify', async () => {
  const m = await setup(); m.round = 4; const p = m.players[0];
  const first = m.board.find(t => t.instanceId === p.facilities[0].tileId);
  const distant = m.board.find(t => t.instanceId !== first.instanceId && !m.areAdjacent(first.instanceId, t.instanceId));
  p.facilities.push({ id: 'offline', tileId: distant.instanceId, category: distant.category });
  assert.ok(!choices(m, 0, 'quantum').some(c => !c.parameters.facility && c.parameters.destinationId === distant.instanceId));
  m.applyBuild(0, alone(m, 0, 'quantum'));
  const awards = structuredClone(p.mandateAwards);
  m.synchronizePublicMandate(p, 'repeat');
  assert.deepEqual(p.mandateAwards, awards);
  // Audit changes resources, not the permanent project record.
  p.scrutiny = 0;
  await m.audit([]);
  assert.equal(p.quantumCompleted, true);
  assert.equal(choices(m, 0, 'quantum').length, 0);
});
