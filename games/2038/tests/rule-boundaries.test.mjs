import assert from "node:assert/strict";
import test from "node:test";
import { createBrowserInteractiveGame } from "../lab/runtime/create-browser-interactive-game.js";
import {
  evaluateEraMandate,
  nominalComputeCapacity,
} from "../lab/rules/era-mandates.js";
async function fixture(options = {}) {
  return (
    await createBrowserInteractiveGame({
      playerCount: 4,
      seed: "small-browser-boundary",
      ...options,
    })
  ).match;
}
function policies(m, select) {
  return m.players.map(() => ({
    async decide(packet) {
      return {
        decision: {
          decisionId: (select?.(packet) || packet.legalDecisions[0]).decisionId,
          rationale: "Boundary fixture",
        },
        receipt: { provider: "fixture" },
      };
    },
  }));
}
function host(m, seat, area = "build", equipped = false) {
  const org = m.players[seat].pieces.find(p => !p.tileId);
  assert.ok(org, "Fixture needs an unassigned Org");
  Object.assign(org, {tileId: area, equipped});
  return org;
}
const find = (m, s, a, pred = () => true) => {
  const d = m.legalResolutions(s, a).find(pred);
  assert.ok(d);
  return d;
};
test("five tracks and eighteen playable hexes form the browser engine state", async () => {
  const m = await fixture();
  assert.equal(m.board.length, 18);
  assert.deepEqual(Object.keys(m.config.resources), [
    "runway",
    "compute",
    "capability",
    "reputation",
    "customers",
  ]);
  assert.equal(m.players[0].customerCards, undefined);
});
test("Fund caps income and preserves the Reputation cost", async () => {
  const m = await fixture();
  const p = m.players[0];
  p.runway = 11;
  p.reputation = 3;
  m.applyResolution(
    0,
    find(m, 0, "fund", (d) => d.parameters.mode === "venture"),
  );
  assert.equal(p.runway, 12);
  assert.equal(p.reputation, 2);
});
test("equipment flips an owned Org from setup and doubles its yield", async () => {
  const m = await fixture({ factionId: "platform_empire" });
  const p = m.players[0]; p.runway = 12; p.compute = 0;
  const org = host(m, 0);
  m.applyResolution(0, find(m, 0, "build", d => d.parameters.equipOrgId === org.id));
  assert.equal(org.equipped, true);
  assert.equal(p.runway, 10);
  assert.equal(p.compute, 0);
  await m.produceAll();
  assert.equal(p.compute, 4);
});
test("Deploy increments Customers, charges Compute and Reputation, triggers only its faction", async () => {
  const m = await fixture({ factionId: "platform_empire" });
  const p = m.players[0];
  p.customers = 0;
  p.capability = 2;
  p.compute = 2;
  p.reputation = 3;
  p.runway = 4;
  m.applyResolution(0, find(m, 0, "deploy"));
  assert.equal(p.customers, 1);
  assert.equal(p.compute, 1);
  assert.equal(p.reputation, 2);
  assert.equal(p.runway, 5);
  assert.ok(!m.legalResolutions(0, "deploy").length);
});
test("Research bank and duplicate crash retain separate Reputation consequences", async () => {
  const m = await fixture({ factionId: "platform_empire" });
  const p = m.players[0];
  p.capability = 0;
  p.compute = 1;
  p.reputation = 3;
  m.trainingDrawPile = [
    { id: "l", type: "benchmark_leak", kind: "special" },
    { id: "a", type: "code", kind: "domain" },
    { id: "b", type: "code", kind: "domain" },
  ];
  await m.research(
    policies(m, (p) =>
      p.legalDecisions.find((d) => d.decisionId === "research_continue"),
    ),
    0,
    find(m, 0, "research"),
  );
  assert.equal(p.capability, 0);
  assert.equal(p.reputation, 2);
  assert.equal(m.trainingRun, null);
});
test("trade rejects wrong quantities and credits both sides atomically", async () => {
  const m = await fixture({ factionId: "platform_empire" });
  Object.assign(m.players[0], { runway: 3, compute: 1 });
  Object.assign(m.players[1], { runway: 2, compute: 3 });
  const o = m
    .immediateTradeDecisions(0)
    .find(
      (d) =>
        d.parameters.partnerSeat === 1 &&
        d.parameters.giveResource === "runway",
    ).parameters;
  const before = m.snapshot();
  assert.equal(
    m.completeImmediateTrade(0, 1, { ...o, receiveAmount: 0 }),
    false,
  );
  assert.deepEqual(m.snapshot(), before);
  assert.equal(m.completeImmediateTrade(0, 1, o), true);
  assert.deepEqual(
    m.players.slice(0, 2).map((p) => [p.runway, p.compute]),
    [
      [2, 2],
      [3, 2],
    ],
  );
});
test("Influence has no hidden Venture or agreement subsystem", async () => {
  const m = await fixture(); m.round = 3;
  assert.ok(m.legalResolutions(0, "influence").every(d => !d.parameters.leftId && !d.parameters.rightId));
  assert.equal(m.contracts, undefined);
  assert.equal(m.publicObservation(0).publicTable.pendingJointVenture, undefined);
});
test("nominal capacity is read-only and current-location dependent", async () => {
  const m = await fixture();
  const org = host(m, 0, "build", true);
  m.players[0].compute = 10;
  const before = m.snapshot();
  assert.equal(nominalComputeCapacity(m, m.players[0]), 4);
  assert.deepEqual(m.snapshot(), before);
  org.tileId = "fund";
  assert.equal(nominalComputeCapacity(m, m.players[0]), 0);
});
test("Review follows income and recognition follows Review", async () => {
  const m = await fixture();
  const p = m.players[0];
  p.runway = 0;
  p.reputation = 1;
  host(m, 0, "fund");
  await m.produceAll();
  assert.equal(p.runway, 2);
  await m.audit();
  assert.equal(p.runway, 0);
  m.round = 4;
  p.capability = 9;
  p.reputation = 4;
  p.compute = 3;
  await m.declareAgiAchievements(policies(m));
  assert.equal(p.agiDeclared, true);
  assert.equal(p.compute, 0);
  assert.equal(
    m.currentScore(p),
    17 +
      m
        .finalObjectives()
        .reduce((n, c) => n + c.standings.find((s) => s.seat === 0).points, 0),
  );
});
test("zero qualifies in pure comparisons and different histories never change standings", async () => {
  const m = await fixture();
  const p = m.players[0];
  p.reputation = 0;
  const c = { metric: "reputation", direction: "min", qualification: [] };
  const before = evaluateEraMandate(c, m, p);
  p.history = { startingReputation: 99 };
  p.metrics.researchCapability = [{ gained: 90 }];
  assert.deepEqual(evaluateEraMandate(c, m, p), before);
  assert.equal(before.qualified, true);
  assert.equal(before.value, 0);
});
test("all four objectives settle only at the final table", async () => {
  const m = await fixture();
  for (let r = 1; r <= 4; r++) {
    m.round = r;
    await m.beginRound();
    assert.equal(m.matchMetrics.eraMandateScores.length, 0);
  }
  assert.equal(m.revealedMandates.length, 4);
  m.complete = true;
  m.scoreMandate();
  assert.equal(m.matchMetrics.eraMandateScores.length, 4);
  assert.equal(
    m.snapshot().players[0].finalScore,
    m.currentScore(m.players[0]),
  );
});
test("complete browser-native game allows repeat Actions, preserves phases and hidden draw state", async () => {
  const m = await fixture();
  const r = await m.play(
    policies(m, (p) =>
      p.legalDecisions.find((d) => d.decisionId === "trade_none"),
    ),
  );
  assert.equal(m.complete, true);
  assert.equal(r.matchMetrics.productionSnapshots.length, 4);
  assert.equal(r.futureTimeline.length, 12);
  assert.equal(r.matchMetrics.eraMandateScores.length, 4);
  for (const p of m.players) {
    assert.equal(p.actionsUsed.length, 3);
    assert.ok(p.actionsUsed.every(a => m.config.actions.some(c => c.id === a)));
    assert.equal(
      Object.values(p.metrics.actions).reduce((n, v) => n + v, 0),
      12,
    );
    assert.equal(p.mandate, undefined);
  }
  assert.equal(m.publicObservation(0).trainingDrawPile, undefined);
  assert.ok(r.standings.every((p) => Number.isFinite(p.score)));
});

test("AGI diagnostics record one final opportunity per player with actual readiness and acceptance", async () => {
  const m = await fixture();
  m.players[0].capability = 9;
  m.players[0].reputation = 4;
  m.players[0].compute = 3;
  m.players[1].capability = 9;
  m.players[1].reputation = 4;
  m.players[1].compute = 2;
  await m.declareAgiAchievements(policies(m));
  const rows = m.matchMetrics.agiFunnel;
  assert.equal(rows.length, m.players.length);
  assert.equal(rows.find(r => r.seat === 0).declared, true);
  assert.equal(rows.find(r => r.seat === 1).coreRequirementsMet, true);
  assert.equal(rows.find(r => r.seat === 1).legalDeclarationWindow, false);
  assert.equal(rows.find(r => r.seat === 1).failingRequirement, "compute");
  await m.declareAgiAchievements(policies(m));
  assert.equal(m.matchMetrics.agiFunnel.length, m.players.length);
});
