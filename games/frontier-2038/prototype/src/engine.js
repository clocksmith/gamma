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
    [1, 1],
    [-1, 2],
    [-2, 1],
    [-1, -1],
    [1, -2],
    [2, -1]
  ])
});

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
    const coordinates = BOARD_RINGS[ring];
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

function rotateBoardRing(board, coordinates, steps) {
  if (!steps) return [];
  const normalized = ((steps % coordinates.length) + coordinates.length) % coordinates.length;
  const indexByCoordinate = new Map(
    coordinates.map(([q, r], index) => [coordinateKey(q, r), index])
  );
  const occupants = board
    .filter((tile) => indexByCoordinate.has(coordinateKey(tile.q, tile.r)))
    .map((tile) => ({
      tile,
      from: indexByCoordinate.get(coordinateKey(tile.q, tile.r))
    }));
  if (occupants.length !== coordinates.length) {
    throw new Error(`Cannot rotate incomplete ${coordinates.length}-space ring.`);
  }
  return occupants.map(({ tile, from }) => {
    const destination = coordinates[(from + normalized) % coordinates.length];
    const movement = {
      tileId: tile.instanceId,
      from: { q: tile.q, r: tile.r },
      to: { q: destination[0], r: destination[1] }
    };
    tile.q = destination[0];
    tile.r = destination[1];
    return movement;
  });
}

export function applyBoardMotion(board, motion) {
  if (!motion || typeof motion.id !== "string") {
    throw new TypeError("A realignment motion is required.");
  }
  return {
    motionId: motion.id,
    movements: [
      ...rotateBoardRing(board, BOARD_RINGS.inner, motion.innerSteps || 0),
      ...rotateBoardRing(board, BOARD_RINGS.outer, motion.outerSteps || 0)
    ]
  };
}

export function resolveBlindRealignmentVote(ballots, initiativeSeat, motionIds) {
  const validMotions = new Set(motionIds);
  const bySeat = new Map();
  const counts = Object.fromEntries(motionIds.map((id) => [id, 0]));
  for (const ballot of ballots) {
    if (!Number.isInteger(ballot.seat) || bySeat.has(ballot.seat)) {
      throw new TypeError("Realignment ballots require one unique integer seat each.");
    }
    if (!validMotions.has(ballot.motionId)) {
      throw new TypeError(`Unknown realignment motion: ${ballot.motionId}.`);
    }
    bySeat.set(ballot.seat, ballot.motionId);
    counts[ballot.motionId] += 1;
  }
  if (ballots.length === 0) throw new TypeError("At least one realignment ballot is required.");
  const maximum = Math.max(...Object.values(counts));
  const leaders = new Set(
    Object.entries(counts)
      .filter(([, count]) => count === maximum)
      .map(([id]) => id)
  );
  let winningMotionId;
  for (let offset = 0; offset < ballots.length; offset += 1) {
    const seat = (initiativeSeat + offset) % ballots.length;
    const motionId = bySeat.get(seat);
    if (leaders.has(motionId)) {
      winningMotionId = motionId;
      break;
    }
  }
  return {
    winningMotionId,
    counts,
    tied: leaders.size > 1,
    initiativeSeat
  };
}

export function calculateAuditDraws(baseDraws, playerCount) {
  return Math.max(1, Math.round(Number(baseDraws) * Number(playerCount) / 4));
}

