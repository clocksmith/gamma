import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import { promisify } from "node:util";
import test from "node:test";
import { contentSourceFiles } from "../tasks/content/source-files.mjs";

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

test("player copy is bound to declared player-facing surfaces", async () => {
  const { stdout } = await execFileAsync(
    process.execPath,
    ["tasks/content/check-boundaries.mjs"],
    { cwd: root }
  );
  assert.match(
    stdout,
    /content-boundaries: verified \d+ complete component sources/
  );
});

test("release content identity includes every player-copy source", async () => {
  const graph = await readJson("content/graph.json");
  const releaseSources = new Set(contentSourceFiles(graph));
  assert.ok(releaseSources.has(graph.world));
  for (const source of Object.values(graph.excerpts)) assert.ok(releaseSources.has(source));
  for (const artifact of graph.artifacts) {
    assert.ok(releaseSources.has(artifact.source), `release binds ${artifact.source}`);
    for (const overlay of artifact.overlays || []) {
      assert.ok(releaseSources.has(overlay), `release binds ${overlay}`);
    }
  }
});

test("content compiler is domain-neutral", async () => {
  const compiler = await readFile(new URL("tasks/content/compile.mjs", root), "utf8");
  for (const forbidden of [
    "LegacyGameName",
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
    "dist/docs/core-rules.md",
    "dist/docs/map-reference.md",
    "dist/docs/component-reference.md",
    "dist/docs/card-reference.md",
    "dist/docs/world-and-institutions.md",
    "dist/docs/optional-tactics.md",
    "dist/contracts/era-situation-ledger.json",
    "dist/runtime/game-config.json",
    "dist/runtime/factions.json",
    "dist/runtime/headlines.json",
    "dist/runtime/projects.json",
    "dist/runtime/mandates.json",
    "dist/runtime/reference-cards.json",
    "dist/runtime/player-strategies.json",
    "dist/runtime/world-copy.json",
    "dist/runtime/ui-copy.json",
    "dist/runtime/simulation-copy.json",
    "dist/site/index.html",
    "dist/site/simulation.html"
  ]) {
    assert.ok(targets.has(target), `semantic graph generates ${target}`);
  }
  assert.equal(targets.size, graph.artifacts.length);
  const sourceRoots = graph.sourceRoots || ["content/"];
  assert.ok(
    graph.artifacts.every((artifact) =>
      [artifact.source, ...(artifact.overlays || [])].every((source) =>
        sourceRoots.some((sourceRoot) => source.startsWith(sourceRoot))
      )
    ),
    "every generated source and overlay has a declared canonical source root"
  );
});

test("physical sources are projected from declared ownership roots", async () => {
  const graph = await readJson("content/graph.json");
  const sources = new Set(graph.artifacts.map((artifact) => artifact.source));
  const physicalSources = [
    "content/data/content-manifest.json",
    "rules.md",
    "content/templates/map-reference.md",
    "content/templates/component-reference.md",
    "content/templates/card-reference.md",
    "world.md",
    "components/factions.json",
    "components/game.json",
    "components/headlines.json",
    "components/mandates.json",
    "components/reference-cards.json",
    "components/projects.json",
    "components/world.json"
  ];

  for (const source of physicalSources) {
    assert.ok(sources.has(source), `physical source is projected: ${source}`);
  }
  assert.ok(
    sources.has("experimental/tactics-rules.md"),
    "deferred Tactic rules are projected separately from baseline rules"
  );
  assert.ok(
    graph.artifacts.every((artifact) => !artifact.source.startsWith("content/game/")),
    "mixed game directory is not a canonical source"
  );
});

