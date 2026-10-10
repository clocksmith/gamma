import {
  apiFetch,
  bridgeRequired,
  connectBridge,
  getBridgeToken,
} from "./api-client.js";
import { createBrowserInteractiveGame } from "../lab/runtime/create-browser-interactive-game.js";

import { createBoard } from "./components/board.js";
import { createPlayerMats } from "./components/player-mats.js";
import { createCardTable } from "./components/card-table.js";

const [factions, config, profilesDocument, uiCopy, headlines, mandates] =
  await Promise.all([
    fetch("/dist/runtime/factions.json").then((response) => response.json()),
    fetch("/dist/runtime/game-config.json").then((response) => response.json()),
    fetch("/dist/runtime/player-strategies.json").then((response) =>
      response.json(),
    ),
    fetch("/dist/runtime/ui-copy.json").then((response) => response.json()),
    fetch("/dist/runtime/headlines.json").then((response) => response.json()),
    fetch("/dist/runtime/mandates.json").then((response) => response.json()),
  ]);
const profiles = profilesDocument.profiles;
const copy = uiCopy.prototype;
const kitSelect = document.createElement("select");
kitSelect.id = "kit";
kitSelect.setAttribute("aria-label", copy.browser.playerKit);
for (const kit of config.playerKits)
  kitSelect.add(
    new Option(`${kit.symbol} ${kit.colorName} · ${kit.symbolName}`, kit.id),
  );
const kitLabel = document.createElement("label");
kitLabel.textContent = copy.browser.playerKit;
kitLabel.append(kitSelect);
const kitGuidance = document.createElement("small");
kitGuidance.textContent = copy.browser.kitSetup;
kitLabel.append(kitGuidance);

const firstGameGuideMode =
  new URLSearchParams(window.location.search).get("guide") === "first-game";

const $ = (id) => document.getElementById(id);
const elements = Object.fromEntries(
  [
    "provider-controls",
    "allow-llm",
    "board",
    "bridge-panel",
    "bridge-status",
    "bridge-token",
    "connect-bridge",
    "decision-context",
    "decision-count",
    "decision-title",
    "decisions",
    "export",
    "faction",
    "game-status",
    "log",
    "max-llm-decisions",
    "model",
    "opponent-config",
    "phase",
    "player-count",
    "players",
    "round-title",
    "seed",
    "setup",
    "start-game",
  ].map((id) => [id, $(id)]),
);

for (const faction of factions.factions) {
  elements.faction.add(
    new Option(`${faction.name} — ${faction.motto}`, faction.id),
  );
}

elements.setup
  .querySelector(".command-fields")
  .insertBefore(kitLabel, elements["start-game"]);

let game = null;
let pollTimer = null;
let bridgeConnected = !bridgeRequired;
let previewState = null;
let previewSerial = 0;
const boardView = createBoard(
  elements.board,
  document.querySelector(".board-note"),
  config,
  copy.table,
);
const matView = createPlayerMats(
  elements.players,
  config,
  factions,
  copy.table,
);
const cardsView = createCardTable(
  $("shared-cards"),
  config,
  factions,
  headlines,
  mandates,
  copy.table,
  elements.decisions,
);

function tableOptions() {
  const playerCount = Number(elements["player-count"].value);
  return {
    factionId: elements.faction.value,
    playerCount,
    seed: elements.seed.value,
    kitAssignments: [
      kitSelect.value,
      ...config.playerKits
        .filter((kit) => kit.id !== kitSelect.value)
        .slice(0, playerCount - 1)
        .map((kit) => kit.id),
    ],
    ...opponentOptions(),
  };
}
async function previewSetup() {
  if (game) return;
  const serial = ++previewSerial;
  // Construct the authoritative initial match without playing or contacting a provider.
  const options = tableOptions();
  options.opponentBackends = Array(options.playerCount - 1).fill("weighted");
  const runtime = await createBrowserInteractiveGame(options, () => {});
  if (serial !== previewSerial || game) return;
  previewState = runtime.match.snapshot();
  $("setup-inventory").textContent = formatCopy(copy.table.setupInventory, {
    players: options.playerCount,
    orgs: options.playerCount * config.playerSupply.agents,
    cubes: options.playerCount * config.playerSupply.resourceTrackCubes,
    hexes: config.sharedSupply.hexTiles,
    cards:
      config.trainingDeck.cards.reduce((sum, card) => sum + card.count, 0) +
      headlines.headlines.length +
      mandates.mandates.length +
      factions.factions.length,
    markers:
      config.sharedSupply.currentEraMarkers +
      config.sharedSupply.initiativeMarkers,
  });
  render();
}
const llmBackends = new Set([
  "claude",
  "codex",
  "hybrid-claude",
  "hybrid-codex",
]);