export function publicMandateAwards(config, player) {
  const awards = [
    ...Array.from({ length: player.customers }, (_, index) => ({
      id: `customer-${index + 1}`,
      points: config.scoring.customerMandate
    })),
    ...config.scoring.capabilityThresholds
      .filter((entry) => player.capability >= entry.value)
      .map((entry) => ({ id: `capability-${entry.value}`, points: entry.mandate })),
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

function firstMissingDomain(seen) {
  return ["code", "science", "web", "books", "images", "video", "synthetic"]
    .find((domain) => !seen.has(domain));
}

export function simulateTrainingRun(config, seed, options = {}) {
  const stopAt = Math.max(1, Math.min(7, Number(options.stopAt || 3)));
  const startingRunway = Number(options.runway ?? 12);
  let runway = startingRunway;
  let safety = Number(options.safety || 0);
  let capability = 0;
  let trust = 0;
  let scrutiny = 0;
  let protectedDuplicate = false;
  let crashProtectable = false;
  let nextDuplicateUnprotected = false;
  const seen = new Set();
  const revealed = [];
  const deck = options.deck || buildTrainingDeck(config, seed);
  let outcome = "stopped";

  for (const card of deck) {
    revealed.push(card.type);

    if (card.kind === "domain") {
      if (seen.has(card.type)) {
        crashProtectable = !nextDuplicateUnprotected;
        if (safety > 0 && !nextDuplicateUnprotected) {
          safety -= 1;
          protectedDuplicate = true;
          outcome = "protected";
        } else {
          capability = 0;
          scrutiny += 1;
          outcome = "crashed";
        }
        break;
      }
      seen.add(card.type);
      capability += 1;
    } else if (card.type === "curated_corpus") {
      const domain = firstMissingDomain(seen);
      if (domain) {
        seen.add(domain);
        capability += 1;
      }
    } else if (card.type === "benchmark_leak") {
      capability += 2;
      scrutiny += 1;
    } else if (card.type === "licensed_dataset") {
      if (runway > 0) {
        runway -= 1;
      } else {
        outcome = "licensed-stop";
        break;
      }
    } else if (card.type === "synthetic_loop") {
      if (!seen.has("synthetic_loop")) {
        seen.add("synthetic_loop");
        capability += 1;
      }
      nextDuplicateUnprotected = true;
    } else if (card.type === "human_evaluation") {
      trust += 1;
      outcome = "human-evaluation";
      break;
    }

    if (seen.size >= stopAt) {
      outcome = "banked";
      break;
    }
  }

  return {
    seed: String(seed),
    stopAt,
    outcome,
    capability,
    trust,
    scrutiny,
    runwaySpent: startingRunway - runway,
    safetySpent: Number(options.safety || 0) - safety,
    protectedDuplicate,
    crashProtectable,
    distinctDomains: seen.size,
    revealed,
    cardsDrawn: revealed.length,
    deckExhausted: revealed.length === deck.length && outcome === "stopped"
  };
}

export function createPlayer(config, faction, frontierTileId) {
  const startingScrutiny = Math.min(
    faction.starts.scrutiny || 0,
    config.playerSupply.scrutinyCubes
  );
  return {
    factionId: faction.id,
    ...structuredClone(faction.starts),
    mandate: 0,
    mandateAwards: [],
    escalation: 0,
    actionsUsed: [],
    wildActionsUsed: [],
    pieces: [
      { id: "ceo", name: "CEO", kind: "ceo", tileId: frontierTileId },
      ...Array.from({ length: 1 }, (_, index) => ({
        id: `team-${index + 1}`,
        name: `Team ${index + 1}`,
        kind: "team",
        tileId: frontierTileId
      }))
    ],
    facilities: [],
    generators: [],
    links: [],
    influence: [],
    startingGridConnection: {
      ...structuredClone(config.board.startingGridConnection),
      assignedFacilityId: null
    },
    auditBag: Array.from({ length: startingScrutiny }, () => faction.id)
  };
}

export function createGame(config, factions, headlines, seed, factionId, playerCount = 4) {
  const board = generateBoard(config, seed);
  const faction = factions.factions.find((entry) => entry.id === factionId) || factions.factions[0];
  const frontier = board.find((tile) => tile.id === "frontier");
  const boundedPlayerCount = Number(playerCount);
  if (
    !Number.isInteger(boundedPlayerCount) ||
    !config.players.supportedCounts.includes(boundedPlayerCount)
  ) {
    throw new RangeError(
      `playerCount must be one of ${config.players.supportedCounts.join(", ")}.`
    );
  }
  const state = {
    seed: String(seed),
    playerCount: boundedPlayerCount,
    round: 1,
    cycle: 1,
    initiativeSeat: 0,
    phase: "select",
    headlineIndex: 0,
    selectedAction: null,
    selectedPieceId: null,
    selectedTileId: null,
    pendingRoundSettlement: null,
    lastRealignment: null,
    board,
    player: createPlayer(config, faction, frontier.instanceId),
    headlines: shuffle(
      headlines.headlines.filter((entry) => entry.round === 1),
      createRng(`${seed}:headlines:1`)
    ),
    metrics: {
      actionSelections: [],
      poweredFacilityRounds: [],
      researchCapabilityGains: [],
      realignmentVotes: [],
      auditHitsByPlayer: { [faction.id]: 0 },
      earliestAgiEligibility: null
    },
    log: [
      `Era I begins. ${faction.name} enters the Frontier.`,
      `${boundedPlayerCount}-player Audit profile selected; this browser records one active seat.`,
      config.board.prototypeNote
    ]
  };
  synchronizePublicMandate(config, state, "setup");
  return state;
}

export function availableCoreActions(config, state) {
  return config.actions.filter((action) => !state.player.actionsUsed.includes(action.id));
}

export function availableWildActions(wildActions, state) {
  return wildActions.wildActions.filter((action) =>
    action.unlockedRound <= state.round &&
    !state.player.wildActionsUsed.includes(action.id) &&
    state.player.escalation > 0
  );
}

export function legalDestinations(state, pieceId) {
  const piece = state.player.pieces.find((entry) => entry.id === pieceId);
  const current = state.board.find((tile) => tile.instanceId === piece?.tileId);
  if (!current) return [];
  return state.board.filter((tile) => axialDistance(current, tile) <= 2);
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
  const requirement = config.agiDeclaration;
  return player.capability >= requirement.capability &&
    player.customers >= requirement.customers &&
    player.facilities.length >= requirement.facilities &&
    player.trust >= requirement.trust &&
    player.compute >= requirement.computeCost;
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
    return venture ? "Venture round: +4 Runway, +2 Scrutiny." : "Conservative round: +2 Runway.";
  }

  if (actionId === "research") {
    if (player.compute < 1) return "Research failed: 1 Compute required.";
    player.compute -= 1;
    const result = simulateTrainingRun(config, `${state.seed}:r${state.round}:c${state.cycle}`, {
      stopAt: options.stopAt,
      runway: player.runway,
      safety: player.safety
    });
    addResource(config, player, "capability", result.capability);
    addResource(config, player, "trust", result.trust);
    player.runway -= result.runwaySpent;
    player.safety -= result.safetySpent;
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
        powered: false,
        gridReady: false
      });
      if (!player.startingGridConnection.assignedFacilityId) {
        player.startingGridConnection.assignedFacilityId = player.facilities.at(-1).id;
        return `Facility constructed at ${destination.name}; the basic starting grid connection supplies its first Power.`;
      }
      return `Facility constructed at ${destination.name}; it requires delivered Power.`;
    }
    if (mode === "generator") {
      if (state.round < 2) return "Generator failed: industrial Power unlocks in The Scale.";
      const source = config.powerSources.find((entry) => entry.id === options.powerSource);
      if (destination.category !== "energy") return "Generator failed: acting piece must end on an Energy location.";
      if (!source || source.round > state.round) return "Generator failed: selected source is unavailable.";
      if (player.runway < source.runwayCost || player.generators.length >= 2) {
        return "Generator failed: insufficient Runway or no Generator supply.";
      }
      player.runway -= source.runwayCost;
      addResource(config, player, "trust", source.trust || 0);
      addScrutiny(config, player, source.scrutinyOnBuild || 0);
      player.generators.push({
        id: `generator-${player.generators.length + 1}`,
        tileId: destination.instanceId,
        sourceId: source.id,
        capacity: source.capacity
      });
      return `${source.name} constructed at ${destination.name}: ${source.capacity} Power.`;
    }
    if (mode === "link") {
      if (state.round < 2) return "Link failed: Networks unlock in The Scale.";
      const facility = player.facilities.find(
        (entry) => entry.tileId === destination.instanceId && !player.links.includes(entry.id)
      );
      if (!facility || player.runway < 1 || player.links.length >= config.playerSupply.linkTokens) {
        return "Link failed: choose an unlinked Facility and pay 1 Runway.";
      }
      player.runway -= 1;
      player.links.push(facility.id);
      return `Network Link installed at ${destination.name}; its Facility is a Network anchor.`;
    }
  }

  if (actionId === "organize") {
    return "Organization resolved. Additional multi-piece movement remains a manual study control.";
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
    addResource(config, player, "trust", 1);
    player.influence.push({ tileId: destination.instanceId });
    return `Influence placed near ${destination.name}; +1 Trust.`;
  }

  return `${actionId} is recorded but not automated in this study.`;
}

