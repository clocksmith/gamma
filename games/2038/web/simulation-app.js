import {
  normalizeSimulationReport
} from "/lab/contracts/report-migrations.js";
import {
  aggregateFactionPersona,
  compatibleReportGroups,
  heatmapCells,
  providerSummary,
  sampledGames,
  trajectoryForSample,
  visualizationMetrics
} from "./report-visualizations.js";
import {
  apiFetch,
  bridgeRequired,
  connectBridge,
  getBridgeToken
} from "./api-client.js";
import { pointyTopAxialPosition } from "./src/hex-layout.js";

const seatColors = ["#a45137", "#536e73", "#a98c3f", "#7a657d", "#607d70", "#6c7a89"];
const [profilesDocument, uiCopy] = await Promise.all([
  fetch("/dist/runtime/player-strategies.json").then((response) => response.json()),
  fetch("/dist/runtime/ui-copy.json").then((response) => response.json())
]);
const profiles = profilesDocument.profiles;
const copy = uiCopy.simulation;
const visualizationLabels = {
  ...copy.labels,
  mandate: uiCopy.prototype.tracks.mandate
};

function interpolate(template, values = {}) {
  return template.replace(/\{([^}]+)\}/g, (match, key) =>
    Object.prototype.hasOwnProperty.call(values, key) ? String(values[key]) : match
  );
}
const elements = Object.fromEntries(
  [
    "allow-llm",
    "analysis-files",
    "analysis-files-results",
    "analysis-heatmap",
    "analysis-heatmap-metric",
    "analysis-llm",
    "analysis-sample",
    "analysis-scatter",
    "analysis-scatter-note",
    "analysis-scatter-size",
    "analysis-scatter-x",
    "analysis-scatter-y",
    "analysis-section",
    "analysis-status",
    "analysis-trajectory",
    "analysis-trajectory-legend",
    "analysis-trajectory-metric",
    "analysis-trajectory-note",
    "archive-path",
    "bridge-panel",
    "bridge-status",
    "bridge-token",
    "connect-bridge",
    "coverage",
    "download-report",
    "distribution-section",
    "evidence-identity",
    "experiment-mode",
    "experiment-results",
    "experiment-results-body",
    "experiment-results-title",
    "execution-controls",
    "faction-results",
    "generations",
    "generations-field",
    "iterations",
    "iterations-field",
    "job-status",
    "llm-controls",
    "llm-concurrency",
    "matrix-batch-field",
    "matrix-batch-size",
    "matrix-initial-field",
    "matrix-initial-runs",
    "max-llm-decisions",
    "model",
    "reasoning-effort",
    "require-llm",
    "new-simulation",
    "optimization-controls",
    "mode-description",
    "population",
    "population-field",
    "player-count-field",
    "profile-results",
    "preregistration-field",
    "preregistration-path",
    "replay-board",
    "replay-caption",
    "replay-next",
    "replay-players",
    "replay-prev",
    "replay-sample",
    "replay-step",
    "report-file",
    "replay-samples-field",
    "recent-reports",
    "recent-reports-status",
    "refresh-reports",
    "results-subtitle",
    "results-title",
    "results-view",
    "run-simulation",
    "runs",
    "runs-field",
    "runs-label",
    "sample-replays",
    "score-distributions",
    "seat-config",
    "persona-controls",
    "seat-results",
    "seat-results-section",
    "setup-view",
    "sim-player-count",
    "sim-seed",
    "simulation-form",
    "stop-job-watch",
    "summary-cards",
    "target-profile",
    "target-profile-field",
    "workers",
    "replay-section"
  ].map((id) => [id, document.getElementById(id)])
);

let report = null;
let rawReport = null;
let replayIndex = 0;
let bridgeConnected = !bridgeRequired;
let analysisReports = [];
let jobPollingController = null;
let activeJobId = null;

const analysisColors = ["#a45137", "#536e73", "#a98c3f", "#7a657d", "#607d70", "#6c7a89"];

function escapeHtml(value) {
  return String(value).replace(/[&<>\"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;"
  })[character]);
}

function showBridgeState(message, connected = false) {
  elements["bridge-status"].textContent = message;
  elements["bridge-status"].classList.toggle("connected", connected);
}

function updateRunAvailability() {
  elements["run-simulation"].disabled = !bridgeConnected;
}

function shortFingerprint(value) {
  return String(value || "unattributed").replace(/^sha256:/, "").slice(0, 12);
}

function renderEvidenceIdentity() {
  const migration = report.migration;
  elements["evidence-identity"].innerHTML = `
    <strong>Game ${report.game.version}</strong>
    <span>rules ${shortFingerprint(report.game.rulesetFingerprint)}</span>
    <span>engine ${report.engine.id}@${report.engine.version} · ${shortFingerprint(report.engine.fingerprint)}</span>
    <span>strategies ${shortFingerprint(report.strategies.fingerprint)}</span>
    <span>experiment ${shortFingerprint(report.experiment.fingerprint)}</span>
    <span>report schema ${report.reportSchemaVersion} · replay schema ${report.replaySchemaVersion}</span>
    ${migration ? `<em>${migration.warning}</em>` : ""}
  `;
}

function backendOptions() {
  return [
    ["weighted", copy.backends.weighted],
    ["greedy", copy.backends.greedy],
    ["claude", copy.backends.claude],
    ["codex", copy.backends.codex],
    ["hybrid-claude", copy.backends.hybridClaude],
    ["hybrid-codex", copy.backends.hybridCodex]
  ];
}

function renderSeats() {
  const count = Number(elements["sim-player-count"].value);
  elements["seat-config"].replaceChildren();
  for (let seat = 0; seat < count; seat += 1) {
    const row = document.createElement("div");
    row.className = "seat-row";
    row.dataset.seat = seat;
    const profile = profiles[seat % profiles.length];
    row.innerHTML = `
      <strong>Seat ${seat + 1}</strong>
      <select class="profile-select" aria-label="${
        interpolate(copy.labels.seatPersona, { seat: seat + 1 })
      }">
        ${profiles.map((candidate) => `
          <option value="${candidate.id}" ${candidate.id === profile.id ? "selected" : ""}>
            ${candidate.name}
          </option>
        `).join("")}
      </select>
      <select class="backend-select" aria-label="${
        interpolate(copy.labels.seatBackend, { seat: seat + 1 })
      }">
        ${backendOptions().map(([value, label]) => `
          <option value="${value}">${label}</option>
        `).join("")}
      </select>
      <input class="seat-model" aria-label="Seat ${seat + 1} model override" placeholder="Provider default">
      <select class="seat-reasoning-effort" aria-label="Seat ${seat + 1} reasoning effort">
        <option value="">Default effort</option>
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
        <option value="xhigh">Extra high</option>
        <option value="max">Max</option>
      </select>
      <p class="persona-summary">${profile.persona.identity}</p>
    `;
    row.querySelector(".profile-select").addEventListener("change", (event) => {
      const selected = profiles.find((candidate) => candidate.id === event.target.value);
      row.querySelector(".persona-summary").textContent = selected.persona.identity;
    });
    elements["seat-config"].append(row);
  }
}

