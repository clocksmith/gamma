import {
  applyBoardMotion,
  axialDistance,
  buildTrainingDeck,
  createRng,
  networkedFacilityIds,
  publicMandateAwards,
  resolveBlindRealignmentVote,
  simulateTrainingRun
} from "../../web/src/engine.js";
import { declarationReadiness } from "../rules/declaration-readiness.js";
import {
  applyAgiDeclarationScenario,
  finalizeAgiDeclarationScenario,
  markScenarioDeclaration,
  validateAgiDeclarationScenario
} from "../scenarios/agi-declaration-window.js";
import { CoreEconomyMatch } from "./core-economy-match.js";
import { effectiveRulesVariant } from "./rules-variant.js";
import {
  renderSimulationCopy,
  simulationCopy
} from "../content/simulation-copy.js";
import { throwIfAborted } from "../cancellation.js";

export const SELECTED_RULES_COVERAGE = simulationCopy.coverage.selectedRules;
const ACTION_RESOLUTIONS_PER_PLAYER = 12;
const decisionLabel = (key, values = {}) =>
  renderSimulationCopy(simulationCopy.decisions[key], values);

const CUSTOMER_REQUIREMENTS = [2, 4, 6, 8, 10];
const POLITICAL_CATEGORIES = new Set(["media", "government", "capital"]);
const RESOURCE_BY_CATEGORY = {
  cloud: "compute",
  chip: "compute",
  capital: "runway",
  consumer: "runway",
  research: "safety"
};

function clone(value) {
  return structuredClone(value);
}

function shuffled(values, seed) {
  const result = [...values];
  const rng = createRng(seed);
  for (let index = result.length - 1; index > 0; index -= 1) {
    const target = Math.floor(rng() * (index + 1));
    [result[index], result[target]] = [result[target], result[index]];
  }
  return result;
}

function increment(target, key, amount = 1) {
  target[key] = (target[key] || 0) + amount;
}

function edgeKey(left, right) {
  return [left, right].sort().join("::");
}

export function immediateTradePacketCeiling(playerCount) {
  if (!Number.isInteger(playerCount) || playerCount < 2) {
    throw new RangeError("Immediate-trade packet ceiling requires at least two players.");
  }
  // Per resolution: active offer/pass, named response, n - 1 claims, and
  // counteroffer-maker selection: n + 2 formal packets.
  return ACTION_RESOLUTIONS_PER_PLAYER * playerCount * (playerCount + 2);
}

function permutations(values) {
  if (values.length < 2) return [values];
  return values.flatMap((value, index) =>
    permutations(values.filter((_, candidate) => candidate !== index))
      .map((rest) => [value, ...rest])
  );
}

export function causallyNecessaryImportSuppliers({
  localAvailable,
  importedSupplierSeats,
  allocatedDemand
}) {
  const suppliers = [...new Set(importedSupplierSeats || [])];
  if (!suppliers.length) return [];
  const totalAvailable = localAvailable + suppliers.length;
  return allocatedDemand > totalAvailable - 1 ? suppliers : [];
}

export class SelectedRulesMatch extends CoreEconomyMatch {
  constructor({
    config,
    factions,
    profiles,
    backends = [],
    models = [],
    reasoningEfforts = [],
    headlines,
    wildActions,
    tactics,
    mandates,
    objectives,
    seed,
    playerCount = 4,
    recordReplay = false,
    projection = "rich",
    rulesVariant = {},
    mandateMode = "variable",
    simulateNegotiation = false,
    scenario = null,
    decisionContext = null,
    onProgress = null,
    signal
  }) {
    super({
      config,
      factions,
      profiles,
      backends,
      models,
      reasoningEfforts,
      seed,
      playerCount,
      recordReplay,
      projection,
      decisionContext
    });
    this.scope = SELECTED_RULES_COVERAGE;
    this.factions = factions;
    this.headlineDocument = headlines;
    this.wildDocument = wildActions;
    this.tacticDocument = tactics;
    this.mandateDocument = mandates;
    this.objectiveDocument = objectives;
    this.rulesVariant = effectiveRulesVariant(config, rulesVariant);
    const coalition = this.players.find(
      (player) => player.factionId === "coalition_lab"
    );
    if (coalition && Number.isFinite(this.rulesVariant.coalitionStartingRunway)) {
      coalition.runway = this.rulesVariant.coalitionStartingRunway;
    }
    const imperial = this.players.find(
      (player) => player.factionId === "imperial_research_lab"
    );
    if (imperial && Number.isFinite(this.rulesVariant.imperialStartingCompute)) {
      imperial.compute = this.rulesVariant.imperialStartingCompute;
    }
    const vertical = this.players.find(
      (player) => player.factionId === "vertical_empire"
    );
    if (vertical && Number.isFinite(this.rulesVariant.verticalStartingCompute)) {
      vertical.compute = this.rulesVariant.verticalStartingCompute;
    }
    const foundry = this.players.find((player) => player.factionId === "foundry");
    if (foundry) {
      foundry.compute = this.rulesVariant.foundryStartingCompute;
    }
    const safety = this.players.find((player) => player.factionId === "safety_laboratory");
    if (safety && Number.isFinite(this.rulesVariant.safetyStartingTrust)) {
      safety.trust = this.rulesVariant.safetyStartingTrust;
    }
    if (!["variable", "fixed"].includes(mandateMode)) {
      throw new TypeError(`Unknown Mandate mode: ${mandateMode}.`);
    }
    this.mandateMode = mandateMode;
    this.simulateNegotiation = Boolean(simulateNegotiation);
    this.scenario = validateAgiDeclarationScenario(scenario, playerCount);
    this.onProgress = typeof onProgress === "function" ? onProgress : null;
    this.signal = signal;
    this.negotiationPromises = [];
    this.relationships = new Map();
    this.systemicRisk = 0;
    this.decisionSerial = 0;
    this.activeImmediateTradeSeat = null;
    this.immediateTradeDecisionWindows = new Set();
    this.immediateTradePackets = 0;
    this.immediateTradePacketCeiling = immediateTradePacketCeiling(playerCount);
    this.contractSerial = 0;
    this.contracts = [];
    this.megaClusters = [];
    this.trainingDrawPile = buildTrainingDeck(config, `${seed}:training-deck`);
    this.trainingDiscard = [];
    this.trainingShuffle = 0;
    this.roundInitialized = false;
    this.firstAgiSeat = null;
    this.matchMetrics = {
      headlines: {},
      headlineOutcomes: {},
      mandates: {},
      wildActions: {},
      tactics: {},
      realignments: {},
      systemicRiskCreated: 0,
      declarations: 0,
      declarationReadiness: [],
      agiFunnel: this.players.map((player) => ({
        seat: player.seat,
        coreRequirementsMet: null,
        neededExternalPower: null,
        receivedPowerOffer: null,
        acceptedPowerPrice: null,
        becameGridReady: null,
        legalDeclarationWindow: null,
        declared: null
      })),
      powerTrades: [],
      negotiations: [],
      round4Start: null,
      futureTimeline: [],
      productionSnapshots: []
    };
    this.activeHeadline = null;
    this.regime = {};
    this.spotlightSeat = 0;
    this.grantSeat = this.players.length - 1;
    this.roundMandate = null;
    this.headlineDecks = Object.fromEntries(
      this.config.rounds.map(({ number: round }) => [
        round,
        shuffled(
          this.headlineDocument.headlines.filter((card) => card.round === round),
          `${seed}:headlines:${round}`
        ).slice(0, 3)
      ])
    );
    this.mandateDeck = Object.fromEntries(
      this.config.rounds.map(({ number: round }) => [
        round,
        mandateMode === "fixed"
          ? this.mandateDocument.mandates.find((card) => card.era === round)
          : shuffled(
            this.mandateDocument.mandates.filter((card) => card.era === round),
            `${seed}:mandates:${round}`
          )[0]
      ])
    );

    for (const player of this.players) {
      const deployedTeams = Math.max(
        0,
        Math.min(config.playerSupply.teams, this.rulesVariant.startingTeamsDeployed)
      );
      player.pieces = player.pieces.filter(
        (piece) => piece.kind !== "team" ||
          Number(piece.id.split("-").at(-1)) <= deployedTeams
      );
      player.teamsInSupply = config.playerSupply.teams - deployedTeams;
      player.escalation = 0;
      player.wildUsed = [];
      player.tactics = [];
      player.objectiveId = null;
      player.links = [];
      player.linkSupply = config.playerSupply.linkTokens;
      player.jointVentures = [];
      player.megaClusters = [];
      player.experts = [];
      player.marketAccess = 0;
      player.policyShields = 0;
      player.buildDiscounts = 0;
      player.agiDeclared = false;
      player.factionAbilityUsed = {};
      player.tacticModifiers = {};
      player.history = {
        deployRounds: [],
        wildRounds: [],
        cumulativeScrutiny: player.scrutiny,
        jointVenturePartners: [],
        openWeightsCapabilitySnapshot: null,
        fusionBuilt: false,
        declarations: 0
      };
      player.roundMetrics = {};
      player.metrics.headlines = {};
      player.metrics.wildActions = {};
      player.metrics.tactics = {};
      player.metrics.mandatesWon = {};
      player.metrics.objectiveCompleted = false;
      player.metrics.systemicRiskHits = 0;
      player.metrics.generatorChoices = {};
      player.metrics.generatorScrutiny = {};
      player.metrics.powerBought = 0;
      player.metrics.powerSold = 0;
      player.metrics.powerTradeRunway = 0;
      player.metrics.shovelsIncome = 0;
      player.metrics.factionAbilityValues = {};
      player.metrics.mandateEvents = [];
      player.dealFlowRunwayCredits = [];
      player.metrics.dealFlowConversion = {
        creditsGranted: 0,
        creditsSpent: 0,
        causallyNecessaryCreditsSpent: 0,
        conversionEligibleCreditsSpent: 0,
        nonConversionCreditsSpent: 0,
        mandateAttributed: 0,
        events: []
      };
      player.metrics.gridReadyFacilityRounds = [];
      player.metrics.promisesMade = 0;
      player.metrics.promisesFulfilled = 0;
      player.metrics.promisesBroken = 0;
      player.mandateAwards = [];
      this.synchronizePublicMandate(player, "setup");
    }
    this.replay = [];
    this.publicHistory = [];
    this.recordEvent("match_started", null, simulationCopy.events.selectedMatchStarted);
  }

  isFactionAbilityPaused(player, abilityId) {
    return this.rulesVariant.pausedFactionAbilities.some((entry) =>
      entry?.factionId === player.factionId && entry?.abilityId === abilityId
    );
  }

  isEmergencyPauseEnabled(player) {
    return this.rulesVariant.safetyEmergencyPauseEnabled &&
      !this.isFactionAbilityPaused(player, "emergency_pause");
  }

  addResource(player, key, amount) {
    if (key === "safety" && player.factionId === "safety_laboratory") {
      player.safety = Math.max(0, Math.min(4, player.safety + amount));
      return;
    }
    super.addResource(player, key, amount);
    if (
      (key === "capability" || key === "trust") &&
      !this.deferredPublicMandateSeats?.has(player.seat)
    ) {
      this.synchronizePublicMandate(player, `${key}_threshold`);
    }
  }

  beginRunwayConversionContext(player, decision, kind = "action") {
    this.runwayConversionContexts ||= [];
    this.runwayConversionContexts.push({
      player,
      actionId: decision.actionId,
      decisionId: decision.decisionId,
      kind,
      events: []
    });
  }

  endRunwayConversionContext(player) {
    const context = this.runwayConversionContexts?.at(-1);
    if (context?.player === player) this.runwayConversionContexts.pop();
  }

  grantDealFlowRunway(player, details = {}) {
    const before = player.runway;
    this.addResource(player, "runway", 1);
    const granted = player.runway - before;
    if (!granted) return 0;
    const credit = {
      id: `deal-flow-r${this.round}-c${this.cycle}-s${player.seat}-` +
        `${player.metrics.dealFlowConversion.creditsGranted + 1}`,
      round: this.round,
      cycle: this.cycle,
      remaining: granted,
      ...clone(details)
    };
    player.dealFlowRunwayCredits.push(credit);
    player.metrics.dealFlowConversion.creditsGranted += granted;
    return granted;
  }

  spendRunway(player, amount, details = {}) {
    const before = player.runway;
    const spent = Math.min(before, Math.max(0, Number(amount) || 0));
    if (!spent) return 0;
    const taggedBefore = player.dealFlowRunwayCredits.reduce(
      (sum, credit) => sum + credit.remaining,
      0
    );
    const untaggedBefore = Math.max(0, before - taggedBefore);
    let taggedSpent = Math.min(taggedBefore, Math.max(0, spent - untaggedBefore));
    let remainingTaggedSpend = taggedSpent;
    for (const credit of player.dealFlowRunwayCredits) {
      if (!remainingTaggedSpend) break;
      const consumed = Math.min(credit.remaining, remainingTaggedSpend);
      credit.remaining -= consumed;
      remainingTaggedSpend -= consumed;
    }
    player.runway -= spent;
    if (!taggedSpent) return spent;

    const context = [...(this.runwayConversionContexts || [])]
      .reverse()
      .find((candidate) => candidate.player === player);
    const conversionEligible = Boolean(details.conversionEligible && context);
    const event = {
      round: this.round,
      cycle: this.cycle,
      cause: details.cause || "runway_spend",
      actionId: context?.actionId || null,
      decisionId: context?.decisionId || null,
      contextKind: context?.kind || null,
      runwaySpent: spent,
      dealFlowCreditsSpent: taggedSpent,
      causallyNecessaryCreditsSpent: conversionEligible ? taggedSpent : 0,
      conversionEligible,
      mandateAttributed: 0
    };
    player.metrics.dealFlowConversion.creditsSpent += taggedSpent;
    if (conversionEligible) {
      player.metrics.dealFlowConversion.causallyNecessaryCreditsSpent += taggedSpent;
      player.metrics.dealFlowConversion.conversionEligibleCreditsSpent += taggedSpent;
      context.events.push(event);
    } else {
      player.metrics.dealFlowConversion.nonConversionCreditsSpent += taggedSpent;
    }
    player.metrics.dealFlowConversion.events.push(event);
    return spent;
  }

  currentAgiRequirements() {
    return {
      capability: this.regime.cycle?.id === "agi_blog_post"
        ? Math.max(1, this.rulesVariant.agiCapability - 1)
        : this.rulesVariant.agiCapability,
      customers: this.rulesVariant.agiCustomers,
      facilities: this.rulesVariant.agiFacilities,
      trust: this.regime.persistent?.agiPersonhood === "person"
        ? Math.max(4, this.rulesVariant.agiTrust)
        : this.rulesVariant.agiTrust,
      computeCost: this.rulesVariant.agiComputeCost
    };
  }

  markAgiFunnel(player, stage, timing, details = {}) {
    const entry = this.matchMetrics.agiFunnel[player.seat];
    if (!entry || entry[stage]) return;
    entry[stage] = {
      round: this.round,
      cycle: this.cycle,
      timing,
      ...clone(details)
    };
  }

  recordAgiCoreRequirements(player, timing) {
    const requirements = this.currentAgiRequirements();
    if (
      player.capability >= requirements.capability &&
      player.customers >= requirements.customers &&
      player.trust >= requirements.trust
    ) {
      this.markAgiFunnel(player, "coreRequirementsMet", timing, {
        capability: player.capability,
        customers: player.customers,
        trust: player.trust
      });
    }
  }

  recordFactionAbility(player, abilityId, values = {}) {
    const entry = player.metrics.factionAbilityValues[abilityId] || {
      uses: 0
    };
    entry.uses += values.uses ?? 1;
    for (const [key, value] of Object.entries(values)) {
      if (key === "uses") continue;
      // Ability telemetry mixes additive measurements with descriptive fields
      // such as Allocation Window's payment resource. Never coerce strings
      // into repeated numeric aggregates ("runwayrunway").
      if (typeof value === "number") {
        entry[key] = (Number(entry[key]) || 0) + value;
      } else if (entry[key] === undefined) {
        entry[key] = value;
      } else if (entry[key] !== value) {
        entry[key] = [...new Set([].concat(entry[key], value))];
      }
    }
    player.metrics.factionAbilityValues[abilityId] = entry;
  }

  addScrutiny(player, amount) {
    const before = player.metrics.scrutinyAdded;
    super.addScrutiny(player, amount);
    player.history.cumulativeScrutiny += player.metrics.scrutinyAdded - before;
  }

  prepareTrainingDrawPile() {
    if (!this.trainingDrawPile.length && this.trainingDiscard.length) {
      const remainder = shuffled(
        this.trainingDiscard,
        `${this.seed}:training-reshuffle:${this.trainingShuffle}`
      );
      this.trainingShuffle += 1;
      this.trainingDrawPile.push(...remainder);
      this.trainingDiscard = [];
    }
    return this.trainingDrawPile;
  }

  resolveTrainingRun(seat, player, parameters) {
    this.prepareTrainingDrawPile();
    let deck = this.trainingDrawPile.map((card) => ({ ...card }));
    let result = simulateTrainingRun(
      this.config,
      `${this.seed}:r${this.round}:c${this.cycle}:s${seat}:training`,
      {
        deck,
        stopAt: parameters.stopAt,
        runway: player.runway,
        safety: player.safety
      }
    );
    if (result.deckExhausted && this.trainingDiscard.length) {
      const remainder = shuffled(
        this.trainingDiscard,
        `${this.seed}:training-reshuffle:${this.trainingShuffle}`
      );
      this.trainingShuffle += 1;
      deck = [...deck, ...remainder];
      result = simulateTrainingRun(
        this.config,
        `${this.seed}:r${this.round}:c${this.cycle}:s${seat}:training`,
        {
          deck,
          stopAt: parameters.stopAt,
          runway: player.runway,
          safety: player.safety
        }
      );
      this.trainingDrawPile.push(...remainder);
      this.trainingDiscard = [];
    }
    const deckSnapshot = deck.map((card) => ({ ...card }));
    this.trainingDiscard.push(
      ...this.trainingDrawPile.splice(0, result.cardsDrawn)
    );
    return { ...result, deckSnapshot };
  }

  currentScore(player) {
    return player.mandate;
  }

  awardMandate(player, points, source) {
    if (!points) return;
    player.mandate += points;
    player.metrics.mandateEvents.push({
      round: this.round,
      cycle: this.cycle,
      source,
      points,
      total: player.mandate
    });
    const context = [...(this.runwayConversionContexts || [])]
      .reverse()
      .find((candidate) => candidate.player === player && candidate.events.length);
    if (context) {
      const event = context.events.at(-1);
      event.mandateAttributed += points;
      player.metrics.dealFlowConversion.mandateAttributed += points;
    }
    this.recordEvent(
      "mandate_awarded",
      player.seat,
      renderSimulationCopy(simulationCopy.events.mandateAwarded, {
        faction: player.factionName,
        points,
        source
      })
    );
  }

  synchronizePublicMandate(
    player,
    source,
    { capabilityMandatePenalty = 0 } = {}
  ) {
    const known = new Set(player.mandateAwards.map((award) => award.id));
    let remainingCapabilityMandatePenalty = Math.max(
      0,
      capabilityMandatePenalty
    );
    let capabilityMandateWithheld = 0;
    for (const baseAward of publicMandateAwards(this.config, player)) {
      let award = baseAward;
      if (baseAward.id.startsWith("customer-")) {
        const schedule = this.rulesVariant.customerMandateSchedule;
        const customerNumber = Number(
          baseAward.id.slice("customer-".length)
        );
        const points =
          schedule &&
          Number.isFinite(customerNumber) &&
          customerNumber >= schedule.lateFromCustomer
            ? schedule.lateMandate
            : schedule?.baseMandate ?? this.rulesVariant.customerMandate;
        award = { ...baseAward, points };
      } else if (
        baseAward.id.startsWith("capability-") &&
        Number.isFinite(this.rulesVariant.capabilityThresholdMandate)
      ) {
        award = {
          ...baseAward,
          points: this.rulesVariant.capabilityThresholdMandate
        };
      } else if (
        baseAward.id.startsWith("capability-") &&
        Number(baseAward.id.slice("capability-".length)) >=
          (this.rulesVariant.imperialLateCapabilityThresholdMandate
            ?.lateFromCapability ?? 9)
      ) {
        const lateCapability = Number(
          baseAward.id.slice("capability-".length)
        );
        const imperialValidation =
          this.rulesVariant.imperialLateCapabilityThresholdMandate;
        let imperialLateMandate = null;
        if (player.factionId === "imperial_research_lab") {
          if (Number.isFinite(imperialValidation)) {
            imperialLateMandate = imperialValidation;
          } else if (
            imperialValidation &&
            Number.isFinite(imperialValidation.baseMandate)
          ) {
            const broadlyValidated =
              lateCapability >=
                imperialValidation.fullValidationCapability &&
              this.players.length - 1 >=
                imperialValidation.minimumRivalsForFullMandate;
            imperialLateMandate = broadlyValidated
              ? imperialValidation.fullMandate
              : imperialValidation.baseMandate;
          }
        }
        award = {
          ...baseAward,
          points: imperialLateMandate ??
            this.rulesVariant.lateCapabilityThresholdMandate
        };
        if (
          imperialLateMandate !== null &&
          !known.has(baseAward.id) &&
          this.rulesVariant.lateCapabilityThresholdMandate >
            imperialLateMandate
        ) {
          this.recordFactionAbility(player, "late_public_validation", {
            mandateWithheld:
              this.rulesVariant.lateCapabilityThresholdMandate -
              imperialLateMandate,
            thresholdsValidated: 1
          });
        }
      }
      if (known.has(award.id)) continue;
      if (
        award.id.startsWith("capability-") &&
        remainingCapabilityMandatePenalty > 0
      ) {
        const withheld = Math.min(
          remainingCapabilityMandatePenalty,
          award.points
        );
        award = { ...award, points: award.points - withheld };
        remainingCapabilityMandatePenalty -= withheld;
        capabilityMandateWithheld += withheld;
      }
      player.mandateAwards.push({ ...award, source });
      this.awardMandate(player, award.points, award.id);
    }
    return { capabilityMandateWithheld };
  }

  controlledCategories(player) {
    const categories = new Set();
    for (const tile of this.board) {
      const scores = this.players.map((candidate) => {
        const pieces = candidate.pieces
          .filter((piece) => piece.tileId === tile.instanceId)
          .reduce((sum, piece) => sum + (piece.kind === "ceo" ? 2 : 1), 0);
        const facilities = candidate.facilities
          .filter((facility) => facility.tileId === tile.instanceId).length;
        const influence = candidate.influence
          .filter((cube) => cube.tileId === tile.instanceId).length;
        const experts = candidate.experts
          .filter((expert) => expert.tileId === tile.instanceId).length;
        return pieces + facilities + influence + experts;
      });
      const maximum = Math.max(...scores);
      if (maximum > 0 && scores.filter((score) => score === maximum).length === 1) {
        if (scores[player.seat] === maximum) categories.add(tile.category);
      }
    }
    return categories;
  }

