import { createRng } from "../../web/src/engine.js";
import { validateDecisionPacket, validateDecisionResponse } from "../contracts/decision-contract.js";
import { validatePlayerProfile } from "../personas/player-profile.js";

export const TRADE_REQUIRED_SELECTION_WEIGHT = 0.02;
export const BLOCKED_SELECTION_WEIGHT = 0.02;
export const supportedPolicyTreatments = new Set([
  null,
  "coalition_conversion_v1"
]);

export function validatePolicyTreatment(treatment) {
  const resolved = treatment ?? null;
  if (!supportedPolicyTreatments.has(resolved)) {
    throw new TypeError(`Unknown deterministic policy treatment: ${treatment}.`);
  }
  return resolved;
}

function readPath(value, path) {
  return path.split(".").reduce((current, segment) => current?.[segment], value);
}

function conditionMatches(packet, condition) {
  const actual = readPath(packet.observation, condition.path);
  switch (condition.operator) {
    case "eq": return actual === condition.value;
    case "ne": return actual !== condition.value;
    case "lt": return actual < condition.value;
    case "lte": return actual <= condition.value;
    case "gt": return actual > condition.value;
    case "gte": return actual >= condition.value;
    case "includes": return Array.isArray(actual) && actual.includes(condition.value);
    default: return false;
  }
}

function ruleTargets(decision, target) {
  return (
    (target.actionId === undefined || target.actionId === decision.actionId) &&
    (
      target.decisionIdPrefix === undefined ||
      decision.decisionId.startsWith(target.decisionIdPrefix)
    )
  );
}

export class WeightedPlayerPolicy {
  constructor(profile, {
    selection = profile.strategy.selection,
    treatment = null,
    rosterProfileIds = []
  } = {}) {
    this.profile = validatePlayerProfile(profile);
    this.selection = selection;
    this.treatment = validatePolicyTreatment(treatment);
    this.rosterProfileIds = [...rosterProfileIds];
    this.kind = "deterministic";
  }

  partnerMultiplier(decision) {
    const targetSeat = decision.parameters?.targetSeat ??
      decision.parameters?.partnerSeat;
    if (!Number.isInteger(targetSeat)) return 1;
    const targetProfileId = this.rosterProfileIds[targetSeat];
    return this.profile.strategy.partnerWeights?.[targetProfileId] || 1;
  }

  spatialMultiplier(packet, decision) {
    const preference = this.profile.strategy.spatialPreference;
    const destinationId = decision.parameters?.destinationId;
    if (!preference || !destinationId) return 1;
    if (
      preference.applyUntilFacilities &&
      packet.observation.self.facilities >= preference.applyUntilFacilities
    ) return 1;
    const targetSeats = this.rosterProfileIds
      .map((profileId, seat) => ({ profileId, seat }))
      .filter((entry) => entry.profileId === preference.targetProfileId)
      .map((entry) => entry.seat);
    if (!targetSeats.length) return 1;
    const destination = packet.observation.board.find(
      (tile) => tile.tileId === destinationId
    );
    if (!destination) return 1;
    const targetTileIds = new Set(packet.observation.board
      .filter((tile) => tile.components.some((component) =>
        targetSeats.includes(component.ownerSeat) &&
        ["piece", "facility", "generator"].includes(component.type)
      ))
      .map((tile) => tile.tileId));
    const distance = (left, right) => Math.max(
      Math.abs(left.q - right.q),
      Math.abs(left.r - right.r),
      Math.abs((-left.q - left.r) - (-right.q - right.r))
    );
    const nearest = Math.min(...packet.observation.board
      .filter((tile) => targetTileIds.has(tile.tileId))
      .map((tile) => distance(destination, tile)));
    return nearest === preference.preferredDistance
      ? preference.multiplier
      : 1;
  }

  tradeMultiplier(decision) {
    const parameters = decision.parameters;
    if (!parameters?.giveResource || !parameters?.receiveResource) return 1;
    const values = this.profile.strategy.resourceValues || {
      runway: 1,
      compute: 1
    };
    const responder = parameters.tradePerspective === "responder";
    const giveResource = responder
      ? parameters.receiveResource
      : parameters.giveResource;
    const giveAmount = responder
      ? parameters.receiveAmount
      : parameters.giveAmount;
    const receiveResource = responder
      ? parameters.giveResource
      : parameters.receiveResource;
    const receiveAmount = responder
      ? parameters.giveAmount
      : parameters.receiveAmount;
    const netValue =
      (values[receiveResource] || 1) * receiveAmount -
      (values[giveResource] || 1) * giveAmount;
    return Math.max(0.05, 1 + netValue * 0.4);
  }

  treatmentMultiplier(packet, decision) {
    if (
      this.treatment !== "coalition_conversion_v1" ||
      packet.factionId !== "coalition_lab" ||
      (packet.observation.self.dealFlowConversion?.unspentCredits || 0) < 1
    ) return 1;

    if (decision.consequences?.stage === "action_selection") {
      if (decision.actionId === "build") return 3;
      if (decision.actionId === "organize") return 1.5;
      if (decision.actionId === "fund") return 0.35;
      return 1;
    }

    const runwayCost = Math.max(0,
      decision.parameters?.actualRunwayCost === undefined
        ? -(Number(decision.consequences?.runway) || 0)
        : Number(decision.parameters.actualRunwayCost) || 0
    );
    const nonDealFlowRunway = Math.max(
      0,
      (packet.observation.self.runway || 0) -
        (packet.observation.self.dealFlowConversion?.unspentCredits || 0)
    );
    if (runwayCost < 1 || runwayCost <= nonDealFlowRunway) return 1;

    if (decision.parameters?.buildMode === "facility") return 4;
    if (decision.parameters?.buildMode === "generator") return 3;
    if (decision.parameters?.mode === "recruit") return 2;
    return 1.25;
  }

