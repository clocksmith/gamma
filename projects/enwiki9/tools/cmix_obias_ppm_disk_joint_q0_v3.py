#!/usr/bin/env python3
"""Fail-closed clean-versus-PPM0 disk-backed 250KB joint decision."""

from __future__ import annotations

import json
from pathlib import Path

import cmix_obias_bithead_delta_midas512_q0_v2 as monitor


ROOT = Path(__file__).resolve().parents[1]
CLEAN_ID = "cmix_obias_ppm_clean_250k_disk_q0_v1"
PPM_ID = "cmix_obias_ppm_always_purge_250k_disk_q0_v2"
CANDIDATE_ID = "cmix_obias_ppm_disk_joint_q0_v3"
RESULT = ROOT / "results" / CANDIDATE_ID
RSS_LIMIT_KIB = 9_765_625
DISK_LIMIT_BYTES = 100_000_000_000


def load(candidate_id: str) -> dict[str, object]:
    path = ROOT / "results" / candidate_id / "decision.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing terminal decision: {path}")
    value = json.loads(path.read_text())
    if value.get("candidate_id") != candidate_id:
        raise ValueError(f"candidate identity mismatch: {candidate_id}")
    return value


def same_bytes(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as a, right.open("rb") as b:
        while True:
            aa = a.read(8 << 20)
            bb = b.read(8 << 20)
            if aa != bb:
                return False
            if not aa:
                return True


def payload_identity(left: dict[str, object], right: dict[str, object]) -> bool:
    a = left.get("payload", {})
    b = right.get("payload", {})
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    try:
        pa = Path(str(a["path"]))
        pb = Path(str(b["path"]))
    except KeyError:
        return False
    return bool(
        pa.is_file()
        and pb.is_file()
        and a.get("bytes") == b.get("bytes")
        and a.get("sha256") == b.get("sha256")
        and same_bytes(pa, pb)
    )


def all_resources_within(value: object) -> bool:
    found: list[bool] = []

    def visit(node: object) -> None:
        if isinstance(node, dict):
            resource = node.get("resource")
            if isinstance(resource, dict) and "within_limit" in resource:
                found.append(resource.get("within_limit") is True)
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return bool(found) and all(found)


def disk_within(decision: dict[str, object]) -> bool:
    policy = decision.get("memory_policy", {})
    boundary = policy.get("scratch_boundary", {}) if isinstance(policy, dict) else {}
    peak = decision.get("scratch_peak", {})
    try:
        allocated = int(peak.get("allocated_bytes", -1)) if isinstance(peak, dict) else -1
    except (TypeError, ValueError):
        return False
    return bool(
        isinstance(boundary, dict)
        and boundary.get("memory_backed") is False
        and boundary.get("filesystem") not in {"tmpfs", "ramfs"}
        and 0 <= allocated <= DISK_LIMIT_BYTES
    )


def exact(decision: dict[str, object]) -> bool:
    integrity = decision.get("integrity", {})
    return bool(
        isinstance(integrity, dict)
        and integrity.get("raw_roundtrip_exact") is True
        and integrity.get("repeat_archive_and_payload_byte_identical") is True
        and decision.get("scratch_cleaned") is True
    )


def main() -> int:
    monitor.refuse_concurrent_cmix()
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    clean = load(CLEAN_ID)
    ppm = load(PPM_ID)
    gates = {
        "clean_roundtrip_repeat_cleanup": exact(clean),
        "ppm0_roundtrip_repeat_cleanup": exact(ppm),
        "clean_ppm0_payload_byte_identity": payload_identity(clean, ppm),
        "clean_process_tree_rss_within_limit": all_resources_within(clean),
        "ppm0_process_tree_rss_within_limit": all_resources_within(ppm),
        "clean_disk_scratch_within_limit": disk_within(clean),
        "ppm0_disk_scratch_within_limit": disk_within(ppm),
        "clean_compile_define_absent": (
            clean.get("memory_policy", {}).get("compile_define") is None
        ),
        "ppm0_compile_define_exact": (
            ppm.get("memory_policy", {}).get("compile_define")
            == "-DCMIX_PPMD_RSS_BUDGET_MB=0ULL"
        ),
    }
    passed = all(gates.values())
    result = {
        "schema": "gamma.enwiki9.cmix-obias-ppm-disk-joint-q0-v3",
        "candidate_id": CANDIDATE_ID,
        "status": "PASS" if passed else "REJECT",
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Opening-250KB probability-neutral disk/RSS infrastructure gate only; "
            "no larger-scope or compression claim."
        ),
        "inputs": {"clean": CLEAN_ID, "ppm0": PPM_ID},
        "limits": {
            "process_tree_rss_kib": RSS_LIMIT_KIB,
            "temporary_disk_bytes": DISK_LIMIT_BYTES,
        },
        "gates": gates,
        "promotion_authorized": passed,
        "next_action": (
            "Run one sealed 250KB causal arm at a time."
            if passed
            else "Retire or correct the PPM0 disk resource mechanism before causal arms."
        ),
    }
    RESULT.mkdir(parents=True)
    (RESULT / "decision.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({"event": "ppm_disk_joint", "passed": passed}), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