  controller(category) {
    const tile = this.board.find((candidate) => candidate.category === category);
    if (!tile) return null;
    const scores = this.players.map((player) => {
      const pieces = player.pieces
        .filter((piece) => piece.tileId === tile.instanceId)
        .reduce((sum, piece) => sum + (piece.kind === "ceo" ? 2 : 1), 0);
      return pieces +
        player.facilities.filter((item) => item.tileId === tile.instanceId).length +
        player.influence.filter((item) => item.tileId === tile.instanceId).length +
        player.experts.filter((item) => item.tileId === tile.instanceId).length;
    });
    const maximum = Math.max(...scores);
    if (maximum === 0 || scores.filter((score) => score === maximum).length !== 1) return null;
    return scores.indexOf(maximum);
  }

  nearestInitiative(seats) {
    return this.initiativeOrder().find((seat) => seats.includes(seat));
  }

  publicObservation(seat) {
    const base = super.publicObservation(seat);
    const player = this.players[seat];
    return {
      ...base,
      activeHeadline: this.activeHeadline
        ? { id: this.activeHeadline.id, name: this.activeHeadline.name, text: this.activeHeadline.text }
        : null,
      roundMandate: this.roundMandate
        ? { id: this.roundMandate.id, name: this.roundMandate.name, rulesText: this.roundMandate.rulesText }
        : null,
      persistentRegimes: this.copyPublic(this.regime.persistent || {}),
      self: {
        ...base.self,
        escalation: player.escalation,
        wildUsed: [...player.wildUsed],
        tactics: [...player.tactics],
        objectiveId: player.objectiveId,
        teamsInSupply: player.teamsInSupply,
        influence: player.influence.length,
        links: player.links.length,
        jointVentures: player.jointVentures.length,
        marketAccess: player.marketAccess,
        policyShields: player.policyShields,
        buildDiscounts: player.buildDiscounts,
        agiDeclared: player.agiDeclared,
        dealFlowConversion: {
          unspentCredits: player.dealFlowRunwayCredits.reduce(
            (sum, credit) => sum + credit.remaining,
            0
          ),
          causallyNecessaryCreditsSpent:
            player.metrics.dealFlowConversion.causallyNecessaryCreditsSpent,
          mandateAttributed: player.metrics.dealFlowConversion.mandateAttributed
        },
        currentScore: this.currentScore(player)
      },
      opponents: base.opponents.map((opponent) => {
        const source = this.players[opponent.seat];
        return {
          ...opponent,
          currentScore: this.currentScore(source),
          influence: source.influence.length,
          escalation: source.escalation,
          agiDeclared: source.agiDeclared,
          relationship: this.relationshipFor(seat, source.seat)
        };
      }),
      publicTable: {
        players: this.players.map((candidate) => ({
          ...this.publicPlayerState(candidate),
          escalation: candidate.escalation,
          wildUsed: [...candidate.wildUsed],
          factionAbilityUsed: this.copyPublic(candidate.factionAbilityUsed || {}),
          teamsInSupply: candidate.teamsInSupply,
          links: [...candidate.links],
          jointVentures: this.copyPublic(candidate.jointVentures),
          megaClusters: this.copyPublic(candidate.megaClusters || []),
          marketAccess: candidate.marketAccess,
          policyShields: candidate.policyShields,
          buildDiscounts: candidate.buildDiscounts,
          temporaryCompute: candidate.temporaryCompute || 0,
          agiDeclared: candidate.agiDeclared,
          currentScore: this.currentScore(candidate)
        })),
        contracts: this.copyPublic(this.contracts),
        systemicRisk: this.systemicRisk
      }
    };
  }

  packet(seat, stage, legalDecisions) {
    const packet = super.packet(seat, `${stage}:${this.decisionSerial++}`, legalDecisions);
    packet.requestId = `${packet.matchId}:r${this.round}:c${this.cycle}:s${seat}:${stage}:${this.decisionSerial}`;
    return packet;
  }

  async choose(policies, seat, stage, legalDecisions) {
    throwIfAborted(this.signal);
    this.registerImmediateTradeDecisionWindow(seat, stage);
    const packet = this.packet(seat, stage, legalDecisions);
    const result = await policies[seat].decide(packet);
    this.recordPolicyReceipt(this.players[seat], result.receipt);
    const selected = legalDecisions.find(
      (decision) => decision.decisionId === result.decision.decisionId
    );
    if (!selected) throw new Error(`Policy selected missing decision ${result.decision.decisionId}.`);
    this.recordEvent("strategy_decision", seat, `${stage}: ${selected.label}.`, result.receipt);
    return selected;
  }

  registerImmediateTradeDecisionWindow(seat, stage) {
    if (!stage.startsWith("immediate_trade")) return;
    const activeSeat = this.activeImmediateTradeSeat ?? seat;
    const key = `${this.round}:${this.cycle}:${activeSeat}:${seat}:${stage}`;
    if (this.immediateTradeDecisionWindows.has(key)) {
      throw new Error(`Immediate-trade formal window repeated: ${key}.`);
    }
    this.immediateTradeDecisionWindows.add(key);
    this.immediateTradePackets += 1;
    if (this.immediateTradePackets > this.immediateTradePacketCeiling) {
      throw new Error(
        `Immediate-trade packet ceiling exceeded: ${this.immediateTradePackets}/` +
        `${this.immediateTradePacketCeiling}.`
      );
    }
  }

  relationshipFor(leftSeat, rightSeat) {
    return clone(this.relationships.get(`${leftSeat}:${rightSeat}`) || {
      fulfilled: 0,
      broken: 0
    });
  }

  changeRelationship(leftSeat, rightSeat, field) {
    for (const key of [`${leftSeat}:${rightSeat}`, `${rightSeat}:${leftSeat}`]) {
      const relationship = this.relationships.get(key) || { fulfilled: 0, broken: 0 };
      relationship[field] += 1;
      this.relationships.set(key, relationship);
    }
  }

  activePowerPromise(supplierSeat, buyerSeat) {
    return this.negotiationPromises.find((promise) =>
      promise.kind === "power" &&
      promise.promisorSeat === supplierSeat &&
      promise.targetSeat === buyerSeat &&
      promise.status === "open"
    );
  }

  async collectNegotiationIntents(policies) {
    if (!this.simulateNegotiation) return;
    for (const seat of this.initiativeOrder()) {
      const player = this.players[seat];
      const decisions = [{
        decisionId: "negotiation_none",
        label: decisionLabel("makeNoPromise"),
        actionId: "negotiation"
      }, ...this.players.filter((target) => target.seat !== seat).map((target) => ({
        decisionId: `negotiation_power_${target.seat}`,
        label: decisionLabel("promisePower", { seat: target.seat + 1 }),
        actionId: "negotiation",
        parameters: {
          targetSeat: target.seat,
          relationship: this.relationshipFor(seat, target.seat)
        },
        consequences: { promise: 1 }
      }))];
      const decision = await this.choose(policies, seat, "negotiation_intent", decisions);
      if (decision.parameters?.targetSeat === undefined) continue;
      for (const promise of this.negotiationPromises.filter((entry) =>
        entry.promisorSeat === seat && entry.status === "open"
      )) {
        promise.status = "superseded";
        this.matchMetrics.negotiations.push({
          ...clone(promise),
          resolvedRound: this.round,
          resolvedCycle: this.cycle
        });
      }
      const promise = {
        id: `promise-${this.round}-${this.cycle}-${seat}`,
        round: this.round,
        cycle: this.cycle,
        kind: "power",
        promisorSeat: seat,
        targetSeat: decision.parameters.targetSeat,
        status: "open"
      };
      this.negotiationPromises.push(promise);
      this.matchMetrics.negotiations.push(clone(promise));
      player.metrics.promisesMade += 1;
    }
  }

  async chooseAll(policies, stage, decisionsForSeat) {
    return Promise.all(this.players.map((player) =>
      this.choose(policies, player.seat, stage, decisionsForSeat(player.seat))
    ));
  }

  dealTactic(player) {
    return player;
  }

  async setup(policies) {
    void policies;
  }

  async beginRound(policies) {
    const scores = this.players.map((player) => this.currentScore(player));
    const high = Math.max(...scores);
    const low = Math.min(...scores);
    const allEqual = high === low;
    if (this.round === 4 && this.matchMetrics.round4Start === null) {
      this.matchMetrics.round4Start = this.players.map((player) => ({
        seat: player.seat,
        score: this.currentScore(player),
        profileId: player.profileId
      }));
    }
    this.spotlightSeat = allEqual ? null : this.nearestInitiative(
      this.players.filter((player) => scores[player.seat] === high).map((player) => player.seat)
    );
    this.grantSeat = allEqual ? null : this.nearestInitiative(
      this.players.filter((player) => scores[player.seat] === low).map((player) => player.seat)
    );
    this.roundMandate = this.mandateDeck[this.round];
    this.regime = { persistent: this.regime.persistent || {}, round: {} };
    for (const player of this.players) {
      player.actionsUsed = [];
      player.selectedAction = null;
      player.escalation = this.config.rounds[this.round - 1].escalationTokens;
      player.tacticModifiers = {};
      player.roundMetrics = {
        capabilityStart: player.capability,
        customersStart: player.customers,
        scrutinyStart: player.metrics.scrutinyAdded,
        fundRunway: 0,
        computeProduced: 0,
        bestTrainingDomains: 0,
        deployed: false,
        jointVenturesCompleted: 0,
        riskyActions: 0
      };
    }
    if (this.grantSeat !== null) {
      const grantPlayer = this.players[this.grantSeat];
      const grant = await this.choose(policies, this.grantSeat, "public_research_grant", [
        {
          decisionId: "grant_runway",
          label: decisionLabel("grantRunway"),
          actionId: "grant",
          consequences: { runway: 1 }
        },
        {
          decisionId: "grant_compute",
          label: decisionLabel("grantCompute"),
          actionId: "grant",
          consequences: { compute: 1 }
        }
      ]);
      this.addResource(grantPlayer, grant.decisionId === "grant_runway" ? "runway" : "compute", 1);
    }
    await this.resolveRoundFactionPowers(policies);
    this.roundInitialized = true;
    this.recordEvent(
      "round_started",
      null,
      renderSimulationCopy(simulationCopy.events.roundStarted, {
        round: this.round,
        mandate: this.roundMandate.name,
        seat: this.spotlightSeat === null ? "none" : this.spotlightSeat + 1
      })
    );
  }

  async resolveRoundFactionPowers(policies) {
    for (const player of this.players) {
      if (this.round === 2 && player.factionId === "imperial_research_lab") {
        const choice = await this.choose(policies, player.seat, "call_mountain_view", [
          { decisionId: "mountain_runway", label: decisionLabel("mountainRunway"), actionId: "fund" },
          { decisionId: "mountain_compute", label: decisionLabel("mountainCompute"), actionId: "research" },
          { decisionId: "mountain_training", label: decisionLabel("mountainTraining"), actionId: "research" }
        ]);
        if (choice.decisionId === "mountain_runway") {
          this.addResource(player, "runway", 3);
          this.recordFactionAbility(player, "call_mountain_view", {
            runwayGained: 3
          });
        } else if (choice.decisionId === "mountain_compute") {
          this.addResource(player, "compute", 3);
          this.recordFactionAbility(player, "call_mountain_view", {
            computeGained: 3
          });
        } else {
          this.prepareTrainingDrawPile();
          const visible = this.trainingDrawPile.slice(0, 4);
          const arrangements = permutations(visible);
          const reorder = await this.choose(
            policies,
            player.seat,
            "call_mountain_view_reorder",
            arrangements.map((cards, index) => ({
              decisionId: `mountain_reorder_${index}`,
              label: decisionLabel("reorderTraining", {
                cards: cards.map((card) => card.type).join(" → ")
              }),
              actionId: "faction",
              parameters: { cardIds: cards.map((card) => card.id) }
            }))
          );
          const byId = new Map(visible.map((card) => [card.id, card]));
          this.trainingDrawPile.splice(
            0,
            visible.length,
            ...reorder.parameters.cardIds.map((id) => byId.get(id))
          );
          this.recordFactionAbility(player, "call_mountain_view", {
            trainingCardsReordered: visible.length
          });
        }
      }
      if (this.round === 3 && player.factionId === "foundry") {
        const demandCoupling =
          this.rulesVariant.foundryNewArchitectureDemandCoupling;
        const demandCoupled =
          demandCoupling !== null &&
          Number.isFinite(demandCoupling?.baseCompute);
        let licensesSold = 0;
        if (!demandCoupled) {
          this.addResource(
            player,
            "compute",
            this.rulesVariant.foundryNewArchitectureCompute
          );
          this.recordFactionAbility(player, "new_architecture", {
            computeGained: this.rulesVariant.foundryNewArchitectureCompute
          });
        }
        for (const rival of this.players.filter((candidate) =>
          candidate.seat !== player.seat && candidate.runway > 0
        )) {
          const license = await this.choose(policies, rival.seat, "architecture_license", [
            {
              decisionId: `architecture_license_${rival.seat}`,
              label: decisionLabel("architectureLicense"),
              actionId: "faction"
            },
            { decisionId: `architecture_decline_${rival.seat}`, label: decisionLabel("architectureDecline"), actionId: "faction" }
          ]);
          if (license.decisionId.startsWith("architecture_license_")) {
            licensesSold += 1;
            this.spendRunway(rival, 1, { cause: "architecture_license" });
            this.addResource(player, "runway", 1);
            this.addResource(rival, "compute", 1);
            this.recordFactionAbility(player, "new_architecture", {
              uses: 0,
              licensesSold: 1,
              runwayGained: 1,
              rivalComputeGranted: 1
            });
          }
        }
        if (demandCoupled) {
          const computeGained = Math.min(
            demandCoupling.maximumCompute,
            demandCoupling.baseCompute +
              licensesSold *
                demandCoupling.computePerLicense
          );
          this.addResource(player, "compute", computeGained);
          this.recordFactionAbility(player, "new_architecture", {
            computeGained
          });
        }
      }
    }
  }

  async preSelectionFactionPowers(policies) {
    const foundry = this.players.find((player) =>
      player.factionId === "foundry"
    );
    if (
      foundry &&
      this.round === 2 &&
      !foundry.factionAbilityUsed.allocationWindow
    ) {
      const allocationWindow = this.config.factionRules.foundry.allocationWindow;
      const { minimumPrice, paymentResource, temporaryCompute } = allocationWindow;
      const activate = await this.choose(policies, foundry.seat, "allocation_window_timing", [
        {
          decisionId: "allocation_wait",
          label: decisionLabel("allocationWait"),
          actionId: "faction"
        },
        {
          decisionId: "allocation_open",
          label: decisionLabel("allocationOpen"),
          actionId: "faction"
        }
      ]);
      if (activate.decisionId === "allocation_open") {
        foundry.factionAbilityUsed.allocationWindow = true;
        this.recordFactionAbility(foundry, "allocation_window");
        for (let unit = 0; unit < temporaryCompute; unit += 1) {
          const buyers = this.players.filter((candidate) =>
            candidate.seat !== foundry.seat && candidate[paymentResource] >= minimumPrice
          );
          const offer = await this.choose(policies, foundry.seat, `allocation_window_${unit}`, [
            {
              decisionId: `allocation_hold_${unit}`,
              label: decisionLabel("allocationExpire"),
              actionId: "faction"
            },
            ...buyers.flatMap((buyer) => {
              const maximumPrice = buyer[paymentResource];
              return Array.from(
                { length: maximumPrice - minimumPrice + 1 },
                (_, index) => {
                  const price = minimumPrice + index;
                  return {
                    decisionId: `allocation_offer_${unit}_${buyer.seat}_${price}`,
                    label: decisionLabel("allocationOffer", { seat: buyer.seat + 1, price }),
                    actionId: "faction",
                    parameters: { buyerSeat: buyer.seat, price }
                  };
                }
              );
            })
          ]);
          if (offer.parameters?.buyerSeat === undefined) continue;
          const buyer = this.players[offer.parameters.buyerSeat];
          const price = offer.parameters.price;
          const response = await this.choose(policies, buyer.seat, `allocation_response_${unit}`, [
            {
              decisionId: `allocation_reject_${unit}`,
              label: decisionLabel("allocationReject"),
              actionId: "faction"
            },
            ...(buyer[paymentResource] >= price ? [{
              decisionId: `allocation_accept_${unit}`,
              label: decisionLabel("allocationAccept", { price }),
              actionId: "faction"
            }] : []),
            ...Array.from(
              { length: Math.max(0, Math.min(price - 1, buyer[paymentResource]) - minimumPrice + 1) },
              (_, index) => {
                const counterPrice = minimumPrice + index;
                return {
                  decisionId: `allocation_counter_${unit}_${counterPrice}`,
                  label: decisionLabel("allocationCounter", { price: counterPrice }),
                  actionId: "faction",
                  parameters: { counterPrice }
                };
              }
            )
          ]);
          if (response.decisionId.startsWith("allocation_accept")) {
            this.completeAllocationWindowSale(foundry, buyer, price, allocationWindow);
          } else if (response.parameters?.counterPrice !== undefined) {
            const counterPrice = response.parameters.counterPrice;
            const counterparty = await this.choose(
              policies,
              foundry.seat,
              `allocation_counterparty_${unit}`,
              [
                {
                  decisionId: `allocation_counter_reject_${unit}`,
                  label: decisionLabel("allocationCounterReject"),
                  actionId: "faction"
                },
                {
                  decisionId: `allocation_counter_accept_${unit}`,
                  label: decisionLabel("allocationCounterAccept", { price: counterPrice }),
                  actionId: "faction"
                }
              ]
            );
            if (counterparty.decisionId.startsWith("allocation_counter_accept")) {
              this.completeAllocationWindowSale(foundry, buyer, counterPrice, allocationWindow);
            }
          }
        }
      }
    }

    const safety = this.players.find((player) =>
      player.factionId === "safety_laboratory"
    );
    if (
      safety &&
      this.round === 4 &&
      this.isEmergencyPauseEnabled(safety) &&
      !safety.factionAbilityUsed.emergencyPause &&
      safety.runway >= 1
    ) {
      const unlocked = this.config.rounds[this.round - 1].wildActions;
      const choice = await this.choose(policies, safety.seat, "emergency_pause_timing", [
        {
          decisionId: "emergency_pause_wait",
          label: decisionLabel("emergencyPauseWait"),
          actionId: "faction"
        },
        ...unlocked.map((wildId) => ({
          decisionId: `emergency_pause_${wildId}`,
          label: decisionLabel("pauseWildAction", { action: wildId }),
          actionId: "faction",
          parameters: { wildId }
        }))
      ]);
      if (choice.parameters?.wildId) {
        const trustBefore = safety.trust;
        this.spendRunway(safety, 1, { cause: "emergency_pause" });
        this.addResource(safety, "trust", 2);
        this.regime.cycle.disabledWild = choice.parameters.wildId;
        safety.factionAbilityUsed.emergencyPause = true;
        this.recordFactionAbility(safety, "emergency_pause", {
          runwaySpent: 1,
          trustGained: safety.trust - trustBefore,
          wildActionsBlocked: 1
        });
      }
    }

    if (
      foundry &&
      this.round === 4 &&
      !foundry.factionAbilityUsed.everybodyGpu
    ) {
      const choice = await this.choose(policies, foundry.seat, "everybody_gpu_timing", [
        {
          decisionId: "everybody_gpu_wait",
          label: decisionLabel("gpuProgramWait"),
          actionId: "faction"
        },
        {
          decisionId: "everybody_gpu_activate",
          label: decisionLabel("selectGpuProgram"),
          actionId: "faction"
        }
      ]);
      if (choice.decisionId === "everybody_gpu_activate") {
        for (const rival of this.players.filter(
          (candidate) => candidate.seat !== foundry.seat
        )) this.addResource(rival, "compute", 1);
        const mandate = this.rulesVariant.foundryGpuMandateEnabled
          ? Math.floor(
            (this.playerCount - 1) /
            this.rulesVariant.foundryGpuRivalsPerMandate
          )
          : 0;
        this.awardMandate(
          foundry,
          mandate,
          "everybody_gets_a_gpu"
        );
        this.removeScrutiny(foundry, 2);
        foundry.factionAbilityUsed.everybodyGpu = true;
        this.recordFactionAbility(foundry, "everybody_gets_a_gpu", {
          rivalComputeGranted: this.playerCount - 1,
          mandateGained: mandate,
          scrutinyRemoved: 2
        });
      }
    }
  }

  async secretAuction(policies, id, label) {
    const bids = await this.chooseAll(policies, `${id}_bid`, (seat) => {
      const maximum = this.players[seat].runway;
      return Array.from({ length: maximum + 1 }, (_, bid) => ({
        decisionId: `${id}_bid_${bid}`,
        label: decisionLabel("auctionBid", { label, bid }),
        actionId: "headline",
        parameters: { bid },
        consequences: { runway: -bid }
      }));
    });
    const high = Math.max(...bids.map((decision) => decision.parameters.bid));
    if (high <= 0) return null;
    const tied = bids
      .map((decision, seat) => ({ seat, bid: decision.parameters.bid }))
      .filter((entry) => entry.bid === high)
      .map((entry) => entry.seat);
    const winner = this.nearestInitiative(tied);
    this.spendRunway(this.players[winner], high, { cause: "secret_auction" });
    return winner;
  }

  async governmentVote(policies, id, outcomes) {
    const controller = this.controller("government");
    const votes = await this.chooseAll(policies, `${id}_vote`, (seat) =>
      outcomes.flatMap((outcome) => {
        const base = [{
          decisionId: `${id}_${outcome.id}`,
          label: decisionLabel("vote", { outcome: outcome.label }),
          actionId: "headline",
          parameters: { outcomeId: outcome.id, extraVote: false }
        }];
        if (this.players[seat].tactics.includes("open_letter")) {
          base.push({
            decisionId: `${id}_${outcome.id}_open_letter`,
            label: decisionLabel("openLetterVote", { outcome: outcome.label }),
            actionId: "headline",
            parameters: { outcomeId: outcome.id, extraVote: true }
          });
        }
        return base;
      })
    );
    const totals = Object.fromEntries(outcomes.map((outcome) => [outcome.id, 0]));
    for (const [seat, vote] of votes.entries()) {
      totals[vote.parameters.outcomeId] += controller === seat ? 2 : 1;
      if (vote.parameters.extraVote) {
        totals[vote.parameters.outcomeId] += 1;
        this.consumeTactic(this.players[seat], "open_letter");
      }
    }
    const maximum = Math.max(...Object.values(totals));
    const tied = outcomes.filter((outcome) => totals[outcome.id] === maximum);
    if (tied.length === 1) return tied[0].id;
    const decider = controller ?? this.initiativeSeat;
    const choice = await this.choose(policies, decider, `${id}_tiebreak`, tied.map((outcome) => ({
      decisionId: `${id}_break_${outcome.id}`,
      label: decisionLabel("breakTie", { outcome: outcome.label }),
      actionId: "headline",
      parameters: { outcomeId: outcome.id }
    })));
    return choice.parameters.outcomeId;
  }

