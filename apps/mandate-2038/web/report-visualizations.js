const metricDefinitions = Object.freeze({
  score: { labelKey: "mandate", value: (row) => row.score ?? row.currentScore ?? row.mandate ?? 0 },
  capability: { labelKey: "capability", value: (row) => row.capability ?? 0 },
  customers: { labelKey: "customers", value: (row) => row.customers ?? 0 },
  trust: { labelKey: "trust", value: (row) => row.trust ?? 0 },
  compute: { labelKey: "compute", value: (row) => row.compute ?? 0 },
  facilities: {
    labelKey: "facilities",
    value: (row) => Array.isArray(row.facilities) ? row.facilities.length : (row.facilities ?? 0)
  },
  scrutiny: { labelKey: "scrutiny", value: (row) => row.scrutiny ?? 0 },
  winShare: { fallbackLabel: "Win share", value: (row) => row.winShare ?? 0 },
  calls: { fallbackLabel: "LLM decisions", value: (row) => row.calls ?? 0 },
  latency: { fallbackLabel: "Mean LLM latency (s)", value: (row) => row.meanLatencyMs ? row.meanLatencyMs / 1000 : 0 }
});

const llmProviders = new Set(["claude-cli", "codex-cli"]);

function metricLabel(definition, labels = {}) {
  if (definition.labelKey) return labels[definition.labelKey] || definition.labelKey;
  return definition.fallbackLabel;
}

export function visualizationMetrics(labels = {}) {
  return Object.entries(metricDefinitions).map(([id, definition]) => ({
    id,
    label: metricLabel(definition, labels)
  }));
}

function average(values) {
  return values.length ? values.reduce((total, value) => total + value, 0) / values.length : 0;
}

function sampleStandings(sample) {
  return Array.isArray(sample?.standings) ? sample.standings : [];
}

function winnerSeats(sample) {
  if (Array.isArray(sample?.winnerSeats)) return new Set(sample.winnerSeats);
  const standings = sampleStandings(sample);
  const bestScore = Math.max(...standings.map((standing) => standing.score ?? -Infinity));
  return new Set(standings.filter((standing) => standing.score === bestScore).map((standing) => standing.seat));
}

function receiptSummary(standing) {
  const receipts = standing?.metrics?.policyReceipts || [];
  const actualLlmReceipts = receipts.filter((receipt) => llmProviders.has(receipt.provider));
  const durations = receipts.map((receipt) => receipt.attemptedProvider
    ? receipt.providerDurationMs ?? receipt.durationMs
    : receipt.durationMs
  ).filter(Number.isFinite);
  return {
    calls: actualLlmReceipts.length,
    fallbacks: receipts.filter((receipt) => receipt.fallback).length,
    latencyTotalMs: durations.reduce((total, duration) => total + duration, 0),
    latencyDecisionCount: durations.length,
    providers: [...new Set(receipts.map((receipt) => receipt.provider).filter(Boolean))]
  };
}

function hasCompleteIdentity(report) {
  return [
    report?.game?.version,
    report?.game?.rulesetFingerprint,
    report?.engine?.fingerprint
  ].every((value) => typeof value === "string" && value.trim().length > 0);
}

export function compatibleReportGroups(reports) {
  const groups = new Map();
  for (const report of reports) {
    if (!hasCompleteIdentity(report)) continue;
    const key = [
      report.game.version,
      report.game.rulesetFingerprint,
      report.engine.fingerprint
    ].join("|");
    const group = groups.get(key) || { key, reports: [] };
    group.reports.push(report);
    groups.set(key, group);
  }
  return [...groups.values()];
}

export function sampledGames(reports) {
  return reports.flatMap((report, reportIndex) => (report.samples || []).map((sample, sampleIndex) => ({
    report,
    reportIndex,
    sample,
    sampleIndex,
    id: `${reportIndex}:${sampleIndex}`,
    label: `${report.seed || "unseeded"} / match ${sampleIndex + 1}`
  })));
}

export function trajectoryForSample(sample, metricId = "score", labels = {}) {
  const metric = metricDefinitions[metricId] || metricDefinitions.score;
  const events = (sample?.replay || []).filter((event) => Array.isArray(event?.state?.players));
  const players = events[0]?.state?.players || [];
  const series = players.map((player) => ({
    seat: player.seat,
    name: player.factionName || `Seat ${player.seat + 1}`,
    profileId: player.profileId,
    backendId: player.backendId,
    model: player.model || null,
    reasoningEffort: player.reasoningEffort || null,
    points: []
  }));
  for (const event of events) {
    for (const player of event.state.players) {
      const target = series.find((entry) => entry.seat === player.seat);
      if (target) target.points.push(metric.value(player));
    }
  }
  const finalStandings = new Map(sampleStandings(sample).map((standing) => [standing.seat, standing]));
  if (finalStandings.size) {
    for (const seriesEntry of series) {
      const standing = finalStandings.get(seriesEntry.seat);
      if (standing) seriesEntry.points.push(metric.value(standing));
    }
    const finalEvent = events.at(-1);
    events.push({
      round: finalEvent?.round ?? null,
      cycle: finalEvent?.cycle ?? null,
      summary: "Final reported standing."
    });
  }
  return {
    metric: metricLabel(metric, labels),
    events: events.map((event, index) => ({
      index,
      round: event.round,
      cycle: event.cycle,
      summary: event.summary
    })),
    series
  };
}

