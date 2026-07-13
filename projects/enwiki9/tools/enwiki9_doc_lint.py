#!/usr/bin/env python3
"""Lint live enwiki9 documentation against the current proof boundary.

The checks here are intentionally narrow. They catch stale routing, obsolete
file names, missing tool inventory entries, and accidental target-win language
that conflicts with the generated certificate.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

LIVE_DOCS = [
    ROOT / "README.md",
    ROOT / "ALGORITHMS.md",
    ROOT / "CANDIDATES.md",
    ROOT / "CMIX21_LOCK_SAFE_QUEUE.md",
    ROOT / "FX2_SC.md",
    ROOT / "PROJECT_ORGANIZATION.md",
    ROOT / "UPPER_BOUND_CERTIFICATE.md",
    ROOT / "docs" / "algorithm_cards.md",
    ROOT / "docs" / "artifact_fingerprint_audit.md",
    ROOT / "docs" / "best_results.md",
    ROOT / "docs" / "cmix21_memory_valves.md",
    ROOT / "docs" / "cmix21_memory_surfaces.md",
    ROOT / "docs" / "embedding_teacher_rules.md",
    ROOT / "docs" / "evidence_matrix.md",
    ROOT / "docs" / "evidence_receipts.md",
    ROOT / "docs" / "official_accounting_checklist.md",
    ROOT / "docs" / "organization_audit.md",
    ROOT / "docs" / "research_register.md",
    ROOT / "docs" / "residual_shadow_matrix.md",
    ROOT / "docs" / "shadow_coder_spec.md",
    ROOT / "docs" / "streaming_retrieval_mixer.md",
    ROOT / "docs" / "status_receipt.md",
    ROOT / "docs" / "takeover_runbook.md",
    ROOT / "docs" / "tooling_inventory.md",
]

NO_ESTIMATE_FILES = [
    ROOT / "agents" / "hutter_contender.md",
    ROOT / "agents" / "lm_explorer.md",
    ROOT / "lib" / "smoke.py",
]

REQUIRED_DOCS = [
    ROOT / "docs" / "algorithm_cards.md",
    ROOT / "docs" / "artifact_fingerprint_audit.md",
    ROOT / "docs" / "artifact_fingerprint_audit.json",
    ROOT / "docs" / "best_results.md",
    ROOT / "docs" / "evidence_receipts.md",
    ROOT / "docs" / "evidence_matrix.md",
    ROOT / "docs" / "official_accounting_checklist.md",
    ROOT / "docs" / "organization_audit.md",
    ROOT / "docs" / "research_register.md",
    ROOT / "docs" / "status_receipt.md",
    ROOT / "docs" / "status_receipt.json",
    ROOT / "docs" / "cmix21_memory_valves.md",
    ROOT / "docs" / "cmix21_memory_surfaces.md",
    ROOT / "docs" / "residual_shadow_matrix.md",
    ROOT / "docs" / "shadow_coder_spec.md",
    ROOT / "docs" / "streaming_retrieval_mixer.md",
    ROOT / "docs" / "takeover_runbook.md",
    ROOT / "docs" / "tooling_inventory.md",
]

OBSOLETE_SNIPPETS = [
    "algorithm_quick_cards",
    "docs/algorithm_quick_cards.md",
    "ppmd21888k no-ceiling 10M replay as pending",
]

FORBIDDEN_DURATION_PHRASES = [
    "~30 min",
    "~2 hr",
    "~2 min",
    "~30 sec",
    "1–4 weeks",
    "multi-day",
    "long-running",
    "months of focused work",
    "API sanity (sub-second)",
    "logic check (seconds)",
    "ETA",
    "~50 hour",
    "50-hour",
    "seven years",
    "saturate quickly",
]

FALSE_WIN_PHRASES = [
    "10.95 constructive upper bound present: `true`",
    "Full-corpus constructive result present: `true`",
    "target reached by this matrix: `True`",
]

ALGORITHM_CARD_PLACEHOLDERS = [
    "<program_or_lane_id>",
    "<plain mechanism>",
    "<exact proof boundary>",
    "<role in the project>",
]

DECIDER_VERDICTS = {
    "incomplete",
    "receipt_incomplete",
    "running",
    "pass",
    "rss_fail",
    "roundtrip_fail",
    "determinism_fail",
    "guard_returncode_fail",
}

DECIDER_APPLY_COMMAND_VERDICTS = {
    "pass",
    "rss_fail",
    "roundtrip_fail",
    "determinism_fail",
    "guard_returncode_fail",
}


@dataclass
class Finding:
    path: pathlib.Path
    message: str

    def render(self) -> str:
        return f"{self.path.relative_to(ROOT)}: {self.message}"


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot load {path}: {exc}") from exc


def live_doc_text() -> list[tuple[pathlib.Path, str]]:
    out: list[tuple[pathlib.Path, str]] = []
    for path in LIVE_DOCS:
        if path.exists():
            out.append((path, path.read_text()))
    return out


def check_required_docs(findings: list[Finding]) -> None:
    for path in REQUIRED_DOCS:
        if not path.exists():
            findings.append(Finding(path, "required orientation document is missing"))


def check_obsolete_and_duration_phrases(findings: list[Finding]) -> None:
    for path, text in live_doc_text():
        for snippet in OBSOLETE_SNIPPETS:
            if snippet in text:
                findings.append(Finding(path, f"obsolete snippet still present: {snippet!r}"))
        for snippet in FORBIDDEN_DURATION_PHRASES:
            if snippet in text:
                findings.append(Finding(path, f"forbidden duration phrase present: {snippet!r}"))
        for snippet in FALSE_WIN_PHRASES:
            if snippet in text:
                findings.append(Finding(path, f"false target-win phrase present: {snippet!r}"))
    for path in NO_ESTIMATE_FILES:
        if not path.exists():
            continue
        text = path.read_text()
        for snippet in FORBIDDEN_DURATION_PHRASES:
            if snippet in text:
                findings.append(Finding(path, f"forbidden duration phrase present: {snippet!r}"))
    cards = ROOT / "docs" / "algorithm_cards.md"
    if cards.exists():
        text = cards.read_text()
        for snippet in ALGORITHM_CARD_PLACEHOLDERS:
            if snippet in text:
                findings.append(Finding(cards, f"algorithm-card placeholder still present: {snippet!r}"))


def top_status_by_label(cert: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = cert.get("top_status", [])
    if not isinstance(rows, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("label"), str):
            out[row["label"]] = row
    return out


def active_gate_from_certificate(cert: dict[str, Any]) -> tuple[str | None, int | None]:
    labels = top_status_by_label(cert)
    row = labels.get("active gate") or labels.get("next gate") or labels.get("active candidate") or {}
    candidate = row.get("program_id")
    scope = row.get("scope_bytes")
    if isinstance(candidate, str) and isinstance(scope, int):
        return candidate, scope
    if isinstance(candidate, str):
        return candidate, None
    return None, None


def check_certificate_and_status(findings: list[Finding]) -> None:
    cert_path = ROOT / "upper_bound_certificate.json"
    status_path = ROOT / "docs" / "status_receipt.json"
    cert = load_json(cert_path)
    status = load_json(status_path)

    proof = cert.get("proof_status", {})
    if proof.get("has_10_95_constructive_upper_bound") is not False:
        findings.append(Finding(cert_path, "10.95 proof flag must remain false until full 1G official accounting passes"))
    if proof.get("has_full_corpus_constructive_result") is not False:
        findings.append(Finding(cert_path, "full-corpus proof flag must remain false without a verified 1G result"))

    if status.get("has_10_95_constructive_upper_bound") is not False:
        findings.append(Finding(status_path, "status receipt target flag disagrees with certificate"))
    if status.get("has_full_corpus_constructive_result") is not False:
        findings.append(Finding(status_path, "status receipt full-corpus flag disagrees with certificate"))

    labels = top_status_by_label(cert)
    active_candidate, active_scope = active_gate_from_certificate(cert)
    active_gate = labels.get("active gate", {})
    status_gate = status.get("active_gate", {})
    for label, row in (("certificate active gate", active_gate), ("status active gate", status_gate)):
        row = row if isinstance(row, dict) else {}
        if active_candidate and row.get("program_id") != active_candidate:
            findings.append(Finding(cert_path if "certificate" in label else status_path, f"{label} does not name active candidate"))
        if active_scope and row.get("scope_bytes") != active_scope:
            findings.append(Finding(cert_path if "certificate" in label else status_path, f"{label} does not use active scope"))

    gate_decision = status.get("gate_decision", {})
    gate_decision = gate_decision if isinstance(gate_decision, dict) else {}
    if active_candidate and gate_decision.get("candidate") != active_candidate:
        findings.append(Finding(status_path, "gate decision candidate mismatch"))
    if active_scope and gate_decision.get("scope_bytes") != active_scope:
        findings.append(Finding(status_path, "gate decision scope mismatch"))
    if gate_decision.get("verdict") not in DECIDER_VERDICTS:
        findings.append(Finding(status_path, "gate decision has unknown verdict"))
    if (
        gate_decision.get("verdict") == "running"
        and gate_decision.get("rss_guard_json_present") is True
    ):
        for key in (
            "latest_sample_max_single_rss_kib",
            "latest_sample_tree_rss_kib",
            "latest_sample_single_rss_margin_kib",
            "latest_sample_tree_rss_margin_kib",
            "rss_guard_json_bytes",
            "rss_guard_json_mtime_utc",
            "rss_guard_json_sha256",
        ):
            if key not in gate_decision:
                findings.append(Finding(status_path, f"running gate decision missing {key}"))

    operator_summary = status.get("operator_summary", {})
    if not isinstance(operator_summary, dict):
        findings.append(Finding(status_path, "status receipt missing operator_summary object"))
    else:
        required_summary_keys = (
            "candidate",
            "scope_bytes",
            "gate_verdict",
            "gate_next_action",
            "heavy_lock_held",
            "active_scorer_observed",
            "active_cmix_mode",
            "driver_result_present",
            "rss_guard_status",
            "rss_samples",
            "binary_10gib_guard_kib",
            "decimal_10gb_guard_kib",
            "single_rss_margin_kib",
            "max_sampled_single_decimal_10gb_margin_kib",
            "latest_sample_single_decimal_10gb_margin_kib",
            "safe_to_launch_heavy_gate",
            "terminal_verdict_present",
            "command_source",
            "has_full_corpus_constructive_result",
            "has_10_95_constructive_upper_bound",
            "claim_rule",
        )
        for key in required_summary_keys:
            if key not in operator_summary:
                findings.append(Finding(status_path, f"operator summary missing {key}"))
        if active_candidate and operator_summary.get("candidate") != active_candidate:
            findings.append(Finding(status_path, "operator summary candidate mismatch"))
        if active_scope and operator_summary.get("scope_bytes") != active_scope:
            findings.append(Finding(status_path, "operator summary scope mismatch"))
        if operator_summary.get("gate_verdict") != gate_decision.get("verdict"):
            findings.append(Finding(status_path, "operator summary verdict mismatch"))
        if operator_summary.get("has_10_95_constructive_upper_bound") is not False:
            findings.append(Finding(status_path, "operator summary target flag disagrees with certificate"))


def check_status_live_process_fields(findings: list[Finding]) -> None:
    status_path = ROOT / "docs" / "status_receipt.json"
    status_md_path = ROOT / "docs" / "status_receipt.md"
    status = load_json(status_path)
    status_md = status_md_path.read_text() if status_md_path.exists() else ""
    if not isinstance(status.get("generated_at_utc"), str):
        findings.append(Finding(status_path, "status receipt missing generated_at_utc"))
    if "Generated at UTC" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing generation timestamp"))
    active_processes = status.get("active_processes", {})
    if not isinstance(active_processes, dict):
        findings.append(Finding(status_path, "active_processes must be an object"))
        return

    if active_processes.get("active_scorer_observed") is not True:
        return

    cmix_rows = active_processes.get("cmix_rows")
    cmix_scorer_observed = isinstance(cmix_rows, list) and bool(cmix_rows)

    required_process_keys = [
        "active_rows",
        "controller_rows",
        "max_cmix_process",
        "decimal_10gb_guard_kib",
        "active_tree_rss_kib",
        "active_tree_margin_kib",
    ]
    if cmix_scorer_observed:
        required_process_keys.extend(
            [
                "active_cmix_mode",
                "active_temp_io",
                "single_process_margin_kib",
                "single_process_decimal_10gb_margin_kib",
            ]
        )
    for key in required_process_keys:
        if key not in active_processes:
            findings.append(Finding(status_path, f"active scorer status missing {key}"))

    if "Active cmix mode" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing active cmix mode"))
    if "Decimal `10GB` guard KiB" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing decimal 10GB memory margin"))
    if "## Active Runner Process Table" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing active runner process table"))
    controller_rows = active_processes.get("controller_rows")
    if isinstance(controller_rows, list) and controller_rows:
        if "## Active Controller Process Table" not in status_md:
            findings.append(Finding(status_md_path, "Markdown status receipt is missing active controller process table"))
        if "`gate_decider`" not in status_md:
            findings.append(Finding(status_md_path, "Markdown status receipt does not label cmix21 decider controller"))
        if "## Observed Controller Command" not in status_md:
            findings.append(Finding(status_md_path, "Markdown status receipt is missing observed controller command"))
        if "Controller Scope" not in status_md:
            findings.append(Finding(status_md_path, "Markdown status receipt is missing parsed controller scope"))
        if "driver command is authoritative for the active gate scope" not in status_md:
            findings.append(Finding(status_md_path, "Markdown status receipt is missing controller scope note"))
    active_rows = active_processes.get("active_rows")
    if isinstance(active_rows, list) and any(
        isinstance(row, dict)
        and "flock" in str(row.get("args", ""))
        and "enwiki9-heavy.lock" in str(row.get("args", ""))
        for row in active_rows
    ) and "`lock_wrapper`" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt does not label heavy-lock flock as lock_wrapper"))
    if isinstance(active_processes.get("active_temp_io"), dict):
        for label in (
            "Temp input path",
            "Temp output path",
            "Temp output staging path",
            "Temp input modified UTC",
            "Temp output modified UTC",
            "Temp output staging modified UTC",
        ):
            if label not in status_md:
                findings.append(Finding(status_md_path, f"Markdown status receipt is missing {label.lower()}"))
    if cmix_scorer_observed and "Temp output staging bytes" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing staging output bytes"))
    if "Latest sampled single RSS KiB" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing latest sampled RSS"))
    gate_decision = status.get("gate_decision", {})
    if (
        isinstance(gate_decision, dict)
        and gate_decision.get("rss_guard_json_present") is True
    ):
        for label in (
            "RSS guard JSON bytes",
            "RSS guard JSON modified UTC",
            "RSS guard JSON SHA-256",
        ):
            if label not in status_md:
                findings.append(Finding(status_md_path, f"Markdown status receipt is missing {label.lower()}"))
    if "Active process tree RSS KiB" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing active process tree RSS"))
    if "Active process tree margin KiB" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing active process tree margin"))
    tree_over_guard = active_processes.get("active_tree_rss_over_guard_kib")
    if isinstance(tree_over_guard, int) and tree_over_guard > 0:
        if "active_tree_rss_warning" not in active_processes:
            findings.append(Finding(status_path, "process tree RSS over guard without active_tree_rss_warning"))
        if "Active process tree warning" not in status_md:
            findings.append(Finding(status_md_path, "Markdown status receipt is missing active process tree warning"))

    if not cmix_scorer_observed or active_processes.get("active_cmix_mode") != "decode":
        return

    progress = active_processes.get("active_decode_progress")
    if not isinstance(progress, dict):
        findings.append(Finding(status_path, "decode scorer status missing active_decode_progress"))
        return
    for key in (
        "scope_bytes",
        "staging_output_bytes",
        "capped_output_bytes",
        "remaining_scope_bytes",
        "scope_percent",
    ):
        if key not in progress:
            findings.append(Finding(status_path, f"active_decode_progress missing {key}"))
    if "Decode scope progress" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing decode scope progress"))
    if "Decode remaining scope bytes" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing decode remaining bytes"))


def check_status_operator_logs(findings: list[Finding]) -> None:
    status_path = ROOT / "docs" / "status_receipt.json"
    status_md_path = ROOT / "docs" / "status_receipt.md"
    status = load_json(status_path)
    status_md = status_md_path.read_text() if status_md_path.exists() else ""
    logs = status.get("operator_logs")
    if not isinstance(logs, dict):
        findings.append(Finding(status_path, "status receipt missing operator_logs"))
        return
    latest_log = logs.get("latest_delayed_status_log")
    if not isinstance(latest_log, str) or "enwiki9_delayed_status_latest.log" not in latest_log:
        findings.append(Finding(status_path, "operator_logs missing latest delayed status log path"))
    active_processes = status.get("active_processes", {})
    if (
        isinstance(active_processes, dict)
        and active_processes.get("active_scorer_observed") is True
        and logs.get("latest_delayed_status_log_present") is not True
    ):
        findings.append(Finding(status_path, "active scorer status requires a present latest delayed status log"))
    if "Latest delayed status log" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing latest delayed status log"))


def check_status_candidate_audit(findings: list[Finding]) -> None:
    status_path = ROOT / "docs" / "status_receipt.json"
    status_md_path = ROOT / "docs" / "status_receipt.md"
    status = load_json(status_path)
    status_md = status_md_path.read_text() if status_md_path.exists() else ""
    audit = status.get("candidate_audit")
    if not isinstance(audit, dict):
        findings.append(Finding(status_path, "status receipt missing candidate_audit"))
        return
    if audit.get("returncode") != 0:
        findings.append(Finding(status_path, "candidate_audit did not complete cleanly"))
        return
    summary = audit.get("summary")
    if not isinstance(summary, dict):
        findings.append(Finding(status_path, "candidate_audit missing summary"))
        return
    for key in (
        "program_directories",
        "registered_programs",
        "untracked_nonignored_entries",
        "modified_tracked_entries",
        "candidate_status_counts",
    ):
        if key not in summary:
            findings.append(Finding(status_path, f"candidate_audit summary missing {key}"))
    if "## Candidate Audit" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing candidate audit section"))


def check_status_recent_artifacts(findings: list[Finding]) -> None:
    status_path = ROOT / "docs" / "status_receipt.json"
    status_md_path = ROOT / "docs" / "status_receipt.md"
    status = load_json(status_path)
    status_md = status_md_path.read_text() if status_md_path.exists() else ""
    artifacts = status.get("active_candidate_recent_artifacts")
    if not isinstance(artifacts, list):
        findings.append(Finding(status_path, "status receipt missing active_candidate_recent_artifacts list"))
        return
    if "## Active Candidate Recent Artifacts" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing active candidate artifact section"))
    if artifacts and not all(isinstance(item, dict) and "path" in item and "bytes" in item for item in artifacts):
        findings.append(Finding(status_path, "active candidate artifact rows must include path and bytes"))


def check_organization_audit_snapshot(findings: list[Finding]) -> None:
    status_path = ROOT / "docs" / "status_receipt.json"
    organization_path = ROOT / "docs" / "organization_audit.md"
    status = load_json(status_path)
    text = organization_path.read_text() if organization_path.exists() else ""
    audit = status.get("candidate_audit")
    if not isinstance(audit, dict):
        return
    summary = audit.get("summary")
    if not isinstance(summary, dict):
        return

    required_pairs = [
        ("program directories under programs/", "program_directories"),
        ("registered programs in index.json", "registered_programs"),
        ("untracked nonignored entries", "untracked_nonignored_entries"),
        ("modified tracked entries", "modified_tracked_entries"),
    ]
    for label, key in required_pairs:
        value = summary.get(key)
        if isinstance(value, int) and f"{label}: {value}" not in text:
            findings.append(Finding(organization_path, f"snapshot does not match candidate_audit {key}={value}"))

    status_counts = summary.get("candidate_status_counts")
    if not isinstance(status_counts, dict):
        return
    for key, value in sorted(status_counts.items()):
        if f"{key}: {value}" not in text:
            findings.append(Finding(organization_path, f"snapshot does not match candidate status {key}={value}"))


def check_status_handoff(findings: list[Finding]) -> None:
    status_path = ROOT / "docs" / "status_receipt.json"
    status_md_path = ROOT / "docs" / "status_receipt.md"
    status = load_json(status_path)
    status_md = status_md_path.read_text() if status_md_path.exists() else ""
    handoff = status.get("handoff")
    if not isinstance(handoff, dict):
        findings.append(Finding(status_path, "status receipt missing handoff"))
        return
    for key in (
        "candidate",
        "scope_bytes",
        "gate_verdict",
        "gate_next_action",
        "terminal_verdict_present",
        "heavy_gate_mutation_allowed",
        "recommended_action",
        "command_source",
        "claim_rule",
    ):
        if key not in handoff:
            findings.append(Finding(status_path, f"handoff missing {key}"))
    gate_decision = status.get("gate_decision", {})
    if isinstance(gate_decision, dict) and gate_decision.get("verdict") == "running":
        if handoff.get("terminal_verdict_present") is not False:
            findings.append(Finding(status_path, "running handoff must not mark terminal verdict present"))
        if handoff.get("heavy_gate_mutation_allowed") is not False:
            findings.append(Finding(status_path, "running handoff must not allow heavy gate mutation"))
    if (
        handoff.get("terminal_verdict_present") is True
        and handoff.get("gate_verdict") in DECIDER_APPLY_COMMAND_VERDICTS
        and "apply_terminal_command" not in handoff
        and not (
            handoff.get("gate_next_action") == "launch_lower_prefix_gate"
            and "next_gate_command" in handoff
        )
    ):
        findings.append(Finding(status_path, "terminal pass/RSS handoff missing command"))
    if handoff.get("gate_verdict") not in DECIDER_APPLY_COMMAND_VERDICTS and "apply_terminal_command" in handoff:
        findings.append(Finding(status_path, "non-apply terminal handoff unexpectedly has apply_terminal_command"))
    if "## Handoff" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing handoff section"))


def check_gate_evidence_status(findings: list[Finding]) -> None:
    status_path = ROOT / "docs" / "status_receipt.json"
    status_md_path = ROOT / "docs" / "status_receipt.md"
    status = load_json(status_path)
    status_md = status_md_path.read_text() if status_md_path.exists() else ""
    evidence = status.get("gate_evidence_status")
    if not isinstance(evidence, dict):
        findings.append(Finding(status_path, "status receipt missing gate_evidence_status"))
        return
    for key in (
        "driver_result_terminal",
        "rss_guard_terminal",
        "scored_gate_result_present",
        "live_guard_only",
        "claim_status",
        "claim_rule",
    ):
        if key not in evidence:
            findings.append(Finding(status_path, f"gate_evidence_status missing {key}"))
    gate_decision = status.get("gate_decision", {})
    if isinstance(gate_decision, dict):
        if (
            gate_decision.get("verdict") == "running"
            and gate_decision.get("rss_guard_json_present") is True
            and gate_decision.get("driver_result_json_present") is False
            and evidence.get("live_guard_only") is not True
        ):
            findings.append(Finding(status_path, "running guard without driver result must be marked live_guard_only"))
        if evidence.get("live_guard_only") is True and evidence.get("scored_gate_result_present") is not False:
            findings.append(Finding(status_path, "live guard monitor cannot be a scored gate result"))
    if "## Gate Evidence Status" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing gate evidence status"))
    if "live_guard_monitor_only" in json.dumps(evidence) and "live_guard_monitor_only" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt does not show live guard claim status"))


def check_observed_gate_command(findings: list[Finding]) -> None:
    status_path = ROOT / "docs" / "status_receipt.json"
    status_md_path = ROOT / "docs" / "status_receipt.md"
    status = load_json(status_path)
    status_md = status_md_path.read_text() if status_md_path.exists() else ""
    observed = status.get("observed_gate_command")
    if not isinstance(observed, dict):
        findings.append(Finding(status_path, "status receipt missing observed_gate_command"))
        return
    for key in (
        "expected_candidate",
        "expected_scope_bytes",
        "driver_process_count",
        "active_gate_command_observed",
        "mismatch_count",
        "driver_processes",
    ):
        if key not in observed:
            findings.append(Finding(status_path, f"observed_gate_command missing {key}"))
    active_processes = status.get("active_processes", {})
    active_gate_owned = (
        isinstance(active_processes, dict)
        and active_processes.get("active_scorer_observed") is True
        and observed.get("active_gate_command_observed") is True
    )
    if active_gate_owned:
        if observed.get("active_gate_command_observed") is not True:
            findings.append(Finding(status_path, "active scorer command does not match active gate candidate/scope"))
        if observed.get("mismatch_count") != 0:
            findings.append(Finding(status_path, "active scorer has mismatched driver command rows"))
    if "## Observed Gate Command" not in status_md:
        findings.append(Finding(status_md_path, "Markdown status receipt is missing observed gate command section"))


def check_live_docs_name_active_candidate(findings: list[Finding]) -> None:
    cert = load_json(ROOT / "upper_bound_certificate.json")
    active_candidate, _active_scope = active_gate_from_certificate(cert)
    if not active_candidate:
        findings.append(Finding(ROOT / "upper_bound_certificate.json", "cannot derive active candidate from certificate"))
        return
    required = [
        ROOT / "ALGORITHMS.md",
        ROOT / "CMIX21_LOCK_SAFE_QUEUE.md",
        ROOT / "FX2_SC.md",
        ROOT / "PROJECT_ORGANIZATION.md",
        ROOT / "docs" / "algorithm_cards.md",
        ROOT / "docs" / "status_receipt.md",
        ROOT / "docs" / "takeover_runbook.md",
    ]
    for path in required:
        text = path.read_text() if path.exists() else ""
        if active_candidate not in text:
            findings.append(Finding(path, "does not name the active candidate"))


def check_operator_scripts_use_certificate_gate(findings: list[Finding]) -> None:
    cert = load_json(ROOT / "upper_bound_certificate.json")
    active_candidate, active_scope = active_gate_from_certificate(cert)
    script = ROOT / "tools" / "enwiki9_delayed_status_check.sh"
    text = script.read_text() if script.exists() else ""

    if "upper_bound_certificate.json" not in text:
        findings.append(Finding(script, "does not derive active gate from upper_bound_certificate.json"))
    if re.search(r"^ACTIVE_CANDIDATE=", text, flags=re.MULTILINE):
        findings.append(Finding(script, "hardcodes ACTIVE_CANDIDATE instead of deriving it from the certificate"))
    if re.search(r"^ACTIVE_SCOPE=", text, flags=re.MULTILINE):
        findings.append(Finding(script, "hardcodes ACTIVE_SCOPE instead of deriving it from the certificate"))

    default_candidate = re.search(r'^DEFAULT_ACTIVE_CANDIDATE="([^"]+)"', text, flags=re.MULTILINE)
    if active_candidate and default_candidate and default_candidate.group(1) != active_candidate:
        findings.append(Finding(script, "fallback active candidate does not match certificate active gate"))

    default_scope = re.search(r'^DEFAULT_ACTIVE_SCOPE="([^"]+)"', text, flags=re.MULTILINE)
    if active_scope and default_scope and default_scope.group(1) != str(active_scope):
        findings.append(Finding(script, "fallback active scope does not match certificate active gate"))

    latest_log = "enwiki9_delayed_status_latest.log"
    if latest_log not in text:
        findings.append(Finding(script, "delayed status script does not maintain a latest-log pointer"))
    inventory = ROOT / "docs" / "tooling_inventory.md"
    inventory_text = inventory.read_text() if inventory.exists() else ""
    if latest_log not in inventory_text:
        findings.append(Finding(inventory, "tooling inventory does not document the delayed-status latest-log pointer"))


def check_tool_inventory(findings: list[Finding]) -> None:
    inventory = ROOT / "docs" / "tooling_inventory.md"
    text = inventory.read_text() if inventory.exists() else ""
    listed = set(re.findall(r"`([^`]+\.(?:py|sh|cpp))`", text))
    actual = {path.name for path in TOOLS.iterdir() if path.suffix in {".py", ".sh", ".cpp"}}
    missing = sorted(actual - listed)
    extra = sorted(listed - actual)
    if missing:
        findings.append(Finding(inventory, "missing tool entries: " + ", ".join(missing)))
    if extra:
        findings.append(Finding(inventory, "stale tool entries: " + ", ".join(extra)))


def check_residual_matrix_summary_counts(findings: list[Finding]) -> None:
    matrix = ROOT / "docs" / "residual_shadow_matrix.md"
    text = matrix.read_text() if matrix.exists() else ""
    receipt_match = re.search(r"Cached JSON receipts scanned into rows: `([0-9,]+)`", text)
    positive_match = re.search(r"Rows with positive measured or held-out shadow bytes: `([0-9,]+)`", text)
    if not receipt_match or not positive_match:
        findings.append(Finding(matrix, "cannot parse generated residual shadow matrix counts"))
        return

    receipt_count = receipt_match.group(1)
    positive_count = positive_match.group(1)
    required_snippets = [
        f"`{receipt_count}` residual/SSE rows",
        f"`{positive_count}` positive measured or held-out shadow rows",
    ]
    for path in (ROOT / "ALGORITHMS.md", ROOT / "docs" / "algorithm_cards.md"):
        summary = path.read_text() if path.exists() else ""
        for snippet in required_snippets:
            if snippet not in summary:
                findings.append(Finding(path, f"residual matrix summary missing {snippet!r}"))


def check_algorithm_cards_orientation(findings: list[Finding]) -> None:
    cards = ROOT / "docs" / "algorithm_cards.md"
    text = cards.read_text() if cards.exists() else ""
    required_snippets = [
        "## How To Read This File",
        "Score reality check:",
        "Plain-English candidate map:",
        "Score and archive answer different questions because program bytes differ.",
        "Raw LZMA2 baseline lane; the artifact below is a measured prefix control.",
    ]
    for snippet in required_snippets:
        if snippet not in text:
            findings.append(Finding(cards, f"algorithm cards missing orientation snippet: {snippet!r}"))


def check_memory_valve_active_alias_warning(findings: list[Finding]) -> None:
    valves = ROOT / "docs" / "cmix21_memory_valves.md"
    text = valves.read_text() if valves.exists() else ""
    required_snippets = [
        "## Decimal 10GB Risk",
        "decimal_10gb_guard_kib = 9,765,625",
        "## PPMD-Only Decimal Feasibility",
        "PPMD-only feasibility verdict: `not feasible`",
        "The next lower cap `21,504` KiB already has historical package rows (`ppmd21m`).",
        "A newly packaged same-cap candidate is a separate evidence lineage and must restart prefix gates.",
    ]
    for snippet in required_snippets:
        if snippet not in text:
            findings.append(Finding(valves, f"memory-valve report missing active alias warning: {snippet!r}"))


def check_memory_surface_scan(findings: list[Finding]) -> None:
    surfaces = ROOT / "docs" / "cmix21_memory_surfaces.md"
    text = surfaces.read_text() if surfaces.exists() else ""
    required_snippets = [
        "# cmix21 Memory Surface Scan",
        "## Observed Knob Values",
        "## Surface Evidence Rows",
        "PPMD cap is well-instrumented, but the decimal `10GB` gap is too large for PPMD-only cuts on current receipts.",
        "do not infer admissibility from names alone",
    ]
    for snippet in required_snippets:
        if snippet not in text:
            findings.append(Finding(surfaces, f"memory-surface scan missing snippet: {snippet!r}"))


def check_streaming_retrieval_mixer(findings: list[Finding]) -> None:
    doc = ROOT / "docs" / "streaming_retrieval_mixer.md"
    text = doc.read_text() if doc.exists() else ""
    required_snippets = [
        "# Streaming Retrieval Mixer",
        "Working name: `SRSTC`",
        "## Strategy Pivot",
        "self-referential probability model",
        "state_t = f(decoded_bytes_before_t, counted_constants)",
        "fixed integer random projections",
        "SimHash/minhash sketches with counted constants",
        '"receipt_type": "streaming_retrieval_shadow"',
        "Promotion requires positive held-out `net_saved_bytes`",
        "Keep the active guarded scorer serialized and untouched.",
    ]
    for snippet in required_snippets:
        if snippet not in text:
            findings.append(Finding(doc, f"streaming retrieval mixer missing snippet: {snippet!r}"))


def main() -> int:
    findings: list[Finding] = []
    check_required_docs(findings)
    check_obsolete_and_duration_phrases(findings)
    check_certificate_and_status(findings)
    check_status_live_process_fields(findings)
    check_status_operator_logs(findings)
    check_status_candidate_audit(findings)
    check_status_recent_artifacts(findings)
    check_organization_audit_snapshot(findings)
    check_status_handoff(findings)
    check_gate_evidence_status(findings)
    check_observed_gate_command(findings)
    check_live_docs_name_active_candidate(findings)
    check_operator_scripts_use_certificate_gate(findings)
    check_tool_inventory(findings)
    check_residual_matrix_summary_counts(findings)
    check_algorithm_cards_orientation(findings)
    check_memory_valve_active_alias_warning(findings)
    check_memory_surface_scan(findings)
    check_streaming_retrieval_mixer(findings)

    if findings:
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 1

    print("doc_lint_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
