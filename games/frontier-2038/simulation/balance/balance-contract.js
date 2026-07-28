import { readFile } from "node:fs/promises";
import { fingerprintObject } from "../versioning/game-identity.js";

const contractUrl = new URL("../contracts/balance-contract.json", import.meta.url);

export async function loadBalanceContract(source = contractUrl) {
  const contract = JSON.parse(await readFile(source, "utf8"));
  if (
    contract.schemaVersion !== 1 ||
    !contract.id ||
    !contract.thresholds ||
    !contract.audit ||
    !contract.playerCountPolicy
  ) {
    throw new TypeError(
      "Balance contract must define schemaVersion 1, id, thresholds, audit, and playerCountPolicy."
    );
  }
  return {
    ...contract,
    fingerprint: fingerprintObject(contract)
  };
}

function check(id, value, operator, threshold, evidence = "observed") {
  const comparable = Number.isFinite(value);
  const passed = comparable && (operator === "max" ? value <= threshold : value >= threshold);
  return { id, value: comparable ? value : null, operator, threshold, evidence, passed };
}

export function evaluateTournamentBalance(report, contract) {
  const t = contract.thresholds;
  const d = report.diagnostics || {};
  const checks = [
    check("seat_win_share_range", d.seatWinShareRange, "max", t.seatWinShareRangeMax),
    check("faction_win_share_range", d.factionWinShareRange, "max", t.factionWinShareRangeMax),
    check("profile_win_share_range", d.profileWinShareRange, "max", t.profileWinShareRangeMax),
    check("action_entropy", d.actionDiversity, "min", t.actionEntropyMin),
    check("opening_entropy", d.openingDiversity?.entropy, "min", t.openingEntropyMin),
    check("opening_top_share", d.openingDiversity?.topShare, "max", t.openingTopShareMax),
    check("winning_path_entropy", d.winningPathDiversity?.entropy, "min", t.winningPathEntropyMin),
    check("winning_path_top_share", d.winningPathDiversity?.topShare, "max", t.winningPathTopShareMax),
    check(
      "faction_strategy_interaction",
      d.factionStrategyInteractionRange,
      "max",
      t.factionStrategyInteractionRangeMax
    ),
    check(
      "round_two_leader_conversion",
      d.leaderPredictability?.round2,
      "max",
      t.roundTwoLeaderConversionMax
    ),
    check("pairwise_dominance", d.pairwiseDominance, "max", t.pairwiseDominanceMax),
    check("integrity_violations", d.integrity?.violations, "max", t.integrityViolationsMax),
    check("policy_fallbacks", d.integrity?.policyFallbacks, "max", t.policyFallbacksMax),
    check(
      "forced_no_op_rate",
      d.integrity?.forcedNoOpRate,
      "max",
      t.forcedNoOpRateMax
    )
  ];
  return {
    contractId: contract.id,
    contractFingerprint: contract.fingerprint,
    status: checks.every((entry) => entry.passed) ? "within_provisional_bounds" : "outside_provisional_bounds",
    checks,
    promotionGate: {
      eligible: false,
      verdict: "tournament_only",
      reasons: ["A tournament cannot satisfy matchup, best-response, counter-response, holdout, receipt, and human-approval requirements."]
    }
  };
}

export function evaluateAuditBalance(report, contract) {
  const t = contract.thresholds;
  const checks = [
    ...report.league.evaluation.checks,
    check("best_response_gain", report.adversarial.maxBestResponseGain, "max", t.bestResponseGainMax),
    check("counter_recovery", report.adversarial.minCounterRecovery, "min", t.counterRecoveryMin),
    check("holdout_collapse", report.adversarial.maxHoldoutCollapse, "max", t.holdoutCollapseMax),
    check("matchup_coverage", report.league.coverage, "min", 1),
    check("seat_rotation", Number(report.design.seatRotation), "min", 1),
    check("faction_rotation", Number(report.design.factionRotation), "min", 1),
    check("common_seeds", Number(report.design.commonSeeds), "min", 1)
  ];
  const automatedPass = checks.every((entry) => entry.passed);
  return {
    contractId: contract.id,
    contractFingerprint: contract.fingerprint,
    status: automatedPass ? "candidate_for_human_review" : "rejected_by_automated_gate",
    checks,
    promotionGate: {
      eligible: false,
      automatedPass,
      sourceClean: null,
      trackedReceipt: false,
      humanApproval: false,
      verdict: automatedPass ? "awaiting_clean_receipt_and_human_approval" : "automated_checks_failed",
      reasons: [
        ...(!automatedPass ? ["One or more provisional automated bounds failed."] : []),
        "A tracked receipt has not yet been attached.",
        "Human approval is always required."
      ]
    }
  };
}