test("shared semantic references construct current cards, rules, UI, and simulation copy", async () => {
  const variables = await readJson("content/data/variables.json");
  const config = await readJson("dist/runtime/game-config.json");
  const escalation = await readJson("dist/runtime/projects.json");
  const ui = await readJson("dist/runtime/ui-copy.json");
  const simulation = await readJson("dist/runtime/simulation-copy.json");
  const rules = await readFile(new URL("dist/docs/core-rules.md", root), "utf8");
  const rulesSource = await readFile(
    new URL("rules.md", root),
    "utf8"
  );
  const graph = await readJson("content/graph.json");
  const sourcePaths = new Set(
    graph.artifacts.flatMap((artifact) => [artifact.source, ...(artifact.overlays || [])])
  );
  const allSources = await Promise.all(
    [...sourcePaths].map((source) => readFile(new URL(source, root), "utf8"))
  );

  const advancedName = variables.terms.technology.advancedGeneration;
  const advancedFacts = variables.facts.shared.advancedGeneration;
  assert.equal(variables.facts.shared.roundsWord, "four");
  assert.deepEqual(variables.terms.resources, {
    runway: "Runway",
    compute: "Compute"
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
    facilities: "Facilities",
    agent: "Agent",
    agents: "Agents"
  });
  const world = await readJson("dist/runtime/world-copy.json");
  assert.equal(config.title, world.title);
  assert.equal(
    config.powerSources.find((source) => source.id === "fusion_demonstrator").name,
    advancedName
  );
  assert.equal(
    escalation.projects.find((action) => action.id === "fusion_demonstrator").name,
    advancedName
  );
  assert.equal(
    config.powerSources.find((source) => source.id === "fusion_demonstrator").capacity,
    advancedFacts.power
  );
  assert.ok(rules.includes(`#### ${advancedName}`));
  assert.equal(ui.prototype.tracks.runway, variables.terms.resources.runway);
  assert.match(simulation.decisions.constructAdvancedGeneration, new RegExp(advancedName));
  assert.match(simulation.coverage.selectedRules.automated.join("\n"), /local Generator connections/);
  assert.match(simulation.coverage.selectedRules.modeledAbstractions.join("\n"), /connection/i);
  assert.doesNotMatch(
    simulation.coverage.selectedRules.automated.join("\n"),
    /adjacency Networks/
  );
  assert.ok(rulesSource.includes("${terms.technology.advancedGeneration}"));
  assert.ok(rulesSource.includes("${facts.shared.roundsWord | capitalize}"));
  assert.match(rules, /\*\*Standard game:\*\* Four Eras, three turns per player per Era/);
  assert.ok(allSources.join("\n").match(/\$\{[^}]+\}/g).length > 500);
  assert.doesNotMatch(
    allSources.join("\n"),
    /\$\{terms\.resources\.(capability|customers?|trust|scrutiny|mandate|power|facilities?)\}/
  );
  assert.ok(!rules.includes("${"));
});

test("Headline cards own their exact text while the rulebook owns timing", async () => {
  const { headlines } = await readJson("dist/runtime/headlines.json");
  const rules = await readFile(new URL("dist/docs/core-rules.md", root), "utf8");
  const cardReference = await readFile(new URL("dist/docs/card-reference.md", root), "utf8");
  const componentReference = await readFile(
    new URL("dist/docs/component-reference.md", root),
    "utf8"
  );

  for (const headline of headlines) {
    assert.ok(headline.name && headline.text, `card owns ${headline.id}`);
    assert.ok(!rules.includes(headline.text), `rulebook does not duplicate ${headline.id}`);
    assert.ok(cardReference.includes(headline.name), `reference projects ${headline.id} name`);
    assert.ok(cardReference.includes(headline.text), `reference projects ${headline.id} text`);
  }
  assert.match(rules, /A Headline is revealed before secret action selection/);
  assert.doesNotMatch(cardReference, /Advanced Play/);
});

test("Mandate cards own their exact text while the rulebook owns scoring timing", async () => {
  const { mandates } = await readJson("dist/runtime/mandates.json");
  const rules = await readFile(new URL("dist/docs/core-rules.md", root), "utf8");
  const cardReference = await readFile(new URL("dist/docs/card-reference.md", root), "utf8");

  for (const mandate of mandates) {
    assert.ok(mandate.name && mandate.rulesText, `card owns ${mandate.id}`);
    assert.ok(!rules.includes(mandate.rulesText), `rulebook does not duplicate ${mandate.id}`);
    assert.ok(cardReference.includes(mandate.name), `reference projects ${mandate.id} name`);
    assert.ok(cardReference.includes(mandate.rulesText), `reference projects ${mandate.id} text`);
  }
  assert.match(rules, /Score the Mandate/);
});

