#!/usr/bin/env python3
"""Certify deterministic source-built full-1G cmix-obias score accounting."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_full1g_determinism_accounting_qm0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
ARM_IDS = (
    "cmix_obias_source_full1g_roundtrip_a_qm0_v1",
    "cmix_obias_source_full1g_roundtrip_b_qm0_v1",
)
PROGRAM_BYTES = 468_481
HEAD_BYTES = 23_002
INVOCATION_BYTES = 48
RAW_BYTES = 1_000_000_000
TARGET_BYTES = 105_000_000
PRIZE_CEILING_BYTES = 109_685_196
DECIMAL_LIMIT_KIB = 9_765_625
EXPECTED_VERDICT = "source_built_full1g_roundtrip_prize_ceiling_candidate"
EXPECTED_RAW_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
EXPECTED_PROGRAM_SHA256 = "4ba53d3652c4e6de4126b4c03006e45a5f7e0511abd5d9661bf8132236ef1d2a"
EXPECTED_HEAD_SHA256 = "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078"
EXTERNAL_ARCHIVE_BYTES = 108_009_834
EXTERNAL_ARCHIVE_SHA256 = "664823c5d9f167bda342745d7b34a3ccb98fd7108723ba83643d9d09bf693900"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(16 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(f"dependency has not terminalized: {path}")
    return json.loads(path.read_text())


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def main() -> int:
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")

    arms: dict[str, dict[str, object]] = {}
    failures: list[str] = []
    for arm_id in ARM_IDS:
        decision_path = ROOT / "results" / arm_id / "decision.json"
        guard_path = ROOT / "results" / f"{arm_id.removesuffix('_v1')}_guard_v1.json"
        decision = load_json(decision_path)
        guard = load_json(guard_path)
        arms[arm_id] = {
            "decision_path": str(decision_path),
            "decision_sha256": sha256(decision_path),
            "guard_path": str(guard_path),
            "guard_sha256": sha256(guard_path),
            "decision": decision,
            "guard": guard,
        }
        if decision.get("overall_pass") is not True:
            failures.append(f"{arm_id}: overall_pass")
        if decision.get("verdict") != EXPECTED_VERDICT:
            failures.append(f"{arm_id}: verdict")
        if decision.get("restored", {}).get("bytes") != RAW_BYTES:
            failures.append(f"{arm_id}: restored bytes")
        if decision.get("restored", {}).get("sha256") != EXPECTED_RAW_SHA256:
            failures.append(f"{arm_id}: restored sha256")
        if decision.get("restored", {}).get("byte_identical_to_canonical") is not True:
            failures.append(f"{arm_id}: raw identity")
        compressor = decision.get("program", {}).get("packaged_compressor", {})
        head = decision.get("program", {}).get("head", {})
        if compressor.get("bytes") != PROGRAM_BYTES:
            failures.append(f"{arm_id}: program bytes")
        if compressor.get("sha256") != EXPECTED_PROGRAM_SHA256:
            failures.append(f"{arm_id}: program sha256")
        if head.get("bytes") != HEAD_BYTES:
            failures.append(f"{arm_id}: head bytes")
        if head.get("sha256") != EXPECTED_HEAD_SHA256:
            failures.append(f"{arm_id}: head sha256")
        if decision.get("program", {}).get("total_bytes") != PROGRAM_BYTES + HEAD_BYTES:
            failures.append(f"{arm_id}: program total")
        if decision.get("gates", {}).get("temporary_disk_within_100gb") is not True:
            failures.append(f"{arm_id}: temporary disk")
        if guard.get("status") != "completed" or guard.get("returncode") != 0:
            failures.append(f"{arm_id}: guard terminal")
        if guard.get("rss_guard_exceeded") is not False:
            failures.append(f"{arm_id}: rss guard")
        if guard.get("official_decimal_over_limit_kib") != 0:
            failures.append(f"{arm_id}: decimal rss")
        if int(guard.get("max_sampled_tree_rss_kib", DECIMAL_LIMIT_KIB + 1)) > DECIMAL_LIMIT_KIB:
            failures.append(f"{arm_id}: tree rss")

    left = arms[ARM_IDS[0]]["decision"]
    right = arms[ARM_IDS[1]]["decision"]
    for key in ("payload", "archive"):
        for field in ("bytes", "sha256"):
            if left.get(key, {}).get(field) != right.get(key, {}).get(field):
                failures.append(f"determinism: {key} {field}")
    payload_identical = all(
        left.get("payload", {}).get(field) == right.get("payload", {}).get(field)
        for field in ("bytes", "sha256")
    )
    archive_identical = all(
        left.get("archive", {}).get(field) == right.get("archive", {}).get(field)
        for field in ("bytes", "sha256")
    )

    archive_bytes = left.get("archive", {}).get("bytes")
    archive_sha256 = left.get("archive", {}).get("sha256")
    if not isinstance(archive_bytes, int) or not isinstance(archive_sha256, str):
        failures.append("source archive identity missing")
        archive_bytes = 0
        archive_sha256 = ""
    counted_score = archive_bytes + PROGRAM_BYTES + HEAD_BYTES + INVOCATION_BYTES
    external_archive_identical = (
        archive_bytes == EXTERNAL_ARCHIVE_BYTES
        and archive_sha256 == EXTERNAL_ARCHIVE_SHA256
    )
    prize_pass = counted_score <= PRIZE_CEILING_BYTES
    target_pass = counted_score <= TARGET_BYTES
    if not prize_pass:
        failures.append("current prize ceiling")

    passed = not failures
    result = {
        "schema": "enwiki9_cmix_obias_source_full1g_determinism_accounting_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "claim_boundary": (
            "Exact local source-built full-1G determinism, roundtrip, memory, disk, "
            "and conservative byte accounting. Isolated official timing and final "
            "committee source/package eligibility remain separate."
        ),
        "target_bytes": TARGET_BYTES,
        "prize_ceiling_bytes": PRIZE_CEILING_BYTES,
        "dependencies": {
            arm_id: {
                "decision_path": arms[arm_id]["decision_path"],
                "decision_sha256": arms[arm_id]["decision_sha256"],
                "guard_path": arms[arm_id]["guard_path"],
                "guard_sha256": arms[arm_id]["guard_sha256"],
            }
            for arm_id in ARM_IDS
        },
        "determinism": {
            "payload_byte_identical": payload_identical,
            "archive_byte_identical": archive_identical,
        },
        "archive": {"bytes": archive_bytes, "sha256": archive_sha256},
        "program": {
            "compressor_bytes": PROGRAM_BYTES,
            "compressor_sha256": EXPECTED_PROGRAM_SHA256,
            "head_bytes": HEAD_BYTES,
            "head_sha256": EXPECTED_HEAD_SHA256,
            "invocation_bytes_conservative": INVOCATION_BYTES,
        },
        "source_archive_identical_to_external_claim": external_archive_identical,
        "verified_local_full_1g_score_bytes": counted_score if passed else None,
        "signed_distance_to_105m_bytes": counted_score - TARGET_BYTES,
        "margin_below_current_prize_ceiling_bytes": PRIZE_CEILING_BYTES - counted_score,
        "gates": {
            "both_roundtrips_exact": all(
                arms[arm_id]["decision"].get("restored", {}).get("byte_identical_to_canonical") is True
                for arm_id in ARM_IDS
            ),
            "payload_deterministic": payload_identical,
            "archive_deterministic": archive_identical,
            "decimal_memory_both_pass": all(
                arms[arm_id]["guard"].get("official_decimal_over_limit_kib") == 0
                for arm_id in ARM_IDS
            ),
            "temporary_disk_both_pass": all(
                arms[arm_id]["decision"].get("gates", {}).get("temporary_disk_within_100gb") is True
                for arm_id in ARM_IDS
            ),
            "current_prize_ceiling_pass": prize_pass,
            "project_105m_target_pass": target_pass,
        },
        "official_eligibility_complete": False,
        "failed_conditions": failures,
        "overall_pass": passed,
        "verdict": (
            "source_built_full1g_determinism_and_105m_score_verified_eligibility_remains"
            if passed and target_pass
            else "source_built_full1g_determinism_and_prize_score_verified_105m_debt_remains"
            if passed
            else "source_built_full1g_determinism_or_score_rejected"
        ),
    }
    RESULT.mkdir(parents=True)
    write_json(RESULT / "decision.json", result)
    print(json.dumps({"event": "source_full1g_accounting_terminal", "overall_pass": passed}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
