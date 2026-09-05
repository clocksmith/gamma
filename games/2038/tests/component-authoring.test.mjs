import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { documentSection, documentSections, omitDocumentSections, playerContent, stripSectionMarkers, validateReferenceLayout } from "../tasks/content/authored.mjs";
import { resolveString, resolveValue } from "../tasks/content/references.mjs";
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

test("rule excerpts resolve nested component data once and reject broken references", () => {
  const source = "<!-- map:start -->\nMove ${limits.steps} spaces.\n<!-- map:end -->\n";
  const variables = { limits: { steps: 2 }, excerpts: { rules: documentSections(source) } };
  assert.equal(resolveString("${excerpts.rules.map}", variables), "Move 2 spaces.\n");
  variables.limits.steps = 3;
  assert.equal(resolveString("${excerpts.rules.map}", variables), "Move 3 spaces.\n");
  assert.throws(() => resolveString("${excerpts.rules.missing}", variables), /Unknown content reference/);
  assert.throws(() => resolveString("${a}", {a:"${b}",b:"${a}"}), /Circular content reference/);
  assert.throws(() => documentSections("<!-- broken:end -->"), /exactly one/);
  assert.doesNotMatch(stripSectionMarkers(source), /<!--/);
});

test("compact documents omit only explicitly declared sections", () => {
  const source = "Keep before.\n<!-- map:start -->\nMap detail.\n<!-- map:end -->\nKeep after.\n";
  assert.equal(omitDocumentSections(source, ["map"]), "Keep before.\nKeep after.\n");
  assert.equal(omitDocumentSections(source), source);
  assert.throws(() => omitDocumentSections(source, ["missing"]), /exactly one/);
  assert.throws(() => omitDocumentSections(source, "map"), /must be an array/);
  assert.equal(resolveString("${section|headings-up}", {section:"### Decks\n#### Training\nKeep prose."}),
    "## Decks\n### Training\nKeep prose.");
});

test("map, component and inventory readers reuse the rulebook's owned passages", async () => {
  const read = path => readFile(new URL(`../${path}`, import.meta.url), "utf8");
  const [source, rawVariables, rawGame, rawGraph] = await Promise.all([
    read("rules.md"), read("content/data/variables.json"), read("components/game.json"), read("content/graph.json")
  ]);
  const variables = JSON.parse(rawVariables);
  const context = {...resolveValue(variables, variables), content:{gameConfig:JSON.parse(rawGame)},
    excerpts:{rules:documentSections(source)}};
  for (const [section, slug] of [["map", "map-reference"], ["components", "component-reference"], ["inventory", "component-inventory"]]) {
    const expected = stripSectionMarkers(resolveString(`\${excerpts.rules.${section}|headings-up}`, context)).trim();
    const actual = (await read(`dist/docs/${slug}.md`)).split("\n").slice(1).join("\n").trim();
    assert.equal(actual, expected, `${slug} has no independent procedural prose`);
  }
  const graph = JSON.parse(rawGraph);
  assert.deepEqual(graph.artifacts.find(a => a.target === "dist/docs/core-rules.md").excludeSections, ["map", "components"]);
  const core = await read("dist/docs/core-rules.md");
  assert.doesNotMatch(core, /Build the jurisdiction|Exact printed-paper count|<!--/);
  assert.match(core, /\/docs\/map-reference.html/);
  assert.match(core, /\/docs\/component-reference.html/);
  const cardReference = await read("dist/docs/card-reference.md");
  const {headlines} = JSON.parse(await read("dist/runtime/headlines.json"));
  for (const card of headlines) {
    const section = cardReference.split(`### ${card.name}\n`)[1]?.split("\n### ")[0];
    assert.ok(section?.includes(`**Duration:** ${variables.terms.durations[card.duration]}`), `${card.id} owns its duration`);
  }
});

test("reference layouts refuse independently authored rules and quantities", () => {
  validateReferenceLayout("# Map\n\n${excerpts.rules.map}\n**Duration:** ${card.duration}\n", "map.md");
  for (const text of ["Move two spaces.", "Gain 10 ${terms.resources.runway}.", "| Cost | 10 |", "**Gain 10:**", "**Move two spaces.**", "| Move two spaces |"] ) {
    assert.throws(() => validateReferenceLayout(text, "map.md"), /unsourced prose/);
  }
  assert.equal(resolveString("${card.duration|label:labels}", {card:{duration:"cycle"},labels:{cycle:"Current cycle"}}), "Current cycle");
  assert.throws(() => resolveString("${card.duration|label:labels}", {card:{duration:"unknown"},labels:{}}), /Unknown content label/);
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
  assert.equal(index.scenarios.flatMap(s => s.surfaceBindings).length, 54);
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
