import {
  normalizeSimulationReport
} from "/simulation/contracts/report-migrations.js";
import {
  apiFetch,
  bridgeRequired,
  connectBridge,
  getBridgeToken
} from "./api-client.js";

const seatColors = ["#a45137", "#536e73", "#a98c3f", "#7a657d", "#607d70", "#6c7a89"];
const [profilesDocument, uiCopy] = await Promise.all([
  fetch("/data/player-strategies.json").then((response) => response.json()),
  fetch("/data/ui-copy.json").then((response) => response.json())
]);
const profiles = profilesDocument.profiles;
const copy = uiCopy.simulation;

function interpolate(template, values = {}) {
  return template.replace(/\{([^}]+)\}/g, (match, key) =>
    Object.prototype.hasOwnProperty.call(values, key) ? String(values[key]) : match
  );
}
const elements = Object.fromEntries(
  [
    "allow-llm",
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
    "faction-results",
    "generations",
    "generations-field",
    "iterations",
    "iterations-field",
    "job-status",
    "llm-controls",
    "matrix-batch-field",
    "matrix-batch-size",
    "matrix-initial-field",
    "matrix-initial-runs",
    "max-llm-decisions",
    "model",
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
    "summary-cards",
    "target-profile",
    "target-profile-field",
    "replay-section"
  ].map((id) => [id, document.getElementById(id)])
);

let report = null;
let rawReport = null;
let replayIndex = 0;
let bridgeConnected = !bridgeRequired;

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
    maxLlmDecisions: Number(elements["max-llm-decisions"].value),
    model: elements.model.value || undefined
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
  }
  return options;
}

async function pollJob(id) {
  while (true) {
    const response = await apiFetch(`/api/simulations/${id}`);
    const job = await response.json();
    if (!response.ok) throw new Error(job.error || copy.errors.readJob);
    elements["job-status"].textContent =
      `${job.status.toUpperCase()} · ${job.progress.completed}/${job.progress.total} · ${job.progress.phase}`;
    if (job.status === "failed") throw new Error(job.error);
    if (job.status === "complete") {
      return { ...job.report, localArchive: job.archive };
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
}

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
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
      copy.labels.genuineAgi,
      formatPercent(report.diagnostics.genuineAgiRate),
      "shared World Ending"
    ),
    summaryCard(
      copy.labels.nonDeclaringWins,
      formatPercent(report.diagnostics.nonDeclaringWinRate),
      "institutional winner did not Declare AGI"
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
  if (report.reportType === "strategy_evolution") {
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
        report.generations * report.population * report.runsPerSeat * report.playerCount,
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
          `${entry.provider} ${entry.version || "unknown"} · ${entry.model || "default model unresolved"}`
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
  const width = size * 0.76;
  const height = size * 0.86;
  const originX = window.innerWidth <= 680 ? 245 : 385;
  const originY = window.innerWidth <= 680 ? 250 : 285;
  return {
    size,
    left: originX + width * (tile.q + tile.r / 2) - size / 2,
    top: originY + height * tile.r - (size * 0.87) / 2
  };
}

function replayEvent() {
  return report.samples[Number(elements["replay-sample"].value)]?.replay?.[replayIndex];
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
    summary: event.summary
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

function showReport(nextReport) {
  rawReport = structuredClone(nextReport);
  report = normalizeSimulationReport(nextReport);
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

elements["simulation-form"].addEventListener("submit", async (event) => {
  event.preventDefault();
  elements["run-simulation"].disabled = true;
  elements["job-status"].textContent = copy.status.submitting;
  try {
    const response = await apiFetch("/api/simulations", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(simulationOptions())
    });
    const job = await response.json();
    if (!response.ok) throw new Error(job.error || copy.errors.startJob);
    history.replaceState(null, "", `?job=${encodeURIComponent(job.id)}`);
    showReport(await pollJob(job.id));
  } catch (error) {
    elements["job-status"].textContent = `${copy.status.failed} · ${error.message}`;
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
  elements["preregistration-field"].hidden = mode !== "llm-holdout";
  elements["runs-field"].hidden = mode === "llm-holdout";
  elements["player-count-field"].hidden =
    ["balance-audit", "llm-holdout"].includes(mode);
  elements["persona-controls"].hidden = optimizing;
  elements["llm-controls"].hidden = !["tournament", "llm-holdout"].includes(mode);
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
    }
  }[mode];
  elements["runs-label"].textContent = presentation.runsLabel;
  elements["run-simulation"].textContent = presentation.button;
  elements["mode-description"].textContent = presentation.description;
  if (resetDefaults) {
    elements.runs.value = presentation.runs;
    elements["sample-replays"].value = mode === "tournament" ? 3 : 0;
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
  history.replaceState(null, "", window.location.pathname);
  elements["results-view"].hidden = true;
  elements["setup-view"].hidden = false;
  elements["job-status"].textContent = "";
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
if (["tournament", "strategy-evolution", "rule-search", "balance-audit", "llm-holdout"].includes(requestedMode)) {
  elements["experiment-mode"].value = requestedMode;
}
renderExperimentMode({ resetDefaults: Boolean(requestedMode) });

const existingJob = searchParameters.get("job");
if (existingJob) {
  elements["run-simulation"].disabled = true;
  elements["job-status"].textContent = copy.status.loadingExisting;
  try {
    showReport(await pollJob(existingJob));
  } catch (error) {
    elements["job-status"].textContent = `${copy.status.failed} · ${error.message}`;
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
    } catch (error) {
      bridgeConnected = false;
      showBridgeState(error.message);
    } finally {
      elements["connect-bridge"].disabled = false;
      updateRunAvailability();
    }
  });
}
updateRunAvailability();
