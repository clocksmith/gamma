import { readFile } from "node:fs/promises";
import { SelectedRulesMatch } from "../environment/selected-rules-match.js";
import { validateDecisionResponse } from "../contracts/decision-contract.js";
import { loadPlayerProfiles } from "../personas/player-profile.js";
import { createPlayerPolicy } from "../policies/policy-factory.js";

const readJson = (path) => readFile(
  new URL(`../../data/${path}`, import.meta.url),
  "utf8"
).then(JSON.parse);

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
  const selectedProfiles = [
    humanProfile,
    ...Array.from({ length: playerCount - 1 }, (_, index) =>
      profiles[(index + 1) % profiles.length]
    )
  ];
  const human = new HumanPlayerPolicy(onPending);
  const policies = [
    human,
    ...selectedProfiles.slice(1).map((profile) =>
      createPlayerPolicy(profile, options.aiBackend || "weighted")
    )
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
  return { match, policies, human, config, factions };
}
