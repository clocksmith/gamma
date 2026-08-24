#!/usr/bin/env python3
"""Independently verify a failed q1 guarded full-corpus Arm A receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-failure-verification.v1"
SOURCE_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1"
GUARD_SCHEMA = "gamma.enwiki9.resource-guard-receipt.v3"
CANONICAL_BYTES = 1_000_000_000
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(16 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def artifact_matches(record: dict[str, Any]) -> bool:
    path = Path(record.get("path", ""))
    return bool(
        path.is_file()
        and path.stat().st_size == record.get("bytes")
        and sha256_file(path) == record.get("sha256")
    )


def write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600
    )
    try:
        cursor = 0
        while cursor < len(payload):
            written = os.write(descriptor, payload[cursor:])
            if written <= 0:
                raise OSError(f"short write: {path}")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def latest_progress(stderr_path: Path) -> tuple[str | None, float | None]:
    text = stderr_path.read_bytes().decode("utf-8", "replace").replace("\r", "\n")
    phase: str | None = None
    percent: float | None = None
    for line in text.splitlines():
        match = re.search(r"\b(progress|pretraining): ([0-9]+(?:\.[0-9]+)?)%", line)
        if match:
            phase = match.group(1)
            percent = float(match.group(2))
    return phase, percent


def verify(receipt_path: Path, guard_path: Path) -> tuple[dict[str, Any], bool]:
    receipt = json.loads(receipt_path.read_text())
    guard = json.loads(guard_path.read_text())
    encode = receipt["stages"]["encode"]
    stderr_path = Path(encode["guard_receipt"]["path"]).parent / "encode.codec.stderr"
    progress_phase, progress_percent = latest_progress(stderr_path)
    cgroup = guard["cgroup"]
    events = guard["cgroup_events"]["delta"]
    peaks = guard["peaks"]
    checks = {
        "source_receipt_schema": receipt.get("schema") == SOURCE_SCHEMA,
        "source_receipt_arm_a": receipt.get("arm") == "a",
        "source_receipt_matches": artifact(receipt_path)["sha256"] == sha256_file(receipt_path),
        "guard_schema": guard.get("schema") == GUARD_SCHEMA,
        "guard_matches_source_receipt": artifact_matches(encode["guard_receipt"])
        and Path(encode["guard_receipt"]["path"]).resolve() == guard_path.resolve(),
        "antecedent_artifacts_match": all(
            artifact_matches(record)
            for name, record in receipt["antecedents"].items()
            if name != "arm_a_reference"
        ),
        "package_artifacts_match": all(
            artifact_matches(receipt["package"][name])
            for name in (
                "raw_binary",
                "dictionary_payload",
                "article_order_payload",
                "header",
                "packaged_compressor",
                "head",
                "build_verification",
            )
        ),
        "canonical_population_bound": receipt["population"]["bytes"] == CANONICAL_BYTES
        and receipt["population"]["sha256"] == CANONICAL_SHA256
        and artifact_matches(receipt["population"]),
        "effective_cgroup_cap_bound": cgroup["requested_memory_max_bytes"] == 10_000_000_000
        and cgroup["memory_max_bytes"] == 9_999_998_976
        and cgroup["memory_max_rounding_bytes"] == 1_024,
        "cgroup_cap_reached": peaks["cgroup_memory_peak_bytes"] == cgroup["memory_max_bytes"]
        and events["max"] > 0,
        "no_oom_kill": events["oom"] == 0
        and events["oom_kill"] == 0
        and events["oom_group_kill"] == 0,
        "guard_failed_only_cgroup_cap": guard["status"] == "cgroup_memory_guard_exceeded"
        and guard["returncode"] == -15
        and guard["guards"]["cgroup_memory_guard_exceeded"] is True
        and all(
            not value
            for name, value in guard["guards"].items()
            if name != "cgroup_memory_guard_exceeded"
        ),
        "process_tree_rss_below_limit": peaks["max_sampled_tree_rss_kib"] < guard["limit_kib"],
        "single_cpu_observed": peaks["max_sampled_allowed_cpu_count"] == 1,
        "measurements_complete": all(guard["measurements"].values()),
        "pretraining_started": progress_phase == "pretraining"
        and progress_percent is not None
        and progress_percent > 0.0,
        "encode_stage_receipt_missing": encode["stage_receipt"] is None
        and not (guard_path.parent / "stage-receipt.json").exists(),
        "decode_not_started": receipt["stages"]["decode"] is None,
        "no_outputs_or_inverse_claim": all(value is None for value in receipt["outputs"].values())
        and receipt["identity"]["exact_raw_inverse_pass"] is False,
        "zero_credit": receipt["accounting"]["score_credit_bytes"] == 0
        and receipt["gamma_compression_credit_bytes"] == 0
        and receipt["gamma_score_credit_bytes"] == 0,
        "terminal_failure_truthful": receipt["terminal_pass"] is False
        and receipt["memory_safe_parent_qualified"] is False
        and receipt["promotion_authorized"] is False,
        "scratch_preserved": receipt["cleanup"]["scratch_preserved_on_failure"] is True
        and Path(receipt["cleanup"]["scratch_root"]).is_dir(),
        "lease_released": receipt["cleanup"]["lease_release_pass"] is True
        and receipt["cleanup"]["lease_removed_pass"] is True
        and not Path(receipt["lease"]["evidence"]["path"]).parents[2]
        .joinpath("operations/runtime/exclusive_full1g.json")
        .exists(),
        "cgroup_removed": receipt["cleanup"]["cgroup_removed_pass"] is True
        and not Path(cgroup["path"]).exists(),
    }
    errors = [f"check failed: {name}" for name, passed in checks.items() if not passed]
    output = {
        "schema": SCHEMA,
        "candidate_id": "cmix_filebacked_fxcm_full_a_qm7_v2",
        "source_receipt": artifact(receipt_path),
        "guard_receipt": artifact(guard_path),
        "observed": {
            "effective_cgroup_memory_max_bytes": cgroup["memory_max_bytes"],
            "cgroup_memory_peak_bytes": peaks["cgroup_memory_peak_bytes"],
            "cgroup_max_event_count": events["max"],
            "process_tree_peak_rss_kib": peaks["max_sampled_tree_rss_kib"],
            "last_progress_phase": progress_phase,
            "last_progress_percent": progress_percent,
        },
        "checks": checks,
        "errors": errors,
        "verification_pass": not errors,
        "claim_boundary": (
            "Independent verification of the preserved Arm A resource failure only; "
            "it grants no archive, inversion, runtime, memory qualification, or score credit."
        ),
        "gamma_score_credit_bytes": 0,
    }
    return output, not errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--guard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        output, passed = verify(args.receipt.resolve(strict=True), args.guard.resolve(strict=True))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        output = {
            "schema": SCHEMA,
            "candidate_id": "cmix_filebacked_fxcm_full_a_qm7_v2",
            "source_receipt": None,
            "guard_receipt": None,
            "observed": None,
            "checks": {},
            "errors": [f"{type(exc).__name__}: {exc}"],
            "verification_pass": False,
            "claim_boundary": "Independent verification failed before evidence could be bound.",
            "gamma_score_credit_bytes": 0,
        }
        passed = False
    payload = (json.dumps(output, sort_keys=True, indent=2) + "\n").encode("ascii")
    write_new(args.output, payload)
    sys.stdout.write(payload.decode("ascii"))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
