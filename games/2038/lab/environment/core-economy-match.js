import {
  axialDistance,
  calculateAuditDraws,
  createRng,
  generateBoard,
  publicMandateAwards,
  simulateTrainingRun
} from "../../web/src/engine.js";
import {
  renderSimulationCopy,
  simulationCopy
} from "../content/simulation-copy.js";

export const CORE_ECONOMY_COVERAGE = simulationCopy.coverage.coreEconomy;

const CUSTOMER_REQUIREMENTS = [2, 4, 6, 8, 10];
const FACILITY_CATEGORIES = new Set([
  "research",
  "cloud",
  "consumer",
  "chip",
  "capital",
  "talent",
  "media",
  "government",
  "energy"
]);
const POLITICAL_CATEGORIES = new Set(["media", "government", "capital"]);

function clamp(value, minimum, maximum) {
  return Math.max(minimum, Math.min(maximum, value));
}

function clone(value) {
  return structuredClone(value);
}

function immutableCopy(value) {
  if (Array.isArray(value)) {
    return Object.freeze(value.map((entry) => immutableCopy(entry)));
  }
  if (value && typeof value === "object") {
    return Object.freeze(Object.fromEntries(
      Object.entries(value).map(([key, entry]) => [key, immutableCopy(entry)])
    ));
  }
  return value;
}

function finalMandate(config, player) {
  return (
    player.mandate +
    publicMandateAwards(config, player).reduce((sum, award) => sum + award.points, 0) -
    player.facilities.filter((facility) => !facility.powered).length
  );
}

function createPlayer(
  config,
  faction,
  seat,
  frontierId,
  profileId,
  backendId = "weighted",
  model = null,
  reasoningEffort = null,
  playerCount = 4
) {
  const starts = clone(faction.starts);
  return {
    seat,
    playerCount,
    factionId: faction.id,
    factionName: faction.name,
    profileId,
    backendId,
    model,
    reasoningEffort,
    runway: starts.runway,
    compute: starts.compute,
    capability: starts.capability,
    customers: starts.customers,
    trust: starts.trust,
    safety: starts.safety,
    mandate: 0,
    scrutiny: starts.scrutiny,
    actionsUsed: [],
    selectedAction: null,
    facilities: [],
    generators: [],
    pieces: [
      { id: `s${seat}-ceo`, kind: "ceo", tileId: frontierId },
      ...Array.from({ length: config.playerSupply.teams }, (_, index) => ({
        id: `s${seat}-team-${index + 1}`,
        kind: "team",
        tileId: frontierId
      }))
    ],
    metrics: {
      actions: {},
      openingActions: [],
      forcedNoOps: 0,
      realignmentBallots: {},
      researchCapability: [],
      poweredFacilityRounds: [],
      auditHits: 0,
      scrutinyAdded: starts.scrutiny,
      policyProviders: {},
      policyReceipts: [],
      policyFallbacks: 0,
      earliestAgiEligibility: null
    }
  };
}

export class CoreEconomyMatch {
  constructor({
    config,
    factions,
    profiles,
    backends = [],
    models = [],
    reasoningEfforts = [],
    seed,
    playerCount = 4,
    recordReplay = false,
    projection = "rich",
    decisionContext = null
  }) {
    if (playerCount < config.players.min || playerCount > config.players.max) {
      throw new RangeError(`playerCount must be ${config.players.min}–${config.players.max}.`);
    }
    this.config = config;
    this.seed = String(seed);
    this.playerCount = playerCount;
    this.round = 1;
    this.cycle = 1;
    this.initiativeSeat = 0;
    this.complete = false;
    this.board = generateBoard(config, `${seed}:board`);
    this.recordReplay = recordReplay;
    if (!["rich", "batch"].includes(projection)) {
      throw new TypeError(`Unknown simulation projection: ${projection}.`);
    }
    this.projection = projection;
    this.decisionContext = decisionContext;
    this.publicMatchId = decisionContext?.publicMatchId || "mandate-2038";
    this.replay = [];
    this.publicHistory = [];
    const frontier = this.board.find((tile) => tile.id === "frontier");
    this.players = Array.from({ length: playerCount }, (_, seat) =>
      createPlayer(
        config,
        factions[seat % factions.length],
        seat,
        frontier.instanceId,
        profiles[seat % profiles.length].id,
        backends[seat % Math.max(1, backends.length)] || "weighted",
        models[seat % Math.max(1, models.length)] || null,
        reasoningEfforts[seat % Math.max(1, reasoningEfforts.length)] || null,
        playerCount
      )
    );
    this.recordEvent("match_started", null, simulationCopy.events.coreMatchStarted);
  }

