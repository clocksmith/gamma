import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import { promisify } from "node:util";
import test from "node:test";

const execFileAsync = promisify(execFile);
const root = new URL("../", import.meta.url);
const readJson = async (path) => JSON.parse(await readFile(new URL(path, root), "utf8"));

test("semantic content graph reproduces every declared artifact without drift", async () => {
  const { stdout } = await execFileAsync(
    process.execPath,
    ["tasks/content/compile.mjs", "--check"],
    { cwd: root }
  );
  assert.match(stdout, /content-graph: verified \d+ generated artifacts/);
});

test("content compiler is domain-neutral", async () => {
  const compiler = await readFile(new URL("tasks/content/compile.mjs", root), "utf8");
  for (const forbidden of [
    "M3T4",
    "Fusion",
    "Runway",
    "Headline",
    "Faction",
    "Mandate"
  ]) {
    assert.ok(!compiler.includes(forbidden), `compiler does not encode ${forbidden}`);
  }
});

test("semantic graph owns every player-facing construction surface", async () => {
  const graph = await readJson("content/graph.json");
  const targets = new Set(graph.artifacts.map((artifact) => artifact.target));
  for (const target of [
    "docs/core-rules.md",
    "docs/world-and-institutions.md",
    "docs/optional-tactics.md",
    "generated/game-config.json",
    "generated/factions.json",
    "generated/headlines.json",
    "generated/wild-actions.json",
    "generated/mandates.json",
    "generated/reference-cards.json",
    "generated/player-strategies.json",
    "generated/world-copy.json",
    "generated/ui-copy.json",
    "generated/simulation-copy.json",
    "web/index.html",
    "web/simulation.html"
  ]) {
    assert.ok(targets.has(target), `semantic graph generates ${target}`);
  }
  assert.equal(targets.size, graph.artifacts.length);
  const sourceRoots = graph.sourceRoots || ["content/"];
  assert.ok(
    graph.artifacts.every((artifact) =>
      sourceRoots.some((sourceRoot) => artifact.source.startsWith(sourceRoot))
    ),
    "every generated artifact has a declared canonical source root"
  );
});

test("physical sources are projected from declared ownership roots", async () => {
  const graph = await readJson("content/graph.json");
  const sources = new Set(graph.artifacts.map((artifact) => artifact.source));
  const physicalSources = [
    "physical/content-manifest.json",
    "physical/core-rules.md",
    "physical/world-and-institutions.md",
    "physical/factions.json",
    "physical/game-config.json",
    "physical/headlines.json",
    "physical/mandates.json",
    "physical/reference-cards.json",
    "physical/wild-actions.json",
    "physical/world-copy.json"
  ];

  for (const source of physicalSources) {
    assert.ok(sources.has(source), `physical source is projected: ${source}`);
  }
  assert.ok(
    sources.has("physical/optional/tactics-rules.md"),
    "deferred Tactic rules are projected separately from baseline rules"
  );
  assert.ok(
    graph.artifacts.every((artifact) => !artifact.source.startsWith("content/game/")),
    "mixed game directory is not a canonical source"
  );
});

