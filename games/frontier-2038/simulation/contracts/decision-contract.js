function requireObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new TypeError(`${label} must be an object.`);
  }
}

function requireNonEmptyString(value, label) {
  if (typeof value !== "string" || value.length === 0) {
    throw new TypeError(`${label} must be a non-empty string.`);
  }
}

export function validateDecisionPacket(packet) {
  requireObject(packet, "Decision packet");
  if (![1, 2].includes(packet.schemaVersion)) {
    throw new TypeError("Decision packet schemaVersion must be 1 or 2.");
  }
  if (packet.schemaVersion === 2) {
    requireObject(packet.game, "Decision packet game");
    for (const key of [
      "version",
      "rulesetFingerprint",
      "engineFingerprint",
      "variantFingerprint"
    ]) {
      requireNonEmptyString(packet.game[key], `Decision packet game ${key}`);
    }
  }

  for (const key of ["requestId", "matchId", "seed", "factionId"]) {
    requireNonEmptyString(packet[key], `Decision packet ${key}`);
  }
  if (!Number.isInteger(packet.seat) || packet.seat < 0) {
    throw new TypeError("Decision packet seat must be a non-negative integer.");
  }
  if (!Number.isInteger(packet.round) || packet.round < 1 || packet.round > 4) {
    throw new TypeError("Decision packet round must be an integer from 1 to 4.");
  }
  if (!Number.isInteger(packet.cycle) || packet.cycle < 1 || packet.cycle > 3) {
    throw new TypeError("Decision packet cycle must be an integer from 1 to 3.");
  }
  requireObject(packet.observation, "Decision packet observation");
  if (!Array.isArray(packet.legalDecisions) || packet.legalDecisions.length === 0) {
    throw new TypeError("Decision packet must enumerate at least one legal decision.");
  }

  const ids = new Set();
  for (const [index, decision] of packet.legalDecisions.entries()) {
    requireObject(decision, `Legal decision ${index}`);
    requireNonEmptyString(decision.decisionId, `Legal decision ${index} decisionId`);
    requireNonEmptyString(decision.label, `Legal decision ${index} label`);
    if (ids.has(decision.decisionId)) {
      throw new TypeError(`Duplicate legal decisionId: ${decision.decisionId}.`);
    }
    ids.add(decision.decisionId);
  }

  JSON.stringify(packet);
  return packet;
}

export function validateDecisionResponse(packet, response) {
  validateDecisionPacket(packet);
  requireObject(response, "Decision response");
  requireNonEmptyString(response.decisionId, "Decision response decisionId");

  const legal = packet.legalDecisions.some(
    (decision) => decision.decisionId === response.decisionId
  );
  if (!legal) {
    throw new TypeError(`Provider selected illegal decisionId: ${response.decisionId}.`);
  }
  if (
    response.rationale !== undefined &&
    response.rationale !== null &&
    typeof response.rationale !== "string"
  ) {
    throw new TypeError("Decision response rationale must be a string.");
  }
  if (
    response.confidence !== undefined &&
    response.confidence !== null &&
    (typeof response.confidence !== "number" ||
      response.confidence < 0 ||
      response.confidence > 1)
  ) {
    throw new TypeError("Decision response confidence must be between 0 and 1.");
  }

  return {
    decisionId: response.decisionId,
    ...(typeof response.rationale === "string"
      ? { rationale: response.rationale }
      : {}),
    ...(typeof response.confidence === "number"
      ? { confidence: response.confidence }
      : {})
  };
}

export function buildDecisionPrompt(packet) {
  validateDecisionPacket(packet);
  return [
    "You are a player-policy function for M3T4 2038.",
    "Choose exactly one decisionId from legalDecisions.",
    "Use only the supplied observation, public history, and strategy.",
    "The game identity fingerprints define the exact rules and engine for this decision.",
    "Do not use tools, inspect files, execute commands, or invent unavailable information.",
    "Return only the JSON object required by the response schema.",
    "",
    "DECISION_PACKET",
    JSON.stringify(packet)
  ].join("\n");
}