  addResource(player, key, amount) {
    const definition = this.config.resources[key];
    player[key] = clamp(player[key] + amount, definition.min, definition.cap);
  }

  spendRunway(player, amount) {
    const spent = Math.min(player.runway, Math.max(0, Number(amount) || 0));
    player.runway -= spent;
    return spent;
  }

  addScrutiny(player, amount) {
    const added = Math.min(
      amount,
      this.config.playerSupply.scrutinyCubes - player.scrutiny
    );
    player.scrutiny += added;
    player.metrics.scrutinyAdded += added;
    let overflow = amount - added;
    while (overflow > 0) {
      if (player.runway > 0) this.spendRunway(player, 1);
      else this.addResource(player, "trust", -1);
      overflow -= 1;
    }
  }

  removeScrutiny(player, amount) {
    player.scrutiny = Math.max(0, player.scrutiny - amount);
  }

  tileOccupancy(tileId) {
    return this.players.reduce(
      (count, player) =>
        count + player.facilities.filter((facility) => facility.tileId === tileId).length,
      0
    );
  }

  generatorOccupancy(tileId) {
    return this.players.reduce(
      (count, player) =>
        count + player.generators.filter((generator) => generator.tileId === tileId).length,
      0
    );
  }

  legalDestinations(player, piece) {
    const current = this.board.find((tile) => tile.instanceId === piece.tileId);
    return this.board.filter((tile) => axialDistance(current, tile) <= 2);
  }

  canDeploy(player) {
    const requirement = CUSTOMER_REQUIREMENTS[player.customers] ?? Infinity;
    return player.customers < this.config.resources.customers.cap &&
      player.capability >= requirement &&
      player.compute >= 0;
  }

  publicPlayerState(player) {
    return {
      seat: player.seat,
      factionId: player.factionId,
      factionName: player.factionName,
      runway: player.runway,
      compute: player.compute,
      capability: player.capability,
      customers: player.customers,
      trust: player.trust,
      safety: player.safety,
      mandate: player.mandate,
      scrutiny: player.scrutiny,
      actionsUsed: [...player.actionsUsed],
      pieces: this.copyPublic(player.pieces),
      facilities: this.copyPublic(player.facilities),
      generators: this.copyPublic(player.generators)
    };
  }

  copyPublic(value) {
    return this.projection === "batch" ? immutableCopy(value) : clone(value);
  }

  publicBoardState() {
    return this.board.map((tile) => ({
      tileId: tile.instanceId,
      name: tile.name,
      category: tile.category,
      q: tile.q,
      r: tile.r,
      facilitySpacesOpen:
        (tile.facilitySpaces ?? this.config.board.facilitySpacesPerHex) -
        this.tileOccupancy(tile.instanceId),
      components: this.players.flatMap((player) => [
        ...player.pieces
          .filter((piece) => piece.tileId === tile.instanceId)
          .map((piece) => ({ type: "piece", ownerSeat: player.seat, ...this.copyPublic(piece) })),
        ...player.facilities
          .filter((facility) => facility.tileId === tile.instanceId)
          .map((facility) => ({ type: "facility", ownerSeat: player.seat, ...this.copyPublic(facility) })),
        ...player.generators
          .filter((generator) => generator.tileId === tile.instanceId)
          .map((generator) => ({ type: "generator", ownerSeat: player.seat, ...this.copyPublic(generator) }))
      ])
    }));
  }