test("shared semantic references construct current cards, rules, UI, and simulation copy", async () => {
  const variables = await readJson("physical/variables.json");
  const config = await readJson("generated/game-config.json");
  const wild = await readJson("generated/wild-actions.json");
  const ui = await readJson("generated/ui-copy.json");
  const simulation = await readJson("generated/simulation-copy.json");
  const rules = await readFile(new URL("docs/core-rules.md", root), "utf8");
  const rulesSource = await readFile(
    new URL("physical/core-rules.md", root),
    "utf8"
  );
  const allSources = await Promise.all(
    (await readJson("content/graph.json")).artifacts.map((artifact) =>
      readFile(new URL(artifact.source, root), "utf8")
    )
  );

  const advancedName = variables.terms.technology.advancedGeneration;
  const advancedFacts = variables.facts.shared.advancedGeneration;
  assert.equal(variables.facts.shared.roundsWord, "four");
  assert.deepEqual(variables.terms.resources, {
    runway: "Runway",
    compute: "Compute",
    safety: "Safety"
  });
  assert.deepEqual(variables.terms.playerTracks, {
    capability: "Capability",
    customers: "Customers",
    customer: "Customer",
    trust: "Trust",
    scrutiny: "Scrutiny",
    mandate: "Mandate"
  });
  assert.deepEqual(variables.terms.infrastructure, { power: "Power" });
  assert.deepEqual(variables.terms.components, {
    facility: "Facility",
    facilities: "Facilities"
  });
  assert.equal(config.title, variables.game.title);
  assert.equal(
    config.powerSources.find((source) => source.id === "fusion_demonstrator").name,
    advancedName
  );
  assert.equal(
    wild.wildActions.find((action) => action.id === "fusion_demonstrator").name,
    advancedName
  );
  assert.equal(
    config.powerSources.find((source) => source.id === "fusion_demonstrator").capacity,
    advancedFacts.power
  );
  assert.ok(rules.includes(`#### ${advancedName}`));
  assert.equal(ui.prototype.tracks.runway, variables.terms.resources.runway);
  assert.match(simulation.decisions.constructAdvancedGeneration, new RegExp(advancedName));
  assert.ok(rulesSource.includes("${terms.technology.advancedGeneration}"));
  assert.ok(rulesSource.includes("${facts.shared.roundsWord | capitalize}"));
  assert.match(rules, /\*\*Standard game:\*\* Four rounds, three turns per player per round/);
  assert.ok(allSources.join("\n").match(/\$\{[^}]+\}/g).length > 500);
  assert.doesNotMatch(
    allSources.join("\n"),
    /\$\{terms\.resources\.(capability|customers?|trust|scrutiny|mandate|power|facilities?)\}/
  );
  assert.ok(!rules.includes("${"));
});

test("Headline cards are the single source for the rulebook inventory", async () => {
  const { headlines } = await readJson("generated/headlines.json");
  const rules = await readFile(new URL("docs/core-rules.md", root), "utf8");
  const rulesSource = await readFile(
    new URL("physical/core-rules.md", root),
    "utf8"
  );

  for (const headline of headlines) {
    assert.ok(rules.includes(headline.name), `rules project ${headline.id} name`);
    assert.ok(rules.includes(headline.text), `rules project ${headline.id} text`);
    assert.ok(
      rulesSource.includes(`\${content.headlines.byId.${headline.id}.name}`),
      `rulebook template references ${headline.id}`
    );
  }
  for (const retiredName of [
    "Open-Weights Drop",
    "Talent Gold Rush",
    "Boardroom Coup",
    "Export Controls",
    "Weights on the Internet",
    "Election Deepfake Panic",
    "Agent Swarm Escapes Scope"
  ]) {
    assert.ok(!rules.includes(retiredName), `rules retire incident-pinned title ${retiredName}`);
  }
});

test("Era cards are the single source for the world-companion escalation lore", async () => {
  const { eraCards } = await readJson("generated/reference-cards.json");
  const world = await readFile(new URL("docs/world-and-institutions.md", root), "utf8");
  const worldSource = await readFile(
    new URL("physical/world-and-institutions.md", root),
    "utf8"
  );

  for (const era of eraCards) {
    assert.ok(era.loreText, `${era.id} owns its lore`);
    assert.ok(world.includes(era.loreText), `world companion projects ${era.id} lore`);
    assert.ok(
      worldSource.includes(`\${content.referenceCards.byId.${era.id}.loreText}`),
      `world companion template references ${era.id} lore`
    );
  }
});

