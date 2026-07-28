import { readFile } from "node:fs/promises";
import { SelectedRulesMatch } from "../environment/selected-rules-match.js";
import { validateDecisionResponse } from "../contracts/decision-contract.js";
import { loadPlayerProfiles } from "../personas/player-profile.js";
import { createPlayerPolicy } from "../policies/policy-factory.js";

const readJson = (path) => readFile(
  new URL(`../../data/${path}`, import.meta.url),
  "utf8"
).then(JSON.parse);
const interactiveBackends = new Set([
  "weighted",
  "greedy",
  "claude",
  "codex",
  "hybrid-claude",
  "hybrid-codex"
]);
const llmBackends = new Set([
  "claude",
  "codex",
  "hybrid-claude",
  "hybrid-codex"
]);
const maximumLlmDecisionsPerOpponent = 24;

function boundedInteger(value, fallback, minimum, maximum, label) {
  const resolved = value === undefined ? fallback : Number(value);
  if (
    !Number.isInteger(resolved) ||
    resolved < minimum ||
    resolved > maximum
  ) {
    throw new RangeError(`${label} must be an integer from ${minimum} to ${maximum}.`);
  }
  return resolved;
}

export class HumanPlayerPolicy {
  constructor(onPending) {
    this.kind = "human";
    this.onPending = onPending;
    this.pending = null;
  }

  async decide(packet) {
    if (this.pending) throw new Error("A human decision is already pending.");
    return new Promise((resolve, reject) => {
      this.pending = { packet, resolve, reject };
      this.onPending(packet);
    });
  }

  submit(decisionId, rationale = "Selected by the human player.") {
    if (!this.pending) throw new Error("No human decision is pending.");
    const { packet, resolve } = this.pending;
    const decision = validateDecisionResponse(packet, { decisionId, rationale });
    this.pending = null;
    resolve({
      decision,
      receipt: {
        provider: "human-browser",
        profileId: "human",
        requestId: packet.requestId
      }
    });
    return packet.requestId;
  }
}

export async function createInteractiveGame(options = {}, onPending) {
  const [
    config,
    factions,
    headlines,
    wildActions,
    tactics,
    mandates,
    objectives,
    profiles
  ] = await Promise.all([
    readJson("game-config.json"),
    readJson("factions.json"),
    readJson("headlines.json"),
    readJson("wild-actions.json"),
    readJson("tactics.json"),
    readJson("mandates.json"),
    readJson("secret-objectives.json"),
    loadPlayerProfiles()
  ]);
  const playerCount = Number(options.playerCount ?? config.players.balanceAuthority);
  if (
    !Number.isInteger(playerCount) ||
    !config.players.supportedCounts.includes(playerCount)
  ) {
    throw new RangeError(
      `playerCount must be one of ${config.players.supportedCounts.join(", ")}.`
    );
  }
  const selectedFaction = factions.factions.find(
    (faction) => faction.id === options.factionId
  ) || factions.factions[0];
  const roster = [
    selectedFaction,
    ...factions.factions.filter((faction) => faction.id !== selectedFaction.id)
  ].slice(0, playerCount);
  const humanProfile = {
    ...structuredClone(profiles[0]),
    id: "human",
    name: "Human player"
  };
  const requestedProfileIds = Array.isArray(options.opponentProfileIds)
    ? options.opponentProfileIds
    : [];
  const requestedBackends = Array.isArray(options.opponentBackends)
    ? options.opponentBackends
    : [];
  if (requestedProfileIds.length > playerCount - 1) {
    throw new RangeError("opponentProfileIds cannot exceed the number of opponent seats.");
  }
  if (requestedBackends.length > playerCount - 1) {
    throw new RangeError("opponentBackends cannot exceed the number of opponent seats.");
  }
  const opponentProfiles = Array.from({ length: playerCount - 1 }, (_, index) => {
    const id = requestedProfileIds[index];
    if (!id) return profiles[(index + 1) % profiles.length];
    const profile = profiles.find((candidate) => candidate.id === id);
    if (!profile) throw new TypeError(`Unknown opponent profile: ${id}.`);
    return profile;
  });
  const opponentBackends = Array.from({ length: playerCount - 1 }, (_, index) =>
    requestedBackends[index] || options.aiBackend || "weighted"
  );
  for (const backend of opponentBackends) {
    if (!interactiveBackends.has(backend)) {
      throw new TypeError(`Unknown interactive opponent backend: ${backend}.`);
    }
  }
  const llmRequested = opponentBackends.some((backend) => llmBackends.has(backend));
  if (llmRequested && !options.allowLlm) {
    throw new Error("LLM-backed opponents require explicit allowLlm authorization.");
  }
  const maxLlmDecisions = boundedInteger(
    options.maxLlmDecisions,
    llmRequested ? 12 : 0,
    0,
    maximumLlmDecisionsPerOpponent,
    "maxLlmDecisions"
  );
  if (llmRequested && maxLlmDecisions === 0) {
    throw new RangeError("LLM-backed opponents require at least one authorized decision.");
  }
  const selectedProfiles = [humanProfile, ...opponentProfiles];
  const human = new HumanPlayerPolicy(onPending);
  const opponents = opponentProfiles.map((profile, index) => {
    const backend = opponentBackends[index];
    const decisionBudget = llmBackends.has(backend)
      ? { remaining: maxLlmDecisions }
      : null;
    return {
      seat: index + 1,
      profile,
      backend,
      decisionBudget,
      policy: createPlayerPolicy(profile, backend, {
        allowLlm: Boolean(options.allowLlm),
        decisionBudget,
        model: options.model,
        timeoutMs: options.timeoutMs,
        shortlistSize: options.shortlistSize,
        llmStages: options.llmStages
      })
    };
  });
  const policies = [
    human,
    ...opponents.map((opponent) => opponent.policy)
  ];
  const match = new SelectedRulesMatch({
    config,
    factions: roster,
    profiles: selectedProfiles,
    headlines,
    wildActions,
    tactics,
    mandates,
    objectives,
    seed: String(options.seed || "frontier-interactive"),
    playerCount,
    recordReplay: true,
    rulesVariant: options.rulesVariant || {}
  });
  return {
    match,
    policies,
    human,
    config,
    factions,
    opponents,
    maximumLlmDecisionsPerOpponent
  };
}