  async prepareHeadline(policies) {
    this.activeHeadline = this.headlineDecks[this.round][this.cycle - 1];
    const coalition = this.players.find((player) =>
      player.factionId === "coalition_lab" &&
      this.round >= 4 &&
      !player.factionAbilityUsed.wildcardGovernance
    );
    if (coalition) {
      const unused = shuffled(
        this.headlineDocument.headlines.filter((card) =>
          card.round === this.round &&
          card.id !== this.activeHeadline.id &&
          !this.matchMetrics.headlines[card.id]
        ),
        `${this.seed}:replacement:${this.cycle}`
      ).slice(0, 2);
      if (unused.length === 2) {
        const replacement = await this.choose(policies, coalition.seat, "wildcard_governance", [
          {
            decisionId: "wildcard_keep",
            label: decisionLabel("keepHeadline", { headline: this.activeHeadline.name }),
            actionId: "faction"
          },
          ...unused.map((card) => ({
            decisionId: `wildcard_replace_${card.id}`,
            label: decisionLabel("replaceHeadline", { headline: card.name }),
            actionId: "faction",
            parameters: { headlineId: card.id }
          }))
        ]);
        if (replacement.parameters?.headlineId) {
          this.activeHeadline = unused.find((card) => card.id === replacement.parameters.headlineId);
          coalition.factionAbilityUsed.wildcardGovernance = true;
          const scrutiny = this.rulesVariant.coalitionWildcardGovernanceScrutiny;
          this.addScrutiny(coalition, scrutiny);
          this.recordFactionAbility(coalition, "wildcard_governance", {
            headlinesReplaced: 1,
            scrutinyAdded: scrutiny
          });
        }
      }
    }
    this.regime.cycle = { id: this.activeHeadline.id };
    const id = this.activeHeadline.id;
    increment(this.matchMetrics.headlines, id);
    this.matchMetrics.futureTimeline.push({
      round: this.round,
      cycle: this.cycle,
      id,
      name: this.activeHeadline.name
    });

    if (id === "open_weights_drop") {
      for (const player of this.players) this.addResource(player, "capability", 1);
      const minimum = Math.min(...this.players.map((player) => player.customers));
      const target = this.nearestInitiative(
        this.players.filter((player) => player.customers === minimum).map((player) => player.seat)
      );
      this.addResource(this.players[target], "trust", 1);
    } else if (id === "talent_gold_rush") {
      const winner = await this.secretAuction(policies, id, decisionLabel("hireExpert"));
      if (winner !== null) {
        const ceo = this.players[winner].pieces.find((piece) => piece.kind === "ceo");
        this.players[winner].experts.push({ id: `expert-${winner}`, tileId: ceo.tileId });
      }
    } else if (id === "data_center_buys_county") {
      const winner = await this.secretAuction(policies, id, decisionLabel("acquireCounty"));
      if (winner !== null) {
        const player = this.players[winner];
        const destinations = this.board.filter((tile) => ["cloud", "energy"].includes(tile.category));
        const move = await this.choose(policies, winner, `${id}_destination`, destinations.map((tile) => ({
          decisionId: `${id}_${tile.instanceId}`,
          label: decisionLabel("moveCeo", { destination: tile.name }),
          actionId: "headline",
          parameters: { tileId: tile.instanceId }
        })));
        player.pieces.find((piece) => piece.kind === "ceo").tileId = move.parameters.tileId;
        player.buildDiscounts = Math.min(2, player.buildDiscounts + 2);
        this.addScrutiny(player, 1);
      }
    } else if (id === "boardroom_coup") {
      if (this.spotlightSeat === null) return;
      const spotlight = this.players[this.spotlightSeat];
      const decisions = [
        ...(spotlight.runway >= 2 ? [{
          decisionId: "boardroom_pay",
          label: decisionLabel("retainAuthority"),
          actionId: "headline"
        }] : []),
        ...this.players.filter((player) => player.seat !== spotlight.seat).map((player) => ({
          decisionId: `boardroom_request_${player.seat}`,
          label: decisionLabel("requestBacking", { seat: player.seat + 1 }),
          actionId: "headline",
          parameters: { targetSeat: player.seat }
        })),
        {
          decisionId: "boardroom_accept_lock",
          label: decisionLabel("acceptCeoLock"),
          actionId: "headline"
        }
      ];
      const choice = await this.choose(policies, spotlight.seat, id, decisions);
      if (choice.decisionId === "boardroom_pay") {
        this.spendRunway(spotlight, 2, { cause: "boardroom_pay" });
      }
      else if (choice.parameters?.targetSeat !== undefined) {
        const target = choice.parameters.targetSeat;
        const response = await this.choose(policies, target, `${id}_response`, [
          {
            decisionId: "boardroom_back",
            label: decisionLabel("backSpotlight"),
            actionId: "headline"
          },
          {
            decisionId: "boardroom_refuse",
            label: decisionLabel("refuseBacking"),
            actionId: "headline"
          }
        ]);
        if (response.decisionId === "boardroom_back") this.addResource(this.players[target], "trust", 1);
        else this.regime.cycle.ceoLockedSeat = spotlight.seat;
      } else this.regime.cycle.ceoLockedSeat = spotlight.seat;
    } else if (id === "export_controls") {
      for (const category of ["chip", "government"]) {
        const seat = this.controller(category);
        if (seat !== null) this.addResource(this.players[seat], "runway", 1);
      }
      this.regime.cycle.computeTradeBlocked = true;
    } else if (id === "ai_written_law") {
      const controller = this.controller("government") ?? this.initiativeSeat;
      const choice = await this.choose(policies, controller, id, this.config.actions.map((action) => ({
        decisionId: `${id}_${action.id}`,
        label: decisionLabel("writeLaw", { action: action.name }),
        actionId: "headline",
        parameters: { actionId: action.id }
      })));
      this.regime.cycle.incentivizedAction = choice.parameters.actionId;
      this.regime.cycle.lawController = this.controller("government");
    } else if (id === "open_weight_non_aligned") {
      const choices = await this.chooseAll(policies, id, () => [
        {
          decisionId: `${id}_join`,
          label: decisionLabel("joinBloc"),
          actionId: "headline",
          parameters: { join: true }
        },
        {
          decisionId: `${id}_refuse`,
          label: decisionLabel("refuseBloc"),
          actionId: "headline",
          parameters: { join: false }
        }
      ]);
      const vertical = this.players.find((player) =>
        player.factionId === "vertical_empire" &&
        !player.factionAbilityUsed.ownTheFeed
      );
      if (vertical) {
        const override = await this.choose(policies, vertical.seat, "own_the_feed", [
          {
            decisionId: "own_feed_public",
            label: decisionLabel("acceptPublicResult"),
            actionId: "faction"
          },
          {
            decisionId: "own_feed_join",
            label: decisionLabel("ownFeedJoin"),
            actionId: "faction",
            parameters: { join: true }
          },
          {
            decisionId: "own_feed_refuse",
            label: decisionLabel("ownFeedRefuse"),
            actionId: "faction",
            parameters: { join: false }
          }
        ]);
        if (override.parameters?.join !== undefined) {
          choices[vertical.seat] = override;
          vertical.factionAbilityUsed.ownTheFeed = true;
          this.recordFactionAbility(vertical, "own_the_feed", {
            outcomesOverridden: 1
          });
        }
      }
      const joiners = choices.map((choice, seat) => choice.parameters.join ? seat : null)
        .filter((seat) => seat !== null);
      for (const [seat, choice] of choices.entries()) {
        if (choice.parameters.join) {
          this.addResource(this.players[seat], "capability", 1);
          this.addScrutiny(this.players[seat], 1);
        } else {
          this.addResource(this.players[seat], "runway", 1);
          this.addResource(this.players[seat], "trust", 1);
        }
      }
      for (const seat of joiners) {
        if (joiners.length > this.playerCount / 2) this.removeScrutiny(this.players[seat], 1);
        else this.addScrutiny(this.players[seat], 1);
      }
    } else if (id === "synthetic_candidate") {
      this.regime.cycle.syntheticCandidate = await this.governmentVote(policies, id, [
        { id: "certify", label: decisionLabel("certifyCandidate") },
        { id: "void", label: decisionLabel("voidElection") }
      ]);
      increment(this.matchMetrics.headlineOutcomes, `${id}:${this.regime.cycle.syntheticCandidate}`);
    } else if (id === "weights_on_internet") {
      const minimum = Math.min(...this.players.map((player) => player.capability));
      const target = this.nearestInitiative(
        this.players.filter((player) => player.capability === minimum).map((player) => player.seat)
      );
      const maximum = Math.max(...this.players.map((player) => player.capability));
      const owner = this.nearestInitiative(
        this.players.filter((player) => player.capability === maximum).map((player) => player.seat)
      );
      const powered = this.players[target].facilities.filter(
        (candidate) => candidate.powered
      );
      if (powered.length) {
        const choice = await this.choose(
          policies,
          target,
          "weights_on_internet_facility",
          powered.map((facility) => ({
            decisionId: `weights_on_internet_${facility.id}`,
            label: decisionLabel("chooseFacilityProduction", {
              facility: facility.id
            }),
            actionId: "headline",
            parameters: { facilityId: facility.id }
          }))
        );
        const facility = powered.find(
          (candidate) => candidate.id === choice.parameters.facilityId
        );
        await this.produceFacility(
          policies,
          this.players[target],
          facility,
          "weights_on_internet"
        );
      }
      this.addResource(this.players[owner], "trust", 1);
    } else if (id === "election_deepfake_panic") {
      this.regime.cycle.deepfake = await this.governmentVote(policies, id, [
        { id: "regulate", label: decisionLabel("regulateMedia") },
        { id: "do_nothing", label: decisionLabel("doNothing") }
      ]);
      if (this.regime.cycle.deepfake === "do_nothing") {
        this.regime.round.deepfakeIncome = true;
      }
      increment(this.matchMetrics.headlineOutcomes, `${id}:${this.regime.cycle.deepfake}`);
    } else if (id === "agi_personhood") {
      this.regime.persistent.agiPersonhood = await this.governmentVote(policies, id, [
        { id: "person", label: decisionLabel("agiPerson") },
        { id: "property", label: decisionLabel("agiProperty") }
      ]);
      increment(this.matchMetrics.headlineOutcomes, `${id}:${this.regime.persistent.agiPersonhood}`);
    } else if (id === "room_temperature_superconductor") {
      const rng = createRng(`${this.seed}:volatility:${this.round}:${this.cycle}`);
      this.regime.cycle.superconductor = rng() < 0.5 ? "fraud" : "replicates";
      this.regime.round.superconductor = this.regime.cycle.superconductor;
      increment(this.matchMetrics.headlineOutcomes, `${id}:${this.regime.cycle.superconductor}`);
    }

    this.recordEvent("headline_revealed", null, `${this.activeHeadline.name}: ${this.activeHeadline.text}`);
  }

  consumeTactic(player, id) {
    const index = player.tactics.indexOf(id);
    if (index >= 0) player.tactics.splice(index, 1);
    increment(player.metrics.tactics, id);
    increment(this.matchMetrics.tactics, id);
  }

  async tacticStage(policies) {
    for (const seat of this.initiativeOrder()) {
      const player = this.players[seat];
      const playable = [...new Set(player.tactics.filter((id) => id !== "open_letter"))];
      const decisions = [
        { decisionId: "tactic_pass", label: decisionLabel("skipTactic"), actionId: "tactic" },
        ...playable.map((id) => {
          const card = this.tacticDocument.tactics.find((candidate) => candidate.id === id);
          return {
            decisionId: `tactic_${id}`,
            label: decisionLabel("playTactic", { card: card.name, text: card.text }),
            actionId: "tactic",
            parameters: { tacticId: id }
          };
        })
      ];
      const choice = await this.choose(policies, seat, "tactic", decisions);
      const id = choice.parameters?.tacticId;
      if (!id) continue;
      this.consumeTactic(player, id);
      if (id === "cloud_partnership") {
        if (player.runway >= 1) {
          this.spendRunway(player, 1, {
            cause: "tactic_cloud_partnership",
            conversionEligible: true
          });
          this.addResource(player, "compute", 2);
          this.addResource(this.players[(seat + 1) % this.playerCount], "runway", 1);
        }
      } else if (id === "talent_raid" && player.runway >= 1) {
        this.spendRunway(player, 1, {
          cause: "tactic_talent_raid",
          conversionEligible: true
        });
        const ceo = player.pieces.find((piece) => piece.kind === "ceo");
        player.experts.push({ id: `expert-${seat}-${player.experts.length}`, tileId: ceo.tileId });
      } else if (id === "board_reshuffle") {
        const ready = player.actionsUsed.find((action) => ["organize", "influence"].includes(action));
        if (ready) player.actionsUsed = player.actionsUsed.filter((action) => action !== ready);
      } else if (id === "custom_silicon" && player.facilities.length) {
        player.facilities[0].customSilicon = true;
      } else if (id === "government_contract" && player.trust >= 4) {
        this.addResource(player, "runway", 2);
      } else if (id === "interconnection_waiver") {
        player.buildDiscounts = Math.min(2, player.buildDiscounts + 1);
        this.addResource(player, "trust", 1);
      } else if (id === "weights_leak") {
        const rivals = this.players.filter((candidate) =>
          candidate.seat !== player.seat &&
          candidate.facilities.some((facility) => facility.powered)
        );
        const source = rivals[0]?.facilities.find((facility) => facility.powered);
        if (source) await this.produceFacility(policies, player, source, "weights_leak");
      } else {
        player.tacticModifiers[id] = true;
      }
    }
  }

  async headlineChoiceStage(policies) {
    if (this.regime.cycle?.id === "emergency_power_authority") {
      for (const seat of this.initiativeOrder()) {
        const choice = await this.choose(policies, seat, "emergency_power", [0, 1, 2].map((power) => ({
          decisionId: `emergency_power_${power}`,
          label: decisionLabel("authorizeEmergencyPower", { power }),
          actionId: "headline",
          parameters: { power }
        })));
        this.players[seat].roundMetrics.emergencyPower =
          Math.max(this.players[seat].roundMetrics.emergencyPower || 0, choice.parameters.power);
      }
    }
    if (this.regime.cycle?.syntheticCandidate) {
      for (const seat of this.initiativeOrder()) {
        const player = this.players[seat];
        if (player.influence.length < 2) continue;
        const certify = this.regime.cycle.syntheticCandidate === "certify";
        const legal = certify && !this.canDeploy(player)
          ? []
          : [{
            decisionId: "synthetic_candidate_participate",
            label: certify
              ? "Return 2 Influence to gain the next eligible Customer"
              : "Return 2 Influence to gain 2 Trust",
            actionId: "headline",
            parameters: { participate: true }
          }];
        const choice = await this.choose(policies, seat, "synthetic_candidate_effect", [
          ...legal,
          {
            decisionId: "synthetic_candidate_pass",
            label: decisionLabel("keepInfluence"),
            actionId: "headline",
            parameters: { participate: false }
          }
        ]);
        if (!choice.parameters.participate) continue;
        player.influence.splice(0, 2);
        if (certify) {
          player.customers += 1;
          this.addScrutiny(player, 2);
          this.synchronizePublicMandate(player, "synthetic_candidate");
          this.recordEligibility(player, "synthetic_candidate");
        } else {
          this.addResource(player, "trust", 2);
        }
      }
    }
  }

  canDeploy(player) {
    return player.customers < this.config.resources.customers.cap &&
      player.capability >= this.customerRequirement(player.customers);
  }

  customerRequirement(customerCount) {
    const base = CUSTOMER_REQUIREMENTS[customerCount] ?? Infinity;
    return Number.isFinite(base)
      ? Math.max(1, base + this.rulesVariant.customerCapabilityOffset)
      : base;
  }

  legalDestinations(player, piece) {
    const current = this.board.find((tile) => tile.instanceId === piece.tileId);
    const range = player.factionId === "vertical_empire" &&
      this.round >= 2 && piece.kind === "ceo" ? 3 : 2;
    return this.board.filter((tile) => axialDistance(current, tile) <= range);
  }

  legalActionSelections(seat) {
    const player = this.players[seat];
    const core = super.legalActionSelections(seat);
    const unlocked = new Set(this.config.rounds[this.round - 1].wildActions);
    const wild = this.wildDocument.wildActions
      .filter((action) => unlocked.has(action.id))
      .filter((action) => !player.wildUsed.includes(action.id))
      .filter((action) => action.id !== this.regime.cycle?.disabledWild)
      .filter((action) =>
        player.escalation > 0 ||
        (action.id === "agent_swarm" && this.regime.cycle?.id === "agent_swarm_escapes_scope")
      )
      .filter((action) => this.legalWildResolutions(seat, action.id).length > 0)
      .map((action) => ({
        decisionId: `select_wild_${action.id}`,
        label: renderSimulationCopy(
          simulationCopy.decisions.selectAction,
          { action: action.name }
        ),
        actionId: action.id,
        consequences: { wildAction: true, escalation: action.id === "agent_swarm" &&
          this.regime.cycle?.id === "agent_swarm_escapes_scope" ? 0 : -1 }
      }));
    if (wild.some((decision) => decision.actionId === "declare_agi")) {
      this.markAgiFunnel(
        player,
        "legalDeclarationWindow",
        "action_selection"
      );
    }
    return [...core, ...wild];
  }

  legalFactionActions(seat) {
    void seat;
    return [];
  }

  async resolveFactionAction(policies, seat, id) {
    const player = this.players[seat];
    if (id === "moonshot") {
      const before = player.capability;
      const research = await this.choose(
        policies,
        seat,
        "moonshot_research",
        this.legalResolutions(seat, "research")
      );
      this.applyResolution(seat, research);
      this.addResource(player, "capability", Math.min(3, player.capability - before));
      this.addScrutiny(player, 2);
      player.factionAbilityUsed.moonshot = true;
    } else if (id === "orbital_compute") {
      const occupied = new Set(player.facilities.map((facility) => facility.tileId));
      const decisions = player.facilities.flatMap((facility) =>
        this.board.filter((tile) => !occupied.has(tile.instanceId)).map((tile) => ({
          decisionId: `orbital_${facility.id}_${tile.instanceId}`,
          label: decisionLabel("moveFacility", {
            facility: facility.id,
            destination: tile.name
          }),
          actionId: "faction",
          parameters: { facilityId: facility.id, tileId: tile.instanceId }
        }))
      );
      const choice = await this.choose(policies, seat, "orbital_compute", decisions);
      const facility = player.facilities.find((item) => item.id === choice.parameters.facilityId);
      facility.tileId = choice.parameters.tileId;
      facility.category = this.board.find((tile) => tile.instanceId === choice.parameters.tileId).category;
      facility.gridReady = false;
      facility.gridReadySupportSeats = [];
      const resource = RESOURCE_BY_CATEGORY[facility.category];
      if (resource) this.addResource(player, resource, resource === "compute" ? 2 : 1);
      if (facility.category === "frontier") {
        this.awardMandate(player, 1, "orbital_frontier");
        this.addScrutiny(player, 1);
      }
      this.addScrutiny(player, 2);
      player.factionAbilityUsed.orbitalCompute = true;
    } else if (id === "emergency_pause" && this.isEmergencyPauseEnabled(player)) {
      const unlocked = this.config.rounds[this.round - 1].wildActions;
      const choice = await this.choose(policies, seat, "emergency_pause", unlocked.map((wildId) => ({
        decisionId: `pause_${wildId}`,
        label: decisionLabel("pauseWildAction", { action: wildId }),
        actionId: "faction",
        parameters: { wildId }
      })));
      const trustBefore = player.trust;
      this.spendRunway(player, 1, { cause: "emergency_pause" });
      this.addResource(player, "trust", 2);
      this.regime.cycle.disabledWild = choice.parameters.wildId;
      player.factionAbilityUsed.emergencyPause = true;
      this.recordFactionAbility(player, "emergency_pause", {
        runwaySpent: 1,
        trustGained: player.trust - trustBefore,
        wildActionsBlocked: 1
      });
    } else if (id === "everybody_gpu") {
      for (const rival of this.players.filter((candidate) => candidate.seat !== seat)) {
        this.addResource(rival, "compute", 1);
      }
      this.awardMandate(
        player,
        this.rulesVariant.foundryGpuMandateEnabled
          ? Math.floor(
            (this.playerCount - 1) /
            this.rulesVariant.foundryGpuRivalsPerMandate
          )
          : 0,
        "everybody_gets_a_gpu"
      );
      this.removeScrutiny(player, 2);
      player.factionAbilityUsed.everybodyGpu = true;
    }
    increment(player.metrics.actions, `faction_${id}`);
    this.recordEvent(
      "faction_action_resolved",
      seat,
      renderSimulationCopy(simulationCopy.events.resolved, {
        faction: player.factionName,
        result: id
      })
    );
  }

