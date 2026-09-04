import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { documentSection, playerContent } from "../tasks/content/authored.mjs";
import { assembleScenarioIndex, scenarioSurfaces } from "../tasks/content/scenario-index.mjs";

test("component notes never enter playable data or mutate authored records", () => {
  const source = {
    headlines: [{ id: "event", round: 2, text: "Gain 1 Compute.",
      $scenario: { id: "test", publicBenefit: "Editorial benefit" } }],
    nested: { $era: { centralConflict: "Editorial question" }, name: "Capacity" }
  };
  const before = structuredClone(source);
  assert.deepEqual(playerContent(source), {
    headlines: [{ id: "event", round: 2, text: "Gain 1 Compute." }],
    nested: { name: "Capacity" }
  });
  assert.deepEqual(source, before);
});

test("world companion extraction excludes editorial guidance and backlog", async () => {
  const world = await readFile(new URL("../world.md", import.meta.url), "utf8");
  const player = documentSection(world, "player-world");
  assert.match(player, /World and Institutions/);
  assert.doesNotMatch(player, /Research provenance|Unadopted scenarios|scenario-backlog/);
  assert.match(documentSection(world, "world-guide"), /Research provenance/);
  for (const source of ["", "<!-- p:start --><!-- p:start --><!-- p:end -->", "<!-- p:end --><!-- p:start -->"]) {
    assert.throws(() => documentSection(source, "p"), /exactly one|Reversed/);
  }
});

test("scenario bindings derive from component identity and point to the complete record", async () => {
  const surfaces = await scenarioSurfaces();
  const index = assembleScenarioIndex({ surfaces, backlog: [], deploymentProfiles: {} });
  const event = index.scenarios.find(s => s.id === "cheap-token-rebound");
  assert.ok(event.surfaceBindings.some(b => b.copyReference ===
    "components/headlines.json#headlines/ten_dollar_intelligence"));
  assert.equal(event.surfaceBindings.length, 4);
  assert.equal(index.eras.length, 4);
  assert.equal(index.scenarios.flatMap(s => s.surfaceBindings).length, 62);
});

test("authoring rejects missing, duplicate, and unresolved scenario definitions", async () => {
  const original = await scenarioSurfaces();
  const assemble = surfaces => assembleScenarioIndex({ surfaces, backlog: [], deploymentProfiles: {} });
  const missing = structuredClone(original);
  delete missing[0].record.$scenario;
  assert.throws(() => assemble(missing), /Missing scenario notes/);
  const unknown = structuredClone(original);
  unknown.find(s => s.record.$scenario.ref).record.$scenario.ref = "missing";
  assert.throws(() => assemble(unknown), /Unknown scenario reference/);
  const duplicate = structuredClone(original);
  const owner = duplicate.find(s => s.record.$scenario.id);
  duplicate.find(s => s.record.$scenario.ref).record.$scenario = structuredClone(owner.record.$scenario);
  assert.throws(() => assemble(duplicate), /Duplicate or missing scenario definition/);
  const manualBindings = structuredClone(original);
  manualBindings.find(s => s.record.$scenario.id).record.$scenario.surfaceBindings = [];
  assert.throws(() => assemble(manualBindings), /bindings must be generated/);
});
