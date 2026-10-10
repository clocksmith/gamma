import assert from "node:assert/strict";
import test from "node:test";
import { fixture, policies, profiles } from "./helpers/smaller-game.mjs";
import { WeightedPlayerPolicy } from "../lab/policies/weighted-policy.js";
for (const count of [2, 3, 4, 5])
  test(`${count}-player games complete deterministically with exactly twelve actions each`, async () => {
    const run = async () => {
      const m = fixture({
        playerCount: count,
        seed: `complete-${count}`,
        recordReplay: true,
      });
      return {
        m,
        r: await m.play(
          m.players.map(
            (p, s) => new WeightedPlayerPolicy(profiles[s % profiles.length]),
          ),
        ),
      };
    };
    const { m, r } = await run();
    assert.deepEqual((await run()).r, r);
    assert.equal(m.complete, true);
    assert.equal(r.futureTimeline.length, 12);
    assert.equal(r.matchMetrics.productionSnapshots.length, 4);
    assert.equal(r.matchMetrics.eraMandateScores.length, 4);
    assert.ok(r.winnerSeats.length);
    for (const p of m.players) {
      assert.equal(
        Object.values(p.metrics.actions).reduce((n, v) => n + v, 0),
        12,
      );
      for (const [k, c] of Object.entries(m.config.resources))
        assert.ok(p[k] >= c.min && p[k] <= c.cap);
      assert.ok(p.facilities.length <= 4 && p.customers <= 5);
    }
    assert.ok(
      r.decisionProtocol.immediateTradePackets <=
        r.decisionProtocol.immediateTradePacketCeiling,
    );
  });
test("zero resources do not deadlock speculative commitments; blocked action is exhausted", async () => {
  const m = fixture({ headlines: { headlines: [] } });
  m.players.forEach((p) => {
    p.compute = 0;
    p.runway = 0;
  });
  await m.playCycle(
    policies(
      m,
      (p) =>
        p.legalDecisions.find((d) => d.decisionId === "select_research") ||
        p.legalDecisions.find((d) => d.decisionId === "trade_none"),
    ),
  );
  assert.ok(
    m.players.every(
      (p) => p.actionsUsed.includes("research") && p.metrics.forcedNoOps === 1,
    ),
  );
});
