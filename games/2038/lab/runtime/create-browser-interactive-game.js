import { loadPlayerProfiles } from "../personas/player-profile.js";
import { WeightedPlayerPolicy } from "../policies/weighted-policy.js";
import {
  createInteractiveGameCore,
  deterministicInteractiveBackends
} from "./interactive-game-core.js";

const dataUrl = (path) => new URL(`../../dist/runtime/${path}`, import.meta.url);

async function readJson(path) {
  const url = dataUrl(path);
  if (url.protocol === "file:") {
    const { readFile } = await import("node:fs/promises");
    return JSON.parse(await readFile(url, "utf8"));
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Could not load ${path}: ${response.status}.`);
  }
  return response.json();
}

export async function createBrowserInteractiveGame(options = {}, onPending) {
  const [
    config,
    factions,
    headlines,
    projects,
    mandates,
    profiles
  ] = await Promise.all([
    readJson("game-config.json"),
    readJson("factions.json"),
    readJson("headlines.json"),
    readJson("projects.json"),
    readJson("mandates.json"),
    loadPlayerProfiles()
  ]);
  return createInteractiveGameCore({
    documents: {
      config,
      factions,
      headlines,
      projects,
      tactics: { schemaVersion: 1, copiesPerCard: 0, tactics: [] },
      mandates,
      objectives: { schemaVersion: 1, objectives: [] },
      profiles
    },
    options,
    onPending,
    policyFactory(profile, backend, policyOptions = {}) {
      if (!deterministicInteractiveBackends.has(backend)) {
        throw new Error(
          `Browser-native play supports weighted and greedy opponents; ${backend} requires the optional local bridge.`
        );
      }
      return new WeightedPlayerPolicy(profile, {
        selection: backend,
        rosterProfileIds: policyOptions.rosterProfileIds
      });
    }
  });
}