  publicObservation(seat) {
    const player = this.players[seat];
    const powered = player.facilities.filter((facility) => facility.powered).length;
    const publicPlayers = this.players.map((candidate) => this.publicPlayerState(candidate));
    return {
      round: this.round,
      cycle: this.cycle,
      initiativeSeat: this.initiativeSeat,
      self: {
        ...publicPlayers[seat],
        runway: player.runway,
        compute: player.compute,
        capability: player.capability,
        customers: player.customers,
        trust: player.trust,
        safety: player.safety,
        scrutiny: player.scrutiny,
        facilities: player.facilities.length,
        generators: player.generators.length,
        poweredFacilities: powered,
        gridReadyFacilities: player.facilities.filter((facility) => facility.gridReady).length,
        unpoweredFacilities: player.facilities.length - powered,
        actionsUsed: [...player.actionsUsed],
        canDeploy: this.canDeploy(player)
      },
      opponents: this.players
        .filter((opponent) => opponent.seat !== seat)
        .map((opponent) => ({
          ...publicPlayers[opponent.seat],
          facilityTileIds: opponent.facilities.map((facility) => facility.tileId),
          facilities: opponent.facilities.length,
          gridReadyFacilities: opponent.facilities.filter(
            (facility) => facility.gridReady
          ).length
        })),
      board: this.publicBoardState()
    };
  }

  packet(seat, stage, legalDecisions) {
    const player = this.players[seat];
    const packet = {
      schemaVersion: this.decisionContext?.schemaVersion || 1,
      ...(this.decisionContext?.game
        ? { game: this.copyPublic(this.decisionContext.game) }
        : {}),
      requestId: `${this.publicMatchId}:r${this.round}:c${this.cycle}:s${seat}:${stage}`,
      matchId: this.publicMatchId,
      seat,
      factionId: player.factionId,
      round: this.round,
      cycle: this.cycle,
      observation: this.publicObservation(seat),
      publicHistory: this.copyPublic(this.publicHistory),
      legalDecisions
    };
    Object.defineProperty(packet, "policySeed", {
      value: this.seed,
      enumerable: false
    });
    return packet;
  }

  legalActionSelections(seat) {
    const player = this.players[seat];
    return this.config.actions
      .filter((action) => !player.actionsUsed.includes(action.id))
      .map((action) => {
        const availability = this.selectionAvailability(seat, action.id);
        if (availability.status === "blocked") return null;
        return {
          decisionId: `select_${action.id}`,
          label: renderSimulationCopy(
            simulationCopy.decisions.selectAction,
            { action: action.name }
          ),
          actionId: action.id,
          consequences: {
            stage: "action_selection",
            ...availability
          }
        };
      })
      .filter(Boolean);
  }

  selectionAvailability(seat, actionId) {
    const currentResolutionCount = this.currentResolutionCountForSelection(
      seat,
      actionId
    );
    return {
      currentResolutionCount,
      resolvableWithoutTrade: currentResolutionCount > 0,
      resolvableWithImmediateTrade: false,
      status: currentResolutionCount > 0 ? "resolvable_now" : "blocked"
    };
  }

  currentResolutionCountForSelection(seat, actionId) {
    return this.legalResolutions(seat, actionId).length;
  }

  movementVariants(player, build) {
    return player.pieces.flatMap((piece) =>
      this.legalDestinations(player, piece).flatMap((destination) =>
        build(piece, destination)
      )
    );
  }

