import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";
import { writeImmutableArtifact } from "../tasks/release-artifacts.mjs";

const root = new URL("../", import.meta.url);
const projectRoot = root.pathname;
const readJson = async (path) => JSON.parse(await readFile(new URL(path, root), "utf8"));

test("current release declaration separates executable game from physical rules candidate", async () => {
  const current = await readJson("versions/current-release.json");

  assert.equal(current.gameVersion, "0.14.2");
  assert.equal(current.rulesCandidate.version, "0.8.0-rc.3-test");
  assert.equal(current.rulesCandidate.implementationStatus, "synchronized");
  assert.equal(current.rulesCandidate.implementedByGameVersion, "0.14.2");
  assert.ok(current.rulesetFiles.includes("dist/runtime/game-config.json"));
  assert.ok(current.playtestKitFiles.includes("dist/runtime/simulation-copy.json"));
  assert.deepEqual(current.rulesCandidate.files.slice(0, 3), [
    "dist/docs/core-rules.md",
    "dist/docs/world-and-institutions.md",
    "dist/docs/optional-tactics.md"
  ]);
});

test("physical authority separates profiles and preserves automatic blind Audit draws", async () => {
  const [spec, inventory, governanceLedger, manufacturing, manifest] = await Promise.all([
    readFile(new URL("physical/component-spec.md", root), "utf8"),
    readFile(new URL("physical/component-inventory.md", root), "utf8"),
    readFile(new URL("physical/governance-ledger.md", root), "utf8"),
    readFile(new URL("docs/manufacturing-and-publishing-study.md", root), "utf8"),
    readJson("content/data/content-manifest.json")
  ]);

  assert.match(spec, /indistinguishable by touch while concealed/);
  assert.match(spec, /same size, shape, material, and\s+weight/);
  assert.doesNotMatch(spec, /distinguishable by touch or sight/);
  assert.match(spec, /shared Mandate track/);
  assert.match(spec, /AGI Dossier/);
  assert.match(spec, /Fusion Demonstrator/);
  assert.doesNotMatch(spec, /Economic Benchmark/);
  assert.doesNotMatch(spec, /Market Access/);
  assert.doesNotMatch(spec, /Influence cube/);
  assert.match(spec, /Initiative/);
  assert.match(spec, /visibly numbered 1–4/);
  assert.match(spec, /Latest Production snapshot/);
  assert.match(spec, /Thirty-six shared silver cubes/);
  assert.match(spec, /Two distinct shared tokens/);

  assert.match(inventory, /## One prepacked faction tray per player/);
  assert.match(inventory, /## Advanced module/);
  assert.match(inventory, /8 Advanced-badged Headline cards/);
  assert.match(inventory, /12 Link tokens/);
  assert.match(inventory, /6 four-way Realignment ballot cards/);
  assert.match(inventory, /1 ordinary six-sided Volatility die/);
  assert.match(inventory, /No component tracks Network capacity/);
  assert.match(inventory, /six captive sliders/);
  assert.match(inventory, /6 shared Program cards/);
  assert.match(inventory, /twelve Program markers/);
  assert.match(inventory, /6 foldout player aids/);
  assert.match(inventory, /36 silver Power cubes/);
  assert.match(inventory, /2 distinct Temporary Compute tokens/);
  assert.doesNotMatch(inventory, /final production copy count remains open/);
  assert.doesNotMatch(inventory, /Unresolved packing quantities/);
  assert.match(governanceLedger, /Current Mandate/);
  assert.match(governanceLedger, /Criterion value or status/);
  assert.match(governanceLedger, /Setup Collective Trust/);
  assert.match(governanceLedger, /Unresolved Systemic Risk/);
  assert.match(governanceLedger, /Final institutional winner/);
  assert.match(governanceLedger, /World Ending/);
  assert.match(governanceLedger, /Do not transcribe Power/);

  for (const staleClaim of [
    "Approximately 190 baseline cards",
    "approximately 188 plus player references",
    "180 Default or 194 with Advanced",
    "older rules release",
    "Four shared ordinary Power Source references"
  ]) {
    assert.ok(!manufacturing.includes(staleClaim), `manufacturing retires ${staleClaim}`);
  }
  assert.match(manufacturing, /140 Default or 154 with Advanced/);
  assert.match(manufacturing, /Advanced Play adds six four-way Realignment ballots/);
  assert.match(manufacturing, /Three Power contracts remain in the rules without separate cards/);

  const mapSurface = manifest.surfaces.find((surface) => surface.id === "map_tile_types");
  assert.equal(mapSurface.physicalCopies, 19);
  const governanceLedgerSurface = manifest.surfaces.find(
    (surface) => surface.id === "governance_ledger"
  );
  assert.equal(governanceLedgerSurface.physicalCopies, 1);
  assert.equal(
    manifest.surfaces.find((surface) => surface.id === "player_aid_panels").physicalCopies,
    6
  );
});

test("release artifacts are immutable once a version path exists", async () => {
  const directory = await mkdtemp(join(tmpdir(), "mandate-2038-release-artifact-"));
  const path = join(directory, "test-version", "manifest.json");
  try {
    assert.equal(await writeImmutableArtifact(path, "first\n"), true);
    assert.equal(await writeImmutableArtifact(path, "first\n"), false);
    await assert.rejects(
      writeImmutableArtifact(path, "different\n"),
      /Refusing to overwrite immutable release artifact/
    );
    assert.equal(await readFile(path, "utf8"), "first\n");
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("complexity-reduction review rules preserve precision and remove table accounting", async () => {
  const [rules, mapReference, componentReference, advanced] = await Promise.all([
    readFile(new URL("dist/docs/core-rules.md", root), "utf8"),
    readFile(new URL("dist/docs/map-reference.md", root), "utf8"),
    readFile(new URL("dist/docs/component-reference.md", root), "utf8"),
    readFile(new URL("dist/docs/advanced-play.md", root), "utf8")
  ]);
  const normalizedRules = [rules, mapReference, componentReference, advanced].join("\n").replace(/\s+/g, " ");
  for (const clause of [
    "**Rules version:** 0.8.0-rc.3-test",
    "synchronized with executable game 0.14.2",
    "Political control uses the CEO, Teams, and Facilities already on the board",
    "cards without an **Advanced Play** badge",
    "A Mega-Cluster uses two adjacent Facilities you own",
    "Each Facility may host at most one Mega-Cluster",
    "The starting grid powers only its assigned first Facility",
    "Facility at the acting piece’s destination",
    "Every cross-player contract or jointly funded project requires the explicit",
    "Facilities sharing one hex are **co-located**. Adjacent host Facilities occupy hexes that share an edge",
    "### Universal costs and caps",
    "integrated starting-grid identifier",
    "Every piece placed on the board during setup begins at Frontier",
    "Use nineteen tiles in a complete radius-two hexagon",
    "Every outer district touches its two outer neighbors",
    "These ring pools are fixed; shuffle tiles only within their listed ring",
    "All copies of one named district are mechanically identical",
    "Every player board presents the same five Production boxes",
    "Leave these cubes until the next Allocate step",
    "No separate Power Source cards are used",
    "Each moving tile carries every CEO, Team, Facility, Generator, Link",
    "A Pass names no motion",
    "Default Game makes no Power purchase request",
    "In Advanced Play, each player may make one request",
    "The secret AGI Dossier",
    "There is no Prediction Bag",
    "Do not run a second Production calculation",
    "Every Headline card is eligible",
    "Every Faction has one persistent institutional identity and one signature ability",
    "each applicable Faction modifier",
    "There is no hidden or deferred conversion",
    "There is no other endgame scoring"
  ]) {
    assert.ok(normalizedRules.includes(clause), `canonical rules include ${clause}`);
  }
  assert.ok(!normalizedRules.includes("simultaneous capacity proof"));
  assert.ok(!normalizedRules.includes("notional transfer counts"));
  assert.ok(!normalizedRules.includes("Upgrade a Facility"));
  assert.ok(!normalizedRules.includes("Power Purchase Agreement"));
});

test("complexity positioning stays broad, unmeasured, and profile-scoped", async () => {
  const [comparisons, decisions, manufacturing] = await Promise.all([
    readFile(new URL("docs/comparisons.md", root), "utf8"),
    readFile(new URL("docs/design-decisions.md", root), "utf8"),
    readFile(new URL("docs/manufacturing-and-publishing-study.md", root), "utf8")
  ]);

  assert.match(comparisons, /Default Game is designed as \*\*upper-medium\*\*/);
  assert.match(comparisons, /`3\.0–3\.4`/);
  assert.match(comparisons, /`3\.6–4\.0`/);
  assert.match(comparisons, /broad positioning hypotheses, not\s+community ratings/);
  assert.match(comparisons, /No current evidence supports a narrower Weight estimate/);
  assert.doesNotMatch(comparisons, /`3\.0–3\.2`/);
  assert.match(manufacturing, /ages 14\+, upper-medium strategy/);
  assert.match(decisions, /Presentation cannot create a new phase/);
  assert.match(decisions, /Production remains the five numbered boxes,\s+followed by the separate Audit and Mandate phases/);
});

test("the thematic inventory matches the two-source Power contract", async () => {
  const bible = await readFile(new URL("docs/thematic-content-bible.md", root), "utf8");
  assert.match(bible, /## Player-copy design inventory/);
  assert.match(bible, /## Physical quantity interpretation/);
  assert.match(bible, /Foldout player aids \| 6 copies containing all 4 panels/);
  assert.match(bible, /Shared Program cards \/ player Program markers \| 6 \/ 12/);
  assert.match(bible, /Printed Power contracts \| 3 embedded surfaces/);
  assert.match(bible, /No replacement\n+or overage allowance has been selected yet/);
  assert.match(bible, /Ordinary Power contracts \| 2 location-defined contracts/);
  assert.doesNotMatch(bible, /Ordinary Power contracts \| 4/);
  assert.match(bible, /Scrutiny cubes \/ captive faction-board sliders \| 60 \/ 36/);
  assert.match(bible, /Mandate markers \/ AGI Dossier cards \| 6 \/ 24/);
  assert.match(bible, /Starting-grid identities \| 6 Facilities carry this identity/);
  assert.doesNotMatch(bible, /Scrutiny \/ Customer markers \| 60 \/ 30/);
});

test("selected deck contracts have exact physical counts", async () => {
  const [config, tactics, escalation, headlines, mandates] = await Promise.all([
    readJson("dist/runtime/game-config.json"),
    readJson("dist/runtime/tactics.json"),
    readJson("dist/runtime/escalations.json"),
    readJson("dist/runtime/headlines.json"),
    readJson("dist/runtime/mandates.json")
  ]);

  const trainingCount = config.trainingDeck.cards.reduce((sum, card) => sum + card.count, 0);
  assert.equal(trainingCount, 40);
  assert.equal(tactics.tactics.length * tactics.copiesPerCard, 36);
  assert.equal(escalation.escalations.length, 6);
  assert.equal(escalation.cardsPerPlayer, 0);
  assert.equal(escalation.sharedCardCount, 6);
  const defaultHeadlineCount = headlines.headlines.filter(
    (headline) => !headline.requiredRuleModules?.length
  ).length;
  assert.deepEqual(
    [1, 2, 3, 4].map((era) =>
      headlines.headlines.filter(
        (headline) => headline.round === era && !headline.requiredRuleModules?.length
      ).length
    ),
    [5, 4, 3, 4]
  );
  assert.deepEqual(
    [1, 2, 3, 4].map((era) =>
      headlines.headlines.filter(
        (headline) => headline.round === era && headline.requiredRuleModules?.length
      ).length
    ),
    [1, 2, 3, 2]
  );
  const defaultStandardCards =
    config.playerSupply.coreActionCards * config.players.max +
    config.sharedSupply.sharedProgramCards +
    defaultHeadlineCount +
    mandates.mandates.length +
    trainingCount +
    config.playerSupply.agiDossierCards * config.players.max;
  const defaultPrintedPieces = defaultStandardCards + config.sharedSupply.playerAidFoldouts;
  const advancedPrintedPieces =
    defaultPrintedPieces +
    (headlines.headlines.length - defaultHeadlineCount) +
    config.playerSupply.realignmentBallotCards * config.players.max;
  assert.equal(defaultStandardCards, 134);
  assert.equal(defaultPrintedPieces, 140);
  assert.equal(advancedPrintedPieces, 154);
  assert.deepEqual(
    config.powerSources.filter((source) => !source.isProgram).map((source) => source.id),
    ["clean_infrastructure", "emergency_infrastructure"]
  );
  for (const source of config.powerSources.filter((candidate) => !candidate.isProgram)) {
    assert.equal(
      source.runwayCost,
      config.singleGeneratorRule.locations[source.location].constructionCost,
      `${source.id} projects its authoritative location cost`
    );
  }
  assert.deepEqual(
    Object.fromEntries(config.powerSources.map((source) => [source.id, source.physicalSurface])),
    {
      clean_infrastructure: "renewable_basin_tile",
      emergency_infrastructure: "grid_reactor_tile",
      fusion_demonstrator: "fusion_demonstrator_program"
    }
  );
  assert.deepEqual(config.playerSupply.facilityConstructionOrder, [1, 2, 3, 4]);
  assert.deepEqual(
    {
      governanceBoardEraPanels: config.sharedSupply.governanceBoardEraPanels,
      currentEraMarkers: config.sharedSupply.currentEraMarkers,
      playerAidFoldouts: config.sharedSupply.playerAidFoldouts,
      governanceLedgers: config.sharedSupply.governanceLedgers,
      sharedDryEraseMarkers: config.sharedSupply.sharedDryEraseMarkers,
      powerAllocationMarkers: config.sharedSupply.powerAllocationMarkers,
      temporaryComputeTokens: config.sharedSupply.temporaryComputeTokens,
      mandateMarkers: config.sharedSupply.mandateMarkers
    },
    {
      governanceBoardEraPanels: 4,
      currentEraMarkers: 1,
      playerAidFoldouts: 6,
      governanceLedgers: 1,
      sharedDryEraseMarkers: 1,
      powerAllocationMarkers: 36,
      temporaryComputeTokens: 2,
      mandateMarkers: 6
    }
  );
});

test("core action and shared Program contracts stay singular", async () => {
  const config = await readJson("dist/runtime/game-config.json");
  assert.deepEqual(
    config.actions.map((action) => action.id),
    ["fund", "research", "build", "organize", "deploy", "influence"]
  );
  assert.deepEqual(config.rounds.map((round) => round.cycles), [3, 3, 3, 3]);
  assert.deepEqual(config.rounds.map((round) => round.programUses), [0, 1, 1, 2]);
  assert.ok(config.rounds[3].escalations.includes("fusion_demonstrator"));
});

test("factions and player supplies match the selected limits", async () => {
  const config = await readJson("dist/runtime/game-config.json");
  const factions = await readJson("dist/runtime/factions.json");

  assert.equal(factions.factions.length, 6);
  assert.equal(new Set(factions.factions.map((faction) => faction.id)).size, 6);
  assert.deepEqual(
    {
      teams: config.playerSupply.teams,
      facilities: config.playerSupply.facilities,
      generators: config.playerSupply.generators,
      linkTokens: config.playerSupply.linkTokens,
      influenceCubes: config.playerSupply.influenceCubes,
      scrutinyCubes: config.playerSupply.scrutinyCubes,
      factionBoardCaptiveSliders: config.playerSupply.factionBoardCaptiveSliders,
      programMarkers: config.playerSupply.programMarkers,
      realignmentBallotCards: config.playerSupply.realignmentBallotCards,
      agiDossierCards: config.playerSupply.agiDossierCards,
      startingGridIdentifiers: config.playerSupply.startingGridIdentifiers
    },
    {
      teams: 3,
      facilities: 4,
      generators: 1,
      linkTokens: 2,
      influenceCubes: 0,
      scrutinyCubes: 10,
      factionBoardCaptiveSliders: 6,
      programMarkers: 2,
      realignmentBallotCards: 1,
      agiDossierCards: 4,
      startingGridIdentifiers: 1
    }
  );
  for (const staleField of [
    "customerMarkers",
    "escalationTokens",
    "agiDeclarationCards",
    "agiDeclarationMarkers",
    "startingGridMarkers",
    "jointVentureMarkers",
    "megaClusterMarkers",
    "networkMarkers",
    "networkTrackMarkers",
    "customerTrackMarkers",
    "escalationTrackMarkers",
    "advancedNetworkCaptiveSliders",
    "realignmentBallots"
  ]) assert.ok(!(staleField in config.playerSupply), `playerSupply retires ${staleField}`);

  const allowedTiming = new Set(factions.abilityTimingContract.allowedTiming);
  for (const faction of factions.factions) {
    assert.equal(faction.abilities.length, 2);
    for (const ability of faction.abilities) {
      assert.ok(ability.id, `${faction.id} ability has a stable id`);
      assert.ok(allowedTiming.has(ability.timing), `${faction.id}/${ability.id} has a timing tag`);
      assert.equal(typeof ability.persistsAfterUnlock, "boolean");
    }
  }

  const platform = factions.factions.find((faction) => faction.id === "platform_empire");
  assert.equal(platform.starts.customers, 1);
  assert.equal(platform.starts.customerOrdinal, 1);
  assert.equal(platform.starts.nextCustomerCapability, 4);

  const vertical = factions.factions.find((faction) => faction.id === "vertical_empire");
  const imperial = factions.factions.find(
    (faction) => faction.id === "imperial_research_lab"
  );
  const safety = factions.factions.find((faction) => faction.id === "safety_laboratory");
  assert.equal(platform.starts.startingPublicMandate, 4);
  assert.equal(imperial.starts.startingPublicMandate, 2);
  assert.equal(vertical.starts.startingPublicMandate, 2);
  assert.equal(safety.starts.startingPublicMandate, 4);
});

test("faction truth constrains balance without becoming a point-buy budget", async () => {
  const factions = await readJson("dist/runtime/factions.json");
  const balance = await readJson("lab/contracts/balance-contract.json");
  const truth = factions.factionTruthContract;
  const factionIds = factions.factions.map((faction) => faction.id);
  const dimensionIds = Object.keys(truth.dimensions);

  assert.equal(truth.status, "selected_design_constraint");
  assert.equal(truth.scale.minimum, 1);
  assert.equal(truth.scale.maximum, 5);
  assert.deepEqual(Object.keys(truth.profiles), factionIds);
  assert.equal(balance.factionTruth.source, "dist/runtime/factions.json#factionTruthContract");
  assert.equal(balance.factionTruth.requiredForRuleProbe, true);

  for (const factionId of factionIds) {
    const profile = truth.profiles[factionId];
    assert.deepEqual(Object.keys(profile.ratings), dimensionIds);
    assert.ok(profile.protectedStrength);
    assert.ok(profile.balanceBottleneck);
    assert.ok(profile.forbiddenCorrection);
    for (const rating of Object.values(profile.ratings)) {
      assert.ok(rating >= truth.scale.minimum && rating <= truth.scale.maximum);
    }
  }
});

test("Faction boards project into Card and Board Reference without duplicating their card text in Default Rules", async () => {
  const factions = await readJson("dist/runtime/factions.json");
  const [rules, cardReference] = await Promise.all([
    readFile(resolve(projectRoot, "dist/docs/core-rules.md"), "utf8"),
    readFile(resolve(projectRoot, "dist/docs/card-reference.md"), "utf8")
  ]);

  for (const faction of factions.factions) {
    if (faction.scoringRule) {
      assert.ok(faction.scoringRule.text, `${faction.id} owns scoring text`);
      assert.ok(!rules.includes(faction.scoringRule.text));
      assert.ok(cardReference.includes(faction.scoringRule.text));
    }
    for (const ability of faction.abilities) {
      assert.ok(ability.text, `${faction.id}/${ability.name} owns card text`);
      assert.ok(!rules.includes(ability.text));
      assert.ok(cardReference.includes(ability.text));
    }
  }

  assert.match(rules, /one persistent institutional identity and one\s+signature ability/);
  assert.match(rules, /use each Faction board’s printed starts/);
  assert.doesNotMatch(rules, /Scientific Method:/);
  assert.doesNotMatch(rules, /Industrial Velocity:/);
});

test("headline and board boundaries remain explicit", async () => {
  const config = await readJson("dist/runtime/game-config.json");
  const headlines = await readJson("dist/runtime/headlines.json");

  assert.equal(headlines.headlines.length, 24);
  for (const round of [1, 2, 3, 4]) {
    assert.equal(headlines.headlines.filter((headline) => headline.round === round).length, 6);
  }
  const expandedTiles = config.board.tiles.reduce((sum, tile) => sum + tile.count, 0);
  assert.equal(config.board.selectedTileCount, 19);
  assert.equal(expandedTiles, config.board.prototypeTileCount);
  assert.equal(expandedTiles, 19);
  assert.equal(config.board.tiles.find((tile) => tile.id === "consumer").count, 2);
  assert.equal(
    config.board.tiles.filter((tile) => tile.category === "energy")
      .reduce((sum, tile) => sum + tile.count, 0),
    3
  );
  assert.equal(config.board.startingGridConnection.capacity, 1);
  assert.deepEqual(config.playRuleDefaults, {
    immediateTradeCounteroffers: false,
    immediateTradeThirdPartyClaims: false,
    powerPurchaseRequests: 0,
    realignmentEnabled: false,
    networkInfrastructureEnabled: false,
    headlinePersistentEffectsEnabled: false,
    headlinePublicProceduresEnabled: false,
    headlineVolatilityEnabled: false
  });
  assert.deepEqual(
    Object.fromEntries(
      Object.entries(config.playRuleModules).map(([id, module]) => [id, module.settings])
    ),
    {
      "advanced-power-market": { powerPurchaseRequests: 1 },
      "jurisdictional-realignment": { realignmentEnabled: true },
      "network-infrastructure": { networkInfrastructureEnabled: true },
      "headline-persistence": { headlinePersistentEffectsEnabled: true },
      "headline-public-procedures": { headlinePublicProceduresEnabled: true },
      "headline-volatility": { headlineVolatilityEnabled: true }
    }
  );
  assert.deepEqual(config.playProfiles, {
    defaultGame: {
      id: "default-game",
      moduleIds: [],
      name: "Default Game",
      summary: "The primary four-Era game: one optional 1-for-1 resource trade before resolution, local Power, immediate Headlines, and a static nineteen-district jurisdiction."
    },
    advancedPlay: {
      id: "advanced-play",
      moduleIds: [
        "advanced-power-market",
        "jurisdictional-realignment",
        "network-infrastructure",
        "headline-persistence",
        "headline-public-procedures",
        "headline-volatility"
      ],
      name: "Advanced Play",
      summary: "The bundled Advanced profile adds connected Networks, one Production Power request, procedural and persistent Headlines, Volatility, and Era III Jurisdictional Realignment."
    }
  });
  const register = await readJson("dist/runtime/rule-change-register.json");
  const implementedModuleIds = register.changes
    .filter((change) => change.implementation === "implemented")
    .flatMap((change) => change.moduleIds)
    .sort();
  assert.deepEqual(Object.keys(config.playRuleModules).sort(), implementedModuleIds);
  for (const profile of Object.values(config.playProfiles)) {
    for (const moduleId of profile.moduleIds) {
      assert.ok(implementedModuleIds.includes(moduleId));
    }
  }
  const acceptedSimplifications = register.changes
    .filter((change) => [
      "equal-presence-control",
      "single-generator-default",
      "shared-program-display",
      "research-protection-refresh",
      "deterministic-dossier",
      "nineteen-hex-board",
      "simplified-profile-boundary"
    ].includes(change.id) && change.status.id === "accepted_current")
    .map((change) => change.id)
    .sort();
  assert.deepEqual(acceptedSimplifications, [
    "deterministic-dossier",
    "equal-presence-control",
    "nineteen-hex-board",
    "research-protection-refresh",
    "shared-program-display",
    "simplified-profile-boundary",
    "single-generator-default"
  ]);
  assert.ok(
    acceptedSimplifications.every(
      (id) => !Object.values(config.playProfiles).some((profile) => profile.moduleIds.includes(id))
    ),
    "canonical simplifications do not masquerade as optional modules"
  );
  assert.deepEqual(
    config.board.realignment.motions.map((motion) => motion.id),
    ["consolidate_core", "expand_periphery", "counter_cycle"]
  );
  assert.deepEqual(config.board.realignment.ballot, {
    cardsPerPlayer: 1,
    orientationChoices: [
      "consolidate_core",
      "expand_periphery",
      "counter_cycle",
      "pass"
    ],
    passChoice: "pass"
  });
  assert.equal(config.playerSupply.realignmentBallotCards, 1);
  assert.equal(config.playerSupply.factionBoardCaptiveSliders, 6);
  assert.equal(config.playerSupply.programMarkers, 2);
  assert.deepEqual(
    Object.fromEntries(config.board.tiles.map((tile) => [tile.id, tile.name])),
    {
      frontier: "Frontier",
      research: "Research Commons",
      cloud: "Compute Estate",
      consumer: "Human Access District",
      foundry: "Fabrication Corridor",
      capital: "Allocation Exchange",
      talent: "Workforce Transition District",
      media: "Consensus Network",
      government: "Civic Permission Authority",
      grid_reactor: "Power Corridor",
      renewable_basin: "Thermal and Water Basin"
    }
  );
  assert.match(
    config.board.tiles.find((tile) => tile.id === "frontier").flavorText,
    /standing civic exception/
  );
  assert.match(
    config.board.tiles.find((tile) => tile.id === "research").flavorText,
    /Publicly chartered inquiry/
  );
  for (const tile of config.board.tiles) {
    assert.equal(
      Object.values(tile.placement).reduce((sum, count) => sum + count, 0),
      tile.count,
      `${tile.id} placement matches physical count`
    );
  }
  for (const motion of config.board.realignment.motions) {
    for (const field of ["name", "ballotText", "flavorText"]) {
      assert.ok(motion[field], `${motion.id} has ${field}`);
    }
  }
  assert.equal(
    config.board.tiles.reduce(
      (sum, tile) => sum + Object.values(tile.placement).reduce((total, count) => total + count, 0),
      0
    ),
    19
  );

  const blogPost = headlines.headlines.find((headline) => headline.id === "agi_blog_post");
  assert.match(blogPost.text, /receives 2 Publication strength instead of 1/);
  assert.match(blogPost.text, /does not change Dossier payment, Scrutiny/);
});

test("Headline deck preserves eight anchors and sixteen future regimes", async () => {
  const { headlines, resolutionContract } = await readJson("dist/runtime/headlines.json");
  const ids = new Set(headlines.map((headline) => headline.id));
  const anchors = [
    "open_weights_drop",
    "talent_gold_rush",
    "boardroom_coup",
    "export_controls",
    "weights_on_internet",
    "election_deepfake_panic",
    "agent_swarm_escapes_scope",
    "agi_blog_post"
  ];
  const replacements = [
    "ten_dollar_intelligence",
    "employee_free_unicorn",
    "synthetic_celebrity",
    "professional_exam_sweep",
    "data_center_buys_county",
    "humanoid_factory_gate",
    "reactor_restart_one_model",
    "emergency_power_authority",
    "ai_written_law",
    "benchmark_is_economy",
    "quantum_advantage_procurement",
    "synthetic_candidate",
    "autonomous_corporation",
    "recursive_self_improvement",
    "agi_personhood",
    "room_temperature_superconductor"
  ];
  const retired = [
    "chatbot_breakout",
    "gpu_backorder",
    "cloud_credits",
    "voluntary_safety_commitments",
    "employee_open_letter",
    "year_of_efficiency",
    "product_feature_paused",
    "supercluster_online",
    "copyright_injunction",
    "benchmark_leak",
    "talent_exodus",
    "search_answer_viral",
    "million_gpu_order",
    "national_compute_reserve",
    "synthetic_feedback_loop",
    "power_grid_backlash"
  ];

  for (const id of [...anchors, ...replacements]) assert.ok(ids.has(id), `${id} is in the selected deck`);
  for (const id of retired) assert.ok(!ids.has(id), `${id} is retired`);
  assert.equal(anchors.filter((id) => ids.has(id)).length, 8);
  assert.equal(replacements.filter((id) => ids.has(id)).length, 16);

  for (const field of [
    "revealTiming",
    "defaultDuration",
    "directive",
    "secretAuction",
    "governmentVote",
    "secretChoice",
    "volatility",
    "modifierLimit",
    "timings"
  ]) {
    assert.ok(resolutionContract[field], `Headline resolution defines ${field}`);
  }
  assert.match(resolutionContract.secretAuction, /highest positive bid/);
  assert.match(resolutionContract.directive, /no separate choice procedure/);
  assert.match(resolutionContract.governmentVote, /counts twice/);
  assert.match(resolutionContract.modifierLimit, /never grants an additional Action/);

  const byId = Object.fromEntries(headlines.map((headline) => [headline.id, headline]));
  const allowedResolutionTypes = new Set([
    "DIRECTIVE",
    "SECRET CHOICE",
    "CIVIC PERMISSION AUTHORITY VOTE",
    "AUCTION",
    "VOLATILITY"
  ]);
  assert.ok(
    headlines.every((headline) => allowedResolutionTypes.has(headline.resolutionType)),
    "every Headline has exactly one supported resolution type"
  );
  assert.equal(byId.talent_gold_rush.name, "Research Talent Receives Diplomatic Status");
  assert.ok(
    headlines.every((headline) => headline.resolutionType !== "REGIME"),
    "standard Headline instructions use the procedural DIRECTIVE badge"
  );
  assert.match(byId.emergency_power_authority.text, /Systemic Risk/);
  assert.match(byId.benchmark_is_economy.text, /immediately scores 1 Mandate/);
  assert.match(byId.autonomous_corporation.text, /No additional Action resolves/);
  assert.match(byId.agi_personhood.text, /remainder of the game/);
  assert.match(byId.agi_personhood.text, /gains 2 Trust/);
  assert.match(byId.boardroom_coup.text, /cannot be chosen as that leader’s acting piece/);
  assert.match(byId.room_temperature_superconductor.text, /1–3 Fraud; 4–6 Replicates/);
  assert.doesNotMatch(byId.room_temperature_superconductor.text, /Link|Fusion|discount/);
  assert.ok(
    headlines.every((headline) => !headline.regimeTags.includes("bonus_action")),
    "Agent Swarm remains the only compound Action surface"
  );
  assert.equal(
    byId.agent_swarm_escapes_scope.name,
    "Posthumous Labor Continuation"
  );
  assert.equal(
    byId.room_temperature_superconductor.name,
    "Entanglement Custody"
  );
});

test("the tone constitution keeps darkness institutional rather than voyeuristic", async () => {
  const [world, thematicBible] = await Promise.all([
    readFile(new URL("dist/docs/world-and-institutions.md", root), "utf8"),
    readFile(new URL("docs/thematic-content-bible.md", root), "utf8")
  ]);

  const bible = thematicBible.replace(/\s+/g, " ");
  const companion = world.replace(/\s+/g, " ");
  assert.match(bible, /Write consequences at institutional distance/);
  assert.match(bible, /Do not depict first-person torment, body horror, or voyeuristic suffering/);
  assert.match(companion, /The Future Timeline is one compounding public record/);
  assert.doesNotMatch(companion, /\*\*Interpretation\.\*\*/);
});

test("every player-facing content surface has complete copy", async () => {
  const [config, factions, headlines, tactics, escalation, references] = await Promise.all([
    readJson("dist/runtime/game-config.json"),
    readJson("dist/runtime/factions.json"),
    readJson("dist/runtime/headlines.json"),
    readJson("dist/runtime/tactics.json"),
    readJson("dist/runtime/escalations.json"),
    readJson("dist/runtime/reference-cards.json")
  ]);

  for (const era of references.eraCards) {
    for (const field of ["name", "strapline", "loreText", "rulesText", "unlockText"]) {
      assert.ok(era[field], `${era.id} has ${field}`);
    }
  }
  for (const action of config.actions) {
    for (const field of ["initiativeName", "slogan", "flavorText"]) {
      assert.ok(action[field], `${action.id} has ${field}`);
    }
  }
  for (const tile of config.board.tiles) {
    for (const field of ["landmark", "flavorText"]) {
      assert.ok(tile[field], `${tile.id} has ${field}`);
    }
  }
  for (const card of config.trainingDeck.cards) {
    for (const field of ["name", "rulesText", "flavorText"]) {
      assert.ok(card[field], `${card.id} has ${field}`);
    }
  }
  for (const source of config.powerSources) {
    for (const field of ["tagline", "rulesText", "publicClaim"]) {
      assert.ok(source[field], `${source.id} has ${field}`);
    }
  }
  for (const faction of factions.factions) {
    for (const field of ["motto", "publicPromise", "privateAnxiety", "introduction", "victoryStatement", "agiDeclaration"]) {
      assert.ok(faction[field], `${faction.id} has ${field}`);
    }
    for (const ability of faction.abilities) {
      for (const field of ["displayName", "flavorText"]) {
        assert.ok(ability[field], `${faction.id}/${ability.name} has ${field}`);
      }
    }
  }
  for (const headline of headlines.headlines) {
    for (const field of ["strapline", "newswire", "quote", "regimeTags"]) {
      assert.ok(headline[field], `${headline.id} has ${field}`);
    }
    assert.ok(headline.regimeTags.length >= 3, `${headline.id} has meaningful regime tags`);
  }
  for (const tactic of tactics.tactics) {
    for (const field of ["displayName", "flavorText", "technology"]) {
      assert.ok(tactic[field], `${tactic.id} has ${field}`);
    }
  }
  for (const action of escalation.escalations) {
    for (const field of ["displayName", "flavorText"]) {
      assert.ok(action[field], `${action.id} has ${field}`);
    }
  }
});

test("new thematic decks and reference surfaces have complete draft inventories", async () => {
  const mandates = await readJson("dist/runtime/mandates.json");
  const objectives = await readJson("dist/runtime/secret-objectives.json");
  const references = await readJson("dist/runtime/reference-cards.json");
  const reserve = await readJson("dist/runtime/reserve-specialists.json");
  const tactics = await readJson("dist/runtime/tactics.json");
  const [world, factions] = await Promise.all([
    readJson("dist/runtime/world-copy.json"),
    readJson("dist/runtime/factions.json")
  ]);
  const manifest = await readJson("dist/runtime/content-manifest.json");

  assert.equal(mandates.mandates.length, 12);
  assert.equal(objectives.objectives.length, 18);
  assert.equal(references.eraCards.length, 4);
  assert.equal(references.playerReferences.length, 4);
  assert.equal(reserve.specialists.length, 12);
  assert.equal(world.agiDeclarations, undefined);
  assert.equal(factions.factions.filter((faction) => faction.agiDeclaration).length, 6);
  assert.equal(world.endings.length, 4);
  assert.deepEqual(
    world.endings.map((ending) => ending.id),
    ["singularity", "closed_loop", "plural_future", "assured_continuity"]
  );
  assert.equal(world.tokenCopy.length, 10);

  for (const card of [...tactics.tactics, ...reserve.specialists, ...objectives.objectives]) {
    assert.ok([1, 2, 3, 4].includes(card.era), `${card.id} has an Era classification`);
  }

  const requiredCardFields = ["name", "rulesText", "flavorText"];
  for (const card of [...mandates.mandates, ...objectives.objectives]) {
    for (const field of requiredCardFields) assert.ok(card[field], `${card.id} has ${field}`);
  }

  const ids = manifest.surfaces.map((surface) => surface.id);
  assert.equal(ids.length, new Set(ids).size);
  assert.ok(manifest.surfaces.every((surface) => surface.status));
  assert.deepEqual(
    manifest.surfaces.filter((surface) => surface.file === null).map((surface) => surface.status).sort(),
    ["final_art_missing", "production_layout_missing"]
  );
});

test("prototype renders canonical names from faction data without a legacy reference layer", async () => {
  const app = await readFile(new URL("web/app.js", root), "utf8");
  assert.doesNotMatch(app, /faction\.historicalReference/);
  assert.match(app, /faction\.motto/);
});

test("browser renders canonical Headline copy and isolates Advanced Play realignment copy", async () => {
  const [app, engine, template, uiCopy] = await Promise.all([
    readFile(new URL("web/app.js", root), "utf8"),
    readFile(new URL("web/src/engine.js", root), "utf8"),
    readFile(new URL("web/templates/prototype.html", root), "utf8"),
    readJson("dist/runtime/ui-copy.json")
  ]);

  assert.match(app, /fetch\("\/dist\/runtime\/ui-copy\.json"\)/);
  assert.match(app, /copy\.browser\.startingStatus/);
  assert.doesNotMatch(app, /config\.board\.prototypeNote/);
  assert.doesNotMatch(engine, /prototypeNote/);
  for (const field of ["name", "strapline", "newswire", "text", "quote"]) {
    assert.match(app, new RegExp(`headline\\?\\.${field}|headline\\.${field}`));
    assert.match(template, new RegExp(`id="headline-${field === "text" ? "consequence" : field}"`));
  }
  assert.match(app, /profileFor\(game\?\.state\)\.realignmentEnabled/);
  assert.match(app, /copy\.realignment\.advancedTitle/);
  assert.match(app, /copy\.realignment\.prompt/);
  assert.match(template, /id="play-profile"><\/select>/);
  assert.doesNotMatch(template, /rc\.5-test|frontier-2038/);
  assert.match(uiCopy.prototype.browser.startingStatus, /deterministic browser opponents/);
  assert.equal(uiCopy.prototype.realignment.advancedTitle, "Advanced Play: Jurisdictional Realignment");
  assert.match(uiCopy.prototype.power.reminder, /^In Advanced Play,/);
});
