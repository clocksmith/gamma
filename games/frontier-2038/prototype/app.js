import {
  apiFetch,
  bridgeRequired,
  connectBridge,
  getBridgeToken
} from "./api-client.js";
import { createBrowserInteractiveGame } from "../simulation/runtime/create-browser-interactive-game.js";

const [factions, config, profilesDocument] = await Promise.all([
  fetch("/data/factions.json").then((response) => response.json()),
  fetch("/data/game-config.json").then((response) => response.json()),
  fetch("/data/player-strategies.json").then((response) => response.json())
]);
const profiles = profilesDocument.profiles;

const $ = (id) => document.getElementById(id);
const elements = Object.fromEntries([
  "allow-llm", "board", "bridge-panel", "bridge-status", "bridge-token",
  "connect-bridge", "decision-context", "decision-count", "decision-title",
  "decisions", "export", "faction", "game-status", "headline-name",
  "headline-text", "log", "max-llm-decisions", "model", "opponent-config",
  "phase", "player-count", "players", "round-title", "seed", "start-game"
].map((id) => [id, $(id)]));

for (const faction of factions.factions) {
  elements.faction.add(new Option(`${faction.name} — ${faction.motto}`, faction.id));
}

let game = null;
let pollTimer = null;
let bridgeConnected = !bridgeRequired;
let renderedTileStates = new Map();
const llmBackends = new Set([
  "claude",
  "codex",
  "hybrid-claude",
  "hybrid-codex"
]);

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function backendOptions() {
  return [
    ["weighted", "Weighted deterministic"],
    ["greedy", "Greedy deterministic"],
    ["claude", "Claude CLI"],
    ["codex", "Codex CLI"],
    ["hybrid-claude", "Hybrid · weighted + Claude"],
    ["hybrid-codex", "Hybrid · weighted + Codex"]
  ];
}

function renderOpponents() {
  const count = Number(elements["player-count"].value) - 1;
  elements["opponent-config"].replaceChildren();
  for (let index = 0; index < count; index += 1) {
    const profile = profiles[(index + 1) % profiles.length];
    const row = document.createElement("div");
    row.className = "opponent-row";
    row.dataset.seat = index + 1;
    row.innerHTML = `
      <strong>Seat ${index + 2}</strong>
      <select class="profile-select" aria-label="Seat ${index + 2} persona">
        ${profiles.map((candidate) => `
          <option value="${escapeHtml(candidate.id)}" ${
            candidate.id === profile.id ? "selected" : ""
          }>${escapeHtml(candidate.name)}</option>
        `).join("")}
      </select>
      <select class="backend-select" aria-label="Seat ${index + 2} decision backend">
        ${backendOptions().map(([value, label]) =>
          `<option value="${value}">${escapeHtml(label)}</option>`
        ).join("")}
      </select>
      <p class="persona-summary">${escapeHtml(profile.persona.identity)}</p>
    `;
    row.querySelector(".profile-select").addEventListener("change", (event) => {
      const selected = profiles.find((candidate) => candidate.id === event.target.value);
      row.querySelector(".persona-summary").textContent = selected.persona.identity;
    });
    row.querySelector(".backend-select").addEventListener(
      "change",
      updateStartAvailability
    );
    elements["opponent-config"].append(row);
  }
  updateStartAvailability();
}

function selectedBackends() {
  return [...elements["opponent-config"].querySelectorAll(".backend-select")]
    .map((select) => select.value);
}

function llmRequested() {
  return selectedBackends().some((backend) => llmBackends.has(backend));
}

function opponentOptions() {
  const rows = [...elements["opponent-config"].querySelectorAll(".opponent-row")];
  return {
    opponentProfileIds: rows.map((row) =>
      row.querySelector(".profile-select").value
    ),
    opponentBackends: rows.map((row) =>
      row.querySelector(".backend-select").value
    ),
    allowLlm: elements["allow-llm"].checked,
    maxLlmDecisions: Number(elements["max-llm-decisions"].value),
    model: elements.model.value || undefined
  };
}

