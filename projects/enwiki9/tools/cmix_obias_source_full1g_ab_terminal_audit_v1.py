#!/usr/bin/env python3
"""Read-only terminal audit of the independent cmix-obias full-1G A/B arms."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_full1g_ab_terminal_audit_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
A_ID = "cmix_obias_source_full1g_roundtrip_a_qm0_v1"
B_ID = "cmix_obias_source_full1g_roundtrip_b_qm0_v1"
A = ROOT / "results" / A_ID
B = ROOT / "results" / B_ID
SOURCE_RECEIPT = ROOT / "results" / "cmix_obias_source_1m_roundtrip_qm3_v1" / "decision.json"
EXPECTED_CANONICAL = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
EXPECTED_A_ARCHIVE = "ade610d6391ac1aee59becf8694c73f4617d435ad0c96d48c372acc4f9450711"
EXPECTED_SCORE = 108_513_707
RSS_LIMIT_KIB = 9_765_625


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(16 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def same_bytes(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as a, right.open("rb") as b:
        while True:
            aa = a.read(16 << 20)
            bb = b.read(16 << 20)
            if aa != bb:
                return False
            if not aa:
                return True


def arm_b_active() -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            argv = [
                part.decode("utf-8", "replace")
                for part in (entry / "cmdline").read_bytes().split(b"\0")
                if part
            ]
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        joined = " ".join(argv)
        if B_ID in joined or "cmix_obias_source_full1g_roundtrip_b_qm0.py" in joined:
            matches.append({"pid": int(entry.name), "argv": argv})
    return matches


def load_decision(directory: Path) -> dict[str, object]:
    path = directory / "decision.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing terminal decision: {path}")
    return json.loads(path.read_text())


def latest_live_resource_evidence() -> tuple[Path, dict[str, object]]:
    matches = sorted(
        (ROOT / "operations" / "evidence").glob(f"*_{B_ID}_live.json")
    )
    if not matches:
        raise FileNotFoundError("missing Arm B live resource evidence")
    path = matches[-1]
    return path, json.loads(path.read_text())


def main() -> int:
    active = arm_b_active()
    if active:
        raise RuntimeError(f"Arm B is nonterminal; refusing audit: {active}")
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")

    a = load_decision(A)
    b = load_decision(B)
    evidence_path, resource = latest_live_resource_evidence()
    required_files = [
        A / "archive9",
        B / "archive9",
        A / "out.cmix",
        B / "out.cmix",
        SOURCE_RECEIPT,
    ]
    missing = [str(path) for path in required_files if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing A/B audit artifacts: {missing}")

    archive_a = artifact(A / "archive9")
    archive_b = artifact(B / "archive9")
    payload_a = artifact(A / "out.cmix")
    payload_b = artifact(B / "out.cmix")
    archive_identity = bool(
        archive_a["bytes"] == archive_b["bytes"]
        and archive_a["sha256"] == archive_b["sha256"]
        and same_bytes(A / "archive9", B / "archive9")
    )
    payload_identity = bool(
        payload_a["bytes"] == payload_b["bytes"]
        and payload_a["sha256"] == payload_b["sha256"]
        and same_bytes(A / "out.cmix", B / "out.cmix")
    )
    inverse_a = bool(
        a.get("restored", {}).get("bytes") == 1_000_000_000
        and a.get("restored", {}).get("sha256") == EXPECTED_CANONICAL
        and a.get("restored", {}).get("byte_identical_to_canonical") is True
    )
    inverse_b = bool(
        b.get("restored", {}).get("bytes") == 1_000_000_000
        and b.get("restored", {}).get("sha256") == EXPECTED_CANONICAL
        and b.get("restored", {}).get("byte_identical_to_canonical") is True
    )
    score_a = a.get("counted_score_bytes")
    score_b = b.get("counted_score_bytes")
    telemetry = resource.get("telemetry", {})
    observed_hwm = telemetry.get("vmhwm_kib")
    observed_rss = telemetry.get("vmrss_kib")
    resource_failed = bool(
        isinstance(observed_hwm, int) and observed_hwm > RSS_LIMIT_KIB
    )
    correctness_gates = {
        "arm_a_terminal_pass": a.get("overall_pass") is True,
        "arm_b_terminal_pass": b.get("overall_pass") is True,
        "arm_a_archive_expected_sha256": archive_a["sha256"] == EXPECTED_A_ARCHIVE,
        "archive_a_b_byte_identity": archive_identity,
        "payload_a_b_byte_identity": payload_identity,
        "arm_a_exact_canonical_inverse": inverse_a,
        "arm_b_exact_canonical_inverse": inverse_b,
        "counted_score_a_b_identity": score_a == score_b == EXPECTED_SCORE,
        "scratch_a_cleaned": a.get("scratch_cleaned") is True,
        "scratch_b_cleaned": b.get("scratch_cleaned") is True,
        "encode_returncodes_zero": a.get("encode", {}).get("returncode") == 0
        and b.get("encode", {}).get("returncode") == 0,
        "decode_returncodes_zero": a.get("decode", {}).get("returncode") == 0
        and b.get("decode", {}).get("returncode") == 0,
    }
    correctness_pass = all(correctness_gates.values())
    resource_gates = {
        "live_resource_evidence_present": True,
        "observed_hwm_within_limit": isinstance(observed_hwm, int)
        and observed_hwm <= RSS_LIMIT_KIB,
        "terminal_runner_contains_process_tree_rss": False,
    }
    strict_resource_pass = all(resource_gates.values())

    if correctness_pass and not strict_resource_pass:
        next_action = (
            "Run the frozen PPM always-purge identity/RSS diagnostic alone; "
            "only an exact positive result may promote to a full correction-only replay."
        )
    elif correctness_pass:
        next_action = "Execute the sealed dP probability-adjoint gate alone."
    else:
        next_action = (
            "Preserve terminal failure evidence and authorize one correction-only "
            "successor with unchanged corpus, algorithm parameters, and accounting boundary."
        )

    result = {
        "schema": "gamma.enwiki9.cmix-obias-source-full1g-ab-terminal-audit.v1",
        "candidate_id": CANDIDATE_ID,
        "claim_boundary": (
            "Two-run external baseline audit under the bound host/package. "
            "Not universal determinism, official prize verification, or Gamma authorship."
        ),
        "score_credit_bytes": 0,
        "gamma_authorship_credit_bytes": 0,
        "source_package_closure": {
            "reference_receipt": artifact(SOURCE_RECEIPT),
            "donor_commit": "51488a0c1228dbeab7c1be837fc90ceaed351728",
            "launch_workspace_identity": "not_captured",
        },
        "arm_a_decision": artifact(A / "decision.json"),
        "arm_b_decision": artifact(B / "decision.json"),
        "archive_a": archive_a,
        "archive_b": archive_b,
        "payload_a": payload_a,
        "payload_b": payload_b,
        "counted_score_bytes": score_a if score_a == score_b else None,
        "correctness_gates": correctness_gates,
        "correctness_pass": correctness_pass,
        "resource_evidence": {
            "path": str(evidence_path),
            "sha256": sha256(evidence_path),
            "observed_vmrss_kib": observed_rss,
            "observed_vmhwm_kib": observed_hwm,
            "limit_kib": RSS_LIMIT_KIB,
            "violation_preserved": resource_failed,
        },
        "resource_gates": resource_gates,
        "strict_resource_pass": strict_resource_pass,
        "external_baseline_classification": (
            "two_run_deterministic_external_baseline_resource_failed"
            if correctness_pass and not strict_resource_pass
            else "two_run_external_baseline_incomplete_or_failed"
            if not correctness_pass
            else "two_run_deterministic_external_baseline"
        ),
        "officially_verified": False,
        "project_105m_target_pass": False,
        "next_action": next_action,
    }
    RESULT.mkdir(parents=True)
    (RESULT / "decision.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "event": "ab_terminal_audit",
                "correctness_pass": correctness_pass,
                "strict_resource_pass": strict_resource_pass,
            }
        ),
        flush=True,
    )
    return 0 if correctness_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