  legalResolutions(seat, actionId) {
    const player = this.players[seat];
    const originalRunway = player.runway;
    if (actionId === "build" && player.buildDiscounts > 0) {
      player.runway += 1;
    }
    let decisions;
    try {
      decisions = super.legalResolutions(seat, actionId);
    } finally {
      player.runway = originalRunway;
    }
    if (actionId === "organize") {
      decisions = this.movementVariants(player, (piece, destination) => {
        const base = {
          pieceId: piece.id,
          destinationId: destination.instanceId,
          destinationCategory: destination.category
        };
        const result = [];
        if (player.teamsInSupply > 0) {
          const humanoid = this.regime.cycle?.id === "humanoid_factory_gate";
          const cost = humanoid ? 1 : Math.max(0, 2 - Number(destination.category === "talent"));
          const maximum = humanoid ? Math.min(2, player.teamsInSupply) : 1;
          if (player.runway >= cost) {
            for (let count = 1; count <= maximum; count += 1) {
              result.push({
                decisionId: `organize_recruit_${count}_${piece.id}_${destination.instanceId}`,
                label: decisionLabel("recruitTeams", {
                  count,
                  plural: count === 1 ? "" : "s",
                  cost
                }),
                actionId,
                parameters: { ...base, mode: "recruit", count, cost },
                consequences: { runway: -cost, teams: count }
              });
            }
          }
        }
        for (const extraPiece of player.pieces) {
          const current = this.board.find((tile) => tile.instanceId === extraPiece.tileId);
          for (const extraDestination of this.board.filter(
            (tile) => axialDistance(current, tile) <= 5
          )) {
            result.push({
              decisionId:
                `organize_redistribute_${piece.id}_${destination.instanceId}_` +
                `${extraPiece.id}_${extraDestination.instanceId}`,
              label: `${decisionLabel("reposition", {
                piece: piece.id,
                destination: destination.name
              })}; redistribute ${extraPiece.id} to ${extraDestination.name}`,
              actionId,
              parameters: {
                ...base,
                mode: "redistribute",
                extraPieceId: extraPiece.id,
                extraDestinationId: extraDestination.instanceId
              },
              consequences: { mobilityOnly: true }
            });
          }
        }
        for (const facility of player.facilities.filter(
          (candidate) => candidate.tileId === destination.instanceId
        )) {
          for (const target of this.board.filter((tile) =>
            axialDistance(destination, tile) === 1 &&
            tile.category !== "frontier" &&
            this.tileOccupancy(tile.instanceId) <
              (tile.facilitySpaces ?? this.config.board.facilitySpacesPerHex)
          )) {
            result.push({
              decisionId: `organize_relocate_${facility.id}_${target.instanceId}_${piece.id}`,
              label: decisionLabel("moveFacilityBetween", {
                facility: facility.id,
                from: destination.name,
                to: target.name
              }),
              actionId,
              parameters: {
                ...base,
                mode: "relocate",
                facilityId: facility.id,
                facilityDestinationId: target.instanceId
              },
              consequences: { relocateFacility: true }
            });
          }
        }
        return result;
      });
    }
    if (actionId === "build" && this.round === 1) {
      decisions = decisions.filter((decision) =>
        decision.parameters?.buildMode === "facility"
      );
    }
    if (
      actionId === "deploy" &&
      player.customers < this.config.resources.customers.cap
    ) {
      const baseRequirement = this.customerRequirement(player.customers);
      decisions = this.movementVariants(player, (piece, destination) => {
        const celebrityDiscount = Number(
          this.regime.cycle?.id === "synthetic_celebrity" &&
          !player.tacticModifiers.syntheticCelebrityUsed &&
          ["consumer", "media"].includes(destination.category)
        );
        let computeCost = destination.category === "consumer"
          ? 0
          : this.rulesVariant.deployComputeCost;
        if (
          this.regime.cycle?.id === "ten_dollar_intelligence" ||
          player.tacticModifiers.api_price_cut ||
          player.tacticModifiers.economicBenchmark ||
          (
            player.factionId === "platform_empire" &&
            ["consumer", "media"].includes(destination.category) &&
            !player.roundMetrics.installedBaseUsed
          )
        ) computeCost = 0;
        if (player.compute < computeCost) return [];
        const accessChoices = player.marketAccess > 0 ? [false, true] : [false];
        return accessChoices.flatMap((useMarketAccess) => {
          const requirement = Math.max(
            1,
            baseRequirement - celebrityDiscount - Number(useMarketAccess)
          );
          if (player.capability < requirement) return [];
          const accessSuffix = useMarketAccess ? "_market_access" : "";
          const accessLabel = useMarketAccess
            ? `; ${decisionLabel("useMarketAccess")}`
            : "";
          return [{
            decisionId:
              `deploy_${destination.category}_${piece.id}_` +
              `${destination.instanceId}${accessSuffix}`,
            label: renderSimulationCopy(simulationCopy.decisions.moveAndDeploy, {
              piece: piece.id,
              destination: destination.name,
              customer: player.customers + 1
            }) + accessLabel,
            actionId,
            parameters: {
              pieceId: piece.id,
              destinationId: destination.instanceId,
              destinationCategory: destination.category,
              computeCost,
              useMarketAccess
            },
            consequences: {
              compute: -computeCost,
              customers: 1,
              scrutiny: 1,
              marketAccess: useMarketAccess ? -1 : 0
            }
          }];
        });
      });
    }
    if (actionId === "research" && decisions.length === 0 && this.regime.cycle?.id === "ten_dollar_intelligence") {
      decisions = this.movementVariants(player, (piece, destination) =>
        [2, 3, 4, 5, 6, 7].map((stopAt) => ({
          decisionId: `research_stop_${stopAt}_${piece.id}_${destination.instanceId}`,
          label: renderSimulationCopy(simulationCopy.decisions.moveAndResearch, {
            piece: piece.id,
            destination: destination.name,
            stopAt
          }),
          actionId,
          parameters: {
            pieceId: piece.id,
            destinationId: destination.instanceId,
            destinationCategory: destination.category,
            stopAt
          },
          consequences: { compute: 0, stopAt }
        }))
      );
    }
    if (actionId === "organize") {
      if (
        player.factionId === "platform_empire" &&
        this.round === 2 &&
        !player.roundMetrics.yearEfficiencyUsed &&
        player.pieces.some((piece) => piece.kind === "team")
      ) {
        const normalModes = decisions.filter((decision) =>
          ["recruit", "redistribute", "relocate"].includes(decision.parameters?.mode)
        );
        decisions.push(...normalModes.map((decision) => ({
          ...clone(decision),
          decisionId: `${decision.decisionId}_year_of_efficiency`,
          label: `${decisionLabel("returnTeamReorganize")}; ${decision.label}`,
          parameters: { ...decision.parameters, yearOfEfficiency: true },
          consequences: {
            ...decision.consequences,
            runway: (decision.consequences?.runway || 0) + 3,
            teams: (decision.consequences?.teams || 0) - 1
          }
        })));
      }
      if (
        this.regime.cycle?.id === "employee_free_unicorn" &&
        player.pieces.some((piece) => piece.kind === "team")
      ) {
        const teams = player.pieces.filter((piece) => piece.kind === "team");
        for (let count = 1; count <= teams.length; count += 1) {
          decisions.push({
            decisionId: `organize_employee_free_${count}`,
            label: decisionLabel("returnTeams", {
              count,
              plural: count === 1 ? "" : "s",
              runway: count * 2
            }),
            actionId,
            parameters: { mode: "employee_free", count },
            consequences: { runway: count * 2, scrutiny: 2 }
          });
        }
      }
    }
    if (actionId === "build" && this.round >= 2 && player.linkSupply > 0) {
      const cost = this.regime.cycle?.superconductor === "replicates" ? 0 : 1;
      if (player.runway + Number(player.buildDiscounts > 0) >= cost) {
        decisions.push(...this.movementVariants(player, (piece, destination) =>
          player.facilities
            .filter((facility) =>
              facility.tileId === destination.instanceId &&
              !player.links.includes(facility.id)
            )
            .map((facility) => ({
              decisionId: `build_link_${facility.id}_${piece.id}`,
              label: decisionLabel("installLink", {
                piece: piece.id,
                destination: destination.name
              }),
              actionId,
              parameters: {
                pieceId: piece.id,
                destinationId: destination.instanceId,
                destinationCategory: destination.category,
                buildMode: "link",
                facilityId: facility.id,
                cost
              },
              consequences: { runway: -cost, links: 1 }
            }))
        ));
      }
    }
    if (actionId === "influence" && this.round >= 3) {
      if (this.jointVentureSupplyAvailable()) decisions.push(...this.movementVariants(player, (piece, destination) => {
        const contractChoices = [];
        for (const rival of this.players.filter((candidate) => candidate.seat !== seat)) {
          const range = player.factionId === "coalition_lab" ? 2 : 1;
          for (const left of player.facilities) for (const right of rival.facilities) {
            const leftTile = this.board.find((tile) => tile.instanceId === left.tileId);
            const rightTile = this.board.find((tile) => tile.instanceId === right.tileId);
            const distance = axialDistance(leftTile, rightTile);
            if (distance < 1 || distance > range) continue;
            const base = {
              pieceId: piece.id,
              destinationId: destination.instanceId,
              destinationCategory: destination.category,
              targetSeat: rival.seat,
              leftFacilityId: left.id,
              rightFacilityId: right.id
            };
            contractChoices.push({
              decisionId:
                `influence_joint_venture_${rival.seat}_${left.id}_${right.id}_` +
                `${piece.id}_${destination.instanceId}`,
              label: decisionLabel("proposeJointVenture", { seat: rival.seat + 1 }),
              actionId,
              parameters: { ...base, mode: "joint_venture" },
              consequences: { negotiation: true }
            });
          }
        }
        return contractChoices;
      }));
      const terminable = this.contracts.filter((contract) =>
        contract.kind === "joint_venture" &&
        (contract.left.seat === seat || contract.right.seat === seat)
      );
      if (terminable.length) decisions.push(...this.movementVariants(player, (piece, destination) =>
        terminable.map((contract) => ({
          decisionId: `influence_terminate_joint_venture_${contract.id}_${piece.id}_` +
            destination.instanceId,
          label: decisionLabel("terminateJointVenture", { contract: contract.id }),
          actionId,
          parameters: {
            pieceId: piece.id,
            destinationId: destination.instanceId,
            destinationCategory: destination.category,
            mode: "terminate_joint_venture",
            contractId: contract.id
          },
          consequences: { terminateJointVenture: contract.id }
        }))
      ));
    }
    if (
      actionId === "deploy" &&
      player.factionId === "platform_empire" &&
      this.round >= 4 &&
      !player.roundMetrics.socialGraphUsed
    ) {
      const existing = new Set(decisions.map((decision) => decision.parameters?.destinationId));
      for (const tile of this.board.filter((candidate) =>
        ["consumer", "media"].includes(candidate.category) &&
        this.controller(candidate.category) === seat &&
        !existing.has(candidate.instanceId)
      )) {
        const cost = tile.category === "consumer" ? 0 : this.rulesVariant.deployComputeCost;
        if (player.compute < cost) continue;
        const baseRequirement = this.customerRequirement(player.customers);
        const accessChoices = player.marketAccess > 0 ? [false, true] : [false];
        for (const useMarketAccess of accessChoices) {
          if (
            player.capability <
            Math.max(1, baseRequirement - Number(useMarketAccess))
          ) continue;
          decisions.push({
            decisionId:
              `deploy_social_graph_${tile.instanceId}` +
              (useMarketAccess ? "_market_access" : ""),
            label: decisionLabel("socialGraphDeploy", {
              destination: tile.name
            }) + (useMarketAccess ? `; ${decisionLabel("useMarketAccess")}` : ""),
            actionId,
            parameters: {
              destinationId: tile.instanceId,
              destinationCategory: tile.category,
              computeCost: cost,
              socialGraph: true,
              useMarketAccess
            },
            consequences: {
              compute: -cost,
              customers: 1,
              scrutiny: 1,
              marketAccess: useMarketAccess ? -1 : 0
            }
          });
        }
      }
    }
    if (
      actionId === "research" &&
      player.factionId === "imperial_research_lab" &&
      this.round >= 4 &&
      !player.factionAbilityUsed.scalingLawBreakthrough
    ) {
      decisions.push(...decisions.map((decision) => ({
        ...clone(decision),
        decisionId: `${decision.decisionId}_scaling_law_breakthrough`,
        label: decisionLabel("scalingLawBreakthrough", { decision: decision.label }),
        parameters: {
          ...decision.parameters,
          scalingLawBreakthrough: true
        },
        consequences: {
          ...decision.consequences,
          capabilityBonusMaximum: 3,
          scrutiny: (decision.consequences?.scrutiny || 0) + 2
        }
      })));
    }
    if (this.regime.cycle?.ceoLockedSeat === seat) {
      decisions = decisions.filter((decision) => decision.parameters?.pieceId !== "ceo");
    }
    if (actionId === "build" && player.buildDiscounts > 0) {
      decisions = decisions.flatMap((decision) => [
        {
          ...clone(decision),
          parameters: {
            ...decision.parameters,
            useBuildDiscount: false
          }
        },
        {
          ...clone(decision),
          decisionId: `${decision.decisionId}_build_discount`,
          label: `${decision.label}; ${decisionLabel("useBuildDiscount")}`,
          parameters: {
            ...decision.parameters,
            useBuildDiscount: true
          },
          consequences: {
            ...decision.consequences,
            buildDiscounts: -1
          }
        }
      ]);
    }
    return decisions
      .map((decision) => this.adjustDecision(player, decision))
      .filter((decision) =>
        decision.parameters?.actualRunwayCost === undefined ||
        decision.parameters.actualRunwayCost <= player.runway
      );
  }

  adjustDecision(player, decision) {
    // This adjustment only annotates parameters.  Legal-decision generation calls
    // it repeatedly while testing prospective trade amounts, so a full deep clone
    // here dominated deterministic simulations without protecting any nested
    // value that we mutate.
    const result = {
      ...decision,
      parameters: { ...(decision.parameters || {}) }
    };
    const category = result.parameters?.destinationCategory;
    if (result.actionId === "fund") {
      const venture = result.parameters.mode === "venture";
      result.parameters.actualRunway = venture
        ? this.rulesVariant.fundVenture
        : this.rulesVariant.fundConservative;
      if (category === "capital") result.parameters.actualRunway += 1;
      if (player.seat === this.spotlightSeat && !player.roundMetrics.spotlightFundUsed) {
        result.parameters.actualRunway += 1;
      }
      const superconductor = this.regime.cycle?.superconductor;
      if (superconductor === "fraud") {
        result.parameters.actualRunway += 3;
        result.parameters.extraScrutiny = 2;
      }
    }
    if (result.actionId === "research") {
      result.parameters.actualComputeCost =
        this.regime.cycle?.id === "ten_dollar_intelligence" || category === "cloud"
          ? 0
          : 1;
    }
    if (result.actionId === "deploy") {
      let cost = category === "consumer" ? 0 : this.rulesVariant.deployComputeCost;
      if (this.regime.cycle?.id === "ten_dollar_intelligence") cost = 0;
      if (player.tacticModifiers.api_price_cut) cost = 0;
      if (player.tacticModifiers.economicBenchmark) cost = 0;
      if (
        player.factionId === "platform_empire" &&
        ["consumer", "media"].includes(category) &&
        !player.roundMetrics.installedBaseUsed
      ) cost = 0;
      result.parameters.computeCost = cost;
    }
    if (result.actionId === "build") {
      const mode = result.parameters?.buildMode;
      const source = mode === "generator"
        ? this.config.powerSources.find(
          (candidate) => candidate.id === result.parameters.sourceId
        )
        : null;
      let cost = mode === "generator"
        ? source?.runwayCost ?? 0
        : mode === "link"
          ? result.parameters.cost ?? 1
          : this.rulesVariant.facilityCost;
      if (category === "chip") cost -= 1;
      if (
        category === "energy" &&
        ["generator", "link"].includes(mode)
      ) cost -= 1;
      const destination = this.board.find(
        (tile) => tile.instanceId === result.parameters.destinationId
      );
      if (
        destination?.id === "renewable_basin" &&
        source?.id === "clean_infrastructure"
      ) cost -= 1;
      if (result.parameters.useBuildDiscount) cost -= 1;
      const costBeforeIndustrialVelocity = Math.max(0, cost);
      if (
        player.factionId === "vertical_empire" &&
        this.rulesVariant.verticalIndustrialVelocityBuildModes.includes(mode) &&
        !player.roundMetrics.industrialVelocityUsed
      ) cost -= this.rulesVariant.verticalIndustrialVelocityDiscount;
      result.parameters.actualRunwayCost = Math.max(0, cost);
      result.parameters.industrialVelocitySavings =
        costBeforeIndustrialVelocity - result.parameters.actualRunwayCost;
    }
    return result;
  }

  legalWildResolutions(seat, id) {
    const player = this.players[seat];
    const globalMoves = (builder) => this.movementVariants(
      player,
      (piece, destination) => builder(piece, destination)
    );
    if (id === "mega_cluster") {
      if (this.megaClusters.length >= this.config.sharedSupply.megaClusterPairs) return [];
      const pairs = [];
      if (player.runway >= 3 && player.compute >= 2) {
        for (const left of player.facilities) for (const right of player.facilities) {
          if (left.id < right.id && this.areAdjacent(left.tileId, right.tileId)) {
            for (const piece of player.pieces) {
              const destinations = this.legalDestinations(player, piece);
              for (const host of [left, right].filter((candidate) =>
                destinations.some((tile) => tile.instanceId === candidate.tileId)
              )) {
                pairs.push({
                  decisionId: `wild_mega_cluster_${left.id}_${right.id}_${piece.id}_${host.id}`,
                  label: decisionLabel("constructMegaCluster", {
                    left: left.id,
                    right: right.id
                  }),
                  actionId: id,
                  parameters: {
                    leftId: left.id,
                    rightId: right.id,
                    pieceId: piece.id,
                    destinationId: host.tileId
                  }
                });
              }
            }
          }
        }
      }
      if (player.runway >= 2 && player.compute >= 1) {
        for (const partner of this.players.filter((candidate) =>
          candidate.seat !== seat && candidate.runway >= 1 && candidate.compute >= 1
        )) {
          for (const left of player.facilities) for (const right of partner.facilities) {
            if (!this.areAdjacent(left.tileId, right.tileId)) continue;
            for (const piece of player.pieces.filter((candidate) =>
              this.legalDestinations(player, candidate)
                .some((tile) => tile.instanceId === left.tileId)
            )) {
              pairs.push({
                decisionId:
                  `wild_mega_cluster_joint_${left.id}_${partner.seat}_${right.id}_${piece.id}`,
                label: decisionLabel("jointMegaCluster", { seat: partner.seat + 1 }),
                actionId: id,
                parameters: {
                  leftId: left.id,
                  rightId: right.id,
                  partnerSeat: partner.seat,
                  pieceId: piece.id,
                  destinationId: left.tileId
                }
              });
            }
          }
        }
      }
      return pairs;
    }
    if (id === "reorganization") {
      return globalMoves((piece, destination) => [
        {
          decisionId: `wild_reorganization_move_${piece.id}_${destination.instanceId}`,
          label: decisionLabel("reorganizeMove"),
          actionId: id,
          parameters: {
            returnTeam: false,
            pieceId: piece.id,
            destinationId: destination.instanceId
          }
        },
        ...(player.pieces.some((candidate) => candidate.kind === "team") ? [{
          decisionId: `wild_reorganization_return_${piece.id}_${destination.instanceId}`,
          label: decisionLabel("reorganizeReturn"),
          actionId: id,
          parameters: {
            returnTeam: true,
            pieceId: piece.id,
            destinationId: destination.instanceId
          }
        }] : [])
      ]);
    }
    if (id === "open_weights") {
      return globalMoves((piece, destination) => [{
        decisionId: `wild_open_weights_${piece.id}_${destination.instanceId}`,
        label: decisionLabel("openWeights"),
        actionId: id,
        parameters: { pieceId: piece.id, destinationId: destination.instanceId }
      }]);
    }
    if (id === "narrative_capture") {
      return globalMoves((piece, destination) => [
        {
          decisionId: `wild_narrative_scrutiny_${piece.id}_${destination.instanceId}`,
          label: decisionLabel("narrativeScrutiny"),
          actionId: id,
          parameters: {
            mode: "scrutiny",
            pieceId: piece.id,
            destinationId: destination.instanceId
          }
        },
        {
          decisionId: `wild_narrative_runway_${piece.id}_${destination.instanceId}`,
          label: decisionLabel("narrativeRunway"),
          actionId: id,
          parameters: {
            mode: "runway",
            pieceId: piece.id,
            destinationId: destination.instanceId
          }
        },
        ...this.players.filter((rival) => rival.customers > player.customers).map((rival) => ({
          decisionId:
            `wild_narrative_target_${rival.seat}_${piece.id}_${destination.instanceId}`,
          label: decisionLabel("narrativeRival", { seat: rival.seat + 1 }),
          actionId: id,
          parameters: {
            mode: "target",
            targetSeat: rival.seat,
            pieceId: piece.id,
            destinationId: destination.instanceId
          }
        }))
      ]);
    }
    if (id === "agent_swarm") {
      return player.actionsUsed.length <= 4
        ? globalMoves((piece, destination) => [{
          decisionId: `wild_agent_swarm_${piece.id}_${destination.instanceId}`,
          label: simulationCopy.decisions.releaseAgentSwarm,
          actionId: id,
          parameters: { pieceId: piece.id, destinationId: destination.instanceId }
        }])
        : [];
    }
    if (id === "declare_agi") {
      return this.isAgiEligible(player)
        ? globalMoves((piece, destination) => [{
          decisionId: `wild_declare_agi_${piece.id}_${destination.instanceId}`,
          label: simulationCopy.decisions.declareAgi,
          actionId: id,
          parameters: { pieceId: piece.id, destinationId: destination.instanceId }
        }])
        : [];
    }
    if (id === "fusion_demonstrator") {
      const cost = this.regime.cycle?.superconductor === "replicates" ? 3 : 5;
      if (player.runway < cost) return [];
      const grid = this.board.find((tile) => tile.id === "grid_reactor");
      if (this.generatorOccupancy(grid.instanceId) >= 3) return [];
      return player.pieces
        .filter((piece) => this.legalDestinations(player, piece)
          .some((tile) => tile.instanceId === grid.instanceId))
        .map((piece) => ({
          decisionId: `wild_fusion_${piece.id}`,
          label: renderSimulationCopy(simulationCopy.decisions.constructAdvancedGeneration, {
            piece: piece.id
          }),
          actionId: id,
          parameters: { pieceId: piece.id, destinationId: grid.instanceId, cost }
        }));
    }
    return [];
  }

  areAdjacent(leftId, rightId) {
    const left = this.board.find((tile) => tile.instanceId === leftId);
    const right = this.board.find((tile) => tile.instanceId === rightId);
    return axialDistance(left, right) === 1;
  }

  hasAdjacentFacilities(left, right) {
    return left.facilities.some((a) =>
      right.facilities.some((b) => this.areAdjacent(a.tileId, b.tileId))
    );
  }

  canFormPartnership(left, right) {
    const range = left.factionId === "coalition_lab" && this.round >= 3 ? 2 : 1;
    return left.facilities.some((a) =>
      right.facilities.some((b) => {
        const leftTile = this.board.find((tile) => tile.instanceId === a.tileId);
        const rightTile = this.board.find((tile) => tile.instanceId === b.tileId);
        return axialDistance(leftTile, rightTile) <= range;
      })
    );
  }

