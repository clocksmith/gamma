export const CURRENT_REPORT_SCHEMA_VERSION = 6;

function clone(value) {
  return structuredClone(value);
}

function reportVersion(report) {
  return Number(report?.reportSchemaVersion || report?.schemaVersion || 0);
}

function legacyIdentity(report) {
  return {
    game: {
      version: "unknown",
      releaseStatus: "legacy_unattributed",
      releaseDate: null,
      rulesetFingerprint: null,
      playtestKitFingerprint: null,
      files: {},
      kitFiles: {}
    },
    engine: {
      id: report.scope?.id || "unknown",
      version: "unknown",
      coverageId: report.scope?.id || "unknown",
      fingerprint: null,
      files: {}
    },
    variant: {
      kind: "legacy_unattributed",
      overlay: {},
      effective: clone(report.rulesVariant || {}),
      fingerprint: null
    },
    strategies: {
      fingerprint: null,
      profiles: [],
      backends: clone(report.configuration?.backends || []),
      model: report.configuration?.model || null
    },
    experiment: {
      reportType: report.reportType || "unknown",
      seed: report.seed || "",
      playerCount: report.playerCount || null,
      fingerprint: null
    },
    rng: {
      algorithm: "unknown",
      version: null
    },
    provenance: {
      sourceCommit: null,
      sourceDirty: null
    }
  };
}

function migrateLegacyToCurrent(report, fromVersion) {
  return {
    ...clone(report),
    ...legacyIdentity(report),
    schemaVersion: CURRENT_REPORT_SCHEMA_VERSION,
    reportSchemaVersion: CURRENT_REPORT_SCHEMA_VERSION,
    replaySchemaVersion: 1,
    decisionSchemaVersion: 1,
    evidenceType: "simulation",
    balanceContract: {
      id: "legacy_missing_balance_contract",
      status: "legacy_unattributed",
      fingerprint: null
    },
    balanceEvaluation: {
      contractId: "legacy_missing_balance_contract",
      status: "not_evaluable",
      checks: [],
      promotionGate: {
        eligible: false,
        verdict: "legacy_report",
        reasons: ["Legacy reports cannot satisfy the balance-promotion gate."]
      }
    },
    migration: {
      migratedFromReportSchemaVersion: fromVersion,
      attribution: "legacy_unattributed",
      warning: "Original report did not record immutable game and engine fingerprints or causal Power-supplier attribution."
    }
  };
}

function migrateV3ToV4(report) {
  return {
    ...clone(report),
    schemaVersion: CURRENT_REPORT_SCHEMA_VERSION,
    reportSchemaVersion: CURRENT_REPORT_SCHEMA_VERSION,
    migration: {
      migratedFromReportSchemaVersion: 3,
      attribution: "identity_preserved_supplier_metrics_legacy",
      warning: "Version 3 supplier-support statistics recorded sellers without proving that imported Power was counterfactually necessary."
    }
  };
}

function migrateV4ToV5(report) {
  return {
    ...clone(report),
    schemaVersion: CURRENT_REPORT_SCHEMA_VERSION,
    reportSchemaVersion: CURRENT_REPORT_SCHEMA_VERSION,
    balanceContract: {
      id: "legacy_missing_balance_contract",
      status: "legacy_unattributed",
      fingerprint: null
    },
    balanceEvaluation: {
      contractId: "legacy_missing_balance_contract",
      status: "not_evaluable",
      checks: [],
      promotionGate: {
        eligible: false,
        verdict: "legacy_report",
        reasons: ["Schema 4 did not record the strategic-unsolvability contract."]
      }
    },
    migration: {
      migratedFromReportSchemaVersion: 4,
      attribution: "identity_preserved_balance_contract_missing",
      warning: "Version 4 reports cannot satisfy the balance-promotion gate."
    }
  };
}

function migrateV5ToV6(report) {
  return {
    ...clone(report),
    schemaVersion: CURRENT_REPORT_SCHEMA_VERSION,
    reportSchemaVersion: CURRENT_REPORT_SCHEMA_VERSION,
    migration: {
      migratedFromReportSchemaVersion: 5,
      attribution: "identity_preserved_unified_matrix_missing",
      warning: "Version 5 reports predate the unified seven-axis matrix, partially pooled intervals, backend rotation, and preregistered LLM holdouts."
    }
  };
}

