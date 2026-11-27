import test from "node:test";
import assert from "node:assert/strict";
import { fixture, policies, mandates, config, factions } from "./helpers/smaller-game.mjs";
import { createRng, shuffle } from "../web/src/engine.js";
import { runMonteCarlo } from "../lab/runner/monte-carlo-runner.js";

const holdings = (p) => Object.fromEntries(Object.keys(config.resources).map(k => [k, p[k]]));
const skip = (m, seat, id) => m.legalResolutions(seat, id).find(d => d.parameters.skipAction);

for (const faction of factions.factions)
for (const actionId of ["fund", "research", "build", "organize", "deploy", "influence"])
  test(`${faction.id}: affordable ${actionId} can be skipped without costs, rewards, or faction triggers`, () => {
    const m = fixture({ factionId: faction.id });
    const p = m.players[0];
    p.runway = 8; p.compute = 8; p.capability = 8; p.reputation = 3;
    assert.ok(m.legalResolutions(0, actionId).some(d => !d.parameters.skipAction));
    const before = holdings(p), deck = [...m.trainingDrawPile];
    const orgs = structuredClone(p.pieces);
    const d = skip(m, 0, actionId);
    assert.deepEqual(d.consequences, {});
    m.applyResolution(0, d);
    assert.deepEqual(holdings(p), before);
    assert.deepEqual(m.trainingDrawPile, deck);
    assert.equal(p.pieces.length, orgs.length);
    assert.deepEqual(p.pieces.map(o => o.equipped), orgs.map(o => o.equipped));
    assert.equal(p.pieces.find(o => o.id === d.parameters.pieceId).tileId, d.parameters.destinationId);
    assert.equal(p.metrics.forcedNoOps, 0);
  });

for (const actionId of ["fund", "research"])
test(`${actionId} movement commits before resolution and cannot select a second Org or destination`, async () => {
  const m = fixture({ headlines: { headlines: [] } });
  let assignments = 0;
  const assign = m.assignAgent.bind(m);
  m.assignAgent = (...args) => { assignments++; return assign(...args); };
  await m.playCycle(policies(m, packet => {
    const stage = packet.requestId.split(":").at(-2);
    if (stage === "immediate_trade") return packet.legalDecisions.find(d => d.decisionId === "trade_none");
    if (stage === "select") return packet.legalDecisions.find(d => d.actionId === actionId);
    if (stage === "resolve") {
      const {pieceId, destinationId} = m.turnMovement;
      assert.equal(packet.observation.self.pieces.find(o => o.id === pieceId).tileId, destinationId);
      assert.ok(packet.legalDecisions.every(d => d.parameters.pieceId === pieceId && d.parameters.destinationId === destinationId));
      const wrong = {...packet.legalDecisions[0], decisionId: "skip_action_s0-agent-2_fund", actionId: "fund"};
      assert.throws(() => m.applyResolution(packet.seat, wrong), /no longer legal/);
      return packet.legalDecisions.find(d => !d.parameters.skipAction);
    }
    return packet.legalDecisions.find(d => d.decisionId === "research_bank");
  }));
  assert.equal(assignments, m.playerCount, "Resolution cannot assign a second time");
  assert.equal(m.turnMovement, null);
  assert.ok(m.players.every(p => p.metrics.turns === 1 && p.metrics.actions[actionId] === 1));
});

test("unaffordable Research permits one-edge movement, keeps equipment, and produces normally", async () => {
  const m = fixture(); const p = m.players[0];
  p.compute = 0;
  p.pieces.forEach(o => { o.tileId = "fund"; o.equipped = true; });
  const move = m.legalMovementSelections(0).find(d => d.parameters.destinationId === "research");
  assert.ok(move); assert.equal(move.consequences.resolvableWithoutTrade, false);
  assert.ok(!m.legalMovementSelections(0).some(d => d.parameters.destinationId === "deploy"));
  m.commitMovement(0, move);
  const ds = m.legalResolutions(0, "research");
  assert.equal(ds.length, 1); assert.equal(ds[0].parameters.skipAction, true);
  m.applyResolution(0, ds[0]); m.turnMovement = null;
  assert.equal(p.compute, 0);
  assert.equal(p.pieces[0].equipped, true);
  await m.produceAll();
  assert.equal(p.compute, 2);
});

for (const playerCount of [2, 3, 4, 5])
  test(`${playerCount} players can deliberately skip all twelve turns without failed resolutions`, async () => {
    const m = fixture({ playerCount, headlines: { headlines: [] } });
    const orders = [];
    const original = m.produceAll.bind(m);
    m.produceAll = async () => { orders.push(m.initiativeSeat); await original(); };
    const outcome = await m.play(policies(m, packet =>
      packet.legalDecisions.find(d => d.decisionId === "trade_none") ||
      packet.legalDecisions.find(d => d.parameters.skipAction)));
    for (const row of outcome.standings) {
      assert.equal(row.metrics.turns, 12);
      assert.equal(row.metrics.deliberateSkips, 12);
      assert.equal(row.metrics.forcedNoOps, 0);
      assert.deepEqual(row.metrics.actions, {});
    }
    assert.deepEqual(orders, [3, 6, 9, 12].map(n => n % playerCount));
    for (const projection of ["rich", "batch"]) {
      const report = await runMonteCarlo({runs:1, seed:"skip-report", projection,
        precomputedOutcomes:[{runIndex:0,outcome}]});
      assert.equal(report.diagnostics.integrity.violations, 0);
      assert.equal(report.diagnostics.integrity.deliberateSkips, 12 * playerCount);
      const corrupted = structuredClone(outcome);
      corrupted.standings[0].metrics.turns = 13;
      const invalid = await runMonteCarlo({runs:1, seed:"skip-report", projection,
        precomputedOutcomes:[{runIndex:0,outcome:corrupted}]});
      assert.ok(invalid.diagnostics.integrity.violations > 0);
    }
  });

for (const mandateMode of ["fixed", "variable"])
  test(`${mandateMode} setup selects the same Era-seeded objectives once before any Headline`, async () => {
    for (const seed of ["candidate-objectives-a", "candidate-objectives-b", "candidate-objectives-c"]) {
      const m = fixture({seed, mandateMode});
      const expected = config.rounds.map(({number}) => {
        const pool = mandates.mandates.filter(c => c.era === number);
        return (mandateMode === "fixed" ? pool : shuffle(pool, createRng(`${seed}:mandates:${number}`)))[0];
      });
      assert.deepEqual(m.revealedMandates, expected);
      assert.equal(m.snapshot().activeHeadline, null);
      assert.equal(m.snapshot().revealedHeadlines.length, 0);
      assert.deepEqual(m.snapshot().revealedMandates, expected);
      assert.deepEqual(m.publicObservation(0).revealedMandates, expected);
      for (const era of [1, 2, 2, 3, 4, 4]) {
        m.round = era; await m.beginRound();
        assert.deepEqual(m.revealedMandates, expected);
        assert.equal(m.roundMandate.id, expected[era - 1].id);
      }
    }
  });


test("a stale unaffordable Research resolution rejects before movement or payment", async () => {
  const m = fixture();
  const d = m.legalResolutions(0, "research").find(d => !d.parameters.skipAction);
  m.players[0].compute = 0;
  const before = m.snapshot();
  await assert.rejects(m.research(policies(m), 0, d), /no longer legal/);
  assert.deepEqual(m.snapshot(), before);
});
