import assert from "node:assert/strict";
import test from "node:test";
import { fixture, host, action } from "./helpers/smaller-game.mjs";
test("two shared slots enforce contention while Agents consume no Facility space", () => {
  const m = fixture();
  for (const p of m.players) {
    p.runway = 12;
    p.compute = 10;
    p.pieces.forEach((a) => (a.tileId = "build"));
  }
  host(m, 1);
  host(m, 2);
  assert.equal(m.tileOccupancy("build"), 2);
  assert.ok(
    !m
      .legalResolutions(0, "build")
      .some((d) => d.parameters.hostAreaId === "build"),
  );
  assert.ok(
    m
      .legalResolutions(0, "build")
      .some((d) => d.parameters.hostAreaId === "research"),
  );
});
test("Facility construction assigns the Agent to Build but may select any open area", () => {
  const m = fixture({ factionId: "platform_empire" });
  m.players[0].runway = 12;
  const d = action(m, 0, "build", (d) => d.parameters.hostAreaId === "fund");
  m.applyResolution(0, d);
  assert.equal(m.players[0].facilities[0].tileId, "fund");
  assert.equal(m.players[0].pieces[0].tileId, "build");
  assert.equal(m.players[0].runway, 10);
});
test("one upgrade unlocks in Era II, flips once, and is exclusive with construction", () => {
  const m = fixture();
  const p = m.players[0];
  p.runway = 12;
  p.compute = 10;
  const f = host(m, 0);
  assert.ok(
    !m.legalResolutions(0, "build").some((d) => d.parameters.upgradeHostId),
  );
  m.round = 2;
  const d = action(m, 0, "build", (d) => d.parameters.upgradeHostId === f.id);
  m.applyResolution(0, d);
  assert.equal(p.runway, 9);
  assert.equal(p.compute, 9);
  assert.equal(p.facilities.length, 1);
  assert.equal(f.upgraded, true);
  assert.ok(
    !m
      .legalResolutions(0, "build")
      .some((d) => d.parameters.upgradeHostId === f.id),
  );
  assert.equal(d.parameters.facility, undefined);
});
test("every Facility operates even with no Agent or neighbouring infrastructure", async () => {
  const m = fixture({ factionId: "platform_empire" });
  const p = m.players[0];
  p.compute = 0;
  p.customerCards = [];
  host(m, 0, "research");
  host(m, 0, "build", true);
  await m.produceAll();
  assert.equal(p.compute, 5);
  assert.equal(m.matchMetrics.productionSnapshots.length, 1);
});
test("upgrades retain ownership and Venture host identity", () => {
  const m = fixture();
  m.round = 3;
  const f = host(m, 0),
    other = host(m, 1, "fund");
  m.contracts = [
    {
      id: 1,
      kind: "joint_venture",
      left: { seat: 0, facilityId: f.id },
      right: { seat: 1, facilityId: other.id },
    },
  ];
  m.players[0].runway = 12;
  m.players[0].compute = 10;
  m.applyResolution(
    0,
    action(m, 0, "build", (d) => d.parameters.upgradeHostId === f.id),
  );
  assert.equal(m.contracts[0].left.facilityId, f.id);
  assert.equal(f.tileId, "build");
});
test("removed construction modes and stale choices fail atomically", () => {
  const m = fixture();
  const before = m.snapshot();
  for (const mode of ["generator", "fusion", "quantum", "relocate", "link"])
    assert.throws(
      () =>
        m.applyResolution(0, {
          actionId: "build",
          decisionId: mode,
          parameters: { mode },
        }),
      /no longer legal/,
    );
  assert.deepEqual(m.snapshot(), before);
});