  legalResolutions(seat, actionId) {
    const player = this.players[seat];
    const variants = this.movementVariants(player, (piece, destination) => {
      const base = {
        pieceId: piece.id,
        destinationId: destination.instanceId,
        destinationCategory: destination.category
      };
      const suffix = `${piece.id}_${destination.instanceId}`;

      if (actionId === "fund") {
        return [
          {
            decisionId: `fund_conservative_${suffix}`,
            label: renderSimulationCopy(simulationCopy.decisions.moveAndFundConservative, {
              piece: piece.id,
              destination: destination.name
            }),
            actionId,
            parameters: { ...base, mode: "conservative" },
            consequences: { runway: 2, scrutiny: 0 }
          },
          {
            decisionId: `fund_venture_${suffix}`,
            label: renderSimulationCopy(simulationCopy.decisions.moveAndFundVenture, {
              piece: piece.id,
              destination: destination.name
            }),
            actionId,
            parameters: { ...base, mode: "venture" },
            consequences: { runway: 4, scrutiny: 2 }
          }
        ];
      }

      if (actionId === "research" && player.compute >= 1) {
        return [2, 3, 4, 5, 6, 7].map((stopAt) => ({
          decisionId: `research_stop_${stopAt}_${suffix}`,
          label: renderSimulationCopy(simulationCopy.decisions.moveAndResearch, {
            piece: piece.id,
            destination: destination.name,
            stopAt
          }),
          actionId,
          parameters: { ...base, stopAt },
          consequences: { compute: -1, stopAt }
        }));
      }

      if (actionId === "build") {
        const decisions = [];
        if (
          player.runway >= 2 &&
          player.facilities.length < this.config.playerSupply.facilities &&
          FACILITY_CATEGORIES.has(destination.category) &&
          this.tileOccupancy(destination.instanceId) <
            (destination.facilitySpaces ?? this.config.board.facilitySpacesPerHex)
        ) {
          decisions.push({
            decisionId: `build_facility_${destination.category}_${suffix}`,
            label: renderSimulationCopy(simulationCopy.decisions.moveAndBuildFacility, {
              piece: piece.id,
              destination: destination.name
            }),
            actionId,
            parameters: { ...base, buildMode: "facility" },
            consequences: { runway: -2, facility: destination.category }
          });
        }
        if (
          destination.category === "energy" &&
          player.generators.length < this.config.playerSupply.generators &&
          this.generatorOccupancy(destination.instanceId) < 3
        ) {
          const locationRule = this.config.singleGeneratorRule.locations[destination.id];
          const source = locationRule && this.config.powerSources.find(
            (candidate) => candidate.id === locationRule.sourceId
          );
          if (source && locationRule.constructionCost <= player.runway) {
            decisions.push({
              decisionId: `build_generator_${source.id}_${suffix}`,
              label: renderSimulationCopy(simulationCopy.decisions.moveAndBuildPower, {
                piece: piece.id,
                destination: destination.name,
                source: source.name
              }),
              actionId,
              parameters: { ...base, buildMode: "generator", sourceId: source.id },
              consequences: {
                runway: -locationRule.constructionCost,
                generation: source.capacity,
                scrutiny: source.scrutinyOnBuild || 0
              }
            });
          }
        }
        return decisions;
      }

      if (actionId === "organize") {
        return [{
          decisionId: `organize_reposition_${suffix}`,
          label: renderSimulationCopy(simulationCopy.decisions.reposition, {
            piece: piece.id,
            destination: destination.name
          }),
          actionId,
          parameters: { ...base, mode: "reposition" },
          consequences: { mobilityOnly: true }
        }];
      }

      if (actionId === "deploy" && this.canDeploy(player)) {
        const computeCost = destination.category === "consumer" ? 0 : 1;
        if (player.compute < computeCost) return [];
        return [{
          decisionId: `deploy_${destination.category}_${suffix}`,
          label: renderSimulationCopy(simulationCopy.decisions.moveAndDeploy, {
            piece: piece.id,
            destination: destination.name,
            customer: player.customers + 1
          }),
          actionId,
          parameters: { ...base, computeCost },
          consequences: { compute: -computeCost, customers: 1, scrutiny: 1 }
        }];
      }

      if (actionId === "influence") {
        if (!POLITICAL_CATEGORIES.has(destination.category)) return [];
        const decisions = [];
        decisions.push({
          decisionId: `influence_gain_trust_${suffix}`,
          label: renderSimulationCopy(simulationCopy.decisions.gainTrust, {
            piece: piece.id,
            destination: destination.name
          }),
          actionId,
          parameters: { ...base, mode: "trust" },
          consequences: {
            trust: player.trust < this.config.resources.trust.cap
              ? destination.category === "government" ? 2 : 1
              : 0
          }
        });
        if (player.scrutiny > 0) {
          decisions.push({
            decisionId: `influence_remove_scrutiny_${suffix}`,
            label: renderSimulationCopy(simulationCopy.decisions.removeScrutiny, {
              piece: piece.id,
              destination: destination.name
            }),
            actionId,
            parameters: { ...base, mode: "scrutiny" },
            consequences: { scrutiny: destination.category === "media" ? -2 : -1 }
          });
        }
        return decisions;
      }

      return [];
    });
    return variants;
  }

