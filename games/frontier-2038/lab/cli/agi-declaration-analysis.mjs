#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import {
  intervalFits,
  normalMeanInterval98,
  subsetMinusGrandMeanInterval98,
  wilsonInterval98,
} from "../statistics/equivalence-intervals.js";

const EXPECTED_RULES_FINGERPRINT =
  "sha256:fc8bd0450b923b4b613ad9f5f855ea1f3832d1468b9be7496ba7f439e0d3ac4d";
const DECLARATION_TOLERANCE = 0.1;
const MANDATE_TOLERANCE = 2;
const WIN_CREDIT_TOLERANCE = 0.1;

function parseArguments(argv) {
  const reportPaths = [];
  let output = null;
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--report") reportPaths.push(argv[++index]);
    else if (argument === "--output") output = argv[++index];
    else throw new Error(`Unknown argument: ${argument}`);
  }
  if (reportPaths.length === 0) {
    throw new Error("Provide at least one --report path.");
  }
  return { reportPaths, output };
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

function roundNumbers(value) {
  if (Array.isArray(value)) return value.map(roundNumbers);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, entry]) => [key, roundNumbers(entry)]),
    );
  }
  return typeof value === "number" && !Number.isInteger(value)
    ? Number(value.toFixed(6))
    : value;
}

function everyRow(report) {
  const registrations = new Map(
    report.preRegistration.comparisons.map((comparison) => [comparison.id, comparison]),
  );
  return report.comparisons.flatMap((comparison) => {
    const registration = registrations.get(comparison.id);
    if (!registration) throw new Error(`Missing registration for ${comparison.id}.`);
    return comparison.paired.rows.map((row) => ({
      ...row,
      comparisonId: comparison.id,
      backend: registration.backend,
      factionId: registration.focalFactionId,
      focalSeat: registration.focalSeat,
    }));
  });
}

function contrast(rows, property, groupProperty, groupValue, tolerance) {
  const interval = subsetMinusGrandMeanInterval98(
    rows.map((row) => Number(row[property])),
    rows.map((row) => row[groupProperty] === groupValue),
  );
  return {
    ...interval,
    tolerance: [-tolerance, tolerance],
    equivalent: intervalFits(interval, -tolerance, tolerance),
  };
}

function analyzeDimension(rows, property, values, tolerance) {
  return Object.fromEntries(values.map((value) => [
    String(value),
    contrast(rows, property, property === "focalSeat" ? "focalSeat" : property, value, tolerance),
  ]));
}

function dimensionContrasts(rows, groupProperty, groupValues, outcomeProperty, tolerance) {
  return Object.fromEntries(groupValues.map((groupValue) => [
    String(groupValue),
    contrast(rows, outcomeProperty, groupProperty, groupValue, tolerance),
  ]));
}

function allEquivalent(groups) {
  return Object.values(groups).every((outcomes) =>
    Object.values(outcomes).every((interval) => interval.equivalent));
}

function analyzeBackend(rows, backend) {
  const backendRows = rows.filter((row) => row.backend === backend);
  const factions = [...new Set(backendRows.map((row) => row.factionId))].sort();
  const seats = [...new Set(backendRows.map((row) => row.focalSeat))].sort((a, b) => a - b);
  const outcomes = {
    declarationRate: { property: "leftDeclared", tolerance: DECLARATION_TOLERANCE },
    mandateEffect: { property: "scoreDelta", tolerance: MANDATE_TOLERANCE },
    winCreditEffect: { property: "winCreditDelta", tolerance: WIN_CREDIT_TOLERANCE },
  };
  const byFaction = {};
  const bySeat = {};
  for (const [outcome, { property, tolerance }] of Object.entries(outcomes)) {
    byFaction[outcome] = dimensionContrasts(
      backendRows, "factionId", factions, property, tolerance,
    );
    bySeat[outcome] = dimensionContrasts(
      backendRows, "focalSeat", seats, property, tolerance,
    );
  }
  return {
    observations: backendRows.length,
    byFaction,
    bySeat,
    equivalent: allEquivalent(byFaction) && allEquivalent(bySeat),
  };
}