function escapeHtml(value) {
  return String(value).replace(
    /[&<>"']/g,
    (character) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[character],
  );
}

function formatCopy(template, values = {}) {
  return template.replace(/\{(\w+)\}/g, (_, key) => String(values[key] ?? ""));
}

function backendOptions() {
  return [
    ["weighted", copy.browser.weighted],
    ["greedy", copy.browser.greedy],
    ["claude", copy.browser.claude],
    ["codex", copy.browser.codex],
    ["hybrid-claude", copy.browser.hybridClaude],
    ["hybrid-codex", copy.browser.hybridCodex],
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
        ${profiles
          .map(
            (candidate) => `
          <option value="${escapeHtml(candidate.id)}" ${
            candidate.id === profile.id ? "selected" : ""
          }>${escapeHtml(candidate.name)}</option>
        `,
          )
          .join("")}
      </select>
      <select class="backend-select" aria-label="${formatCopy(copy.browser.backend, { seat: index + 2 })}">
        ${backendOptions()
          .map(
            ([value, label]) =>
              `<option value="${value}">${escapeHtml(label)}</option>`,
          )
          .join("")}
      </select>
      <p class="persona-summary">${escapeHtml(profile.persona.identity)}</p>
    `;
    row.querySelector(".profile-select").addEventListener("change", (event) => {
      const selected = profiles.find(
        (candidate) => candidate.id === event.target.value,
      );
      row.querySelector(".persona-summary").textContent =
        selected.persona.identity;
    });
    row
      .querySelector(".backend-select")
      .addEventListener("change", updateStartAvailability);
    elements["opponent-config"].append(row);
  }
  updateStartAvailability();
}

function selectedBackends() {
  return [
    ...elements["opponent-config"].querySelectorAll(".backend-select"),
  ].map((select) => select.value);
}

function llmRequested() {
  return selectedBackends().some((backend) => llmBackends.has(backend));
}

function opponentOptions() {
  const rows = [
    ...elements["opponent-config"].querySelectorAll(".opponent-row"),
  ];
  return {
    opponentProfileIds: rows.map(
      (row) => row.querySelector(".profile-select").value,
    ),
    opponentBackends: rows.map(
      (row) => row.querySelector(".backend-select").value,
    ),
    allowLlm: elements["allow-llm"].checked,
    maxLlmDecisions: Number(elements["max-llm-decisions"].value),
    model: elements.model.value || undefined,
  };
}

function updateStartAvailability() {
  const needsLlm = llmRequested();
  const needsRemoteBridge = needsLlm && bridgeRequired;
  elements["bridge-panel"].hidden = !needsRemoteBridge;
  if (needsRemoteBridge) elements["provider-controls"].open = true;
  elements["start-game"].disabled = Boolean(
    needsLlm && (!elements["allow-llm"].checked || !bridgeConnected),
  );
}

function showBridgeState(message, connected = false) {
  elements["bridge-status"].textContent = message;
  elements["bridge-status"].classList.toggle("connected", connected);
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
    remainingLlmDecisions: null,
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
    error: null,
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
  clientGame.execution = clientGame.runtime.match
    .play(clientGame.runtime.policies)
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
    body: JSON.stringify({ requestId: packet.requestId, decisionId }),
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
  select.replaceChildren(
    ...choices.map((choice) => new Option(label(choice), String(choice))),
  );
  if (choices.some((choice) => String(choice) === previous))
    select.value = previous;
}

function factionName(seat) {
  return (
    game?.state?.players?.find((player) => player.seat === Number(seat))
      ?.factionName || formatCopy(copy.browser.seat, { seat: Number(seat) + 1 })
  );
}

function renderTradeBuilder(
  offers,
  { heading, timing: selectedTiming = null, onBack = null } = {},
) {
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
    const partners = [
      ...new Set(offers.map((decision) => decision.parameters.partnerSeat)),
    ];
    replaceOptions(partner, partners, factionName);
    const forPartner = offers.filter(
      (decision) => decision.parameters.partnerSeat === Number(partner.value),
    );
    const gifts = [
      ...new Set(
        forPartner.map(
          (decision) =>
            `${decision.parameters.giveResource}:${decision.parameters.giveAmount}`,
        ),
      ),
    ];
    replaceOptions(give, gifts, (choice) => {
      const [resource, amount] = choice.split(":");
      return optionLabel(resource, amount);
    });
    const [giveResource, giveAmount] = give.value.split(":");
    const afterGift = forPartner.filter(
      (decision) =>
        decision.parameters.giveResource === giveResource &&
        decision.parameters.giveAmount === Number(giveAmount),
    );
    const requests = [
      ...new Set(
        afterGift.map(
          (decision) =>
            `${decision.parameters.receiveResource}:${decision.parameters.receiveAmount}`,
        ),
      ),
    ];
    replaceOptions(receive, requests, (choice) => {
      const [resource, amount] = choice.split(":");
      return optionLabel(resource, amount);
    });
    const [receiveResource, receiveAmount] = receive.value.split(":");
    const afterRequest = afterGift.filter(
      (decision) =>
        decision.parameters.receiveResource === receiveResource &&
        decision.parameters.receiveAmount === Number(receiveAmount),
    );
    const selected = afterRequest.find(
      (decision) =>
        !selectedTiming || decision.parameters.timing === selectedTiming,
    );
    submit.disabled = !selected;
    summary.textContent = selected
      ? selected.label
      : "No legal offer matches this combination.";
    submit.onclick = selected
      ? () =>
          submitDecision(selected.decisionId).catch((error) => {
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

function renderTradeDecisions(packet, stage) {
  if (!["immediate_trade", "trade_response"].includes(stage)) return false;
  const heading = document.createElement("p");
  heading.textContent =
    stage === "immediate_trade"
      ? "Optional trade before your Action: offer one Runway for one Compute, or continue."
      : "Accept or refuse the printed one-for-one trade.";
  elements.decisions.append(heading);
  packet.legalDecisions.forEach((decision, index) =>
    elements.decisions.append(decisionButton(decision, index)),
  );
  return true;
}

function pieceName(pieceId) {
  const number = pieceId?.match(/agent-(\d+)$/)?.[1];
  return number ? `Org ${number}` : pieceId;
}

function tileName(tileId) {
  const tile = game?.state?.board?.find((t) => t.instanceId === tileId);
  return tile ? `${tile.name} (${tile.q}, ${tile.r})` : tileId;
}

function renderAssignmentDecisions(packet, stage) {
  if (stage !== "resolve" && stage !== "talent_assignment") return false;
  const decisions = packet.legalDecisions;
  if (
    !decisions.length ||
    !decisions.every(
      (decision) =>
        decision.parameters?.pieceId && decision.parameters?.destinationId,
    )
  )
    return false;

  const builder = document.createElement("section");
  builder.className = "move-builder";
  builder.innerHTML =
    "<h3>Assign an Org</h3><p>Stay or move one edge to the selected hex, then resolve its Action.</p>";
  if (stage === "talent_assignment")
    builder.querySelector("p").textContent = copy.browser.talentAssignmentHint;
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
  addField("Org", piece);
  addField("Hex", destination);
  if (stage !== "talent_assignment") addField("Action", outcome);

  const summary = document.createElement("p");
  summary.className = "trade-summary";
  const actions = document.createElement("div");
  actions.className = "trade-actions";
  const submit = document.createElement("button");
  submit.type = "button";
  submit.textContent = "Confirm assignment";
  actions.append(submit);

  const refresh = () => {
    const pieces = [
      ...new Set(decisions.map((decision) => decision.parameters.pieceId)),
    ];
    replaceOptions(piece, pieces, pieceName);
    const forPiece = decisions.filter(
      (decision) => decision.parameters.pieceId === piece.value,
    );
    const destinations = [
      ...new Set(forPiece.map((decision) => decision.parameters.destinationId)),
    ];
    replaceOptions(destination, destinations, tileName);
    const atDestination = forPiece.filter(
      (decision) => decision.parameters.destinationId === destination.value,
    );
    replaceOptions(
      outcome,
      atDestination.map((decision) => decision.decisionId),
      (id) =>
        atDestination.find((decision) => decision.decisionId === id)?.label ||
        id,
    );
    const selected = atDestination.find(
      (decision) => decision.decisionId === outcome.value,
    );
    submit.disabled = !selected;
    summary.textContent =
      selected?.label || "No legal action matches this assignment.";
    submit.onclick = selected
      ? () =>
          submitDecision(selected.decisionId).catch((error) => {
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
    elements["decision-title"].textContent =
      game?.status === "complete"
        ? formatCopy(copy.browser.gameComplete, {
            ending: game.result.worldEnding.name,
          })
        : game
          ? copy.browser.otherInstitutionsResolving
          : copy.browser.startGame;
    elements["decision-context"].textContent =
      game?.status === "complete"
        ? formatCopy(copy.browser.completeContext, {
            winners: game.result.standings
              .filter((row) => game.result.winnerSeats.includes(row.seat))
              .map((row) => row.factionName)
              .join(" and "),
            score: game.result.standings[0].score,
            ending: game.result.worldEnding.name,
          })
        : game
          ? copy.browser.waitingContext
          : copy.table.preview;
    elements["decision-count"].textContent = formatCopy(
      copy.browser.legalChoices,
      {
        count: 0,
        plural: "s",
      },
    );
    return;
  }
  elements["decision-title"].textContent = decisionStage(packet, game?.state);
  elements["decision-context"].textContent =
    packet.requestId.split(":").at(-2) === "select"
      ? copy.browser.selectContext
      : packet.requestId.split(":").at(-2) === "resolve"
        ? copy.browser.resolveContext
        : formatCopy(copy.browser.decisionContext, packet);
  elements["decision-count"].textContent = formatCopy(
    copy.browser.legalChoices,
    {
      count: packet.legalDecisions.length,
      plural: packet.legalDecisions.length === 1 ? "" : "s",
    },
  );
  const stage = packet.requestId?.split(":").at(-2);
  if (renderTradeDecisions(packet, stage)) return;
  if (renderAssignmentDecisions(packet, stage)) return;
  for (const [index, decision] of packet.legalDecisions.entries()) {
    elements.decisions.append(decisionButton(decision, index));
  }
}

function renderLedger() {
  const replay = game?.replay || [];
  elements.log.innerHTML = replay
    .slice()
    .reverse()
    .map(
      (event, index) =>
        `<li class="${index === 0 ? "latest-event" : ""}"><strong>E${event.round}C${event.cycle}</strong> ${escapeHtml(event.summary)}</li>`,
    )
    .join("");
}

function render() {
  const state = game?.state || previewState;
  // The setup controls are only relevant before the first match is created.
  // Keep the live board and decisions at the top once play begins.
  elements.setup.hidden = Boolean(game);
  elements.phase.textContent = game?.status || copy.browser.ready;
  elements["game-status"].textContent =
    game?.error ||
    (game
      ? formatCopy(copy.browser.gameStatus, {
          mode:
            game.executionMode === "client"
              ? copy.browser.browserNative
              : copy.browser.localBridge,
          id: game.id.slice(0, 8),
          status: game.status,
        })
      : copy.browser.startingStatus);
  elements["round-title"].textContent = state
    ? formatCopy(copy.browser.roundCycle, state)
    : copy.browser.board;
  elements.export.disabled = !game;
  boardView.update(state);
  matView.update(state);
  cardsView.update(state);
  $("setup-preview-label").hidden = Boolean(game);
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
  try {
    const opponents = opponentOptions();
    const options = tableOptions();
    if (
      !opponents.opponentBackends.some((backend) => llmBackends.has(backend))
    ) {
      await startClientGame(options);
      return;
    }
    const response = await apiFetch("/api/games", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(options),
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
          maximum: status.maximumLlmDecisionsPerOpponent,
        }),
        true,
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
  const receipt =
    game.executionMode === "client"
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
          error: game.error,
        }
      : game;
  const blob = new Blob([JSON.stringify(receipt, null, 2)], {
    type: "application/json",
  });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = formatCopy(copy.browser.downloadFile, { id: game.id });
  link.click();
  URL.revokeObjectURL(link.href);
});

for (const control of [
  elements.faction,
  kitSelect,
  elements["player-count"],
  elements.seed,
]) {
  control.addEventListener("change", () =>
    previewSetup().catch((error) => {
      elements["game-status"].textContent = error.message;
    }),
  );
}
renderOpponents();
updateStartAvailability();
render();
await previewSetup();
if (firstGameGuideMode) {
  elements.setup.hidden = true;
  document.querySelector(".opponent-setup").hidden = true;
  elements.seed.value = "mandate-2038-first-game";
  elements["player-count"].value = "4";
  renderOpponents();
  elements["start-game"].click();
}