function updateStartAvailability() {
  const needsLlm = llmRequested();
  const needsRemoteBridge = needsLlm && bridgeRequired;
  elements["bridge-panel"].hidden = !needsRemoteBridge;
  elements["start-game"].disabled = Boolean(
    needsLlm && (!elements["allow-llm"].checked || !bridgeConnected)
  );
}

function showBridgeState(message, connected = false) {
  elements["bridge-status"].textContent = message;
  elements["bridge-status"].classList.toggle("connected", connected);
}

function tilePosition(tile) {
  const size = window.innerWidth <= 680 ? 92 : 120;
  const width = size * 0.78;
  const height = size * 0.89;
  const originX = window.innerWidth <= 680 ? 250 : 410;
  const originY = window.innerWidth <= 680 ? 240 : 285;
  return {
    left: originX + width * (tile.q + tile.r / 2) - size / 2,
    top: originY + height * tile.r - size * 0.44
  };
}

function markerKey(player, type, marker, index) {
  return `${player.seat}:${type}:${marker.id || marker.sourceId || marker.tileId || index}`;
}

function markerState(tile, players) {
  const markers = [];
  for (const player of players) {
    for (const [index, piece] of player.pieces.entries()) {
      if (piece.tileId !== tile.instanceId) continue;
      markers.push({
        key: markerKey(player, "piece", piece, index),
        signature: `piece:${piece.kind}`
      });
    }
    for (const [index, facility] of player.facilities.entries()) {
      if (facility.tileId !== tile.instanceId) continue;
      markers.push({
        key: markerKey(player, "facility", facility, index),
        signature: `facility:${facility.powered}:${facility.gridReady}`
      });
    }
    for (const [index, generator] of player.generators.entries()) {
      if (generator.tileId !== tile.instanceId) continue;
      markers.push({
        key: markerKey(player, "generator", generator, index),
        signature: `generator:${generator.sourceId}`
      });
    }
  }
  return markers;
}

function tileSignature(tile, markers) {
  const position = `${tile.instanceId}:${tile.name}:${tile.category}:${tile.q}:${tile.r}`;
  return `${position}|${markers.map((marker) => `${marker.key}:${marker.signature}`).sort().join("|")}`;
}

function contentsForTile(tile, players, priorMarkerKeys = new Set()) {
  const marks = [];
  for (const player of players) {
    for (const [index, piece] of player.pieces.entries()) {
      if (piece.tileId !== tile.instanceId) continue;
      const arrivalClass = priorMarkerKeys.has(markerKey(player, "piece", piece, index)) ? "" : " arrival";
      marks.push(`<i class="dot ${piece.kind}${arrivalClass}" style="--seat:${player.seat}" ` +
        `title="${escapeHtml(player.factionName)} ${piece.kind}"></i>`);
    }
    for (const [index, facility] of player.facilities.entries()) {
      if (facility.tileId !== tile.instanceId) continue;
      const arrivalClass = priorMarkerKeys.has(markerKey(player, "facility", facility, index)) ? "" : " arrival";
      const status = facility.gridReady
        ? "Grid-Ready"
        : facility.powered ? "powered this Production" : "offline";
      marks.push(`<i class="dot facility ${facility.powered ? "powered" : "offline"}${arrivalClass} ` +
        `${facility.gridReady ? "grid-ready" : ""}" style="--seat:${player.seat}" ` +
        `title="${escapeHtml(player.factionName)} Facility — ${status}"></i>`);
    }
    for (const [index, generator] of player.generators.entries()) {
      if (generator.tileId !== tile.instanceId) continue;
      const arrivalClass = priorMarkerKeys.has(markerKey(player, "generator", generator, index)) ? "" : " arrival";
      marks.push(`<i class="dot generator${arrivalClass}" style="--seat:${player.seat}" ` +
        `title="${escapeHtml(player.factionName)} ${escapeHtml(generator.sourceId)}"></i>`);
    }
  }
  return marks.join("");
}