function analyzeReport(report, source) {
  const rows = everyRow(report);
  const backends = [...new Set(rows.map((row) => row.backend))].sort();
  const greedyRows = rows.filter((row) => row.backend === "greedy");
  const weightedRows = rows.filter((row) => row.backend === "weighted");
  const weightedDeclarations = weightedRows.filter((row) => row.leftDeclared).length;
  const weightedWilson = wilsonInterval98(weightedDeclarations, weightedRows.length);

  const coverage = {
    eligibleLegal: rows.filter((row) => row.leftLegalDeclaration).length,
    eligibleTotal: rows.length,
    blockedIllegal: rows.filter((row) => !row.rightLegalDeclaration).length,
    blockedTotal: rows.length,
  };
  coverage.passed = coverage.eligibleLegal === coverage.eligibleTotal &&
    coverage.blockedIllegal === coverage.blockedTotal;

  const policy = {
    greedy: {
      declarations: greedyRows.filter((row) => row.leftDeclared).length,
      legalWindows: greedyRows.length,
    },
    weighted: weightedWilson,
  };
  policy.greedy.rate = policy.greedy.declarations / policy.greedy.legalWindows;
  policy.greedy.passed = policy.greedy.declarations === policy.greedy.legalWindows;
  policy.weighted.passed = weightedWilson.estimate >= 0.75 && weightedWilson.lower > 0.65;
  policy.passed = policy.greedy.passed && policy.weighted.passed;

  const aggregate = {
    mandateEffect: normalMeanInterval98(rows.map((row) => row.scoreDelta)),
    winCreditEffect: normalMeanInterval98(rows.map((row) => row.winCreditDelta)),
    rankAdvantage: normalMeanInterval98(rows.map((row) => row.rankAdvantage)),
  };
  const precision = {
    mandateHalfWidthMaximum: 1,
    winCreditHalfWidthMaximum: 0.075,
  };
  precision.passed = aggregate.mandateEffect.halfWidth <= precision.mandateHalfWidthMaximum &&
    aggregate.winCreditEffect.halfWidth <= precision.winCreditHalfWidthMaximum;

  const backendAnalysis = Object.fromEntries(
    backends.map((backend) => [backend, analyzeBackend(rows, backend)]),
  );
  const equivalencePassed = Object.values(backendAnalysis).every((entry) => entry.equivalent);

  const integrity = {
    sourceDirty: report.provenance.sourceDirty,
    quarantinedMatches: report.execution.quarantinedMatches,
    quarantinedPairs: report.comparisons.reduce(
      (sum, comparison) => sum + comparison.paired.quarantinedPairs,
      0,
    ),
    runs: report.runs,
    scheduledRuns: report.scheduledRuns,
    pairedEvidenceRuns: report.pairedEvidenceRuns,
    comparisonCount: report.comparisons.length,
    registeredComparisonCount: report.preRegistration.comparisons.length,
    rulesetFingerprint: report.game.rulesetFingerprint,
  };
  integrity.passed = integrity.sourceDirty === false &&
    integrity.quarantinedMatches === 0 && integrity.quarantinedPairs === 0 &&
    integrity.runs === integrity.scheduledRuns &&
    integrity.pairedEvidenceRuns === integrity.scheduledRuns &&
    integrity.comparisonCount === integrity.registeredComparisonCount &&
    integrity.rulesetFingerprint === EXPECTED_RULES_FINGERPRINT;

  return {
    field: `p${report.playerCount}`,
    playerCount: report.playerCount,
    source,
    sourceCommit: report.provenance.sourceCommit,
    gameVersion: report.game.version,
    engineVersion: report.engine.version,
    seed: report.seed,
    integrity,
    coverage,
    policy,
    aggregate,
    precision,
    backends: backendAnalysis,
    equivalencePassed,
    requiresConfirmation: !precision.passed || !equivalencePassed,
    qualifiedAtLook1: integrity.passed && coverage.passed && policy.passed &&
      precision.passed && equivalencePassed,
  };
}

const { reportPaths, output } = parseArguments(process.argv.slice(2));
const loaded = await Promise.all(reportPaths.map(async (reportPath) => {
  const buffer = await readFile(reportPath);
  return {
    report: JSON.parse(buffer),
    source: {
      path: reportPath,
      bytes: buffer.length,
      sha256: sha256(buffer),
    },
  };
}));

const fields = loaded
  .map(({ report, source }) => analyzeReport(report, source))
  .sort((left, right) => left.playerCount - right.playerCount);
const commits = new Set(fields.map((field) => field.sourceCommit));
const result = roundNumbers({
  schemaVersion: 1,
  studyId: "agi-declaration-endpoint-v1",
  intervalMethod: {
    confidenceLevel: 0.98,
    meanAndContrast: "normal interval using sample variance; subset-minus-grand-mean contrast includes covariance through the group-versus-complement form",
    binomial: "Wilson score interval",
  },
  fields,
  crossFieldIntegrity: {
    oneSourceCommit: commits.size === 1,
    sourceCommits: [...commits],
  },
  requiresConfirmationFields: fields
    .filter((field) => field.requiresConfirmation)
    .map((field) => field.field),
  qualifiedAtLook1: fields.length === 3 && commits.size === 1 &&
    fields.every((field) => field.qualifiedAtLook1),
});
const serialized = `${JSON.stringify(result, null, 2)}\n`;
if (output) {
  await writeFile(path.resolve(output), serialized);
} else {
  process.stdout.write(serialized);
}

