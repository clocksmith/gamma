import test from 'node:test';
import assert from 'node:assert/strict';
import {scenarios, playArm, observeProduction, interval} from '../evidence/studies/2026-10-11-early-recruitment.mjs';
import {playGame} from '../evidence/studies/2026-10-11-seat-diversity.mjs';
import {json, profiles, fixture} from './helpers/smaller-game.mjs';

const input = Object.fromEntries(await Promise.all(['game-config', 'factions', 'headlines', 'projects', 'mandates']
  .map(async n => [n, await json(n)])));

test('recruitment scenarios have independent seeds and complete crossed institution/seat coverage', () => {
  for (const [n, expected] of [[3, 360], [4, 960], [5, 300]]) {
    const rows = scenarios(n); assert.equal(rows.length, expected);
    assert.equal(new Set(rows.map(b => b.seed)).size, expected);
    const coverage = {};
    for (const b of rows) {
      const k = `${b.seat}:${b.institutions[b.seat]}`; coverage[k] = (coverage[k] || 0) + 1;
    }
    assert.equal(Object.keys(coverage).length, n * 6);
    assert.equal(new Set(Object.values(coverage)).size, 1);
    assert.ok(scenarios(n, true).every(b => !rows.some(r => r.seed === b.seed)));
  }
});

test('study parent preserves ordinary full outcomes; production observation preserves execution', async () => {
  const roster = profiles.slice(0, 4), block = {...scenarios(4, true)[0], seed: 'early-recruitment-test:parent'};
  const ordinary = await playGame(input, block, roster, 'greedy');
  const observed = await playArm(input, block, roster, 'parent');
  const unobserved = await playArm(input, block, roster, 'parent', 'rich', false);
  assert.deepEqual(observed.outcome, ordinary); assert.deepEqual(unobserved.outcome, ordinary);
  assert.deepEqual(observed.final, unobserved.final);
  assert.equal(observed.trace.production.length, 4);
  assert.ok(observed.decisions.every(d => d.decision === d.parentDecision));
});

test('extra Org is legally recruited and actively positioned before first Production', async () => {
  const roster = profiles.slice(0, 4), block = {...scenarios(4, true)[0], seed: 'early-recruitment-test:setup'};
  const run = await playArm(input, block, roster, 'recruit');
  assert.ok(run.decisions.some(d => d.stage === 'resolve' && d.reason === 'early_recruit'));
  const setup = run.decisions.find(d => d.stage === 'resolve' && ['position_extra_org', 'equip_extra_org'].includes(d.reason));
  assert.ok(setup); assert.equal(setup.round, 1);
  const third = run.sources.filter(s => s.source === 'org' && s.orgId === 's0-agent-3');
  assert.equal(third.length, 4); assert.equal(third[0].resource, 'compute');
  assert.ok(third[0].nominal >= 2);
  const unobserved = await playArm(input, block, roster, 'recruit', 'rich', false);
  assert.deepEqual(run.outcome, unobserved.outcome); assert.deepEqual(run.final, unobserved.final);
});

test('per-Org production attributes actual yield and cap losses in real engine order', async () => {
  const match = fixture({playerCount: 3}), p = match.players[0];
  const t = match.board.find(t => t.yield.resource === 'compute' && t.yield.amount === 2);
  p.compute = 9; p.pieces.forEach(o => {o.tileId = t.instanceId; o.equipped = false;});
  p.pieces.push({id: 's0-agent-3', tileId: t.instanceId, equipped: true});
  const rows = observeProduction(match); await match.produceAll();
  const orgs = rows.filter(r => r.seat === 0 && r.source === 'org');
  assert.deepEqual(orgs.map(o => o.nominal), [2, 2, 4]);
  assert.deepEqual(orgs.map(o => o.actual), [1, 0, 0]);
  assert.deepEqual(orgs.map(o => o.capLoss), [1, 2, 4]);
  assert.equal(p.compute, 10);
});

test('paired inference rejects out-of-range or incomplete observations', () => {
  assert.throws(() => interval([0]), RangeError); assert.throws(() => interval([0, 2]), RangeError);
  assert.equal(interval([0, 0]).mean, 0); assert.equal(interval([40, -40], 40).mean, 0);
});