function renderBoard(state) {
  elements.board.replaceChildren();
  if (!state) {
    renderedTileStates = new Map();
    return;
  }
  const nextTileStates = new Map();
  const hasPriorBoard = renderedTileStates.size > 0;
  for (const tile of state.board) {
    const hex = document.createElement("div");
    const position = tilePosition(tile);
    const markers = markerState(tile, state.players);
    const signature = tileSignature(tile, markers);
    const priorState = renderedTileStates.get(tile.instanceId);
    const changed = hasPriorBoard && priorState?.signature !== signature;
    nextTileStates.set(tile.instanceId, {
      signature,
      markerKeys: new Set(markers.map((marker) => marker.key))
    });
    hex.className = `hex ${tile.category}${changed ? " state-shift" : ""}`;
    hex.style.left = `${position.left}px`;
    hex.style.top = `${position.top}px`;
    hex.innerHTML = `
      <span class="hex-name">${escapeHtml(tile.name)}</span>
      <span class="hex-type">${escapeHtml(tile.category)}</span>
      <span class="hex-pieces">${contentsForTile(tile, state.players, hasPriorBoard ? priorState?.markerKeys : undefined)}</span>
    `;
    elements.board.append(hex);
  }
  renderedTileStates = nextTileStates;
}

function resetBoardTransitions() {
  renderedTileStates = new Map();
}

function renderPlayers(state) {
  elements.players.replaceChildren();
  if (!state) return;
  for (const player of state.players) {
    const opponent = game?.opponents?.find((candidate) =>
      candidate.seat === player.seat
    );
    const card = document.createElement("article");
    card.className = `public-player ${player.seat === 0 ? "human" : ""}`;
    card.style.setProperty("--seat", player.seat);
    card.innerHTML = `
      <p class="eyebrow">Seat ${player.seat + 1}${player.seat === 0 ? " · you" : ""}</p>
      <h3>${escapeHtml(player.factionName)}</h3>
      ${opponent ? `<p class="readiness">${
        escapeHtml(opponent.profileName)
      } · ${escapeHtml(opponent.backend)}${
        opponent.remainingLlmDecisions === null
          ? ""
          : ` · ${opponent.remainingLlmDecisions} LLM calls left`
      }</p>` : ""}
      <p class="readiness ${player.agiReadiness.ready ? "ready" : ""}">
        AGI ${player.agiReadiness.ready
          ? "grid-ready"
          : `blocked: ${escapeHtml(player.agiReadiness.failingRequirement)}`}
      </p>
      <dl>
        <dt>Mandate</dt><dd>${player.mandate}</dd>
        <dt>Runway</dt><dd>${player.runway}</dd>
        <dt>Compute</dt><dd>${player.compute}</dd>
        <dt>Capability</dt><dd>${player.capability}</dd>
        <dt>Customers</dt><dd>${player.customers}</dd>
        <dt>Trust</dt><dd>${player.trust}</dd>
        <dt>Scrutiny</dt><dd>${player.scrutiny}</dd>
        <dt>Grid-Ready</dt><dd>${player.agiReadiness.gridReadyFacilities}</dd>
      </dl>
    `;
    elements.players.append(card);
  }
}

function decisionStage(packet) {
  const stage = packet?.requestId?.split(":").at(-2) || "decision";
  return stage.replaceAll("_", " ");
}

function syncClientGame(clientGame = game) {
  if (clientGame?.executionMode !== "client" || !clientGame.runtime) return;
  clientGame.state = clientGame.runtime.match.snapshot();
  clientGame.replay = clientGame.runtime.match.replay || [];
  clientGame.opponents = clientGame.runtime.opponents.map((opponent) => ({
    seat: opponent.seat,
    profileId: opponent.profile.id,
    profileName: opponent.profile.name,
    backend: opponent.backend,
    remainingLlmDecisions: null
  }));
  clientGame.updatedAt = Date.now();
}