function simulationOptions() {
  const rows = [...elements["seat-config"].querySelectorAll(".seat-row")];
  const mode = elements["experiment-mode"].value;
  const options = {
    mode,
    runs: Number(elements.runs.value),
    playerCount: Number(elements["sim-player-count"].value),
    seed: elements["sim-seed"].value,
    sampleReplays: Number(elements["sample-replays"].value),
    profileIds: rows.map((row) => row.querySelector(".profile-select").value),
    backends: rows.map((row) => row.querySelector(".backend-select").value),
    allowLlm: elements["allow-llm"].checked,
    requireLlm: elements["require-llm"].checked,
    maxLlmDecisions: elements["max-llm-decisions"].value
      ? Number(elements["max-llm-decisions"].value)
      : undefined,
    model: elements.model.value || undefined,
    models: rows.map((row) => row.querySelector(".seat-model").value || undefined),
    reasoningEffort: elements["reasoning-effort"].value || undefined,
    reasoningEfforts: rows.map((row) =>
      row.querySelector(".seat-reasoning-effort").value || undefined
    ),
    workers: elements.workers.value
      ? Number(elements.workers.value)
      : undefined,
    llmConcurrency: elements["llm-concurrency"].value
      ? Number(elements["llm-concurrency"].value)
      : undefined
  };
  if (mode === "strategy-evolution") {
    options.targetProfileId = elements["target-profile"].value;
    options.generations = Number(elements.generations.value);
    options.population = Number(elements.population.value);
    options.runsPerSeat = Number(elements.runs.value);
    options.sampleReplays = 0;
    options.allowLlm = false;
  } else if (mode === "rule-search") {
    options.iterations = Number(elements.iterations.value);
    options.sampleReplays = 0;
    options.allowLlm = false;
  } else if (mode === "balance-audit") {
    options.maximumMatches = Number(elements.runs.value);
    options.initialRunsPerCell = Number(elements["matrix-initial-runs"].value);
    options.batchSize = Number(elements["matrix-batch-size"].value);
    options.playerCounts = [3, 4, 5];
    options.mandateModes = ["variable", "fixed"];
    options.sampleReplays = 0;
    options.allowLlm = false;
  } else if (mode === "llm-holdout") {
    options.preRegistrationPath = elements["preregistration-path"].value;
    options.sampleReplays = 0;
  } else if (mode === "faction-swap") {
    options.preRegistrationPath = elements["preregistration-path"].value;
    options.sampleReplays = 0;
  }
  return options;
}

function abortableDelay(milliseconds, signal) {
  return new Promise((resolve, reject) => {
    let settled = false;
    const settle = (callback) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
      callback();
    };
    const timer = setTimeout(() => settle(resolve), milliseconds);
    const onAbort = () => {
      settle(() => reject(new DOMException("Simulation monitoring stopped.", "AbortError")));
    };
    if (signal?.aborted) onAbort();
    else signal?.addEventListener("abort", onAbort, { once: true });
  });
}

function jobProgressLabel(job) {
  const progress = job.progress || {};
  const cycle = progress.cycleNumber ?? progress.cycle;
  const checkpoint = progress.kind === "turn"
    ? `turn ${progress.turnNumber ?? "in progress"}`
    : cycle !== null && cycle !== undefined
      ? `cycle ${cycle}`
      : progress.phase;
  return `${job.status.toUpperCase()} · ${progress.completed}/${progress.total} · ${checkpoint}`;
}

async function pollJob(id, { signal } = {}) {
  let lastProgressKey = null;
  let lastProgressAt = Date.now();
  let retries = 0;
  while (true) {
    let job;
    try {
      const response = await apiFetch(`/api/simulations/${id}`, { signal });
      job = await response.json();
      if (!response.ok) throw new Error(job.error || copy.errors.readJob);
      retries = 0;
    } catch (error) {
      if (error?.name === "AbortError") throw error;
      retries += 1;
      elements["job-status"].textContent =
        `MONITORING RETRY ${retries} · ${error.message} · job ${id} remains recoverable at this URL.`;
      await abortableDelay(Math.min(5000, 250 * 2 ** retries), signal);
      continue;
    }
    const progressKey = JSON.stringify([job.status, job.progress]);
    if (progressKey !== lastProgressKey) {
      lastProgressKey = progressKey;
      lastProgressAt = Date.now();
    }
    const stale = job.status === "running" && Date.now() - lastProgressAt > 30000;
    elements["job-status"].textContent = stale
      ? `STALE JOB · ${jobProgressLabel(job)} · Monitoring continues; stop monitoring or reload this job URL to recover.`
      : jobProgressLabel(job);
    if (job.status === "cancelled") {
      throw new DOMException("Simulation cancelled.", "AbortError");
    }
    if (job.status === "failed") throw new Error(job.error);
    if (job.status === "complete") {
      return { ...job.report, localArchive: job.archive };
    }
    await abortableDelay(250, signal);
  }
}

async function watchJob(id) {
  jobPollingController?.abort();
  const controller = new AbortController();
  jobPollingController = controller;
  activeJobId = id;
  elements["stop-job-watch"].hidden = false;
  try {
    return await pollJob(id, { signal: controller.signal });
  } finally {
    if (jobPollingController === controller) {
      jobPollingController = null;
      elements["stop-job-watch"].hidden = true;
    }
    if (activeJobId === id) activeJobId = null;
  }
}

async function cancelActiveJob() {
  const id = activeJobId;
  jobPollingController?.abort();
  if (!id) return;
  elements["job-status"].textContent = "CANCELLING SIMULATION";
  try {
    const response = await apiFetch(`/api/simulations/${id}/cancel`, {
      method: "POST"
    });
    const job = await response.json();
    if (!response.ok) throw new Error(job.error || copy.errors.readJob);
    elements["job-status"].textContent = "SIMULATION CANCELLED";
    history.replaceState(null, "", window.location.pathname);
  } catch (error) {
    elements["job-status"].textContent = `${copy.status.failed} · ${error.message}`;
  }
}

