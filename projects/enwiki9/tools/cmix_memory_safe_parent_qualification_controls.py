#!/usr/bin/env python3
"""Exercise q1 qualification pass, truthful-failure, and malformed controls."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


OUTPUT_SCHEMA = "gamma.enwiki9.cmix-memory-safe-parent-qualification-controls.v1"
INPUT_SCHEMA = "gamma.enwiki9.cmix-memory-safe-parent-qualification-receipt.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def sha256_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def regular_file(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise SystemExit(f"{label}: symlink component forbidden: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise SystemExit(f"{label}: expected single-link regular file")
    return absolute.resolve(strict=True)


def fixture() -> dict[str, Any]:
    source_hashes = {
        "source_closure_sha256": digest("source-closure"),
        "program_lock_sha256": digest("program-lock"),
        "build_a_receipt_sha256": digest("build-a-receipt"),
        "build_b_receipt_sha256": digest("build-b-receipt"),
        "build_verification_sha256": digest("build-verification"),
        "binary_a_sha256": digest("binary"),
        "binary_b_sha256": digest("binary"),
        "command_contract_sha256": digest("command-contract"),
    }
    archive_hash = digest("archive")
    payload_hash = digest("payload")
    probability_hash = digest("full-probability-stream")
    archive_bytes = 108_022_224
    program_bytes = 491_483
    evidence_fields = [
        "source_closure_sha256",
        "program_lock_sha256",
        "build_a_receipt_sha256",
        "build_b_receipt_sha256",
        "build_verification_sha256",
        "command_contract_sha256",
    ]
    return {
        "schema": INPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "authoritative_parent_id": "cmix_obias_source_full1g_roundtrip_a_qm0_v1",
        "population": {"path": "enwik9", "bytes": 1_000_000_000, "sha256": CANONICAL_SHA256, "canonical_enwik9": True},
        "source_and_build": {
            **source_hashes,
            "binary_identity_pass": True,
            "compiler_trace_controls_pass": True,
        },
        "probability_identity": {
            "scopes": [
                {"offset": 0, "bytes": 250_000, "parent_integer_probability_sha256": digest("scope-0"), "candidate_integer_probability_sha256": digest("scope-0"), "identity_pass": True},
                {"offset": 500_000_000, "bytes": 250_000, "parent_integer_probability_sha256": digest("scope-1"), "candidate_integer_probability_sha256": digest("scope-1"), "identity_pass": True},
                {"offset": 999_750_000, "bytes": 250_000, "parent_integer_probability_sha256": digest("scope-2"), "candidate_integer_probability_sha256": digest("scope-2"), "identity_pass": True},
            ],
            "full_stream_parent_sha256": probability_hash,
            "full_stream_candidate_sha256": probability_hash,
            "full_stream_identity_pass": True,
            "persistent_state_identity_pass": True,
        },
        "roundtrips": [
            {"arm": "A", "archive_bytes": archive_bytes, "archive_sha256": archive_hash, "payload_sha256": payload_hash, "encode_return_code": 0, "decode_return_code": 0, "decoded_bytes": 1_000_000_000, "decoded_sha256": CANONICAL_SHA256, "bytewise_inverse_pass": True, "cleanup_pass": True},
            {"arm": "B", "archive_bytes": archive_bytes, "archive_sha256": archive_hash, "payload_sha256": payload_hash, "encode_return_code": 0, "decode_return_code": 0, "decoded_bytes": 1_000_000_000, "decoded_sha256": CANONICAL_SHA256, "bytewise_inverse_pass": True, "cleanup_pass": True},
        ],
        "resources": {
            "process_tree_peak_rss_kib": 9_000_000,
            "largest_process_vmhwm_kib": 8_900_000,
            "cgroup_memory_peak_bytes": 9_500_000_000,
            "memory_events_oom": 0,
            "memory_events_oom_kill": 0,
            "maximum_logical_cpus": 1,
            "scratch_logical_peak_bytes": 20_000_000_000,
            "scratch_allocated_peak_bytes": 20_000_000_000,
            "scratch_after_cleanup_bytes": 0,
            "temporary_disk_pass": True,
            "memory_pass": True,
            "runtime_measured": True,
            "runtime_eligible": True,
        },
        "package": {
            "archive_bytes": archive_bytes,
            "required_program_model_bytes": program_bytes,
            "other_counted_bytes": 0,
            "complete_counted_bytes": archive_bytes + program_bytes,
            "dependency_closure_pass": True,
            "license_closure_pass": True,
        },
        "decisions": {
            "build_identity_pass": True,
            "probability_identity_pass": True,
            "payload_identity_pass": True,
            "archive_identity_pass": True,
            "two_run_determinism_pass": True,
            "exact_inverse_pass": True,
            "memory_pass": True,
            "temporary_disk_pass": True,
            "package_accounting_complete": True,
            "memory_safe_parent_qualified": True,
            "officially_verified": False,
            "gamma_compression_credit_bytes": 0,
            "gamma_score_credit_bytes": 0,
        },
        "claim_boundary": "synthetic control fixture with no scientific authority",
        "evidence": [
            {"path": f"evidence/{field}.json", "bytes": 1, "sha256": source_hashes[field]}
            for field in evidence_fields
        ],
    }


def truthful_memory_failure(value: dict[str, Any]) -> None:
    value["resources"]["process_tree_peak_rss_kib"] = 9_765_626
    value["resources"]["memory_pass"] = False
    value["decisions"]["memory_pass"] = False
    value["decisions"]["memory_safe_parent_qualified"] = False


def truthful_cleanup_failure(value: dict[str, Any]) -> None:
    value["roundtrips"][1]["cleanup_pass"] = False
    value["decisions"]["memory_safe_parent_qualified"] = False


def truthful_archive_identity_failure(value: dict[str, Any]) -> None:
    value["roundtrips"][1]["archive_sha256"] = digest("different-archive")
    value["decisions"]["archive_identity_pass"] = False
    value["decisions"]["two_run_determinism_pass"] = False
    value["decisions"]["memory_safe_parent_qualified"] = False


def truthful_probability_identity_failure(value: dict[str, Any]) -> None:
    value["probability_identity"]["full_stream_candidate_sha256"] = digest("different-full-probability-stream")
    value["probability_identity"]["full_stream_identity_pass"] = False
    value["decisions"]["probability_identity_pass"] = False
    value["decisions"]["two_run_determinism_pass"] = False
    value["decisions"]["memory_safe_parent_qualified"] = False


def malformed_package_sum(value: dict[str, Any]) -> None:
    value["package"]["complete_counted_bytes"] += 1


def contradictory_memory_boolean(value: dict[str, Any]) -> None:
    value["resources"]["process_tree_peak_rss_kib"] = 9_765_626


def contradictory_scope_identity(value: dict[str, Any]) -> None:
    value["probability_identity"]["scopes"][0]["candidate_integer_probability_sha256"] = digest("different-scope")


def missing_authority_evidence(value: dict[str, Any]) -> None:
    value["evidence"] = value["evidence"][:-1]


def run_verifier(verifier: Path, receipt: Path, lease: Path, output: Path) -> subprocess.CompletedProcess[bytes]:
    environment = {"LANG": "C", "LC_ALL": "C", "PYTHONHASHSEED": "0", "TZ": "UTC"}
    return subprocess.run(
        [sys.executable, os.fspath(verifier), "--receipt", os.fspath(receipt), "--exclusive-lease", os.fspath(lease), "--verification", os.fspath(output)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verifier", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    verifier = regular_file(args.verifier, "verifier")
    lease = args.exclusive_lease.absolute()
    lock_path = lease.with_name(f"{lease.name}.lock")
    if lease.exists() or lease.is_symlink() or lock_path.exists() or lock_path.is_symlink():
        raise SystemExit("exclusive lease namespace is occupied")
    if args.evidence_root.exists() or args.evidence_root.is_symlink():
        raise SystemExit("evidence root already exists")
    if args.receipt.exists() or args.receipt.is_symlink():
        raise SystemExit("receipt already exists")
    args.evidence_root.mkdir(parents=True)

    controls: dict[str, tuple[Callable[[dict[str, Any]], None] | None, bool | None, bool | None]] = {
        "positive": (None, True, True),
        "truthful_memory_failure": (truthful_memory_failure, True, False),
        "truthful_cleanup_failure": (truthful_cleanup_failure, True, False),
        "truthful_archive_identity_failure": (truthful_archive_identity_failure, True, False),
        "truthful_probability_identity_failure": (truthful_probability_identity_failure, True, False),
        "malformed_package_sum": (malformed_package_sum, False, False),
        "contradictory_memory_boolean": (contradictory_memory_boolean, False, False),
        "contradictory_scope_identity": (contradictory_scope_identity, False, False),
        "missing_authority_evidence": (missing_authority_evidence, False, False),
    }
    errors: list[str] = []
    results: dict[str, dict[str, Any]] = {}
    for name, (mutation, expected_verified, expected_qualified) in controls.items():
        root = args.evidence_root / name
        root.mkdir()
        value = fixture()
        if mutation is not None:
            mutation(value)
        input_path = root / "input.json"
        output_path = root / "verification.json"
        input_path.write_bytes(json_bytes(value))
        completed = run_verifier(verifier, input_path, lease, output_path)
        observed_verified: bool | None = None
        observed_qualified: bool | None = None
        if output_path.is_file():
            output = json.loads(output_path.read_text(encoding="utf-8"))
            if isinstance(output, dict):
                observed_verified = output.get("verified") if isinstance(output.get("verified"), bool) else None
                observed_qualified = output.get("qualified") if isinstance(output.get("qualified"), bool) else None
        passed = (
            observed_verified is expected_verified
            and observed_qualified is expected_qualified
            and ((completed.returncode == 0) is expected_verified)
        )
        if not passed:
            errors.append(f"control {name} produced an unexpected decision")
        results[name] = {
            "return_code": completed.returncode,
            "output_present": output_path.is_file(),
            "observed_verified": observed_verified,
            "observed_qualified": observed_qualified,
            "expected_verified": expected_verified,
            "expected_qualified": expected_qualified,
            "pass": passed,
            "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        }

    active_root = args.evidence_root / "active_exclusive_lease"
    active_root.mkdir()
    active_lease = active_root / "lease.json"
    active_lease.write_bytes(json_bytes({"active": True, "candidate_id": "negative-control"}))
    active_input = active_root / "input.json"
    active_input.write_bytes(json_bytes(fixture()))
    active_output = active_root / "verification.json"
    active_completed = run_verifier(verifier, active_input, active_lease, active_output)
    active_pass = active_completed.returncode != 0 and not active_output.exists()
    if not active_pass:
        errors.append("active exclusive lease was not rejected without output")
    results["active_exclusive_lease"] = {
        "return_code": active_completed.returncode,
        "output_present": active_output.is_file(),
        "observed_verified": None,
        "observed_qualified": None,
        "expected_verified": None,
        "expected_qualified": None,
        "pass": active_pass,
        "stdout_sha256": hashlib.sha256(active_completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(active_completed.stderr).hexdigest(),
    }
    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "verified": not errors,
        "errors": errors,
        "verifier_sha256": sha256_file(verifier),
        "controls": results,
        "claim_authority": "none",
        "promotion_authority": False,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("xb") as stream:
        stream.write(json_bytes(output))
        stream.flush()
        os.fsync(stream.fileno())
    return 0 if output["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
