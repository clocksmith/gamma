import assert from "node:assert/strict";
import test from "node:test";
import {
  aggregateFactionPersona,
  compatibleReportGroups,
  heatmapCells,
  providerSummary,
  trajectoryForSample
} from "../web/report-visualizations.js";

function standing({
  seat,
  factionId,
  factionName,
  profileId,
  score,
  capability = 0,
  provider = null,
  durationMs = null,
  fallback = false,
  receipts = null
}) {
  return {
    seat,
    factionId,
    factionName,
    profileId,
    backendId: provider ? "codex" : "weighted",
    score,
    capability,
    customers: 0,
    trust: 0,
    compute: 0,
    facilities: 0,
    metrics: {
      policyReceipts: receipts || (provider ? [{ provider, durationMs, fallback }] : [])
    }
  };
}

function report({ fingerprint = "rules-a", samples = [] } = {}) {
  return {
    game: { version: "0.8.23", rulesetFingerprint: fingerprint },
    engine: { fingerprint: "engine-a" },
    samples
  };
}

test("trajectory extraction retains every recorded player state", () => {
  const sample = {
    standings: [
      standing({ seat: 0, factionId: "sam", factionName: "Sam", profileId: "rush", score: 6 }),
      standing({ seat: 1, factionId: "mark", factionName: "Mark", profileId: "broker", score: 4 })
    ],
    replay: [
      {
        round: 1,
        cycle: 1,
        summary: "Start.",
        state: { players: [
          { seat: 0, factionName: "Sam", profileId: "rush", backendId: "codex", model: "gpt-5.6-sol", reasoningEffort: "medium", currentScore: 2 },
          { seat: 1, factionName: "Mark", profileId: "broker", backendId: "weighted", currentScore: 4 }
        ] }
      },
      {
        round: 1,
        cycle: 2,
        summary: "Research resolved.",
        state: { players: [
          { seat: 0, factionName: "Sam", profileId: "rush", backendId: "codex", currentScore: 5 },
          { seat: 1, factionName: "Mark", profileId: "broker", backendId: "weighted", currentScore: 4 }
        ] }
      }
    ]
  };

  const trajectory = trajectoryForSample(sample, "score", { mandate: "Mandate" });
  assert.equal(trajectory.metric, "Mandate");
  assert.deepEqual(trajectory.series.map((series) => series.points), [[2, 5, 6], [4, 4, 4]]);
  assert.equal(trajectory.series[0].model, "gpt-5.6-sol");
  assert.equal(trajectory.series[0].reasoningEffort, "medium");
  assert.equal(trajectory.events.at(-1).summary, "Final reported standing.");
  assert.equal(trajectory.events[1].summary, "Research resolved.");
});

test("aggregate views preserve faction-persona pairings and LLM receipt provenance", () => {
  const sample = {
    winnerSeats: [0],
    standings: [
      standing({
        seat: 0,
        factionId: "coalition_lab",
        factionName: "Dovetalis Labs",
        profileId: "capability_rusher",
        score: 18,
        capability: 10,
        receipts: [
          { provider: "codex-cli", durationMs: 8000 },
          {
            provider: "weighted",
            attemptedProvider: "codex-cli",
            fallback: true,
            providerDurationMs: 1500
          },
          {
            provider: "greedy",
            attemptedProvider: "claude-cli",
            fallback: true,
            providerDurationMs: 500
          }
        ]
      }),
      standing({
        seat: 1,
        factionId: "platform_empire",
        factionName: "Loopfold AI",
        profileId: "power_broker",
        score: 15,
        capability: 8
      })
    ]
  };
  const rows = aggregateFactionPersona([report({ samples: [sample] })]);
  const sam = rows.find((row) => row.factionId === "coalition_lab");
  assert.equal(sam.winShare, 1);
  assert.equal(sam.score, 18);
  assert.equal(sam.calls, 1);
  assert.equal(sam.meanLatencyMs, 10000 / 3);
  assert.deepEqual(sam.providers, ["codex-cli", "greedy", "weighted"]);

  const map = heatmapCells(rows);
  assert.equal(map.cells.get("Dovetalis Labs|capability_rusher"), 1);
  assert.deepEqual(providerSummary([report({ samples: [sample] })]), [
    {
      actualProvider: "codex-cli",
      attemptedProvider: "codex-cli",
      actualModel: null,
      actualReasoningEffort: null,
      attemptedModel: null,
      attemptedReasoningEffort: null,
      decisions: 1,
      weightedLatency: 8000,
      latencyDecisions: 1,
      fallbacks: 0,
      appearances: 1,
      meanLatencyMs: 8000
    },
    {
      actualProvider: "greedy",
      attemptedProvider: "claude-cli",
      actualModel: null,
      actualReasoningEffort: null,
      attemptedModel: null,
      attemptedReasoningEffort: null,
      decisions: 1,
      weightedLatency: 500,
      latencyDecisions: 1,
      fallbacks: 1,
      appearances: 1,
      meanLatencyMs: 500
    },
    {
      actualProvider: "weighted",
      attemptedProvider: "codex-cli",
      actualModel: null,
      actualReasoningEffort: null,
      attemptedModel: null,
      attemptedReasoningEffort: null,
      decisions: 1,
      weightedLatency: 1500,
      latencyDecisions: 1,
      fallbacks: 1,
      appearances: 1,
      meanLatencyMs: 1500
    }
  ]);
});

test("cross-report aggregation separates incompatible and incomplete identities", () => {
  const groups = compatibleReportGroups([
    report({ fingerprint: "rules-a" }),
    report({ fingerprint: "rules-a" }),
    report({ fingerprint: "rules-b" }),
    { game: { version: "0.8.23", rulesetFingerprint: "rules-a" }, engine: {} }
  ]);
  assert.equal(groups.length, 2);
  assert.deepEqual(groups.map((group) => group.reports.length).sort(), [1, 2]);
});
