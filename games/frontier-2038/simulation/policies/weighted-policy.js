import { createRng } from "../../prototype/src/engine.js";
import { validateDecisionPacket, validateDecisionResponse } from "../contracts/decision-contract.js";
import { validatePlayerProfile } from "../personas/player-profile.js";

export const UNRESOLVABLE_SELECTION_WEIGHT = 0.02;

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

function hexDistance(left, right) {
  return Math.max(
    Math.abs(left.q - right.q),
    Math.abs(left.r - right.r),
    Math.abs((-left.q - left.r) - (-right.q - right.r))
  );
}

export class WeightedPlayerPolicy {
  constructor(profile, { selection = profile.strategy.selection } = {}) {
    this.profile = validatePlayerProfile(profile);
    this.selection = selection;
    this.kind = "deterministic";
  }

  score(packet, decision) {
    const strategy = this.profile.strategy;
    const negotiation = strategy.negotiation;
    if (decision.decisionId === "negotiation_none") return 1;
    if (decision.decisionId.startsWith("negotiation_power_")) {
      return negotiation.promiseWeight;
    }
    if (decision.decisionId === "trade_none") return 4;
    if (decision.decisionId === "trade_before" || decision.decisionId === "trade_after") {
      return 0.45;
    }
    if (decision.decisionId.startsWith("trade_offer_")) return 0.7;
    if (decision.decisionId === "trade_reject") return 2;
    let weight = strategy.actionWeights[decision.actionId] || 1;
    if (
      decision.consequences?.stage === "action_selection" &&
      decision.consequences.resolvableWithoutTrade === false
    ) {
      weight *= UNRESOLVABLE_SELECTION_WEIGHT;
    }
    for (const [prefix, multiplier] of Object.entries(strategy.decisionWeights || {})) {
      if (decision.decisionId.startsWith(prefix)) weight *= multiplier;
    }
    const targetProfileId = decision.parameters?.targetProfileId;
    if (targetProfileId) {
      weight *= strategy.partnerWeights?.[targetProfileId] || 1;
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
    const preference = strategy.spatialPreference;
    const destinationId = decision.parameters?.destinationId;
    if (
      preference &&
      destinationId &&
      decision.parameters?.buildMode === "facility" &&
      (packet.observation.self?.facilities || 0) <
        (preference.applyUntilFacilities || 1)
    ) {
      const destination = packet.observation.board?.find(
        (tile) => tile.tileId === destinationId
      );
      const targets = packet.observation.opponents?.filter(
        (opponent) => opponent.profileId === preference.targetProfileId
      ) || [];
      const targetTiles = targets.flatMap((opponent) =>
        (opponent.facilityTileIds || []).map((tileId) =>
          packet.observation.board?.find((tile) => tile.tileId === tileId)
        ).filter(Boolean)
      );
      if (destination && targetTiles.length) {
        const distance = Math.min(
          ...targetTiles.map((target) => hexDistance(destination, target))
        );
        if (distance === preference.preferredDistance) {
          weight *= preference.multiplier;
        } else if (distance === 0 && preference.preferredDistance === 1) {
          weight *= 0.05;
        }
      }
    }
    for (const rule of strategy.rules) {
      if (
        ruleTargets(decision, rule.target) &&
        rule.when.every((condition) => conditionMatches(packet, condition))
      ) {
        weight *= rule.multiplier;
      }
    }
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
        `${packet.seed}:${packet.requestId}:${packet.seat}:${this.profile.id}`
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
    }

    return {
      decision: validateDecisionResponse(packet, {
        decisionId: selected.decision.decisionId,
        rationale: `${this.profile.name} selected with weight ${selected.weight.toFixed(3)}.`
      }),
      receipt: {
        provider: `${this.selection}-policy`,
        profileId: this.profile.id,
        requestId: packet.requestId,
        selectedWeight: selected.weight
      }
    };
  }
}