test("How to Play is trimmed while every moved authority remains governed", async () => {
  const [rules, world, tactics, tacticDocument] = await Promise.all([
    readFile(new URL("docs/core-rules.md", root), "utf8"),
    readFile(new URL("docs/world-and-institutions.md", root), "utf8"),
    readFile(new URL("docs/optional-tactics.md", root), "utf8"),
    readJson("generated/tactics.json")
  ]);
  const wordCount = rules
    .replace(/[#>*`|_\-]+/g, " ")
    .split(/\s+/)
    .filter(Boolean).length;
  const previousWordCount = 11565;

  assert.ok(wordCount <= Math.floor(previousWordCount * 0.9), `${wordCount} words is at least 10% shorter`);
  assert.ok(wordCount >= Math.ceil(previousWordCount * 0.8), `${wordCount} words preserves the 20% trim floor`);
  assert.doesNotMatch(rules, /### Tone contract/);
  assert.doesNotMatch(rules, /## 15\. Balance rationale and test boundary/);
  assert.doesNotMatch(rules, /## 12\. Deferred module: Tactic cards/);
  assert.match(world, /## Tone contract/);
  assert.match(world, /## The four Eras/);
  assert.match(world, /## The two World Endings/);

  for (const tactic of tacticDocument.tactics) {
    assert.ok(tactics.includes(tactic.name), `optional rules include ${tactic.id} name`);
    assert.ok(tactics.includes(tactic.text), `optional rules include ${tactic.id} exact card text`);
  }
  assert.match(tactics, /not used in the baseline game/i);
});

test("numeric typography preserves exact card digits while prose may spell numbers", async () => {
  const [{ headlines }, rules, thematicBible] = await Promise.all([
    readJson("generated/headlines.json"),
    readFile(new URL("docs/core-rules.md", root), "utf8"),
    readFile(new URL("docs/thematic-content-bible.md", root), "utf8")
  ]);
  const normalizedBible = thematicBible.replace(/\s+/g, " ");

  assert.match(normalizedBible, /Use Arabic digits in card rules, costs, quantities, thresholds/);
  assert.match(normalizedBible, /Spell out ordinary whole numbers in narrative and explanatory prose/);
  assert.match(normalizedBible, /content compiler must not apply a spell-out filter/);
  assert.ok(
    headlines.every((headline) => rules.includes(headline.text)),
    "rulebook preserves exact digit-bearing Headline text"
  );
  assert.match(
    headlines.find((headline) => headline.id === "ten_dollar_intelligence").text,
    /adds 1 additional/
  );
  assert.match(rules, /CEO: two presence/);
});

test("fictional institution identities are canonical across generated game surfaces", async () => {
  const variables = await readJson("physical/variables.json");
  const factions = await readJson("generated/factions.json");
  const rules = await readFile(new URL("docs/core-rules.md", root), "utf8");
  const expectedNames = [
    "Dovetalis Labs",
    "Loopfold AI",
    "Mirevanta Works",
    "Kestralyn",
    "Orisonix",
    "Corthaven"
  ];
  const formerIdentities = [
    "Sam Altman",
    "Mark Zuckerberg",
    "Demis Hassabis",
    "Elon Musk",
    "Dario Amodei",
    "Jensen Huang"
  ];

  assert.deepEqual(Object.values(variables.terms.factions), expectedNames);
  assert.deepEqual(factions.factions.map((faction) => faction.name), expectedNames);
  assert.deepEqual(
    factions.factions.map((faction) => faction.roleId),
    ["faction-1", "faction-2", "faction-3", "faction-4", "faction-5", "faction-6"]
  );
  assert.ok(factions.factions.every((faction) => !("historicalReference" in faction)));
  for (const name of expectedNames) assert.ok(rules.includes(`### ${name}`));
  for (const identity of formerIdentities) {
    assert.ok(!rules.includes(identity), `generated rules omit former identity ${identity}`);
  }
});

test("canonical faction source contains no real-person identity vocabulary", async () => {
  const source = await readFile(new URL("physical/factions.json", root), "utf8");
  for (const name of [
    "Sam Altman",
    "Mark Zuckerberg",
    "Demis Hassabis",
    "Elon Musk",
    "Dario Amodei",
    "Jensen Huang"
  ]) {
    assert.ok(!source.includes(name), `mechanical faction graph omits identity ${name}`);
  }
});