function allocatePower(state) {
  const player = state.player;
  const startingFacility = player.facilities.find(
    (facility) => facility.id === player.startingGridConnection.assignedFacilityId
  );
  const startingGridCapacity = startingFacility
    ? player.startingGridConnection.capacity
    : 0;
  const generatedCapacity = player.generators.reduce((sum, item) => sum + item.capacity, 0);
  const generation = startingGridCapacity + generatedCapacity;
  const networked = networkedFacilityIds(state.board, player);
  let available = generation;
  let powered = 0;
  for (const facility of player.facilities) {
    const demand = 1;
    facility.powered = networked.has(facility.id) && available >= demand;
    facility.gridReady = facility.powered;
    if (facility.powered) {
      available -= demand;
      powered += 1;
    }
  }
  return {
    generation,
    generatedCapacity,
    startingGridCapacity,
    powered,
    demand: player.facilities.length
  };
}

export function networkedFacilityIds(board, player) {
  const result = new Set();
  const startingId = player.startingGridConnection?.assignedFacilityId;
  if (startingId) result.add(startingId);
  for (const id of player.links || []) result.add(id);
  for (const facility of player.facilities) {
    const tile = board.find((entry) => entry.instanceId === facility.tileId);
    if (player.generators.some((generator) => {
      const generatorTile = board.find((entry) => entry.instanceId === generator.tileId);
      return generatorTile && tile && axialDistance(generatorTile, tile) <= 1;
    })) result.add(facility.id);
  }
  let changed = true;
  while (changed) {
    changed = false;
    for (const facility of player.facilities) {
      if (result.has(facility.id)) continue;
      const tile = board.find((entry) => entry.instanceId === facility.tileId);
      if (player.facilities.some((candidate) => {
        if (!result.has(candidate.id)) return false;
        const candidateTile = board.find((entry) => entry.instanceId === candidate.tileId);
        return tile && candidateTile && axialDistance(tile, candidateTile) <= 1;
      })) {
        result.add(facility.id);
        changed = true;
      }
    }
  }
  return result;
}

