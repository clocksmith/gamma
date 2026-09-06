import { connectedFacilityIds } from "../../lab/rules/local-power-connections.js";
export function seedToUint32(value) {
  let hash = 2166136261;
  for (const character of String(value)) {
    hash ^= character.codePointAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

export function createRng(seed) {
  let value = seedToUint32(seed);
  return () => {
    value += 0x6d2b79f5;
    let mixed = value;
    mixed = Math.imul(mixed ^ (mixed >>> 15), mixed | 1);
    mixed ^= mixed + Math.imul(mixed ^ (mixed >>> 7), mixed | 61);
    return ((mixed ^ (mixed >>> 14)) >>> 0) / 4294967296;
  };
}

export function shuffle(values, rng) {
  const copy = [...values];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const target = Math.floor(rng() * (index + 1));
    [copy[index], copy[target]] = [copy[target], copy[index]];
  }
  return copy;
}

export const BOARD_RINGS = Object.freeze({
  center: Object.freeze([[0, 0]]),
  inner: Object.freeze([
    [1, 0],
    [0, 1],
    [-1, 1],
    [-1, 0],
    [0, -1],
    [1, -1]
  ]),
  outer: Object.freeze([
    [2, 0],
    [1, 1],
    [0, 2],
    [-1, 2],
    [-2, 2],
    [-2, 1],
    [-2, 0],
    [-1, -1],
    [0, -2],
    [1, -2],
    [2, -2],
    [2, -1]
  ])
});

const LEGACY_OUTER_RING = Object.freeze([
  [1, 1],
  [-1, 2],
  [-2, 1],
  [-1, -1],
  [1, -2],
  [2, -1]
]);

function ringCoordinates(ring, count) {
  if (ring === "outer" && count === LEGACY_OUTER_RING.length) {
    return LEGACY_OUTER_RING;
  }
  return BOARD_RINGS[ring];
}

const coordinateKey = (q, r) => `${q},${r}`;

function expandTileDefinitions(config) {
  return config.board.tiles.flatMap((tile) => {
    const placementTotal = Object.values(tile.placement || {})
      .reduce((sum, count) => sum + count, 0);
    if (placementTotal !== tile.count) {
      throw new Error(
        `${tile.id} declares ${tile.count} copies but places ${placementTotal}.`
      );
    }
    let instance = 0;
    return Object.entries(tile.placement || {}).flatMap(([ring, count]) =>
      Array.from({ length: count }, () => ({
        ...tile,
        instanceId: `${tile.id}-${instance += 1}`,
        placementRing: ring
      }))
    );
  });
}

export function generateBoard(config, seed) {
  const definitions = expandTileDefinitions(config);
  if (definitions.length !== config.board.prototypeTileCount) {
    throw new Error(
      `Board placement expands to ${definitions.length} tiles; expected ${config.board.prototypeTileCount}.`
    );
  }
  return ["center", "inner", "outer"].flatMap((ring) => {
    const pool = shuffle(
      definitions.filter((tile) => tile.placementRing === ring),
      createRng(`${seed}:${ring}`)
    );
    const coordinates = ringCoordinates(ring, pool.length);
    if (pool.length !== coordinates.length) {
      throw new Error(
        `${ring} ring requires ${coordinates.length} tiles; received ${pool.length}.`
      );
    }
    return pool.map((tile, index) => ({
      ...tile,
      q: coordinates[index][0],
      r: coordinates[index][1]
    }));
  });
}

export function axialDistance(left, right) {
  const leftS = -left.q - left.r;
  const rightS = -right.q - right.r;
  return Math.max(
    Math.abs(left.q - right.q),
    Math.abs(left.r - right.r),
    Math.abs(leftS - rightS)
  );
}

export function calculateAuditDraws(baseDraws, playerCount) {
  return Math.max(1, Math.round(Number(baseDraws) * Number(playerCount) / 4));
}

export function publicMandateAwards(config, player) {
  const customerSchedule = config.scoring.customerMandateSchedule;
  const peerValidation = config.factionRules?.imperial?.peerValidation;
  const playerCount = Number(player.playerCount || 4);
  const awards = [
    ...Array.from({ length: player.customers }, (_, index) => ({
      id: `customer-${index + 1}`,
      points:
        customerSchedule &&
        index + 1 >= customerSchedule.lateFromCustomer
          ? customerSchedule.lateMandate
          : customerSchedule?.baseMandate ?? config.scoring.customerMandate
    })),
    ...config.scoring.capabilityThresholds
      .filter((entry) => player.capability >= entry.value)
      .map((entry) => {
        let points = entry.mandate;
        if (
          player.factionId === "imperial_research_lab" &&
          peerValidation &&
          entry.value >= peerValidation.lateFromCapability
        ) {
          const broadlyValidated =
            entry.value >= peerValidation.fullValidationCapability &&
            playerCount - 1 >= peerValidation.minimumRivalsForFullMandate;
          points = broadlyValidated
            ? peerValidation.fullMandate
            : peerValidation.baseMandate;
        }
        return { id: `capability-${entry.value}`, points };
      }),
    ...config.scoring.trustThresholds
      .filter((entry) => player.trust >= entry.value)
      .map((entry) => ({ id: `trust-${entry.value}`, points: entry.mandate }))
  ];
  return awards;
}

export function resolveTieByInitiative(tiedPlayerIds, initiativeOrder, initiativeIndex = 0) {
  const tied = new Set(tiedPlayerIds);
  for (let offset = 0; offset < initiativeOrder.length; offset += 1) {
    const candidate = initiativeOrder[(initiativeIndex + offset) % initiativeOrder.length];
    if (tied.has(candidate)) return candidate;
  }
  return null;
}

export function buildTrainingDeck(config, seed) {
  const cards = config.trainingDeck.cards.flatMap((entry) =>
    Array.from({ length: entry.count }, (_, index) => ({
      id: `${entry.id}-${index + 1}`,
      type: entry.id,
      kind: entry.kind
    }))
  );
  return shuffle(cards, createRng(seed));
}

export const TRAINING_DOMAINS = Object.freeze([
  "code",
  "science",
  "web",
  "books",
  "images",
  "video",
  "synthetic"
]);

function firstMissingDomain(seen) {
  return TRAINING_DOMAINS.find((domain) => !seen.has(domain));
}

export function simulateTrainingRun(config, seed, options = {}) {
  const stopAt = Math.max(1, Number(options.stopAt || 3));
  let capability = 0;
  let trust = 0;
  let scrutiny = 0;
  let protectedDuplicate = false;
  let crashProtectable = false;
  const ordinaryDomains = new Set();
  const revealed = [];
  const deck = options.deck || buildTrainingDeck(config, seed);
  let outcome = "stopped";

  for (const card of deck) {
    revealed.push(card.type);

    let duplicate = false;
    if (card.kind === "domain") {
      duplicate = ordinaryDomains.has(card.type);
      if (!duplicate) {
        ordinaryDomains.add(card.type);
        capability += Number(options.domainGain || 1);
      }
    } else if (card.type === "curated_corpus") {
      const domain = firstMissingDomain(ordinaryDomains);
      if (domain) {
        ordinaryDomains.add(domain);
        capability += Number(options.domainGain || 1);
      } else duplicate = true;
    } else if (card.type === "benchmark_leak") {
      capability += 2;
      scrutiny += 1;
    } else if (card.type === "human_evaluation") {
      trust += 1;
      outcome = "human-evaluation";
      break;
    }

    if (duplicate) {
      crashProtectable = true;
      if (options.scientificMethod) {
        protectedDuplicate = true;
        outcome = "scientific-method-banked";
      } else {
        capability = Math.min(capability, Number(options.crashRetain || 0));
        scrutiny += 1;
        outcome = "crashed";
      }
      break;
    }

    if (ordinaryDomains.size >= stopAt) {
      outcome = "banked";
      break;
    }
  }

  return {
    seed: String(seed),
    stopAt,
    outcome,
    capability: capability + (outcome === "crashed" ? 0 : Number(options.bankBonus || 0)),
    trust,
    scrutiny,
    runwaySpent: 0,
    protection: protectedDuplicate ? "scientific_method" : null,
    protectedDuplicate,
    crashProtectable,
    ordinaryDomains: [...ordinaryDomains],
    ordinaryDomainCount: ordinaryDomains.size,
    distinctDomains: ordinaryDomains.size,
    revealed,
    cardsDrawn: revealed.length,
    deckExhausted: revealed.length === deck.length && outcome === "stopped"
  };
}

export function createPlayer(config, faction, frontierTileId, playerCount = 4) {
  const startingScrutiny = Math.min(
    faction.starts.scrutiny || 0,
    config.playerSupply.scrutinyCubes
  );
  return {
    factionId: faction.id,
    playerCount,
    ...structuredClone(faction.starts),
    mandate: 0,
    mandateAwards: [],
    programUses: 0,
    actionsUsed: [],
    escalationsUsed: [],
    pieces: [
      ...Array.from({ length: config.playerSupply.startingAgents }, (_, index) => ({
        id: `agent-${index + 1}`,
        name: `Agent ${index + 1}`,
        kind: "agent",
        tileId: frontierTileId
      }))
    ],
    facilities: [],
    generators: [],
    startingGridConnection: {
      ...structuredClone(config.board.startingGridConnection),
      assignedFacilityId: null
    },
    auditBag: Array.from({ length: startingScrutiny }, () => faction.id)
  };
}

export function createGame(
  config,
  factions,
  headlines,
  seed,
  factionId,
  playerCount = 4,
  options = {}
) {
  const board = generateBoard(config, seed);
  if (Object.keys(options).length) throw new Error("Game setup does not accept alternate rules options.");
  const faction = factions.factions.find((entry) => entry.id === factionId) || factions.factions[0];
  const frontier = board.find((tile) => tile.id === "frontier");
  const boundedPlayerCount = Number(playerCount);
  if (
    !Number.isInteger(boundedPlayerCount) ||
    !config.players.playableCounts.includes(boundedPlayerCount)
  ) {
    throw new RangeError(
      `playerCount must be one of ${config.players.playableCounts.join(", ")}.`
    );
  }
  const state = {
    seed: String(seed),
    playerCount: boundedPlayerCount,
    round: config.rounds[0].number,
    cycle: 1,
    initiativeSeat: 0,
    phase: "select",
    headlineIndex: 0,
    selectedAction: null,
    selectedPieceId: null,
    selectedTileId: null,
    board,
    player: createPlayer(config, faction, frontier.instanceId, boundedPlayerCount),
    headlines: shuffle(
      availableHeadlines(headlines, 1),
      createRng(`${seed}:headlines:1`)
    ),
    metrics: {
      actionSelections: [],
      poweredFacilityRounds: [],
      researchCapabilityGains: [],
      auditHitsByPlayer: { [faction.id]: 0 },
      earliestAgiEligibility: null
    },
    log: [
      `Era I begins. ${faction.name} enters the Frontier.`,
      `${boundedPlayerCount}-player Audit profile selected; this browser records one active seat.`
    ]
  };
  synchronizePublicMandate(config, state, "setup");
  return state;
}

export function availableHeadlines(headlineDocument, round) {
  return headlineDocument.headlines.filter(headline => headline.round === round);
}

export function availableCoreActions(config, state) {
  return config.actions.filter((action) => !state.player.actionsUsed.includes(action.id));
}

export function availableEscalations(escalations, state) {
  return escalations.escalations.filter((action) =>
    action.unlockedRound <= state.round &&
    !state.player.escalationsUsed.includes(action.id) &&
    state.player.programUses > 0
  );
}

export function legalDestinations(state, pieceId) {
  const piece = state.player.pieces.find((entry) => entry.id === pieceId);
  const current = state.board.find((tile) => tile.instanceId === piece?.tileId);
  if (!current) return [];
  return [...state.board];
}

function cap(value, definition) {
  return Math.max(definition.min, Math.min(definition.cap, value));
}

function addResource(config, player, key, amount) {
  player[key] = cap(player[key] + amount, config.resources[key]);
}

function synchronizePublicMandate(config, state, source) {
  const player = state.player;
  const known = new Set(player.mandateAwards.map((award) => award.id));
  for (const award of publicMandateAwards(config, player)) {
    if (known.has(award.id)) continue;
    player.mandate += award.points;
    player.mandateAwards.push({ ...award, source, round: state.round, cycle: state.cycle });
    if (state.log) state.log.unshift(`Public Mandate: ${award.id} scores ${award.points}.`);
  }
}

export function addScrutiny(config, player, amount) {
  const available = Math.max(0, config.playerSupply.scrutinyCubes - player.auditBag.length);
  const added = Math.min(available, amount);
  const overflow = amount - added;
  let paidRunway = 0;
  let lostTrust = 0;

  player.auditBag.push(...Array.from({ length: added }, () => player.factionId));
  for (let index = 0; index < overflow; index += 1) {
    if (player.runway > 0) {
      player.runway -= 1;
      paidRunway += 1;
    } else {
      addResource(config, player, "trust", -1);
      lostTrust += 1;
    }
  }
  player.scrutiny = player.auditBag.length;
  return { added, overflow, paidRunway, lostTrust };
}

export function isAgiEligible(config, player) {
  const rule = config.agiAchievement;
  return player.compute >= rule.computeCost && player.capability >= rule.capability &&
    player.trust >= rule.trust && player.facilities.filter((facility) => facility.powered).length >= rule.poweredFacilities;
}

function recordAgiEligibility(config, state, timing) {
  if (!state.metrics.earliestAgiEligibility && isAgiEligible(config, state.player)) {
    state.metrics.earliestAgiEligibility = {
      round: state.round,
      cycle: state.cycle,
      timing
    };
  }
}

function resolveCore(config, state, actionId, destination, options) {
  const player = state.player;
  if (actionId === "fund") {
    const venture = options.fundMode === "venture";
    addResource(config, player, "runway", venture ? 4 : 2);
    if (venture) {
      addScrutiny(config, player, 2);
    }
    return venture ? "Venture funding: +4 Runway, +2 Scrutiny." : "Conservative funding: +2 Runway.";
  }

  if (actionId === "research") {
    if (player.compute < 1) return "Research failed: 1 Compute required.";
    player.compute -= 1;
    const result = simulateTrainingRun(config, `${state.seed}:r${state.round}:c${state.cycle}`, {
      stopAt: options.stopAt,
      bankBonus: Number(destination.category === "research"),
      crashRetain: player.factionId === "safety_laboratory" ? 1 : 0
    });
    addResource(config, player, "capability", result.capability);
    addResource(config, player, "trust", result.trust);
    addScrutiny(config, player, result.scrutiny);
    state.metrics.researchCapabilityGains.push({
      round: state.round,
      cycle: state.cycle,
      gained: result.capability,
      outcome: result.outcome
    });
    return `Training ${result.outcome}: +${result.capability} Capability; ${result.revealed.join(" → ")}.`;
  }

  if (actionId === "build") {
    const mode = options.buildMode || "facility";
    if (!["facility", "generator"].includes(mode)) throw new RangeError(`Unknown build mode: ${mode}`);
    if (mode === "facility") {
      if (destination.category === "frontier") {
        return "Facility failed: Frontier has no Facility spaces.";
      }
      const capacity = destination.facilitySpaces ?? config.board.facilitySpacesPerHex;
      const occupied = player.facilities.filter(
        (facility) => facility.tileId === destination.instanceId
      ).length;
      if (player.runway < 2 || player.facilities.length >= 4) {
        return "Facility failed: requires 2 Runway and available supply.";
      }
      if (occupied >= capacity) return "Facility failed: no open Facility space.";
      player.runway -= 2;
      player.facilities.push({
        id: `facility-${player.facilities.length + 1}`,
        tileId: destination.instanceId,
        powered: false
      });
      if (!player.startingGridConnection.assignedFacilityId) {
        player.startingGridConnection.assignedFacilityId = player.facilities.at(-1).id;
        return `Facility constructed at ${destination.name}; the basic starting grid connection supplies its first Power.`;
      }
      return `Facility constructed at ${destination.name}; it requires delivered Power.`;
    }
    if (mode === "generator") {
      if (state.round < 2) return "Generator failed: industrial Power unlocks in Capacity.";
      if (destination.category !== "energy") return "Generator failed: acting piece must end on an Energy location.";
      const locationRule = config.singleGeneratorRule.locations[destination.id];
      const source = locationRule && config.powerSources.find(
        (entry) => entry.id === locationRule.sourceId
      );
      if (!source || source.round > state.round) return "Generator failed: this Energy location has no available source.";
      if (player.runway < locationRule.constructionCost || player.generators.length >= 1) {
        return "Generator failed: insufficient Runway or no Generator supply.";
      }
      player.runway -= locationRule.constructionCost;
      addResource(config, player, "trust", source.trust || 0);
      addScrutiny(config, player, source.scrutinyOnBuild || 0);
      player.generators.push({
        id: `generator-${player.generators.length + 1}`,
        tileId: destination.instanceId,
        sourceId: source.id
      });
      return `${source.name} constructed at ${destination.name}: nearby Facilities are connected.`;
    }

  }

  if (actionId === "organize") {
    if (options.mode === "relocate") {
      const facility = player.facilities.find((item) => item.id === options.facilityId && item.tileId === destination.instanceId);
      const target = state.board.find((tile) => tile.instanceId === options.facilityDestinationId);
      if (!facility || !target || target.category === "frontier" || axialDistance(destination, target) !== 1 ||
          player.facilities.filter((item) => item.tileId === target.instanceId).length >= (target.facilitySpaces ?? config.board.facilitySpacesPerHex)) return "Relocation blocked.";
      facility.tileId = target.instanceId; facility.category = target.category;
      return "Facility relocated; local connections now follow its new district.";
    }
    const cost = 2 - Number(destination.category === "talent");
    if (player.pieces.length >= config.playerSupply.agents || player.runway < cost) return "Recruitment blocked.";
    const number = Array.from({ length: config.playerSupply.agents }, (_, index) => index + 1)
      .find((value) => !player.pieces.some((piece) => piece.id === `agent-${value}`));
    player.runway -= cost;
    player.pieces.push({ id: `agent-${number}`, name: `Agent ${number}`, kind: "agent", tileId: destination.instanceId });
    return "An Agent joins the assignment; no additional action is granted.";
  }

  if (actionId === "deploy") {
    const requirement = [2, 4, 6, 8, 10][player.customers] ?? Infinity;
    const computeCost = destination.category === "consumer" ? 0 : 1;
    if (player.capability < requirement || player.compute < computeCost || player.customers >= 5) {
      return `Deploy failed: Customer ${player.customers + 1} needs Capability ${requirement} and ${computeCost} Compute.`;
    }
    player.compute -= computeCost;
    player.customers += 1;
    addScrutiny(config, player, 1);
    return `Customer ${player.customers} deployed at ${destination.name}; +1 Scrutiny.`;
  }

  if (actionId === "influence") {
    if (!["media", "government", "capital"].includes(destination.category)) {
      return "Influence failed: the acting piece must end at Media, Government, or Capital.";
    }
    if (options.influenceMode === "scrutiny") {
      const removed = destination.category === "media" ? 2 : 1;
      player.auditBag.splice(0, Math.min(removed, player.auditBag.length));
      player.scrutiny = player.auditBag.length;
      return `Political presence at ${destination.name} removes up to ${removed} Scrutiny.`;
    }
    const gained = destination.category === "government" ? 2 : 1;
    addResource(config, player, "trust", gained);
    return `Political presence at ${destination.name}: +${gained} Trust.`;
  }

  return `${actionId} is recorded but not automated in this study.`;
}

function connectedPowerState(config, state) {
  const connected = connectedFacilityIds(state.board, state.player);
  for (const facility of state.player.facilities) facility.powered = connected.has(facility.id);
  return { powered: connected.size };
}

export function locallyEligibleFacilityIds(board, player) {
  return connectedFacilityIds(board, player);
}

function finishRound(config, headlines, state) {
  const power = connectedPowerState(config, state);
  state.metrics.poweredFacilityRounds.push({
    round: state.round,
    powered: power.powered,
    facilities: state.player.facilities.length,
  });
  addResource(config, state.player, "runway", state.player.customers);

  const draws = calculateAuditDraws(
    config.rounds[state.round - 1].auditBaseDraws,
    state.playerCount
  );
  const rng = createRng(`${state.seed}:audit:${state.round}`);
  let penalties = 0;
  for (let index = 0; index < draws && state.player.auditBag.length > 0; index += 1) {
    const target = Math.floor(rng() * state.player.auditBag.length);
    state.player.auditBag.splice(target, 1);
    state.player.scrutiny = state.player.auditBag.length;
    penalties += 1;
    state.metrics.auditHitsByPlayer[state.player.factionId] += 1;
    if (state.player.runway > 0) state.player.runway -= 1;
    else addResource(config, state.player, "trust", -1);
  }

  state.log.unshift(
    `Production: ${power.powered}/${state.player.facilities.length} Facilities powered. Audit profile drew ${draws}; ${penalties} active-seat cube(s) resolved.`
  );
  recordAgiEligibility(config, state, "after_production");
  synchronizePublicMandate(config, state, "production");

  advanceRound(config, headlines, state);
}

function advanceRound(config, headlines, state) {
  if (state.round < config.rounds.at(-1).number) {
    state.round += 1;
    state.cycle = 1;
    state.player.actionsUsed = [];
    state.player.programUses = config.rounds[state.round - 1].programUses;
    state.headlines = shuffle(
      availableHeadlines(headlines, state.round),
      createRng(`${state.seed}:headlines:${state.round}`)
    );
    state.log.unshift(`Era ${state.round} begins: ${config.rounds[state.round - 1].name}.`);
  } else {
    state.phase = "complete";
    state.log.unshift("Era IV settled. Final scoring is ready for manual review.");
  }
}

export function commitAction(state, actionId, kind = "core") {
  if (state.phase !== "select") throw new Error("Action cannot be selected in the current phase.");
  state.selectedAction = { id: actionId, kind };
  state.metrics.actionSelections.push({
    round: state.round,
    cycle: state.cycle,
    actionId,
    kind
  });
  state.phase = "act";
  state.log.unshift(`${kind === "escalation" ? "Escalation" : "Core"} Action revealed: ${actionId}. Acting piece remains undeclared.`);
}

export function resolveSelectedAction(config, headlines, state, pieceId, tileId, options = {}) {
  if (state.phase !== "act" || !state.selectedAction) throw new Error("No revealed action is waiting for resolution.");
  if (state.selectedAction.id === "build" && options.buildMode && !["facility", "generator"].includes(options.buildMode)) {
    throw new RangeError(`Unknown build mode: ${options.buildMode}`);
  }
  const legal = legalDestinations(state, pieceId);
  if (!legal.some((entry) => entry.instanceId === tileId)) throw new Error("Choose an owned Agent and an existing district.");

  const piece = state.player.pieces.find((entry) => entry.id === pieceId);
  const destination = state.board.find((entry) => entry.instanceId === tileId);
  piece.tileId = tileId;

  let summary;
  if (state.selectedAction.kind === "core") {
    summary = resolveCore(config, state, state.selectedAction.id, destination, options);
    state.player.actionsUsed.push(state.selectedAction.id);
  } else {
    if (state.player.programUses < 1) throw new Error("No Program use is currently available.");
    state.player.programUses -= 1;
    state.player.escalationsUsed.push(state.selectedAction.id);
    summary = `${state.selectedAction.id} committed at ${destination.name}; detailed Escalation resolution is recorded for manual study.`;
  }

  state.log.unshift(summary);
  recordAgiEligibility(config, state, "after_action");
  synchronizePublicMandate(config, state, "action");
  state.selectedAction = null;
  state.phase = "select";
  state.initiativeSeat = (state.initiativeSeat + 1) % state.playerCount;

  const cycleLimit = config.rounds.find((round) => round.number === state.round).cycles;
  if (state.cycle === cycleLimit) {
    finishRound(config, headlines, state);
  } else {
    state.cycle += 1;
  }
}
