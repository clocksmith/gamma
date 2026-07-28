import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const root = new URL("../", import.meta.url);
const projectRoot = root.pathname;
const readJson = async (path) => JSON.parse(await readFile(new URL(path, root), "utf8"));

test("release index separates executable game from physical rules candidate", async () => {
  const current = await readJson("versions/current.json");
  const executable = await readJson(current.manifest);
  const candidate = await readJson(current.rulesCandidate.manifest);

  assert.equal(current.gameVersion, "0.8.19");
  assert.equal(executable.gameVersion, "0.8.19");
  assert.equal(current.rulesCandidate.version, "0.5.0-rc.20-test");
  assert.equal(candidate.artifactKind, "physical-rules-candidate");
  assert.equal(candidate.implementation.status, "synchronized");
  assert.equal(candidate.implementation.executableGameVersion, "0.8.19");
  assert.equal(candidate.implementation.implementedByGameVersion, "0.8.19");
  assert.notEqual(current.rulesetFingerprint, current.rulesCandidate.rulesFingerprint);
  assert.match(current.contentGraphFingerprint, /^sha256:[a-f0-9]{64}$/);
  assert.equal(executable.contentGraphFingerprint, current.contentGraphFingerprint);
  assert.equal(candidate.contentGraphFingerprint, current.contentGraphFingerprint);
  assert.ok(Object.hasOwn(executable.contentGraphFiles, "content/graph.json"));
  assert.ok(Object.hasOwn(executable.contentGraphFiles, "content/variables.json"));
  assert.ok(!Object.hasOwn(executable.files, "docs/core-rules.md"));
  assert.ok(!Object.hasOwn(executable.files, "data/simulation-copy.json"));
  assert.ok(Object.hasOwn(executable.kitFiles, "data/simulation-copy.json"));
  assert.ok(Object.hasOwn(candidate.files, "docs/core-rules.md"));
});