  async negotiate(policies, seat, decision) {
    if (
      decision.parameters.mode === "joint_venture" &&
      !this.jointVentureSupplyAvailable()
    ) return false;
    const targetSeat = decision.parameters.targetSeat;
    const response = await this.choose(policies, targetSeat, "negotiation_response", [
      {
        decisionId: "agreement_accept",
        label: decisionLabel("agreementAccept"),
        actionId: "influence"
      },
      {
        decisionId: "agreement_reject",
        label: decisionLabel("agreementReject"),
        actionId: "influence"
      }
    ]);
    if (response.decisionId === "agreement_reject") return false;
    const player = this.players[seat];
    const target = this.players[targetSeat];
    const contract = {
      id: ++this.contractSerial,
      kind: decision.parameters.mode,
      createdRound: this.round,
      left: {
        seat,
        facilityId: decision.parameters.leftFacilityId
      },
      right: {
        seat: targetSeat,
        facilityId: decision.parameters.rightFacilityId
      },
      supplierSeat: decision.parameters.supplierSeat,
      buyerSeat: decision.parameters.buyerSeat
    };
    this.contracts.push(contract);
    if (decision.parameters.mode === "joint_venture") {
      player.jointVentures.push({ contractId: contract.id, partnerSeat: targetSeat, createdRound: this.round });
      target.jointVentures.push({ contractId: contract.id, partnerSeat: seat, createdRound: this.round });
      player.roundMetrics.jointVenturesCompleted += 1;
      target.roundMetrics.jointVenturesCompleted += 1;
      player.history.jointVenturePartners.push(targetSeat);
      target.history.jointVenturePartners.push(seat);
      if (player.factionId === "coalition_lab") this.addResource(player, "runway", 1);
      if (player.factionId === "coalition_lab") {
        const left = player.facilities.find(
          (facility) => facility.id === decision.parameters.leftFacilityId
        );
        const right = target.facilities.find(
          (facility) => facility.id === decision.parameters.rightFacilityId
        );
        const leftTile = this.board.find((tile) => tile.instanceId === left?.tileId);
        const rightTile = this.board.find((tile) => tile.instanceId === right?.tileId);
        const distance = leftTile && rightTile
          ? axialDistance(leftTile, rightTile)
          : 0;
        this.recordFactionAbility(player, "strategic_partnership", {
          jointVenturesCreated: 1,
          runwayGained: 1,
          remoteJointVentures: Number(distance > 1)
        });
      }
    }
    return true;
  }

  completeAllocationWindowSale(foundry, buyer, price, allocationWindow) {
    const { minimumPrice, paymentResource } = allocationWindow;
    if (
      !Number.isInteger(price) ||
      price < minimumPrice ||
      buyer[paymentResource] < price
    ) return false;
    if (paymentResource === "runway") {
      this.spendRunway(buyer, price, { cause: "allocation_window_purchase" });
    } else {
      buyer[paymentResource] -= price;
    }
    if (!buyer.temporaryCompute) buyer.temporaryComputeBaseline = buyer.compute;
    this.addResource(buyer, "compute", 1);
    buyer.temporaryCompute = (buyer.temporaryCompute || 0) + 1;
    this.addResource(foundry, paymentResource, price);
    this.recordFactionAbility(foundry, "allocation_window", {
      uses: 0,
      unitsSold: 1,
      paymentResource,
      paymentReceived: price,
      temporaryComputeGranted: 1
    });
    return true;
  }

  jointVentureSupplyAvailable() {
    return this.contracts.filter((contract) => contract.kind === "joint_venture").length <
      this.config.sharedSupply.jointVenturePairs;
  }

  terminateJointVenture(seat, contractId) {
    const index = this.contracts.findIndex((contract) =>
      contract.kind === "joint_venture" &&
      contract.id === contractId &&
      (contract.left.seat === seat || contract.right.seat === seat)
    );
    if (index < 0) return false;
    const [contract] = this.contracts.splice(index, 1);
    for (const participant of [contract.left.seat, contract.right.seat]) {
      this.players[participant].jointVentures = this.players[participant].jointVentures.filter(
        (venture) => venture.contractId !== contract.id
      );
    }
    return true;
  }

  applyResolution(seat, decision) {
    const player = this.players[seat];
    this.beginRunwayConversionContext(player, decision);
    if (decision.consequences?.noOp) {
      this.markAction(player, decision.actionId, decision.label);
      return;
    }
    const before = {
      runway: player.runway,
      compute: player.compute,
      capability: player.capability,
      customers: player.customers,
      scrutiny: player.scrutiny,
      safety: player.safety
    };
    let scientificMethodUsedThisResolution = false;
    if (decision.actionId === "organize" && decision.parameters?.yearOfEfficiency) {
      const team = player.pieces.find((piece) => piece.kind === "team");
      if (team) {
        player.pieces = player.pieces.filter((piece) => piece.id !== team.id);
        player.teamsInSupply += 1;
        this.addResource(player, "runway", 3);
        for (const piece of player.pieces) {
          const current = this.board.find((tile) => tile.instanceId === piece.tileId);
          const options = this.board
            .filter((tile) => axialDistance(current, tile) <= 1)
            .sort((left, right) =>
              Number(right.instanceId === decision.parameters.destinationId) -
                Number(left.instanceId === decision.parameters.destinationId) ||
              left.instanceId.localeCompare(right.instanceId)
            );
          if (options[0]) piece.tileId = options[0].instanceId;
        }
        player.roundMetrics.yearEfficiencyUsed = true;
      }
    }
    if (decision.actionId === "organize" && decision.parameters?.mode === "recruit") {
      this.spendRunway(player, decision.parameters.cost, {
        cause: "organize_recruit",
        conversionEligible: true
      });
      this.movePiece(player, decision.parameters);
      for (let index = 0; index < decision.parameters.count; index += 1) {
        const usedNumbers = new Set(
          player.pieces
            .filter((piece) => piece.kind === "team")
            .map((piece) => Number(piece.id.split("-").at(-1)))
        );
        const number = Array.from(
          { length: this.config.playerSupply.teams },
          (_, candidate) => candidate + 1
        ).find((candidate) => !usedNumbers.has(candidate));
        if (!number) throw new Error(`No Team piece remains in seat ${seat}'s supply.`);
        player.pieces.push({
          id: `s${seat}-team-${number}`,
          kind: "team",
          tileId: decision.parameters.destinationId
        });
        player.teamsInSupply -= 1;
      }
      if (this.regime.cycle?.id === "humanoid_factory_gate") {
        this.addScrutiny(player, decision.parameters.count);
      }
      this.markAction(player, "organize", decision.label);
      return;
    }
    if (decision.actionId === "organize" && decision.parameters?.mode === "redistribute") {
      this.movePiece(player, decision.parameters);
      const extra = player.pieces.find(
        (piece) => piece.id === decision.parameters.extraPieceId
      );
      if (extra) extra.tileId = decision.parameters.extraDestinationId;
      this.markAction(player, "organize", decision.label);
      return;
    }
    if (decision.actionId === "organize" && decision.parameters?.mode === "relocate") {
      this.movePiece(player, decision.parameters);
      const facility = player.facilities.find(
        (candidate) => candidate.id === decision.parameters.facilityId
      );
      if (facility) {
        facility.tileId = decision.parameters.facilityDestinationId;
        facility.category = this.board.find(
          (tile) => tile.instanceId === facility.tileId
        )?.category;
        facility.gridReady = false;
        facility.gridReadySupportSeats = [];
      }
      this.markAction(player, "organize", decision.label);
      return;
    }
    if (decision.actionId === "organize" && decision.parameters?.mode === "employee_free") {
      const teams = player.pieces.filter((piece) => piece.kind === "team")
        .slice(0, decision.parameters.count);
      player.pieces = player.pieces.filter((piece) => !teams.includes(piece));
      player.teamsInSupply += teams.length;
      this.addResource(player, "runway", teams.length * 2);
      this.addScrutiny(player, 2);
      this.markAction(player, "organize", decision.label);
      return;
    }
    if (decision.actionId === "build" && decision.parameters?.buildMode === "link") {
      this.spendRunway(player, decision.parameters.actualRunwayCost, {
        cause: "build_link",
        conversionEligible: true
      });
      if (decision.parameters.useBuildDiscount) player.buildDiscounts -= 1;
      player.links.push(decision.parameters.facilityId);
      player.linkSupply -= 1;
      this.movePiece(player, decision.parameters);
      this.markAction(player, "build", decision.label);
      return;
    }
    if (decision.actionId === "influence" &&
      ["joint_venture", "terminate_joint_venture"].includes(decision.parameters?.mode)) {
      this.movePiece(player, decision.parameters);
      const tile = this.board.find(
        (candidate) => candidate.instanceId === decision.parameters.destinationId
      );
      if (tile && POLITICAL_CATEGORIES.has(tile.category)) {
        const count = 2 + Number(
          !decision.parameters.suppressDestinationBonus &&
          ["media", "government"].includes(tile.category)
        );
        for (let index = 0; index < count; index += 1) {
          if (player.influence.length < this.config.playerSupply.influenceCubes) {
            player.influence.push({ tileId: tile.instanceId });
          } else if (player.influence.length) {
            player.influence[index % player.influence.length].tileId = tile.instanceId;
          }
        }
      }
      if (decision.parameters.mode === "terminate_joint_venture") {
        this.terminateJointVenture(player.seat, decision.parameters.contractId);
      }
      this.markAction(player, "influence", decision.label);
      return;
    }
    const scientificMethodLifetimeLimit =
      this.rulesVariant.imperialScientificMethodLifetimeLimit;
    const scientificMethodLifetimeUses =
      player.factionAbilityUsed.scientificMethodUses || 0;
    const scientificMethodRunwayCost =
      this.rulesVariant.imperialScientificMethodRunwayCost;
    const scientificMethodAvailable = Number.isFinite(scientificMethodLifetimeLimit)
      ? scientificMethodLifetimeUses < scientificMethodLifetimeLimit
      : !player.roundMetrics.scientificMethodUsed;
    const scientificMethodProtection =
      decision.actionId === "research" &&
      player.factionId === "imperial_research_lab" &&
      player.runway >= scientificMethodRunwayCost &&
      player.safety === 0 &&
      decision.parameters?.destinationCategory !== "research" &&
      scientificMethodAvailable;
    const scientificProtection =
      decision.actionId === "research" &&
      (scientificMethodProtection || decision.parameters?.destinationCategory === "research");
    const deferPublicMandate =
      scientificMethodProtection &&
      this.rulesVariant.imperialScientificMethodThresholdMandatePenalty > 0;
    if (deferPublicMandate) {
      this.deferredPublicMandateSeats ||= new Set();
      this.deferredPublicMandateSeats.add(player.seat);
    }
    if (scientificMethodProtection) this.spendRunway(
      player,
      scientificMethodRunwayCost,
      { cause: "scientific_method", conversionEligible: true }
    );
    if (scientificProtection) player.safety += 1;
    super.applyResolution(seat, decision);
    if (scientificProtection) {
      const scientificMethodUsed =
        scientificMethodProtection &&
        player.lastTrainingResult?.safetySpent > 0;
      player.safety = Math.min(before.safety, player.safety);
      if (scientificMethodUsed) {
        scientificMethodUsedThisResolution = true;
        const capabilityPenalty = Math.min(
          this.rulesVariant.imperialScientificMethodCapabilityPenalty,
          player.lastTrainingResult?.capability || 0
        );
        if (capabilityPenalty > 0) {
          player.capability -= capabilityPenalty;
          player.lastTrainingResult.capability -= capabilityPenalty;
          const researchResults = player.metrics.researchCapability;
          researchResults[researchResults.length - 1] -= capabilityPenalty;
        }
        player.roundMetrics.scientificMethodUsed = true;
        player.factionAbilityUsed.scientificMethodUses =
          scientificMethodLifetimeUses + 1;
        const scrutinyAdded =
          this.rulesVariant.imperialScientificMethodScrutiny;
        if (scrutinyAdded > 0) this.addScrutiny(player, scrutinyAdded);
        this.recordFactionAbility(player, "scientific_method", {
          runwaySpent: scientificMethodRunwayCost,
          duplicatesProtected: 1,
          capabilityPreserved: player.lastTrainingResult?.capability || 0,
          capabilityPenalty,
          thresholdMandateWithheld: 0,
          scrutinyAdded
        });
      } else if (scientificMethodProtection) {
        player.runway += scientificMethodRunwayCost;
      }
    }

    if (decision.actionId === "fund") {
      const expected = decision.parameters.mode === "venture" ? 4 : 2;
      const actual = decision.parameters.actualRunway ?? expected;
      this.addResource(player, "runway", actual - expected);
      player.roundMetrics.fundRunway += actual;
      player.roundMetrics.spotlightFundUsed = true;
      if (decision.parameters.extraScrutiny) this.addScrutiny(player, decision.parameters.extraScrutiny);
    }
    if (decision.actionId === "research") {
      const actualCost = decision.parameters.actualComputeCost ?? 1;
      player.compute += 1 - actualCost;
      const gained = player.capability - before.capability;
      if (decision.parameters.scalingLawBreakthrough) {
        const bonus = Math.min(3, gained);
        this.addResource(player, "capability", bonus);
        this.addScrutiny(player, 2);
        player.factionAbilityUsed.scalingLawBreakthrough = true;
        this.recordFactionAbility(player, "scaling_law_breakthrough", {
          capabilityGained: bonus,
          scrutinyAdded: 2
        });
      }
      if (this.regime.cycle?.id === "recursive_self_improvement") {
        this.addResource(player, "capability", gained);
      }
      if (decision.parameters.destinationCategory === "frontier" && gained > 0) {
        this.addResource(player, "capability", 1);
      }
      if (
        this.regime.cycle?.id === "professional_exam_sweep" &&
        gained >= 3
      ) {
        player.marketAccess += 1;
        if (gained >= 5) this.addResource(player, "trust", 1);
      }
      if (this.regime.cycle?.id === "benchmark_is_economy" && gained >= 3) {
        player.tacticModifiers.economicBenchmark = true;
      }
      if (player.tacticModifiers.benchmark_optimization && gained > 0) {
        this.addResource(player, "capability", 1);
        this.addScrutiny(player, 1);
        delete player.tacticModifiers.benchmark_optimization;
      }
      if (player.factionId === "imperial_research_lab" && this.round >= 3 && gained >= 5) {
        const trustBeforeNobel = player.trust;
        this.addResource(
          player,
          "trust",
          this.rulesVariant.imperialNobelTrust
        );
        this.recordFactionAbility(player, "nobel_effect", {
          trustGained: player.trust - trustBeforeNobel,
          qualifyingCapability: gained
        });
      }
      player.roundMetrics.bestTrainingDomains = Math.max(
        player.roundMetrics.bestTrainingDomains,
        gained
      );
      if (
        this.regime.cycle?.id === "recursive_self_improvement" &&
        gained === 0 &&
        player.scrutiny > before.scrutiny
      ) {
        this.addScrutiny(player, 2);
        this.systemicRisk += 1;
        this.matchMetrics.systemicRiskCreated += 1;
      }
      if (this.regime.cycle?.id === "ten_dollar_intelligence") this.addScrutiny(player, 1);
      if (
        player.tacticModifiers.emergency_pause &&
        player.capability === before.capability &&
        player.scrutiny > before.scrutiny
      ) {
        this.removeScrutiny(player, player.scrutiny - before.scrutiny);
        delete player.tacticModifiers.emergency_pause;
      }
    }
    if (decision.actionId === "build" && decision.parameters?.actualRunwayCost !== undefined) {
      const source = decision.parameters.buildMode === "generator"
        ? this.config.powerSources.find(
          (candidate) => candidate.id === decision.parameters.sourceId
        )
        : null;
      const defaultCost = decision.parameters.buildMode === "generator"
        ? source.runwayCost
        : decision.parameters.buildMode === "link"
          ? decision.parameters.cost
          : 2;
      if (decision.parameters.useBuildDiscount) player.buildDiscounts -= 1;
      if (
        player.factionId === "vertical_empire" &&
        this.rulesVariant.verticalIndustrialVelocityBuildModes.includes(
          decision.parameters.buildMode
        ) &&
        !player.roundMetrics.industrialVelocityUsed
      ) {
        const runwaySaved = decision.parameters.industrialVelocitySavings || 0;
        const mandateGained = runwaySaved >= 1
          ? this.rulesVariant.verticalIndustrialVelocityMandate
          : 0;
        player.roundMetrics.industrialVelocityUsed = true;
        this.awardMandate(
          player,
          mandateGained,
          "industrial_velocity"
        );
        this.recordFactionAbility(player, "industrial_velocity", {
          runwaySaved,
          mandateGained
        });
      }
      if (
        this.regime.cycle?.id === "reactor_restart_one_model" &&
        decision.parameters.sourceId === "clean_infrastructure" &&
        !this.regime.cycle.reactorClaimed
      ) {
        player.runway += 1;
        this.awardMandate(player, 1, "reactor_restart_one_model");
        this.regime.cycle.reactorClaimed = true;
        const government = this.board.find((tile) => tile.category === "government");
        for (const rival of this.players.filter((candidate) => candidate.seat !== seat)) {
          if (rival.influence.length < this.config.playerSupply.influenceCubes) {
            rival.influence.push({ tileId: government.instanceId });
          }
        }
      }
    }
    if (decision.actionId === "deploy") {
      if (decision.parameters.useMarketAccess) player.marketAccess -= 1;
      player.roundMetrics.deployed = true;
      if (!player.history.deployRounds.includes(this.round)) player.history.deployRounds.push(this.round);
      if (player.factionId === "safety_laboratory" && this.round >= 3 &&
        !player.roundMetrics.auditedDeployUsed) {
        const scrutinyBeforeAudit = player.scrutiny;
        this.removeScrutiny(player, 1);
        player.roundMetrics.auditedDeployUsed = true;
        this.recordFactionAbility(player, "audited_deployment", {
          scrutinyRemoved: scrutinyBeforeAudit - player.scrutiny,
          deploymentsCovered: 1
        });
      }
      if (player.factionId === "platform_empire" &&
        ["consumer", "media"].includes(decision.parameters.destinationCategory)) {
        player.roundMetrics.installedBaseUsed = true;
      }
      if (decision.parameters.socialGraph) player.roundMetrics.socialGraphUsed = true;
      if (player.seat === this.spotlightSeat && !player.roundMetrics.spotlightRiskUsed) {
        this.addScrutiny(player, 1);
        player.roundMetrics.spotlightRiskUsed = true;
      }
      if (this.regime.cycle?.id === "ten_dollar_intelligence") this.addScrutiny(player, 1);
      if (
        this.regime.cycle?.id === "synthetic_celebrity" &&
        ["consumer", "media"].includes(decision.parameters.destinationCategory)
      ) {
        this.addScrutiny(player, 2);
        player.tacticModifiers.syntheticCelebrityUsed = true;
      }
      if (this.regime.cycle?.deepfake === "regulate") {
        player.compute = Math.max(0, player.compute - 1);
        this.addResource(player, "trust", 1);
      }
      if (this.regime.cycle?.deepfake === "do_nothing") this.addScrutiny(player, 1);
      if (player.tacticModifiers.model_card) {
        this.removeScrutiny(player, 1);
        delete player.tacticModifiers.model_card;
      }
      if (player.tacticModifiers.api_price_cut) {
        player.roundMetrics.discountedCustomerNoIncome =
          (player.roundMetrics.discountedCustomerNoIncome || 0) + 1;
        delete player.tacticModifiers.api_price_cut;
      }
      if (player.tacticModifiers.economicBenchmark) {
        this.awardMandate(player, 1, "economic_benchmark");
        delete player.tacticModifiers.economicBenchmark;
      }
    }
    if (decision.actionId === "influence") {
      const destination = decision.parameters.destinationId;
      const tile = this.board.find((candidate) => candidate.instanceId === destination);
      if (tile && POLITICAL_CATEGORIES.has(tile.category)) {
        const extra = !decision.parameters.suppressDestinationBonus &&
          ["media", "government"].includes(tile.category) ? 1 : 0;
        for (let index = 0; index < 2 + extra; index += 1) {
          if (player.influence.length < this.config.playerSupply.influenceCubes) {
            player.influence.push({ tileId: destination });
          } else if (player.influence.length) {
            player.influence[index % player.influence.length].tileId = destination;
          }
        }
      }
    }

    if (player.scrutiny > before.scrutiny) player.roundMetrics.riskyActions += 1;
    if (
      this.regime.cycle?.incentivizedAction === decision.actionId
    ) {
      this.addResource(player, "runway", 2);
      this.addScrutiny(player, 1);
      player.roundMetrics.compliedWithLaw = true;
    }
    if (this.regime.cycle?.consensusAction === decision.actionId) {
      this.addResource(player, "runway", 2);
      this.addScrutiny(player, 2);
    }
    if (deferPublicMandate) {
      this.deferredPublicMandateSeats.delete(player.seat);
    }
    const mandateSynchronization = this.synchronizePublicMandate(
      player,
      decision.actionId,
      {
        capabilityMandatePenalty: scientificMethodUsedThisResolution
          ? this.rulesVariant.imperialScientificMethodThresholdMandatePenalty
          : 0
      }
    );
    if (
      scientificMethodUsedThisResolution &&
      mandateSynchronization.capabilityMandateWithheld > 0
    ) {
      const scientificMethod =
        player.metrics.factionAbilityValues.scientific_method;
      scientificMethod.thresholdMandateWithheld +=
        mandateSynchronization.capabilityMandateWithheld;
    }
    this.endRunwayConversionContext(player);
  }

  rewardFoundryComputeSpend(spenderSeat, spentCompute) {
    if (spentCompute < 2) return;
    for (const foundry of this.players.filter((candidate) =>
      candidate.factionId === "foundry" &&
      candidate.seat !== spenderSeat &&
      (candidate.roundMetrics.shovelTriggers || 0) <
        this.rulesVariant.foundryShovelsPerRound
    )) {
      this.addResource(foundry, "runway", 1);
      foundry.roundMetrics.shovelTriggers =
        (foundry.roundMetrics.shovelTriggers || 0) + 1;
      foundry.metrics.shovelsIncome += 1;
      this.recordFactionAbility(foundry, "the_shovels", {
        runwayGained: 1,
        qualifyingComputeSpend: spentCompute
      });
    }
  }

  markAction(player, actionId, label) {
    player.actionsUsed.push(actionId);
    increment(player.metrics.actions, actionId);
    if (this.round === 1) player.metrics.openingActions.push(actionId);
    this.synchronizePublicMandate(player, actionId);
    this.recordEligibility(player, "after_action");
    this.recordEvent("action_resolved", player.seat, `${player.factionName}: ${label}.`);
    this.endRunwayConversionContext(player);
  }

  suppressAgentSwarmDestinationBonus(player, decision) {
    const resolution = clone(decision);
    resolution.parameters.suppressDestinationBonus = true;
    const category = resolution.parameters.destinationCategory;
    if (resolution.actionId === "fund" && category === "capital") {
      resolution.parameters.actualRunway -= 1;
    }
    if (resolution.actionId === "research" && category === "cloud" &&
        this.regime.cycle?.id !== "ten_dollar_intelligence") {
      resolution.parameters.actualComputeCost = 1;
    }
    if (resolution.actionId === "deploy" && category === "consumer" &&
        this.regime.cycle?.id !== "ten_dollar_intelligence") {
      resolution.parameters.computeCost = this.rulesVariant.deployComputeCost;
    }
    if (resolution.actionId === "build" &&
        ["chip", "energy"].includes(category)) {
      resolution.parameters.actualRunwayCost += 1;
    }
    const computeCost = resolution.actionId === "research"
      ? resolution.parameters.actualComputeCost ?? 1
      : resolution.actionId === "deploy"
        ? resolution.parameters.computeCost
        : 0;
    const runwayCost = resolution.actionId === "build"
      ? resolution.parameters.actualRunwayCost
      : 0;
    return player.compute >= computeCost && player.runway >= runwayCost
      ? resolution
      : null;
  }