function migrateIncompleteV6MatchArchive(report) {
  const launch = report.launchIdentity;
  return {
    ...clone(report),
    rng: clone(launch.rng),
    provenance: clone(launch.provenance),
    experiment: {
      reportType: report.reportType || "tournament",
      seed: report.seed || "",
      playerCount: report.playerCount || null,
      runs: report.runs ?? null,
      sampleReplays: report.samples?.length ?? 0,
      fingerprint: null
    },
    balanceContract: {
      id: "legacy_missing_balance_contract",
      status: "legacy_unattributed",
      fingerprint: null
    },
    balanceEvaluation: {
      contractId: "legacy_missing_balance_contract",
      status: "not_evaluable",
      checks: [],
      promotionGate: {
        eligible: false,
        verdict: "incomplete_match_archive",
        reasons: [
          "This completed per-match archive predates complete experiment and balance-contract attribution."
        ]
      }
    },
    migration: {
      migratedFromReportSchemaVersion: 6,
      attribution: "launch_identity_preserved_experiment_backfilled",
      warning: "The original per-match archive omitted experiment and balance-contract fields. The Lab reconstructed only the non-promotional viewing envelope from its recorded launch identity."
    }
  };
}

export function normalizeSimulationReport(rawReport) {
  if (!rawReport || typeof rawReport !== "object" || Array.isArray(rawReport)) {
    throw new TypeError("Simulation report must be an object.");
  }
  if (rawReport.evidenceLabel !== "simulation" && rawReport.evidenceType !== "simulation") {
    throw new TypeError("Report is not labeled as simulation evidence.");
  }
  const version = reportVersion(rawReport);
  if (version === 1 || version === 2) {
    return migrateLegacyToCurrent(rawReport, version);
  }
  if (version === 3) return migrateV5ToV6(migrateV4ToV5(migrateV3ToV4(rawReport)));
  if (version === 4) return migrateV5ToV6(migrateV4ToV5(rawReport));
  if (version === 5) return migrateV5ToV6(rawReport);
  if (version !== CURRENT_REPORT_SCHEMA_VERSION) {
    throw new TypeError(`Unsupported simulation report schema ${version || "unknown"}.`);
  }
  const incompleteMatchArchive = rawReport.launchIdentity?.rng &&
    rawReport.launchIdentity?.provenance &&
    !rawReport.experiment &&
    !rawReport.rng &&
    !rawReport.provenance &&
    !rawReport.balanceContract &&
    !rawReport.balanceEvaluation;
  const report = incompleteMatchArchive
    ? migrateIncompleteV6MatchArchive(rawReport)
    : clone(rawReport);
  for (const key of [
    "game",
    "engine",
    "variant",
    "strategies",
    "experiment",
    "rng",
    "provenance"
  ]) {
    if (!report[key] || typeof report[key] !== "object") {
      throw new TypeError(`Simulation report schema 6 requires ${key}.`);
    }
  }
  for (const key of ["balanceContract", "balanceEvaluation"]) {
    if (!report[key] || typeof report[key] !== "object") {
      throw new TypeError(`Simulation report schema 6 requires ${key}.`);
    }
  }
  return report;
}

function same(left, right, path) {
  const keys = path.split(".");
  const read = (value) => keys.reduce((current, key) => current?.[key], value);
  return read(left) !== null && read(left) === read(right);
}

export function classifyReportComparison(leftInput, rightInput) {
  const left = normalizeSimulationReport(leftInput);
  const right = normalizeSimulationReport(rightInput);
  if (!left.game.rulesetFingerprint || !right.game.rulesetFingerprint ||
      !left.engine.fingerprint || !right.engine.fingerprint) {
    return {
      classification: "incompatible",
      causalClaimAllowed: false,
      reason: "At least one report lacks immutable ruleset or engine attribution."
    };
  }

  const commonExecution = (
    same(left, right, "engine.fingerprint") &&
    same(left, right, "experiment.fingerprint")
  );
  const sameRules = (
    same(left, right, "game.rulesetFingerprint") &&
    same(left, right, "variant.fingerprint")
  );
  const sameStrategies = same(left, right, "strategies.fingerprint");

  if (commonExecution && sameRules && sameStrategies) {
    return {
      classification: "exact",
      causalClaimAllowed: true,
      reason: "Rules, engine, strategies, player count, and common seed match."
    };
  }
  if (commonExecution && sameStrategies && !sameRules) {
    return {
      classification: "controlled_rules",
      causalClaimAllowed: true,
      reason: "Only the ruleset or tested variant differs."
    };
  }
  if (commonExecution && sameRules && !sameStrategies) {
    return {
      classification: "controlled_strategy",
      causalClaimAllowed: true,
      reason: "Only the strategy field differs."
    };
  }
  return {
    classification: "descriptive_historical",
    causalClaimAllowed: false,
    reason: "Multiple experimental dimensions differ."
  };
}