test("complexity-reduction review rules preserve precision and remove table accounting", async () => {
  const rules = await readFile(new URL("docs/core-rules.md", root), "utf8");
  const normalizedRules = rules.replace(/\s+/g, " ");
  for (const clause of [
    "**Rules version:** 0.5.0-rc.20-test",
    "synchronized with executable game 0.8.19",
    "Influence may place or relocate one additional cube on Government",
    "only if the Headline explicitly instructs the table",
    "A **solo Mega-Cluster**",
    "A **joint Mega-Cluster**",
    "Infrastructure Network exists from setup",
    "Facility at the acting piece’s destination",
    "Every cross-player contract or jointly funded project requires the explicit",
    "Facilities sharing one hex are **co-located**, not adjacent",
    "### Universal costs and caps",
    "temporary Compute remaining anywhere at cycle end disappears",
    "One starting-grid marker",
    "When choosing Organize’s Recruit mode this cycle",
    "From this vote until round end",
    "each Customer gained after this vote",
    "Fusion counts as an owned Generator for Infrastructure Network connection",
    "does not count against the owner’s two ordinary Generator-piece limit",
    "Every piece placed on the board during setup begins at Frontier",
    "Every player board presents the same five Production boxes",
    "Ring rotation moves the district, not the Facility for Grid-Ready purposes",
    "return a Grid-Ready marker only from a Facility that is now outside",
    "each player may buy up to two Power",
    "A **grid-ready Facility** has a Grid-Ready marker",
    "it never runs a second Production calculation",
    "Every Headline has exactly one resolution badge",
    "Every faction board uses the same four-row reading order",
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

test("the thematic inventory matches the two-source Power contract", async () => {
  const bible = await readFile(new URL("docs/thematic-content-bible.md", root), "utf8");
  assert.match(bible, /Ordinary Power Sources \| 2 shared reference types/);
  assert.doesNotMatch(bible, /Ordinary Power Sources \| 4 reference types/);
});

test("selected deck contracts have exact physical counts", async () => {
  const config = await readJson("data/game-config.json");
  const tactics = await readJson("data/tactics.json");
  const wild = await readJson("data/wild-actions.json");

  const trainingCount = config.trainingDeck.cards.reduce((sum, card) => sum + card.count, 0);
  assert.equal(trainingCount, 50);
  assert.equal(tactics.tactics.length * tactics.copiesPerCard, 36);
  assert.equal(wild.wildActions.length, 7);
  assert.equal(wild.cardsPerPlayer, 7);
  assert.deepEqual(
    config.powerSources.filter((source) => !source.wildAction).map((source) => source.id),
    ["clean_infrastructure", "emergency_infrastructure"]
  );
});

test("core action and escalation contracts stay singular", async () => {
  const config = await readJson("data/game-config.json");
  assert.deepEqual(
    config.actions.map((action) => action.id),
    ["fund", "research", "build", "organize", "deploy", "influence"]
  );
  assert.deepEqual(config.rounds.map((round) => round.cycles), [3, 3, 3, 3]);
  assert.deepEqual(config.rounds.map((round) => round.escalationTokens), [0, 1, 1, 2]);
  assert.ok(config.rounds[3].wildActions.includes("fusion_demonstrator"));
});

test("factions and player supplies match the selected limits", async () => {
  const config = await readJson("data/game-config.json");
  const factions = await readJson("data/factions.json");

  assert.equal(factions.factions.length, 6);
  assert.equal(new Set(factions.factions.map((faction) => faction.id)).size, 6);
  assert.deepEqual(
    {
      teams: config.playerSupply.teams,
      facilities: config.playerSupply.facilities,
      generators: config.playerSupply.generators,
      linkTokens: config.playerSupply.linkTokens,
      networkMarkers: config.playerSupply.networkMarkers,
      influenceCubes: config.playerSupply.influenceCubes,
      scrutinyCubes: config.playerSupply.scrutinyCubes
    },
    {
      teams: 3,
      facilities: 4,
      generators: 2,
      linkTokens: 2,
      networkMarkers: 1,
      influenceCubes: 8,
      scrutinyCubes: 10
    }
  );

  const allowedTiming = new Set(factions.abilityTimingContract.allowedTiming);
  for (const faction of factions.factions) {
    for (const ability of faction.abilities) {
      assert.ok(allowedTiming.has(ability.timing), `${faction.id}/${ability.name} has a timing tag`);
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
  const factions = await readJson("data/factions.json");
  const balance = await readJson("simulation/contracts/balance-contract.json");
  const truth = factions.factionTruthContract;
  const factionIds = factions.factions.map((faction) => faction.id);
  const dimensionIds = Object.keys(truth.dimensions);

  assert.equal(truth.status, "selected_design_constraint");
  assert.equal(truth.scale.minimum, 1);
  assert.equal(truth.scale.maximum, 5);
  assert.deepEqual(Object.keys(truth.profiles), factionIds);
  assert.equal(balance.factionTruth.source, "data/factions.json#factionTruthContract");
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

test("physical faction rules are rendered from the semantic faction graph", async () => {
  const factions = await readJson("data/factions.json");
  const rules = await readFile(resolve(projectRoot, "docs/core-rules.md"), "utf8");

  for (const faction of factions.factions) {
    if (faction.scoringRule) {
      assert.ok(
        rules.includes(faction.scoringRule.text),
        `${faction.id}/${faction.scoringRule.name} must appear verbatim in the physical rules`
      );
    }
    for (const ability of faction.abilities) {
      assert.ok(
        rules.includes(ability.text),
        `${faction.id}/${ability.name} must appear verbatim in the physical rules`
      );
    }
  }

  assert.match(rules, /Demis Hassabis[\s\S]*Starts with 3[\s\S]*Compute,[\s\S]*Trust[\s\n]*3\./);
  assert.match(rules, /Scientific Method:[\s\S]*pay 1 Runway/);
  assert.match(rules, /Peer Validation:[\s\S]*Capability 9 and 12 score 1 Mandate/);
  assert.match(rules, /Elon Musk[\s\S]*Starts with 6[\s\S]*Runway, 3[\s\S]*Compute,[\s\S]*Trust[\s\n]*2\./);
  assert.doesNotMatch(
    rules,
    /Industrial Velocity:[\s\S]{0,240}add 1 Scrutiny/
  );
  assert.match(
    rules,
    /Industrial Velocity:[\s\S]{0,360}completed Facility,[\s\S]{0,80}score 1 Mandate/
  );
  assert.match(
    rules,
    /New Architecture:[\s\S]{0,520}Gain 1 Compute per rival who pays, maximum 3; automatic base gain: 0/
  );
  assert.match(
    rules,
    /Customers #1–3 immediately score two public Mandate[\s\S]{0,180}Customers #4–5 score one each/
  );
});

test("headline and board boundaries remain explicit", async () => {
  const config = await readJson("data/game-config.json");
  const headlines = await readJson("data/headlines.json");

  assert.equal(headlines.headlines.length, 24);
  for (const round of [1, 2, 3, 4]) {
    assert.equal(headlines.headlines.filter((headline) => headline.round === round).length, 6);
  }
  const expandedTiles = config.board.tiles.reduce((sum, tile) => sum + tile.count, 0);
  assert.equal(config.board.selectedTileCount, 13);
  assert.equal(config.board.inventoryStatus, "selected");
  assert.equal(expandedTiles, config.board.prototypeTileCount);
  assert.equal(expandedTiles, 13);
  assert.equal(config.board.tiles.find((tile) => tile.id === "consumer").count, 1);
  assert.equal(
    config.board.tiles.filter((tile) => tile.category === "energy")
      .reduce((sum, tile) => sum + tile.count, 0),
    2
  );
  assert.equal(config.board.startingGridConnection.capacity, 1);
  assert.deepEqual(
    config.board.realignment.motions.map((motion) => motion.id),
    ["consolidate_core", "expand_periphery", "counter_cycle"]
  );
  assert.equal(config.playerSupply.realignmentBallots, 3);
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
    13
  );

  const blogPost = headlines.headlines.find((headline) => headline.id === "agi_blog_post");
  assert.match(blogPost.text, /consumes the action slot and Escalation token/);
  assert.match(blogPost.text, /spends 3 Compute/);
  assert.match(blogPost.text, /flips the Wild Action/);
  assert.match(blogPost.text, /adds 3 Scrutiny/);
});

test("Headline deck preserves eight anchors and sixteen future regimes", async () => {
  const { headlines, resolutionContract } = await readJson("data/headlines.json");
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
    "open_weight_non_aligned",
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
    "GOVERNMENT VOTE",
    "AUCTION",
    "VOLATILITY"
  ]);
  assert.ok(
    headlines.every((headline) => allowedResolutionTypes.has(headline.resolutionType)),
    "every Headline has exactly one supported resolution type"
  );
  assert.equal(byId.talent_gold_rush.name, "Leading Researchers Receive Sovereign Status");
  assert.ok(
    headlines.every((headline) => headline.resolutionType !== "REGIME"),
    "standard Headline instructions use the procedural DIRECTIVE badge"
  );
  assert.match(byId.emergency_power_authority.text, /Systemic Risk/);
  assert.match(byId.benchmark_is_economy.text, /Economic Benchmark token/);
  assert.match(byId.autonomous_corporation.text, /No additional Action resolves/);
  assert.match(byId.agi_personhood.text, /remainder of the game/);
  assert.match(byId.agi_personhood.text, /Trust 4/);
  assert.match(byId.room_temperature_superconductor.text, /1–3 Fraud; 4–6 Replicates/);
  assert.ok(
    headlines.every((headline) => !headline.regimeTags.includes("bonus_action")),
    "Agent Swarm remains the only compound Action surface"
  );
  assert.equal(
    byId.agent_swarm_escapes_scope.name,
    "Agent Swarm Charters Its Own Jurisdictions"
  );
  assert.equal(
    byId.room_temperature_superconductor.name,
    "Yesterday’s Electricity Returns to the Grid"
  );
});

test("the tone constitution keeps darkness institutional rather than voyeuristic", async () => {
  const [rules, thematicBible] = await Promise.all([
    readFile(new URL("docs/core-rules.md", root), "utf8"),
    readFile(new URL("docs/thematic-content-bible.md", root), "utf8")
  ]);

  for (const document of [rules, thematicBible]) {
    const normalized = document.replace(/\s+/g, " ");
    assert.match(normalized, /Darkness is reported at institutional distance/);
    assert.match(normalized, /do not stage first-person torment, body horror, or voyeuristic suffering/);
    assert.match(normalized, /institutions treating harm as an administrable output/);
  }
});

test("every existing player-facing content surface has complete thematic copy", async () => {
  const config = await readJson("data/game-config.json");
  const factions = await readJson("data/factions.json");
  const headlines = await readJson("data/headlines.json");
  const tactics = await readJson("data/tactics.json");
  const wild = await readJson("data/wild-actions.json");

  for (const round of config.rounds) {
    for (const field of ["tagline", "flavorText", "artDirection"]) {
      assert.ok(round[field], `${round.id} has ${field}`);
    }
  }
  for (const action of config.actions) {
    for (const field of ["initiativeName", "slogan", "flavorText", "artDirection"]) {
      assert.ok(action[field], `${action.id} has ${field}`);
    }
  }
  for (const tile of config.board.tiles) {
    for (const field of ["landmark", "flavorText", "artDirection"]) {
      assert.ok(tile[field], `${tile.id} has ${field}`);
    }
  }
  for (const card of config.trainingDeck.cards) {
    for (const field of ["name", "flavorText", "artDirection"]) {
      assert.ok(card[field], `${card.id} has ${field}`);
    }
  }
  for (const source of config.powerSources) {
    for (const field of ["tagline", "publicClaim", "hiddenConsequence", "artDirection"]) {
      assert.ok(source[field], `${source.id} has ${field}`);
    }
  }
  for (const faction of factions.factions) {
    for (const field of ["motto", "publicPromise", "privateAnxiety", "introduction", "victoryStatement", "artDirection"]) {
      assert.ok(faction[field], `${faction.id} has ${field}`);
    }
    for (const ability of faction.abilities) {
      for (const field of ["displayName", "flavorText", "artDirection"]) {
        assert.ok(ability[field], `${faction.id}/${ability.name} has ${field}`);
      }
    }
  }
  for (const headline of headlines.headlines) {
    for (const field of ["strapline", "newswire", "quote", "artDirection", "regimeTags"]) {
      assert.ok(headline[field], `${headline.id} has ${field}`);
    }
    assert.ok(headline.regimeTags.length >= 3, `${headline.id} has meaningful regime tags`);
  }
  for (const tactic of tactics.tactics) {
    for (const field of ["displayName", "flavorText", "artDirection", "technology"]) {
      assert.ok(tactic[field], `${tactic.id} has ${field}`);
    }
  }
  for (const action of wild.wildActions) {
    for (const field of ["displayName", "flavorText", "artDirection", "absurdity"]) {
      assert.ok(action[field], `${action.id} has ${field}`);
    }
  }
});

test("new thematic decks and reference surfaces have complete draft inventories", async () => {
  const mandates = await readJson("data/mandates.json");
  const objectives = await readJson("data/secret-objectives.json");
  const references = await readJson("data/reference-cards.json");
  const reserve = await readJson("data/reserve-specialists.json");
  const world = await readJson("data/world-copy.json");
  const manifest = await readJson("data/content-manifest.json");

  assert.equal(mandates.mandates.length, 12);
  assert.equal(objectives.objectives.length, 18);
  assert.equal(references.eraCards.length, 4);
  assert.equal(references.playerReferences.length, 4);
  assert.equal(reserve.specialists.length, 12);
  assert.equal(world.agiDeclarations.length, 6);
  assert.equal(world.endings.length, 6);
  assert.equal(world.tokenCopy.length, 14);

  const requiredCardFields = ["name", "rulesText", "flavorText", "artDirection"];
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
  const app = await readFile(new URL("prototype/app.js", root), "utf8");
  assert.doesNotMatch(app, /faction\.historicalReference/);
  assert.match(app, /faction\.motto/);
});