  recordPolicyReceipt(player, receipt) {
    const provider = receipt.provider || "unknown";
    player.metrics.policyProviders[provider] =
      (player.metrics.policyProviders[provider] || 0) + 1;
    if (receipt.fallback) player.metrics.policyFallbacks += 1;
    if (provider.includes("cli") || receipt.cached || receipt.fallback || receipt.gated) {
      player.metrics.policyReceipts.push({
        provider,
        model: receipt.model || null,
        reasoningEffort: receipt.reasoningEffort || null,
        requestId: receipt.requestId || null,
        decisionId: receipt.decisionId || null,
        promptSha256: receipt.promptSha256 || null,
        cached: Boolean(receipt.cached),
        cacheKey: receipt.cacheKey || null,
        fallback: Boolean(receipt.fallback),
        gated: Boolean(receipt.gated),
        fallbackReason: receipt.fallbackReason || null,
        durationMs: receipt.durationMs ?? null,
        attemptedProvider: receipt.attemptedProvider || null,
        attemptedModel: receipt.attemptedModel || null,
        attemptedReasoningEffort: receipt.attemptedReasoningEffort || null,
        attemptedRequestId: receipt.attemptedRequestId || null,
        attemptedPromptSha256: receipt.attemptedPromptSha256 || null,
        providerErrorClass: receipt.providerErrorClass || null,
        providerErrorMessage: receipt.providerErrorMessage || null,
        providerErrorExitCode: receipt.providerErrorExitCode ?? null,
        providerErrorStderrSha256: receipt.providerErrorStderrSha256 || null,
        providerDurationMs: receipt.providerDurationMs ?? null,
        brokerTaskIndex: receipt.brokerTaskIndex ?? null,
        brokerRequestToken: receipt.brokerRequestToken || null,
        brokerAttempts: receipt.brokerAttempts ?? null,
        brokerRetries: receipt.brokerRetries ?? null,
        brokerQueuedMs: receipt.brokerQueuedMs ?? null
      });
    }
  }

  movePiece(player, parameters) {
    const piece = player.pieces.find((candidate) => candidate.id === parameters.pieceId);
    if (piece) piece.tileId = parameters.destinationId;
  }