  gridReadyFacilityCount(player) {
    return this.declarationReadiness(player).gridReadyFacilities;
  }

  declarationReadiness(player) {
    const requirements = this.currentAgiRequirements();
    return declarationReadiness({
      board: this.board,
      players: this.players,
      contracts: this.contracts,
      megaClusters: this.megaClusters,
      startingGridPower: this.rulesVariant.startingGridPower,
      requirements
    }, player);
  }

  isAgiEligible(player) {
    return this.declarationReadiness(player).ready;
  }

  recordEligibility(player, timing) {
    this.recordAgiCoreRequirements(player, timing);
    if (!player.metrics.earliestAgiEligibility && this.isAgiEligible(player)) {
      player.metrics.earliestAgiEligibility = {
        round: this.round,
        cycle: this.cycle,
        timing
      };
    }
  }

  declareAgi(player) {
    const readiness = this.declarationReadiness(player);
    this.matchMetrics.declarationReadiness.push({
      seat: player.seat,
      round: this.round,
      cycle: this.cycle,
      ready: readiness.ready,
      failingRequirement: readiness.failingRequirement,
      ppaIterations: readiness.ppaIterations,
      capacityOps: readiness.capacityOps,
      supportingSeats: readiness.supportingSeats
    });
    player.compute -= this.rulesVariant.agiComputeCost;
    const first = this.firstAgiSeat === null;
    if (first) this.firstAgiSeat = player.seat;
    let score = first ? this.rulesVariant.agiFirstMandate : this.rulesVariant.agiLaterMandate;
    if (this.regime.persistent?.agiPersonhood === "person") {
      score += 2;
      this.removeScrutiny(player, 1);
    } else if (this.regime.persistent?.agiPersonhood === "property") {
      const controller = this.controller("government");
      if (controller !== null) this.addResource(this.players[controller], "runway", 2);
      this.systemicRisk += 1;
      this.matchMetrics.systemicRiskCreated += 1;
    }
    this.awardMandate(player, score, first ? "first_agi_declaration" : "agi_declaration");
    player.agiDeclared = true;
    markScenarioDeclaration(this, player);
    player.history.declarations += 1;
    this.matchMetrics.declarations += 1;
    this.markAgiFunnel(player, "declared", "wild_action_resolved", {
      supportingSeats: readiness.supportingSeats
    });
    this.addScrutiny(player, 3 + (player.seat === this.spotlightSeat ? 1 : 0));
    this.recordEvent(
      "agi_declared",
      player.seat,
      renderSimulationCopy(simulationCopy.events.agiDeclared, {
        faction: player.factionName,
        score
      })
    );
  }

  async applyWild(policies, seat, id, decision) {
    const player = this.players[seat];
    if (
      id === "mega_cluster" &&
      this.megaClusters.length >= this.config.sharedSupply.megaClusterPairs
    ) return;
    this.beginRunwayConversionContext(player, decision, "wild_action");
    this.movePiece(player, decision.parameters || {});
    const tokenFree = id === "agent_swarm" &&
      this.regime.cycle?.id === "agent_swarm_escapes_scope";
    if (!tokenFree) player.escalation -= 1;
    player.wildUsed.push(id);
    if (!player.history.wildRounds.includes(this.round)) player.history.wildRounds.push(this.round);
    increment(player.metrics.wildActions, id);
    increment(this.matchMetrics.wildActions, id);

    if (id === "mega_cluster") {
      const partner = decision.parameters.partnerSeat === undefined
        ? null
        : this.players[decision.parameters.partnerSeat];
      const leadCanPay = player.runway >= (partner ? 2 : 3) &&
        player.compute >= (partner ? 1 : 2);
      let accepted = leadCanPay;
      if (partner) {
        const partnerCanPay = partner.runway >= 1 && partner.compute >= 1;
        const response = await this.choose(
          policies,
          partner.seat,
          "mega_cluster_partner",
          [
            ...(leadCanPay && partnerCanPay ? [{
              decisionId: "mega_cluster_accept",
              label: decisionLabel("megaClusterAccept"),
              actionId: "mega_cluster"
            }] : []),
            {
              decisionId: "mega_cluster_reject",
              label: decisionLabel("megaClusterReject"),
              actionId: "mega_cluster"
            }
          ]
        );
        accepted = response.decisionId === "mega_cluster_accept";
      }
      if (partner && accepted) {
        this.spendRunway(player, 2, {
          cause: "mega_cluster",
          conversionEligible: true
        });
        player.compute -= 1;
        this.beginRunwayConversionContext(partner, {
          actionId: "mega_cluster",
          decisionId: "mega_cluster_accept"
        }, "wild_action_partner");
        this.spendRunway(partner, 1, {
          cause: "mega_cluster_partner",
          conversionEligible: true
        });
        this.endRunwayConversionContext(partner);
        partner.compute -= 1;
      } else if (!partner) {
        this.spendRunway(player, 3, {
          cause: "mega_cluster",
          conversionEligible: true
        });
        player.compute -= 2;
      }
      if (accepted) {
        const cluster = {
          id: `mega-${this.megaClusters.length + 1}`,
          leadSeat: seat,
          partnerSeat: partner?.seat ?? null,
          leftId: decision.parameters.leftId,
          rightId: decision.parameters.rightId,
          powered: false
        };
        this.megaClusters.push(cluster);
        player.megaClusters.push(cluster);
        if (partner) partner.megaClusters.push(cluster);
        this.addScrutiny(player, 2 + (seat === this.spotlightSeat ? 1 : 0));
      }
    } else if (id === "reorganization") {
      for (const piece of player.pieces.filter((piece) => piece.kind === "team")) {
        const options = this.board.filter((tile) =>
          axialDistance(
            this.board.find((current) => current.instanceId === piece.tileId),
            tile
          ) <= 1
        );
        piece.tileId = options[0].instanceId;
      }
      if (decision.parameters.returnTeam) {
        const team = player.pieces.find((piece) => piece.kind === "team");
        player.pieces = player.pieces.filter((piece) => piece.id !== team.id);
        player.teamsInSupply += 1;
        this.addResource(player, "runway", 3);
        this.addScrutiny(player, 1);
      }
    } else if (id === "open_weights") {
      player.history.openWeightsCapabilitySnapshot = this.players.map((candidate) => candidate.capability);
      for (const candidate of this.players) this.addResource(candidate, "capability", 1);
      this.addResource(player, "trust", player.factionId === "platform_empire" ? 3 : 2);
      if (player.factionId === "platform_empire") player.marketAccess += 1;
      this.removeScrutiny(player, 1);
      const media = this.board.find((tile) => tile.category === "media");
      if (media && player.influence.length < this.config.playerSupply.influenceCubes) {
        player.influence.push({ tileId: media.instanceId });
      }
    } else if (id === "narrative_capture") {
      for (const category of ["media", "government", "capital"]) {
        const tile = this.board.find((candidate) => candidate.category === category);
        if (player.influence.length < this.config.playerSupply.influenceCubes) {
          player.influence.push({ tileId: tile.instanceId });
        }
      }
      if (decision.parameters.mode === "scrutiny") this.removeScrutiny(player, 2);
      else if (decision.parameters.mode === "runway") this.addResource(player, "runway", 2);
      else this.addScrutiny(this.players[decision.parameters.targetSeat], 1);
    } else if (id === "agent_swarm") {
      const swarmDestination = decision.parameters.destinationId;
      const swarmPiece = decision.parameters.pieceId;
      for (let index = 0; index < 2; index += 1) {
        const selections = this.config.actions
          .filter((action) => !player.actionsUsed.includes(action.id))
          .filter((action) => this.legalResolutions(seat, action.id).length > 0)
          .map((action) => ({
            decisionId: `agent_select_${action.id}`,
            label: decisionLabel("agentSwarmSelects", { action: action.name }),
            actionId: action.id,
            parameters: { actionId: action.id }
          }));
        if (!selections.length) break;
        const selection = await this.choose(policies, seat, `agent_swarm_${index + 1}`, selections);
        let legal = this.legalResolutions(seat, selection.parameters.actionId)
          .filter((candidate) =>
            candidate.parameters?.destinationId === swarmDestination &&
            candidate.parameters?.pieceId === swarmPiece
          );
        if (index === 1) {
          legal = legal
            .map((candidate) =>
              this.suppressAgentSwarmDestinationBonus(player, candidate)
            )
            .filter(Boolean);
        }
        if (!legal.length) break;
        const resolution = clone(
          await this.choose(policies, seat, `agent_resolve_${index + 1}`, legal)
        );
        this.applyResolution(seat, resolution);
      }
      this.addScrutiny(
        player,
        (this.regime.cycle?.id === "agent_swarm_escapes_scope" ? 4 : 3) +
          (seat === this.spotlightSeat && !player.roundMetrics.spotlightRiskUsed ? 1 : 0)
      );
      if (seat === this.spotlightSeat) player.roundMetrics.spotlightRiskUsed = true;
    } else if (id === "declare_agi") {
      this.declareAgi(player);
    } else if (id === "fusion_demonstrator") {
      this.movePiece(player, decision.parameters);
      this.spendRunway(player, decision.parameters.cost, {
        cause: "fusion_demonstrator",
        conversionEligible: true
      });
      player.generators.push({
        id: `s${seat}-fusion`,
        tileId: decision.parameters.destinationId,
        sourceId: "fusion_demonstrator",
        capacity: 6
      });
      this.awardMandate(player, 2, "fusion_demonstrator");
      player.history.fusionBuilt = true;
      this.addScrutiny(player, 3);
    }
    this.recordEligibility(player, "after_wild_action");
    this.recordEvent(
      "wild_action_resolved",
      seat,
      renderSimulationCopy(simulationCopy.events.resolved, {
        faction: player.factionName,
        result: id
      })
    );
    this.endRunwayConversionContext(player);
  }

  infrastructureState(player) {
    const networked = networkedFacilityIds(this.board, {
      ...player,
      startingGridConnection: {
        assignedFacilityId: player.facilities[0]?.id || null
      }
    });
    const connectedGenerators = player.generators.filter((generator) => {
      const generatorTile = this.board.find((tile) => tile.instanceId === generator.tileId);
      return player.facilities.some((facility) => {
        if (!networked.has(facility.id)) return false;
        const facilityTile = this.board.find((tile) => tile.instanceId === facility.tileId);
        return generatorTile && facilityTile && axialDistance(generatorTile, facilityTile) <= 1;
      });
    });
    return { networked, connectedGenerators };
  }

  facilityContractResource(facility) {
    const tile = this.board.find((candidate) => candidate.instanceId === facility.tileId);
    if (!tile) return null;
    if (["research", "cloud", "chip"].includes(tile.category)) return "compute";
    if (tile.id === "grid_reactor") return "compute";
    if (["consumer", "capital", "talent", "media", "government"].includes(tile.category)) {
      return "runway";
    }
    if (tile.id === "renewable_basin") return "runway";
    return null;
  }

  async produceFacility(policies, player, facility, stage = "facility_production") {
    if (facility.category === "cloud") {
      this.addResource(player, "compute", 2);
      player.roundMetrics.computeProduced += 2;
    } else if (facility.category === "research") {
      this.addResource(player, "safety", 1);
    } else if (facility.category === "consumer") {
      this.addResource(player, "runway", 1);
    } else if (facility.category === "chip") {
      this.addResource(player, "compute", 1);
      player.roundMetrics.computeProduced += 1;
      player.buildDiscounts = Math.min(2, player.buildDiscounts + 1);
    } else if (facility.category === "capital") {
      this.addResource(player, "runway", 2);
    } else if (facility.category === "talent") {
      const decisions = [{
        decisionId: `${stage}_talent_stay`,
        label: decisionLabel("declineTalentMovement"),
        actionId: "production"
      }];
      for (const team of player.pieces.filter((piece) => piece.kind === "team")) {
        const current = this.board.find((tile) => tile.instanceId === team.tileId);
        for (const destination of this.board.filter(
          (tile) => axialDistance(current, tile) === 1
        )) {
          decisions.push({
            decisionId: `${stage}_talent_${team.id}_${destination.instanceId}`,
            label: decisionLabel("moveTalentTeam", {
              team: team.id,
              destination: destination.name
            }),
            actionId: "production",
            parameters: {
              pieceId: team.id,
              destinationId: destination.instanceId
            }
          });
        }
      }
      if (decisions.length > 1) {
        const choice = await this.choose(
          policies,
          player.seat,
          `${stage}_talent_movement`,
          decisions
        );
        const team = player.pieces.find(
          (piece) => piece.id === choice.parameters?.pieceId
        );
        if (team && choice.parameters?.destinationId) {
          team.tileId = choice.parameters.destinationId;
        }
      }
    } else if (facility.category === "media") {
      this.removeScrutiny(player, 1);
    } else if (facility.category === "government") {
      player.policyShields = Math.min(2, player.policyShields + 1);
    } else if (facility.category === "energy") {
      const tile = this.board.find((candidate) => candidate.instanceId === facility.tileId);
      if (tile?.id === "grid_reactor") {
        this.addResource(player, "compute", 1);
        player.roundMetrics.computeProduced += 1;
      } else {
        this.removeScrutiny(player, 1);
      }
    }
    if (facility.customSilicon) {
      this.addResource(player, "compute", 1);
      player.roundMetrics.computeProduced += 1;
    }
  }

  async produceAll(policies) {
    const infrastructure = this.players.map((player) => this.infrastructureState(player));
    const generation = this.players.map(() => ({
      starter: 0,
      generated: 0,
      exportable: 0,
      exported: 0,
      imported: 0,
      importSuppliers: []
    }));

    for (const player of this.players) {
      const state = infrastructure[player.seat];
      generation[player.seat].starter = player.facilities[0] &&
        state.networked.has(player.facilities[0].id)
        ? this.rulesVariant.startingGridPower
        : 0;
      for (const generator of state.connectedGenerators) {
        const source = this.config.powerSources.find(
          (candidate) => candidate.id === generator.sourceId
        ) || { id: generator.sourceId, name: generator.sourceId };
        increment(player.metrics.generatorChoices, source.id);
        if (source.scrutinyPerUse) this.addScrutiny(player, source.scrutinyPerUse);
        if (source.scrutinyPerUse) {
          increment(player.metrics.generatorScrutiny, source.id, source.scrutinyPerUse);
        }
        generation[player.seat].generated += generator.capacity;
        generation[player.seat].exportable += generator.capacity;
      }
      const superconductor = this.regime.round?.superconductor;
      if (superconductor === "replicates") {
        generation[player.seat].generated +=
          infrastructure[player.seat].connectedGenerators.length * 2;
      }
      const emergency = player.roundMetrics.emergencyPower || 0;
      generation[player.seat].generated += emergency;
      this.addScrutiny(player, emergency);
      if (emergency === 2) {
        this.systemicRisk += 1;
        this.matchMetrics.systemicRiskCreated += 1;
      }
      this.recordAgiCoreRequirements(player, "production_started");
      const localAvailable =
        generation[player.seat].starter + generation[player.seat].generated;
      const networkedFacilityCount = player.facilities.filter((facility) =>
        state.networked.has(facility.id)
      ).length;
      if (
        this.matchMetrics.agiFunnel[player.seat].coreRequirementsMet &&
        networkedFacilityCount >= this.rulesVariant.agiFacilities &&
        localAvailable < this.rulesVariant.agiFacilities
      ) {
        this.markAgiFunnel(
          player,
          "neededExternalPower",
          "before_power_market",
          {
            localAvailable,
            networkedFacilityCount,
            requiredFacilities: this.rulesVariant.agiFacilities
          }
        );
      }
    }

    const suppliersUsed = new Set();
    for (const buyerSeat of this.initiativeOrder()) {
      if (this.round < 3) break;
      const buyer = this.players[buyerSeat];
      for (let purchase = 0; purchase < 2 && buyer.runway > 0; purchase += 1) {
        const suppliers = this.players.filter((supplier) =>
          supplier.seat !== buyerSeat &&
          !suppliersUsed.has(supplier.seat) &&
          generation[supplier.seat].exportable - generation[supplier.seat].exported >= 1 &&
          [...infrastructure[buyerSeat].networked].some((buyerFacilityId) => {
            const buyerFacility = buyer.facilities.find(
              (facility) => facility.id === buyerFacilityId
            );
            return [...infrastructure[supplier.seat].networked].some((supplierFacilityId) => {
              const supplierFacility = supplier.facilities.find(
                (facility) => facility.id === supplierFacilityId
              );
              return buyerFacility && supplierFacility &&
                this.areAdjacent(buyerFacility.tileId, supplierFacility.tileId);
            });
          })
        );
        if (!suppliers.length) break;
        const request = await this.choose(policies, buyerSeat, `power_purchase_${purchase}`, [
          {
            decisionId: `power_purchase_none_${purchase}`,
            label: decisionLabel("declinePower"),
            actionId: "production"
          },
          ...suppliers.map((supplier) => ({
            decisionId: `power_purchase_from_${supplier.seat}_${purchase}`,
            label: decisionLabel("buyPower", { seat: supplier.seat + 1 }),
            actionId: "production",
            parameters: {
              supplierSeat: supplier.seat,
              targetSeat: supplier.seat,
            }
          }))
        ]);
        if (request.parameters?.supplierSeat === undefined) break;
        const supplier = this.players[request.parameters.supplierSeat];
        const promise = this.activePowerPromise(supplier.seat, buyerSeat);
        const response = await this.choose(
          policies,
          supplier.seat,
          `power_sale_${buyerSeat}_${purchase}`,
          [
            {
              decisionId: `power_sale_accept_${buyerSeat}_${purchase}`,
              label: decisionLabel("offerPower", { seat: buyerSeat + 1 }),
              actionId: "production",
              parameters: {
                buyerSeat,
                targetSeat: buyerSeat,
                relationship: this.relationshipFor(supplier.seat, buyerSeat)
              },
              consequences: {
                runway: 1,
                exportedPower: -1,
                promiseFulfillment: promise ? 1 : 0
              }
            },
            {
              decisionId: `power_sale_reject_${buyerSeat}_${purchase}`,
              label: decisionLabel("declinePower"),
              actionId: "production",
              parameters: {
                buyerSeat,
                targetSeat: buyerSeat,
                relationship: this.relationshipFor(supplier.seat, buyerSeat)
              },
              consequences: {
                retainedPower: 1,
                promiseBetrayal: promise ? 1 : 0
              }
            }
          ]
        );
        if (!response.decisionId.startsWith("power_sale_accept_")) {
          if (promise) {
            promise.status = "broken";
            supplier.metrics.promisesBroken += 1;
            this.changeRelationship(supplier.seat, buyerSeat, "broken");
            this.matchMetrics.negotiations.push({
              ...clone(promise),
              status: "broken",
              resolvedRound: this.round
            });
          }
          continue;
        }
        this.markAgiFunnel(buyer, "receivedPowerOffer", "power_sale_accepted", {
          supplierSeat: supplier.seat,
          priceRunway: 1
        });
        this.spendRunway(buyer, 1, { cause: "power_purchase" });
        this.addResource(supplier, "runway", 1);
        generation[supplier.seat].exported += 1;
        generation[buyer.seat].imported += 1;
        generation[buyer.seat].importSuppliers.push(supplier.seat);
        suppliersUsed.add(supplier.seat);
        buyer.metrics.powerBought += 1;
        this.markAgiFunnel(buyer, "acceptedPowerPrice", "power_transferred", {
          supplierSeat: supplier.seat,
          priceRunway: 1
        });
        supplier.metrics.powerSold += 1;
        supplier.metrics.powerTradeRunway += 1;
        if (promise) {
          promise.status = "fulfilled";
          supplier.metrics.promisesFulfilled += 1;
          this.changeRelationship(supplier.seat, buyerSeat, "fulfilled");
          this.matchMetrics.negotiations.push({
            ...clone(promise),
            status: "fulfilled",
            resolvedRound: this.round
          });
        }
        this.matchMetrics.powerTrades.push({
          round: this.round,
          buyerSeat,
          supplierSeat: supplier.seat,
          causallyNecessary: false
        });
      }
    }

    for (const promise of this.negotiationPromises.filter((entry) =>
      entry.status === "open" && entry.round <= this.round
    )) {
      promise.status = "unexercised";
      this.matchMetrics.negotiations.push({
        ...clone(promise),
        status: "unexercised",
        resolvedRound: this.round
      });
    }

    for (const player of this.players) {
      const state = infrastructure[player.seat];
      const available =
        generation[player.seat].starter +
        generation[player.seat].generated -
        generation[player.seat].exported +
        generation[player.seat].imported;
      const eligible = player.facilities.filter((facility) => state.networked.has(facility.id));
      const subsets = [];
      for (let mask = 0; mask < 2 ** eligible.length; mask += 1) {
        const selected = eligible.filter((_, index) => mask & (1 << index));
        const demand = selected.length;
        if (demand <= available) subsets.push({ selected, demand });
      }
      const decisions = subsets.map(({ selected, demand }) => ({
        decisionId: `power_${selected.map((facility) => facility.id).join("_") || "none"}`,
        label: selected.length
          ? `Power ${selected.map((facility) => facility.id).join(", ")} (${demand}/${available})`
          : `Power no Facilities (0/${available})`,
        actionId: "production",
        parameters: { facilityIds: selected.map((facility) => facility.id), demand },
        consequences: { poweredFacilities: selected.length, powerDemand: demand }
      }));
      const allocation = await this.choose(
        policies,
        player.seat,
        "power_allocation",
        decisions
      );
      const poweredIds = new Set(allocation.parameters.facilityIds);
      const localAvailable =
        generation[player.seat].starter +
        generation[player.seat].generated -
        generation[player.seat].exported;
      const necessarySuppliers = causallyNecessaryImportSuppliers({
        localAvailable,
        importedSupplierSeats: generation[player.seat].importSuppliers,
        allocatedDemand: allocation.parameters.demand
      });
      for (const trade of this.matchMetrics.powerTrades.filter(
        (candidate) =>
          candidate.round === this.round &&
          candidate.buyerSeat === player.seat
      )) {
        trade.causallyNecessary = necessarySuppliers.includes(
          trade.supplierSeat
        );
      }
      for (const facility of player.facilities) {
        facility.powered = poweredIds.has(facility.id);
        facility.gridReady = facility.powered;
        facility.gridReadySupportSeats = facility.gridReady
          ? [...necessarySuppliers]
          : [];
      }
      if (
        player.facilities.filter((facility) => facility.gridReady).length >=
        this.rulesVariant.agiFacilities
      ) {
        this.markAgiFunnel(player, "becameGridReady", "power_allocated", {
          gridReadyFacilities: player.facilities.filter(
            (facility) => facility.gridReady
          ).length,
          supportingSeats: necessarySuppliers
        });
      }
      player.roundMetrics.powerDemandSatisfied = allocation.parameters.demand;
      player.roundMetrics.availablePower = available;
    }

    for (const cluster of this.megaClusters) {
      const lead = this.players[cluster.leadSeat];
      const partner = cluster.partnerSeat === null ? lead : this.players[cluster.partnerSeat];
      const left = lead.facilities.find((facility) => facility.id === cluster.leftId);
      const right = partner.facilities.find((facility) => facility.id === cluster.rightId) ||
        lead.facilities.find((facility) => facility.id === cluster.rightId);
      if (!left || !right || !left.powered || !right.powered ||
          !this.areAdjacent(left.tileId, right.tileId)) {
        cluster.powered = false;
        continue;
      }
      if (cluster.partnerSeat === null) {
        const remaining =
          lead.roundMetrics.availablePower - lead.roundMetrics.powerDemandSatisfied;
        cluster.powered = remaining >= 2;
        if (cluster.powered) {
          lead.roundMetrics.powerDemandSatisfied += 2;
          this.addResource(lead, "compute", 3);
          lead.roundMetrics.computeProduced += 3;
        }
      } else {
        const leadRemaining =
          lead.roundMetrics.availablePower - lead.roundMetrics.powerDemandSatisfied;
        const partnerRemaining =
          partner.roundMetrics.availablePower - partner.roundMetrics.powerDemandSatisfied;
        cluster.powered = leadRemaining >= 1 && partnerRemaining >= 1;
        if (cluster.powered) {
          lead.roundMetrics.powerDemandSatisfied += 1;
          partner.roundMetrics.powerDemandSatisfied += 1;
          this.addResource(lead, "compute", 2);
          this.addResource(partner, "compute", 1);
          lead.roundMetrics.computeProduced += 2;
          partner.roundMetrics.computeProduced += 1;
        }
      }
    }

    for (const player of this.players) {
      for (const facility of player.facilities.filter((candidate) => candidate.powered)) {
        await this.produceFacility(policies, player, facility);
      }
      if (
        this.round >= 2 &&
        player.facilities.filter((facility) => facility.powered).length >= 2
      ) {
        const choice = await this.choose(policies, player.seat, "network_bonus", [
          {
            decisionId: "network_runway",
            label: decisionLabel("networkBonusRunway"),
            actionId: "production",
            consequences: { runway: 1 }
          },
          {
            decisionId: "network_compute",
            label: decisionLabel("networkBonusCompute"),
            actionId: "production",
            consequences: { compute: 1 }
          }
        ]);
        const resource = choice.decisionId === "network_compute" ? "compute" : "runway";
        this.addResource(player, resource, 1);
        if (resource === "compute") player.roundMetrics.computeProduced += 1;
      }
    }

    for (const contract of this.contracts
      .filter((candidate) => candidate.kind === "joint_venture")
      .sort((left, right) => left.id - right.id)) {
      const leftPlayer = this.players[contract.left.seat];
      const rightPlayer = this.players[contract.right.seat];
      const left = leftPlayer.facilities.find(
        (facility) => facility.id === contract.left.facilityId
      );
      const right = rightPlayer.facilities.find(
        (facility) => facility.id === contract.right.facilityId
      );
      const range = [leftPlayer, rightPlayer].some(
        (candidate) => candidate.factionId === "coalition_lab"
      ) ? 2 : 1;
      if (!left?.powered || !right?.powered) continue;
      const leftTile = this.board.find((tile) => tile.instanceId === left.tileId);
      const rightTile = this.board.find((tile) => tile.instanceId === right.tileId);
      if (axialDistance(leftTile, rightTile) > range) continue;
      const leftResource = this.facilityContractResource(right);
      const rightResource = this.facilityContractResource(left);
      if (leftResource) this.addResource(leftPlayer, leftResource, 1);
      if (rightResource) this.addResource(rightPlayer, rightResource, 1);
      if (contract.createdRound === this.round) {
        leftPlayer.roundMetrics.activeNewJointVentures =
          (leftPlayer.roundMetrics.activeNewJointVentures || 0) + 1;
        rightPlayer.roundMetrics.activeNewJointVentures =
          (rightPlayer.roundMetrics.activeNewJointVentures || 0) + 1;
      }
    }

    for (const player of this.players) {
      let customerIncome = Math.max(
        0,
        player.customers - (player.roundMetrics.discountedCustomerNoIncome || 0)
      );
      if (this.regime.round?.deepfakeIncome) customerIncome +=
        player.customers - player.roundMetrics.customersStart;
      this.addResource(player, "runway", customerIncome);
      const powered = player.facilities.filter((facility) => facility.powered).length;
      player.metrics.poweredFacilityRounds.push({
        round: this.round,
        powered,
        facilities: player.facilities.length,
        supply: player.roundMetrics.availablePower,
        demandSatisfied: player.roundMetrics.powerDemandSatisfied,
        networked: infrastructure[player.seat].networked.size
      });
      player.metrics.gridReadyFacilityRounds.push({
        round: this.round,
        gridReady: player.facilities.filter((facility) => facility.gridReady).length
      });
      this.recordEligibility(player, "after_production");
    }
    const platform = this.players.find((player) => player.factionId === "platform_empire");
    const leader = Math.max(...this.players.map((player) => this.currentScore(player)));
    this.matchMetrics.productionSnapshots.push({
      round: this.round,
      scores: this.players.map((player) => ({
        seat: player.seat,
        factionId: player.factionId,
        mandate: this.currentScore(player),
        poweredFacilities: player.facilities.filter((facility) => facility.powered).length,
        gridReadyFacilities: player.facilities.filter((facility) => facility.gridReady).length
      })),
      platformLead: platform ? this.currentScore(platform) - leader : null,
      gridGeneratorSlotsFilled: this.generatorOccupancy(
        this.board.find((tile) => tile.id === "grid_reactor").instanceId
      )
    });
  }