function finishRound(config, headlines, state) {
  const power = allocatePower(state);
  state.metrics.poweredFacilityRounds.push({
    round: state.round,
    powered: power.powered,
    facilities: state.player.facilities.length,
    supply: power.generation,
    demand: power.demand
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
    `Production: ${power.powered}/${state.player.facilities.length} Facilities powered (${power.generation} supply / ${power.demand} demand, including ${power.startingGridCapacity} starting-grid Power). Audit profile drew ${draws}; ${penalties} active-seat cube(s) resolved.`
  );
  recordAgiEligibility(config, state, "after_production");
  synchronizePublicMandate(config, state, "production");
  state.pendingRoundSettlement = {
    round: state.round,
    finalRound: state.round === 4
  };
  if (state.round === 3) {
    state.phase = "realign";
    state.log.unshift(
      "Mandate scoring complete. Every institution now submits its one secret Jurisdictional Realignment ballot."
    );
  } else {
    advanceAfterRealignment(config, headlines, state);
  }
}

function advanceAfterRealignment(config, headlines, state) {
  state.pendingRoundSettlement = null;
  if (state.round < 4) {
    state.round += 1;
    state.cycle = 1;
    state.player.actionsUsed = [];
    state.player.escalation = config.rounds[state.round - 1].escalationTokens;
    state.headlines = shuffle(
      headlines.headlines.filter((entry) => entry.round === state.round),
      createRng(`${state.seed}:headlines:${state.round}`)
    );
    state.log.unshift(`Era ${state.round} begins: ${config.rounds[state.round - 1].name}.`);
  } else {
    state.phase = "complete";
    state.log.unshift("Round IV settled. Final scoring is ready for manual review.");
  }
}

export function castRealignmentVote(config, headlines, state, motionId) {
  if (state.phase !== "realign" || !state.pendingRoundSettlement) {
    throw new Error("No Jurisdictional Realignment vote is waiting.");
  }
  const motions = config.board.realignment.motions;
  const selected = motions.find((motion) => motion.id === motionId);
  if (!selected) throw new Error(`Unknown realignment motion: ${motionId}.`);

  const rng = createRng(`${state.seed}:realignment:${state.round}`);
  const ballots = [{ seat: 0, motionId }];
  for (let seat = 1; seat < state.playerCount; seat += 1) {
    ballots.push({
      seat,
      motionId: motions[Math.floor(rng() * motions.length)].id
    });
  }
  const result = resolveBlindRealignmentVote(
    ballots,
    state.initiativeSeat,
    motions.map((motion) => motion.id)
  );
  const winner = motions.find((motion) => motion.id === result.winningMotionId);
  const movement = applyBoardMotion(state.board, winner);
  const networked = networkedFacilityIds(state.board, state.player);
  for (const facility of state.player.facilities) {
    if (!networked.has(facility.id)) facility.gridReady = false;
  }
  const receipt = {
    round: state.round,
    activeBallot: motionId,
    ballots,
    ...result,
    movedTiles: movement.movements.length
  };
  state.lastRealignment = receipt;
  state.metrics.realignmentVotes.push(receipt);
  state.log.unshift(
    `${winner.name} adopted${result.tied ? " by Initiative-order tie-break" : ""}: ` +
    `${winner.ballotText} Network reach will be recalculated from visible adjacency.`
  );
  state.log.unshift(
    `Secret ballots revealed: ${motions.map((motion) =>
      `${motion.name} ${result.counts[motion.id]}`
    ).join(" · ")}.`
  );
  advanceAfterRealignment(config, headlines, state);
  return receipt;
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
  state.phase = "move";
  state.log.unshift(`${kind === "wild" ? "Wild" : "Core"} Action revealed: ${actionId}. Acting piece remains undeclared.`);
}

export function resolveSelectedAction(config, headlines, state, pieceId, tileId, options = {}) {
  if (state.phase !== "move" || !state.selectedAction) throw new Error("No revealed action is waiting for resolution.");
  const legal = legalDestinations(state, pieceId);
  if (!legal.some((entry) => entry.instanceId === tileId)) throw new Error("Destination is more than two hexes away.");

  const piece = state.player.pieces.find((entry) => entry.id === pieceId);
  const destination = state.board.find((entry) => entry.instanceId === tileId);
  piece.tileId = tileId;

  let summary;
  if (state.selectedAction.kind === "core") {
    summary = resolveCore(config, state, state.selectedAction.id, destination, options);
    state.player.actionsUsed.push(state.selectedAction.id);
  } else {
    if (state.player.escalation < 1) throw new Error("No Escalation token is available.");
    state.player.escalation -= 1;
    state.player.wildActionsUsed.push(state.selectedAction.id);
    summary = `${state.selectedAction.id} committed at ${destination.name}; detailed Wild Action resolution is recorded for manual study.`;
  }

  state.log.unshift(summary);
  recordAgiEligibility(config, state, "after_action");
  synchronizePublicMandate(config, state, "action");
  state.selectedAction = null;
  state.phase = "select";
  state.initiativeSeat = (state.initiativeSeat + 1) % state.playerCount;

  if (state.cycle === 3) {
    finishRound(config, headlines, state);
  } else {
    state.cycle += 1;
  }
}