  applyResolution(seat, decision) {
    const player = this.players[seat];
    const parameters = decision.parameters || {};
    if (decision.consequences?.noOp) {
      player.actionsUsed.push(decision.actionId);
      player.metrics.actions[decision.actionId] =
        (player.metrics.actions[decision.actionId] || 0) + 1;
      this.recordEvent(
        "action_blocked",
        seat,
        `${player.factionName}: ${decision.label}.`
      );
      return;
    }
    this.movePiece(player, parameters);

    if (decision.actionId === "fund") {
      this.addResource(player, "runway", parameters.mode === "venture" ? 4 : 2);
      if (parameters.mode === "venture") this.addScrutiny(player, 2);
    } else if (decision.actionId === "research") {
      player.compute -= 1;
      const result = this.resolveTrainingRun(seat, player, parameters);
      player.lastTrainingResult = result;
      this.addResource(player, "capability", result.capability);
      this.addResource(player, "trust", result.trust);
      this.spendRunway(player, result.runwaySpent, {
        cause: "research_training",
        conversionEligible: true
      });
      player.safety -= result.safetySpent;
      this.addScrutiny(player, result.scrutiny);
      player.metrics.researchCapability.push(result.capability);
    } else if (decision.actionId === "build") {
      if (parameters.buildMode === "facility") {
        this.spendRunway(player, parameters.actualRunwayCost ?? 2, {
          cause: "build_facility",
          conversionEligible: true
        });
        player.facilities.push({
          id: `s${seat}-facility-${player.facilities.length + 1}`,
          tileId: parameters.destinationId,
          category: parameters.destinationCategory,
          powered: false,
          gridReady: false,
          gridReadySupportSeats: []
        });
      } else if (parameters.buildMode === "generator") {
        const source = this.config.powerSources.find(
          (candidate) => candidate.id === parameters.sourceId
        );
        this.spendRunway(player, parameters.actualRunwayCost ?? source.runwayCost, {
          cause: "build_generator",
          conversionEligible: true
        });
        this.addResource(player, "trust", source.trust || 0);
        this.addScrutiny(player, source.scrutinyOnBuild || 0);
        player.generators.push({
          id: `s${seat}-generator-${player.generators.length + 1}`,
          tileId: parameters.destinationId,
          sourceId: source.id,
          capacity: source.capacity
        });
      }
    } else if (decision.actionId === "deploy") {
      player.compute -= parameters.computeCost;
      player.customers += 1;
      this.addScrutiny(player, 1);
    } else if (decision.actionId === "influence") {
      if (parameters.mode === "trust") {
        this.addResource(player, "trust", parameters.destinationCategory === "government" ? 2 : 1);
      } else {
        this.removeScrutiny(player, parameters.destinationCategory === "media" ? 2 : 1);
      }
    }

    player.actionsUsed.push(decision.actionId);
    player.metrics.actions[decision.actionId] =
      (player.metrics.actions[decision.actionId] || 0) + 1;
    if (this.round === 1) player.metrics.openingActions.push(decision.actionId);
    this.recordEligibility(player, "after_action");
    this.recordEvent(
      "action_resolved",
      seat,
      `${player.factionName}: ${decision.label}.`
    );
  }

  resolveTrainingRun(seat, player, parameters) {
    return simulateTrainingRun(
      this.config,
      `${this.seed}:r${this.round}:c${this.cycle}:s${seat}:training`,
      {
        stopAt: parameters.stopAt,
        runway: player.runway,
        safety: player.safety
      }
    );
  }

  recordEligibility(player, timing) {
    const requirement = this.config.agiDeclaration;
    if (
      !player.metrics.earliestAgiEligibility &&
      player.capability >= requirement.capability &&
      player.customers >= requirement.customers &&
      player.facilities.length >= requirement.facilities &&
      player.trust >= requirement.trust &&
      player.compute >= requirement.computeCost
    ) {
      player.metrics.earliestAgiEligibility = {
        round: this.round,
        cycle: this.cycle,
        timing
      };
    }
  }

