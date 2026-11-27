import assert from "node:assert/strict";
import test from "node:test";
import { fixture, host, action } from "./helpers/smaller-game.mjs";

test("Orgs can stay or move one edge, but cannot jump or enter the Era center", () => {
  const m = fixture();
  m.players[0].pieces.forEach(p => p.tileId = "fund");
  assert.ok(m.legalResolutions(0, "fund").length);
  assert.ok(m.legalResolutions(0, "research").length);
  assert.equal(m.legalResolutions(0, "deploy").length, 0);
  assert.equal(m.legalResolutions(0, "organize").length, 0);
  assert.ok(!m.board.some(h => h.instanceId === "era"));
});
test("Build equips one owned Org and preserves its identity and position", () => {
  const m = fixture({ factionId: "platform_empire" });
  const p = m.players[0]; p.runway = 12;
  const target = host(m, 0, "fund");
  const decision = action(m, 0, "build", d => d.parameters.equipOrgId === target.id);
  m.applyResolution(0, decision);
  assert.equal(target.tileId, "fund");
  assert.equal(target.equipped, true);
  assert.equal(p.pieces[1].tileId, "build");
  assert.equal(p.runway, 10);
  assert.ok(!m.legalResolutions(0, "build").some(d => d.parameters.equipOrgId === target.id));
  assert.ok(!m.legalResolutions(1, "build").some(d => d.parameters.equipOrgId === target.id));
});
test("every placed Org produces, equipped yield doubles, unassigned Orgs do not", async () => {
  const m = fixture({ factionId: "platform_empire" });
  const p = m.players[0]; p.compute = 0; p.customers = 0;
  host(m, 0, "research"); host(m, 0, "build", true);
  await m.produceAll();
  assert.equal(p.compute, 5);
  assert.equal(m.matchMetrics.productionSnapshots.length, 1);
});
test("different physical copies of the same Action have distinct legal destinations", () => {
  const m = fixture();
  const choices = m.legalResolutions(0, "fund");
  assert.equal(new Set(choices.map(d => d.parameters.destinationId)).size, 3);
  assert.equal(new Set(choices.map(d => d.decisionId)).size, choices.length);
  m.applyResolution(0, action(m, 0, "fund", d => d.parameters.destinationId === "fund-2"));
  assert.equal(m.players[0].pieces[0].tileId, "fund-2");
});
test("stale movement or equipment choices reject without spending or moving", () => {
  const m = fixture(); m.players[0].runway = 12;
  const decision = action(m, 0, "build");
  m.players[0].pieces.forEach(p => p.tileId = "fund");
  const before = m.snapshot();
  assert.throws(() => m.applyResolution(0, decision), /no longer legal/);
  assert.deepEqual(m.snapshot(), before);
  for (const mode of ["generator", "fusion", "quantum", "link"])
    assert.throws(() => m.applyResolution(0, { actionId: "build", decisionId: mode, parameters: {mode} }), /no longer legal/);
  assert.deepEqual(m.snapshot(), before);
});