export function aggregateFactionPersona(reports) {
  const rows = new Map();
  for (const { sample } of sampledGames(reports)) {
    const winners = winnerSeats(sample);
    for (const standing of sampleStandings(sample)) {
      const key = [
        standing.factionId || "unknown",
        standing.profileId || "unknown",
        standing.backendId || "unknown",
        standing.model || "default",
        standing.reasoningEffort || "default"
      ].join("|");
      const entry = rows.get(key) || {
        factionId: standing.factionId || "unknown",
        factionName: standing.factionName || standing.factionId || "Unknown faction",
        profileId: standing.profileId || "unknown",
        backendId: standing.backendId || "unknown",
        model: standing.model || null,
        reasoningEffort: standing.reasoningEffort || null,
        count: 0,
        scores: [],
        capabilities: [],
        customers: [],
        trusts: [],
        computes: [],
        facilities: [],
        wins: 0,
        calls: [],
        latencies: [],
        latencyDecisionCount: 0,
        fallbacks: 0,
        providers: new Set()
      };
      const calls = receiptSummary(standing);
      entry.count += 1;
      entry.scores.push(standing.score ?? 0);
      entry.capabilities.push(standing.capability ?? 0);
      entry.customers.push(standing.customers ?? 0);
      entry.trusts.push(standing.trust ?? 0);
      entry.computes.push(standing.compute ?? 0);
      entry.facilities.push(standing.facilities ?? 0);
      entry.wins += winners.has(standing.seat) ? 1 : 0;
      entry.calls.push(calls.calls);
      if (calls.latencyDecisionCount) {
        entry.latencies.push(calls.latencyTotalMs);
        entry.latencyDecisionCount += calls.latencyDecisionCount;
      }
      entry.fallbacks += calls.fallbacks;
      calls.providers.forEach((provider) => entry.providers.add(provider));
      rows.set(key, entry);
    }
  }
  return [...rows.values()].map((entry) => ({
    ...entry,
    score: average(entry.scores),
    capability: average(entry.capabilities),
    customers: average(entry.customers),
    trust: average(entry.trusts),
    compute: average(entry.computes),
    facilities: average(entry.facilities),
    winShare: entry.wins / entry.count,
    calls: average(entry.calls),
    meanLatencyMs: entry.latencyDecisionCount
      ? entry.latencies.reduce((total, value) => total + value, 0) / entry.latencyDecisionCount
      : 0,
    providers: [...entry.providers].sort()
  }));
}

export function heatmapCells(rows, metricId = "winShare", labels = {}) {
  const metric = metricDefinitions[metricId] || metricDefinitions.winShare;
  const factions = [...new Set(rows.map((row) => row.factionName))].sort();
  const profiles = [...new Set(rows.map((row) => row.profileId))].sort();
  const cells = new Map(rows.map((row) => [`${row.factionName}|${row.profileId}`, metric.value(row)]));
  return { factions, profiles, cells, metric: metricLabel(metric, labels) };
}

export function providerSummary(reports) {
  const providers = new Map();
  for (const { reportIndex, sampleIndex, sample } of sampledGames(reports)) {
    for (const standing of sampleStandings(sample)) {
      for (const receipt of standing.metrics?.policyReceipts || []) {
        const actualProvider = receipt.provider || "unknown";
        const attemptedProvider = receipt.attemptedProvider || actualProvider;
        const actualModel = receipt.model || null;
        const actualReasoningEffort = receipt.reasoningEffort || null;
        const attemptedModel = receipt.attemptedModel || actualModel;
        const attemptedReasoningEffort = receipt.attemptedReasoningEffort || actualReasoningEffort;
        const key = [
          actualProvider,
          attemptedProvider,
          actualModel || "default",
          actualReasoningEffort || "default",
          attemptedModel || "default",
          attemptedReasoningEffort || "default"
        ].join("|");
        const entry = providers.get(key) || {
          actualProvider,
          attemptedProvider,
          actualModel,
          actualReasoningEffort,
          attemptedModel,
          attemptedReasoningEffort,
          decisions: 0,
          weightedLatency: 0,
          latencyDecisions: 0,
          fallbacks: 0,
          appearances: new Set()
        };
        const providerDuration = receipt.attemptedProvider
          ? receipt.providerDurationMs ?? receipt.durationMs
          : receipt.durationMs;
        entry.decisions += 1;
        entry.fallbacks += receipt.fallback ? 1 : 0;
        if (Number.isFinite(providerDuration)) {
          entry.weightedLatency += providerDuration;
          entry.latencyDecisions += 1;
        }
        entry.appearances.add(`${reportIndex}:${sampleIndex}:${standing.seat}`);
        providers.set(key, entry);
      }
    }
  }
  return [...providers.values()].map(({ appearances, ...entry }) => ({
    ...entry,
    appearances: appearances.size,
    meanLatencyMs: entry.latencyDecisions ? entry.weightedLatency / entry.latencyDecisions : 0
  })).sort((left, right) => right.decisions - left.decisions ||
    left.actualProvider.localeCompare(right.actualProvider));
}
