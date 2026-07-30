import { readFile } from "node:fs/promises";
import { loadPlayerProfiles } from "../personas/player-profile.js";
import { createPlayerPolicy } from "../policies/policy-factory.js";
import { createInteractiveGameCore } from "./interactive-game-core.js";

const readJson = (path) => readFile(
  new URL(`../../data/${path}`, import.meta.url),
  "utf8"
).then(JSON.parse);
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
  return createInteractiveGameCore({
    documents: {
      config,
      factions,
      headlines,
      wildActions,
      tactics,
      mandates,
      objectives,
      profiles
    },
    options,
    onPending,
    policyFactory: createPlayerPolicy
  });
}

export { HumanPlayerPolicy } from "./interactive-game-core.js";
