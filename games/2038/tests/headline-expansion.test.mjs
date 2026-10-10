import assert from "node:assert/strict";
import test from "node:test";
import { fixture, host, headlines, policies } from "./helpers/smaller-game.mjs";
for (const card of headlines.headlines)
  test(`Headline ${card.id} resolves only its printed current-state effect`, async () => {
    const m = fixture({ factionId: "platform_empire" });
    m.round = card.round;
    m.cycle = 1;
    m.eraHeadlines = [card];
    for (const p of m.players) {
      Object.assign(p, { runway: 5, compute: 5, capability: 6, reputation: 4 });
      host(m, p.seat);
      p.customers = 0;
    }
    const before = m.players.map((p) => ({
      runway: p.runway,
      compute: p.compute,
      capability: p.capability,
      reputation: p.reputation,
      customers: p.customers,
    }));
    await m.prepareHeadline(policies(m));
    for (const p of m.players) {
      const eligible =
        card.effect.target === "each" || p.seat === m.initiativeSeat;
      for (const key of [
        "runway",
        "compute",
        "capability",
        "reputation",
        "customers",
      ]) {
        const n =
          before[p.seat][key] +
          (eligible
            ? (card.effect.gain[key] || 0) - (card.effect.cost?.[key] || 0)
            : 0);
        assert.equal(
          p[key],
          Math.min(
            key === "customers" ? 5 : m.config.resources[key].cap,
            Math.max(0, n),
          ),
          `${key} effect`,
        );
      }
      assert.deepEqual(p.actionsUsed, []);
    }
    assert.equal(m.matchMetrics.productionSnapshots.length, 0);
    assert.equal(m.matchMetrics.futureTimeline.at(-1).id, card.id);
  });
test("Customer Headline requires next Capability and never triggers Installed Base", async () => {
  const m = fixture({ factionId: "platform_empire" });
  const p = m.players[0];
  p.capability = 0;
  p.reputation = 4;
  p.runway = 5;
  p.customers = 0;
  m.eraHeadlines = [
    headlines.headlines.find((h) => h.id === "human_original_guarantee"),
  ];
  await m.prepareHeadline(policies(m));
  assert.equal(p.customers, 0);
  assert.equal(p.runway, 5);
  p.capability = 2;
  await m.prepareHeadline(policies(m));
  assert.equal(p.customers, 1);
  assert.equal(p.runway, 4);
});