  facilityComponents(player) {
    const remaining = new Set(player.facilities.map((facility) => facility.id));
    const result = [];
    while (remaining.size) {
      const first = remaining.values().next().value;
      remaining.delete(first);
      const component = [first];
      const queue = [first];
      while (queue.length) {
        const currentId = queue.shift();
        const current = player.facilities.find((facility) => facility.id === currentId);
        for (const candidate of player.facilities) {
          if (remaining.has(candidate.id) && this.areAdjacent(current.tileId, candidate.tileId)) {
            remaining.delete(candidate.id);
            component.push(candidate.id);
            queue.push(candidate.id);
          }
        }
      }
      result.push(component);
    }
    return result;
  }

  audit() {
    const base = this.config.rounds[this.round - 1].auditBaseDraws;
    const draws = Math.max(
      1,
      Math.round(base * this.playerCount / 4 * this.rulesVariant.auditMultiplier)
    );
    const rng = createRng(`${this.seed}:audit:${this.round}`);
    for (let draw = 0; draw < draws; draw += 1) {
      const bag = [
        ...this.players.flatMap((player) =>
          Array.from({ length: player.scrutiny }, () => ({ type: "player", seat: player.seat }))
        ),
        ...Array.from({ length: this.systemicRisk }, () => ({ type: "systemic" }))
      ];
      if (!bag.length) break;
      const selected = bag[Math.floor(rng() * bag.length)];
      if (selected.type === "systemic") {
        this.systemicRisk -= 1;
        for (const player of this.players.filter((candidate) => candidate.customers >= 3)) {
          if (this.round === 4) {
            if (player.runway >= 2) {
              this.spendRunway(player, 2, { cause: "systemic_audit" });
            }
            else if (player.mandate > 0) player.mandate -= 1;
            else this.spendRunway(player, player.runway, { cause: "systemic_audit" });
          } else if (player.runway > 0) {
            this.spendRunway(player, 1, { cause: "systemic_audit" });
          }
          else this.addResource(player, "trust", -1);
          player.metrics.systemicRiskHits += 1;
        }
      } else {
        const player = this.players[selected.seat];
        player.scrutiny -= 1;
        player.metrics.auditHits += 1;
        if (this.round === 4) {
          if (player.runway >= 2) {
            this.spendRunway(player, 2, { cause: "player_audit" });
          }
          else if (player.mandate > 0) player.mandate -= 1;
          else this.spendRunway(player, player.runway, { cause: "player_audit" });
        } else if (player.runway > 0) {
          this.spendRunway(player, 1, { cause: "player_audit" });
        }
        else if (player.policyShields > 0) player.policyShields -= 1;
        else this.addResource(player, "trust", -1);
      }
    }
  }

  scoreMandate() {
    const id = this.roundMandate.id;
    const values = this.players.map((player) => {
      if (id === "quarter_humanity_notices") return player.capability - player.roundMetrics.capabilityStart;
      if (id === "continent_signs_loi") return player.customers - player.roundMetrics.customersStart;
      if (id === "building_has_weather") return player.facilities.filter((facility) => facility.powered).length;
      if (id === "stack_reaches_horizon") return player.roundMetrics.powerDemandSatisfied || 0;
      if (id === "voluntary_coordination_triumphs") return player.roundMetrics.activeNewJointVentures || 0;
      if (id === "legibility_offensive") return player.roundMetrics.deployed ? player.trust : -1;
      if (id === "national_champion_without_nationalization") return this.controlledCategories(player).size;
      if (id === "model_ate_tuesday") return player.roundMetrics.bestTrainingDomains;
      if (id === "compute_new_weather") return player.roundMetrics.computeProduced;
      if (id === "zero_incident_quarter") {
        const added = player.metrics.scrutinyAdded - player.roundMetrics.scrutinyStart;
        return added > 0 ? -added : -Infinity;
      }
      if (id === "responsible_acceleration") return player.trust >= 4 ? player.capability : -1;
      if (id === "markets_prefer_destiny") return player.roundMetrics.fundRunway;
      return 0;
    });
    const minimum = this.roundMandate.minimumQualification ?? 1;
    const qualifiedValues = values.map((value) => value >= minimum ? value : -Infinity);
    const maximum = Math.max(...qualifiedValues);
    increment(this.matchMetrics.mandates, id);
    if (!Number.isFinite(maximum)) return;
    const winners = qualifiedValues.map((value, seat) => value === maximum ? seat : null)
      .filter((seat) => seat !== null);
    for (const seat of winners) {
      const points = winners.length === 1 ? this.mandateDocument.points.winner : this.mandateDocument.points.tied;
      this.awardMandate(this.players[seat], points, `round_mandate:${id}`);
      this.players[seat].metrics.mandatesWon[id] = points;
    }
  }

  objectiveComplete(player) {
    const id = player.objectiveId;
    const powered = player.facilities.filter((facility) => facility.powered).length;
    if (id === "quietly_indispensable") return powered >= 2 && player.scrutiny <= 4;
    if (id === "too_big_to_pause") return player.customers >= 3 && player.trust <= 3;
    if (id === "benevolent_monopoly") return player.customers >= 3 && player.trust >= 4;
    if (id === "institutional_capture") {
      return ["media", "government", "capital"]
        .filter((category) => this.controller(category) === player.seat).length >= 2;
    }
    if (id === "distributed_scarcity") {
      return this.facilityComponents(player).some((component) => component.length >= 2) &&
        player.generators.length >= 1;
    }
    if (id === "paper_agi") return player.agiDeclared && player.facilities.length === 2;
    if (id === "industrial_sublime") {
      return player.facilities.length >= 3 && player.generators.length >= 1 &&
        player.links.length >= 2;
    }
    if (id === "public_option_private_invoice") {
      return [this.controller("government"), this.controller("capital")].includes(player.seat) &&
        player.runway >= 6;
    }
    if (id === "open_closed_loop") {
      if (!player.history.openWeightsCapabilitySnapshot) return false;
      return this.players.every((candidate) =>
        candidate.seat === player.seat ||
        player.history.openWeightsCapabilitySnapshot[candidate.seat] >=
          player.history.openWeightsCapabilitySnapshot[player.seat] ||
        player.capability > candidate.capability
      );
    }
    if (id === "alignment_as_service") return player.trust >= 4 && player.jointVentures.length > 0;
    if (id === "everyone_customer") return player.history.deployRounds.length >= 2;
    if (id === "regulatory_moat") return player.policyShields >= 1 && this.controller("government") === player.seat;
    if (id === "recursive_revenue") {
      return player.customers > 0 && player.facilities.length > 0 &&
        this.facilityComponents(player).some((component) => component.length >= 2) &&
        player.jointVentures.length > 0;
    }
    if (id === "compute_diplomacy") {
      return player.metrics.powerBought + player.metrics.powerSold >= 1;
    }
    if (id === "credible_denial") return player.capability >= 8 && player.customers <= 1;
    if (id === "history_will_call") return player.history.cumulativeScrutiny >= 6 && player.trust >= 4;
    if (id === "fusion_press_cycle") return player.history.fusionBuilt && player.agiDeclared;
    if (id === "perfectly_normal_quarter") return player.history.wildRounds.length >= 2;
    return false;
  }

  tradableResources(player, receiver, excluded = null) {
    const exportControl = this.regime.cycle?.id === "export_controls";
    const caps = {
      runway: this.config.resources.runway.cap,
      compute: this.config.resources.compute.cap,
      safety: this.config.resources.safety.cap
    };
    return ["runway", "compute", "safety"].filter((resource) =>
      resource !== excluded &&
      !(exportControl && resource === "compute") &&
      player[resource] > 0 &&
      receiver[resource] < (
        resource === "safety" && receiver.factionId === "safety_laboratory"
          ? 4
          : caps[resource]
      )
    );
  }

  selectedActionResolutions(seat) {
    const player = this.players[seat];
    if (!player.selectedAction) return [];
    if (player.selectedAction.startsWith("wild_")) {
      return this.legalWildResolutions(seat, player.selectedAction.slice(5));
    }
    if (player.selectedAction.startsWith("faction_")) return [];
    return this.legalResolutions(seat, player.selectedAction);
  }

  preservesSelectedActionResolution(seat, resource, amount) {
    const player = this.players[seat];
    if (!player.selectedAction) return true;
    const before = player[resource];
    player[resource] -= amount;
    const remainsResolvable = this.selectedActionResolutions(seat).length > 0;
    player[resource] = before;
    return remainsResolvable;
  }

  immediateTradeGiveAmounts(seat, partner, resource) {
    const player = this.players[seat];
    const partnerCap = resource === "safety" && partner.factionId === "safety_laboratory"
      ? 4
      : this.config.resources[resource].cap;
    const maximumGive = Math.min(player[resource], partnerCap - partner[resource]);
    return Array.from({ length: maximumGive }, (_, index) => index + 1)
      .filter((amount) => this.preservesSelectedActionResolution(seat, resource, amount));
  }

  immediateTradeReceiveAmounts(seat, partner, resource) {
    const player = this.players[seat];
    const playerCap = resource === "safety" && player.factionId === "safety_laboratory"
      ? 4
      : this.config.resources[resource].cap;
    const maximumReceive = Math.min(partner[resource], playerCap - player[resource]);
    return Array.from({ length: maximumReceive }, (_, index) => index + 1)
      .filter((amount) =>
        this.preservesSelectedActionResolution(partner.seat, resource, amount)
      );
  }

  immediateTradeDecisions(seat) {
    const player = this.players[seat];
    const decisions = [{
      decisionId: "trade_none",
      label: decisionLabel("tradeNone"),
      actionId: "trade"
    }];
    for (const partner of this.players.filter((candidate) => candidate.seat !== seat)) {
      const giveResources = this.tradableResources(player, partner).filter(
        (resource) => this.immediateTradeGiveAmounts(seat, partner, resource).length > 0
      );
      for (const giveResource of giveResources) {
        for (const giveAmount of this.immediateTradeGiveAmounts(seat, partner, giveResource)) {
          const receiveResources = this.tradableResources(partner, player, giveResource).filter(
            (resource) => this.immediateTradeReceiveAmounts(seat, partner, resource).length > 0
          );
          for (const receiveResource of receiveResources) {
            for (const receiveAmount of this.immediateTradeReceiveAmounts(
              seat,
              partner,
              receiveResource
            )) {
              for (const timing of ["before", "after"]) {
                decisions.push({
                  decisionId: [
                    "trade_offer",
                    timing,
                    partner.seat,
                    giveResource,
                    giveAmount,
                    receiveResource,
                    receiveAmount
                  ].join("_"),
                  label: decisionLabel("tradeOffer", {
                    timing: timing === "before"
                      ? decisionLabel("tradeTimingBefore")
                      : decisionLabel("tradeTimingAfter"),
                    giveAmount,
                    giveResource,
                    partner: partner.factionName,
                    receiveAmount,
                    receiveResource
                  }),
                  actionId: "trade",
                  parameters: {
                    timing,
                    partnerSeat: partner.seat,
                    targetSeat: partner.seat,
                    giveResource,
                    giveAmount,
                    receiveResource,
                    receiveAmount
                  }
                });
              }
            }
          }
        }
      }
    }
    return decisions;
  }

  async chooseImmediateTrade(policies, seat) {
    const decisions = this.immediateTradeDecisions(seat);
    if (decisions.length === 1) return null;
    const choice = await this.choose(policies, seat, "immediate_trade", decisions);
    return choice.parameters?.partnerSeat === undefined ? null : choice.parameters;
  }

  canCompleteImmediateTrade(seat, partnerSeat, offer) {
    const partner = this.players[partnerSeat];
    return this.immediateTradeGiveAmounts(seat, partner, offer.giveResource).includes(
      offer.giveAmount
    ) && this.immediateTradeReceiveAmounts(seat, partner, offer.receiveResource).includes(
      offer.receiveAmount
    );
  }

  immediateTradeCounterDecisions(seat, offer) {
    const counterMaker = this.players[offer.partnerSeat];
    return this.immediateTradeDecisions(counterMaker.seat)
      .filter((decision) =>
        decision.parameters?.partnerSeat === seat &&
        decision.parameters.timing === offer.timing
      )
      .map((decision) => ({
        ...decision,
        decisionId: decision.decisionId.replace("trade_offer_", "trade_counter_"),
        label: decisionLabel("tradeCounter", { offer: decision.label }),
        parameters: {
          ...decision.parameters,
          counterMakerSeat: counterMaker.seat
        }
      }));
  }

  completeImmediateTrade(seat, partnerSeat, offer) {
    const player = this.players[seat];
    const partner = this.players[partnerSeat];
    if (!this.canCompleteImmediateTrade(seat, partnerSeat, offer)) return false;
    if (offer.giveResource === "runway") {
      this.spendRunway(player, offer.giveAmount, { cause: "immediate_trade_payment" });
    } else {
      player[offer.giveResource] -= offer.giveAmount;
    }
    if (offer.receiveResource === "runway") {
      this.spendRunway(partner, offer.receiveAmount, {
        cause: "immediate_trade_payment"
      });
    } else {
      partner[offer.receiveResource] -= offer.receiveAmount;
    }
    this.addResource(partner, offer.giveResource, offer.giveAmount);
    this.addResource(player, offer.receiveResource, offer.receiveAmount);
    for (const participant of [player, partner]) {
      if (
        participant.factionId === "coalition_lab" &&
        !this.isFactionAbilityPaused(participant, "deal_flow") &&
        !participant.roundMetrics.dealFlowUsed
      ) {
        const runwayGained = this.grantDealFlowRunway(participant, {
          tradeMakerSeat: seat,
          partnerSeat
        });
        participant.roundMetrics.dealFlowUsed = true;
        this.recordFactionAbility(participant, "deal_flow", {
          runwayGained,
          creditsGranted: runwayGained,
          completedTrades: 1
        });
      }
    }
    this.recordEvent(
      "immediate_trade",
      seat,
      `${player.factionName} traded ${offer.giveAmount} ${offer.giveResource} to ` +
        `${partner.factionName} for ${offer.receiveAmount} ${offer.receiveResource}.`
    );
    return true;
  }

  async settleImmediateTrade(policies, seat, offer) {
    if (!offer) return false;
    this.activeImmediateTradeSeat = seat;
    const partner = this.players[offer.partnerSeat];
    const counters = this.immediateTradeCounterDecisions(seat, offer);
    const response = await this.choose(policies, partner.seat, "immediate_trade_response", [
      {
        decisionId: "trade_reject",
        label: decisionLabel("tradeReject", offer),
        actionId: "trade"
      },
      {
        decisionId: "trade_accept",
        label: decisionLabel("tradeAccept", offer),
        actionId: "trade"
      },
      ...counters
    ]);
    if (response.decisionId === "trade_accept") {
      return this.completeImmediateTrade(seat, partner.seat, offer);
    }
    if (!response.parameters?.counterMakerSeat) return false;

    const counterOffer = response.parameters;
    const claimants = this.players.filter((candidate) =>
      candidate.seat !== partner.seat &&
      this.canCompleteImmediateTrade(partner.seat, candidate.seat, counterOffer)
    );
    const claims = await Promise.all(claimants.map(async (claimant) => ({
      claimant,
      choice: await this.choose(policies, claimant.seat, "immediate_trade_claim", [
        {
          decisionId: "trade_claim_pass",
          label: decisionLabel("tradeClaimPass"),
          actionId: "trade"
        },
        {
          decisionId: "trade_claim_accept",
          label: decisionLabel("tradeClaimAccept"),
          actionId: "trade",
          parameters: { claimantSeat: claimant.seat }
        }
      ])
    })));
    const claimed = claims.filter(({ choice }) => choice.parameters?.claimantSeat !== undefined);
    if (!claimed.length) return false;
    const counterparty = await this.choose(
      policies,
      partner.seat,
      "immediate_trade_counterparty",
      [
        {
          decisionId: "trade_counterparty_decline",
          label: decisionLabel("tradeCounterpartyDecline"),
          actionId: "trade"
        },
        ...claimed.map(({ claimant }) => ({
          decisionId: `trade_counterparty_${claimant.seat}`,
          label: decisionLabel("tradeCounterpartyAccept", {
            faction: claimant.factionName
          }),
          actionId: "trade",
          parameters: { claimantSeat: claimant.seat }
        }))
      ]
    );
    if (counterparty.parameters?.claimantSeat === undefined) return false;
    return this.completeImmediateTrade(
      partner.seat,
      counterparty.parameters.claimantSeat,
      counterOffer
    );
  }