  score(packet, decision) {
    if (decision.decisionId === "agi_declare") return 4;
    if (decision.decisionId === "agi_pass") return 1;
    const strategy = this.profile.strategy;
    const negotiation = strategy.negotiation;
    if (decision.decisionId === "trade_none") {
      return decision.consequences?.selectedActionCurrentlyResolvable === false
        ? 0.01
        : 2;
    }
    if (
      decision.decisionId.startsWith("trade_offer_") ||
      decision.decisionId.startsWith("trade_counter_before_") ||
      decision.decisionId.startsWith("trade_counter_after_")
    ) {
      const enablesAction = decision.consequences?.enablesSelectedAction ? 8 : 1;
      return 1.2 * enablesAction * this.tradeMultiplier(decision) *
        this.partnerMultiplier(decision);
    }
    if (
      decision.decisionId === "trade_accept" ||
      decision.decisionId === "trade_counter_accept"
    ) return this.tradeMultiplier(decision);
    if (
      decision.decisionId === "trade_reject" ||
      decision.decisionId === "trade_counter_reject"
    ) return 1;
    let weight = strategy.actionWeights[decision.actionId] || 1;
    if (decision.consequences?.stage === "action_selection") {
      if (decision.consequences.status === "trade_required") {
        weight *= TRADE_REQUIRED_SELECTION_WEIGHT;
      } else if (decision.consequences.resolvableWithoutTrade === false) {
        weight *= BLOCKED_SELECTION_WEIGHT;
      }
    }
    for (const [prefix, multiplier] of Object.entries(strategy.decisionWeights || {})) {
      if (decision.decisionId.startsWith(prefix)) weight *= multiplier;
    }
    const relationship = decision.parameters?.relationship;
    if (relationship) {
      weight *= Math.max(
        0.05,
        1 +
          (relationship.fulfilled || 0) * negotiation.reciprocityWeight -
          (relationship.broken || 0) * negotiation.reciprocityWeight
      );
    }
    if (decision.consequences?.promiseFulfillment) {
      weight *= negotiation.fulfillWeight;
    }
    if (decision.consequences?.promiseBetrayal) {
      weight *= negotiation.betrayWeight;
    }
    let consequenceValue = 0;
    for (const [key, multiplier] of Object.entries(
      strategy.consequenceWeights || {}
    )) {
      const value = decision.consequences?.[key];
      if (typeof value === "number") consequenceValue += value * multiplier;
    }
    weight *= Math.max(0.01, 1 + consequenceValue);
    weight *= this.partnerMultiplier(decision);
    weight *= this.spatialMultiplier(packet, decision);
    for (const rule of strategy.rules) {
      if (
        ruleTargets(decision, rule.target) &&
        rule.when.every((condition) => conditionMatches(packet, condition))
      ) {
        weight *= rule.multiplier;
      }
    }
    weight *= this.treatmentMultiplier(packet, decision);
    return weight;
  }

  rank(packet) {
    validateDecisionPacket(packet);
    return packet.legalDecisions
      .map((decision) => ({ decision, weight: this.score(packet, decision) }))
      .sort((left, right) =>
        right.weight - left.weight ||
        left.decision.decisionId.localeCompare(right.decision.decisionId)
      );
  }

  async decide(packet) {
    const ranked = this.rank(packet);
    let selected = ranked[0];
    if (this.selection === "weighted") {
      const total = ranked.reduce((sum, entry) => sum + entry.weight, 0);
      const rng = createRng(
        `${packet.policySeed || packet.seed || packet.matchId}:${packet.requestId}:${packet.seat}:${this.profile.id}`
      );
      let target = rng() * total;
      selected = ranked.at(-1);
      for (const entry of ranked) {
        target -= entry.weight;
        if (target <= 0) {
          selected = entry;
          break;
        }
      }
    } else {
      const tied = ranked.filter((entry) => entry.weight === ranked[0].weight);
      if (tied.length > 1) {
        const rng = createRng(
          `${packet.policySeed || packet.seed || packet.matchId}:` +
          `${packet.requestId}:${packet.seat}:${this.profile.id}:greedy-tie`
        );
        selected = tied[Math.floor(rng() * tied.length)];
      }
    }

    return {
      decision: validateDecisionResponse(packet, {
        decisionId: selected.decision.decisionId,
        rationale: `${this.profile.name} selected with weight ${selected.weight.toFixed(3)}.`
      }),
      receipt: {
        provider: `${this.selection}-policy`,
        profileId: this.profile.id,
        policyTreatment: this.treatment,
        requestId: packet.requestId,
        selectedWeight: selected.weight,
        tiedTopCount: ranked.filter(
          (entry) => entry.weight === ranked[0].weight
        ).length
      }
    };
  }
}
