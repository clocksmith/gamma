const [factions, config] = await Promise.all([
  fetch("/data/factions.json").then((response) => response.json()),
  fetch("/data/game-config.json").then((response) => response.json())
]);

const $ = (id) => document.getElementById(id);
const elements = Object.fromEntries([
  "board", "decision-context", "decision-count", "decision-title", "decisions",
  "export", "faction", "game-status", "headline-name", "headline-text", "log",
  "phase", "player-count", "players", "round-title", "seed", "start-game"
].map((id) => [id, $(id)]));

for (const faction of factions.factions) {
  elements.faction.add(new Option(`${faction.name} — ${faction.motto}`, faction.id));
}

let game = null;
let pollTimer = null;

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
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

function contentsForTile(tile, players) {
  const marks = [];
  for (const player of players) {
    for (const piece of player.pieces.filter((item) => item.tileId === tile.instanceId)) {
      marks.push(`<i class="dot ${piece.kind}" style="--seat:${player.seat}" ` +
        `title="${escapeHtml(player.factionName)} ${piece.kind}"></i>`);
    }
    for (const facility of player.facilities.filter((item) => item.tileId === tile.instanceId)) {
      const status = facility.gridReady
        ? "Grid-Ready"
        : facility.powered ? "powered this Production" : "offline";
      marks.push(`<i class="dot facility ${facility.powered ? "powered" : "offline"} ` +
        `${facility.gridReady ? "grid-ready" : ""}" style="--seat:${player.seat}" ` +
        `title="${escapeHtml(player.factionName)} Facility — ${status}"></i>`);
    }
    for (const generator of player.generators.filter((item) => item.tileId === tile.instanceId)) {
      marks.push(`<i class="dot generator" style="--seat:${player.seat}" ` +
        `title="${escapeHtml(player.factionName)} ${escapeHtml(generator.sourceId)}"></i>`);
    }
  }
  return marks.join("");
}

function renderBoard(state) {
  elements.board.replaceChildren();
  if (!state) return;
  for (const tile of state.board) {
    const hex = document.createElement("div");
    const position = tilePosition(tile);
    hex.className = `hex ${tile.category}`;
    hex.style.left = `${position.left}px`;
    hex.style.top = `${position.top}px`;
    hex.innerHTML = `
      <span class="hex-name">${escapeHtml(tile.name)}</span>
      <span class="hex-type">${escapeHtml(tile.category)}</span>
      <span class="hex-pieces">${contentsForTile(tile, state.players)}</span>
    `;
    elements.board.append(hex);
  }
}

function renderPlayers(state) {
  elements.players.replaceChildren();
  if (!state) return;
  for (const player of state.players) {
    const card = document.createElement("article");
    card.className = `public-player ${player.seat === 0 ? "human" : ""}`;
    card.style.setProperty("--seat", player.seat);
    card.innerHTML = `
      <p class="eyebrow">Seat ${player.seat + 1}${player.seat === 0 ? " · you" : ""}</p>
      <h3>${escapeHtml(player.factionName)}</h3>
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

async function submitDecision(decisionId) {
  const packet = game.pending;
  elements.decisions.querySelectorAll("button").forEach((button) => {
    button.disabled = true;
  });
  const response = await fetch(`/api/games/${game.id}/decisions`, {
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
  for (const decision of packet.legalDecisions) {
    const button = document.createElement("button");
    button.className = "decision-card";
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
  elements.log.innerHTML = replay.slice().reverse().map((event) =>
    `<li><strong>R${event.round}C${event.cycle}</strong> ${escapeHtml(event.summary)}</li>`
  ).join("");
}

function render() {
  const state = game?.state;
  elements.phase.textContent = game?.status || "ready";
  elements["game-status"].textContent = game?.error ||
    (game ? `Game ${game.id.slice(0, 8)} · ${game.status}` :
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
  const response = await fetch(`/api/games/${game.id}`);
  const next = await response.json();
  if (!response.ok) throw new Error(next.error || "Could not read the game.");
  game = next;
  render();
  if (!["complete", "failed", "waiting"].includes(game.status)) schedulePoll();
}

function schedulePoll() {
  clearTimeout(pollTimer);
  pollTimer = setTimeout(() => {
    refresh().catch((error) => {
      elements["game-status"].textContent = error.message;
    });
  }, 120);
}

elements["start-game"].addEventListener("click", async () => {
  clearTimeout(pollTimer);
  elements["start-game"].disabled = true;
  try {
    const response = await fetch("/api/games", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        factionId: elements.faction.value,
        playerCount: Number(elements["player-count"].value),
        seed: elements.seed.value
      })
    });
    game = await response.json();
    if (!response.ok) throw new Error(game.error || "Could not start game.");
    render();
    schedulePoll();
  } catch (error) {
    elements["game-status"].textContent = error.message;
  } finally {
    elements["start-game"].disabled = false;
  }
});

elements.export.addEventListener("click", () => {
  if (!game) return;
  const blob = new Blob([JSON.stringify(game, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `frontier-2038-${game.id}-game.json`;
  link.click();
  URL.revokeObjectURL(link.href);
});

window.addEventListener("resize", () => renderBoard(game?.state));
render();
