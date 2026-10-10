import {
  createRng,
  shuffle,
  generateBoard,
  buildTrainingDeck,
  TRAINING_DOMAINS,
} from "../../web/src/engine.js";
import { resolvePlayerKits } from "../rules/player-kits.js";
import { effectiveRulesVariant } from "./rules-variant.js";
import { validateDecisionResponse } from "../contracts/decision-contract.js";
import {
  evaluateEraMandate,
  finalObjectiveStandings,
  activeJointVenture,
  facilityContractResource,
  controlledAreas,
} from "../rules/era-mandates.js";
import { throwIfAborted } from "../cancellation.js";
const clone = (value) => structuredClone(value);
const increment = (target, key, n = 1) => {
  target[key] = (target[key] || 0) + n;
};
export const SELECTED_RULES_COVERAGE = {
  id: "six-area-four-track-v1",
  verdictBoundary:
    "Six-area four-track prototype; implementation evidence only.",
  automated: [
    "Six Core Actions",
    "Shared Training deck",
    "Limited Facility spaces and one upgrade",
    "Customer cards",
    "Bilateral trades and fixed-host Ventures",
    "Final-state scoring",
  ],
  excluded: [
    "Balance promotion",
    "Human usability",
    "Manufacturing qualification",
  ],
};
export function immediateTradePacketCeiling(count, options = {}) {
  if (
    !Number.isInteger(count) ||
    count < 2 ||
    options.counteroffers ||
    options.thirdPartyClaims
  )
    throw new RangeError("Only one bilateral fixed-rate offer is permitted.");
  return count * 12 * 2;
}
const choice = (
  decisionId,
  label,
  actionId,
  parameters = {},
  consequences = {},
) => ({ decisionId, label, actionId, parameters, consequences });
function metrics() {
  return {
    actions: {},
    openingActions: [],
    projects: {},
    mandatesWon: {},
    policyProviders: {},
    policyReceipts: [],
    policyFallbacks: 0,
    forcedNoOps: 0,
    auditHits: 0,
    reputationReviewHits: 0,
    researchCapability: [],
    poweredFacilityRounds: [],
    earliestAgiEligibility: null,
    shovelsIncome: 0,
    factionAbilityValues: {},
    selectionAvailability: { resolvableNow: 0, tradeRequired: 0 },
    requiredTradeOffers: 0,
    requiredTradeAcceptances: 0,
    requiredTradeFailures: 0,
    blockedAfterCommitment: 0,
    mandateEvents: [],
    promisesMade: 0,
    promisesFulfilled: 0,
    promisesBroken: 0,
  };
}
export class SelectedRulesMatch {
  constructor({
    config,
    factions,
    profiles,
    kitAssignments,
    backends = [],
    models = [],
    reasoningEfforts = [],
    headlines = { headlines: [] },
    projects = {},
    mandates = { mandates: [] },
    seed = "mandate",
    playerCount = 4,
    recordReplay = false,
    projection = "rich",
    rulesVariant = {},
    mandateMode = "variable",
    decisionContext = null,
    onProgress = null,
    signal,
    scenario = null,
  }) {
    if (!config.players.playableCounts.includes(playerCount))
      throw new RangeError("playerCount must be 2–5.");
    if (scenario)
      throw new RangeError(
        "Historical AGI interventions are unavailable in the redesigned game.",
      );
    if (
      !["rich", "batch"].includes(projection) ||
      !["fixed", "variable"].includes(mandateMode)
    )
      throw new RangeError("Invalid projection or objective ordering.");
    this.config = config;
    this.factions = factions;
    this.seed = String(seed);
    this.playerCount = playerCount;
    this.board = generateBoard(config);
    this.rulesVariant = effectiveRulesVariant(config, rulesVariant);
    this.projection = projection;
    this.recordReplay = recordReplay;
    this.decisionContext = decisionContext;
    this.publicMatchId = decisionContext?.publicMatchId || "mandate-2038";
    this.onProgress = onProgress;
    this.signal = signal;
    this.scope = SELECTED_RULES_COVERAGE;
    this.headlineDocument = headlines;
    this.projectDocument = projects;
    this.mandateDocument = mandates;
    this.mandateMode = mandateMode;
    this.round = 1;
    this.cycle = 1;
    this.initiativeSeat = 0;
    this.complete = false;
    this.roundInitialized = false;
    this.decisionSerial = 0;
    this.contractSerial = 0;
    this.contracts = [];
    this.revealedMandates = [];
    this.replay = [];
    this.publicHistory = [];
    this.pendingJointVenture = null;
    this.immediateTradePackets = 0;
    this.immediateTradePacketCeiling = immediateTradePacketCeiling(playerCount);
    this.trainingDrawPile = buildTrainingDeck(config, `${seed}:training:0`);
    this.trainingDiscard = [];
    this.trainingShuffle = 0;
    this.matchMetrics = {
      headlines: {},
      headlineOutcomes: {},
      mandates: {},
      projects: {},
      declarations: 0,
      agiFunnel: [],
      trades: { offers: 0, accepted: 0, refused: 0 },
      productionSnapshots: [],
      projectProduction: [],
      futureTimeline: [],
      eraMandateScores: [],
      agiResolution: null,
    };
    const kits = resolvePlayerKits(config, playerCount, kitAssignments);
    this.players = Array.from({ length: playerCount }, (_, seat) => {
      const faction = factions[seat % factions.length];
      const p = {
        seat,
        kitId: kits[seat].id,
        playerCount,
        factionId: faction.id,
        factionName: faction.name,
        profileId: profiles[seat % profiles.length].id,
        backendId: backends[seat % Math.max(1, backends.length)] || "weighted",
        model: models[seat % Math.max(1, models.length)] || null,
        reasoningEffort:
          reasoningEfforts[seat % Math.max(1, reasoningEfforts.length)] || null,
        runway: faction.starts.runway,
        compute: faction.starts.compute,
        capability: faction.starts.capability,
        reputation: faction.starts.reputation,
        customerCards: Array.from(
          { length: faction.starts.customers || 0 },
          (_, i) => ({ id: `s${seat}-customer-${i + 1}`, ordinal: i + 1 }),
        ),
        pieces: Array.from(
          { length: this.rulesVariant.startingAgentsDeployed },
          (_, i) => ({
            id: `s${seat}-agent-${i + 1}`,
            kind: "agent",
            tileId: null,
          }),
        ),
        facilities: [],
        actionsUsed: [],
        selectedAction: null,
        agiDeclared: false,
        agentsInSupply:
          config.playerSupply.agents - this.rulesVariant.startingAgentsDeployed,
        metrics: metrics(),
      };
      Object.defineProperty(p, "customers", {
        get() {
          return this.customerCards.length;
        },
        enumerable: true,
      });
      return p;
    });
    this.recordEvent("match_started", null, "Six shared areas; four tracks.");
  }
  hasFactionAbility(player, id) {
    return (
      this.factions
        .find((f) => f.id === player.factionId)
        ?.abilities.some((a) => a.id === id) &&
      !this.rulesVariant.pausedFactionAbilities.some(
        (a) => a.factionId === player.factionId && a.abilityId === id,
      )
    );
  }
  addResource(player, key, amount) {
    const d = this.config.resources[key];
    if (!d || !Number.isFinite(amount))
      throw new TypeError(`Invalid resource: ${key}`);
    const before = player[key];
    player[key] = Math.max(d.min, Math.min(d.cap, before + amount));
    return player[key] - before;
  }
  spendRunway(player, amount) {
    if (!Number.isInteger(amount) || amount < 0 || player.runway < amount)
      throw new RangeError("Insufficient Runway.");
    player.runway -= amount;
    return amount;
  }
  gainCustomer(player) {
    if (player.customers >= this.config.customerCards.perPlayer) return false;
    player.customerCards.push({
      id: `s${player.seat}-customer-${player.customers + 1}`,
      ordinal: player.customers + 1,
    });
    return true;
  }
  canDeploy(player) {
    return (
      player.customers < this.config.customerCards.perPlayer &&
      player.capability >=
        this.config.customerCards.requirements[player.customers]
    );
  }
  tileOccupancy(id) {
    return this.players.reduce(
      (n, p) => n + p.facilities.filter((f) => f.tileId === id).length,
      0,
    );
  }
  initiativeOrder() {
    return Array.from(
      { length: this.playerCount },
      (_, i) => (this.initiativeSeat + i) % this.playerCount,
    );
  }
  publicPlayerState(p) {
    return clone({
      seat: p.seat,
      kitId: p.kitId,
      factionId: p.factionId,
      factionName: p.factionName,
      runway: p.runway,
      compute: p.compute,
      capability: p.capability,
      reputation: p.reputation,
      customerCards: p.customerCards,
      customers: p.customers,
      actionsUsed: p.actionsUsed,
      pieces: p.pieces,
      facilities: p.facilities,
      agentsInSupply: p.agentsInSupply,
      agiDeclared: p.agiDeclared,
    });
  }
  publicBoardState() {
    return this.board.map((a) => ({
      ...clone(a),
      tileId: a.instanceId,
      facilitySpacesOpen: a.facilitySpaces - this.tileOccupancy(a.instanceId),
      components: this.players.flatMap((p) => [
        ...p.pieces
          .filter((x) => x.tileId === a.instanceId)
          .map((x) => ({ type: "piece", ownerSeat: p.seat, ...clone(x) })),
        ...p.facilities
          .filter((x) => x.tileId === a.instanceId)
          .map((x) => ({ type: "facility", ownerSeat: p.seat, ...clone(x) })),
      ]),
    }));
  }
  currentEraObjective(p) {
    return this.roundMandate
      ? {
          id: this.roundMandate.id,
          metric: this.roundMandate.metric,
          ...evaluateEraMandate(this.roundMandate, this, p),
        }
      : null;
  }
  publicObservation(seat) {
    const p = this.players[seat];
    return {
      round: this.round,
      cycle: this.cycle,
      initiativeSeat: this.initiativeSeat,
      activeHeadline: this.activeHeadline ? clone(this.activeHeadline) : null,
      roundMandate: this.roundMandate ? clone(this.roundMandate) : null,
      revealedMandates: clone(this.revealedMandates),
      self: {
        ...this.publicPlayerState(p),
        facilities: p.facilities.length,
        jointVentures: this.contracts.filter((c) =>
          [c.left.seat, c.right.seat].includes(seat),
        ).length,
        canDeploy: this.canDeploy(p),
        agiReadiness: this.declarationReadiness(p),
        currentEraObjective: this.currentEraObjective(p),
      },
      opponents: this.players
        .filter((x) => x.seat !== seat)
        .map((x) => ({
          ...this.publicPlayerState(x),
          facilities: x.facilities.length,
        })),
      board: this.publicBoardState(),
      trainingRun: this.trainingRun ? clone(this.trainingRun) : null,
      publicTable: {
        pendingJointVenture: clone(this.pendingJointVenture),
        players: this.players.map((x) => this.publicPlayerState(x)),
        contracts: clone(this.contracts),
      },
    };
  }
  packet(seat, stage, legalDecisions) {
    const p = this.players[seat];
    const packet = {
      schemaVersion: this.decisionContext?.schemaVersion || 1,
      ...(this.decisionContext?.game
        ? { game: clone(this.decisionContext.game) }
        : {}),
      requestId: `${this.publicMatchId}:r${this.round}:c${this.cycle}:s${seat}:${stage}:${++this.decisionSerial}`,
      matchId: this.publicMatchId,
      seat,
      factionId: p.factionId,
      kitId: p.kitId,
      round: this.round,
      cycle: this.cycle,
      observation: this.publicObservation(seat),
      publicHistory: clone(this.publicHistory),
      legalDecisions: clone(legalDecisions),
    };
    Object.defineProperty(packet, "policySeed", { value: this.seed });
    return packet;
  }
  async choose(policies, seat, stage, decisions) {
    throwIfAborted(this.signal);
    if (!decisions.length) throw new Error(`Empty decision stage: ${stage}`);
    const packet = this.packet(seat, stage, decisions);
    const response = await policies[seat].decide(packet);
    throwIfAborted(this.signal);
    const answer = validateDecisionResponse(
      packet,
      response.decision || response,
    );
    const selected = decisions.find((d) => d.decisionId === answer.decisionId);
    const receipt = response.receipt || {
      provider: "policy",
      requestId: packet.requestId,
    };
    increment(
      this.players[seat].metrics.policyProviders,
      receipt.provider || "policy",
    );
    this.players[seat].metrics.policyReceipts.push(clone(receipt));
    this.recordEvent("decision", seat, selected.label, receipt);
    return clone(selected);
  }
  legalActionSelections(seat) {
    const p = this.players[seat];
    return this.config.actions
      .filter((a) => !p.actionsUsed.includes(a.id))
      .map((a) =>
        choice(
          `select_${a.id}`,
          `Select ${a.name}`,
          a.id,
          {},
          {
            stage: "action_selection",
            resolvableWithoutTrade:
              this.legalResolutions(seat, a.id).length > 0,
          },
        ),
      );
  }
  legalResolutions(seat, actionId) {
    const p = this.players[seat];
    const a = this.board.find((a) => a.actionId === actionId);
    if (!a) return [];
    return p.pieces.flatMap((agent) => {
      const base = {
        pieceId: agent.id,
        destinationId: a.instanceId,
        destinationCategory: a.category,
      };
      let decisions = [];
      if (actionId === "fund")
        decisions = [
          choice(
            "fund_conservative",
            `Gain ${this.rulesVariant.fundConservative} Runway`,
            "fund",
            { mode: "conservative" },
            { runway: this.rulesVariant.fundConservative },
          ),
          choice(
            "fund_venture",
            `Gain ${this.rulesVariant.fundVenture} Runway; lose ${this.rulesVariant.ventureReputationLoss} Reputation`,
            "fund",
            { mode: "venture" },
            {
              runway: this.rulesVariant.fundVenture,
              reputation: -this.rulesVariant.ventureReputationLoss,
            },
          ),
        ];
      if (actionId === "research" && p.compute >= 1)
        decisions = [
          choice(
            "research_run",
            "Pay 1 Compute; begin Training Run",
            "research",
            {},
            { compute: -1 },
          ),
        ];
      if (
        actionId === "deploy" &&
        p.compute >= this.rulesVariant.deployComputeCost &&
        this.canDeploy(p)
      )
        decisions = [
          choice(
            "deploy_customer",
            `Pay ${this.rulesVariant.deployComputeCost} Compute; take Customer ${p.customers + 1}; lose 1 Reputation`,
            "deploy",
            {},
            {
              compute: -this.rulesVariant.deployComputeCost,
              customers: 1,
              reputation: -1,
            },
          ),
        ];
      if (actionId === "build") {
        const price = Math.max(
          0,
          this.rulesVariant.facilityCost -
            (this.hasFactionAbility(p, "industrial_velocity") ? 1 : 0),
        );
        if (
          p.facilities.length < this.config.playerSupply.facilities &&
          p.runway >= price
        )
          for (const area of this.board)
            if (this.tileOccupancy(area.instanceId) < area.facilitySpaces)
              decisions.push(
                choice(
                  `build_facility_${area.instanceId}`,
                  `Build Facility in ${area.name} (${price} Runway)`,
                  "build",
                  {
                    facility: true,
                    hostAreaId: area.instanceId,
                    actualRunwayCost: price,
                  },
                  { runway: -price, facility: 1 },
                ),
              );
        const cost = this.config.construction.upgradeCost;
        if (
          this.round >= this.config.construction.upgradeUnlockEra &&
          p.runway >= cost.runway &&
          p.compute >= cost.compute
        )
          for (const f of p.facilities.filter((f) => !f.upgraded))
            decisions.push(
              choice(
                `build_upgrade_${f.id}`,
                `Upgrade ${f.id}: double Production (${cost.runway} Runway, ${cost.compute} Compute)`,
                "build",
                { upgradeHostId: f.id, actualRunwayCost: cost.runway },
                {
                  runway: -cost.runway,
                  compute: -cost.compute,
                  project: "upgrade",
                },
              ),
            );
      }
      if (actionId === "organize") {
        if (p.agentsInSupply > 0 && p.runway >= 2)
          decisions.push(
            choice(
              "organize_recruit",
              "Establish an Org (2 Runway)",
              "organize",
              { mode: "recruit" },
              { runway: -2, agents: 1 },
            ),
          );
        for (const other of p.pieces.filter((x) => x.id !== agent.id))
          for (const area of this.board)
            if (other.tileId !== area.instanceId)
              decisions.push(
                choice(
                  `organize_assign_${other.id}_${area.instanceId}`,
                  `Reassign Org ${p.pieces.indexOf(other) + 1} to ${area.name}`,
                  "organize",
                  {
                    mode: "reassign",
                    otherAgentId: other.id,
                    otherAreaId: area.instanceId,
                  },
                ),
              );
      }
      if (actionId === "influence") {
        decisions.push(
          choice(
            "influence_reputation",
            "Gain 2 Reputation",
            "influence",
            { mode: "reputation" },
            { reputation: 2 },
          ),
        );
        if (
          this.round >= 3 &&
          this.contracts.length < this.config.sharedSupply.jointVenturePairs
        )
          for (const left of p.facilities)
            for (const other of this.players.filter((x) => x.seat !== seat))
              for (const right of other.facilities)
                if (
                  !this.contracts.some(
                    (c) =>
                      [c.left.facilityId, c.right.facilityId].includes(
                        left.id,
                      ) ||
                      [c.left.facilityId, c.right.facilityId].includes(
                        right.id,
                      ),
                  )
                )
                  decisions.push(
                    choice(
                      `influence_venture_${left.id}_${right.id}`,
                      `Propose Joint Venture: ${left.id} + ${right.id}`,
                      "influence",
                      {
                        mode: "venture",
                        leftId: left.id,
                        rightId: right.id,
                        targetSeat: other.seat,
                      },
                    ),
                  );
        for (const c of this.contracts.filter((c) =>
          [c.left.seat, c.right.seat].includes(seat),
        ))
          decisions.push(
            choice(
              `influence_end_${c.id}`,
              `Terminate Joint Venture ${c.id}`,
              "influence",
              { mode: "terminate", contractId: c.id },
            ),
          );
      }
      return decisions.map((d) => ({
        ...d,
        decisionId: `${d.decisionId}_${agent.id}`,
        parameters: { ...base, ...d.parameters },
      }));
    });
  }
  assignAgent(p, parameters) {
    const agent = p.pieces.find((x) => x.id === parameters.pieceId);
    if (
      !agent ||
      !this.board.some((a) => a.instanceId === parameters.destinationId)
    )
      throw new RangeError("Invalid Org assignment.");
    agent.tileId = parameters.destinationId;
  }
  applyResolution(seat, decision) {
    const current = this.legalResolutions(seat, decision.actionId).find(
      (d) => d.decisionId === decision.decisionId,
    );
    if (!current) throw new RangeError("Action is no longer legal.");
    const p = this.players[seat],
      a = current.parameters;
    this.assignAgent(p, a);
    switch (current.actionId) {
      case "fund":
        this.addResource(
          p,
          "runway",
          a.mode === "venture"
            ? this.rulesVariant.fundVenture
            : this.rulesVariant.fundConservative,
        );
        if (a.mode === "venture")
          this.addResource(
            p,
            "reputation",
            -this.rulesVariant.ventureReputationLoss,
          );
        break;
      case "deploy":
        this.addResource(p, "compute", -this.rulesVariant.deployComputeCost);
        this.gainCustomer(p);
        this.addResource(p, "reputation", -1);
        if (this.hasFactionAbility(p, "installed_base"))
          this.addResource(p, "runway", 1);
        break;
      case "build":
        this.spendRunway(p, a.actualRunwayCost);
        if (a.facility) {
          const area = this.board.find((x) => x.instanceId === a.hostAreaId);
          p.facilities.push({
            id: `s${seat}-facility-${p.facilities.length + 1}`,
            tileId: area.instanceId,
            category: area.category,
            upgraded: false,
          });
        } else {
          this.addResource(
            p,
            "compute",
            -this.config.construction.upgradeCost.compute,
          );
          p.facilities.find((f) => f.id === a.upgradeHostId).upgraded = true;
          increment(p.metrics.projects, "upgrade");
          increment(this.matchMetrics.projects, "upgrade");
        }
        break;
      case "organize":
        if (a.mode === "recruit") {
          this.spendRunway(p, 2);
          p.pieces.push({
            id: `s${seat}-agent-${p.pieces.length + 1}`,
            kind: "agent",
            tileId: a.destinationId,
          });
          p.agentsInSupply--;
        } else
          p.pieces.find((x) => x.id === a.otherAgentId).tileId = a.otherAreaId;
        break;
      case "influence":
        if (a.mode === "reputation") this.addResource(p, "reputation", 2);
        else if (a.mode === "terminate")
          this.contracts = this.contracts.filter((c) => c.id !== a.contractId);
        else throw new Error("Venture requires a responder.");
        break;
      default:
        throw new Error("Research requires its interactive draw sequence.");
    }
    return current;
  }
  drawTrainingCard() {
    if (!this.trainingDrawPile.length) {
      this.trainingDrawPile = shuffle(
        this.trainingDiscard,
        createRng(`${this.seed}:training:${++this.trainingShuffle}`),
      );
      this.trainingDiscard = [];
    }
    const card = this.trainingDrawPile.shift();
    if (!card) throw new Error("Training deck is empty.");
    this.trainingDiscard.push(card);
    return card;
  }
  async research(policies, seat, decision) {
    const p = this.players[seat];
    this.assignAgent(p, decision.parameters);
    this.addResource(p, "compute", -1);
    let provisional = 0;
    const domains = new Set(),
      revealed = [];
    let outcome = "banked";
    try {
      for (let draws = 0; draws < 40; draws++) {
        const card = this.drawTrainingCard();
        revealed.push(card.type);
        let duplicate = false;
        if (card.kind === "domain") {
          duplicate = domains.has(card.type);
          if (!duplicate) {
            domains.add(card.type);
            provisional++;
          }
        } else if (card.type === "curated_corpus") {
          const missing = TRAINING_DOMAINS.find((x) => !domains.has(x));
          if (missing) {
            domains.add(missing);
            provisional++;
          } else duplicate = true;
        } else if (card.type === "benchmark_leak") {
          provisional += 2;
          this.addResource(p, "reputation", -1);
        } else if (card.type === "human_evaluation") {
          this.addResource(p, "reputation", 1);
          outcome = "human-evaluation";
          break;
        }
        this.trainingRun = {
          seat,
          provisionalCapability: provisional,
          revealed: [...revealed],
          domains: [...domains],
        };
        if (duplicate) {
          if (this.hasFactionAbility(p, "scientific_method") && p.runway >= 1) {
            const d = await this.choose(policies, seat, "research_duplicate", [
              choice("research_pay_bank", "Pay 1 Runway and bank", "research"),
              choice("research_crash", "Accept crash", "research"),
            ]);
            if (d.decisionId === "research_pay_bank") {
              this.spendRunway(p, 1);
              outcome = "scientific-method-banked";
              break;
            }
          }
          provisional = Math.min(
            provisional,
            this.hasFactionAbility(p, "crash_retention") ? 1 : 0,
          );
          outcome = "crashed";
          break;
        }
        const d = await this.choose(policies, seat, "research_continue", [
          choice(
            "research_bank",
            `Bank ${provisional} Capability`,
            "research",
            {},
            { capability: provisional },
          ),
          choice("research_continue", "Draw another card", "research"),
        ]);
        if (d.decisionId === "research_bank") break;
      }
      this.addResource(p, "capability", provisional);
      p.metrics.researchCapability.push({
        round: this.round,
        gained: provisional,
        outcome,
        distinctDomains: domains.size,
      });
      this.recordEvent(
        "research_result",
        seat,
        `${outcome}: ${provisional} Capability`,
      );
    } finally {
      this.trainingRun = null;
    }
  }
  async negotiate(policies, seat, decision) {
    const p = this.players[seat],
      v = decision.parameters;
    this.assignAgent(p, v);
    const left = p.facilities.find((f) => f.id === v.leftId),
      other = this.players[v.targetSeat],
      right = other.facilities.find((f) => f.id === v.rightId);
    if (!left || !right) throw new Error("Missing Venture host.");
    this.pendingJointVenture = {
      proposerSeat: seat,
      responderSeat: other.seat,
      left: { seat, facilityId: left.id, tileId: left.tileId },
      right: { seat: other.seat, facilityId: right.id, tileId: right.tileId },
      income: [
        {
          seat,
          resource: facilityContractResource(this.board, right),
          amount: 1,
        },
        {
          seat: other.seat,
          resource: facilityContractResource(this.board, left),
          amount: 1,
        },
      ],
    };
    try {
      const answer = await this.choose(
        policies,
        other.seat,
        "agreement_response",
        [
          choice("agreement_accept", "Accept Joint Venture", "influence"),
          choice("agreement_reject", "Reject Joint Venture", "influence"),
        ],
      );
      if (answer.decisionId === "agreement_accept")
        this.contracts.push({
          id: ++this.contractSerial,
          kind: "joint_venture",
          left: { seat, facilityId: left.id },
          right: { seat: other.seat, facilityId: right.id },
        });
    } finally {
      this.pendingJointVenture = null;
    }
  }
  immediateTradeDecisions(seat) {
    const p = this.players[seat],
      choices = [choice("trade_none", "Continue without a trade", "trade")];
    for (const other of this.players.filter((x) => x.seat !== seat))
      for (const giveResource of ["runway", "compute"]) {
        const receiveResource =
          giveResource === "runway" ? "compute" : "runway";
        if (
          p[giveResource] >= 1 &&
          other[receiveResource] >= 1 &&
          p[receiveResource] < this.config.resources[receiveResource].cap &&
          other[giveResource] < this.config.resources[giveResource].cap
        )
          choices.push(
            choice(
              `trade_offer_${other.seat}_${giveResource}`,
              `Offer 1 ${giveResource} for 1 ${receiveResource} to ${other.factionName}`,
              "trade",
              {
                partnerSeat: other.seat,
                giveResource,
                receiveResource,
                giveAmount: 1,
                receiveAmount: 1,
              },
            ),
          );
      }
    return choices;
  }
  completeImmediateTrade(seat, otherSeat, offer) {
    const legal = this.immediateTradeDecisions(seat).find(
      (d) =>
        d.parameters.partnerSeat === otherSeat &&
        d.parameters.giveResource === offer.giveResource &&
        d.parameters.receiveResource === offer.receiveResource,
    );
    if (!legal || offer.giveAmount !== 1 || offer.receiveAmount !== 1)
      return false;
    const p = this.players[seat],
      other = this.players[otherSeat];
    p[offer.giveResource]--;
    other[offer.receiveResource]--;
    p[offer.receiveResource]++;
    other[offer.giveResource]++;
    if (this.hasFactionAbility(p, "deal_flow"))
      this.addResource(p, "runway", 1);
    this.matchMetrics.trades.accepted++;
    return true;
  }
  async trade(policies, seat) {
    this.immediateTradePackets++;
    const offered = await this.choose(
      policies,
      seat,
      "immediate_trade",
      this.immediateTradeDecisions(seat),
    );
    if (offered.decisionId === "trade_none") return;
    this.matchMetrics.trades.offers++;
    const v = offered.parameters;
    this.immediateTradePackets++;
    const answer = await this.choose(
      policies,
      v.partnerSeat,
      "trade_response",
      [
        choice(
          "trade_accept",
          `Accept: give 1 ${v.receiveResource}, receive 1 ${v.giveResource}`,
          "trade",
          { ...v, tradePerspective: "responder" },
        ),
        choice("trade_reject", "Reject trade", "trade"),
      ],
    );
    if (answer.decisionId === "trade_accept")
      this.completeImmediateTrade(seat, v.partnerSeat, v);
    else this.matchMetrics.trades.refused++;
  }
  recordEligibility(p, stage) {
    if (!p.metrics.earliestAgiEligibility && this.declarationReadiness(p).ready)
      p.metrics.earliestAgiEligibility = {
        round: this.round,
        cycle: this.cycle,
        stage,
      };
  }
  declarationReadiness(p) {
    const a = this.config.agiAchievement;
    const failing =
      p.capability < a.capability
        ? "capability"
        : p.reputation < a.reputation
          ? "reputation"
          : p.compute < a.computeCost
            ? "compute"
            : null;
    return { ready: !failing, failingRequirement: failing };
  }
  async declareAgiAchievements(policies) {
    for (const seat of this.initiativeOrder()) {
      const p = this.players[seat];
      const readiness = this.declarationReadiness(p);
      const requirements = this.config.agiAchievement;
      const entry = {
        seat,
        factionId: p.factionId,
        coreRequirementsMet:
          p.capability >= requirements.capability &&
          p.reputation >= requirements.reputation,
        legalDeclarationWindow: readiness.ready,
        failingRequirement: readiness.failingRequirement,
        claimRegistered: p.agiDeclared,
        emergenceTriggered: p.agiDeclared,
        declared: p.agiDeclared,
      };
      this.matchMetrics.agiFunnel = this.matchMetrics.agiFunnel.filter(
        (row) => row.seat !== seat,
      );
      this.matchMetrics.agiFunnel.push(entry);
      this.recordEligibility(p, "final_recognition");
      if (p.agiDeclared || !readiness.ready) continue;
      const d = await this.choose(policies, seat, "agi_recognition", [
        choice(
          "agi_declare",
          `Pay ${this.config.agiAchievement.computeCost} Compute; recognize AGI`,
          "agi",
        ),
        choice("agi_pass", "Pass", "agi"),
      ]);
      if (d.decisionId === "agi_declare") {
        this.addResource(p, "compute", -this.config.agiAchievement.computeCost);
        p.agiDeclared = true;
        this.matchMetrics.declarations++;
        entry.claimRegistered =
          entry.emergenceTriggered =
          entry.declared =
            true;
      }
    }
  }
  async produceAll() {
    for (const seat of this.initiativeOrder()) {
      const p = this.players[seat];
      if (this.hasFactionAbility(p, "the_shovels")) {
        const income = Math.min(
          2,
          this.players.filter((x) => x.seat !== seat && x.facilities.length)
            .length,
        );
        p.metrics.shovelsIncome += this.addResource(p, "runway", income);
      }
      for (const f of p.facilities) {
        const area = this.board.find((a) => a.instanceId === f.tileId);
        this.addResource(
          p,
          area.yield.resource,
          area.yield.amount * (f.upgraded ? 2 : 1),
        );
      }
      this.addResource(p, "runway", p.customers);
    }
    for (const c of this.contracts.filter((c) => activeJointVenture(this, c)))
      for (const [own, other] of [
        [c.left, c.right],
        [c.right, c.left],
      ]) {
        const host = this.players[other.seat].facilities.find(
          (f) => f.id === other.facilityId,
        );
        this.addResource(
          this.players[own.seat],
          facilityContractResource(this.board, host),
          1,
        );
      }
    this.matchMetrics.productionSnapshots.push({
      round: this.round,
      players: this.players.map((p) => ({
        seat: p.seat,
        runway: p.runway,
        compute: p.compute,
        reputation: p.reputation,
        projectedScore: this.currentScore(p),
      })),
    });
  }
  async audit() {
    for (const p of this.players)
      if (p.reputation <= this.config.reputationReview.atMost) {
        p.runway = Math.max(
          0,
          p.runway - this.rulesVariant.reviewRunwayPenalty,
        );
        p.metrics.auditHits++;
        p.metrics.reputationReviewHits++;
      }
    this.recordEvent(
      "reputation_review",
      null,
      "Low Reputation pays the printed Runway penalty.",
    );
  }
  async prepareHeadline(policies) {
    const card = this.eraHeadlines[this.cycle - 1];
    this.activeHeadline = card || null;
    if (!card) return;
    increment(this.matchMetrics.headlines, card.id);
    this.matchMetrics.futureTimeline.push({
      round: this.round,
      cycle: this.cycle,
      id: card.id,
      name: card.name,
    });
    const effect = card.effect;
    if (!effect) throw new Error(`Missing Headline effect: ${card.id}`);
    let seats = this.initiativeOrder();
    if (effect.target === "lowest_customers") {
      const min = Math.min(...this.players.map((p) => p.customers));
      seats = [seats.find((s) => this.players[s].customers === min)];
    }
    for (const seat of seats) {
      const p = this.players[seat];
      if (
        Object.entries(effect.minimum || {}).some(
          ([key, n]) =>
            (key === "facilities" ? p.facilities.length : p[key]) < n,
        )
      )
        continue;
      if (effect.normalCustomerRequirement && !this.canDeploy(p)) continue;
      if (Object.entries(effect.cost || {}).some(([key, n]) => p[key] < n))
        continue;
      if (effect.optional) {
        const d = await this.choose(policies, seat, "headline_choice", [
          choice(
            `headline_${card.id}_accept`,
            card.text,
            "headline",
            {},
            effect.gain,
          ),
          choice(`headline_${card.id}_pass`, "Pass", "headline"),
        ]);
        if (d.decisionId.endsWith("_pass")) continue;
      }
      for (const [key, n] of Object.entries(effect.cost || {}))
        this.addResource(p, key, -n);
      for (const [key, n] of Object.entries(effect.gain || {})) {
        if (key === "customers")
          for (let i = 0; i < n; i++) this.gainCustomer(p);
        else this.addResource(p, key, n);
      }
    }
    this.recordEvent("headline", null, card.text);
  }
  async beginRound() {
    this.roundInitialized = true;
    this.players.forEach((p) => {
      p.actionsUsed = [];
    });
    const pool = this.mandateDocument.mandates.filter(
      (m) => m.era === this.round,
    );
    this.roundMandate =
      (this.mandateMode === "fixed"
        ? pool
        : shuffle(pool, createRng(`${this.seed}:mandates:${this.round}`)))[0] ||
      null;
    if (this.roundMandate) this.revealedMandates.push(this.roundMandate);
    this.eraHeadlines = shuffle(
      this.headlineDocument.headlines.filter((h) => h.round === this.round),
      createRng(`${this.seed}:headlines:${this.round}`),
    ).slice(0, 3);
  }
  async playCycle(policies) {
    if (this.complete) return;
    throwIfAborted(this.signal);
    if (!this.roundInitialized) await this.beginRound();
    await this.prepareHeadline(policies);
    const committed = await Promise.all(
      this.players.map((p) =>
        this.choose(
          policies,
          p.seat,
          "select",
          this.legalActionSelections(p.seat),
        ),
      ),
    );
    committed.forEach((d, s) => {
      this.players[s].selectedAction = d.actionId;
    });
    for (const seat of this.initiativeOrder()) {
      const p = this.players[seat],
        id = p.selectedAction;
      await this.trade(policies, seat);
      const legal = this.legalResolutions(seat, id);
      if (legal.length) {
        const d = await this.choose(policies, seat, "resolve", legal);
        if (id === "research") await this.research(policies, seat, d);
        else if (id === "influence" && d.parameters.mode === "venture")
          await this.negotiate(policies, seat, d);
        else this.applyResolution(seat, d);
      } else {
        p.metrics.forcedNoOps++;
        p.metrics.blockedAfterCommitment++;
        this.recordEvent(
          "blocked_action",
          seat,
          `${id} has no legal resolution.`,
        );
      }
      p.actionsUsed.push(id);
      p.selectedAction = null;
      increment(p.metrics.actions, id);
      if (this.round === 1) p.metrics.openingActions.push(id);
      this.recordEligibility(p, "after_action");
    }
    this.initiativeSeat = (this.initiativeSeat + 1) % this.playerCount;
    if (this.cycle === 3) {
      await this.produceAll();
      await this.audit();
      if (this.round === 4) {
        await this.declareAgiAchievements(policies);
        this.complete = true;
        this.scoreMandate();
      } else {
        this.round++;
        this.cycle = 1;
        this.roundInitialized = false;
      }
    } else this.cycle++;
    this.onProgress?.({
      kind: "cycle_complete",
      round: this.round,
      cycle: this.cycle,
      complete: this.complete,
    });
    this.recordEvent("cycle_complete", null, "Cycle complete.");
  }
  async play(policies) {
    while (!this.complete) await this.playCycle(policies);
    return this.result();
  }
  finalObjectives() {
    return this.revealedMandates.map((card) => ({
      id: card.id,
      round: card.era,
      standings: finalObjectiveStandings(card, this),
    }));
  }
  scoreMandate() {
    this.matchMetrics.eraMandateScores = this.finalObjectives();
    for (const p of this.players) {
      p.metrics.mandatesWon = Object.fromEntries(
        this.matchMetrics.eraMandateScores.map((c) => [
          c.id,
          c.standings.find((s) => s.seat === p.seat).points,
        ]),
      );
    }
  }
  currentScore(p) {
    const s = this.config.scoring;
    return (
      p.capability * s.capability +
      p.customers * this.rulesVariant.customerPoints +
      p.reputation * s.reputation +
      (p.agiDeclared ? s.agi : 0) +
      this.finalObjectives().reduce(
        (n, c) => n + c.standings.find((r) => r.seat === p.seat).points,
        0,
      )
    );
  }
  finalMandate(p) {
    return { score: this.currentScore(p) };
  }
  recordEvent(type, seat, summary, receipt = null) {
    const e = {
      round: this.round,
      cycle: this.cycle,
      type,
      seat,
      summary,
      ...(receipt ? { decisionReceipt: clone(receipt) } : {}),
    };
    this.publicHistory.push(e);
    if (this.recordReplay)
      this.replay.push({ ...clone(e), state: this.snapshot() });
  }
  snapshot() {
    return {
      round: this.round,
      cycle: this.cycle,
      initiativeSeat: this.initiativeSeat,
      complete: this.complete,
      board: clone(this.board),
      activeHeadline: this.activeHeadline ? clone(this.activeHeadline) : null,
      roundMandate: this.roundMandate?.id || null,
      revealedMandates: clone(this.revealedMandates),
      contracts: clone(this.contracts),
      players: this.players.map((p) => ({
        ...this.publicPlayerState(p),
        agiReadiness: this.declarationReadiness(p),
        currentEraObjective: this.currentEraObjective(p),
        ...(this.complete ? { finalScore: this.currentScore(p) } : {}),
      })),
    };
  }
  result() {
    const standings = this.players
      .map((p) => ({
        ...this.publicPlayerState(p),
        profileId: p.profileId,
        backendId: p.backendId,
        score: this.currentScore(p),
        facilities: p.facilities.length,
        metrics: clone(p.metrics),
        agiReadiness: this.declarationReadiness(p),
      }))
      .sort(
        (a, b) =>
          b.score - a.score ||
          b.reputation - a.reputation ||
          b.customers - a.customers ||
          b.compute - a.compute ||
          a.seat - b.seat,
      );
    const first = standings[0];
    const winnerSeats = standings
      .filter(
        (p) =>
          p.score === first.score &&
          p.reputation === first.reputation &&
          p.customers === first.customers &&
          p.compute === first.compute,
      )
      .map((p) => p.seat);
    const agiEmerges = this.players.some((p) => p.agiDeclared),
      averageReputation =
        this.players.reduce((n, p) => n + p.reputation, 0) / this.playerCount,
      openContinuity =
        averageReputation >=
        this.config.worldEnding.openContinuity.minimumAverageReputation;
    const id = agiEmerges
      ? openContinuity
        ? "singularity"
        : "closed_loop"
      : openContinuity
        ? "plural_future"
        : "assured_continuity";
    const names = this.config.worldEnding.outcomes;
    return {
      schemaVersion: 1,
      evidenceLabel: "simulation",
      scope: this.scope,
      seed: this.seed,
      playerCount: this.playerCount,
      rulesVariant: clone(this.rulesVariant),
      matchMetrics: {
        ...clone(this.matchMetrics),
        activeVentures: this.contracts.filter((c) =>
          activeJointVenture(this, c),
        ).length,
      },
      decisionProtocol: {
        immediateTradePackets: this.immediateTradePackets,
        immediateTradePacketCeiling: this.immediateTradePacketCeiling,
      },
      futureTimeline: clone(this.matchMetrics.futureTimeline),
      worldEnding: {
        id,
        name: {
          singularity: names.singularity,
          closed_loop: names.closedLoop,
          plural_future: names.pluralFuture,
          assured_continuity: names.assuredContinuity,
        }[id],
        agiEmerges,
        openContinuity,
        averageReputation,
      },
      standings,
      winnerSeats,
      replay: this.recordReplay ? clone(this.replay) : undefined,
    };
  }
}