function formatPercent(value) {
  if (!Number.isFinite(value)) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

function renderAnalysisMetricOptions() {
  for (const id of [
    "analysis-trajectory-metric",
    "analysis-scatter-x",
    "analysis-scatter-y",
    "analysis-scatter-size",
    "analysis-heatmap-metric"
  ]) {
    const element = elements[id];
    if (element.options.length) continue;
    element.innerHTML = visualizationMetrics(visualizationLabels).map((metric) =>
      `<option value="${metric.id}">${metric.label}</option>`
    ).join("");
  }
  elements["analysis-trajectory-metric"].value = "score";
  elements["analysis-scatter-x"].value = "capability";
  elements["analysis-scatter-y"].value = "winShare";
  elements["analysis-scatter-size"].value = "score";
  elements["analysis-heatmap-metric"].value = "winShare";
}

function svgLineChart(trajectory) {
  const width = 720;
  const height = 260;
  const padding = { top: 20, right: 18, bottom: 34, left: 42 };
  const allValues = trajectory.series.flatMap((series) => series.points);
  if (!allValues.length) return "<p class=\"muted\">This sample has no replay snapshots.</p>";
  const minimum = Math.min(0, ...allValues);
  const maximum = Math.max(1, ...allValues);
  const span = Math.max(1, maximum - minimum);
  const x = (index, count) => padding.left + index / Math.max(1, count - 1) * (width - padding.left - padding.right);
  const y = (value) => height - padding.bottom - (value - minimum) / span * (height - padding.top - padding.bottom);
  const grid = Array.from({ length: 5 }, (_, index) => {
    const value = minimum + span * index / 4;
    const position = y(value);
    return `<path d="M${padding.left} ${position}H${width - padding.right}" class="chart-grid"/><text x="${padding.left - 8}" y="${position + 4}" text-anchor="end">${value.toFixed(1)}</text>`;
  }).join("");
  const lines = trajectory.series.map((series, index) => {
    const points = series.points.map((value, pointIndex) => `${x(pointIndex, series.points.length)},${y(value)}`).join(" ");
    return `<polyline points="${points}" class="trajectory-line" style="--chart-color:${analysisColors[index % analysisColors.length]}"/>`;
  }).join("");
  return `<svg viewBox="0 0 ${width} ${height}" aria-label="Recorded ${escapeHtml(trajectory.metric)} trajectory" preserveAspectRatio="none">${grid}${lines}<text x="${padding.left}" y="${height - 8}">match start</text><text x="${width - padding.right}" y="${height - 8}" text-anchor="end">final reported standing</text></svg>`;
}

function renderTrajectory(games) {
  const selectedId = elements["analysis-sample"].value;
  elements["analysis-sample"].innerHTML = games.map((game) =>
    `<option value="${game.id}">${escapeHtml(game.label)}</option>`
  ).join("");
  const selected = games.find((game) => game.id === selectedId) || games[0];
  if (!selected) {
    elements["analysis-trajectory"].innerHTML = "<p class=\"muted\">Load a tournament report with a sampled replay to inspect a game.</p>";
    elements["analysis-trajectory-legend"].replaceChildren();
    elements["analysis-trajectory-note"].textContent = "No replay evidence is loaded.";
    return;
  }
  elements["analysis-sample"].value = selected.id;
  const trajectory = trajectoryForSample(
    selected.sample,
    elements["analysis-trajectory-metric"].value,
    visualizationLabels
  );
  elements["analysis-trajectory"].innerHTML = svgLineChart(trajectory);
  elements["analysis-trajectory-note"].textContent =
    `${trajectory.metric} at recorded state transitions, followed by the authoritative final standing. This is observed replay evidence, not a forecast.`;
  elements["analysis-trajectory-legend"].innerHTML = trajectory.series.map((series, index) => `
    <span><i style="--chart-color:${analysisColors[index % analysisColors.length]}"></i>${escapeHtml(series.name)} · ${escapeHtml(series.profileId)} · ${escapeHtml(series.backendId)} · ${escapeHtml(series.model || "provider default")} · ${escapeHtml(series.reasoningEffort || "default effort")}</span>
  `).join("");
}

function renderHeatmap(rows) {
  const map = heatmapCells(rows, elements["analysis-heatmap-metric"].value, visualizationLabels);
  const values = [...map.cells.values()];
  const max = Math.max(...values, 1);
  elements["analysis-heatmap"].innerHTML = `
    <div class="heatmap-grid" style="--heatmap-columns:${map.profiles.length}">
      <span></span>${map.profiles.map((profile) => `<strong>${escapeHtml(profile)}</strong>`).join("")}
      ${map.factions.map((faction) => `
        <strong>${escapeHtml(faction)}</strong>
        ${map.profiles.map((profile) => {
          const value = map.cells.get(`${faction}|${profile}`);
          if (value === undefined) return "<span class=\"heatmap-cell empty\">-</span>";
          return `<span class="heatmap-cell" style="--heatmap-intensity:${Math.max(0.12, value / max)}" title="${escapeHtml(faction)} / ${escapeHtml(profile)}: ${value.toFixed(3)}">${value.toFixed(2)}</span>`;
        }).join("")}
      `).join("")}
    </div>
    <p class="muted">Cell value: ${escapeHtml(map.metric)}. Empty cells have no sampled game with that faction-persona pairing.</p>
  `;
}

function metricLabel(id) {
  return visualizationMetrics(visualizationLabels).find((metric) => metric.id === id)?.label || id;
}

function renderScatter(rows) {
  const xMetric = elements["analysis-scatter-x"].value;
  const yMetric = elements["analysis-scatter-y"].value;
  const sizeMetric = elements["analysis-scatter-size"].value;
  const value = (row, metric) => row[metric] || 0;
  const xValues = rows.map((row) => value(row, xMetric));
  const yValues = rows.map((row) => value(row, yMetric));
  const sizeValues = rows.map((row) => value(row, sizeMetric));
  if (!rows.length) {
    elements["analysis-scatter"].innerHTML = "<p class=\"muted\">No sampled standings are available for this comparison.</p>";
    return;
  }
  const width = 500;
  const height = 300;
  const pad = 42;
  const extent = (values) => [Math.min(...values, 0), Math.max(...values, 1)];
  const [minX, maxX] = extent(xValues);
  const [minY, maxY] = extent(yValues);
  const maxSize = Math.max(...sizeValues, 1);
  const scale = (number, min, max, start, end) => start + (number - min) / Math.max(1e-9, max - min) * (end - start);
  const dots = rows.map((row, index) => {
    const cx = scale(value(row, xMetric), minX, maxX, pad, width - pad);
    const cy = scale(value(row, yMetric), minY, maxY, height - pad, pad);
    const radius = 5 + 17 * Math.sqrt(value(row, sizeMetric) / maxSize);
    const title = `${row.factionName} / ${row.profileId}: ${metricLabel(xMetric)} ${value(row, xMetric).toFixed(2)}, ${metricLabel(yMetric)} ${value(row, yMetric).toFixed(2)}`;
    return `<circle cx="${cx}" cy="${cy}" r="${radius}" style="--chart-color:${analysisColors[index % analysisColors.length]}" class="scatter-dot"><title>${escapeHtml(title)}</title></circle>`;
  }).join("");
  elements["analysis-scatter"].innerHTML = `<svg viewBox="0 0 ${width} ${height}" aria-label="Aggregate scatter plot"><path d="M${pad} ${pad}V${height - pad}H${width - pad}" class="chart-axis"/>${dots}<text x="${width / 2}" y="${height - 8}" text-anchor="middle">${escapeHtml(metricLabel(xMetric))}</text><text x="14" y="${height / 2}" transform="rotate(-90 14 ${height / 2})" text-anchor="middle">${escapeHtml(metricLabel(yMetric))}</text></svg>`;
  elements["analysis-scatter-note"].textContent =
    `One point per observed faction-persona pairing. Point area represents ${metricLabel(sizeMetric)}; color distinguishes pairings, not a balance verdict.`;
}

function renderLlmEvidence(reports) {
  const providers = providerSummary(reports);
  if (!providers.length) {
    elements["analysis-llm"].innerHTML = "<p class=\"muted\">No provider receipts are present in the loaded sampled games.</p>";
    return;
  }
  elements["analysis-llm"].innerHTML = providers.map((provider) => `
    <article>
      <h4>${escapeHtml(provider.actualProvider)}${
        provider.attemptedProvider === provider.actualProvider
          ? ""
          : ` <small>after ${escapeHtml(provider.attemptedProvider)}</small>`
      }</h4>
      <dl>
        <dt>Model / effort</dt><dd>${escapeHtml(provider.actualModel || "provider default")} · ${escapeHtml(provider.actualReasoningEffort || "default effort")}</dd>
        <dt>Attempted model / effort</dt><dd>${escapeHtml(provider.attemptedModel || "provider default")} · ${escapeHtml(provider.attemptedReasoningEffort || "default effort")}</dd>
        <dt>Recorded decisions</dt><dd>${provider.decisions.toFixed(0)}</dd>
        <dt>Attempted-provider latency</dt><dd>${provider.latencyDecisions ? `${(provider.meanLatencyMs / 1000).toFixed(2)}s` : "not recorded"}</dd>
        <dt>Fallbacks</dt><dd>${provider.fallbacks}</dd>
        <dt>Seat appearances</dt><dd>${provider.appearances}</dd>
      </dl>
    </article>
  `).join("");
}

function analysisGroupElement() {
  let select = document.getElementById("analysis-group");
  if (!select) {
    const label = document.createElement("label");
    label.textContent = "Evidence identity";
    select = document.createElement("select");
    select.id = "analysis-group";
    label.append(select);
    elements["analysis-trajectory-metric"].closest(".analysis-controls").prepend(label);
  }
  if (!select.dataset.analysisGroupBound) {
    select.addEventListener("change", renderAnalysis);
    select.dataset.analysisGroupBound = "true";
  }
  return select;
}

function selectAnalysisGroup(groups) {
  const select = analysisGroupElement();
  const selectedKey = select.value;
  const sortedGroups = [...groups].sort((left, right) => right.reports.length - left.reports.length);
  select.innerHTML = sortedGroups.map((group) => {
    const [version, rulesetFingerprint, engineFingerprint] = group.key.split("|");
    return `<option value="${escapeHtml(group.key)}">Game ${escapeHtml(version)} · rules ${shortFingerprint(rulesetFingerprint)} · engine ${shortFingerprint(engineFingerprint)} (${group.reports.length})</option>`;
  }).join("");
  const selected = sortedGroups.find((group) => group.key === selectedKey) || sortedGroups[0];
  if (selected) select.value = selected.key;
  return selected;
}

function renderAnalysis() {
  renderAnalysisMetricOptions();
  const groups = compatibleReportGroups(analysisReports);
  const active = selectAnalysisGroup(groups);
  const reports = active?.reports || [];
  const games = sampledGames(reports);
  const identifiedReports = groups.reduce((total, group) => total + group.reports.length, 0);
  const incompleteIdentityReports = analysisReports.length - identifiedReports;
  const sourceDescription = active
    ? `${reports.length} compatible report${reports.length === 1 ? "" : "s"}, ${games.length} sampled game${games.length === 1 ? "" : "s"}`
    : "No reports loaded";
  const notices = [];
  if (groups.length > 1) notices.push(`${groups.length - 1} other compatible identity group(s) remain available in the selector.`);
  if (incompleteIdentityReports) notices.push(`${incompleteIdentityReports} report(s) lack a complete game/ruleset/engine identity and are not aggregated.`);
  elements["analysis-status"].textContent = `${sourceDescription}. Aggregate plots use only recorded samples and retain their report identities.${notices.length ? ` ${notices.join(" ")}` : ""}`;
  renderTrajectory(games);
  const rows = aggregateFactionPersona(reports);
  renderHeatmap(rows);
  renderScatter(rows);
  renderLlmEvidence(reports);
}

function setAnalysisReports(reports) {
  analysisReports = reports;
  renderAnalysis();
}

async function addAnalysisFiles(files) {
  const loaded = await Promise.all([...files].map(async (file) => normalizeSimulationReport(JSON.parse(await file.text()))));
  setAnalysisReports([...analysisReports, ...loaded]);
  return loaded;
}

function summaryCard(label, value, note) {
  return `
    <div class="summary-card">
      <span class="eyebrow">${label}</span>
      <strong>${value}</strong>
      <small>${note}</small>
    </div>
  `;
}

function renderSummary() {
  const best = [...report.profiles].sort((left, right) => right.winShare - left.winShare)[0];
  const eligibility = report.seats.reduce((sum, seat) => sum + seat.agiEligibilityRate, 0) /
    report.seats.length;
  const totalFallbacks = report.seats.reduce((sum, seat) => sum + seat.policyFallbacks, 0);
  elements["summary-cards"].innerHTML = [
    summaryCard(
      copy.labels.matches,
      report.runs,
      interpolate(copy.notes.playerProfile, { players: report.playerCount })
    ),
    summaryCard(copy.labels.highestPersonaShare, formatPercent(best.winShare), best.profileId),
    summaryCard(copy.labels.agiEligibility, formatPercent(eligibility), copy.notes.meanAcrossSeats),
    summaryCard(
      copy.labels.agiEmergence,
      formatPercent(report.diagnostics.agiEmergenceRate),
      "qualified declaration"
    ),
    summaryCard(
      copy.labels.openContinuity,
      formatPercent(report.diagnostics.openContinuityRate),
      "Collective Trust and Systemic Risk"
    ),
    summaryCard(
      copy.labels.nonDeclaringWins,
      formatPercent(report.diagnostics.nonDeclaringWinRate),
      "institutional winner did not form AGI"
    ),
    summaryCard(
      copy.labels.llmFallbacks,
      totalFallbacks,
      interpolate(copy.notes.llmCalls, {
        calls: report.configuration?.usedLlmDecisions || 0
      })
    )
  ].join("");
}

function formatWeights(weights) {
  return Object.entries(weights)
    .sort((left, right) => right[1] - left[1])
    .map(([key, value]) => `<li><span>${key.replaceAll("_", " ")}</span><strong>${value}</strong></li>`)
    .join("");
}

function renderExperimentReport() {
  elements["experiment-results"].hidden = false;
  elements["seat-results-section"].hidden = true;
  elements["distribution-section"].hidden = true;
  elements["replay-section"].hidden = true;
  elements["summary-cards"].replaceChildren();
  if (report.diagnosticKind === "paired_faction_swap") {
    const execution = report.execution;
    const llm = execution.llm;
    elements["results-title"].textContent = copy.modes.factionSwap.completed;
    elements["results-subtitle"].textContent =
      `${report.preRegistration.id} · ${report.scheduledRuns} scheduled arms · seed ${report.seed}`;
    elements["summary-cards"].innerHTML = [
      summaryCard(
        copy.execution.cpuArms,
        execution.workers,
        `${execution.scheduler} · ${execution.taskUnit}`
      ),
      summaryCard(
        copy.execution.peakLlmCalls,
        llm?.peakActiveLlmCalls || 0,
        `configured ${execution.llmConcurrency || 0}`
      ),
      summaryCard(
        copy.execution.providerThrottling,
        llm?.throttledRequests || 0,
        llm
          ? Object.entries(llm.providerConcurrency)
            .map(([provider, limit]) => `${provider} ${limit}`)
            .join(" · ")
          : copy.execution.deterministicOnly
      ),
      summaryCard(
        copy.execution.quarantined,
        execution.quarantinedMatches,
        report.quarantine.policy.replaceAll("_", " ")
      )
    ].join("");
    elements["experiment-results-title"].textContent = copy.execution.summary;
    elements["experiment-results-body"].innerHTML = `
      <table>
        <thead><tr>
          <th>${copy.execution.comparison}</th>
          <th>${copy.execution.paired}</th>
          <th>${copy.execution.mandateDelta}</th>
          <th>${copy.execution.rankAdvantage}</th>
        </tr></thead>
        <tbody>${report.comparisons.map((comparison) => `
          <tr>
            <td>${escapeHtml(comparison.id)}</td>
            <td>${comparison.paired.pairs}/${comparison.paired.scheduledPairs}</td>
            <td>${comparison.paired.meanMandateDelta.toFixed(2)}</td>
            <td>${comparison.paired.meanRankAdvantage.toFixed(3)}</td>
          </tr>
        `).join("")}</tbody>
      </table>
    `;
  } else if (report.reportType === "strategy_evolution") {
    const final = report.history.at(-1);
    const baseline = report.history[0].candidates.find((candidate) =>
      candidate.profile.actionWeights &&
      JSON.stringify(candidate.profile.actionWeights) ===
        JSON.stringify(report.baselineProfile.strategy.actionWeights)
    ) || report.history[0].candidates.at(-1);
    elements["results-title"].textContent =
      `${report.generations} strategy generations completed`;
    elements["results-subtitle"].textContent =
      `${report.targetProfileId} · ${report.population} candidates/generation · every seat · seed ${report.seed}`;
    elements["summary-cards"].innerHTML = [
      summaryCard(
        copy.labels.championFitness,
        final.champion.fitness.toFixed(3),
        copy.notes.simulationObjective
      ),
      summaryCard(
        copy.labels.championWinShare,
        formatPercent(final.champion.meanWinShare),
        copy.notes.meanAcrossSeats
      ),
      summaryCard(
        copy.labels.baselineFitness,
        baseline.evaluation.fitness.toFixed(3),
        copy.notes.generationIncumbent
      ),
      summaryCard(copy.labels.evaluatedMatches,
        report.generations * report.population * report.evaluatedMatchesPerCandidate,
        copy.notes.commonSeededMatches)
    ].join("");
    elements["experiment-results-title"].textContent = copy.results.evolvedStrategy;
    elements["experiment-results-body"].innerHTML = `
      <div class="experiment-grid">
        <article>
          <h3>${copy.results.championWeights}</h3>
          <ul class="weight-list">${formatWeights(report.championProfile.strategy.actionWeights)}</ul>
        </article>
        <article>
          <h3>${copy.results.generationHistory}</h3>
          <ol class="generation-list">
            ${report.history.map((generation) => `
              <li>
                <strong>Generation ${generation.generation}</strong>
                fitness ${generation.champion.fitness.toFixed(3)} ·
                win ${formatPercent(generation.champion.meanWinShare)}
              </li>
            `).join("")}
          </ol>
        </article>
      </div>
      <p class="callout">This profile is a tested candidate. Download the report to review every mutation before adopting it.</p>
    `;
  } else if (report.reportType === "unified_matrix_audit") {
    const gate = report.balanceEvaluation;
    const matrix = copy.matrix;
    elements["results-title"].textContent = matrix.completed;
    elements["results-subtitle"].textContent = interpolate(matrix.subtitle, {
      runs: report.runs,
      cells: report.design.cellCount,
      seed: report.seed
    });
    elements["summary-cards"].innerHTML = [
      summaryCard(copy.labels.automatedGate, gate.status.replaceAll("_", " "), matrix.humanApproval),
      summaryCard(copy.labels.matchupCoverage,
        `${report.playerCounts.length} player counts`, matrix.frameNote),
      summaryCard(copy.labels.bestResponseGain,
        report.balanceEvaluation.maximumCoreHalfWidth.toFixed(3), matrix.halfWidthNote),
      summaryCard(copy.labels.counterRecovery,
        formatPercent(report.cooperation.betrayalRate), matrix.betrayalNote)
    ].join("");
    elements["experiment-results-title"].textContent = matrix.uncertaintyTitle;
    elements["experiment-results-body"].innerHTML = `
      <div class="experiment-grid">
        <article>
          <h3>${matrix.promotionGate}</h3>
          <p><strong>${gate.promotionGate.verdict.replaceAll("_", " ")}</strong></p>
          <ul>${gate.promotionGate.reasons.map((reason) => `<li>${reason}</li>`).join("")}</ul>
        </article>
        <article>
          <h3>${matrix.dominanceCells}</h3>
          <ul>${gate.dominance.map((entry) =>
            `<li>${entry.familyId}: ${entry.id} · n=${entry.exposure}</li>`
          ).join("") || `<li>${matrix.noDominance}</li>`}</ul>
        </article>
        <article>
          <h3>${matrix.pairwiseDominance}</h3>
          <ul>${gate.pairwiseDominance.map((entry) =>
            `<li>${entry.id} · n=${entry.exposure}</li>`
          ).join("") || `<li>${matrix.noPairwiseDominance}</li>`}</ul>
        </article>
        <article>
          <h3>${matrix.metaCycles}</h3>
          <p>${report.inference.credibleMetaCycles.count}</p>
        </article>
      </div>
      <table>
        <thead><tr><th>${matrix.family}</th><th>${matrix.cells}</th><th>${matrix.grandMean}</th><th>${matrix.priorPrecision}</th></tr></thead>
        <tbody>${Object.entries(report.inference.families).map(([id, family]) => `
          <tr><td>${id}</td><td>${family.cells.length}</td>
          <td>${formatPercent(family.grandMean)}</td><td>${family.prior.precision.toFixed(1)}</td></tr>
        `).join("")}</tbody>
      </table>
    `;
  } else if (report.reportType === "llm_negotiation_holdout") {
    const holdout = copy.holdout;
    const receipts = (report.observations || []).flatMap((observation) =>
      observation.standings.flatMap((standing) => standing.policyReceipts || [])
    );
    const fresh = receipts.filter((entry) => entry.provider.includes("cli") && !entry.cached);
    const attempted = receipts.filter((entry) =>
      !entry.cached &&
      (entry.provider.includes("cli") || entry.attemptedProvider?.includes("cli"))
    );
    const cached = receipts.filter((entry) => entry.cached);
    const broken = report.matchMetrics?.negotiationOutcomes?.broken || 0;
    elements["results-title"].textContent = holdout.completed;
    elements["results-subtitle"].textContent =
      `${report.preRegistration.id} · ${report.preRegistration.purpose} · seed ${report.seed}`;
    elements["summary-cards"].innerHTML = [
      summaryCard(holdout.freshDecisions, fresh.length, holdout.freshNote),
      summaryCard(
        holdout.providerAttempts,
        attempted.length,
        holdout.providerAttemptsNote
      ),
      summaryCard(holdout.cachedDecisions, cached.length, holdout.cachedNote),
      summaryCard(holdout.brokenPromises, broken, holdout.brokenNote),
      summaryCard(copy.labels.fallbacks,
        report.seats.reduce((sum, seat) => sum + seat.policyFallbacks, 0),
        holdout.fallbackNote)
    ].join("");
    elements["experiment-results-title"].textContent = holdout.provenanceTitle;
    elements["experiment-results-body"].innerHTML = `
      <p class="callout">${report.preRegistration.analysis.interpretationBoundary}</p>
      <dl>
        <dt>${holdout.registrationCommit}</dt><dd>${report.preRegistration.registrationCommit}</dd>
        <dt>${holdout.planFingerprint}</dt><dd>${report.preRegistration.fingerprint}</dd>
        <dt>${holdout.sourceClean}</dt><dd>${String(report.provenance.sourceDirty === false)}</dd>
        <dt>${holdout.providers}</dt><dd>${report.configuration.cliProviders.map((entry) =>
          `${entry.provider} ${entry.version || "unknown"} · ${(entry.models || [entry.model || "default model unresolved"]).join(", ")} · ${(entry.reasoningEfforts || [entry.reasoningEffort || "default effort unresolved"]).join(", ")}`
        ).join("<br>")}</dd>
      </dl>
    `;
  } else {
    const baseline = report.baseline;
    const recommendation = report.recommendation;
    const changed = Object.entries(recommendation.variant)
      .filter(([key, value]) => baseline.variant[key] !== value);
    elements["results-title"].textContent =
      `${report.iterations} rule variants compared`;
    elements["results-subtitle"].textContent =
      `${report.runsPerVariant} common-seed matches/variant · seed ${report.seed}`;
    elements["summary-cards"].innerHTML = [
      summaryCard(
        copy.labels.bestBalanceLoss,
        recommendation.fitness.toFixed(3),
        copy.notes.lowerIsBetter
      ),
      summaryCard(copy.labels.baselineLoss, baseline.fitness.toFixed(3), copy.notes.canonicalValues),
      summaryCard(copy.labels.factionSpread,
        formatPercent(recommendation.diagnostics.factionWinShareRange),
        copy.notes.bestVariant),
      summaryCard(copy.labels.agiDeclaration,
        formatPercent(recommendation.diagnostics.agiDeclarationRate),
        interpolate(copy.notes.target, { target: formatPercent(report.targetAgiRate) }))
    ].join("");
    elements["experiment-results-title"].textContent = copy.results.recommendedVariant;
    elements["experiment-results-body"].innerHTML = `
      <div class="experiment-grid">
        <article>
          <h3>${copy.results.changesFromBaseline}</h3>
          <ul class="weight-list">
            ${changed.length ? changed.map(([key, value]) =>
              `<li><span>${key}</span><strong>${baseline.variant[key]} → ${value}</strong></li>`
            ).join("") : "<li>No mutation beat the baseline.</li>"}
          </ul>
        </article>
        <article>
          <h3>${copy.results.rankedVariants}</h3>
          <ol class="generation-list">
            ${report.evaluations.slice(0, 10).map((entry) => `
              <li><strong>loss ${entry.fitness.toFixed(3)}</strong> ·
                faction spread ${formatPercent(entry.diagnostics.factionWinShareRange)} ·
                action diversity ${formatPercent(entry.diagnostics.actionDiversity)}
              </li>
            `).join("")}
          </ol>
        </article>
      </div>
      <p class="callout">Recommendation only. The simulator never edits the canonical rulebook.</p>
    `;
  }
}

function renderSeatResults() {
  const aggregateCard = (entry, label, index) => `
    <article class="seat-result" style="--seat-color:${seatColors[index % seatColors.length]}">
      <p class="eyebrow">${label}</p>
      <h3>${entry.factionId || entry.profileId}</h3>
      <dl>
        <dt>${copy.labels.winShare}</dt><dd>${formatPercent(entry.winShare)}</dd>
        <dt>${copy.labels.meanMandate}</dt><dd>${entry.meanScore.toFixed(2)}</dd>
        <dt>${copy.labels.capability}</dt><dd>${entry.meanCapability.toFixed(2)}</dd>
        <dt>${copy.labels.customers}</dt><dd>${entry.meanCustomers.toFixed(2)}</dd>
        <dt>${copy.labels.facilities}</dt><dd>${entry.meanFacilities.toFixed(2)}</dd>
        <dt>${copy.labels.auditHits}</dt><dd>${entry.meanAuditHits.toFixed(2)}</dd>
        <dt>${copy.labels.agiDeclared}</dt><dd>${formatPercent(entry.agiDeclarationRate)}</dd>
        <dt>${copy.labels.shovelsIncome}</dt><dd>${entry.meanShovelsIncome.toFixed(2)}</dd>
      </dl>
    </article>
  `;
  elements["faction-results"].innerHTML = report.factions
    .sort((left, right) => right.winShare - left.winShare)
    .map((entry, index) => aggregateCard(entry, copy.labels.faction, index))
    .join("");
  elements["profile-results"].innerHTML = report.profiles
    .sort((left, right) => right.winShare - left.winShare)
    .map((entry, index) => aggregateCard(entry, copy.labels.persona, index))
    .join("");
  elements["seat-results"].innerHTML = report.seats.map((seat) => `
    <article class="seat-result" style="--seat-color:${seatColors[seat.seat]}">
      <p class="eyebrow">Seat ${seat.seat + 1} · rotating factions</p>
      <h3>${
        seat.profileIds?.length > 1
          ? copy.labels.rotatingPersonas
          : seat.profileIds?.[0] || copy.labels.persona
      }</h3>
      <dl>
        <dt>${copy.labels.winShare}</dt><dd>${formatPercent(seat.winShare)}</dd>
        <dt>${copy.labels.meanMandate}</dt><dd>${seat.meanScore.toFixed(2)}</dd>
        <dt>${copy.labels.capability}</dt><dd>${seat.meanCapability.toFixed(2)}</dd>
        <dt>${copy.labels.customers}</dt><dd>${seat.meanCustomers.toFixed(2)}</dd>
        <dt>${copy.labels.facilities}</dt><dd>${seat.meanFacilities.toFixed(2)}</dd>
        <dt>${copy.labels.auditHits}</dt><dd>${seat.meanAuditHits.toFixed(2)}</dd>
        <dt>${copy.labels.agiEligible}</dt><dd>${formatPercent(seat.agiEligibilityRate)}</dd>
        <dt>${copy.labels.fallbacks}</dt><dd>${seat.policyFallbacks}</dd>
      </dl>
    </article>
  `).join("");
}

function renderDistributions() {
  elements["score-distributions"].innerHTML = report.seats.map((seat) => {
    const entries = Object.entries(seat.scoreDistribution)
      .map(([score, count]) => [Number(score), count])
      .sort((left, right) => left[0] - right[0]);
    const maximum = Math.max(...entries.map((entry) => entry[1]));
    return `
      <div class="distribution" style="--seat-color:${seatColors[seat.seat]}">
        <div>
          <p class="eyebrow">Seat ${seat.seat + 1}</p>
          <h3>${
            seat.profileIds?.length > 1
              ? copy.labels.rotatingPersonas
              : seat.profileIds?.[0] || copy.labels.persona
          }</h3>
          <small>${interpolate(copy.replay.scoreRange, {
            minimum: entries[0][0],
            maximum: entries.at(-1)[0]
          })}</small>
        </div>
        <div class="histogram" aria-label="${
          interpolate(copy.labels.scoreHistogram, { seat: seat.seat + 1 })
        }">
          ${entries.map(([score, count]) => `
            <i class="histogram-bar" style="--height:${Math.max(3, count / maximum * 105)}px"
              title="${interpolate(copy.replay.histogramEntry, { score, matches: count })}"></i>
          `).join("")}
        </div>
      </div>
    `;
  }).join("");
}

function replayPosition(tile) {
  const size = window.innerWidth <= 680 ? 96 : 122;
  const originX = window.innerWidth <= 680 ? 245 : 385;
  const originY = window.innerWidth <= 680 ? 250 : 285;
  return {
    size,
    ...pointyTopAxialPosition(tile, {
      width: size,
      height: size * 0.87,
      originX,
      originY
    })
  };
}

function replayEvent() {
  return report.samples[Number(elements["replay-sample"].value)]?.replay?.[replayIndex];
}

function replayDecisionProvenance(event) {
  const receipt = event.decisionReceipt;
  if (!receipt) return "";
  const provider = receipt.provider || receipt.attemptedProvider || "unknown provider";
  const model = receipt.model || receipt.attemptedModel || "provider default";
  const effort = receipt.reasoningEffort || receipt.attemptedReasoningEffort || "default effort";
  return ` · ${provider} / ${model} / ${effort}${receipt.fallback ? " (fallback)" : ""}`;
}

function renderReplay() {
  if (!report) return;
  const sample = report.samples[Number(elements["replay-sample"].value)];
  const event = replayEvent();
  if (!sample || !event) {
    elements["replay-caption"].textContent = copy.results.noReplay;
    elements["replay-board"].replaceChildren();
    return;
  }
  elements["replay-step"].max = sample.replay.length - 1;
  elements["replay-step"].value = replayIndex;
  elements["replay-caption"].textContent = interpolate(copy.replay.step, {
    step: replayIndex + 1,
    steps: sample.replay.length,
    round: event.round,
    cycle: event.cycle,
    summary: `${event.summary}${replayDecisionProvenance(event)}`
  });
  elements["replay-board"].replaceChildren();

  for (const tile of event.state.board) {
    const hex = document.createElement("div");
    const position = replayPosition(tile);
    hex.className = `hex ${tile.category}`;
    hex.style.left = `${position.left}px`;
    hex.style.top = `${position.top}px`;
    hex.style.width = `${position.size}px`;
    hex.style.height = `${position.size * 0.87}px`;
    const markers = [];
    for (const player of event.state.players) {
      const color = seatColors[player.seat];
      for (const piece of player.pieces.filter((item) => item.tileId === tile.instanceId)) {
        markers.push(
          `<i class="replay-marker" style="--seat-color:${color}" title="${
            interpolate(copy.replay.marker, { seat: player.seat + 1, kind: piece.kind })
          }"></i>`
        );
      }
      for (const facility of player.facilities.filter((item) => item.tileId === tile.instanceId)) {
        markers.push(
          `<i class="replay-marker facility" style="--seat-color:${color}" title="${
            interpolate(copy.replay.marker, { seat: player.seat + 1, kind: copy.labels.facility })
          }"></i>`
        );
      }
      for (const generator of player.generators.filter((item) => item.tileId === tile.instanceId)) {
        markers.push(
          `<i class="replay-marker generator" style="--seat-color:${color}" title="${
            interpolate(copy.replay.marker, { seat: player.seat + 1, kind: copy.labels.generator })
          }"></i>`
        );
      }
    }
    hex.innerHTML = `
      <span class="hex-name">${tile.name}</span>
      <span class="hex-type">${tile.category}</span>
      <span class="replay-markers">${markers.join("")}</span>
    `;
    elements["replay-board"].append(hex);
  }

  elements["replay-players"].innerHTML = event.state.players.map((player) => `
    <article class="replay-player" style="--seat-color:${seatColors[player.seat]}">
      <p class="eyebrow">Seat ${player.seat + 1} · ${player.profileId}</p>
      <h3>${player.factionName}</h3>
      <p class="muted">${escapeHtml(player.backendId)} · ${escapeHtml(player.model || "provider default")} · ${escapeHtml(player.reasoningEffort || "default effort")}</p>
      <dl>
        <dt>${copy.labels.runway}</dt><dd>${player.runway}</dd>
        <dt>${copy.labels.compute}</dt><dd>${player.compute}</dd>
        <dt>${copy.labels.capability}</dt><dd>${player.capability}</dd>
        <dt>${copy.labels.customers}</dt><dd>${player.customers}</dd>
        <dt>${copy.labels.trust}</dt><dd>${player.trust}</dd>
        <dt>${copy.labels.scrutiny}</dt><dd>${player.scrutiny}</dd>
        <dt>${copy.labels.facilities}</dt><dd>${player.facilities.length}</dd>
      </dl>
    </article>
  `).join("");
}

function renderCoverage() {
  const automated = report.scope.automated || [report.scope.verdictBoundary];
  const excluded = report.scope.excluded || [];
  elements.coverage.innerHTML = `
    <div>
      <h3>${copy.results.automated}</h3>
      <ul>${automated.map((item) => `<li>${item}</li>`).join("")}</ul>
    </div>
    <div>
      <h3>${copy.results.excluded}</h3>
      <ul>${excluded.map((item) => `<li>${item}</li>`).join("")}</ul>
    </div>
  `;
}

function showReport(nextReport, { preserveAnalysis = false } = {}) {
  rawReport = structuredClone(nextReport);
  report = normalizeSimulationReport(nextReport);
  if (preserveAnalysis) {
    renderAnalysis();
  } else {
    setAnalysisReports([report]);
  }
  elements["setup-view"].hidden = true;
  elements["results-view"].hidden = false;
  elements["archive-path"].textContent = report.localArchive
    ? interpolate(copy.results.savedTo, { path: report.localArchive.relativePath })
    : copy.results.loadedWithoutArchive;
  renderEvidenceIdentity();
  elements["experiment-results"].hidden = true;
  elements["seat-results-section"].hidden = false;
  elements["distribution-section"].hidden = false;
  elements["replay-section"].hidden = false;
  if (report.reportType && report.reportType !== "tournament") {
    renderCoverage();
    renderExperimentReport();
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }
  elements["results-title"].textContent = interpolate(
    copy.report.completedMatches,
    { runs: report.runs }
  );
  elements["results-subtitle"].textContent = interpolate(copy.report.subtitle, {
    version: report.game.version,
    scope: report.scope.id,
    seed: report.seed,
    players: report.playerCount,
    boundary: report.scope.verdictBoundary
  });
  renderSummary();
  renderSeatResults();
  renderDistributions();
  renderCoverage();
  elements["replay-sample"].innerHTML = report.samples.map((sample, index) =>
    `<option value="${index}">Match ${index + 1} · ${sample.seed}</option>`
  ).join("");
  replayIndex = 0;
  renderReplay();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function formatReportTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return "Unknown date";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function renderRecentReports(entries) {
  elements["recent-reports"].replaceChildren(...entries.map((entry) => {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "recent-report";
    item.dataset.fileName = entry.fileName;
    const title = document.createElement("strong");
    title.textContent = copy.results.openReport;
    const metadata = document.createElement("span");
    metadata.textContent = `${formatReportTimestamp(entry.modifiedAt)} · ${entry.fileName}`;
    item.append(title, metadata);
    return item;
  }));
}

async function refreshRecentReports() {
  if (bridgeRequired && !bridgeConnected) return;
  elements["refresh-reports"].disabled = true;
  elements["recent-reports-status"].textContent = copy.results.loadingReports;
  try {
    const response = await apiFetch("/api/simulation-reports");
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || copy.results.loadReportError);
    renderRecentReports(body.reports);
    elements["recent-reports-status"].textContent = body.reports.length
      ? ""
      : copy.results.noRecentReports;
  } catch (error) {
    elements["recent-reports-status"].textContent =
      `${copy.results.loadReportError} ${error.message}`;
  } finally {
    elements["refresh-reports"].disabled = false;
  }
}

async function openRecentReport(fileName) {
  elements["recent-reports-status"].textContent = copy.results.loadingReports;
  try {
    const response = await apiFetch(
      `/api/simulation-reports/${encodeURIComponent(fileName)}`
    );
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || copy.results.loadReportError);
    showReport(body);
    elements["recent-reports-status"].textContent = "";
  } catch (error) {
    elements["recent-reports-status"].textContent =
      `${copy.results.loadReportError} ${error.message}`;
  }
}