  produce(player) {
    const firstFacility = player.facilities[0];
    const starter = firstFacility
      ? this.config.board.startingGridConnection.capacity
      : 0;
    let generated = 0;
    for (const generator of player.generators) {
      const source = this.config.powerSources.find(
        (candidate) => candidate.id === generator.sourceId
      );
      generated += generator.capacity;
      if (source.scrutinyPerUse) this.addScrutiny(player, source.scrutinyPerUse);
    }
    let available = starter + generated;
    for (const facility of player.facilities) {
      const demand = 1;
      facility.powered = available >= demand;
      if (facility.powered) available -= demand;
    }

    for (const facility of player.facilities.filter((candidate) => candidate.powered)) {
      const multiplier = 1;
      if (facility.category === "cloud") this.addResource(player, "compute", 2 * multiplier);
      if (facility.category === "research") this.addResource(player, "safety", 1 * multiplier);
      if (facility.category === "consumer") this.addResource(player, "runway", 1 * multiplier);
      if (facility.category === "chip") this.addResource(player, "compute", 1 * multiplier);
      if (facility.category === "capital") this.addResource(player, "runway", 2 * multiplier);
      if (facility.category === "media") this.removeScrutiny(player, 1 * multiplier);
      if (facility.category === "frontier") {
        player.mandate += 1 * multiplier;
        this.addScrutiny(player, 1 * multiplier);
      }
    }
    this.addResource(player, "runway", player.customers);
    const powered = player.facilities.filter((facility) => facility.powered).length;
    player.metrics.poweredFacilityRounds.push({
      round: this.round,
      powered,
      facilities: player.facilities.length,
      supply: starter + generated
    });
    this.recordEligibility(player, "after_production");
  }

  audit() {
    const draws = calculateAuditDraws(
      this.config.rounds[this.round - 1].auditBaseDraws,
      this.playerCount
    );
    const rng = createRng(`${this.seed}:audit:${this.round}`);
    for (let draw = 0; draw < draws; draw += 1) {
      const bag = this.players.flatMap((player) =>
        Array.from({ length: player.scrutiny }, () => player.seat)
      );
      if (bag.length === 0) break;
      const seat = bag[Math.floor(rng() * bag.length)];
      const player = this.players[seat];
      player.scrutiny -= 1;
      player.metrics.auditHits += 1;
      if (player.runway > 0) this.spendRunway(player, 1);
      else this.addResource(player, "trust", -1);
    }
  }

  finishRound() {
    for (const player of this.players) this.produce(player);
    this.audit();
    this.recordEvent(
      "round_settled",
      null,
      renderSimulationCopy(simulationCopy.events.roundSettled, { round: this.round })
    );
    if (this.round === this.config.rounds.at(-1).number) {
      this.complete = true;
      return;
    }
    this.round += 1;
    this.cycle = 1;
    for (const player of this.players) {
      player.actionsUsed = [];
      player.selectedAction = null;
    }
  }

  initiativeOrder() {
    return Array.from(
      { length: this.playerCount },
      (_, offset) => (this.initiativeSeat + offset) % this.playerCount
    );
  }

  async playCycle(policies) {
    const selectionPackets = this.players.map((player) =>
      this.packet(player.seat, "select", this.legalActionSelections(player.seat))
    );
    const selections = await Promise.all(
      selectionPackets.map((packet, seat) => policies[seat].decide(packet))
    );
    for (const [seat, result] of selections.entries()) {
      const player = this.players[seat];
      player.selectedAction = result.decision.decisionId.replace(/^select_/, "");
      this.recordPolicyReceipt(player, result.receipt);
      this.recordEvent(
        "action_selected",
        seat,
        `${player.factionName} selected ${player.selectedAction}.`
      );
    }

    for (const seat of this.initiativeOrder()) {
      const player = this.players[seat];
      let legal = this.legalResolutions(seat, player.selectedAction);
      if (legal.length === 0) {
        legal = [{
          decisionId: `forced_noop_${player.selectedAction}`,
          label: renderSimulationCopy(simulationCopy.decisions.noLegalResolution, {
            action: player.selectedAction
          }),
          actionId: player.selectedAction,
          parameters: {},
          consequences: { noOp: true }
        }];
      }
      const packet = this.packet(seat, "resolve", legal);
      const result = await policies[seat].decide(packet);
      this.recordPolicyReceipt(player, result.receipt);
      const decision = legal.find(
        (candidate) => candidate.decisionId === result.decision.decisionId
      );
      this.applyResolution(seat, decision);
      player.selectedAction = null;
    }

    this.initiativeSeat = (this.initiativeSeat + 1) % this.playerCount;
    const cycleLimit = this.config.rounds.find((round) => round.number === this.round).cycles;
    if (this.cycle === cycleLimit) this.finishRound();
    else this.cycle += 1;
  }

