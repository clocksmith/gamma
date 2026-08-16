import { createHash } from "node:crypto";
import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import { promisify } from "node:util";
import { relative, resolve } from "node:path";

const execFileAsync = promisify(execFile);
export const projectRoot = resolve(import.meta.dirname, "../..");
export const gameVersionUrl = new URL("../../versions/current-release.json", import.meta.url);
const balanceContractUrl = new URL("../contracts/balance-contract.json", import.meta.url);

function sortValue(value) {
  if (Array.isArray(value)) return value.map(sortValue);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.keys(value).sort().map((key) => [key, sortValue(value[key])])
  );
}

export function canonicalJson(value) {
  return JSON.stringify(sortValue(value));
}

export function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

export function fingerprintObject(value) {
  return `sha256:${sha256(canonicalJson(value))}`;
}

async function fingerprintFiles(root, paths) {
  const files = {};
  for (const path of [...paths].sort()) {
    const absolute = resolve(root, path);
    const contents = await readFile(absolute);
    files[path] = {
      bytes: contents.byteLength,
      sha256: sha256(contents)
    };
  }
  return files;
}

function collectionFingerprint(files) {
  return fingerprintObject(
    Object.entries(files).map(([path, metadata]) => ({
      path,
      bytes: metadata.bytes,
      sha256: metadata.sha256
    }))
  );
}

const VOCABULARY_KEYS = new Set([
  "artDirection",
  "description",
  "displayName",
  "flavorText",
  "introduction",
  "label",
  "microcopy",
  "motto",
  "name",
  "newsCopy",
  "privateAnxiety",
  "publicPromise",
  "rulesText",
  "slogan",
  "strapline",
  "summary",
  "text",
  "victoryStatement"
]);

export function mechanicsProjection(value) {
  if (Array.isArray(value)) return value.map(mechanicsProjection);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value)
      .filter(([key]) => !VOCABULARY_KEYS.has(key))
      .map(([key, entry]) => [key, mechanicsProjection(entry)])
  );
}

async function mechanicsFingerprint(root, paths) {
  const documents = [];
  for (const path of [...paths].sort()) {
    if (!path.endsWith(".json")) continue;
    const parsed = JSON.parse(await readFile(resolve(root, path), "utf8"));
    documents.push({ path, value: mechanicsProjection(parsed) });
  }
  return fingerprintObject(documents);
}

async function gitIdentity(root) {
  try {
    const [{ stdout: commit }, { stdout: status }] = await Promise.all([
      execFileAsync("git", ["rev-parse", "HEAD"], { cwd: root }),
      execFileAsync("git", ["status", "--porcelain=v1", "--untracked-files=all"], {
        cwd: root
      })
    ]);
    const sourceChanges = status.split(/\r?\n/).filter((line) => {
      const path = line.slice(3).trim();
      // Reports are outputs of a study, not inputs to the simulated engine.
      // A multi-report batch must not make its later reports source-dirty by
      // archiving its earlier ones.
      return path && !path.startsWith("evidence/studies/simulation/");
    });
    return {
      sourceCommit: commit.trim(),
      sourceDirty: sourceChanges.length > 0
    };
  } catch {
    return {
      sourceCommit: null,
      sourceDirty: null
    };
  }
}

export async function loadGameIdentity({
  root = projectRoot,
  rulesVariant = null,
  variantOverlay = null,
  profiles = [],
  backends = [],
  model = null,
  reasoningEffort = null,
  policyProjection = "rich",
  experimentKind = "tournament",
  experimentConfiguration = null
} = {}) {
  const version = JSON.parse(await readFile(resolve(root, "versions/current-release.json"), "utf8"));
  const rulesetFiles = await fingerprintFiles(root, version.rulesetFiles);
  const playtestKitFiles = await fingerprintFiles(root, version.playtestKitFiles);
  const engineFiles = await fingerprintFiles(root, version.engine.files);
  const effectiveVariant = rulesVariant || {};
  const overlay = variantOverlay || {};
  const strategySnapshot = {
    profiles: profiles.map((profile) => sortValue(profile)),
    backends: [...backends],
    model,
    reasoningEffort,
    policyProjection,
    experimentKind,
    experimentConfiguration: sortValue(experimentConfiguration)
  };

  return {
    game: {
      version: version.gameVersion,
      releaseStatus: version.releaseStatus,
      releaseDate: version.releaseDate,
      rulesetFingerprint: collectionFingerprint(rulesetFiles),
      mechanicsFingerprint: await mechanicsFingerprint(root, version.rulesetFiles),
      playtestKitFingerprint: collectionFingerprint({
        ...rulesetFiles,
        ...playtestKitFiles
      }),
      files: rulesetFiles,
      kitFiles: playtestKitFiles
    },
    engine: {
      id: version.engine.id,
      version: version.engine.version,
      coverageId: version.engine.coverageId,
      fingerprint: collectionFingerprint(engineFiles),
      files: engineFiles
    },
    contracts: structuredClone(version.contracts),
    variant: {
      kind: effectiveVariant.configurations
        ? "experiment_matrix"
        : Object.keys(overlay).length
          ? "candidate_overlay"
          : "canonical",
      overlay: sortValue(overlay),
      effective: sortValue(effectiveVariant),
      fingerprint: fingerprintObject({
        overlay,
        effective: effectiveVariant
      })
    },
    strategies: {
      fingerprint: fingerprintObject(strategySnapshot),
      profiles: profiles.map((profile) => ({
        id: profile.id,
        fingerprint: fingerprintObject(profile)
      })),
      backends: [...backends],
      model
    },
    rng: structuredClone(version.rng),
    provenance: await gitIdentity(root)
  };
}