async function startClientGame(options) {
  const clientGame = {
    id: crypto.randomUUID(),
    executionMode: "client",
    status: "starting",
    pending: null,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    state: null,
    replay: [],
    opponents: [],
    result: null,
    error: null
  };
  clientGame.runtime = await createBrowserInteractiveGame(options, (packet) => {
    clientGame.pending = packet;
    clientGame.status = "waiting";
    syncClientGame(clientGame);
    if (game === clientGame) render();
  });
  game = clientGame;
  clientGame.status = "running";
  syncClientGame(clientGame);
  clientGame.execution = clientGame.runtime.match.play(clientGame.runtime.policies)
    .then((result) => {
      clientGame.result = result;
      clientGame.pending = null;
      clientGame.status = "complete";
      syncClientGame(clientGame);
      if (game === clientGame) render();
    })
    .catch((error) => {
      clientGame.pending = null;
      clientGame.status = "failed";
      clientGame.error = error.message;
      syncClientGame(clientGame);
      if (game === clientGame) render();
    });
  render();
}

async function submitDecision(decisionId) {
  const packet = game.pending;
  elements.decisions.querySelectorAll("button").forEach((button) => {
    button.disabled = true;
  });
  if (game.executionMode === "client") {
    game.runtime.human.submit(decisionId);
    game.pending = null;
    game.status = "running";
    syncClientGame();
    render();
    return;
  }
  const response = await apiFetch(`/api/games/${game.id}/decisions`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ requestId: packet.requestId, decisionId })
  });
  const next = await response.json();
  if (!response.ok) throw new Error(next.error || "Decision failed.");
  game = next;
  render();
  schedulePoll();
}

function renderDecisions() {
  elements.decisions.replaceChildren();
  const packet = game?.pending;
  if (!packet) {
    elements["decision-title"].textContent = game?.status === "complete"
      ? `Game complete · ${game.result.worldEnding.name}`
      : game ? "Other institutions are resolving" : "Start a game";
    elements["decision-context"].textContent = game?.status === "complete"
      ? "Read the Future Timeline in the ledger, then compare the institutional winner with the shared ending."
      : "The authoritative engine will pause here for your next legal decision.";
    elements["decision-count"].textContent = "0 legal choices";
    return;
  }
  elements["decision-title"].textContent = decisionStage(packet);
  elements["decision-context"].textContent =
    `Round ${packet.round}, cycle ${packet.cycle}. Choose one enumerated legal result; ` +
    "the engine validates it before play resumes.";
  elements["decision-count"].textContent =
    `${packet.legalDecisions.length} legal choice${packet.legalDecisions.length === 1 ? "" : "s"}`;
  for (const [index, decision] of packet.legalDecisions.entries()) {
    const button = document.createElement("button");
    button.className = "decision-card";
    button.style.setProperty("--card-index", index);
    button.innerHTML = `
      <strong>${escapeHtml(decision.label)}</strong>
      <small>${escapeHtml(decision.actionId || "decision")}</small>
    `;
    button.addEventListener("click", () => {
      submitDecision(decision.decisionId).catch((error) => {
        elements["game-status"].textContent = error.message;
        renderDecisions();
      });
    });
    elements.decisions.append(button);
  }
}

function renderLedger() {
  const replay = game?.replay || [];
  elements.log.innerHTML = replay.slice().reverse().map((event, index) =>
    `<li class="${index === 0 ? "latest-event" : ""}"><strong>R${event.round}C${event.cycle}</strong> ${escapeHtml(event.summary)}</li>`
  ).join("");
}

