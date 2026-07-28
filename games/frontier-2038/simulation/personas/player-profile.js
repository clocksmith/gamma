import { readFile } from "node:fs/promises";

export const defaultProfilesUrl = new URL("../../data/player-strategies.json", import.meta.url);

function requireObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new TypeError(`${label} must be an object.`);
  }
}

export function validatePlayerProfile(profile) {
  requireObject(profile, "Player profile");
  if (!/^[a-z0-9_]+$/.test(profile.id || "")) {
    throw new TypeError("Player profile id must use lowercase letters, numbers, and underscores.");
  }
  if (typeof profile.name !== "string" || profile.name.length === 0) {
    throw new TypeError(`Player profile ${profile.id} requires a name.`);
  }
  requireObject(profile.persona, `Player profile ${profile.id} persona`);
  for (const field of ["identity", "worldview", "riskPosture", "negotiationStyle"]) {
    if (typeof profile.persona[field] !== "string" || profile.persona[field].length === 0) {
      throw new TypeError(`Player profile ${profile.id} persona requires ${field}.`);
    }
  }
  requireObject(profile.strategy, `Player profile ${profile.id} strategy`);
  if (!["weighted", "greedy"].includes(profile.strategy.selection)) {
    throw new TypeError(`Player profile ${profile.id} has an invalid selection mode.`);
  }
  requireObject(profile.strategy.actionWeights, `Player profile ${profile.id} actionWeights`);
  requireObject(profile.strategy.negotiation, `Player profile ${profile.id} negotiation`);
  for (const field of [
    "promiseWeight",
    "fulfillWeight",
    "betrayWeight",
    "reciprocityWeight"
  ]) {
    if (!(profile.strategy.negotiation[field] >= 0)) {
      throw new TypeError(`Player profile ${profile.id} negotiation requires ${field}.`);
    }
  }
  if (!Array.isArray(profile.strategy.rules)) {
    throw new TypeError(`Player profile ${profile.id} rules must be an array.`);
  }
  for (const [actionId, weight] of Object.entries(profile.strategy.actionWeights)) {
    if (!(weight > 0)) {
      throw new TypeError(`Player profile ${profile.id} weight for ${actionId} must be positive.`);
    }
  }
  if (profile.strategy.partnerWeights !== undefined) {
    requireObject(profile.strategy.partnerWeights, `Player profile ${profile.id} partnerWeights`);
    for (const [partnerId, weight] of Object.entries(profile.strategy.partnerWeights)) {
      if (!(weight > 0)) {
        throw new TypeError(
          `Player profile ${profile.id} partner weight for ${partnerId} must be positive.`
        );
      }
    }
  }
  if (profile.strategy.consequenceWeights !== undefined) {
    requireObject(
      profile.strategy.consequenceWeights,
      `Player profile ${profile.id} consequenceWeights`
    );
    for (const [consequence, weight] of Object.entries(
      profile.strategy.consequenceWeights
    )) {
      if (!Number.isFinite(weight)) {
        throw new TypeError(
          `Player profile ${profile.id} consequence weight for ${consequence} must be finite.`
        );
      }
    }
  }
  if (profile.strategy.spatialPreference !== undefined) {
    requireObject(
      profile.strategy.spatialPreference,
      `Player profile ${profile.id} spatialPreference`
    );
    const preference = profile.strategy.spatialPreference;
    if (
      typeof preference.targetProfileId !== "string" ||
      !Number.isInteger(preference.preferredDistance) ||
      preference.preferredDistance < 0 ||
      !(preference.multiplier > 1)
    ) {
      throw new TypeError(
        `Player profile ${profile.id} has an invalid spatialPreference.`
      );
    }
  }
  return profile;
}

export async function loadPlayerProfiles(source = defaultProfilesUrl) {
  const document = JSON.parse(await readFile(source, "utf8"));
  if (document.schemaVersion !== 1 || !Array.isArray(document.profiles)) {
    throw new TypeError("Player strategy document must use schemaVersion 1 and contain profiles.");
  }
  const profiles = document.profiles.map(validatePlayerProfile);
  if (new Set(profiles.map((profile) => profile.id)).size !== profiles.length) {
    throw new TypeError("Player profile ids must be unique.");
  }
  return profiles;
}

export function profileForPrompt(profile) {
  validatePlayerProfile(profile);
  return {
    id: profile.id,
    name: profile.name,
    description: profile.description || "",
    persona: profile.persona,
    objectives: profile.strategy.objectives || [],
    operatingRules: profile.strategy.rules
  };
}