  async resolveSelectedSeat(policies, seat) {
    const player = this.players[seat];
    const trade = await this.chooseImmediateTrade(policies, seat);
    if (trade?.timing === "before") await this.settleImmediateTrade(policies, seat, trade);
    const orbitalUsed = await this.maybeUseOrbitalCompute(policies, seat);
    if (player.selectedAction.startsWith("faction_")) {
      const computeBeforeAction = player.compute;
      await this.resolveFactionAction(
        policies,
        seat,
        player.selectedAction.slice("faction_".length)
      );
      this.rewardFoundryComputeSpend(
        seat,
        computeBeforeAction - player.compute
      );
      player.selectedAction = null;
      return;
    }
    if (player.selectedAction.startsWith("wild_")) {
      const id = player.selectedAction.slice(5);
      let legal = this.legalWildResolutions(seat, id);
      if (orbitalUsed) {
        legal = legal.filter((decision) => {
          const piece = player.pieces.find(
            (candidate) => candidate.id === decision.parameters?.pieceId
          );
          return !decision.parameters?.pieceId ||
            decision.parameters.destinationId === piece?.tileId;
        });
      }
      if (!legal.length) {
        this.recordEvent(
          "wild_action_blocked",
          seat,
          renderSimulationCopy(simulationCopy.events.wildBlocked, {
            faction: player.factionName,
            action: id
          })
        );
        player.selectedAction = null;
        return;
      }
      const decision = await this.choose(policies, seat, `resolve_wild_${id}`, legal);
      const computeBeforeAction = player.compute;
      await this.applyWild(policies, seat, id, decision);
      this.rewardFoundryComputeSpend(
        seat,
        computeBeforeAction - player.compute
      );
      await this.resolveFrontierBridge(policies, seat, decision);
      if (trade?.timing === "after") await this.settleImmediateTrade(policies, seat, trade);
      player.selectedAction = null;
      return;
    }
    const capabilityBefore = player.capability;
    const scrutinyBefore = player.scrutiny;
    const runwayBefore = player.runway;
    const dealFlowCreditsBefore = clone(player.dealFlowRunwayCredits);
    const dealFlowConversionBefore = clone(player.metrics.dealFlowConversion);
    const trustBefore = player.trust;
    const safetyBefore = player.safety;
    let legal = this.legalResolutions(seat, player.selectedAction);
    if (orbitalUsed) {
      legal = legal.filter((decision) => {
        const piece = player.pieces.find(
          (candidate) => candidate.id === decision.parameters?.pieceId
        );
        return decision.parameters?.destinationId === piece?.tileId;
      });
    }
    if (!legal.length) {
      player.metrics.forcedNoOps += 1;
      legal = [{
        decisionId: `forced_noop_${player.selectedAction}`,
        label: decisionLabel("noLegalResolution", { action: player.selectedAction }),
        actionId: player.selectedAction,
        parameters: {},
        consequences: { noOp: true }
      }];
    }
    const decision = await this.choose(policies, seat, "resolve", legal);
    if (decision.parameters?.mode === "joint_venture") {
      await this.negotiate(policies, seat, decision);
    }
    const computeBeforeAction = player.compute;
    this.applyResolution(seat, decision);
    this.rewardFoundryComputeSpend(
      seat,
      computeBeforeAction - player.compute
    );
    await this.resolveFrontierBridge(policies, seat, decision);
    if (trade?.timing === "after") await this.settleImmediateTrade(policies, seat, trade);
    if (
      decision.actionId === "organize" &&
      player.factionId === "coalition_lab" &&
      this.round === 2 &&
      !player.roundMetrics.boardReshuffleUsed
    ) {
      const readyable = [...new Set(player.actionsUsed.filter((action) =>
        action !== "organize" && this.config.actions.some((candidate) => candidate.id === action)
      ))];
      if (readyable.length) {
        const choice = await this.choose(policies, seat, "board_reshuffle", [
          {
            decisionId: "board_reshuffle_pass",
            label: decisionLabel("keepBoard"),
            actionId: "faction"
          },
          ...readyable.map((action) => ({
            decisionId: `board_reshuffle_ready_${action}`,
            label: decisionLabel("readyAction", { action }),
            actionId: "faction",
            parameters: { action }
          }))
        ]);
        if (choice.parameters?.action) {
          const index = player.actionsUsed.indexOf(choice.parameters.action);
          player.actionsUsed.splice(index, 1);
          this.addScrutiny(player, 1);
          player.roundMetrics.boardReshuffleUsed = true;
          this.recordFactionAbility(player, "board_reshuffle", {
            coreActionsReadied: 1,
            scrutinyAdded: 1
          });
        }
      }
    }
    if (
      decision.actionId === "research" &&
      player.capability === capabilityBefore &&
      player.scrutiny > scrutinyBefore &&
      player.lastTrainingResult?.crashProtectable
    ) {
      const safety = this.players.find((candidate) =>
        candidate.factionId === "safety_laboratory" &&
        candidate.seat !== seat &&
        this.round === 2 &&
        !candidate.roundMetrics.responsibleScalingUsed &&
        candidate.safety > 0 &&
        player.runway > 0
      );
      if (safety) {
        const offer = await this.choose(policies, safety.seat, "responsible_scaling_offer", [
          {
            decisionId: "responsible_offer",
            label: decisionLabel("responsibleOffer"),
            actionId: "faction"
          },
          {
            decisionId: "responsible_decline",
            label: decisionLabel("responsibleDecline"),
            actionId: "faction"
          }
        ]);
        this.recordFactionAbility(safety, "responsible_scaling", {
          uses: 0,
          offersMade: 1
        });
        if (offer.decisionId === "responsible_offer") {
          const response = await this.choose(policies, seat, "responsible_scaling_response", [
            {
              decisionId: "responsible_accept",
              label: decisionLabel("responsibleAccept"),
              actionId: "faction"
            },
            {
              decisionId: "responsible_reject",
              label: decisionLabel("responsibleReject"),
              actionId: "faction"
            }
          ]);
          if (response.decisionId === "responsible_accept") {
            const trustBeforeSale = safety.trust;
            const replayed = simulateTrainingRun(
              this.config,
              `${this.seed}:r${this.round}:c${this.cycle}:s${seat}:training`,
              {
                deck: player.lastTrainingResult.deckSnapshot,
                stopAt: decision.parameters.stopAt,
                runway: runwayBefore,
                safety: 1
              }
            );
            player.capability = capabilityBefore;
            player.trust = trustBefore;
            player.safety = safetyBefore;
            player.runway = runwayBefore;
            player.dealFlowRunwayCredits = clone(dealFlowCreditsBefore);
            player.metrics.dealFlowConversion = clone(dealFlowConversionBefore);
            this.beginRunwayConversionContext(
              player,
              decision,
              "responsible_scaling_replay"
            );
            this.spendRunway(player, replayed.runwaySpent, {
              cause: "research_training",
              conversionEligible: true
            });
            this.spendRunway(player, 1, { cause: "responsible_scaling_payment" });
            player.scrutiny = scrutinyBefore;
            this.addResource(player, "capability", replayed.capability);
            this.addResource(player, "trust", replayed.trust);
            this.addScrutiny(player, replayed.scrutiny);
            player.lastTrainingResult = replayed;
            player.metrics.researchCapability[
              player.metrics.researchCapability.length - 1
            ] = replayed.capability;
            safety.safety -= 1;
            this.addResource(safety, "runway", 1);
            this.addResource(safety, "trust", 1);
            safety.roundMetrics.responsibleScalingUsed = true;
            this.recordFactionAbility(safety, "responsible_scaling", {
              acceptedSales: 1,
              safetySold: 1,
              runwayGained: 1,
              trustGained: safety.trust - trustBeforeSale
            });
            this.synchronizePublicMandate(player, "responsible_scaling");
            this.endRunwayConversionContext(player);
          } else {
            this.recordFactionAbility(safety, "responsible_scaling", {
              uses: 0,
              offersRejected: 1
            });
          }
        } else {
          this.recordFactionAbility(safety, "responsible_scaling", {
            uses: 0,
            offersDeclined: 1
          });
        }
      }
    }
    player.selectedAction = null;
  }

  async maybeUseOrbitalCompute(policies, seat) {
    const player = this.players[seat];
    if (
      player.factionId !== "vertical_empire" ||
      this.round < 4 ||
      player.factionAbilityUsed.orbitalCompute ||
      !player.facilities.length
    ) return false;
    const stationaryResolutionExists = this.selectedActionResolutions(seat).some(
      (decision) => {
        const piece = player.pieces.find(
          (candidate) => candidate.id === decision.parameters?.pieceId
        );
        return !decision.parameters?.pieceId ||
          decision.parameters.destinationId === piece?.tileId;
      }
    );
    if (!stationaryResolutionExists) return false;
    const decisions = [{
      decisionId: "orbital_compute_pass",
      label: decisionLabel("normalMovement"),
      actionId: "faction"
    }];
    for (const facility of player.facilities) {
      for (const tile of this.board.filter((candidate) =>
        candidate.category !== "frontier" &&
        candidate.instanceId !== facility.tileId &&
        this.tileOccupancy(candidate.instanceId) <
          (candidate.facilitySpaces ?? this.config.board.facilitySpacesPerHex)
      )) {
        decisions.push({
          decisionId: `orbital_compute_${facility.id}_${tile.instanceId}`,
          label: decisionLabel("moveFacility", {
            facility: facility.id,
            destination: tile.name
          }),
          actionId: "faction",
          parameters: { facilityId: facility.id, tileId: tile.instanceId }
        });
      }
    }
    const choice = await this.choose(policies, seat, "orbital_compute_movement", decisions);
    if (!choice.parameters?.facilityId) return false;
    const facility = player.facilities.find(
      (candidate) => candidate.id === choice.parameters.facilityId
    );
    facility.tileId = choice.parameters.tileId;
    facility.gridReady = false;
    facility.gridReadySupportSeats = [];
    facility.category = this.board.find(
      (tile) => tile.instanceId === facility.tileId
    ).category;
    const infrastructure = this.infrastructureState(player);
    const installed = this.rulesVariant.startingGridPower +
      infrastructure.connectedGenerators.reduce(
        (sum, generator) => sum + generator.capacity,
        0
      );
    if (
      infrastructure.networked.has(facility.id) &&
      installed >= 1
    ) {
      await this.produceFacility(policies, player, facility, "orbital_compute");
    }
    this.addScrutiny(player, 2);
    player.factionAbilityUsed.orbitalCompute = true;
    this.recordFactionAbility(player, "orbital_compute", {
      facilitiesMoved: 1,
      immediateProductions: Number(
        infrastructure.networked.has(facility.id) && installed >= 1
      ),
      scrutinyAdded: 2
    });
    return true;
  }

  async resolveFrontierBridge(policies, seat, decision) {
    const destination = this.board.find(
      (tile) => tile.instanceId === decision.parameters?.destinationId
    );
    if (destination?.category !== "frontier") return;
    const choice = await this.choose(policies, seat, "frontier_bridge", [
      {
        decisionId: "frontier_bridge_pass",
        label: decisionLabel("frontierBridgeDecline"),
        actionId: "frontier"
      },
      {
        decisionId: "frontier_bridge_take",
        label: decisionLabel("frontierBridgeAccept"),
        actionId: "frontier",
        consequences: { runway: 1, scrutiny: 1 }
      }
    ]);
    if (choice.decisionId === "frontier_bridge_take") {
      this.addResource(this.players[seat], "runway", 1);
      this.addScrutiny(this.players[seat], 1);
    }
  }

  async postCycle(policies, selections) {
    if (this.regime.cycle?.lawController !== null &&
      this.regime.cycle?.lawController !== undefined) {
      const controller = this.players[this.regime.cycle.lawController];
      const rivals = this.players.filter((player) =>
        player.seat !== controller.seat &&
        selections[player.seat] === this.regime.cycle.incentivizedAction
      );
      if (rivals.length >= 2) this.addResource(controller, "trust", 1);
    }
    for (const player of this.players) {
      const temporary = player.temporaryCompute || 0;
      if (!temporary) continue;
      const remaining = Math.min(
        temporary,
        Math.max(0, player.compute - (player.temporaryComputeBaseline || 0))
      );
      player.compute -= remaining;
      player.temporaryCompute = 0;
      delete player.temporaryComputeBaseline;
    }
  }

  async finishSelectedRound(policies) {
    await this.produceAll(policies);
    this.audit();
    this.scoreMandate();
    if (this.round === 3) await this.resolveRealignment(policies);
    this.recordEvent(
      "round_settled",
      null,
      renderSimulationCopy(simulationCopy.events.selectedRoundSettled, { round: this.round })
    );
    this.reportProgress("round");
    if (this.round === this.config.rounds.at(-1).number) {
      this.complete = true;
      return;
    }
    this.round += 1;
    this.cycle = 1;
    this.roundInitialized = false;
    await this.beginRound(policies);
  }

  async resolveRealignment(policies) {
    const motions = this.config.board.realignment.motions;
    const decisions = motions.map((motion) => ({
      decisionId: `realignment_${motion.id}`,
      label: `${motion.name}: ${motion.ballotText}`,
      actionId: "realignment",
      parameters: { motionId: motion.id },
      consequences: {
        innerSteps: motion.innerSteps,
        outerSteps: motion.outerSteps
      }
    }));
    decisions.push({
      decisionId: "realignment_no_ballot",
      label: decisionLabel("realignmentNoBallot"),
      actionId: "realignment",
      parameters: { motionId: null }
    });
    const choices = await this.chooseAll(
      policies,
      "realignment_ballot",
      () => decisions
    );
    const ballots = choices.map((choice, seat) => ({
      seat,
      motionId: choice.parameters.motionId
    }));
    for (const ballot of ballots) {
      if (ballot.motionId !== null) {
        increment(this.players[ballot.seat].metrics.realignmentBallots, ballot.motionId);
      }
    }
    const vote = resolveBlindRealignmentVote(
      ballots,
      this.initiativeSeat,
      motions.map((motion) => motion.id)
    );
    let motion = motions.find((candidate) => candidate.id === vote.winningMotionId);
    if (!motion) {
      const tiebreak = await this.choose(
        policies,
        this.initiativeSeat,
        "realignment_tiebreak",
        motions.filter((candidate) => vote.leadingMotionIds.includes(candidate.id)).map((candidate) => ({
          decisionId: `realignment_tiebreak_${candidate.id}`,
          label: decisionLabel("realignmentTiebreak", { motion: candidate.name }),
          actionId: "realignment",
          parameters: { motionId: candidate.id }
        }))
      );
      motion = motions.find((candidate) => candidate.id === tiebreak.parameters.motionId);
    }
    const movement = applyBoardMotion(this.board, motion);
    for (const player of this.players) {
      const networked = this.infrastructureState(player).networked;
      for (const facility of player.facilities) {
        if (!networked.has(facility.id)) {
          facility.gridReady = false;
          facility.gridReadySupportSeats = [];
        }
      }
    }
    increment(this.matchMetrics.realignments, motion.id);
    this.recordEvent(
      "realignment_resolved",
      null,
      renderSimulationCopy(simulationCopy.events.realignmentResolved, {
        motion: motion.name,
        districts: movement.movements.length,
        counts: motions
          .map((candidate) => `${candidate.id}:${vote.counts[candidate.id]}`)
          .join(", ")
      })
    );
  }

  async playCycle(policies) {
    if (!this.roundInitialized) await this.beginRound(policies);
    await this.prepareHeadline(policies);
    await this.headlineChoiceStage(policies);
    await this.preSelectionFactionPowers(policies);
    applyAgiDeclarationScenario(this);
    await this.collectNegotiationIntents(policies);

    const selectionPackets = this.players.map((player) =>
      this.packet(player.seat, "select", this.legalActionSelections(player.seat))
    );
    const results = await Promise.all(
      selectionPackets.map((packet, seat) => policies[seat].decide(packet))
    );
    const selections = [];
    for (const [seat, result] of results.entries()) {
      const player = this.players[seat];
      this.recordPolicyReceipt(player, result.receipt);
      const legal = selectionPackets[seat].legalDecisions.find(
        (decision) => decision.decisionId === result.decision.decisionId
      );
      player.selectedAction = legal.decisionId.replace(/^select_/, "");
      selections[seat] = player.selectedAction;
      this.recordEvent(
        "action_selected",
        seat,
        renderSimulationCopy(simulationCopy.events.actionSelected, {
          faction: player.factionName,
          action: player.selectedAction
        }),
        result.receipt
      );
    }

    if (this.regime.cycle?.id === "autonomous_corporation") {
      const counts = {};
      for (const action of selections.filter((value) =>
        this.config.actions.some((candidate) => candidate.id === value)
      )) increment(counts, action);
      const maximum = Math.max(0, ...Object.values(counts));
      const tied = Object.keys(counts).filter((action) => counts[action] === maximum);
      if (tied.length === 1) {
        this.regime.cycle.consensusAction = tied[0];
      } else if (tied.length > 1) {
        const choice = await this.choose(
          policies,
          this.initiativeSeat,
          "autonomous_consensus",
          tied.map((action) => ({
            decisionId: `autonomous_${action}`,
            label: decisionLabel("recognizeConsensus", { action }),
            actionId: "headline",
            parameters: { actionId: action }
          }))
        );
        this.regime.cycle.consensusAction = choice.parameters.actionId;
      }
    }

    for (const [turnInCycle, seat] of this.initiativeOrder().entries()) {
      await this.resolveSelectedSeat(policies, seat);
      this.reportProgress("turn", {
        completedSeat: seat,
        turnNumber: (this.config.rounds
          .filter((round) => round.number < this.round)
          .reduce((total, round) => total + round.cycles, 0) * this.playerCount) +
          ((this.cycle - 1) * this.playerCount) + turnInCycle + 1
      });
    }
    await this.postCycle(policies, selections);
    this.reportProgress("cycle", {
      cycleNumber: this.config.rounds
        .filter((round) => round.number < this.round)
        .reduce((total, round) => total + round.cycles, this.cycle)
    });
    this.initiativeSeat = (this.initiativeSeat + 1) % this.playerCount;
    const cycleLimit = this.config.rounds.find((round) => round.number === this.round).cycles;
    if (this.cycle === cycleLimit) await this.finishSelectedRound(policies);
    else this.cycle += 1;
  }

  async play(policies) {
    throwIfAborted(this.signal);
    await this.setup(policies);
    while (!this.complete) {
      throwIfAborted(this.signal);
      await this.playCycle(policies);
    }
    return this.result();
  }

  reportProgress(kind, details = {}) {
    if (!this.onProgress) return;
    const standings = this.players.map((player) => ({
      seat: player.seat,
      factionName: player.factionName,
      profileId: player.profileId,
      backendId: player.backendId,
      model: player.model,
      reasoningEffort: player.reasoningEffort,
      score: this.currentScore(player),
      trust: player.trust,
      customers: player.customers,
      compute: player.compute,
      capability: player.capability,
      facilities: player.facilities.length,
      agiDeclared: player.agiDeclared
    })).sort((left, right) =>
      right.score - left.score ||
      right.trust - left.trust ||
      right.customers - left.customers ||
      right.compute - left.compute ||
      left.seat - right.seat
    );
    this.onProgress({
      kind,
      round: this.round,
      cycle: this.cycle,
      ...details,
      projectedWinnerSeat: standings[0]?.seat ?? null,
      standings
    });
  }

  snapshot() {
    const base = super.snapshot();
    if (!this.rulesVariant) return base;
    return {
      ...base,
      activeHeadline: this.activeHeadline
        ? { id: this.activeHeadline.id, name: this.activeHeadline.name }
        : null,
      roundMandate: this.roundMandate?.id || null,
      systemicRisk: this.systemicRisk,
      players: base.players.map((snapshot, seat) => {
        const player = this.players[seat];
        return {
          ...snapshot,
          escalation: player.escalation,
          wildUsed: [...(player.wildUsed || [])],
          tactics: [...(player.tactics || [])],
          objectiveId: player.objectiveId,
          links: [...(player.links || [])],
          jointVentures: clone(player.jointVentures || []),
          megaClusters: clone(player.megaClusters || []),
          agiDeclared: player.agiDeclared,
          agiReadiness: this.declarationReadiness(player),
          currentScore: this.currentScore(player)
        };
      })
    };
  }

  result() {
    finalizeAgiDeclarationScenario(this);
    for (const player of this.players) {
      this.recordAgiCoreRequirements(player, "match_complete");
      player.metrics.dealFlowConversion.unspentCredits =
        player.dealFlowRunwayCredits.reduce(
          (sum, credit) => sum + credit.remaining,
          0
        );
    }
    const standings = this.players.map((player) => {
      const offlinePenalty = player.facilities.filter((facility) => !facility.powered).length;
      const score = Math.max(0, this.currentScore(player) - offlinePenalty);
      return {
        seat: player.seat,
        factionId: player.factionId,
        factionName: player.factionName,
        profileId: player.profileId,
        backendId: player.backendId,
        model: player.model,
        reasoningEffort: player.reasoningEffort,
        score,
        trust: player.trust,
        customers: player.customers,
        compute: player.compute,
        capability: player.capability,
        facilities: player.facilities.length,
        offlinePenalty,
        agiDeclared: player.agiDeclared,
        metrics: clone(player.metrics)
      };
    }).sort((left, right) =>
      right.score - left.score ||
      right.trust - left.trust ||
      right.customers - left.customers ||
      right.compute - left.compute ||
      left.seat - right.seat
    );
    const best = standings[0];
    const winnerSeats = standings.filter((entry) =>
      entry.score === best.score &&
      entry.trust === best.trust &&
      entry.customers === best.customers &&
      entry.compute === best.compute
    ).map((entry) => entry.seat);
    const setupCollectiveTrust = this.players.reduce(
      (sum, player) => sum + Number(
        this.factions.find((faction) => faction.id === player.factionId)?.starts.trust || 0
      ),
      0
    );
    const collectiveTrust = this.players.reduce((sum, player) => sum + player.trust, 0);
    const qualifyingDeclarers = this.players.filter(
      (player) => player.agiDeclared &&
        player.capability >= this.config.worldEnding.genuineAgi.declarerCapability
    ).length;
    const genuineAgi = qualifyingDeclarers >=
        this.config.worldEnding.genuineAgi.minimumQualifiedDeclarers &&
      collectiveTrust >= setupCollectiveTrust +
        this.playerCount * this.config.worldEnding.genuineAgi.collectiveTrustOffsetPerPlayer &&
      this.systemicRisk < this.playerCount;
    return {
      schemaVersion: 1,
      evidenceLabel: "simulation",
      scope: this.scope,
      seed: this.seed,
      playerCount: this.playerCount,
      rulesVariant: clone(this.rulesVariant),
      matchMetrics: clone(this.matchMetrics),
      decisionProtocol: {
        immediateTradePackets: this.immediateTradePackets,
        immediateTradePacketCeiling: this.immediateTradePacketCeiling
      },
      futureTimeline: clone(this.matchMetrics.futureTimeline),
      worldEnding: {
        id: genuineAgi ? "genuine_agi" : "closed_loop",
        name: genuineAgi
          ? this.config.worldEnding.genuineName
          : this.config.worldEnding.closedLoopName,
        qualifyingDeclarers,
        collectiveTrust,
        requiredCollectiveTrust: setupCollectiveTrust + this.playerCount,
        unresolvedSystemicRisk: this.systemicRisk
      },
      standings,
      winnerSeats,
      replay: this.recordReplay ? this.replay : undefined
    };
  }
}