function render() {
  const state = game?.state;
  elements.phase.textContent = game?.status || "ready";
  elements["game-status"].textContent = game?.error ||
    (game ? `${
      game.executionMode === "client" ? "Browser-native" : "Local bridge"
    } game ${game.id.slice(0, 8)} · ${game.status}` :
      config.board.prototypeNote);
  elements["round-title"].textContent = state
    ? `Round ${state.round} · cycle ${state.cycle}`
    : "The board";
  const headline = state?.activeHeadline;
  elements["headline-name"].textContent = headline?.name || "Not revealed";
  elements["headline-text"].textContent = headline
    ? "Its complete mechanical effect is active in the match and preserved in the Future Timeline."
    : "";
  elements.export.disabled = !game;
  renderBoard(state);
  renderPlayers(state);
  renderDecisions();
  renderLedger();
}

async function refresh() {
  if (!game || ["complete", "failed"].includes(game.status)) return;
  const response = await apiFetch(`/api/games/${game.id}`);
  const next = await response.json();
  if (!response.ok) throw new Error(next.error || "Could not read the game.");
  game = next;
  render();
  if (!["complete", "failed", "waiting"].includes(game.status)) schedulePoll();
}

function schedulePoll() {
  clearTimeout(pollTimer);
  if (game?.executionMode === "client") return;
  pollTimer = setTimeout(() => {
    refresh().catch((error) => {
      elements["game-status"].textContent = error.message;
    });
  }, 120);
}

elements["start-game"].addEventListener("click", async () => {
  clearTimeout(pollTimer);
  elements["start-game"].disabled = true;
  resetBoardTransitions();
  try {
    const opponents = opponentOptions();
    const options = {
      factionId: elements.faction.value,
      playerCount: Number(elements["player-count"].value),
      seed: elements.seed.value,
      ...opponents
    };
    if (!opponents.opponentBackends.some((backend) => llmBackends.has(backend))) {
      await startClientGame(options);
      return;
    }
    const response = await apiFetch("/api/games", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(options)
    });
    game = await response.json();
    game.executionMode = "server";
    if (!response.ok) throw new Error(game.error || "Could not start game.");
    render();
    schedulePoll();
  } catch (error) {
    elements["game-status"].textContent = error.message;
  } finally {
    updateStartAvailability();
  }
});

elements["player-count"].addEventListener("change", renderOpponents);

if (bridgeRequired) {
  elements["bridge-token"].value = getBridgeToken();
  bridgeConnected = false;
  showBridgeState("Optional · required only for Claude, Codex, or hybrid opponents.");
  elements["connect-bridge"].addEventListener("click", async () => {
    elements["connect-bridge"].disabled = true;
    showBridgeState("Requesting access to the local bridge…");
    try {
      const status = await connectBridge(elements["bridge-token"].value);
      bridgeConnected = true;
      showBridgeState(
        `Connected · ${status.maximumLlmDecisionsPerOpponent} maximum LLM decisions per opponent.`,
        true
      );
    } catch (error) {
      bridgeConnected = false;
      showBridgeState(error.message);
    } finally {
      elements["connect-bridge"].disabled = false;
      updateStartAvailability();
    }
  });
}

elements["allow-llm"].addEventListener("change", updateStartAvailability);

elements.export.addEventListener("click", () => {
  if (!game) return;
  syncClientGame();
  const receipt = game.executionMode === "client"
    ? {
        id: game.id,
        executionMode: game.executionMode,
        status: game.status,
        createdAt: game.createdAt,
        updatedAt: game.updatedAt,
        pending: game.pending,
        state: game.state,
        replay: game.replay,
        opponents: game.opponents,
        result: game.result,
        error: game.error
      }
    : game;
  const blob = new Blob(
    [JSON.stringify(receipt, null, 2)],
    { type: "application/json" }
  );
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `frontier-2038-${game.id}-game.json`;
  link.click();
  URL.revokeObjectURL(link.href);
});

window.addEventListener("resize", () => renderBoard(game?.state));
renderOpponents();
updateStartAvailability();
render();