test("Card and Board Reference projects every other required card surface", async () => {
  const [factionDocument, projectDocument, referenceDocument, config, cardReference] = await Promise.all([
    readJson("dist/runtime/factions.json"),
    readJson("dist/runtime/projects.json"),
    readJson("dist/runtime/reference-cards.json"),
    readJson("dist/runtime/game-config.json"),
    readFile(new URL("dist/docs/card-reference.md", root), "utf8")
  ]);

  for (const faction of factionDocument.factions) {
    assert.ok(cardReference.includes(faction.name), `reference projects ${faction.id}`);
    if (faction.scoringRule) assert.ok(cardReference.includes(faction.scoringRule.text));
    for (const ability of faction.abilities) {
      assert.ok(cardReference.includes(ability.text));
      assert.ok(ability.timingLabel, `${faction.id}/${ability.id} owns player timing copy`);
      assert.ok(cardReference.includes(ability.timingLabel));
    }
  }
  assert.doesNotMatch(cardReference, /once_per_(?:round|game)|once_when_unlocked/);
  for (const escalation of projectDocument.projects) {
    assert.ok(cardReference.includes(escalation.name));
    assert.ok(cardReference.includes(escalation.text));
    assert.ok(cardReference.includes(`**Unlock Era:** ${escalation.unlockedRound}`));
  }
  for (const era of referenceDocument.eraCards) {
    assert.equal(era.physicalSurface, "governance_board");
    assert.ok(cardReference.includes(era.rulesText));
    assert.ok(cardReference.includes(era.unlockText));
  }
  assert.match(cardReference, /## Governance Board Era panels/);
  assert.match(cardReference, /## Three-panel player aid/);
  assert.match(cardReference, /## Printed Power contracts/);
  assert.match(cardReference, /No separate Power Source\s+cards are used/);
  for (const reference of referenceDocument.playerReferences) {
    for (const line of [...reference.frontText, ...reference.backText]) {
      assert.ok(cardReference.includes(line), `foldout projects ${reference.id}: ${line}`);
    }
  }
  assert.deepEqual(
    referenceDocument.playerReferences.map((reference) => [
      reference.physicalSurface,
      reference.panel
    ]),
    [
      ["foldout_player_aid", 1],
      ["foldout_player_aid", 2],
      ["foldout_player_aid", 3]
    ]
  );
  const eraThree = referenceDocument.eraCards.find((era) => era.id === "era_narrative");
  assert.match(eraThree.unlockText, /Joint Ventures/);

  for (const action of config.actions) assert.ok(cardReference.includes(action.summary));
  for (const training of config.trainingDeck.cards) {
    assert.ok(cardReference.includes(training.rulesText));
    assert.ok(cardReference.includes(training.flavorText));
  }
  for (const source of config.powerSources) {
    assert.ok(cardReference.includes(source.rulesText));
    assert.ok(cardReference.includes(source.publicClaim));
  }
});

test("world companion owns four ordered Era overviews and references canonical Era identities", async () => {
  const { eraCards } = await readJson("dist/runtime/reference-cards.json");
  const variables = await readJson("content/data/variables.json");
  const world = await readFile(new URL("dist/docs/world-and-institutions.md", root), "utf8");
  const source = await readFile(new URL("world.md", root), "utf8");
  const playerSource = source.split("<!-- player-world:start -->")[1].split("<!-- player-world:end -->")[0];
  const chapters = [...world.matchAll(/^### Era ([IV]+): (.+)$/gm)];
  assert.deepEqual(chapters.map((match) => match[1]), ["I", "II", "III", "IV"]);
  assert.deepEqual(chapters.map((match) => match[2]), eraCards.map((era) => era.name));
  for (const era of eraCards) {
    assert.equal(era.loreText, undefined, `${era.id} uses its epigraph without a second world summary`);
    for (const field of ["name", "strapline"]) {
      assert.ok(playerSource.includes(`\${content.referenceCards.byId.${era.id}.${field}}`));
    }
    assert.ok(world.includes(`> ${era.strapline}`));
  }
  for (const [key, name] of Object.entries(variables.terms.factions)) {
    assert.ok(playerSource.includes(`\${terms.factions.${key}}`), `${name} uses shared identity`);
    assert.ok(world.includes(name), `${name} appears in the Era overviews`);
  }
  assert.doesNotMatch(playerSource, /worldPrimer|\.loreText}/);
  assert.match(world, /^# [^\n]+\n\n### Era I:/);
  assert.match(world, /By 2038,/);
  assert.doesNotMatch(world, /Rules version:|The jurisdiction|This companion contains|two independent axes/);
  assert.ok(chapters.at(-1).index < world.indexOf("## The four World Endings"));
});

test("Era overviews retain institutions and scenarios alongside authorized mechanic revisions", async () => {
  const previous = await readJson("versions/0.15.6/game-bundle.json");
  const source = await readFile(new URL("world.md", root), "utf8");
  const player = source.split("<!-- player-world:start -->")[1].split("<!-- player-world:end -->")[0];
  assert.doesNotMatch(player, /Mara|Lio|Southbank|Chapter/);
  for (const subtitle of ["AI becomes ordinary", "AI becomes infrastructure", "AI begins deciding for people", "people and institutions become reproducible"]) assert.ok(player.toLowerCase().includes(subtitle.toLowerCase()));
  for (const [file, collection] of [["factions.json", "factions"], ["headlines.json", "headlines"], ["reference-cards.json", "eraCards"], ["world.json", "endings"]]) {
    const current = await readJson(`components/${file}`);
    const original = previous.contentGraph[`components/${file}`];
    assert.deepEqual(current[collection].map(row => row.id), original[collection].map(row => row.id));
  }
  const { factions } = await readJson("components/factions.json");
  for (const faction of factions) {
    const old = previous.contentGraph["components/factions.json"].factions.find(row => row.id === faction.id);
    assert.deepEqual(faction.ceo, old.ceo, "CEO remains the same faction character");
    assert.equal(faction.abilities.length, 1);
    for (const ability of old.abilities) assert.ok([...faction.abilities, ...faction.lore].some(row => row.flavorText === ability.flavorText), "institutional fiction is preserved");
  }
});

test("ending descriptions retain four rule-owned outcomes without procedural prose", async () => {
  const { endings } = await readJson("dist/runtime/world-copy.json");
  const world = await readFile(new URL("dist/docs/world-and-institutions.md", root), "utf8");
  const config = await readJson("dist/runtime/game-config.json");
  assert.deepEqual(endings.map((ending) => ending.name).sort(), Object.values(config.worldEnding.outcomes).sort());
  for (const ending of endings) {
    assert.ok(world.includes(ending.text));
    assert.doesNotMatch(ending.text, /printed (?:threshold|test)|scoring|player count|Mandate/);
  }
  assert.doesNotMatch(world, /Rules version:|This companion contains|two independent axes|Open AGI|Closed Non-AGI/);
});

test("retained signature abilities project concrete continuity institutions", async () => {
  const [factionsDocument, mandatesDocument, eraLedger] = await Promise.all([
    readJson("dist/runtime/factions.json"),
    readJson("dist/runtime/mandates.json"),
    readJson("dist/contracts/era-situation-ledger.json")
  ]);
  const factions = Object.fromEntries(
    factionsDocument.factions.map((faction) => [faction.id, faction])
  );
  const eraIvAbility = (factionId) => factions[factionId].lore.at(-1);

  assert.deepEqual(
    [
      eraIvAbility("coalition_lab").displayName,
      eraIvAbility("platform_empire").displayName,
      eraIvAbility("imperial_research_lab").displayName,
      eraIvAbility("vertical_empire").displayName,
      eraIvAbility("safety_laboratory").displayName,
      eraIvAbility("foundry").displayName
    ],
    [
      "Shared Capacity Compact",
      "Substrate Continuity Layer",
      "Substrate-Neutral Verification Standard",
      "Extraterritorial Succession Transfer",
      "Certified Right of Refusal",
      "Priority Allocation Window"
    ]
  );
  assert.equal(
    eraIvAbility("coalition_lab").flavorText,
    "The governments remain at war. Their jointly owned bridge carries desalinated water and coolant on schedule."
  );
  assert.equal(
    eraIvAbility("imperial_research_lab").flavorText,
    "Evidence assembled across distinct domains becomes eligible for recognition across biological, synthetic, and distributed institutions."
  );

  const mandates = Object.fromEntries(
    mandatesDocument.mandates.map((mandate) => [mandate.id, mandate])
  );
  assert.equal(mandates.continent_signs_loi.name, "Successor Accounts Recognized");
  assert.equal(mandates.zero_incident_quarter.name, "Maintained Reality Is Certified");
  assert.equal(mandates.responsible_acceleration.name, "Contestability Standard Maintained");
  assert.match(mandates.continent_signs_loi.rulesText, /most Customers/);
  assert.equal(
    mandates.continent_signs_loi.flavorText,
    "The institution registers the most new service identities, successor agents, or continuing accounts."
  );
  assert.match(mandates.zero_incident_quarter.rulesText, /fewest Scrutiny/);
  assert.match(mandates.responsible_acceleration.rulesText, /at least 4 Trust/);
  for (const concept of [
    "Instance Quorum",
    "Right of Exit Certification"
  ]) {
    assert.ok(
      eraLedger.scenarios.some((scenario) =>
        scenario.eraId === "continuity"
        && scenario.disposition.startsWith("adopted")
        && scenario.concepts.includes(concept)
      ),
      `${concept} remains adopted Continuity framing`
    );
  }
  const humanCompatibility = eraLedger.scenarios.find(
    (scenario) => scenario.id === "human-compatibility-office"
  );
  assert.equal(humanCompatibility.disposition, "research-backlog");
  assert.deepEqual(humanCompatibility.surfaceBindings, []);
});

test("Core Rules are compact while every moved authority has one table surface", async () => {
  const [rules, mapReference, componentReference, world, tactics, tacticDocument] = await Promise.all([
    readFile(new URL("dist/docs/core-rules.md", root), "utf8"),
    readFile(new URL("dist/docs/map-reference.md", root), "utf8"),
    readFile(new URL("dist/docs/component-reference.md", root), "utf8"),
    readFile(new URL("dist/docs/world-and-institutions.md", root), "utf8"),
    readFile(new URL("dist/docs/optional-tactics.md", root), "utf8"),
    readJson("dist/runtime/tactics.json")
  ]);
  const wordCount = rules
    .replace(/[#>*|_\-]+/g, " ")
    .split(/\s+/)
    .filter(Boolean).length;

  assert.match(rules, /Construct up to one Facility, then up to one unlocked infrastructure project/);
  assert.ok(wordCount <= 6500, "Core Rules stay printable");
  assert.match(rules, /## How to Play/);
  assert.match(rules, /## Rules Reference/);
  assert.ok(rules.indexOf("## How to Play") < rules.indexOf("## Rules Reference"));
  assert.match(rules, /Use the browser \*\*First Game Guide\*\* for a guided introduction/);
  assert.match(rules, /## 9\. Printed card authorities/);
  assert.match(rules, /## 10\. Map and component reference/);
  assert.doesNotMatch(rules, /Advanced Play/);
  assert.doesNotMatch(rules, /Jurisdictional Realignment/);
  assert.doesNotMatch(rules, /Every recognized successor enters the quorum/);
  assert.doesNotMatch(rules, /adds 1 additional Runway/);

  assert.match(mapReference, /## Build the jurisdiction/);
  assert.match(mapReference, /Every outer district touches its two outer neighbors/);
  assert.match(mapReference, /either one or two\s+inner districts/);
  assert.match(mapReference, /## District effects/);
  assert.match(componentReference, /### Training deck: 40 cards/);
  assert.match(componentReference, /integrated starting-grid identifier/);
  assert.match(componentReference, /## Defined markers and effects/);

  assert.match(world, /### Era I: Progress/);
  assert.doesNotMatch(world, /\*\*Interpretation\.\*\*/);
  assert.doesNotMatch(world, /Nobody knows whether it works/);
  assert.match(world, /## The four World Endings/);
  assert.match(world, /### The Singularity/);
  assert.match(world, /### The Closed Loop/);
  assert.match(world, /### The Plural Future/);
  assert.match(world, /### Assured Continuity/);

  const references = await readJson("dist/runtime/reference-cards.json");
  const cardReference = await readFile(new URL("dist/docs/card-reference.md", root), "utf8");
  const mandateReference = references.playerReferences.find((reference) => reference.id === "public_mandate");
  assert.match(mandateReference.backText.join("\n"), /Highest final Mandate wins/);
  assert.doesNotMatch(mandateReference.backText.join("\n"), /Draw two without replacement/);
  assert.match(mandateReference.backText.join("\n"), /The Singularity.*The Closed Loop.*The Plural Future.*Assured Continuity/);
  assert.match(cardReference, /Minimum qualification:\*\* 2/);
  assert.match(cardReference, /Deal Flow[\s\S]*Unlock Era:\*\* 1; permanent/);
  assert.doesNotMatch(cardReference, /Advanced Play/);
  assert.match(cardReference, /Each Faction has one permanent ability available from setup/);
  assert.match(cardReference, /current.*connect/i);

  for (const tactic of tacticDocument.tactics) {
    assert.ok(tactics.includes(tactic.name));
    assert.ok(tactics.includes(tactic.text));
  }
  assert.match(tactics, /not used in the baseline game/i);
});

test("numeric typography preserves exact card digits while prose may spell numbers", async () => {
  const [{ headlines }, mapReference, thematicBible] = await Promise.all([
    readJson("dist/runtime/headlines.json"),
    readFile(new URL("dist/docs/map-reference.md", root), "utf8"),
    readFile(new URL("world.md", root), "utf8")
  ]);
  const normalizedBible = thematicBible.replace(/\s+/g, " ");

  assert.match(normalizedBible, /preserve Arabic digits in exact rules, costs, thresholds/);
  assert.match(normalizedBible, /Spell out ordinary whole numbers in prose/);
  assert.match(normalizedBible, /content compiler must not apply a spell-out filter/);
  assert.ok(headlines.every((headline) => /\d/.test(headline.text)));
  assert.match(
    headlines.find((headline) => headline.id === "ten_dollar_intelligence").text,
    /gain 1 Compute and add 1 Scrutiny/
  );
  assert.match(mapReference, /Agent or Facility: one presence/);
});

test("fictional institution identities are canonical across generated game surfaces", async () => {
  const variables = await readJson("content/data/variables.json");
  const factions = await readJson("dist/runtime/factions.json");
  const rules = await readFile(new URL("dist/docs/core-rules.md", root), "utf8");
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
  assert.match(rules, /All Factions and CEOs are fictional/);
  assert.ok(rules.includes("Orisonix"), "the rules state the exceptional Research Protection refresh");
  for (const name of expectedNames.filter((name) => name !== "Orisonix")) {
    assert.ok(!rules.includes(name));
  }
  for (const identity of formerIdentities) {
    assert.ok(!rules.includes(identity), `generated rules omit former identity ${identity}`);
  }
});

test("canonical faction source contains no real-person identity vocabulary", async () => {
  const source = await readFile(new URL("components/factions.json", root), "utf8");
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