  async play(policies) {
    while (!this.complete) await this.playCycle(policies);
    return this.result();
  }

  snapshot() {
    return {
      round: this.round,
      cycle: this.cycle,
      initiativeSeat: this.initiativeSeat,
      board: this.board.map((tile) => ({
        instanceId: tile.instanceId,
        name: tile.name,
        category: tile.category,
        q: tile.q,
        r: tile.r
      })),
      players: this.players.map((player) => ({
        seat: player.seat,
        factionId: player.factionId,
        factionName: player.factionName,
        profileId: player.profileId,
        backendId: player.backendId,
        model: player.model,
        reasoningEffort: player.reasoningEffort,
        runway: player.runway,
        compute: player.compute,
        capability: player.capability,
        customers: player.customers,
        trust: player.trust,
        scrutiny: player.scrutiny,
        mandate: player.mandate,
        pieces: clone(player.pieces),
        facilities: clone(player.facilities),
        generators: clone(player.generators)
      }))
    };
  }

  recordEvent(type, seat, summary, decisionReceipt = null) {
    if (type !== "strategy_decision") {
      const event = {
        type,
        round: this.round,
        cycle: this.cycle,
        seat
      };
      if (this.projection === "rich" || this.recordReplay) event.summary = summary;
      this.publicHistory.push(event);
    }
    if (!this.recordReplay) return;
    this.replay.push({
      index: this.replay.length,
      type,
      round: this.round,
      cycle: this.cycle,
      seat,
      summary,
      decisionReceipt: decisionReceipt ? {
        provider: decisionReceipt.provider || null,
        model: decisionReceipt.model || null,
        reasoningEffort: decisionReceipt.reasoningEffort || null,
        requestId: decisionReceipt.requestId || null,
        decisionId: decisionReceipt.decisionId || null,
        fallback: Boolean(decisionReceipt.fallback),
        attemptedProvider: decisionReceipt.attemptedProvider || null,
        attemptedModel: decisionReceipt.attemptedModel || null,
        attemptedReasoningEffort: decisionReceipt.attemptedReasoningEffort || null
      } : null,
      state: this.snapshot()
    });
  }

  result() {
    const standings = this.players
      .map((player) => ({
        seat: player.seat,
        factionId: player.factionId,
        factionName: player.factionName,
        profileId: player.profileId,
        score: finalMandate(this.config, player),
        trust: player.trust,
        customers: player.customers,
        compute: player.compute,
        capability: player.capability,
        facilities: player.facilities.length,
        metrics: clone(player.metrics)
      }))
      .sort((left, right) =>
        right.score - left.score ||
        right.trust - left.trust ||
        right.customers - left.customers ||
        right.compute - left.compute ||
        left.seat - right.seat
      );
    const best = standings[0];
    const winnerSeats = standings
      .filter((entry) =>
        entry.score === best.score &&
        entry.trust === best.trust &&
        entry.customers === best.customers &&
        entry.compute === best.compute
      )
      .map((entry) => entry.seat);
    return {
      schemaVersion: 1,
      evidenceLabel: "simulation",
      scope: CORE_ECONOMY_COVERAGE,
      seed: this.seed,
      playerCount: this.playerCount,
      standings,
      winnerSeats,
      replay: this.recordReplay ? this.replay : undefined
    };
  }
}
