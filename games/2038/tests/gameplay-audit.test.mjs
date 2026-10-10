import assert from "node:assert/strict";
import test from "node:test";
import { fixture, host, action, policies } from "./helpers/smaller-game.mjs";
const c = (type, kind = "special") => ({ id: type, type, kind });
test("Reputation Review charges exactly low-Reputation players after income, floor zero", async () => {
  const m = fixture();
  m.players.forEach((p, s) => {
    p.runway = s === 0 ? 1 : 5;
    p.reputation = s;
  });
  await m.audit();
  assert.deepEqual(
    m.players.map((p) => p.runway),
    [0, 3, 5, 5],
  );
  assert.equal(m.players[0].compute, m.factions[0].starts.compute);
});
test("riskier Fund applies cap-clipped income and Reputation consequence in order", () => {
  const m = fixture();
  const p = m.players[0];
  p.runway = 11;
  p.reputation = 0;
  m.applyResolution(
    0,
    action(m, 0, "fund", (d) => d.parameters.mode === "venture"),
  );
  assert.equal(p.runway, 12);
  assert.equal(p.reputation, 0);
});
test("accepted trade is bilateral and only fixed quantities are valid", () => {
  const m = fixture({ factionId: "coalition_lab" });
  Object.assign(m.players[0], { runway: 3, compute: 1 });
  Object.assign(m.players[1], { runway: 2, compute: 4 });
  const o = m
    .immediateTradeDecisions(0)
    .find(
      (d) =>
        d.parameters.partnerSeat === 1 &&
        d.parameters.giveResource === "runway",
    ).parameters;
  const before = m.snapshot();
  assert.equal(m.completeImmediateTrade(0, 1, { ...o, giveAmount: 99 }), false);
  assert.deepEqual(m.snapshot(), before);
  assert.equal(m.completeImmediateTrade(0, 1, o), true);
  assert.equal(m.players[0].compute, 2);
  assert.equal(m.players[1].compute, 3);
  assert.equal(m.players[0].runway, 3);
  assert.equal(m.players[1].runway, 3);
  assert.equal(m.matchMetrics.trades.accepted, 1);
});
test("recipient cap prevents a transfer and refusal changes neither account", async () => {
  const m = fixture();
  m.players[0].compute = 10;
  assert.ok(
    !m
      .immediateTradeDecisions(0)
      .some((d) => d.parameters.receiveResource === "compute"),
  );
  const before = m.players.map((p) => [p.runway, p.compute]);
  await m.trade(
    policies(
      m,
      (p) =>
        p.legalDecisions.find((d) => d.decisionId === "trade_reject") ||
        p.legalDecisions.find((d) => d.decisionId.startsWith("trade_offer_")),
    ),
    0,
  );
  assert.deepEqual(
    m.players.map((p) => [p.runway, p.compute]),
    before,
  );
});
test("shared Research duplicate loses provisional Capability but retains Leak consequence", async () => {
  const m = fixture({ factionId: "platform_empire" });
  const p = m.players[0];
  p.compute = 2;
  p.capability = 0;
  p.reputation = 3;
  m.trainingDrawPile = [
    c("benchmark_leak"),
    c("code", "domain"),
    c("code", "domain"),
  ];
  await m.research(
    policies(m, (p) =>
      p.legalDecisions.find((d) => d.decisionId === "research_continue"),
    ),
    0,
    action(m, 0, "research"),
  );
  assert.equal(p.capability, 0);
  assert.equal(p.reputation, 2);
  assert.equal(p.compute, 1);
  assert.equal(m.trainingDiscard.length, 3);
  assert.equal(m.trainingRun, null);
});
test("Human Evaluation forces banking and curated Corpus uses absent printed domain", async () => {
  const m = fixture();
  const p = m.players[0];
  p.capability = 0;
  p.compute = 2;
  p.reputation = 1;
  m.trainingDrawPile = [
    c("curated_corpus"),
    c("science", "domain"),
    c("human_evaluation"),
  ];
  await m.research(
    policies(m, (p) =>
      p.legalDecisions.find((d) => d.decisionId === "research_continue"),
    ),
    0,
    action(m, 0, "research"),
  );
  assert.equal(p.capability, 2);
  assert.equal(p.reputation, 2);
  assert.equal(p.metrics.researchCapability[0].outcome, "human-evaluation");
});
test("Scientific Method offers affordable paid bank; Safety retains only one on crash", async () => {
  for (const id of ["imperial_research_lab", "safety_laboratory"]) {
    const m = fixture({ factionId: id });
    const p = m.players[0];
    p.capability = 0;
    p.compute = 2;
    p.runway = 3;
    m.trainingDrawPile = [
      c("code", "domain"),
      c("science", "domain"),
      c("code", "domain"),
    ];
    await m.research(
      policies(
        m,
        (p) =>
          p.legalDecisions.find((d) => d.decisionId === "research_continue") ||
          p.legalDecisions.find((d) => d.decisionId === "research_pay_bank"),
      ),
      0,
      action(m, 0, "research"),
    );
    assert.equal(p.capability, id === "safety_laboratory" ? 1 : 2);
    assert.equal(p.runway, id === "safety_laboratory" ? 3 : 2);
  }
});
test("Customers give capped income without changing their count", async () => {
  const m = fixture({ factionId: "platform_empire" });
  const p = m.players[0];
  p.runway = 11;
  p.customers = 0;
  m.gainCustomer(p);
  m.gainCustomer(p);
  await m.produceAll();
  assert.equal(p.runway, 12);
  assert.equal(p.customers, 2);
  assert.equal(p.customerCards, undefined);
});
