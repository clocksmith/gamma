#!/usr/bin/env python3
"""Bind conservative counted totals for both cmix-obias program forms."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_full1g_submission_accounting_qm0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
EXTERNAL_ARCHIVE = Path("/home/x/enwiki9-nonproof/cmix-obias-donor/final/archive9")
EXTERNAL_COMPRESSOR = Path("/home/x/enwiki9-nonproof/cmix-obias-donor/final/cmix")
EXTERNAL_HEAD = Path(
    "/home/x/enwiki9-nonproof/cmix-obias-donor/cmix-obias/models/bitlstm32/"
    "refit_golden256_fp16.blob"
)
SOURCE_RESULT = ROOT / "results/cmix_obias_source_1m_roundtrip_qm3_v1"
SOURCE_COMPRESSOR = SOURCE_RESULT / "cmix"
SOURCE_HEAD = SOURCE_RESULT / "head.blob"
SOURCE_DECISION = SOURCE_RESULT / "decision.json"
INVOCATION = "KH_BITLSTM32=head.blob ./cmix -e enwik9 out.cmix"
PRIZE_CEILING = 109_685_196
TARGET = 105_000_000
EXPECTED = {
    EXTERNAL_ARCHIVE: (108_009_834, "664823c5d9f167bda342745d7b34a3ccb98fd7108723ba83643d9d09bf693900"),
    EXTERNAL_COMPRESSOR: (459_989, "eee69c879f4bbd58015efd4d34f55c6dc986ec818fa68c2f32a9ee5ab5568f68"),
    EXTERNAL_HEAD: (23_002, "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078"),
    SOURCE_COMPRESSOR: (468_481, "4ba53d3652c4e6de4126b4c03006e45a5f7e0511abd5d9661bf8132236ef1d2a"),
    SOURCE_HEAD: (23_002, "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078"),
    SOURCE_DECISION: (6_790, "c7c70a8349f42169fd07d782a9439cedc512a3b687aae2518bb982496079d312"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    expected_bytes, expected_hash = EXPECTED[path]
    actual = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    actual["identity_pass"] = (
        actual["bytes"] == expected_bytes and actual["sha256"] == expected_hash
    )
    return actual


def package(program_bytes: int, archive_bytes: int, invocation_bytes: int) -> dict[str, object]:
    total = archive_bytes + program_bytes + invocation_bytes
    return {
        "archive_bytes": archive_bytes,
        "program_and_head_bytes": program_bytes,
        "invocation_bytes_conservative": invocation_bytes,
        "conditional_total_bytes": total,
        "signed_distance_to_105m_bytes": total - TARGET,
        "margin_below_current_prize_ceiling_bytes": PRIZE_CEILING - total,
        "below_current_prize_ceiling": total <= PRIZE_CEILING,
        "at_or_below_105m": total <= TARGET,
    }


def main() -> int:
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    RESULT.mkdir(parents=True)
    artifacts = {
        "external_archive": artifact(EXTERNAL_ARCHIVE),
        "external_compressor": artifact(EXTERNAL_COMPRESSOR),
        "external_head": artifact(EXTERNAL_HEAD),
        "source_built_compressor": artifact(SOURCE_COMPRESSOR),
        "source_built_head": artifact(SOURCE_HEAD),
        "source_build_decision": artifact(SOURCE_DECISION),
    }
    source_decision = json.loads(SOURCE_DECISION.read_text())
    source_build_identity = (
        source_decision.get("decision", {}).get("promotion_authorized") is True
        and source_decision.get("independent_clean_build_identity", {}).get(
            "all_artifacts_byte_identical"
        )
        is True
    )
    invocation_bytes = len(INVOCATION.encode("ascii"))
    external = package(
        EXPECTED[EXTERNAL_COMPRESSOR][0] + EXPECTED[EXTERNAL_HEAD][0],
        EXPECTED[EXTERNAL_ARCHIVE][0],
        invocation_bytes,
    )
    source_built = package(
        EXPECTED[SOURCE_COMPRESSOR][0] + EXPECTED[SOURCE_HEAD][0],
        EXPECTED[EXTERNAL_ARCHIVE][0],
        invocation_bytes,
    )
    failed: list[str] = []
    if not all(bool(value["identity_pass"]) for value in artifacts.values()):
        failed.append("artifact_identity_mismatch")
    if not source_build_identity:
        failed.append("independent_source_build_identity_missing")
    if invocation_bytes != 48:
        failed.append("invocation_byte_count_mismatch")
    if external["conditional_total_bytes"] != 108_492_873:
        failed.append("external_total_mismatch")
    if source_built["conditional_total_bytes"] != 108_501_365:
        failed.append("source_built_total_mismatch")
    if not external["below_current_prize_ceiling"] or not source_built["below_current_prize_ceiling"]:
        failed.append("prize_ceiling_mismatch")
    if external["at_or_below_105m"] or source_built["at_or_below_105m"]:
        failed.append("target_boundary_mismatch")

    decision = {
        "schema": "enwiki9_cmix_obias_full1g_submission_accounting_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": (
            "Exact artifact and conditional package arithmetic only. The external form still "
            "requires terminal full decode and compressor reproduction; the source-built form "
            "uses the external archive size only as a conditional boundary until its active "
            "full encode terminates. Neither is a verified full-1G Gamma score."
        ),
        "score_credit_bytes": 0,
        "verified_full_1g_score_bytes": None,
        "target_bytes": TARGET,
        "current_prize_ceiling_bytes": PRIZE_CEILING,
        "invocation": {"text": INVOCATION, "bytes": invocation_bytes},
        "artifacts": artifacts,
        "independent_source_build_identity": source_build_identity,
        "external_artifact_form": external,
        "source_built_conditional_form": source_built,
        "failed_conditions": failed,
        "overall_pass": not failed,
        "verdict": "accounting_boundary_certified_full_scope_execution_pending" if not failed else "reject_accounting_boundary",
    }
    (RESULT / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
