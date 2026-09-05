import { validateDecisionPacket } from "../contracts/decision-contract.js";
import { profileForPrompt, validatePlayerProfile } from "../personas/player-profile.js";
import { throwIfAborted } from "../cancellation.js";

function formalResponseDefault(packet) {
  const stage = packet.requestId.split(":").at(-2) || "";
  const decisionId = stage.startsWith("immediate_trade_response")
    ? "trade_reject"
    : stage.startsWith("immediate_trade_claim")
      ? "trade_claim_pass"
      : stage.startsWith("immediate_trade_counterparty")
        ? "trade_counterparty_decline"
        : stage === "negotiation_response"
          ? "agreement_reject"
          : stage === "mega_cluster_partner"
            ? "mega_cluster_reject"
            : null;
  if (decisionId) {
    return packet.legalDecisions.find((decision) => decision.decisionId === decisionId) || null;
  }
  if (stage.startsWith("allocation_response_")) {
    return packet.legalDecisions.find((decision) =>
      decision.decisionId.startsWith("allocation_reject_")
    ) || null;
  }
  if (stage.startsWith("allocation_counterparty_")) {
    return packet.legalDecisions.find((decision) =>
      decision.decisionId.startsWith("allocation_counter_reject_")
    ) || null;
  }
  return null;
}

export class CliBackedPlayerPolicy {
  constructor(profile, caller, {
    fallback,
    decisionBudget,
    decisionCache,
    cacheMode = "off",
    backendId,
    model,
    reasoningEffort,
    signal,
    requireLlm = false,
    strictLlmEvidence = false,
    llmStages
  } = {}) {
    this.profile = validatePlayerProfile(profile);
    this.caller = caller;
    this.fallback = fallback;
    this.decisionBudget = decisionBudget;
    this.decisionCache = decisionCache;
    this.cacheMode = cacheMode;
    this.backendId = backendId;
    this.model = model;
    this.reasoningEffort = reasoningEffort;
    this.signal = signal;
    this.requireLlm = requireLlm;
    this.strictLlmEvidence = strictLlmEvidence;
    this.llmStages = llmStages || null;
    this.kind = "llm";
  }

  async decide(packet) {
    throwIfAborted(this.signal);
    validateDecisionPacket(packet);
    const augmented = {
      ...packet,
      strategy: profileForPrompt(this.profile)
    };
    if (packet.policySeed !== undefined) {
      Object.defineProperty(augmented, "policySeed", {
        value: packet.policySeed,
        enumerable: false
      });
    }
    if (
      this.llmStages?.length &&
      !this.llmStages.some((stage) => packet.requestId.includes(`:${stage}`))
    ) {
      if (this.strictLlmEvidence) {
        const error = new Error(
          `Strict LLM decision is unavailable for gated stage ${packet.requestId}.`
        );
        error.evidenceOutcome = "quarantined";
        throw error;
      }
      const defaultResponse = formalResponseDefault(augmented);
      if (defaultResponse) {
        return this.rulebookResponseDefault(
          augmented,
          defaultResponse,
          "LLM response stage is not enabled."
        );
      }
      if (this.requireLlm) {
        throw new Error(
          `Required LLM decision is unavailable for gated stage ${packet.requestId}.`
        );
      }
      const result = await this.fallback.decide(augmented);
      return {
        ...result,
        receipt: {
          ...result.receipt,
          profileId: this.profile.id,
          gated: true,
          fallback: false,
          fallbackReason: null
        }
      };
    }
    let cacheKey = null;
    const cacheInput = {
      backend: this.backendId,
      model: this.model,
      reasoningEffort: this.reasoningEffort,
      decisionProtocolVersion:
        this.caller.decisionProtocolVersion || "canonical-decision-id-v1",
      packet: augmented,
      profile: profileForPrompt(this.profile)
    };
    if (this.decisionCache && ["read-write", "read-only"].includes(this.cacheMode)) {
      const cached = await this.decisionCache.read(cacheInput);
      cacheKey = cached.key;
      if (cached.value) {
        if (this.strictLlmEvidence && cached.value.receipt?.fallback) {
          const error = new Error(
            `Strict LLM evidence rejected fallback cache entry ${cacheKey}.`
          );
          error.providerReceipt = structuredClone(cached.value.receipt);
          error.evidenceOutcome = "quarantined";
          throw error;
        }
        return {
          decision: cached.value.decision,
          receipt: {
            ...cached.value.receipt,
            profileId: this.profile.id,
            cached: true,
            cacheKey,
            fallback: false
          }
        };
      }
      if (this.cacheMode === "read-only") {
        throw new Error(`Decision cache miss for ${cacheKey}.`);
      }
    } else if (this.decisionCache && this.cacheMode === "write-only") {
      cacheKey = this.decisionCache.key(cacheInput);
    }

    if (this.decisionBudget && this.decisionBudget.remaining <= 0) {
      return this.fallbackDecision(augmented, "LLM decision budget exhausted.");
    }
    if (this.decisionBudget?.maxPerSeatCycle) {
      const key = packet.requestId.replace(/^(.*:r\d+:c\d+:s\d+):.*$/, "$1");
      const used = this.decisionBudget.perSeatCycleUsage.get(key) || 0;
      if (used >= this.decisionBudget.maxPerSeatCycle) {
        throw new Error(
          `LLM prompt budget exhausted for ${key}: ` +
          `${used}/${this.decisionBudget.maxPerSeatCycle}.`
        );
      }
      this.decisionBudget.perSeatCycleUsage.set(key, used + 1);
    }
    if (this.decisionBudget) {
      this.decisionBudget.remaining -= 1;
      this.decisionBudget.used = (this.decisionBudget.used || 0) + 1;
    }

    try {
      const result = await this.caller.decide(augmented, { signal: this.signal });
      const completed = {
        ...result,
        receipt: {
          ...result.receipt,
          profileId: this.profile.id,
          cached: false,
          cacheKey,
          fallback: false
        }
      };
      if (
        this.decisionCache &&
        ["read-write", "write-only"].includes(this.cacheMode) &&
        cacheKey
      ) {
        await this.decisionCache.write(cacheKey, completed);
      }
      return completed;
    } catch (error) {
      throwIfAborted(this.signal);
      return this.fallbackDecision(
        augmented,
        error.message,
        error.providerReceipt || null
      );
    }
  }

