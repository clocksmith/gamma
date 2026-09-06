import {
  apiFetch,
  bridgeRequired,
  connectBridge,
  getBridgeToken
} from "./api-client.js";
import { createBrowserInteractiveGame } from "../lab/runtime/create-browser-interactive-game.js";
import { pointyTopAxialPosition } from "./src/hex-layout.js";

const [factions, config, profilesDocument, uiCopy] = await Promise.all([
  fetch("/dist/runtime/factions.json").then((response) => response.json()),
  fetch("/dist/runtime/game-config.json").then((response) => response.json()),
  fetch("/dist/runtime/player-strategies.json").then((response) => response.json()),
  fetch("/dist/runtime/ui-copy.json").then((response) => response.json())
]);
const profiles = profilesDocument.profiles;
const copy = uiCopy.prototype;
const factionColors = new Map(
  factions.factions.map((faction) => [faction.id, faction.color])
);
const firstGameGuideMode = new URLSearchParams(window.location.search).get("guide") === "first-game";

const $ = (id) => document.getElementById(id);
const elements = Object.fromEntries([
  "provider-controls", "allow-llm", "board", "bridge-panel", "bridge-status", "bridge-token",
  "connect-bridge", "decision-context", "decision-count", "decision-title",
  "decisions", "export", "faction", "game-status", "headline-consequence",
  "headline-label", "headline-name", "headline-newswire", "headline-quote",
  "log", "max-llm-decisions", "model", "opponent-config",
  "phase", "player-count", "players", "round-title", "seed", "setup", "start-game"
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

function formatCopy(template, values = {}) {
  return template.replace(/\{(\w+)\}/g, (_, key) => String(values[key] ?? ""));
}

function factionColor(player) {
  return factionColors.get(player.factionId) || "#000000";
}

function backendOptions() {
  return [
    ["weighted", copy.browser.weighted],
    ["greedy", copy.browser.greedy],
    ["claude", copy.browser.claude],
    ["codex", copy.browser.codex],
    ["hybrid-claude", copy.browser.hybridClaude],
    ["hybrid-codex", copy.browser.hybridCodex]
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
      <strong>${formatCopy(copy.browser.seat, { seat: index + 2 })}</strong>
      <select class="profile-select" aria-label="${formatCopy(copy.browser.persona, { seat: index + 2 })}">
        ${profiles.map((candidate) => `
          <option value="${escapeHtml(candidate.id)}" ${
            candidate.id === profile.id ? "selected" : ""
          }>${escapeHtml(candidate.name)}</option>
        `).join("")}
      </select>
      <select class="backend-select" aria-label="${formatCopy(copy.browser.backend, { seat: index + 2 })}">
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
  if (needsRemoteBridge) elements["provider-controls"].open = true;
  elements["start-game"].disabled = Boolean(
    needsLlm && (!elements["allow-llm"].checked || !bridgeConnected)
  );
}

function showBridgeState(message, connected = false) {
  elements["bridge-status"].textContent = message;
  elements["bridge-status"].classList.toggle("connected", connected);
}

function tilePosition(tile) {
  const compact = window.innerWidth <= 680;
  const hexWidth = compact ? 100 : 144;
  const hexHeight = compact ? 87 : 125;
  const originX = elements.board.clientWidth / 2;
  const originY = elements.board.clientHeight / 2;
  return pointyTopAxialPosition(tile, {
    width: hexWidth,
    height: hexHeight,
    originX,
    originY
  });
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
        signature: `facility:${facility.powered}`
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
      marks.push(`<i class="dot ${piece.kind}${arrivalClass}" style="--seat:${player.seat};--faction-color:${factionColor(player)}" ` +
        `title="${escapeHtml(player.factionName)} ${piece.kind}"></i>`);
    }
    for (const [index, facility] of player.facilities.entries()) {
      if (facility.tileId !== tile.instanceId) continue;
      const arrivalClass = priorMarkerKeys.has(markerKey(player, "facility", facility, index)) ? "" : " arrival";
      const status = facility.powered ? copy.browser.connectedNow : copy.browser.offline;
      marks.push(`<i class="dot facility ${facility.powered ? "powered" : "offline"}${arrivalClass} ` +
        `" style="--seat:${player.seat};--faction-color:${factionColor(player)}" ` +
        `title="${escapeHtml(player.factionName)} Facility — ${status}"></i>`);
    }
    for (const [index, generator] of player.generators.entries()) {
      if (generator.tileId !== tile.instanceId) continue;
      const arrivalClass = priorMarkerKeys.has(markerKey(player, "generator", generator, index)) ? "" : " arrival";
      marks.push(`<i class="dot generator${arrivalClass}" style="--seat:${player.seat};--faction-color:${factionColor(player)}" ` +
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
    card.style.setProperty("--faction-color", factionColor(player));
    card.innerHTML = `
      <p class="eyebrow">${formatCopy(copy.browser.seat, { seat: player.seat + 1 })}${player.seat === 0 ? ` · ${copy.browser.you}` : ""}</p>
      <h3>${escapeHtml(player.factionName)}</h3>
      ${opponent ? `<p class="readiness">${
        escapeHtml(opponent.profileName)
      } · ${escapeHtml(opponent.backend)}${
        opponent.remainingLlmDecisions === null
          ? ""
          : ` · ${formatCopy(copy.browser.llmCallsLeft, { count: opponent.remainingLlmDecisions })}`
      }</p>` : ""}
      <p class="readiness ${player.agiReadiness.ready ? "ready" : ""}">
        ${player.agiDeclared
          ? copy.browser.agiRecognized
          : player.agiReadiness.ready
          ? copy.browser.agiGridReady
          : formatCopy(copy.browser.agiBlocked, {
            requirement: escapeHtml(copy.browser.requirements[player.agiReadiness.failingRequirement])
          })}
      </p>
      <dl>
        <dt>${copy.tracks.mandate}</dt><dd>${player.mandate}</dd>
        <dt>${copy.tracks.runway}</dt><dd>${player.runway}</dd>
        <dt>${copy.tracks.compute}</dt><dd>${player.compute}</dd>
        <dt>${copy.tracks.capability}</dt><dd>${player.capability}</dd>
        <dt>${copy.tracks.customers}</dt><dd>${player.customers}</dd>
        <dt>${copy.tracks.trust}</dt><dd>${player.trust}</dd>
        <dt>${copy.tracks.scrutiny}</dt><dd>${player.scrutiny}</dd>
        <dt>AGI recognized</dt><dd>${player.agiDeclared ? "Yes" : "No"}</dd>
      </dl>
    `;
    elements.players.append(card);
  }
}

function decisionStage(packet, state) {
  const stage = packet?.requestId?.split(":").at(-2) || copy.browser.decision;

  return copy.browser.stages[stage] || stage.replaceAll("_", " ");
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

function decisionButton(decision, index = 0, className = "decision-card") {
  const button = document.createElement("button");
  button.className = className;
  button.style.setProperty("--card-index", index);
  button.innerHTML = `
    <strong>${escapeHtml(decision.label)}</strong>
    <small>${escapeHtml(decision.actionId || copy.browser.decision)}</small>
  `;
  button.addEventListener("click", () => {
    submitDecision(decision.decisionId).catch((error) => {
      elements["game-status"].textContent = error.message;
      renderDecisions();
    });
  });
  return button;
}

function optionLabel(resource, amount) {
  return `${amount} ${resource}`;
}

function replaceOptions(select, choices, label) {
  const previous = select.value;
  select.replaceChildren(...choices.map((choice) =>
    new Option(label(choice), String(choice))
  ));
  if (choices.some((choice) => String(choice) === previous)) select.value = previous;
}

function factionName(seat) {
  return game?.state?.players?.find((player) => player.seat === Number(seat))?.factionName ||
    formatCopy(copy.browser.seat, { seat: Number(seat) + 1 });
}

function renderTradeBuilder(offers, { heading, timing: selectedTiming = null, onBack = null } = {}) {
  const builder = document.createElement("section");
  builder.className = "trade-builder";
  const title = document.createElement("h3");
  title.textContent = heading;
  const summary = document.createElement("p");
  summary.className = "trade-summary";
  const fields = document.createElement("div");
  fields.className = "trade-fields";
  const partner = document.createElement("select");
  const give = document.createElement("select");
  const receive = document.createElement("select");
  const addField = (label, control) => {
    const field = document.createElement("label");
    field.textContent = label;
    field.append(control);
    fields.append(field);
  };
  addField("Trade with", partner);
  addField("Give", give);
  addField("Request", receive);

  const actions = document.createElement("div");
  actions.className = "trade-actions";
  const submit = document.createElement("button");
  submit.type = "button";
  submit.textContent = "Propose offer";
  actions.append(submit);
  if (onBack) {
    const back = document.createElement("button");
    back.type = "button";
    back.className = "trade-pass";
    back.textContent = "Change timing";
    back.addEventListener("click", onBack);
    actions.append(back);
  }

  const refresh = () => {
    const partners = [...new Set(offers.map((decision) => decision.parameters.partnerSeat))];
    replaceOptions(partner, partners, factionName);
    const forPartner = offers.filter((decision) =>
      decision.parameters.partnerSeat === Number(partner.value)
    );
    const gifts = [...new Set(forPartner.map((decision) =>
      `${decision.parameters.giveResource}:${decision.parameters.giveAmount}`
    ))];
    replaceOptions(give, gifts, (choice) => {
      const [resource, amount] = choice.split(":");
      return optionLabel(resource, amount);
    });
    const [giveResource, giveAmount] = give.value.split(":");
    const afterGift = forPartner.filter((decision) =>
      decision.parameters.giveResource === giveResource &&
      decision.parameters.giveAmount === Number(giveAmount)
    );
    const requests = [...new Set(afterGift.map((decision) =>
      `${decision.parameters.receiveResource}:${decision.parameters.receiveAmount}`
    ))];
    replaceOptions(receive, requests, (choice) => {
      const [resource, amount] = choice.split(":");
      return optionLabel(resource, amount);
    });
    const [receiveResource, receiveAmount] = receive.value.split(":");
    const afterRequest = afterGift.filter((decision) =>
      decision.parameters.receiveResource === receiveResource &&
      decision.parameters.receiveAmount === Number(receiveAmount)
    );
    const selected = afterRequest.find((decision) =>
      !selectedTiming || decision.parameters.timing === selectedTiming
    );
    submit.disabled = !selected;
    summary.textContent = selected ? selected.label : "No legal offer matches this combination.";
    submit.onclick = selected
      ? () => submitDecision(selected.decisionId).catch((error) => {
        elements["game-status"].textContent = error.message;
        renderDecisions();
      })
      : null;
  };
  for (const control of [partner, give, receive]) {
    control.addEventListener("change", refresh);
  }
  builder.append(title, fields, summary, actions);
  refresh();
  elements.decisions.append(builder);
}

function renderTradeTimingChoices(offers, emptyDecision) {
  const chooser = document.createElement("section");
  chooser.className = "trade-builder trade-timing";
  chooser.innerHTML = "<h3>Trade this action?</h3><p>Choose when to settle an offer, or continue without one.</p>";
  const actions = document.createElement("div");
  actions.className = "trade-actions";
  const addChoice = (label, timing) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "trade-timing-button";
    button.textContent = label;
    const matchingOffers = offers.filter((decision) => decision.parameters.timing === timing);
    button.disabled = matchingOffers.length === 0;
    button.addEventListener("click", () => {
      elements.decisions.replaceChildren();
      renderTradeBuilder(matchingOffers, {
        heading: label,
        timing,
        onBack: () => {
          elements.decisions.replaceChildren();
          renderTradeTimingChoices(offers, emptyDecision);
        }
      });
    });
    actions.append(button);
  };
  const noTrade = document.createElement("button");
  noTrade.type = "button";
  noTrade.className = "trade-pass";
  noTrade.textContent = "No trade";
  noTrade.disabled = !emptyDecision;
  noTrade.addEventListener("click", () => submitDecision(emptyDecision.decisionId).catch((error) => {
    elements["game-status"].textContent = error.message;
    renderDecisions();
  }));
  actions.append(noTrade);
  addChoice("Trade before action", "before");
  addChoice("Trade after action", "after");
  chooser.append(actions);
  elements.decisions.append(chooser);
}

function renderTradeDecisions(packet, stage) {
  const decisions = packet.legalDecisions;
  const offers = decisions.filter((decision) => decision.parameters?.partnerSeat !== undefined);
  if (!offers.length) return false;
  if (stage === "immediate_trade") {
    renderTradeTimingChoices(
      offers,
      decisions.find((decision) => decision.decisionId === "trade_none")
    );
    return true;
  }
  if (stage === "immediate_trade_response") {
    const response = document.createElement("section");
    response.className = "trade-response";
    const offer = decisions.find((decision) => decision.decisionId === "trade_accept");
    response.innerHTML = `<h3>Offer received</h3><p>${escapeHtml(offer?.label || "Review the proposed trade.")}</p>`;
    const controls = document.createElement("div");
    controls.className = "trade-actions";
    for (const decision of decisions.filter((decision) =>
      decision.decisionId === "trade_accept" || decision.decisionId === "trade_reject"
    )) controls.append(decisionButton(decision, 0, "trade-response-button"));
    response.append(controls);
    elements.decisions.append(response);
    renderTradeBuilder(offers, { heading: "Counteroffer" });
    return true;
  }
  return false;
}

function pieceName(pieceId) {
  const number = pieceId?.match(/agent-(\d+)$/)?.[1];
  return number ? `Agent ${number}` : pieceId;
}

function tileName(tileId) {
  return game?.state?.board?.find((tile) => tile.instanceId === tileId)?.name || tileId;
}

function renderAssignmentDecisions(packet, stage) {
  if (stage !== "resolve" && stage !== "blocked_program_assignment" && !stage.startsWith("resolve_escalation_")) return false;
  const decisions = packet.legalDecisions;
  if (!decisions.length || !decisions.every((decision) =>
    decision.parameters?.pieceId && decision.parameters?.destinationId
  )) return false;

  const builder = document.createElement("section");
  builder.className = "move-builder";
  builder.innerHTML = "<h3>Assign an Agent</h3><p>Choose an Agent, district, and action effect. The Agent remains as presence until reassigned.</p>";
  const fields = document.createElement("div");
  fields.className = "trade-fields";
  const piece = document.createElement("select");
  const destination = document.createElement("select");
  const outcome = document.createElement("select");
  const addField = (label, control) => {
    const field = document.createElement("label");
    field.textContent = label;
    field.append(control);
    fields.append(field);
  };
  addField("Agent", piece);
  addField("To district", destination);
  addField("Action", outcome);

  const summary = document.createElement("p");
  summary.className = "trade-summary";
  const actions = document.createElement("div");
  actions.className = "trade-actions";
  const submit = document.createElement("button");
  submit.type = "button";
  submit.textContent = "Confirm assignment";
  actions.append(submit);

  const refresh = () => {
    const pieces = [...new Set(decisions.map((decision) => decision.parameters.pieceId))];
    replaceOptions(piece, pieces, pieceName);
    const forPiece = decisions.filter((decision) => decision.parameters.pieceId === piece.value);
    const destinations = [...new Set(forPiece.map((decision) => decision.parameters.destinationId))];
    replaceOptions(destination, destinations, tileName);
    const atDestination = forPiece.filter((decision) =>
      decision.parameters.destinationId === destination.value
    );
    replaceOptions(outcome, atDestination.map((decision) => decision.decisionId), (id) =>
      atDestination.find((decision) => decision.decisionId === id)?.label || id
    );
    const selected = atDestination.find((decision) => decision.decisionId === outcome.value);
    submit.disabled = !selected;
    summary.textContent = selected?.label || "No legal action matches this assignment.";
    submit.onclick = selected
      ? () => submitDecision(selected.decisionId).catch((error) => {
        elements["game-status"].textContent = error.message;
        renderDecisions();
      })
      : null;
  };
  for (const control of [piece, destination, outcome]) {
    control.addEventListener("change", refresh);
  }
  builder.append(fields, summary, actions);
  refresh();
  elements.decisions.append(builder);
  return true;
}

function renderDecisions() {
  elements.decisions.replaceChildren();
  const packet = game?.pending;
  if (!packet) {
    elements["decision-title"].textContent = game?.status === "complete"
      ? formatCopy(copy.browser.gameComplete, { ending: game.result.worldEnding.name })
      : game ? copy.browser.otherInstitutionsResolving : copy.browser.startGame;
    elements["decision-context"].textContent = game?.status === "complete"
      ? formatCopy(copy.browser.completeContext, {
        winners: game.result.standings.filter(row => game.result.winnerSeats.includes(row.seat)).map(row => row.factionName).join(" and "),
        score: game.result.standings[0].score, ending: game.result.worldEnding.name
      })
      : copy.browser.waitingContext;
    elements["decision-count"].textContent = formatCopy(copy.browser.legalChoices, {
      count: 0,
      plural: "s"
    });
    return;
  }
  elements["decision-title"].textContent = decisionStage(packet, game?.state);
  elements["decision-context"].textContent =
    packet.requestId.split(":").at(-2) === "select" ? copy.browser.selectContext
      : packet.requestId.split(":").at(-2) === "resolve" ? copy.browser.resolveContext
      : formatCopy(copy.browser.decisionContext, packet);
  elements["decision-count"].textContent =
    formatCopy(copy.browser.legalChoices, {
      count: packet.legalDecisions.length,
      plural: packet.legalDecisions.length === 1 ? "" : "s"
    });
  const stage = packet.requestId?.split(":").at(-2);
  if (renderTradeDecisions(packet, stage)) return;
  if (renderAssignmentDecisions(packet, stage)) return;
  for (const [index, decision] of packet.legalDecisions.entries()) {
    elements.decisions.append(decisionButton(decision, index));
  }
}

function renderLedger() {
  const replay = game?.replay || [];
  elements.log.innerHTML = replay.slice().reverse().map((event, index) =>
    `<li class="${index === 0 ? "latest-event" : ""}"><strong>E${event.round}C${event.cycle}</strong> ${escapeHtml(event.summary)}</li>`
  ).join("");
}

function render() {
  const state = game?.state;
  // The setup controls are only relevant before the first match is created.
  // Keep the live board and decisions at the top once play begins.
  elements.setup.hidden = Boolean(game);
  elements.phase.textContent = game?.status || copy.browser.ready;
  elements["game-status"].textContent = game?.error ||
    (game ? formatCopy(copy.browser.gameStatus, {
      mode: game.executionMode === "client" ? copy.browser.browserNative : copy.browser.localBridge,
      id: game.id.slice(0, 8),
      status: game.status
    }) :
      copy.browser.startingStatus);
  elements["round-title"].textContent = state
    ? formatCopy(copy.browser.roundCycle, state)
    : copy.browser.board;
  const headline = state?.activeHeadline;
  elements["headline-label"].textContent = headline
    ? copy.headline.current
    : copy.headline.unrevealed;
  elements["headline-name"].textContent = headline?.name || "";
  elements["headline-newswire"].textContent = headline?.newswire || "";
  elements["headline-consequence"].textContent = headline
    ? `${copy.headline.consequence}: ${headline.text}`
    : "";
  elements["headline-quote"].textContent = headline?.quote
    ? `“${headline.quote}”`
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
  showBridgeState(copy.browser.bridgeOptional);
  elements["connect-bridge"].addEventListener("click", async () => {
    elements["connect-bridge"].disabled = true;
    showBridgeState(copy.browser.bridgeRequesting);
    try {
      const status = await connectBridge(elements["bridge-token"].value);
      bridgeConnected = true;
      showBridgeState(
        formatCopy(copy.browser.bridgeConnected, {
          maximum: status.maximumLlmDecisionsPerOpponent
        }),
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
  link.download = formatCopy(copy.browser.downloadFile, { id: game.id });
  link.click();
  URL.revokeObjectURL(link.href);
});

window.addEventListener("resize", () => renderBoard(game?.state));
renderOpponents();
updateStartAvailability();
render();
if (firstGameGuideMode) {
  elements.setup.hidden = true;
  document.querySelector(".opponent-setup").hidden = true;
  elements.seed.value = "mandate-2038-first-game";
  elements["player-count"].value = "4";
  renderOpponents();
  elements["start-game"].click();
}