export function createLaunchIdentity(identity) {
  const payload = {
    schemaVersion: 1,
    game: structuredClone(identity.game),
    engine: structuredClone(identity.engine),
    contracts: structuredClone(identity.contracts),
    variant: structuredClone(identity.variant),
    strategies: structuredClone(identity.strategies),
    rng: structuredClone(identity.rng),
    provenance: structuredClone(identity.provenance)
  };
  return {
    ...payload,
    fingerprint: fingerprintObject(payload)
  };
}

export function assertLaunchIdentity(expected, identity, context = "simulation") {
  if (!expected) return createLaunchIdentity(identity);
  const expectedPayload = structuredClone(expected);
  const expectedFingerprint = expectedPayload.fingerprint;
  delete expectedPayload.fingerprint;
  const recalculatedExpected = fingerprintObject(expectedPayload);
  if (expectedFingerprint !== recalculatedExpected) {
    const error = new Error(`${context} received a malformed launch identity.`);
    error.code = "launch_identity_malformed";
    throw error;
  }
  const actual = createLaunchIdentity(identity);
  if (actual.fingerprint !== expectedFingerprint) {
    const error = new Error(`${context} identity differs from its launch snapshot.`);
    error.code = "launch_identity_mismatch";
    error.expectedLaunchIdentity = expectedFingerprint;
    error.actualLaunchIdentity = actual.fingerprint;
    error.changedIdentitySections = Object.keys(expectedPayload).filter(
      (key) => fingerprintObject(expectedPayload[key]) !== fingerprintObject(actual[key])
    );
    throw error;
  }
  return actual;
}

export async function createReportIdentity({
  report,
  root = projectRoot,
  identity: suppliedIdentity = null,
  rulesVariant,
  variantOverlay,
  profiles,
  backends,
  model,
  reasoningEffort,
  policyProjection,
  experimentKind,
  experimentConfiguration
}) {
  const identity = suppliedIdentity || await loadGameIdentity({
    root,
    rulesVariant,
    variantOverlay,
    profiles,
    backends,
    model,
    reasoningEffort,
    policyProjection,
    experimentKind,
    experimentConfiguration
  });
  const balanceContractDocument = JSON.parse(await readFile(balanceContractUrl, "utf8"));
  const experimentDefinition = {
    reportType: report.reportType,
    seed: report.seed,
    playerCount: report.playerCount,
    runs: report.runs ?? null,
    sampleReplays: report.samples?.length ?? 0,
    generations: report.generations ?? null,
    population: report.population ?? null,
    runsPerSeat: report.runsPerSeat ?? null,
    opponentCoverage: report.opponentCoverage ?? null,
    targetWinShare: report.targetWinShare ?? null,
    iterations: report.iterations ?? null,
    runsPerVariant: report.runsPerVariant ?? null,
    runsPerMatchup: report.runsPerMatchup ?? null,
    playerCounts: report.playerCounts ?? null,
    preRegistrationFingerprint: report.preRegistration?.fingerprint || null,
    matrixContractFingerprint: report.matrixContract?.fingerprint || null,
    targetAgiRate: report.targetAgiRate ?? null,
    configurationFingerprint: report.configuration
      ? fingerprintObject(report.configuration)
      : null,
    strategyArtifactsFingerprint: report.adversarial
      ? fingerprintObject(
        report.adversarial.profiles ||
        report.adversarial.rows ||
        report.adversarial.status
      )
      : null,
    scopeId: report.scope?.id || null
  };
  const completed = {
    ...report,
    balanceContract: report.balanceContract || {
      id: balanceContractDocument.id,
      status: balanceContractDocument.status,
      fingerprint: fingerprintObject(balanceContractDocument),
      provenance: balanceContractDocument.provenance
    },
    balanceEvaluation: report.balanceEvaluation || {
      contractId: balanceContractDocument.id,
      status: "not_applicable",
      checks: [],
      promotionGate: {
        eligible: false,
        verdict: "experiment_type_not_promotable",
        reasons: ["This experiment type cannot promote canonical rules."]
      }
    },
    schemaVersion: identity.contracts.reportSchemaVersion,
    reportSchemaVersion: identity.contracts.reportSchemaVersion,
    replaySchemaVersion: identity.contracts.replaySchemaVersion,
    decisionSchemaVersion: identity.contracts.decisionSchemaVersion,
    evidenceType: "simulation",
    game: identity.game,
    engine: identity.engine,
    variant: identity.variant,
    strategies: identity.strategies,
    experiment: {
      ...experimentDefinition,
      fingerprint: fingerprintObject(experimentDefinition)
    },
    rng: identity.rng,
    provenance: identity.provenance
  };
  if (completed.balanceEvaluation?.promotionGate) {
    completed.balanceEvaluation.promotionGate.sourceClean =
      identity.provenance.sourceDirty === false;
    if (identity.provenance.sourceDirty !== false) {
      completed.balanceEvaluation.promotionGate.automatedPass = false;
      completed.balanceEvaluation.promotionGate.verdict = "dirty_source_rejected";
      completed.balanceEvaluation.promotionGate.reasons.push(
        "The source worktree was dirty, so the experiment is not reconstructable from its commit."
      );
    }
    completed.balanceEvaluation.promotionGate.eligible = Boolean(
      completed.balanceEvaluation.promotionGate.automatedPass &&
      completed.balanceEvaluation.promotionGate.sourceClean &&
      completed.balanceEvaluation.promotionGate.trackedReceipt &&
      completed.balanceEvaluation.promotionGate.humanApproval
    );
  }
  return completed;
}

export function shortFingerprint(value) {
  return String(value || "unknown").replace(/^sha256:/, "").slice(0, 12);
}

export function relativeVersionPath(path, root = projectRoot) {
  return relative(root, resolve(root, path));
}