elements["simulation-form"].addEventListener("submit", async (event) => {
  event.preventDefault();
  elements["run-simulation"].disabled = true;
  elements["job-status"].textContent = copy.status.submitting;
  let jobId = null;
  try {
    const response = await apiFetch("/api/simulations", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(simulationOptions())
    });
    const job = await response.json();
    if (!response.ok) throw new Error(job.error || copy.errors.startJob);
    jobId = job.id;
    history.replaceState(null, "", `?job=${encodeURIComponent(job.id)}`);
    showReport(await watchJob(job.id));
    void refreshRecentReports();
  } catch (error) {
    elements["job-status"].textContent = error?.name === "AbortError"
      ? `SIMULATION CANCELLED · job ${jobId || "unknown"} will not publish a report.`
      : `${copy.status.failed} · ${error.message}`;
  } finally {
    updateRunAvailability();
  }
});

elements["sim-player-count"].addEventListener("change", renderSeats);
function renderExperimentMode({ resetDefaults = false } = {}) {
  const mode = elements["experiment-mode"].value;
  const optimizing = mode !== "tournament";
  elements["optimization-controls"].hidden = !optimizing;
  elements["target-profile-field"].hidden = mode !== "strategy-evolution";
  elements["generations-field"].hidden = mode !== "strategy-evolution";
  elements["population-field"].hidden = mode !== "strategy-evolution";
  elements["iterations-field"].hidden = mode !== "rule-search";
  elements["matrix-initial-field"].hidden = mode !== "balance-audit";
  elements["matrix-batch-field"].hidden = mode !== "balance-audit";
  elements["preregistration-field"].hidden =
    !["llm-holdout", "faction-swap"].includes(mode);
  elements["runs-field"].hidden = mode === "llm-holdout";
  elements["player-count-field"].hidden =
    ["balance-audit", "llm-holdout", "faction-swap"].includes(mode);
  elements["persona-controls"].hidden = optimizing;
  elements["llm-controls"].hidden =
    !["tournament", "llm-holdout", "faction-swap"].includes(mode);
  elements["execution-controls"].hidden = mode !== "faction-swap";
  elements["replay-samples-field"].hidden = optimizing;
  const presentation = {
    tournament: {
      ...copy.modes.tournament,
      runs: copy.modes.tournament.defaultRuns
    },
    "strategy-evolution": {
      ...copy.modes.strategyEvolution,
      runs: copy.modes.strategyEvolution.defaultRuns
    },
    "rule-search": {
      ...copy.modes.ruleSearch,
      runs: copy.modes.ruleSearch.defaultRuns
    },
    "balance-audit": {
      ...copy.modes.balanceAudit,
      runs: copy.modes.balanceAudit.defaultRuns
    },
    "llm-holdout": {
      ...copy.modes.llmHoldout,
      runs: copy.modes.llmHoldout.defaultRuns
    },
    "faction-swap": {
      ...copy.modes.factionSwap,
      runs: copy.modes.factionSwap.defaultRuns
    }
  }[mode];
  elements["runs-label"].textContent = presentation.runsLabel;
  elements["run-simulation"].textContent = presentation.button;
  elements["mode-description"].textContent = presentation.description;
  if (resetDefaults) {
    elements.runs.value = presentation.runs;
    elements["sample-replays"].value = mode === "tournament" ? 3 : 0;
    if (mode === "llm-holdout") {
      elements["preregistration-path"].value =
        "evidence/studies/simulation/preregistrations/llm-negotiation-holdout-v3-capture.json";
    } else if (mode === "faction-swap") {
      elements["preregistration-path"].value =
        "evidence/studies/simulation/preregistrations/faction-swap-diagnostic-v1.json";
    }
  }
}

