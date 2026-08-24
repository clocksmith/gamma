#!/usr/bin/env python3
"""Verify Geekbench-5-bound q1 compression and decompression runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import platform
from pathlib import Path
from typing import Any

import jsonschema
import research_contracts


PROJECT = Path(__file__).resolve().parents[1]
CONTRACTS = PROJECT / "contracts/research/v1"
SOURCE_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-runtime-qualification.schema.json"
OUTPUT_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-runtime-qualification-verification.schema.json"
HOST_SCHEMA = CONTRACTS / "cmix-runtime-host-fingerprint.schema.json"
SOURCE_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-runtime-qualification.v1"
OUTPUT_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-runtime-qualification-verification.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
GUARD_SCHEMA = "gamma.enwiki9.resource-guard-receipt.v3"
STAGE_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-stage.v1"
WALL_TIME_NUMERATOR = 252_000_000
RSS_LIMIT_KIB = 9_765_625
CGROUP_LIMIT_BYTES = 10_000_000_000
DISK_LIMIT_BYTES = 100_000_000_000
SCORE_RE = re.compile(r"Single[- ]Core\s+Score\s*:?\s*([0-9][0-9,]*)", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(16 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def regular_file(path: Path, label: str) -> Path:
    absolute = (path if path.is_absolute() else Path.cwd() / path).absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"{label}: symlink component forbidden: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise ValueError(f"{label}: expected single-link regular file")
    return absolute.resolve(strict=True)


def artifact(path: Path) -> dict[str, Any]:
    path = regular_file(path, "artifact")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def artifact_matches(record: Any, label: str) -> bool:
    if not isinstance(record, dict):
        return False
    try:
        path = regular_file(Path(record["path"]), label)
    except (KeyError, OSError, ValueError):
        return False
    return path.stat().st_size == record.get("bytes") and sha256_file(path) == record.get("sha256")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(regular_file(path, "JSON artifact").read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def write_new(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
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


def parse_geekbench5_score(path: Path) -> int:
    raw = regular_file(path, "Geekbench report").read_bytes()
    text = raw.decode("utf-8", errors="replace")
    if re.search(r"Geekbench\s+5(?:\.|\s|$)", text, re.IGNORECASE) is None:
        raise ValueError("raw report does not identify Geekbench 5")
    scores = [int(value.replace(",", "")) for value in SCORE_RE.findall(text)]
    if len(scores) != 1 or scores[0] <= 0:
        raise ValueError("raw report does not contain exactly one positive single-core score")
    return scores[0]


def current_host_fingerprint() -> dict[str, Any]:
    machine_id = regular_file(Path("/etc/machine-id"), "machine id").read_bytes()
    model_names = sorted({
        line.split(":", 1)[1].strip()
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines()
        if line.lower().startswith("model name") and ":" in line
    })
    if not model_names:
        raise ValueError("current host exposes no CPU model name")
    return {
        "schema": "gamma.enwiki9.cmix-runtime-host-fingerprint.v1",
        "machine_id_sha256": hashlib.sha256(machine_id).hexdigest(),
        "uname_machine": platform.machine(),
        "cpu_model_names": model_names,
    }


def guard_pass(guard: dict[str, Any], phase: str, score: float, package_paths: list[str]) -> bool:
    expected_limit = WALL_TIME_NUMERATOR / score
    events = guard["cgroup_events"]["delta"]
    peaks = guard["peaks"]
    command = guard["command"]
    return bool(
        guard["schema"] == GUARD_SCHEMA
        and guard["phase"] == phase
        and guard["status"] == "complete"
        and guard["returncode"] == 0
        and math.isclose(guard["geekbench5_single_core_score"], score, rel_tol=0.0, abs_tol=1e-9)
        and math.isclose(guard["wall_time_limit_seconds"], expected_limit, rel_tol=0.0, abs_tol=1e-6)
        and guard["elapsed_s"] < expected_limit
        and guard["limit_mode"] == "tree"
        and guard["limit_kib"] == RSS_LIMIT_KIB
        and guard["official_decimal_limit_kib"] == RSS_LIMIT_KIB
        and guard["cgroup"]["requested_memory_max_bytes"] == CGROUP_LIMIT_BYTES
        and guard["cgroup"]["memory_max_bytes"] <= CGROUP_LIMIT_BYTES
        and guard["cgroup"]["joined_before_exec"] is True
        and peaks["max_sampled_tree_rss_kib"] < RSS_LIMIT_KIB
        and peaks["max_observed_process_vmhwm_kib"] < RSS_LIMIT_KIB
        and peaks["cgroup_memory_peak_bytes"] < CGROUP_LIMIT_BYTES
        and peaks["max_sampled_scratch_logical_bytes"] < DISK_LIMIT_BYTES
        and peaks["max_sampled_scratch_allocated_bytes"] < DISK_LIMIT_BYTES
        and peaks["max_sampled_allowed_cpu_count"] <= 1
        and events.get("max", 0) == 0
        and events.get("oom", 0) == 0
        and events.get("oom_kill", 0) == 0
        and events.get("oom_group_kill", 0) == 0
        and all(guard["measurements"].values())
        and not any(guard["guards"].values())
        and all(path in command for path in package_paths)
    )


def verify(receipt_path: Path) -> tuple[dict[str, Any], bool]:
    source = load_json(receipt_path)
    jsonschema.Draft202012Validator(json.loads(SOURCE_SCHEMA.read_text(encoding="utf-8"))).validate(source)
    if source["schema"] != SOURCE_SCHEMA_ID:
        raise ValueError("runtime receipt schema mismatch")
    checks: dict[str, bool] = {}
    checks["source_artifacts_match"] = all(
        artifact_matches(record, label)
        for label, record in (
            ("population", source["population"]),
            ("benchmark report", source["benchmark"]["raw_report"]),
            ("host fingerprint", source["benchmark"]["host_fingerprint"]),
            ("packaged compressor", source["package"]["packaged_compressor"]),
            ("head", source["package"]["head"]),
            ("package archive", source["package"]["archive"]),
            ("compression guard", source["guards"]["compression"]),
            ("decompression guard", source["guards"]["decompression"]),
            ("compression stage", source["stage_receipts"]["compression"]),
            ("decompression stage", source["stage_receipts"]["decompression"]),
            ("output archive", source["outputs"]["archive"]),
            ("restored corpus", source["outputs"]["restored"]),
        )
    )
    parsed_score = parse_geekbench5_score(Path(source["benchmark"]["raw_report"]["path"]))
    declared_score = source["benchmark"]["single_core_score"]
    checks["geekbench5_report_rederived"] = parsed_score == declared_score
    host_fingerprint = load_json(Path(source["benchmark"]["host_fingerprint"]["path"]))
    jsonschema.Draft202012Validator(json.loads(HOST_SCHEMA.read_text(encoding="utf-8"))).validate(host_fingerprint)
    checks["current_host_fingerprint_exact"] = host_fingerprint == current_host_fingerprint()

    guards = {name: load_json(Path(record["path"])) for name, record in source["guards"].items()}
    stages = {name: load_json(Path(record["path"])) for name, record in source["stage_receipts"].items()}
    for name, value in guards.items():
        value_source = source["guards"][name]["path"]
        research_contracts.validate_artifact(Path(value_source))
        if value["schema"] != GUARD_SCHEMA:
            raise ValueError(f"{value_source}: unexpected guard schema")
    for name, value in stages.items():
        path = Path(source["stage_receipts"][name]["path"])
        research_contracts.validate_artifact(path)
        if value["schema"] != STAGE_SCHEMA:
            raise ValueError(f"{path}: unexpected stage schema")

    package = source["package"]
    checks["compression_guard_pass"] = guard_pass(
        guards["compression"], "compression", declared_score,
        [package["packaged_compressor"]["path"], package["head"]["path"]],
    )
    checks["decompression_guard_pass"] = guard_pass(
        guards["decompression"], "decompression", declared_score,
        [package["archive"]["path"]],
    )
    encode = stages["compression"]
    decode = stages["decompression"]
    checks["stages_pass"] = (
        encode["mode"] == "encode"
        and decode["mode"] == "decode"
        and encode["return_code"] == decode["return_code"] == 0
        and encode["stage_pass"] is True
        and decode["stage_pass"] is True
        and encode["backing_cleanup_pass"] is True
        and decode["backing_cleanup_pass"] is True
        and decode["exact_raw_inverse_pass"] is True
    )
    checks["stage_inputs_exact_package"] = (
        encode["inputs"]["package"] == package["packaged_compressor"]
        and encode["inputs"]["head"] == package["head"]
        and decode["inputs"]["archive"] == package["archive"]
    )
    checks["archive_and_inverse_bound"] = (
        encode["outputs"]["archive"] == package["archive"]
        and source["outputs"]["archive"] == package["archive"]
        and decode["outputs"]["restored"] == source["outputs"]["restored"]
    )
    expected_limit = WALL_TIME_NUMERATOR / declared_score
    runtime_eligible = all(checks.values())
    derived = {
        "geekbench5_single_core_score": declared_score,
        "wall_time_limit_seconds": expected_limit,
        "compression_elapsed_seconds": guards["compression"]["elapsed_s"],
        "decompression_elapsed_seconds": guards["decompression"]["elapsed_s"],
        "compression_runtime_pass": checks["compression_guard_pass"],
        "decompression_runtime_pass": checks["decompression_guard_pass"],
        "runtime_eligible": runtime_eligible,
    }
    errors = [f"check failed: {name}" for name, passed in checks.items() if not passed]
    output = {
        "schema": OUTPUT_SCHEMA_ID,
        "candidate_id": CANDIDATE_ID,
        "source_receipt": artifact(receipt_path),
        "checks": checks,
        "derived": derived,
        "errors": errors,
        "verification_pass": not errors,
        "claim_boundary": "Exact-package runtime qualification on the Geekbench-5-measured host only; no compression or score credit.",
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.Draft202012Validator(json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))).validate(output)
    return output, not errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt_path = regular_file(args.receipt, "runtime receipt")
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit("output already exists")
    output, passed = verify(receipt_path)
    write_new(args.output, output)
    print(json.dumps(output, sort_keys=True, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
