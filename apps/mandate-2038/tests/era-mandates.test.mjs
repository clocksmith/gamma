import assert from "node:assert/strict";
import test from "node:test";
import { fixture, host, mandates } from "./helpers/smaller-game.mjs";
import {
  evaluateEraMandate,
  finalObjectiveStandings,
  nominalComputeCapacity,
  neighboringRivals,
} from "../lab/rules/era-mandates.js";
for (const card of mandates.mandates)
  test(`final objective ${card.id} evaluates current state without history or mutation`, () => {
    const m = fixture();
    for (const p of m.players) {
      Object.assign(p, { runway: 5, compute: 3, capability: 4, reputation: 3 });
      m.gainCustomer(p);
      host(m, p.seat, "build", true);
    }
    const before = m.snapshot();
    const rows = finalObjectiveStandings(card, m);
    assert.equal(rows.length, 4);
    assert.ok(
      rows.every(
        (r) => Number.isFinite(r.value) && [0, 1, 2].includes(r.points),
      ),
    );
    m.players[0].objectiveRecord = { value: 999 };
    m.players[0].metrics.researchCapability = [{ gained: 900 }];
    assert.deepEqual(finalObjectiveStandings(card, m), rows);
    assert.deepEqual(m.snapshot(), before);
  });
test("qualification is separate from max/min, ties, and valid zero", () => {
  const m = fixture();
  m.players.forEach((p) => {
    p.reputation = 0;
    p.customers = 0;
  });
  const card = {
    metric: "reputation",
    direction: "min",
    qualification: [{ metric: "customers", minimum: 1 }],
  };
  assert.ok(finalObjectiveStandings(card, m).every((r) => r.points === 0));
  m.gainCustomer(m.players[0]);
  m.gainCustomer(m.players[1]);
  let rows = finalObjectiveStandings(card, m);
  assert.deepEqual(
    rows.map((r) => r.points),
    [1, 1, 0, 0],
  );
  m.players[1].reputation = 2;
  rows = finalObjectiveStandings(card, m);
  assert.deepEqual(
    rows.map((r) => r.points),
    [2, 0, 0, 0],
  );
  card.direction = "max";
  assert.deepEqual(
    finalObjectiveStandings(card, m).map((r) => r.points),
    [0, 2, 0, 0],
  );
});
test("capacity reads equipped Org locations; neighboring rivals need an actual edge", () => {
  const m = fixture();
  const org = host(m, 0, "build", true);
  host(m, 1, "research");
  m.players[0].compute = 10;
  assert.equal(nominalComputeCapacity(m, m.players[0]), 4);
  assert.equal(neighboringRivals(m, m.players[0]), 1);
  org.tileId = "fund";
  assert.equal(nominalComputeCapacity(m, m.players[0]), 0);
  m.players[1].pieces.forEach(p => p.tileId = null);
  assert.equal(neighboringRivals(m, m.players[0]), 0);
});
test("all four revealed objectives use final holdings, no early earned points", async () => {
  const m = fixture();
  for (let era = 1; era <= 4; era++) {
    m.round = era;
    await m.beginRound();
    assert.equal(m.matchMetrics.eraMandateScores.length, 0);
    assert.equal(m.snapshot().players[0].finalScore, undefined);
  }
  assert.equal(m.revealedMandates.length, 4);
  m.players[0].capability = 12;
  m.complete = true;
  m.scoreMandate();
  const old = m.currentScore(m.players[0]);
  m.players[0].capability = 1;
  m.scoreMandate();
  assert.ok(m.currentScore(m.players[0]) < old);
  assert.equal(m.matchMetrics.eraMandateScores.length, 4);
});
test("final score and World Ending depend only on final holdings", () => {
  const m = fixture();
  m.revealedMandates = [];
  const p = m.players[0];
  p.capability = 9;
  p.reputation = 4;
  p.customers = 0;
  m.gainCustomer(p);
  p.agiDeclared = true;
  assert.equal(m.currentScore(p), 19);
  p.mandate = 100;
  p.highestTrustMilestone = 999;
  assert.equal(m.currentScore(p), 19);
  m.players.forEach((p) => (p.reputation = 3));
  assert.equal(m.result().worldEnding.id, "singularity");
  m.players.forEach((p) => (p.reputation = 0));
  assert.equal(m.result().worldEnding.id, "closed_loop");
});
