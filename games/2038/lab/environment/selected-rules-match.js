import {
  axialDistance,
  buildTrainingDeck,
  createRng,
  locallyEligibleFacilityIds,
  publicMandateAwards,
  simulateTrainingRun,
  TRAINING_DOMAINS
} from "../../web/src/engine.js";
import { canAllocateLocalPower } from "../rules/local-power-allocation.js";
import {
  applyAgiDeclarationScenario,
  finalizeAgiDeclarationScenario,
  markScenarioClaim,
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
  research: "compute"
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

export function immediateTradePacketCeiling(playerCount, {
  counteroffers = false,
  thirdPartyClaims = false
} = {}) {
  if (!Number.isInteger(playerCount) || playerCount < 2) {
    throw new RangeError("Immediate-trade packet ceiling requires at least two players.");
  }
  if (counteroffers || thirdPartyClaims) {
    throw new RangeError("The simplified trade contract forbids counteroffers and claims.");
  }
  const packetsPerResolution = 2;
  return ACTION_RESOLUTIONS_PER_PLAYER * playerCount * packetsPerResolution;
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
    escalations,
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
    this.escalationDocument = escalations;
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
    this.immediateTradePacketCeiling = immediateTradePacketCeiling(playerCount, {
      counteroffers: this.rulesVariant.immediateTradeCounteroffers,
      thirdPartyClaims: this.rulesVariant.immediateTradeThirdPartyClaims
    });
    this.contractSerial = 0;
    this.contracts = [];
    this.megaClusters = [];
    this.fusionBuiltBy = null;
    this.trainingDrawPile = buildTrainingDeck(config, `${seed}:training-deck`);
    this.trainingDiscard = [];
    this.trainingShuffle = 0;
    this.tacticDrawPile = this.rulesVariant.tacticsEnabled
      ? shuffled(
        this.tacticDocument.tactics.flatMap((card) =>
          Array.from(
            { length: this.tacticDocument.copiesPerCard || 1 },
            () => card.id
          )
        ),
        `${seed}:tactics`
      )
      : [];
    this.tacticDiscard = [];
    this.scrutinyChoicesEnabled = false;
    this.pendingScrutinyOverflow = [];
    this.roundInitialized = false;
    this.firstAgiSeat = null;
    this.agiWinnerSeat = null;
    this.matchMetrics = {
      headlines: {},
      headlineOutcomes: {},
      mandates: {},
      escalations: {},
      tactics: {},
      systemicRiskCreated: 0,
      declarations: 0,
      agiResolution: null,
      declarationReadiness: [],
      agiFunnel: this.players.map((player) => ({
        seat: player.seat,
        coreRequirementsMet: null,
        legalDeclarationWindow: null,
        claimRegistered: null,
        emergenceTriggered: null,
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
    this.roundMandate = null;
    this.headlineDecks = Object.fromEntries(
      this.config.rounds.map(({ number: round }) => [
        round,
        shuffled(
          this.headlineDocument.headlines.filter((card) => this.headlineAvailable(card, round)),
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
      const deployedAgents = Math.max(
        0,
        Math.min(config.playerSupply.agents, this.rulesVariant.startingAgentsDeployed)
      );
      player.pieces = player.pieces.filter(
        (piece) => piece.kind !== "agent" ||
          Number(piece.id.split("-").at(-1)) <= deployedAgents
      );
      player.agentsInSupply = config.playerSupply.agents - deployedAgents;
      player.programUses = 0;
      player.escalationsUsed = [];
      player.tactics = [];
      player.tacticPlayedCycleKey = null;
      player.objectiveId = null;
      player.jointVentures = [];
      player.megaClusters = [];
      player.agiDeclared = false;
      player.agiClaimed = false;
      player.agiDossier = {
        choices: {},
        revealed: false,
        fullyPaid: false,
        eligible: false,
        committedCount: 0,
        computePaid: 0,
        finalPoweredFacilities: 0,
        supportedEvidenceClaims: 0,
        claimStrength: 0
      };
      player.latestProductionSnapshot = null;
      player.factionAbilityUsed = {};
      player.tacticModifiers = {};
      player.history = {
        deployRounds: [],
        escalationRounds: [],
        cumulativeScrutiny: player.scrutiny,
        jointVenturePartners: [],
        openWeightsCapabilitySnapshot: null,
        fusionBuilt: false,
        declarations: 0
      };
      player.roundMetrics = {};
      player.metrics.headlines = {};
      player.metrics.escalations = {};
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
      player.metrics.promisesMade = 0;
      player.metrics.promisesFulfilled = 0;
      player.metrics.promisesBroken = 0;
      player.metrics.selectionAvailability = {
        resolvableNow: 0,
        tradeRequired: 0
      };
      player.metrics.requiredTradeOffers = 0;
      player.metrics.requiredTradeAcceptances = 0;
      player.metrics.requiredTradeFailures = 0;
      player.metrics.blockedAfterCommitment = 0;
      player.mandateAwards = [];
      this.synchronizePublicMandate(player, "setup");
    }
    this.replay = [];
    this.publicHistory = [];
    this.recordEvent("match_started", null, simulationCopy.events.selectedMatchStarted);
  }

  isFactionAbilityPaused(player, abilityId) {
    return !this.hasFactionAbility(player, abilityId) ||
      this.rulesVariant.pausedFactionAbilities.some((entry) =>
      entry?.factionId === player.factionId && entry?.abilityId === abilityId
    );
  }

  hasFactionAbility(player, abilityId) {
    const factionList = Array.isArray(this.factions)
      ? this.factions
      : this.factions.factions;
    const faction = factionList.find((candidate) =>
      candidate.id === player.factionId
    );
    const ability = faction?.abilities.find((candidate) => candidate.id === abilityId);
    return Boolean(
      ability &&
      this.round >= ability.round &&
      (ability.persistsAfterUnlock || this.round === ability.round)
    );
  }

  isEmergencyPauseEnabled(player) {
    return this.rulesVariant.safetyEmergencyPauseEnabled &&
      !this.isFactionAbilityPaused(player, "emergency_pause");
  }

  addResource(player, key, amount) {
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
    if (player.compute >= this.rulesVariant.agiComputePerCommit) {
      this.markAgiFunnel(player, "coreRequirementsMet", timing, {
        capability: player.capability,
        compute: player.compute
      });
    }
  }

  currentAgiRequirements() {
    return {
      computeCost: this.config.agiDossier.modules.length *
        this.rulesVariant.agiComputePerCommit
    };
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
    if (!this.scrutinyChoicesEnabled) {
      const before = player.metrics.scrutinyAdded;
      super.addScrutiny(player, amount);
      player.history.cumulativeScrutiny += player.metrics.scrutinyAdded - before;
      return;
    }
    const before = player.metrics.scrutinyAdded;
    const added = Math.min(
      Math.max(0, amount),
      this.config.playerSupply.scrutinyCubes - player.scrutiny
    );
    player.scrutiny += added;
    player.metrics.scrutinyAdded += added;
    const overflow = Math.max(0, amount - added);
    if (overflow) {
      this.pendingScrutinyOverflow.push({
        seat: player.seat,
        count: overflow,
        round: this.round,
        cycle: this.cycle
      });
    }
    player.history.cumulativeScrutiny += player.metrics.scrutinyAdded - before;
  }

  async settlePendingScrutinyOverflow(policies, stage = "scrutiny_overflow") {
    void policies;
    while (this.pendingScrutinyOverflow.length) {
      const pending = this.pendingScrutinyOverflow.shift();
      const player = this.players[pending.seat];
      for (let index = 0; index < pending.count; index += 1) {
        this.applyAutomaticPenalty(player, stage);
      }
    }
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
        researchProtection: player.researchProtection +
          Number(parameters.destinationCategory === "research")
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
          researchProtection: player.researchProtection +
            Number(parameters.destinationCategory === "research")
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

  drawTrainingCard() {
    this.prepareTrainingDrawPile();
    if (!this.trainingDrawPile.length) return null;
    return this.trainingDrawPile.shift();
  }

  scientificMethodAvailable(player) {
    if (!this.hasFactionAbility(player, "scientific_method")) return false;
    const limit = this.rulesVariant.imperialScientificMethodLifetimeLimit;
    const uses = player.factionAbilityUsed.scientificMethodUses || 0;
    const withinLimit = Number.isFinite(limit)
      ? uses < limit
      : !player.roundMetrics.scientificMethodUsed;
    return withinLimit &&
      player.runway >= this.rulesVariant.imperialScientificMethodRunwayCost;
  }

  async resolveTrainingRunWithPolicies(policies, seat, parameters) {
    const player = this.players[seat];
    const ordinaryDomains = new Set();
    const revealedCards = [];
    const revealed = [];
    let provisionalCapability = 0;
    let trust = 0;
    let scrutiny = 0;
    let researchProtectionSpent = 0;
    let outcome = "banked";
    let protection = null;
    let crashProtectable = false;

    while (true) {
      const card = this.drawTrainingCard();
      if (!card) {
        outcome = "deck-exhausted-banked";
        break;
      }
      revealedCards.push(card);
      revealed.push(card.type);
      let duplicate = false;

      if (card.kind === "domain") {
        duplicate = ordinaryDomains.has(card.type);
        if (!duplicate) {
          ordinaryDomains.add(card.type);
          provisionalCapability += 1;
        }
      } else if (card.type === "curated_corpus") {
        const missing = TRAINING_DOMAINS.filter((domain) => !ordinaryDomains.has(domain));
        if (!missing.length) duplicate = true;
        else {
          const choice = await this.choose(
            policies,
            seat,
            "training_curated_domain",
            missing.map((domain) => ({
              decisionId: `training_curated_${domain}`,
              label: decisionLabel("trainingCuratedDomain", { domain }),
              actionId: "research",
              parameters: { domain }
            }))
          );
          ordinaryDomains.add(choice.parameters.domain);
          provisionalCapability += 1;
        }
      } else if (card.type === "benchmark_leak") {
        provisionalCapability += 2;
        scrutiny += 1;
      } else if (card.type === "human_evaluation") {
        trust += 1;
        outcome = "human-evaluation-banked";
        break;
      }

      if (duplicate) {
        crashProtectable = true;
        const choices = [];
        if (player.researchProtection - researchProtectionSpent > 0) {
          choices.push({
            decisionId: "training_protect_research_protection",
            label: decisionLabel("trainingProtectResearchProtection"),
            actionId: "research",
            parameters: { protection: "research_protection" }
          });
        }
        if (crashProtectable && parameters.destinationCategory === "research") {
          choices.push({
            decisionId: "training_protect_research_visit",
            label: decisionLabel("trainingProtectResearchVisit"),
            actionId: "research",
            parameters: { protection: "research_visit" }
          });
        }
        if (crashProtectable && this.scientificMethodAvailable(player)) {
          choices.push({
            decisionId: "training_protect_scientific_method",
            label: decisionLabel("trainingProtectScientificMethod", {
              cost: this.rulesVariant.imperialScientificMethodRunwayCost
            }),
            actionId: "research",
            parameters: { protection: "scientific_method" }
          });
        }
        if (
          this.rulesVariant.tacticsEnabled &&
          player.tactics.includes("emergency_pause") &&
          player.tacticPlayedCycleKey !== `${this.round}:${this.cycle}`
        ) {
          choices.push({
            decisionId: "training_emergency_pause",
            label: decisionLabel("trainingEmergencyPause"),
            actionId: "research",
            parameters: { protection: "emergency_pause" }
          });
        }
        choices.push({
          decisionId: "training_accept_crash",
          label: decisionLabel("trainingAcceptCrash"),
          actionId: "research",
          parameters: { protection: null }
        });
        const choice = choices.length === 1
          ? choices[0]
          : await this.choose(policies, seat, "training_duplicate", choices);
        protection = choice.parameters.protection;
        if (protection === "emergency_pause") {
          provisionalCapability = 0;
          outcome = "emergency-pause";
          this.consumeTactic(player, "emergency_pause");
          player.tacticPlayedCycleKey = `${this.round}:${this.cycle}`;
        } else if (protection) {
          if (protection === "research_protection") researchProtectionSpent += 1;
          outcome = `${protection}-banked`;
        } else {
          provisionalCapability = 0;
          scrutiny += 1;
          outcome = "crashed";
        }
        break;
      }

      const choice = await this.choose(policies, seat, "training_continue", [
        {
          decisionId: "training_bank",
          label: decisionLabel("trainingBank", { capability: provisionalCapability }),
          actionId: "research",
          parameters: { continue: false }
        },
        {
          decisionId: "training_continue",
          label: decisionLabel("trainingContinue", { capability: provisionalCapability }),
          actionId: "research",
          parameters: { continue: true }
        }
      ]);
      if (!choice.parameters.continue) {
        outcome = "banked";
        break;
      }
    }

    this.trainingDiscard.push(...revealedCards);
    return {
      seed: `${this.seed}:r${this.round}:c${this.cycle}:s${seat}:training`,
      outcome,
      capability: provisionalCapability,
      trust,
      scrutiny,
      runwaySpent: 0,
      researchProtectionSpent,
      protectedDuplicate: Boolean(protection),
      protection,
      crashProtectable,
      ordinaryDomains: [...ordinaryDomains],
      ordinaryDomainCount: ordinaryDomains.size,
      distinctDomains: ordinaryDomains.size,
      revealed,
      cardsDrawn: revealed.length,
      deckExhausted: this.trainingDrawPile.length === 0,
      deckSnapshot: revealedCards.map((card) => ({ ...card }))
    };
  }

  currentScore(player) {
    return player.mandate;
  }

  factionResourceCap(player, resource) {
    const factionList = Array.isArray(this.factions)
      ? this.factions
      : this.factions.factions;
    return factionList.find((faction) => faction.id === player.factionId)
      ?.resourceCaps?.[resource] ?? this.config.resources[resource].cap;
  }

  latestPoweredFacilities(player) {
    const poweredIds = new Set(
      player.latestProductionSnapshot?.poweredFacilityIds ||
      player.facilities.filter((facility) => facility.powered).map((facility) => facility.id)
    );
    return player.facilities.filter((facility) => poweredIds.has(facility.id));
  }

  latestOfflineFacilities(player) {
    const poweredIds = new Set(this.latestPoweredFacilities(player).map((facility) => facility.id));
    return player.facilities.filter((facility) => !poweredIds.has(facility.id));
  }

  finalMandate(player) {
    const poweredFacilityMandate = this.latestPoweredFacilities(player).length *
      this.rulesVariant.finalPoweredFacilityMandate;
    const offlinePenalty = this.latestOfflineFacilities(player).length *
      this.config.scoring.finalOnly.offlineFacilityPenalty;
    return {
      score: Math.max(
        0,
        this.currentScore(player) + poweredFacilityMandate - offlinePenalty
      ),
      poweredFacilityMandate,
      offlinePenalty
    };
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
      if (tile.category === "frontier") continue;
      const scores = this.players.map((candidate) => {
        const pieces = candidate.pieces
          .filter((piece) => piece.tileId === tile.instanceId)
          .length;
        const facilities = candidate.facilities
          .filter((facility) => facility.tileId === tile.instanceId).length;
        return pieces + facilities;
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
        .length;
      return pieces +
        player.facilities.filter((item) => item.tileId === tile.instanceId).length;
    });
    const maximum = Math.max(...scores);
    if (maximum === 0 || scores.filter((score) => score === maximum).length !== 1) return null;
    return scores.indexOf(maximum);
  }

  hasPresenceAtCategory(player, category) {
    const tileIds = new Set(
      this.board.filter((tile) => tile.category === category).map((tile) => tile.instanceId)
    );
    return player.pieces.some((piece) => tileIds.has(piece.tileId)) ||
      player.facilities.some((facility) => tileIds.has(facility.tileId));
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
        programUses: player.programUses,
        escalationsUsed: [...player.escalationsUsed],
        tactics: [...player.tactics],
        objectiveId: player.objectiveId,
        agentsInSupply: player.agentsInSupply,
        jointVentures: player.jointVentures.length,
        agiDeclared: player.agiDeclared,
        agiDossier: clone(player.agiDossier),
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
          programUses: source.programUses,
          agiDeclared: source.agiDeclared,
          relationship: this.relationshipFor(seat, source.seat)
        };
      }),
      publicTable: {
        players: this.players.map((candidate) => ({
          ...this.publicPlayerState(candidate),
          programUses: candidate.programUses,
          escalationsUsed: [...candidate.escalationsUsed],
          factionAbilityUsed: this.copyPublic(candidate.factionAbilityUsed || {}),
          agentsInSupply: candidate.agentsInSupply,
          jointVentures: this.copyPublic(candidate.jointVentures),
          megaClusters: this.copyPublic(candidate.megaClusters || []),
          temporaryCompute: candidate.temporaryCompute || 0,
          agiDeclared: candidate.agiDeclared,
          dossierCardsFiled: Object.keys(candidate.agiDossier.choices).length,
          agiDossier: candidate.agiDossier.revealed
            ? clone(candidate.agiDossier)
            : undefined,
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

  async chooseAll(policies, stage, decisionsForSeat) {
    return Promise.all(this.players.map((player) =>
      this.choose(policies, player.seat, stage, decisionsForSeat(player.seat))
    ));
  }

  dealTactic(player) {
    if (!this.rulesVariant.tacticsEnabled || !this.tacticDrawPile.length) return null;
    const tacticId = this.tacticDrawPile.shift();
    player.tactics.push(tacticId);
    return tacticId;
  }

  async setup(policies) {
    this.scrutinyChoicesEnabled = true;
    if (!this.rulesVariant.tacticsEnabled) return;
    for (const player of this.players) this.dealTactic(player);
  }

  async beginRound(policies) {
    if (this.round === 4 && this.matchMetrics.round4Start === null) {
      this.matchMetrics.round4Start = this.players.map((player) => ({
        seat: player.seat,
        score: this.currentScore(player),
        profileId: player.profileId
      }));
    }
    this.roundMandate = this.mandateDeck[this.round];
    this.regime = { persistent: this.regime.persistent || {}, round: {} };
    for (const player of this.players) {
      player.actionsUsed = [];
      player.selectedAction = null;
      player.programUses = this.config.rounds[this.round - 1].programUses;
      player.researchProtection = player.factionId === "safety_laboratory" ? 2 : 1;
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
      if (this.rulesVariant.tacticsEnabled) {
        this.dealTactic(player);
        while (player.tactics.length > 3) {
          const uniqueChoices = player.tactics.map((tacticId, index) => {
            const card = this.tacticDocument.tactics.find(
              (candidate) => candidate.id === tacticId
            );
            return {
              decisionId: `tactic_discard_${index}_${tacticId}`,
              label: decisionLabel("discardTactic", { card: card?.name || tacticId }),
              actionId: "tactic",
              parameters: { index, tacticId }
            };
          });
          const choice = await this.choose(
            policies,
            player.seat,
            "tactic_hand_limit",
            uniqueChoices
          );
          const [discarded] = player.tactics.splice(choice.parameters.index, 1);
          this.tacticDiscard.push(discarded);
        }
      }
    }
    this.roundInitialized = true;
    this.recordEvent(
      "round_started",
      null,
      renderSimulationCopy(simulationCopy.events.roundStarted, {
        round: this.round,
        mandate: this.roundMandate.name
      })
    );
  }

  async preSelectionFactionPowers(policies) {
    const foundry = this.players.find((player) =>
      player.factionId === "foundry"
    );
    if (
      foundry &&
      this.hasFactionAbility(foundry, "allocation_window") &&
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
        ...(!this.regime.cycle?.computeTradeBlocked ? [{
          decisionId: "allocation_open",
          label: decisionLabel("allocationOpen"),
          actionId: "faction"
        }] : [])
      ]);
      if (activate.decisionId === "allocation_open") {
        foundry.factionAbilityUsed.allocationWindow = true;
        this.recordFactionAbility(foundry, "allocation_window");
        if (!foundry.temporaryCompute) foundry.temporaryComputeBaseline = foundry.compute;
        const computeBefore = foundry.compute;
        this.addResource(foundry, "compute", temporaryCompute);
        foundry.temporaryCompute = foundry.compute - computeBefore;
        for (let unit = 0; unit < temporaryCompute; unit += 1) {
          const buyers = this.players.filter((candidate) =>
            candidate.seat !== foundry.seat && candidate[paymentResource] >= minimumPrice
          );
          if (!buyers.length || foundry.temporaryCompute <= 0) continue;
          const offer = await this.choose(policies, foundry.seat, `allocation_window_${unit}`, [
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
      const unlocked = this.config.rounds[this.round - 1].escalations;
      const choice = await this.choose(policies, safety.seat, "emergency_pause_escalation_timing", [
        {
          decisionId: "emergency_pause_escalation_wait",
          label: decisionLabel("emergencyPauseWait"),
          actionId: "faction"
        },
        ...unlocked.map((escalationId) => ({
          decisionId: `emergency_pause_escalation_${escalationId}`,
          label: decisionLabel("pauseEscalation", { action: escalationId }),
          actionId: "faction",
          parameters: { escalationId }
        }))
      ]);
      if (choice.parameters?.escalationId) {
        const trustBefore = safety.trust;
        this.spendRunway(safety, 1, { cause: "emergency_pause" });
        this.addResource(safety, "trust", 2);
        this.regime.cycle.disabledEscalation = choice.parameters.escalationId;
        safety.factionAbilityUsed.emergencyPause = true;
        this.recordFactionAbility(safety, "emergency_pause", {
          runwaySpent: 1,
          trustGained: safety.trust - trustBefore,
          escalationsBlocked: 1
        });
      }
    }

  }

  headlineAvailable(card, round) {
    if (card.round !== round) return false;
    return true;
  }

  async prepareHeadline(policies) {
    this.activeHeadline = this.headlineDecks[this.round][this.cycle - 1];
    this.regime.cycle = { id: this.activeHeadline.id };
    const id = this.activeHeadline.id;
    if (id === "emergency_power_authority") {
      this.regime.round.emergencyPowerAuthority = true;
    }
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
    } else if (id === "weights_on_internet") {
      const minimum = Math.min(...this.players.map((player) => player.capability));
      const target = this.nearestInitiative(
        this.players.filter((player) => player.capability === minimum).map((player) => player.seat)
      );
      const maximum = Math.max(...this.players.map((player) => player.capability));
      const owner = this.nearestInitiative(
        this.players.filter((player) => player.capability === maximum).map((player) => player.seat)
      );
      const powered = this.latestPoweredFacilities(this.players[target]);
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
    } else if (id === "agi_blog_post") {
      this.regime.persistent.agiBlogPost = true;
    }

    this.recordEvent("headline_revealed", null, `${this.activeHeadline.name}: ${this.activeHeadline.text}`);
  }

  consumeTactic(player, id) {
    const index = player.tactics.indexOf(id);
    if (index >= 0) {
      player.tactics.splice(index, 1);
      this.tacticDiscard.push(id);
    }
    increment(player.metrics.tactics, id);
    increment(this.matchMetrics.tactics, id);
  }

  async maybePlayTacticForResolution(policies, seat, selectedDecision) {
    const decision = clone(selectedDecision);
    const player = this.players[seat];
    const cycleKey = `${this.round}:${this.cycle}`;
    if (
      !this.rulesVariant.tacticsEnabled ||
      player.tacticPlayedCycleKey === cycleKey
    ) return decision;

    const tacticRequired = decision.actionId === "deploy" &&
      (decision.parameters?.computeCost || 0) > player.compute;
    const usable = [...new Set(player.tactics)].filter((id) => {
      if (tacticRequired) return id === "api_price_cut";
      if (["open_letter", "emergency_pause"].includes(id)) return false;
      if (id === "cloud_partnership") return player.runway >= 1;
      if (id === "api_price_cut" || id === "model_card") {
        return decision.actionId === "deploy";
      }
      if (id === "talent_raid") {
        return player.runway >= 1 && player.agentsInSupply > 0 &&
          Boolean(decision.parameters?.destinationId);
      }
      if (id === "board_reshuffle") {
        return player.actionsUsed.some((action) =>
          ["organize", "influence"].includes(action)
        );
      }
      if (id === "weights_leak") {
        return this.players.some((candidate) =>
          candidate.seat !== seat && this.latestPoweredFacilities(candidate).length
        );
      }
      if (id === "custom_silicon") return player.facilities.length > 0;
      if (id === "government_contract") return player.trust >= 4;
      if (id === "benchmark_optimization") return decision.actionId === "research";
      return id === "interconnection_waiver";
    });
    if (!usable.length) return decision;

    const choice = await this.choose(policies, seat, "tactic_resolution", [
      ...(!tacticRequired ? [{
        decisionId: "tactic_pass",
        label: decisionLabel("skipTactic"),
        actionId: "tactic",
        parameters: { tacticId: null }
      }] : []),
      ...usable.map((id) => {
        const card = this.tacticDocument.tactics.find((candidate) => candidate.id === id);
        return {
          decisionId: `tactic_${id}`,
          label: decisionLabel("playTactic", { card: card.name, text: card.text }),
          actionId: "tactic",
          parameters: { tacticId: id }
        };
      })
    ]);
    const id = choice.parameters.tacticId;
    if (!id) return decision;

    if (id === "cloud_partnership") {
      const target = await this.choose(
        policies,
        seat,
        "tactic_cloud_partnership_target",
        this.players.filter((candidate) => candidate.seat !== seat).map((candidate) => ({
          decisionId: `tactic_cloud_partnership_${candidate.seat}`,
          label: decisionLabel("tacticChooseBeneficiary", { seat: candidate.seat + 1 }),
          actionId: "tactic",
          parameters: { targetSeat: candidate.seat }
        }))
      );
      this.spendRunway(player, 1, {
        cause: "tactic_cloud_partnership",
        conversionEligible: true
      });
      this.addResource(player, "compute", 2);
      this.addResource(this.players[target.parameters.targetSeat], "runway", 1);
    } else if (id === "api_price_cut") {
      decision.parameters.computeCost = 0;
      player.tacticModifiers.api_price_cut = true;
    } else if (id === "model_card") {
      player.tacticModifiers.model_card = true;
    } else if (id === "talent_raid") {
      this.spendRunway(player, 1, {
        cause: "tactic_talent_raid",
        conversionEligible: true
      });
      const usedNumbers = new Set(
        player.pieces.filter((piece) => piece.kind === "agent")
          .map((piece) => Number(piece.id.split("-").at(-1)))
      );
      const number = Array.from(
        { length: this.config.playerSupply.agents },
        (_, candidate) => candidate + 1
      ).find((candidate) => !usedNumbers.has(candidate));
      player.pieces.push({
        id: `s${seat}-agent-${number}`,
        kind: "agent",
        tileId: decision.parameters.destinationId
      });
      player.agentsInSupply -= 1;
    } else if (id === "board_reshuffle") {
      const readyable = [...new Set(player.actionsUsed.filter((action) =>
        ["organize", "influence"].includes(action)
      ))];
      const target = await this.choose(
        policies,
        seat,
        "tactic_board_reshuffle_target",
        readyable.map((action) => ({
          decisionId: `tactic_board_reshuffle_${action}`,
          label: decisionLabel("tacticReadyAction", { action }),
          actionId: "tactic",
          parameters: { action }
        }))
      );
      const index = player.actionsUsed.indexOf(target.parameters.action);
      if (index >= 0) player.actionsUsed.splice(index, 1);
    } else if (id === "weights_leak") {
      const targets = this.players.flatMap((candidate) =>
        candidate.seat === seat ? [] : this.latestPoweredFacilities(candidate).map((facility) => ({
          decisionId: `tactic_weights_leak_${candidate.seat}_${facility.id}`,
          label: decisionLabel("tacticChooseRivalFacility", {
            seat: candidate.seat + 1,
            facility: facility.id
          }),
          actionId: "tactic",
          parameters: { targetSeat: candidate.seat, facilityId: facility.id }
        }))
      );
      const target = await this.choose(policies, seat, "tactic_weights_leak_target", targets);
      const source = this.latestPoweredFacilities(
        this.players[target.parameters.targetSeat]
      ).find((facility) => facility.id === target.parameters.facilityId);
      await this.produceFacility(policies, player, source, "weights_leak");
    } else if (id === "custom_silicon") {
      const target = await this.choose(
        policies,
        seat,
        "tactic_custom_silicon_target",
        player.facilities.map((facility) => ({
          decisionId: `tactic_custom_silicon_${facility.id}`,
          label: decisionLabel("tacticChooseOwnFacility", { facility: facility.id }),
          actionId: "tactic",
          parameters: { facilityId: facility.id }
        }))
      );
      player.facilities.find(
        (facility) => facility.id === target.parameters.facilityId
      ).customSilicon = true;
    } else if (id === "government_contract") {
      this.addResource(player, "runway", 2);
    } else if (id === "benchmark_optimization") {
      player.tacticModifiers.benchmark_optimization = true;
    } else if (id === "interconnection_waiver") {
      this.addResource(player, "runway", 1);
      this.addResource(player, "trust", 1);
    }
    this.consumeTactic(player, id);
    player.tacticPlayedCycleKey = cycleKey;
    return decision;
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
    return this.board.filter((tile) => axialDistance(current, tile) <= 2);
  }

  legalActionSelections(seat) {
    const player = this.players[seat];
    const core = super.legalActionSelections(seat);
    const unlocked = new Set(this.config.rounds[this.round - 1].escalations);
    const escalation = this.escalationDocument.escalations
      .filter((action) => unlocked.has(action.id))
      .filter((action) => !player.escalationsUsed.includes(action.id))
      .filter((action) => action.id !== this.regime.cycle?.disabledEscalation)
      .filter((action) =>
        player.programUses > 0 ||
        (action.id === "agent_swarm" && this.regime.cycle?.id === "agent_swarm_escapes_scope")
      )
      .map((action) => {
        const availability = this.selectionAvailability(seat, action.id, {
          isEscalation: true
        });
        if (availability.status === "blocked") return null;
        return {
          decisionId: `select_escalation_${action.id}`,
          label: renderSimulationCopy(
            simulationCopy.decisions.selectAction,
            { action: action.name }
          ),
          actionId: action.id,
          consequences: {
            stage: "action_selection",
            ...availability,
            isEscalation: true,
            escalation: action.id === "agent_swarm" &&
              this.regime.cycle?.id === "agent_swarm_escapes_scope" ? 0 : -1
          }
        };
      })
      .filter(Boolean);
    return [...core, ...escalation];
  }

  selectionResolutionCount(seat, actionId, { isEscalation = false } = {}) {
    return isEscalation
      ? this.legalEscalationResolutions(seat, actionId).length
      : this.currentResolutionCountForSelection(seat, actionId);
  }

  selectionAvailability(seat, actionId, { isEscalation = false } = {}) {
    const currentResolutionCount = this.selectionResolutionCount(
      seat,
      actionId,
      { isEscalation }
    );
    return {
      currentResolutionCount,
      resolvableWithoutTrade: currentResolutionCount > 0,
      resolvableWithImmediateTrade: false,
      status: currentResolutionCount > 0 ? "resolvable_now" : "blocked"
    };
  }

  legalFactionActions(seat) {
    void seat;
    return [];
  }

  async resolveFactionAction(policies, seat, id) {
    const player = this.players[seat];
    if (id === "orbital_compute" && this.hasFactionAbility(player, id)) {
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
      const resource = RESOURCE_BY_CATEGORY[facility.category];
      if (resource) this.addResource(player, resource, resource === "compute" ? 2 : 1);
      if (facility.category === "frontier") {
        this.awardMandate(player, 1, "orbital_frontier");
        this.addScrutiny(player, 1);
      }
      this.addScrutiny(player, 2);
      player.factionAbilityUsed.orbitalCompute = true;
    } else if (id === "emergency_pause" && this.isEmergencyPauseEnabled(player)) {
      const unlocked = this.config.rounds[this.round - 1].escalations;
      const choice = await this.choose(policies, seat, "emergency_pause", unlocked.map((escalationId) => ({
        decisionId: `pause_${escalationId}`,
        label: decisionLabel("pauseEscalation", { action: escalationId }),
        actionId: "faction",
        parameters: { escalationId }
      })));
      const trustBefore = player.trust;
      this.spendRunway(player, 1, { cause: "emergency_pause" });
      this.addResource(player, "trust", 2);
      this.regime.cycle.disabledEscalation = choice.parameters.escalationId;
      player.factionAbilityUsed.emergencyPause = true;
      this.recordFactionAbility(player, "emergency_pause", {
        runwaySpent: 1,
        trustGained: player.trust - trustBefore,
        escalationsBlocked: 1
      });
    } else {
      throw new RangeError(`Unavailable faction action: ${id}.`);
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
    let decisions = super.legalResolutions(seat, actionId, {
      skipAffordability: true
    });
    const singleGeneratorRule = this.rulesVariant.singleGeneratorRule;
    if (actionId === "build" && singleGeneratorRule) {
      const ordinaryGeneratorCount = player.generators.filter(
        (generator) => generator.sourceId !== "fusion_demonstrator"
      ).length;
      decisions = decisions.flatMap((decision) => {
        if (decision.parameters?.buildMode !== "generator") return [decision];
        if (ordinaryGeneratorCount >= singleGeneratorRule.ordinaryGeneratorLimit) {
          return [];
        }
        const destination = this.board.find(
          (tile) => tile.instanceId === decision.parameters.destinationId
        );
        const location = singleGeneratorRule.locations[destination?.id];
        if (!location || decision.parameters.sourceId !== location.sourceId) return [];
        return [{
          ...decision,
          decisionId: decision.decisionId.replace(
            `build_generator_${location.sourceId}_`,
            `build_generator_${destination.id}_`
          ),
          parameters: {
            ...decision.parameters,
            generatorRuleId: singleGeneratorRule.id
          }
        }];
      });
    }
    if (actionId === "organize") {
      decisions = this.movementVariants(player, (piece, destination) => {
        const base = {
          pieceId: piece.id,
          destinationId: destination.instanceId,
          destinationCategory: destination.category
        };
        const result = [];
        if (player.agentsInSupply > 0) {
          const humanoid = this.regime.cycle?.id === "humanoid_factory_gate";
          const cost = humanoid ? 1 : Math.max(0, 2 - Number(destination.category === "talent"));
          const maximum = humanoid ? Math.min(2, player.agentsInSupply) : 1;
          if (player.runway >= cost) {
            for (let count = 1; count <= maximum; count += 1) {
              result.push({
                decisionId: `organize_recruit_${count}_${piece.id}_${destination.instanceId}`,
                label: decisionLabel("recruitAgents", {
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
        result.push({
          decisionId: `organize_redistribute_${piece.id}_${destination.instanceId}`,
          label: `${decisionLabel("reposition", {
            piece: piece.id,
            destination: destination.name
          })}; then distribute up to five adjacent movement steps`,
          actionId,
          parameters: { ...base, mode: "redistribute" },
          consequences: { mobilityOnly: true, additionalMovementSteps: 5 }
        });
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
          (
            this.hasFactionAbility(player, "installed_base") &&
            ["consumer", "media"].includes(destination.category) &&
            !player.roundMetrics.installedBaseUsed
          )
        ) computeCost = 0;
        const requirement = Math.max(1, baseRequirement - celebrityDiscount);
        if (player.capability < requirement) return [];
        return [{
          decisionId:
            `deploy_${destination.category}_${piece.id}_${destination.instanceId}`,
          label: renderSimulationCopy(simulationCopy.decisions.moveAndDeploy, {
            piece: piece.id,
            destination: destination.name,
            customer: player.customers + 1
          }),
          actionId,
          parameters: {
            pieceId: piece.id,
            destinationId: destination.instanceId,
            destinationCategory: destination.category,
            computeCost
          },
          consequences: {
            compute: -computeCost,
            customers: 1,
            scrutiny: 1
          }
        }];
      });
    }

    if (actionId === "influence" && this.round >= 3) {
      if (this.jointVentureSupplyAvailable()) decisions.push(...this.movementVariants(player, (piece, destination) => {
        if (!player.facilities.some((facility) => facility.tileId === destination.instanceId)) {
          return [];
        }
        const contractChoices = [];
        for (const rival of this.players.filter((candidate) => candidate.seat !== seat)) {
          const range = this.hasFactionAbility(player, "strategic_partnership") ? 2 : 1;
          for (const left of player.facilities.filter((facility) =>
            facility.tileId === destination.instanceId
          )) for (const right of rival.facilities) {
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
        player.facilities.some((facility) => facility.tileId === destination.instanceId)
          ? terminable.map((contract) => ({
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
          : []
      ));
    }
    if (
      actionId === "deploy" &&
      this.hasFactionAbility(player, "social_graph") &&
      !player.roundMetrics.socialGraphUsed
    ) {
      for (const tile of this.board.filter((candidate) =>
        ["consumer", "media"].includes(candidate.category) &&
        this.controller(candidate.category) === seat
      )) {
        const cost = tile.category === "consumer" ? 0 : this.rulesVariant.deployComputeCost;
        const baseRequirement = this.customerRequirement(player.customers);
        if (player.capability < baseRequirement) continue;
        decisions.push({
          decisionId: `deploy_social_graph_${tile.instanceId}`,
          label: decisionLabel("socialGraphDeploy", {
            destination: tile.name
          }),
          actionId,
          parameters: {
            destinationId: tile.instanceId,
            destinationCategory: tile.category,
            computeCost: cost,
            socialGraph: true
          },
          consequences: {
            compute: -cost,
            customers: 1,
            scrutiny: 1
          }
        });
      }
    }
    if (
      actionId === "research" &&
      this.hasFactionAbility(player, "scaling_law_breakthrough") &&
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
    return decisions
      .map((decision) => this.adjustDecision(player, decision))
      .filter((decision) =>
        decision.parameters?.actualRunwayCost === undefined ||
        decision.parameters.actualRunwayCost <= player.runway
      )
      .filter((decision) => {
        const computeCost = decision.actionId === "research"
          ? decision.parameters?.actualComputeCost ?? 1
          : decision.actionId === "deploy"
            ? decision.parameters?.computeCost ?? 0
            : 0;
        const apiPriceCutAvailable =
          this.rulesVariant.tacticsEnabled &&
          decision.actionId === "deploy" &&
          player.tactics.includes("api_price_cut") &&
          player.tacticPlayedCycleKey !== `${this.round}:${this.cycle}`;
        return computeCost <= player.compute || apiPriceCutAvailable;
      });
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
      if (
        this.hasFactionAbility(player, "installed_base") &&
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
      const destination = this.board.find(
        (tile) => tile.instanceId === result.parameters.destinationId
      );
      const singleGeneratorLocation = mode === "generator"
        ? this.rulesVariant.singleGeneratorRule?.locations[destination?.id]
        : null;
      let cost = mode === "generator"
        ? singleGeneratorLocation?.constructionCost ?? source?.runwayCost ?? 0
        : this.rulesVariant.facilityCost;
      if (category === "chip") cost -= 1;
      if (
        !singleGeneratorLocation &&
        category === "energy" &&
        mode === "generator"
      ) cost -= 1;
      if (
        !singleGeneratorLocation &&
        destination?.id === "renewable_basin" &&
        source?.id === "clean_infrastructure"
      ) cost -= 1;
      const costBeforeIndustrialVelocity = Math.max(0, cost);
      if (
        this.hasFactionAbility(player, "industrial_velocity") &&
        this.rulesVariant.verticalIndustrialVelocityBuildModes.includes(mode) &&
        !player.roundMetrics.industrialVelocityUsed
      ) cost -= this.rulesVariant.verticalIndustrialVelocityDiscount;
      result.parameters.actualRunwayCost = Math.max(0, cost);
      result.parameters.industrialVelocitySavings =
        costBeforeIndustrialVelocity - result.parameters.actualRunwayCost;
    }
    return result;
  }

  legalEscalationResolutions(seat, id) {
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
          if (
            left.id < right.id &&
            this.areAdjacent(left.tileId, right.tileId) &&
            this.megaClusterHostsAvailable([left.id, right.id]) &&
            this.megaClusterLocallyEligible(player, [left.id, right.id])
          ) {
            for (const piece of player.pieces) {
              const destinations = this.legalDestinations(player, piece);
              for (const host of [left, right].filter((candidate) =>
                destinations.some((tile) => tile.instanceId === candidate.tileId)
              )) {
                pairs.push({
                  decisionId: `escalation_mega_cluster_${left.id}_${right.id}_${piece.id}_${host.id}`,
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
      return pairs;
    }
    if (id === "reorganization") {
      return globalMoves((piece, destination) => [{
        decisionId: `escalation_reorganization_${piece.id}_${destination.instanceId}`,
        label: decisionLabel("reorganizeMove"),
        actionId: id,
        parameters: {
          pieceId: piece.id,
          destinationId: destination.instanceId
        }
      }]);
    }
    if (id === "open_weights") {
      return globalMoves((piece, destination) => [{
        decisionId: `escalation_open_weights_${piece.id}_${destination.instanceId}`,
        label: decisionLabel("openWeights"),
        actionId: id,
        parameters: { pieceId: piece.id, destinationId: destination.instanceId }
      }]);
    }
    if (id === "narrative_capture") {
      return globalMoves((piece, destination) => [
        {
          decisionId: `escalation_narrative_scrutiny_${piece.id}_${destination.instanceId}`,
          label: decisionLabel("narrativeScrutiny"),
          actionId: id,
          parameters: {
            mode: "scrutiny",
            pieceId: piece.id,
            destinationId: destination.instanceId
          }
        },
        {
          decisionId: `escalation_narrative_runway_${piece.id}_${destination.instanceId}`,
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
            `escalation_narrative_target_${rival.seat}_${piece.id}_${destination.instanceId}`,
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
          decisionId: `escalation_agent_swarm_${piece.id}_${destination.instanceId}`,
          label: simulationCopy.decisions.releaseAgentSwarm,
          actionId: id,
          parameters: { pieceId: piece.id, destinationId: destination.instanceId }
        }])
        : [];
    }
    if (id === "fusion_demonstrator") {
      if (this.fusionBuiltBy !== null) return [];
      const cost = this.config.powerSources.find(
        (source) => source.id === "fusion_demonstrator"
      ).runwayCost;
      if (player.runway < cost) return [];
      const grid = this.board.find((tile) => tile.id === "grid_reactor");
      if (this.generatorOccupancy(grid.instanceId) >= 3) return [];
      return player.pieces
        .filter((piece) => this.legalDestinations(player, piece)
          .some((tile) => tile.instanceId === grid.instanceId))
        .map((piece) => ({
          decisionId: `escalation_fusion_${piece.id}`,
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
      if (this.hasFactionAbility(player, "strategic_partnership")) {
        this.addResource(player, "runway", 1);
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
      buyer[paymentResource] < price ||
      (foundry.temporaryCompute || 0) < 1 ||
      foundry.compute < 1
    ) return false;
    if (paymentResource === "runway") {
      this.spendRunway(buyer, price, { cause: "allocation_window_purchase" });
    } else {
      buyer[paymentResource] -= price;
    }
    foundry.compute -= 1;
    foundry.temporaryCompute -= 1;
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
    if (decision.actionId === "build" && (decision.parameters?.buildMode !== undefined || !decision.consequences?.noOp) && !["facility", "generator"].includes(decision.parameters?.buildMode)) {
      throw new RangeError(`Unknown build mode: ${decision.parameters?.buildMode}`);
    }
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
      researchProtection: player.researchProtection
    };
    let scientificMethodUsedThisResolution = false;
    if (decision.actionId === "organize" && decision.parameters?.mode === "recruit") {
      this.spendRunway(player, decision.parameters.cost, {
        cause: "organize_recruit",
        conversionEligible: true
      });
      this.movePiece(player, decision.parameters);
      for (let index = 0; index < decision.parameters.count; index += 1) {
        const usedNumbers = new Set(
          player.pieces
            .filter((piece) => piece.kind === "agent")
            .map((piece) => Number(piece.id.split("-").at(-1)))
        );
        const number = Array.from(
          { length: this.config.playerSupply.agents },
          (_, candidate) => candidate + 1
        ).find((candidate) => !usedNumbers.has(candidate));
        if (!number) throw new Error(`No Agent piece remains in seat ${seat}'s supply.`);
        player.pieces.push({
          id: `s${seat}-agent-${number}`,
          kind: "agent",
          tileId: decision.parameters.destinationId
        });
        player.agentsInSupply -= 1;
      }
      if (this.regime.cycle?.id === "humanoid_factory_gate") {
        this.addScrutiny(player, decision.parameters.count);
      }
      this.markAction(player, "organize", decision.label);
      return;
    }
    if (decision.actionId === "organize" && decision.parameters?.mode === "redistribute") {
      this.movePiece(player, decision.parameters);
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
      }
      this.markAction(player, "organize", decision.label);
      return;
    }

    if (decision.actionId === "influence" &&
      ["joint_venture", "terminate_joint_venture"].includes(decision.parameters?.mode)) {
      this.movePiece(player, decision.parameters);
      const tile = this.board.find(
        (candidate) => candidate.instanceId === decision.parameters.destinationId
      );
      if (!tile) throw new Error("Influence resolution requires a board destination.");
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
      !decision.parameters?.trainingResult &&
      this.hasFactionAbility(player, "scientific_method") &&
      player.runway >= scientificMethodRunwayCost &&
      player.researchProtection === 0 &&
      decision.parameters?.destinationCategory !== "research" &&
      scientificMethodAvailable;
    const scientificProtection =
      decision.actionId === "research" &&
      (scientificMethodProtection || decision.parameters?.destinationCategory === "research");
    const resolvedScientificMethod =
      decision.parameters?.trainingResult?.protection === "scientific_method";
    const deferPublicMandate =
      (scientificMethodProtection || resolvedScientificMethod) &&
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
    if (scientificProtection) player.researchProtection += 1;
    super.applyResolution(seat, decision);
    if (scientificProtection) {
      const scientificMethodUsed =
        scientificMethodProtection &&
        player.lastTrainingResult?.researchProtectionSpent > 0;
      player.researchProtection = Math.min(
        before.researchProtection,
        player.researchProtection
      );
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
    if (resolvedScientificMethod) {
      scientificMethodUsedThisResolution = true;
      this.spendRunway(player, scientificMethodRunwayCost, {
        cause: "scientific_method",
        conversionEligible: true
      });
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
      player.factionAbilityUsed.scientificMethodUses = scientificMethodLifetimeUses + 1;
      const scrutinyAdded = this.rulesVariant.imperialScientificMethodScrutiny;
      if (scrutinyAdded > 0) this.addScrutiny(player, scrutinyAdded);
      this.recordFactionAbility(player, "scientific_method", {
        runwaySpent: scientificMethodRunwayCost,
        duplicatesProtected: 1,
        capabilityPreserved: player.lastTrainingResult?.capability || 0,
        capabilityPenalty,
        thresholdMandateWithheld: 0,
        scrutinyAdded
      });
    }

    if (decision.actionId === "fund") {
      const expected = decision.parameters.mode === "venture" ? 4 : 2;
      const actual = decision.parameters.actualRunway ?? expected;
      this.addResource(player, "runway", actual - expected);
      player.roundMetrics.fundRunway += Math.max(0, player.runway - before.runway);
      if (decision.parameters.extraScrutiny) this.addScrutiny(player, decision.parameters.extraScrutiny);
    }
    if (decision.actionId === "research") {
      const actualCost = decision.parameters.actualComputeCost ?? 1;
      player.compute += 1 - actualCost;
      const gained = player.capability - before.capability;
      const bankedOrdinaryDomains = gained > 0
        ? player.lastTrainingResult?.ordinaryDomainCount || 0
        : 0;
      if (decision.parameters.scalingLawBreakthrough) {
        const bonus = Math.min(3, bankedOrdinaryDomains);
        this.addResource(player, "capability", bonus);
        this.addScrutiny(player, 2);
        player.factionAbilityUsed.scalingLawBreakthrough = true;
        this.recordFactionAbility(player, "scaling_law_breakthrough", {
          capabilityGained: bonus,
          scrutinyAdded: 2
        });
      }
      if (this.regime.cycle?.id === "recursive_self_improvement") {
        this.addResource(player, "capability", bankedOrdinaryDomains);
      }
      if (
        this.regime.cycle?.id === "professional_exam_sweep" &&
        gained >= 3
      ) {
        this.addResource(player, "trust", 1);
        if (gained >= 5) this.removeScrutiny(player, 1);
      }
      if (this.regime.cycle?.id === "benchmark_is_economy" && gained >= 3) {
        this.awardMandate(player, 1, "benchmark_is_economy");
      }
      if (player.tacticModifiers.benchmark_optimization && gained > 0) {
        this.addResource(player, "capability", 1);
        this.addScrutiny(player, 1);
        delete player.tacticModifiers.benchmark_optimization;
      }
      player.roundMetrics.bestTrainingDomains = Math.max(
        player.roundMetrics.bestTrainingDomains,
        player.lastTrainingResult?.outcome === "crashed"
          ? 0
          : player.lastTrainingResult?.ordinaryDomainCount || 0
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
      if (
        this.hasFactionAbility(player, "industrial_velocity") &&
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
      }
    }
    if (decision.actionId === "deploy") {
      player.roundMetrics.deployed = true;
      if (!player.history.deployRounds.includes(this.round)) player.history.deployRounds.push(this.round);
      if (this.hasFactionAbility(player, "audited_deployment") &&
        !player.roundMetrics.auditedDeployUsed) {
        const scrutinyBeforeAudit = player.scrutiny;
        this.removeScrutiny(player, 1);
        player.roundMetrics.auditedDeployUsed = true;
        this.recordFactionAbility(player, "audited_deployment", {
          scrutinyRemoved: scrutinyBeforeAudit - player.scrutiny,
          deploymentsCovered: 1
        });
      }
      if (this.hasFactionAbility(player, "installed_base") &&
        ["consumer", "media"].includes(decision.parameters.destinationCategory)) {
        player.roundMetrics.installedBaseUsed = true;
      }
      if (decision.parameters.socialGraph) player.roundMetrics.socialGraphUsed = true;
      if (this.regime.cycle?.id === "ten_dollar_intelligence") this.addScrutiny(player, 1);
      if (
        this.regime.cycle?.id === "synthetic_celebrity" &&
        ["consumer", "media"].includes(decision.parameters.destinationCategory)
      ) {
        this.addScrutiny(player, 2);
        player.tacticModifiers.syntheticCelebrityUsed = true;
      }

      if (player.tacticModifiers.model_card) {
        this.removeScrutiny(player, 1);
        delete player.tacticModifiers.model_card;
      }
      if (player.tacticModifiers.api_price_cut) {
        player.roundMetrics.discountedCustomerNoIncome =
          (player.roundMetrics.discountedCustomerNoIncome || 0) + 1;
        delete player.tacticModifiers.api_price_cut;
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

  async resolveAdditionalMovement(policies, seat, {
    stage,
    steps,
    eligibleKinds = new Set(["ceo", "team"])
  }) {
    const player = this.players[seat];
    for (let step = 0; step < steps; step += 1) {
      const moves = player.pieces
        .filter((piece) => eligibleKinds.has(piece.kind))
        .flatMap((piece) => {
          const current = this.board.find((tile) => tile.instanceId === piece.tileId);
          return this.board
            .filter((tile) => axialDistance(current, tile) === 1)
            .map((tile) => ({
              decisionId: `${stage}_${step + 1}_${piece.id}_${tile.instanceId}`,
              label: decisionLabel("moveAdditionalStep", {
                piece: piece.id,
                destination: tile.name,
                remaining: steps - step - 1
              }),
              actionId: "organize",
              parameters: { pieceId: piece.id, destinationId: tile.instanceId }
            }));
        });
      const choice = await this.choose(policies, seat, `${stage}_${step + 1}`, [
        {
          decisionId: `${stage}_finish_${step + 1}`,
          label: decisionLabel("finishAdditionalMovement", {
            remaining: steps - step
          }),
          actionId: "organize",
          parameters: { finish: true }
        },
        ...moves
      ]);
      if (choice.parameters.finish) break;
      this.movePiece(player, choice.parameters);
    }
  }

  async resolveRecruitFollowUp(policies, seat) {
    const player = this.players[seat];
    const pieceChoice = await this.choose(policies, seat, "organize_recruit_follow_up", [
      {
        decisionId: "organize_recruit_move_none",
        label: decisionLabel("declineRecruitFollowUp"),
        actionId: "organize",
        parameters: { decline: true }
      },
      ...player.pieces.map((piece) => ({
        decisionId: `organize_recruit_move_${piece.id}`,
        label: decisionLabel("chooseRecruitFollowUpPiece", { piece: piece.id }),
        actionId: "organize",
        parameters: { pieceId: piece.id }
      }))
    ]);
    if (pieceChoice.parameters.decline) return;
    const pieceId = pieceChoice.parameters.pieceId;
    for (let step = 0; step < 2; step += 1) {
      const piece = player.pieces.find((candidate) => candidate.id === pieceId);
      const current = this.board.find((tile) => tile.instanceId === piece.tileId);
      const choice = await this.choose(
        policies,
        seat,
        `organize_recruit_follow_up_step_${step + 1}`,
        [
          {
            decisionId: `organize_recruit_finish_${step + 1}`,
            label: decisionLabel("finishRecruitFollowUp"),
            actionId: "organize",
            parameters: { finish: true }
          },
          ...this.board.filter((tile) => axialDistance(current, tile) === 1).map((tile) => ({
            decisionId: `organize_recruit_step_${step + 1}_${pieceId}_${tile.instanceId}`,
            label: decisionLabel("moveRecruitFollowUp", {
              piece: pieceId,
              destination: tile.name
            }),
            actionId: "organize",
            parameters: { pieceId, destinationId: tile.instanceId }
          }))
        ]
      );
      if (choice.parameters.finish) break;
      this.movePiece(player, choice.parameters);
    }
  }

  agentSubsets(player) {
    const teams = player.pieces.filter((piece) => piece.kind === "agent");
    const subsets = [];
    for (let mask = 1; mask < (1 << teams.length); mask += 1) {
      subsets.push(teams.filter((_, index) => mask & (1 << index)).map((team) => team.id));
    }
    return subsets;
  }

  async resolveEmployeeFreeFollowUp(policies, seat) {
    if (this.regime.cycle?.id !== "employee_free_unicorn") return;
    const player = this.players[seat];
    const subsets = this.agentSubsets(player);
    if (!subsets.length) return;
    const choice = await this.choose(policies, seat, "employee_free_return", [
      {
        decisionId: "employee_free_return_none",
        label: decisionLabel("returnNoAgents"),
        actionId: "organize",
        parameters: { agentIds: [] }
      },
      ...subsets.map((agentIds) => ({
        decisionId: `employee_free_return_${agentIds.join("_")}`,
        label: decisionLabel("returnNamedAgents", {
          teams: agentIds.join(", "),
          runway: agentIds.length * 2
        }),
        actionId: "organize",
        parameters: { agentIds }
      }))
    ]);
    const returned = new Set(choice.parameters.agentIds);
    if (!returned.size) return;
    player.pieces = player.pieces.filter((piece) => !returned.has(piece.id));
    player.agentsInSupply += returned.size;
    this.addResource(player, "runway", returned.size * 2);
    this.addScrutiny(player, 2);
  }

  async applyResolutionWithPolicies(policies, seat, selectedDecision) {
    const decision = clone(selectedDecision);
    if (decision.actionId === "research" && !decision.consequences?.noOp) {
      decision.parameters ||= {};
      decision.parameters.trainingResult = await this.resolveTrainingRunWithPolicies(
        policies,
        seat,
        decision.parameters
      );
    }
    this.applyResolution(seat, decision);
    if (decision.actionId === "organize" && !decision.consequences?.noOp) {
      if (decision.parameters?.mode === "recruit") {
        await this.resolveRecruitFollowUp(policies, seat);
      } else if (decision.parameters?.mode === "redistribute") {
        await this.resolveAdditionalMovement(policies, seat, {
          stage: "organize_redistribute",
          steps: 5
        });
      }
      await this.resolveEmployeeFreeFollowUp(policies, seat);
    }
    await this.settlePendingScrutinyOverflow(policies, "action_scrutiny_overflow");
    return decision;
  }

  rewardFoundryComputeSpend(spenderSeat, spentCompute) {
    if (spentCompute < 2) return;
    for (const foundry of this.players.filter((candidate) =>
      this.hasFactionAbility(candidate, "the_shovels") &&
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

  provisionalWinnerSeats() {
    const standings = this.players.map((player) => ({
      seat: player.seat,
      score: this.finalMandate(player).score,
      trust: player.trust,
      customers: player.customers,
      compute: player.compute
    })).sort((left, right) =>
      right.score - left.score ||
      right.trust - left.trust ||
      right.customers - left.customers ||
      right.compute - left.compute ||
      left.seat - right.seat
    );
    const best = standings[0];
    return standings.filter((entry) =>
      entry.score === best.score &&
      entry.trust === best.trust &&
      entry.customers === best.customers &&
      entry.compute === best.compute
    ).map((entry) => entry.seat);
  }

  declarationReadiness(player) {
    const dossier = player.agiDossier;
    const committedCount = Object.values(dossier?.choices || {})
      .filter((choice) => choice === "commit").length;
    const publicationCommitted = dossier?.choices?.publication_claim === "commit";
    return {
      ready: publicationCommitted && player.compute >=
        committedCount * this.rulesVariant.agiComputePerCommit,
      failingRequirement: publicationCommitted
        ? (player.compute >= committedCount * this.rulesVariant.agiComputePerCommit
          ? null
          : "compute")
        : "publication",
      committedCount,
      publicationCommitted,
      fullyPaid: Boolean(dossier?.fullyPaid),
      eligible: Boolean(dossier?.eligible)
    };
  }

  isAgiEligible(player) {
    if (player.agiDossier?.revealed) return Boolean(player.agiDossier.eligible);
    return this.declarationReadiness(player).ready;
  }

  agiDossierDecisionAssessment(player, module, orientation) {
    const choices = player.agiDossier?.choices || {};
    const committedBefore = Object.entries(choices)
      .filter(([moduleId, choice]) =>
        moduleId !== module.id && choice === "commit"
      ).length;
    const projectedCommittedCount = committedBefore + Number(orientation === "commit");
    const projectedComputeCost = projectedCommittedCount *
      this.rulesVariant.agiComputePerCommit;
    const evidenceModules = this.config.agiDossier.modules
      .filter((candidate) => candidate.metric !== "publication");
    const evidenceValue = (candidate) => {
      if (candidate.metric === "capability") return player.capability;
      if (candidate.metric === "poweredFacilities") {
        return this.latestPoweredFacilities(player).length;
      }
      if (candidate.metric === "trust") return player.trust;
      return 0;
    };
    const supportedCommittedEvidenceClaims = evidenceModules.filter((candidate) =>
      choices[candidate.id] === "commit" &&
      evidenceValue(candidate) >= candidate.threshold
    ).length;
    const publication = module.metric === "publication";
    const currentEvidenceValue = publication
      ? supportedCommittedEvidenceClaims
      : evidenceValue(module);
    const currentEvidenceThreshold = publication
      ? this.rulesVariant.agiMinimumSupportedEvidenceClaims
      : module.threshold;
    return {
      moduleId: module.id,
      metric: module.metric,
      orientation,
      currentEvidenceValue,
      currentEvidenceThreshold,
      supportedNow: currentEvidenceValue >= currentEvidenceThreshold,
      supportedCommittedEvidenceClaims,
      minimumSupportedEvidenceClaims:
        this.rulesVariant.agiMinimumSupportedEvidenceClaims,
      committedBefore,
      projectedCommittedCount,
      projectedComputeCost,
      currentCompute: player.compute,
      canPayProjectedCost: player.compute >= projectedComputeCost
    };
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

  async fileAgiDossiers(policies) {
    const module = this.config.agiDossier.modules.find(
      (candidate) => candidate.round === this.round
    );
    if (!module) throw new Error(`Missing AGI Dossier module for Era ${this.round}.`);
    const choices = await Promise.all(this.players.map((player) => {
      const legalDecisions = [
        {
          decisionId: `agi_dossier_commit_${module.id}`,
          label: `Commit the ${module.id.replaceAll("_", " ")} Dossier.`,
          actionId: "agi_dossier",
          parameters: {
            moduleId: module.id,
            orientation: "commit",
            dossierAssessment: this.agiDossierDecisionAssessment(
              player,
              module,
              "commit"
            )
          },
          consequences: { agiClaim: 1, compute: -1, scrutiny: 1 }
        },
        {
          decisionId: `agi_dossier_hedge_${module.id}`,
          label: `Hedge the ${module.id.replaceAll("_", " ")} Dossier.`,
          actionId: "agi_dossier",
          parameters: {
            moduleId: module.id,
            orientation: "hedge",
            dossierAssessment: this.agiDossierDecisionAssessment(
              player,
              module,
              "hedge"
            )
          },
          consequences: { agiClaim: 0 }
        }
      ];
      const scenarioOrientation = this.scenario?.applied &&
        this.scenario.focalSeat === player.seat
        ? player.agiDossier.choices[module.id]
        : null;
      return this.choose(
        policies,
        player.seat,
        `agi_dossier_${module.id}`,
        scenarioOrientation
          ? legalDecisions.filter((decision) =>
            decision.parameters.orientation === scenarioOrientation
          )
          : legalDecisions
      );
    }));
    for (const [seat, choice] of choices.entries()) {
      this.players[seat].agiDossier.choices[module.id] = choice.parameters.orientation;
    }
    this.recordEvent(
      "agi_dossiers_filed",
      null,
      `Every institution filed its Era ${this.round} AGI Dossier card.`
    );
    if (this.round === this.config.rounds.at(-1).number) this.revealAgiDossiers();
  }

  revealAgiDossiers() {
    for (const player of this.players) {
      const dossier = player.agiDossier;
      dossier.revealed = true;
      dossier.finalPoweredFacilities = this.latestPoweredFacilities(player).length;
      dossier.committedCount = Object.values(dossier.choices)
        .filter((choice) => choice === "commit").length;
      const computeCost = dossier.committedCount * this.rulesVariant.agiComputePerCommit;
      if (this.scenario?.applied && this.scenario.focalSeat === player.seat) {
        player.compute = this.scenario.arm === "eligible"
          ? Math.max(player.compute, computeCost)
          : Math.min(player.compute, Math.max(0, computeCost - 1));
      }
      dossier.computePaid = Math.min(player.compute, computeCost);
      player.compute -= dossier.computePaid;
      dossier.fullyPaid = dossier.computePaid === computeCost;
      dossier.eligible = dossier.fullyPaid &&
        dossier.choices.publication_claim === "commit";
      player.agiClaimed = dossier.eligible;
      this.recordEligibility(player, "dossier_reveal");
      this.addScrutiny(
        player,
        dossier.committedCount * this.rulesVariant.agiScrutinyPerCommit
      );
      if (dossier.eligible) {
        this.markAgiFunnel(player, "legalDeclarationWindow", "dossier_reveal", {
          computeCost,
          committedCount: dossier.committedCount
        });
        markScenarioClaim(this, player);
        this.markAgiFunnel(player, "claimRegistered", "dossier_reveal", {
          computeSpent: dossier.computePaid,
          committedCount: dossier.committedCount
        });
      }
      this.matchMetrics.declarationReadiness.push({
        seat: player.seat,
        round: this.round,
        cycle: this.cycle,
        ready: dossier.eligible,
        failingRequirement: dossier.eligible
          ? null
          : (dossier.choices.publication_claim === "commit" ? "compute" : "publication"),
        committedCount: dossier.committedCount,
        computeCost,
        computePaid: dossier.computePaid,
        supportingSeats: []
      });
      this.recordEvent(
        "agi_dossier_revealed",
        player.seat,
        `${player.factionName} revealed ${dossier.committedCount} commitments; ` +
          `${dossier.eligible ? "the claim is eligible" : "the claim is ineligible"}.`
      );
    }
  }

  agiClaimStrengths() {
    const publicationStrength = this.regime.persistent?.agiBlogPost ? 2 : 1;
    const thresholds = this.config.agiDossier.claimResolution.capabilityThresholds;
    const minimumEvidence = this.rulesVariant.agiMinimumSupportedEvidenceClaims;
    return this.players.filter((player) => player.agiDossier.eligible).flatMap((player) => {
      const dossier = player.agiDossier;
      const supportedEvidence = {
        benchmark: Number(
          dossier.choices.benchmark_claim === "commit" &&
          player.capability >= this.config.agiDossier.modules
            .find((module) => module.id === "benchmark_claim").threshold
        ),
        deployment: Number(
          dossier.choices.deployment_claim === "commit" &&
          dossier.finalPoweredFacilities >= this.config.agiDossier.modules
            .find((module) => module.id === "deployment_claim").threshold
        ),
        authority: Number(
          dossier.choices.authority_claim === "commit" &&
          player.trust >= this.config.agiDossier.modules
            .find((module) => module.id === "authority_claim").threshold
        )
      };
      const supportedEvidenceClaims = Object.values(supportedEvidence)
        .reduce((sum, value) => sum + value, 0);
      const capabilityStrength = thresholds
        .filter((threshold) => player.capability >= threshold).length;
      const strength = publicationStrength + supportedEvidenceClaims + capabilityStrength;
      dossier.supportedEvidenceClaims = supportedEvidenceClaims;
      dossier.claimStrength = strength;
      player.agiClaimed = supportedEvidenceClaims >= minimumEvidence;
      if (!player.agiClaimed) return [];
      return [{
        seat: player.seat,
        mandate: this.finalMandate(player).score,
        committedCount: dossier.committedCount,
        publicationStrength,
        supportedEvidence,
        supportedEvidenceClaims,
        capabilityStrength,
        strength
      }];
    });
  }

  resolveAgiOutcome() {
    const initiativeRank = new Map(
      this.initiativeOrder().map((seat, index) => [seat, index])
    );
    const strengths = this.agiClaimStrengths().sort((left, right) =>
      right.strength - left.strength ||
      right.mandate - left.mandate ||
      this.players[right.seat].trust - this.players[left.seat].trust ||
      this.players[right.seat].customers - this.players[left.seat].customers ||
      this.players[right.seat].compute - this.players[left.seat].compute ||
      initiativeRank.get(left.seat) - initiativeRank.get(right.seat)
    );
    const resolution = {
      method: "highest-supported-claim",
      claimantSeats: strengths.map((entry) => entry.seat),
      provisionalWinnerSeats: this.provisionalWinnerSeats(),
      strengths,
      selectedSeat: null,
      winnerOverridden: false,
      emerged: false
    };
    if (!strengths.length) {
      this.matchMetrics.agiResolution = resolution;
      return;
    }
    const selected = strengths[0];
    const player = this.players[selected.seat];
    player.agiDeclared = true;
    this.firstAgiSeat = player.seat;
    this.agiWinnerSeat = player.seat;
    player.history.declarations += 1;
    this.matchMetrics.declarations = 1;
    this.markAgiFunnel(player, "emergenceTriggered", "final_agi_resolution", {
      claimStrength: selected.strength
    });
    this.markAgiFunnel(player, "declared", "final_agi_resolution", {
      mandate: selected.mandate,
      claimStrength: selected.strength,
      supportedEvidenceClaims: selected.supportedEvidenceClaims
    });
    markScenarioDeclaration(this, player);

    resolution.selectedSeat = player.seat;
    resolution.winnerOverridden = !resolution.provisionalWinnerSeats.includes(
      player.seat
    );
    resolution.emerged = true;
    this.matchMetrics.agiResolution = resolution;
    this.recordEvent(
      "agi_declared",
      player.seat,
      `${player.factionName} formed the strongest supported AGI claim.`
    );
  }

  async applyEscalation(policies, seat, id, decision) {
    const player = this.players[seat];
    if (
      id === "mega_cluster" &&
      this.megaClusters.length >= this.config.sharedSupply.megaClusterPairs
    ) return;
    if (id === "fusion_demonstrator" && this.fusionBuiltBy !== null) return;
    if (id === "mega_cluster" && !this.megaClusterDecisionLocallyEligible(
      seat,
      decision.parameters
    )) return;
    this.commitEscalationSelection(player, id);
    this.beginRunwayConversionContext(player, decision, "escalation");
    this.movePiece(player, decision.parameters || {});

    if (id === "mega_cluster") {
      if (player.runway >= 3 && player.compute >= 2) {
        this.spendRunway(player, 3, {
          cause: "mega_cluster",
          conversionEligible: true
        });
        player.compute -= 2;
        const cluster = {
          id: `mega-${this.megaClusters.length + 1}`,
          leadSeat: seat,
          leftId: decision.parameters.leftId,
          rightId: decision.parameters.rightId,
          powered: false
        };
        this.megaClusters.push(cluster);
        player.megaClusters.push(cluster);
        this.addScrutiny(player, 2);
      }
    } else if (id === "reorganization") {
      for (const team of player.pieces.filter((piece) => piece.kind === "agent")) {
        const current = this.board.find((tile) => tile.instanceId === team.tileId);
        const choice = await this.choose(
          policies,
          seat,
          `reorganization_move_${team.id}`,
          this.board.filter((tile) => axialDistance(current, tile) <= 1).map((tile) => ({
            decisionId: `reorganization_${team.id}_${tile.instanceId}`,
            label: decisionLabel("reorganizationAgentDestination", {
              team: team.id,
              destination: tile.name
            }),
            actionId: id,
            parameters: { teamId: team.id, destinationId: tile.instanceId }
          }))
        );
        team.tileId = choice.parameters.destinationId;
      }
      const teams = player.pieces.filter((piece) => piece.kind === "agent");
      if (teams.length) {
        const choice = await this.choose(policies, seat, "reorganization_return", [
          {
            decisionId: "reorganization_return_none",
            label: decisionLabel("reorganizationReturnNone"),
            actionId: id,
            parameters: { teamId: null }
          },
          ...teams.map((team) => ({
            decisionId: `reorganization_return_${team.id}`,
            label: decisionLabel("reorganizationReturnNamed", { team: team.id }),
            actionId: id,
            parameters: { teamId: team.id }
          }))
        ]);
        if (choice.parameters.teamId) {
          player.pieces = player.pieces.filter(
            (piece) => piece.id !== choice.parameters.teamId
          );
          player.agentsInSupply += 1;
          this.addResource(player, "runway", 3);
          this.addScrutiny(player, 1);
        }
      }
    } else if (id === "open_weights") {
      player.history.openWeightsCapabilitySnapshot = this.players.map((candidate) => candidate.capability);
      for (const candidate of this.players) this.addResource(candidate, "capability", 1);
      this.addResource(player, "trust", 2);
      this.removeScrutiny(player, 1);
    } else if (id === "narrative_capture") {
      if (decision.parameters.mode === "scrutiny") this.removeScrutiny(player, 2);
      else if (decision.parameters.mode === "runway") this.addResource(player, "runway", 2);
      else this.addScrutiny(this.players[decision.parameters.targetSeat], 1);
    } else if (id === "agent_swarm") {
      const swarmDestination = decision.parameters.destinationId;
      const swarmPiece = decision.parameters.pieceId;
      for (let index = 0; index < 2; index += 1) {
        const swarmResolutions = (actionId) => {
          let resolutions = this.legalResolutions(seat, actionId)
            .filter((candidate) =>
              candidate.parameters?.destinationId === swarmDestination &&
              candidate.parameters?.pieceId === swarmPiece
            );
          if (index === 1) {
            resolutions = resolutions
              .map((candidate) =>
                this.suppressAgentSwarmDestinationBonus(player, candidate)
              )
              .filter(Boolean);
          }
          return resolutions;
        };
        const selections = this.config.actions
          .filter((action) => !player.actionsUsed.includes(action.id))
          .map((action) => {
            const currentResolutionCount = swarmResolutions(action.id).length;
            return {
              decisionId: `agent_select_${action.id}`,
              label: decisionLabel("agentSwarmSelects", { action: action.name }),
              actionId: action.id,
              parameters: { actionId: action.id },
              consequences: {
                stage: "action_selection",
                currentResolutionCount,
                resolvableWithoutTrade: currentResolutionCount > 0
              }
            };
          })
          .filter((selection) => selection.consequences.currentResolutionCount > 0);
        if (!selections.length) break;
        const selection = await this.choose(policies, seat, `agent_swarm_${index + 1}`, selections);
        const legal = swarmResolutions(selection.parameters.actionId);
        const resolution = clone(
          await this.choose(policies, seat, `agent_resolve_${index + 1}`, legal)
        );
        const computeBeforeSubaction = player.compute;
        await this.applyResolutionWithPolicies(policies, seat, resolution);
        this.rewardFoundryComputeSpend(
          seat,
          computeBeforeSubaction - player.compute
        );
      }
      this.addScrutiny(
        player,
        this.regime.cycle?.id === "agent_swarm_escapes_scope" ? 4 : 3
      );
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
      this.fusionBuiltBy = seat;
      this.addScrutiny(player, 3);
    }
    this.recordEligibility(player, "after_escalation");
    this.recordEvent(
      "escalation_resolved",
      seat,
      renderSimulationCopy(simulationCopy.events.resolved, {
        faction: player.factionName,
        result: id
      })
    );
    this.endRunwayConversionContext(player);
  }

  infrastructureState(player) {
    const locallyEligible = locallyEligibleFacilityIds(this.board, {
      ...player,
      startingGridConnection: {
        assignedFacilityId: player.facilities[0]?.id || null
      }
    });
    const connectedGenerators = player.generators.filter((generator) => {
      const generatorTile = this.board.find((tile) => tile.instanceId === generator.tileId);
      return player.facilities.some((facility) => {
        if (!locallyEligible.has(facility.id)) return false;
        const facilityTile = this.board.find((tile) => tile.instanceId === facility.tileId);
        return generatorTile && facilityTile && axialDistance(generatorTile, facilityTile) <= 1;
      });
    });
    return { locallyEligible, connectedGenerators };
  }

  megaClusterLocallyEligible(player, facilityIds) {
    const state = this.infrastructureState(player);
    if (facilityIds.some((facilityId) => !player.facilities.some((facility) =>
      facility.id === facilityId
    ))) return false;

    return canAllocateLocalPower({
      board: this.board,
      player,
      selectedFacilityIds: facilityIds,
      connectedGenerators: state.connectedGenerators,
      startingGridPower: player.facilities[0] && state.locallyEligible.has(player.facilities[0].id)
        ? this.rulesVariant.startingGridPower
        : 0,
      supplementalPower: 0,
    });
  }

  megaClusterHostsAvailable(facilityIds) {
    const requested = new Set(facilityIds);
    if (requested.size !== facilityIds.length) return false;
    return this.megaClusters.every((cluster) =>
      !requested.has(cluster.leftId) && !requested.has(cluster.rightId)
    );
  }

  megaClusterDecisionLocallyEligible(seat, parameters = {}) {
    const player = this.players[seat];
    if (!player || !parameters.leftId || !parameters.rightId) return false;
    if (!this.megaClusterHostsAvailable([parameters.leftId, parameters.rightId])) {
      return false;
    }
    return this.megaClusterLocallyEligible(player, [parameters.leftId, parameters.rightId]);
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
    const countsForProduction = stage === "facility_production";
    if (facility.category === "cloud") {
      this.addResource(player, "compute", 2);
      if (countsForProduction) player.roundMetrics.computeProduced += 2;
    } else if (facility.category === "research") {
      this.addResource(player, "compute", 1);
      if (countsForProduction) player.roundMetrics.computeProduced += 1;
    } else if (facility.category === "consumer") {
      this.addResource(player, "runway", 1);
    } else if (facility.category === "chip") {
      this.addResource(player, "compute", 1);
      this.addResource(player, "runway", 1);
      if (countsForProduction) player.roundMetrics.computeProduced += 1;
    } else if (facility.category === "capital") {
      this.addResource(player, "runway", 2);
    } else if (facility.category === "talent") {
      const decisions = [{
        decisionId: `${stage}_talent_stay`,
        label: decisionLabel("declineTalentMovement"),
        actionId: "production"
      }];
      for (const team of player.pieces.filter((piece) => piece.kind === "agent")) {
        const current = this.board.find((tile) => tile.instanceId === team.tileId);
        for (const destination of this.board.filter(
          (tile) => axialDistance(current, tile) === 1
        )) {
          decisions.push({
            decisionId: `${stage}_talent_${team.id}_${destination.instanceId}`,
            label: decisionLabel("moveTalentAgent", {
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
      this.addResource(player, "trust", 1);
    } else if (facility.category === "energy") {
      const tile = this.board.find((candidate) => candidate.instanceId === facility.tileId);
      if (tile?.id === "grid_reactor") {
        this.addResource(player, "compute", 1);
        if (countsForProduction) player.roundMetrics.computeProduced += 1;
      } else {
        this.removeScrutiny(player, 1);
      }
    }
    if (facility.customSilicon) {
      this.addResource(player, "compute", 1);
      if (countsForProduction) player.roundMetrics.computeProduced += 1;
    }
  }

  commitEscalationSelection(player, id) {
    if (player.escalationsUsed.includes(id)) return;
    const tokenFree = id === "agent_swarm" &&
      this.regime.cycle?.id === "agent_swarm_escapes_scope";
    if (!tokenFree) player.programUses -= 1;
    player.escalationsUsed.push(id);
    if (!player.history.escalationRounds.includes(this.round)) {
      player.history.escalationRounds.push(this.round);
    }
    increment(player.metrics.escalations, id);
    increment(this.matchMetrics.escalations, id);
  }

  async produceAll(policies) {
    const infrastructure = this.players.map((player) => this.infrastructureState(player));
    const generation = this.players.map(() => ({
      starter: 0,
      generated: 0,
    }));

    for (const player of this.players) {
      const state = infrastructure[player.seat];
      generation[player.seat].starter = player.facilities[0] &&
        state.locallyEligible.has(player.facilities[0].id)
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
      }

      this.recordAgiCoreRequirements(player, "production_started");
    }
    await this.settlePendingScrutinyOverflow(
      policies,
      "production_generation_scrutiny_overflow"
    );

    // Headline-granted supplemental Power is chosen in the Allocate box, after
    // installed generation is public.
    if (this.regime.round?.emergencyPowerAuthority) {
      for (const seat of this.initiativeOrder()) {
        const choice = await this.choose(
          policies,
          seat,
          "production_emergency_power",
          [0, 1, 2].map((power) => ({
            decisionId: `production_emergency_power_${power}`,
            label: decisionLabel("authorizeEmergencyPower", { power }),
            actionId: "production",
            parameters: { power }
          }))
        );
        const player = this.players[seat];
        const power = choice.parameters.power;
        player.roundMetrics.emergencyPower = power;
        generation[seat].generated += power;
        this.addScrutiny(player, power);
        if (power === 2) {
          this.systemicRisk += 1;
          this.matchMetrics.systemicRiskCreated += 1;
        }
      }
      await this.settlePendingScrutinyOverflow(
        policies,
        "production_supplemental_power_scrutiny_overflow"
      );
    }

    for (const player of this.players) {
      const state = infrastructure[player.seat];
      const available =
        generation[player.seat].starter +
        generation[player.seat].generated;
      const eligible = player.facilities.filter((facility) => state.locallyEligible.has(facility.id));
      const projectContributions = this.megaClusters.flatMap((cluster) => {
        if (cluster.leadSeat === player.seat) {
          return [{
            clusterId: cluster.id,
            demand: 2,
            hostIds: [cluster.leftId, cluster.rightId],
            additionalDemandHostIds: [cluster.leftId, cluster.rightId]
          }];
        }
        return [];
      });
      const subsets = [];
      for (let facilityMask = 0; facilityMask < 2 ** eligible.length; facilityMask += 1) {
        const selected = eligible.filter((_, index) => facilityMask & (1 << index));
        const selectedIds = selected.map((facility) => facility.id);
        const selectedSet = new Set(selectedIds);
        for (
          let projectMask = 0;
          projectMask < 2 ** projectContributions.length;
          projectMask += 1
        ) {
          const projects = projectContributions.filter(
            (_, index) => projectMask & (1 << index)
          );
          if (projects.some((project) =>
            project.hostIds.some((hostId) => !selectedSet.has(hostId))
          )) continue;
          const additionalFacilityDemandIds = projects.flatMap(
            (project) => project.additionalDemandHostIds
          );
          const demand = selected.length + projects.reduce(
            (sum, project) => sum + project.demand,
            0
          );
          const installedGeneratorPower = state.connectedGenerators.reduce(
            (sum, generator) => sum + generator.capacity,
            0
          );
          const candidateAllocationValid = !this.rulesVariant.singleGeneratorRule ||
            canAllocateLocalPower({
              board: this.board,
              player,
              selectedFacilityIds: selectedIds,
              connectedGenerators: state.connectedGenerators,
              startingGridPower: generation[player.seat].starter,

              supplementalPower: Math.max(
                0,
                generation[player.seat].generated - installedGeneratorPower
              ),
              additionalFacilityDemandIds
            });
          if (demand <= available && candidateAllocationValid) {
            subsets.push({ selected, projects, demand });
          }
        }
      }
      const decisions = subsets.map(({ selected, projects, demand }) => {
        const projectIds = projects.map((project) => project.clusterId);
        return {
          decisionId:
            `power_${selected.map((facility) => facility.id).join("_") || "none"}_` +
            `projects_${projectIds.join("_") || "none"}`,
          label: decisionLabel("allocatePower", {
            facilities: selected.map((facility) => facility.id).join(", ") || "none",
            projects: projectIds.join(", ") || "none",
            demand,
            available
          }),
          actionId: "production",
          parameters: {
            facilityIds: selected.map((facility) => facility.id),
            projectIds,
            demand
          },
          consequences: {
            poweredFacilities: selected.length,
            poweredProjects: projectIds.length,
            powerDemand: demand
          }
        };
      });
      const allocation = await this.choose(
        policies,
        player.seat,
        "power_allocation",
        decisions
      );
      const poweredIds = new Set(allocation.parameters.facilityIds);
      for (const facility of player.facilities) facility.powered = poweredIds.has(facility.id);
      player.roundMetrics.poweredProjectIds = allocation.parameters.projectIds;
      player.roundMetrics.powerDemandSatisfied = allocation.parameters.demand;
      player.roundMetrics.availablePower = available;
    }

    for (const cluster of this.megaClusters) {
      const lead = this.players[cluster.leadSeat];
      const left = lead.facilities.find((facility) => facility.id === cluster.leftId);
      const right = lead.facilities.find((facility) => facility.id === cluster.rightId);
      const leadCommitted = lead.roundMetrics.poweredProjectIds?.includes(cluster.id);
      cluster.powered = Boolean(
        left && right && left.powered && right.powered &&
        this.areAdjacent(left.tileId, right.tileId) &&
        leadCommitted
      );
    }

    // Produce box: Facilities for every player, then Customer income, then
    // active Mega-Clusters. Initiative orders each sub-step.
    for (const seat of this.initiativeOrder()) {
      const player = this.players[seat];
      for (const facility of player.facilities.filter((candidate) => candidate.powered)) {
        await this.produceFacility(policies, player, facility);
      }
    }

    for (const seat of this.initiativeOrder()) {
      const player = this.players[seat];
      let customerIncome = Math.max(
        0,
        player.customers - (player.roundMetrics.discountedCustomerNoIncome || 0)
      );

      this.addResource(player, "runway", customerIncome);
    }

    const initiativeRank = new Map(
      this.initiativeOrder().map((seat, index) => [seat, index])
    );
    for (const cluster of [...this.megaClusters].sort((left, right) =>
      initiativeRank.get(left.leadSeat) - initiativeRank.get(right.leadSeat) ||
      left.id.localeCompare(right.id)
    )) {
      if (!cluster.powered) continue;
      const lead = this.players[cluster.leadSeat];
      this.addResource(lead, "compute", 3);
      lead.roundMetrics.computeProduced += 3;
    }

    // Partner box: Joint Ventures always resolve after all Produce sub-steps.
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
        (candidate) => this.hasFactionAbility(candidate, "strategic_partnership")
      ) ? 2 : 1;
      if (!left?.powered || !right?.powered) continue;
      const leftTile = this.board.find((tile) => tile.instanceId === left.tileId);
      const rightTile = this.board.find((tile) => tile.instanceId === right.tileId);
      if (axialDistance(leftTile, rightTile) > range) continue;
      const leftResource = this.facilityContractResource(right);
      const rightResource = this.facilityContractResource(left);
      if (leftResource) {
        this.addResource(leftPlayer, leftResource, 1);
        if (leftResource === "compute") leftPlayer.roundMetrics.computeProduced += 1;
      }
      if (rightResource) {
        this.addResource(rightPlayer, rightResource, 1);
        if (rightResource === "compute") rightPlayer.roundMetrics.computeProduced += 1;
      }
      if (contract.createdRound === this.round) {
        leftPlayer.roundMetrics.activeNewJointVentures =
          (leftPlayer.roundMetrics.activeNewJointVentures || 0) + 1;
        rightPlayer.roundMetrics.activeNewJointVentures =
          (rightPlayer.roundMetrics.activeNewJointVentures || 0) + 1;
      }
    }

    await this.settlePendingScrutinyOverflow(
      policies,
      "production_scrutiny_overflow"
    );

    for (const player of this.players) {
      const poweredFacilityIds = player.facilities
        .filter((facility) => facility.powered)
        .map((facility) => facility.id);
      const powered = poweredFacilityIds.length;
      player.latestProductionSnapshot = {
        round: this.round,
        poweredFacilityIds,
        offlineFacilityIds: player.facilities
          .filter((facility) => !poweredFacilityIds.includes(facility.id))
          .map((facility) => facility.id),
        powerSupply: player.roundMetrics.availablePower,
        powerDemandSatisfied: player.roundMetrics.powerDemandSatisfied
      };
      player.metrics.poweredFacilityRounds.push({
        round: this.round,
        powered,
        facilities: player.facilities.length,
        supply: player.roundMetrics.availablePower,
        demandSatisfied: player.roundMetrics.powerDemandSatisfied,
        locallyEligible: infrastructure[player.seat].locallyEligible.size
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
        poweredFacilities: player.latestProductionSnapshot.poweredFacilityIds.length
      })),
      platformLead: platform ? this.currentScore(platform) - leader : null,
      gridGeneratorSlotsFilled: this.generatorOccupancy(
        this.board.find((tile) => tile.id === "grid_reactor").instanceId
      )
    });
    for (const player of this.players) {
      for (const facility of player.facilities) facility.powered = false;
    }
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

  applyAutomaticPenalty(player, cause) {
    if (player.runway > 0) this.spendRunway(player, 1, { cause });
    else if (player.trust > 0) this.addResource(player, "trust", -1);
  }

  async audit(policies) {
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
        for (const seat of this.initiativeOrder()) {
          const player = this.players[seat];
          if (player.customers < 3) continue;
          this.applyAutomaticPenalty(player, "systemic_audit");
          player.metrics.systemicRiskHits += 1;
        }
      } else {
        const player = this.players[selected.seat];
        player.scrutiny -= 1;
        player.metrics.auditHits += 1;
        this.applyAutomaticPenalty(player, "player_audit");
      }
    }
  }

  scoreMandate() {
    const id = this.roundMandate.id;
    const values = this.players.map((player) => {
      if (id === "quarter_humanity_notices") return player.capability - player.roundMetrics.capabilityStart;
      if (id === "continent_signs_loi") return player.customers - player.roundMetrics.customersStart;
      if (id === "building_has_weather") return this.latestPoweredFacilities(player).length;
      if (id === "stack_reaches_horizon") return player.roundMetrics.powerDemandSatisfied || 0;
      if (id === "voluntary_coordination_triumphs") return player.roundMetrics.activeNewJointVentures || 0;
      if (id === "legibility_offensive") return player.roundMetrics.deployed ? player.trust : -1;
      if (id === "national_champion_without_nationalization") return this.controlledCategories(player).size;
      if (id === "model_ate_tuesday") return player.roundMetrics.bestTrainingDomains;
      if (id === "compute_new_weather") return player.roundMetrics.computeProduced;
      if (id === "zero_incident_quarter") {
        const added = player.metrics.scrutinyAdded - player.roundMetrics.scrutinyStart;
        return -added;
      }
      if (id === "responsible_acceleration") return player.trust >= 4 ? player.capability : -1;
      if (id === "markets_prefer_destiny") return player.roundMetrics.fundRunway;
      return 0;
    });
    const minimum = this.roundMandate.minimumQualification ?? 1;
    const qualificationValues = id === "zero_incident_quarter"
      ? this.players.map((player) =>
        player.metrics.scrutinyAdded - player.roundMetrics.scrutinyStart
      )
      : values;
    const qualifiedValues = values.map((value, index) =>
      qualificationValues[index] >= minimum ? value : -Infinity
    );
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
    const powered = this.latestPoweredFacilities(player).length;
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
      return player.facilities.length >= 3 && player.generators.length >= 1;
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
    if (id === "regulatory_moat") {
      return player.trust >= 4 && this.controller("government") === player.seat;
    }
    if (id === "recursive_revenue") {
      return player.customers > 0 && player.facilities.length > 0 &&
        player.jointVentures.length > 0;
    }
    if (id === "credible_denial") return player.capability >= 8 && player.customers <= 1;
    if (id === "history_will_call") return player.history.cumulativeScrutiny >= 6 && player.trust >= 4;
    if (id === "fusion_press_cycle") return player.history.fusionBuilt && player.agiDeclared;
    if (id === "perfectly_normal_quarter") return player.history.escalationRounds.length >= 2;
    return false;
  }

  tradableResources(player, receiver, excluded = null) {
    const exportControl = this.regime.cycle?.id === "export_controls";
    return ["runway", "compute"].filter((resource) =>
      resource !== excluded &&
      !(exportControl && resource === "compute") &&
      player[resource] > 0 &&
      receiver[resource] < (
        this.factionResourceCap(receiver, resource)
      )
    );
  }

  selectedActionResolutions(seat) {
    const player = this.players[seat];
    if (!player.selectedAction) return [];
    if (player.selectedAction.startsWith("escalation_")) {
      return this.legalEscalationResolutions(seat, player.selectedAction.slice(11));
    }
    if (player.selectedAction.startsWith("faction_")) return [];
    return this.legalResolutions(seat, player.selectedAction);
  }

  immediateTradeGiveAmounts(seat, partner, resource) {
    const player = this.players[seat];
    const partnerCap = this.factionResourceCap(partner, resource);
    const maximumGive = Math.min(player[resource], partnerCap - partner[resource]);
    return maximumGive >= 1 ? [1] : [];
  }

  immediateTradeReceiveAmounts(seat, partner, resource) {
    const player = this.players[seat];
    const playerCap = this.factionResourceCap(player, resource);
    const maximumReceive = Math.min(partner[resource], playerCap - player[resource]);
    return maximumReceive >= 1 ? [1] : [];
  }

  dealFlowEligibleTrade(offer) {
    return offer.giveResource !== offer.receiveResource;
  }

  provisionalTradeResolvesSelection(seat, offer, actionId, {
    isEscalation = false
  } = {}) {
    const player = this.players[seat];
    const partner = this.players[offer.partnerSeat];
    const snapshots = [player, partner].map((participant) => ({
      participant,
      runway: participant.runway,
      compute: participant.compute
    }));
    player[offer.giveResource] -= offer.giveAmount;
    partner[offer.giveResource] += offer.giveAmount;
    partner[offer.receiveResource] -= offer.receiveAmount;
    player[offer.receiveResource] += offer.receiveAmount;
    if (
      this.dealFlowEligibleTrade(offer) &&
      player.factionId === "coalition_lab" &&
      !this.isFactionAbilityPaused(player, "deal_flow") &&
      !player.roundMetrics?.dealFlowUsed
    ) {
      player.runway = Math.min(
        this.config.resources.runway.cap,
        player.runway + 1
      );
    }
    const resolves = this.selectionResolutionCount(
      seat,
      actionId,
      { isEscalation }
    ) > 0;
    for (const snapshot of snapshots) {
      snapshot.participant.runway = snapshot.runway;
      snapshot.participant.compute = snapshot.compute;
    }
    return resolves;
  }

  immediateTradeOffers(seat, timing) {
    const player = this.players[seat];
    const offers = [];
    for (const partner of this.players.filter((candidate) => candidate.seat !== seat)) {
      const giveResources = this.tradableResources(player, partner).filter(
        (resource) => this.immediateTradeGiveAmounts(seat, partner, resource).length > 0
      );
      for (const giveResource of giveResources) {
        for (const giveAmount of this.immediateTradeGiveAmounts(seat, partner, giveResource)) {
          const receiveResources = this.tradableResources(partner, player).filter(
            (resource) => this.immediateTradeReceiveAmounts(seat, partner, resource).length > 0
          );
          for (const receiveResource of receiveResources) {
            if (receiveResource === giveResource) continue;
            for (const receiveAmount of this.immediateTradeReceiveAmounts(
              seat,
              partner,
              receiveResource
            )) {
              offers.push({
                timing,
                partnerSeat: partner.seat,
                targetSeat: partner.seat,
                giveResource,
                giveAmount,
                receiveResource,
                receiveAmount
              });
            }
          }
        }
      }
    }
    return offers;
  }

  canResolveSelectionAfterImmediateTrade(seat, actionId, options = {}) {
    return this.immediateTradeOffers(seat, "before").some((offer) =>
      this.provisionalTradeResolvesSelection(seat, offer, actionId, options)
    );
  }

  immediateTradeDecisions(seat, timing = "before") {
    if (timing !== "before") {
      throw new RangeError("Immediate trades occur only before action resolution.");
    }
    const player = this.players[seat];
    const selectedAction = player.selectedAction;
    const selectedEscalation = selectedAction?.startsWith("escalation_");
    const selectedActionId = selectedEscalation
      ? selectedAction.slice("escalation_".length)
      : selectedAction;
    const selectedCurrentlyResolvable = selectedAction
      ? this.selectedActionResolutions(seat).length > 0
      : true;
    const offers = this.immediateTradeOffers(seat, timing).filter((offer) =>
      !selectedActionId ||
      this.provisionalTradeResolvesSelection(seat, offer, selectedActionId, {
        isEscalation: selectedEscalation
      })
    );
    const decisions = [{
      decisionId: "trade_none",
      label: decisionLabel("tradeNone"),
      actionId: "trade",
      consequences: {
        timing,
        selectedActionCurrentlyResolvable: selectedCurrentlyResolvable
      }
    }];
    for (const offer of offers) {
      decisions.push({
        decisionId: [
          "trade_offer",
          timing,
          offer.partnerSeat,
          offer.giveResource,
          offer.giveAmount,
          offer.receiveResource,
          offer.receiveAmount
        ].join("_"),
        label: decisionLabel("tradeOffer", {
          timing: decisionLabel("tradeTimingBefore"),
          giveAmount: offer.giveAmount,
          giveResource: offer.giveResource,
          partner: this.players[offer.partnerSeat].factionName,
          receiveAmount: offer.receiveAmount,
          receiveResource: offer.receiveResource
        }),
        actionId: "trade",
        parameters: offer,
        consequences: {
          timing,
          enablesSelectedAction: !selectedCurrentlyResolvable
        }
      });
    }
    return decisions;
  }

  async chooseImmediateTrade(policies, seat, timing) {
    const decisions = this.immediateTradeDecisions(seat, timing);
    if (decisions.length === 1) return null;
    const choice = await this.choose(
      policies,
      seat,
      `immediate_trade_${timing}`,
      decisions
    );
    return choice.parameters?.partnerSeat === undefined ? null : choice.parameters;
  }

  canCompleteImmediateTrade(seat, partnerSeat, offer) {
    const partner = this.players[partnerSeat];
    const allowedResources = new Set(["runway", "compute"]);
    if (
      !partner ||
      offer?.timing !== "before" ||
      !allowedResources.has(offer.giveResource) ||
      !allowedResources.has(offer.receiveResource) ||
      offer.giveResource === offer.receiveResource ||
      offer.giveAmount !== 1 ||
      offer.receiveAmount !== 1
    ) return false;
    const resourcesAvailable = this.immediateTradeGiveAmounts(
      seat,
      partner,
      offer.giveResource
    ).includes(
      offer.giveAmount
    ) && this.immediateTradeReceiveAmounts(seat, partner, offer.receiveResource).includes(
      offer.receiveAmount
    );
    if (!resourcesAvailable) return false;
    const selectedAction = this.players[seat].selectedAction;
    if (!selectedAction) return resourcesAvailable;
    const isEscalation = selectedAction.startsWith("escalation_");
    const actionId = isEscalation
      ? selectedAction.slice("escalation_".length)
      : selectedAction;
    return this.provisionalTradeResolvesSelection(seat, offer, actionId, {
      isEscalation
    });
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
        this.dealFlowEligibleTrade(offer) &&
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
    const response = await this.choose(policies, partner.seat, "immediate_trade_response", [
      {
        decisionId: "trade_reject",
        label: decisionLabel("tradeReject", offer),
        actionId: "trade",
        parameters: {
          ...offer,
          partnerSeat: seat,
          targetSeat: seat,
          tradePerspective: "responder"
        }
      },
      {
        decisionId: "trade_accept",
        label: decisionLabel("tradeAccept", offer),
        actionId: "trade",
        parameters: {
          ...offer,
          partnerSeat: seat,
          targetSeat: seat,
          tradePerspective: "responder"
        }
      }
    ]);
    if (response.decisionId === "trade_accept") {
      return this.completeImmediateTrade(seat, partner.seat, offer);
    }
    return false;
  }

  async resolveSelectedSeat(policies, seat) {
    const player = this.players[seat];
    const beforeTrade = await this.chooseImmediateTrade(policies, seat, "before");
    const beforeTradeAccepted = beforeTrade
      ? await this.settleImmediateTrade(policies, seat, beforeTrade)
      : false;
    void beforeTradeAccepted;
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
    if (player.selectedAction.startsWith("escalation_")) {
      const id = player.selectedAction.slice(11);
      let legal = this.legalEscalationResolutions(seat, id);
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
        player.metrics.forcedNoOps += 1;
        player.metrics.blockedAfterCommitment += 1;
        this.recordEvent(
          "escalation_blocked",
          seat,
          renderSimulationCopy(simulationCopy.events.escalationBlocked, {
            faction: player.factionName,
            action: id
          })
        );
        player.selectedAction = null;
        return;
      }
      let decision = await this.choose(policies, seat, `resolve_escalation_${id}`, legal);
      decision = await this.maybePlayTacticForResolution(policies, seat, decision);
      const computeBeforeAction = player.compute;
      await this.applyEscalation(policies, seat, id, decision);
      if (id !== "agent_swarm") {
        this.rewardFoundryComputeSpend(
          seat,
          computeBeforeAction - player.compute
        );
      }
      await this.resolveFrontierBridge(policies, seat, decision);
      player.selectedAction = null;
      return;
    }
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
      player.metrics.blockedAfterCommitment += 1;
      legal = [{
        decisionId: `forced_noop_${player.selectedAction}`,
        label: decisionLabel("noLegalResolution", { action: player.selectedAction }),
        actionId: player.selectedAction,
        parameters: {},
        consequences: { noOp: true }
      }];
    }
    let decision = await this.choose(policies, seat, "resolve", legal);
    decision = await this.maybePlayTacticForResolution(policies, seat, decision);
    if (decision.parameters?.mode === "joint_venture") {
      await this.negotiate(policies, seat, decision);
    }
    const computeBeforeAction = player.compute;
    await this.applyResolutionWithPolicies(policies, seat, decision);
    this.rewardFoundryComputeSpend(
      seat,
      computeBeforeAction - player.compute
    );
    await this.resolveFrontierBridge(policies, seat, decision);
    player.selectedAction = null;
  }

  async maybeUseOrbitalCompute(policies, seat) {
    const player = this.players[seat];
    if (
      !this.hasFactionAbility(player, "orbital_compute") ||
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
      infrastructure.locallyEligible.has(facility.id) &&
      installed >= 1
    ) {
      await this.produceFacility(policies, player, facility, "orbital_compute");
    }
    this.addScrutiny(player, 2);
    player.factionAbilityUsed.orbitalCompute = true;
    this.recordFactionAbility(player, "orbital_compute", {
      facilitiesMoved: 1,
      immediateProductions: Number(
        infrastructure.locallyEligible.has(facility.id) && installed >= 1
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
      if (rivals.length >= Math.ceil((this.playerCount - 1) / 2)) {
        this.addResource(controller, "trust", 1);
      }
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
    await this.fileAgiDossiers(policies);
    await this.settlePendingScrutinyOverflow(policies, "dossier_scrutiny_overflow");
    await this.audit(policies);
    this.scoreMandate();

    if (this.round === this.config.rounds.at(-1).number) {
      this.resolveAgiOutcome();
    }
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

  async playCycle(policies) {
    if (!this.roundInitialized) await this.beginRound(policies);
    await this.prepareHeadline(policies);
    await this.settlePendingScrutinyOverflow(policies, "headline_scrutiny_overflow");
    await this.settlePendingScrutinyOverflow(policies, "headline_choice_scrutiny_overflow");
    await this.preSelectionFactionPowers(policies);
    await this.settlePendingScrutinyOverflow(policies, "faction_scrutiny_overflow");
    applyAgiDeclarationScenario(this);

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
      player.metrics.selectionAvailability.resolvableNow += 1;
      if (player.selectedAction.startsWith("escalation_")) {
        this.commitEscalationSelection(
          player,
          player.selectedAction.slice("escalation_".length)
        );
      }
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
      await this.settlePendingScrutinyOverflow(policies, "turn_scrutiny_overflow");
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
        ? {
          id: this.activeHeadline.id,
          name: this.activeHeadline.name,
          newswire: this.activeHeadline.newswire,
          text: this.activeHeadline.text,
          quote: this.activeHeadline.quote
        }
        : null,
      roundMandate: this.roundMandate?.id || null,
      fusionBuiltBy: this.fusionBuiltBy,
      systemicRisk: this.systemicRisk,
      players: base.players.map((snapshot, seat) => {
        const player = this.players[seat];
        return {
          ...snapshot,
          programUses: player.programUses,
          escalationsUsed: [...(player.escalationsUsed || [])],
          tactics: [...(player.tactics || [])],
          objectiveId: player.objectiveId,
          jointVentures: clone(player.jointVentures || []),
          megaClusters: clone(player.megaClusters || []),
          agiDeclared: player.agiDeclared,
          agiClaimed: player.agiClaimed,
          agiDossier: clone(player.agiDossier),
          latestProductionSnapshot: clone(player.latestProductionSnapshot),
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
      const {
        score,
        poweredFacilityMandate,
        offlinePenalty
      } = this.finalMandate(player);
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
        poweredFacilityMandate,
        offlinePenalty,
        agiDeclared: player.agiDeclared,
        agiClaimed: player.agiClaimed,
        agiDossier: clone(player.agiDossier),
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
    const winnerSeats = this.agiWinnerSeat === null
      ? standings.filter((entry) =>
        entry.score === best.score &&
        entry.trust === best.trust &&
        entry.customers === best.customers &&
        entry.compute === best.compute
      ).map((entry) => entry.seat)
      : [this.agiWinnerSeat];
    const setupCollectiveTrust = this.players.reduce(
      (sum, player) => sum + Number(
        this.factions.find((faction) => faction.id === player.factionId)?.starts.trust || 0
      ),
      0
    );
    const collectiveTrust = this.players.reduce((sum, player) => sum + player.trust, 0);
    const qualifyingDeclarers = this.players.filter(
      (player) => player.agiDeclared
    ).length;
    const agiEmerges = qualifyingDeclarers >=
        this.config.worldEnding.agiEmergence.minimumFormations;
    const requiredCollectiveTrust = setupCollectiveTrust +
      this.playerCount * this.config.worldEnding.openContinuity.collectiveTrustOffsetPerPlayer;
    const systemicRiskBounded = !this.config.worldEnding.openContinuity
      .systemicRiskMustBeBelowPlayerCount || this.systemicRisk < this.playerCount;
    const openContinuity = collectiveTrust >= requiredCollectiveTrust && systemicRiskBounded;
    const outcomeId = agiEmerges
      ? (openContinuity ? "singularity" : "closed_loop")
      : (openContinuity ? "plural_future" : "assured_continuity");
    const outcomeNames = this.config.worldEnding.outcomes;
    const outcomeName = {
      singularity: outcomeNames.singularity,
      closed_loop: outcomeNames.closedLoop,
      plural_future: outcomeNames.pluralFuture,
      assured_continuity: outcomeNames.assuredContinuity
    }[outcomeId];
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
        id: outcomeId,
        name: outcomeName,
        agiEmerges,
        openContinuity,
        qualifyingDeclarers,
        collectiveTrust,
        requiredCollectiveTrust,
        unresolvedSystemicRisk: this.systemicRisk,
        systemicRiskExclusiveCeiling: this.playerCount
      },
      standings,
      winnerSeats,
      replay: this.recordReplay ? this.replay : undefined
    };
  }
}