elements["experiment-mode"].addEventListener("change", () => {
  history.replaceState(
    null,
    "",
    `${window.location.pathname}?mode=${encodeURIComponent(elements["experiment-mode"].value)}`
  );
  renderExperimentMode({ resetDefaults: true });
});
elements["new-simulation"].addEventListener("click", () => {
  void cancelActiveJob();
  history.replaceState(null, "", window.location.pathname);
  elements["results-view"].hidden = true;
  elements["setup-view"].hidden = false;
  elements["job-status"].textContent = "";
});
elements["stop-job-watch"].addEventListener("click", () => void cancelActiveJob());
elements["refresh-reports"].addEventListener("click", () => void refreshRecentReports());
elements["recent-reports"].addEventListener("click", (event) => {
  const button = event.target.closest("button[data-file-name]");
  if (button) void openRecentReport(button.dataset.fileName);
});
elements["download-report"].addEventListener("click", () => {
  const blob = new Blob([JSON.stringify(rawReport, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = [
    "frontier-2038",
    `v${report.game.version}`,
    shortFingerprint(report.game.rulesetFingerprint),
    "simulation",
    report.seed
  ].join("-") + ".json";
  link.click();
  URL.revokeObjectURL(link.href);
});
elements["report-file"].addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (file) showReport(JSON.parse(await file.text()));
});
for (const id of ["analysis-files", "analysis-files-results"]) {
  elements[id].addEventListener("change", async (event) => {
    try {
      const loaded = await addAnalysisFiles(event.target.files);
      if (!report && loaded[0]) showReport(loaded[0], { preserveAnalysis: true });
    } catch (error) {
      elements["job-status"].textContent = `Could not load analysis report: ${error.message}`;
    } finally {
      event.target.value = "";
    }
  });
}
for (const id of [
  "analysis-sample",
  "analysis-trajectory-metric",
  "analysis-scatter-x",
  "analysis-scatter-y",
  "analysis-scatter-size",
  "analysis-heatmap-metric"
]) {
  elements[id].addEventListener("change", renderAnalysis);
}
elements["replay-sample"].addEventListener("change", () => {
  replayIndex = 0;
  renderReplay();
});
elements["replay-step"].addEventListener("input", () => {
  replayIndex = Number(elements["replay-step"].value);
  renderReplay();
});
elements["replay-prev"].addEventListener("click", () => {
  replayIndex = Math.max(0, replayIndex - 1);
  renderReplay();
});
elements["replay-next"].addEventListener("click", () => {
  const sample = report.samples[Number(elements["replay-sample"].value)];
  replayIndex = Math.min((sample?.replay?.length || 1) - 1, replayIndex + 1);
  renderReplay();
});
window.addEventListener("resize", renderReplay);

renderSeats();
elements["target-profile"].innerHTML = profiles.map((profile) =>
  `<option value="${profile.id}">${profile.name}</option>`
).join("");
const searchParameters = new URLSearchParams(window.location.search);
const requestedMode = searchParameters.get("mode");
if ([
  "tournament",
  "strategy-evolution",
  "rule-search",
  "balance-audit",
  "llm-holdout",
  "faction-swap"
].includes(requestedMode)) {
  elements["experiment-mode"].value = requestedMode;
}
renderExperimentMode({ resetDefaults: Boolean(requestedMode) });

const existingJob = searchParameters.get("job");
if (existingJob) {
  elements["run-simulation"].disabled = true;
  elements["job-status"].textContent = copy.status.loadingExisting;
  try {
    showReport(await watchJob(existingJob));
  } catch (error) {
    elements["job-status"].textContent = error?.name === "AbortError"
      ? `SIMULATION CANCELLED · job ${existingJob} will not publish a report.`
      : `${copy.status.failed} · ${error.message}`;
  } finally {
    updateRunAvailability();
  }
}

if (bridgeRequired) {
  elements["bridge-panel"].hidden = false;
  elements["bridge-token"].value = getBridgeToken();
  bridgeConnected = false;
  showBridgeState("Start npm run dev locally, then pair this page.");
  elements["connect-bridge"].addEventListener("click", async () => {
    elements["connect-bridge"].disabled = true;
    showBridgeState("Requesting access to the local bridge…");
    try {
      const status = await connectBridge(elements["bridge-token"].value);
      bridgeConnected = true;
      showBridgeState(
        `Connected · local Node authority · ${status.interactiveBackends.length} interactive backends available.`,
        true
      );
      void refreshRecentReports();
    } catch (error) {
      bridgeConnected = false;
      showBridgeState(error.message);
    } finally {
      elements["connect-bridge"].disabled = false;
      updateRunAvailability();
    }
  });
}
if (!bridgeRequired) void refreshRecentReports();
updateRunAvailability();