  rulebookResponseDefault(packet, decision, reason, providerReceipt = null) {
    return {
      decision: { decisionId: decision.decisionId },
      receipt: {
        provider: "rulebook-default",
        profileId: this.profile.id,
        requestId: packet.requestId,
        fallback: true,
        fallbackReason: reason,
        formalResponseDefault: true,
        ...(providerReceipt || {})
      }
    };
  }

  async fallbackDecision(packet, reason, providerReceipt = null) {
    if (this.strictLlmEvidence) {
      const error = new Error(`Strict LLM decision failed: ${reason}`);
      error.providerReceipt = providerReceipt;
      error.evidenceOutcome = "quarantined";
      throw error;
    }
    const defaultResponse = formalResponseDefault(packet);
    if (defaultResponse) {
      return this.rulebookResponseDefault(packet, defaultResponse, reason, providerReceipt);
    }
    if (this.requireLlm) {
      const error = new Error(`Required LLM decision failed: ${reason}`);
      error.providerReceipt = providerReceipt;
      error.evidenceOutcome = "blocked";
      throw error;
    }
    if (!this.fallback) throw new Error(reason);
    const result = await this.fallback.decide(packet);
    return {
      ...result,
      receipt: {
        ...result.receipt,
        profileId: this.profile.id,
        fallback: true,
        fallbackReason: reason,
        ...(providerReceipt || {})
      }
    };
  }
}

export class HybridPlayerPolicy extends CliBackedPlayerPolicy {
  constructor(profile, caller, {
    fallback,
    decisionBudget,
    decisionCache,
    cacheMode,
    backendId,
    model,
    reasoningEffort,
    signal,
    requireLlm,
    strictLlmEvidence,
    llmStages,
    shortlistSize = 4
  } = {}) {
    super(profile, caller, {
      fallback,
      decisionBudget,
      decisionCache,
      cacheMode,
      backendId,
      model,
      reasoningEffort,
      signal,
      requireLlm,
      strictLlmEvidence,
      llmStages
    });
    this.shortlistSize = shortlistSize;
    this.kind = "hybrid";
  }

  async decide(packet) {
    const ranked = this.fallback.rank(packet);
    const shortlisted = {
      ...packet,
      legalDecisions: ranked
        .slice(0, this.shortlistSize)
        .map((entry) => entry.decision)
    };
    return super.decide(shortlisted);
  }
}
