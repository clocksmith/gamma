import { validateDecisionPacket } from "../contracts/decision-contract.js";
import { profileForPrompt, validatePlayerProfile } from "../personas/player-profile.js";

export class CliBackedPlayerPolicy {
  constructor(profile, caller, {
    fallback,
    decisionBudget,
    decisionCache,
    cacheMode = "off",
    backendId,
    model,
    reasoningEffort,
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
    this.llmStages = llmStages || null;
    this.kind = "llm";
  }

  async decide(packet) {
    validateDecisionPacket(packet);
    const augmented = {
      ...packet,
      strategy: profileForPrompt(this.profile)
    };
    if (
      this.llmStages?.length &&
      !this.llmStages.some((stage) => packet.requestId.includes(`:${stage}`))
    ) {
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
      packet: augmented,
      profile: profileForPrompt(this.profile)
    };
    if (this.decisionCache && ["read-write", "read-only"].includes(this.cacheMode)) {
      const cached = await this.decisionCache.read(cacheInput);
      cacheKey = cached.key;
      if (cached.value) {
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
    if (this.decisionBudget) this.decisionBudget.remaining -= 1;

    try {
      const result = await this.caller.decide(augmented);
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
      return this.fallbackDecision(
        augmented,
        error.message,
        error.providerReceipt || null
      );
    }
  }

  async fallbackDecision(packet, reason, providerReceipt = null) {
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
