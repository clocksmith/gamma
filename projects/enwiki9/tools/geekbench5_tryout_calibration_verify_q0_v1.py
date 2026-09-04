#!/usr/bin/env python3
"""Independently verify guarded Geekbench 5 Tryout calibration evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
from typing import Any

import managed_exclusive_lease_verify


PROJECT = Path(__file__).resolve().parents[1]
PLAN_SCHEMA = "gamma.enwiki9.geekbench5-tryout-calibration-plan.v1"
RECEIPT_SCHEMA = "gamma.enwiki9.geekbench5-tryout-calibration.v1"
WORKER_SCHEMA = "gamma.enwiki9.geekbench5-tryout-calibration-worker.v1"
VERIFY_SCHEMA = "gamma.enwiki9.geekbench5-tryout-calibration-verification.v1"
CANDIDATE = "geekbench5_5_5_1_tryout_calibration_q0_v1"
SCORE_RE = re.compile(r"Single[- ]Core\s+Score\s*:?\s*([0-9][0-9,]*)", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(16 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def regular_file(path: Path, label: str) -> Path:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label}: symlink component forbidden: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label}: expected single-link regular file")
    return absolute.resolve(strict=True)


def load_json(path: Path, label: str) -> tuple[Path, dict[str, Any]]:
    path = regular_file(path, label)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{label}: expected JSON object")
    return path, value


def verify_binding(record: Any, label: str) -> Path:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise RuntimeError(f"{label}: malformed binding")
    path = Path(str(record["path"]))
    if not path.is_absolute():
        path = PROJECT / path
    path = regular_file(path, label)
    if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
        raise RuntimeError(f"{label}: binding mismatch")
    return path


def artifact(path: Path) -> dict[str, Any]:
    path = regular_file(path, "verification artifact")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def write_new(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
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


def command_sha256(argv: list[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(value) for value in argv)).hexdigest()


def host_fingerprint() -> dict[str, Any]:
    models = sorted(
        {
            line.split(":", 1)[1].strip()
            for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines()
            if line.lower().startswith("model name") and ":" in line
        }
    )
    return {
        "schema": "gamma.enwiki9.cmix-runtime-host-fingerprint.v1",
        "machine_id_sha256": hashlib.sha256(Path("/etc/machine-id").read_bytes()).hexdigest(),
        "uname_machine": platform.machine(),
        "uname_release": platform.release(),
        "cpu_model_names": models,
    }


def check(condition: bool, name: str, checks: dict[str, bool], errors: list[str]) -> None:
    checks[name] = bool(condition)
    if not condition:
        errors.append(name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    plan_path, plan = load_json(
        args.plan if args.plan.is_absolute() else PROJECT / args.plan,
        "calibration plan",
    )
    if sha256_file(plan_path) != args.plan_sha256:
        raise RuntimeError("calibration plan SHA-256 mismatch")
    receipt_path, receipt = load_json(args.receipt, "producer receipt")
    if plan.get("$schema") != PLAN_SCHEMA or plan.get("candidate_id") != CANDIDATE:
        raise RuntimeError("calibration plan identity mismatch")
    if receipt.get("$schema") != RECEIPT_SCHEMA or receipt.get("candidate_id") != CANDIDATE:
        raise RuntimeError("producer receipt identity mismatch")
    verifier = verify_binding(plan["implementation"]["verifier"], "calibration verifier")
    if verifier != Path(__file__).resolve(strict=True):
        raise RuntimeError("plan does not bind this verifier")
    implementations = {
        name: verify_binding(record, f"implementation {name}")
        for name, record in plan["implementation"].items()
    }
    if implementations["lease_verifier"] != Path(
        managed_exclusive_lease_verify.__file__
    ).resolve(strict=True):
        raise RuntimeError("lease verifier import mismatch")
    for name, record in plan["antecedents"].items():
        verify_binding(record, f"antecedent {name}")
    geekbench = {
        name: verify_binding(record, f"Geekbench {name}")
        for name, record in plan["geekbench"].items()
    }
    system_tools = {
        name: verify_binding(record, f"system tool {name}")
        for name, record in plan["system_tools"].items()
    }

    checks: dict[str, bool] = {}
    errors: list[str] = []
    check(receipt.get("plan") == artifact(plan_path), "producer_plan_binding", checks, errors)
    check(
        receipt.get("implementation") == artifact(implementations["producer"]),
        "producer_implementation_binding",
        checks,
        errors,
    )
    host_path = verify_binding(receipt.get("host"), "host receipt")
    _, observed_host = load_json(host_path, "host receipt")
    check(observed_host == host_fingerprint(), "current_host_identity", checks, errors)

    worker_path = verify_binding(receipt.get("worker_receipt"), "worker receipt")
    _, worker = load_json(worker_path, "worker receipt")
    check(worker.get("$schema") == WORKER_SCHEMA, "worker_schema", checks, errors)
    check(worker.get("candidate_id") == CANDIDATE, "worker_candidate", checks, errors)
    check(worker.get("plan") == artifact(plan_path), "worker_plan_binding", checks, errors)
    check(
        worker.get("implementation")
        == artifact(implementations["worker"]),
        "worker_implementation_binding",
        checks,
        errors,
    )

    runs = worker.get("runs")
    check(isinstance(runs, list) and len(runs) == 3, "three_worker_runs", checks, errors)
    valid_scores: list[tuple[str, int, dict[str, Any]]] = []
    if isinstance(runs, list):
        for index, run in enumerate(runs, 1):
            if not isinstance(run, dict):
                errors.append(f"run_{index}_object")
                continue
            run_id = f"run-{index}"
            expected_argv = [
                str(system_tools["unshare"]),
                "--map-current-user",
                "--net",
                str(geekbench["launcher"]),
                "--cpu",
            ]
            check(run.get("run_id") == run_id, f"{run_id}_identity", checks, errors)
            check(run.get("argv") == expected_argv, f"{run_id}_argv", checks, errors)
            check(
                run.get("argv_sha256") == command_sha256(expected_argv),
                f"{run_id}_argv_digest",
                checks,
                errors,
            )
            stdout_path = verify_binding(run.get("stdout"), f"{run_id} stdout")
            verify_binding(run.get("stderr"), f"{run_id} stderr")
            text = stdout_path.read_bytes().decode("utf-8", errors="replace")
            scores = [int(value.replace(",", "")) for value in SCORE_RE.findall(text)]
            identifies = re.search(r"Geekbench\s+5(?:\.|\s|$)", text, re.IGNORECASE) is not None
            valid = (
                run.get("timed_out") is False
                and identifies
                and len(scores) == 1
                and scores[0] > 0
                and run.get("single_core_scores") == scores
                and run.get("valid_score") is True
            )
            check(valid, f"{run_id}_valid_score", checks, errors)
            if valid:
                valid_scores.append((run_id, scores[0], run["stdout"]))

    all_valid = len(valid_scores) == 3
    relative_spread = (
        (max(value for _, value, _ in valid_scores) - min(value for _, value, _ in valid_scores))
        / max(value for _, value, _ in valid_scores)
        if all_valid
        else None
    )
    stability = (
        relative_spread is not None
        and relative_spread <= float(plan["benchmark"]["maximum_relative_score_spread"])
    )
    check(worker.get("all_runs_valid") is all_valid, "worker_all_runs_valid", checks, errors)
    check(worker.get("relative_score_spread") == relative_spread, "score_spread", checks, errors)
    check(worker.get("score_stability_pass") is stability, "score_stability", checks, errors)
    selected = max(valid_scores, key=lambda row: row[1]) if all_valid and stability else None
    check(
        worker.get("selected_run_id") == (selected[0] if selected else None),
        "selected_run",
        checks,
        errors,
    )
    check(
        worker.get("selected_single_core_score") == (selected[1] if selected else None),
        "selected_score",
        checks,
        errors,
    )
    check(
        worker.get("selected_raw_report") == (selected[2] if selected else None),
        "selected_report",
        checks,
        errors,
    )
    worker_pass = all_valid and stability
    check(worker.get("worker_calibration_pass") is worker_pass, "worker_pass", checks, errors)

    resources = receipt.get("resources", {})
    memory_limit = int(plan["resources"]["memory_max_bytes"])
    resource_pass = bool(
        resources.get("sample_count", 0) > 0
        and resources.get("affinity_violations") == []
        and isinstance(resources.get("memory_peak_bytes"), int)
        and resources["memory_peak_bytes"] < memory_limit
        and resources.get("memory_event_delta", {}).get("oom", 0) == 0
        and resources.get("memory_event_delta", {}).get("oom_kill", 0) == 0
        and resources.get("memory_event_delta", {}).get("max", 0) == 0
        and resources.get("cgroup_cleanup_pass") is True
        and receipt.get("network", {}).get("isolation_observed") is True
    )
    check(resources.get("resource_pass") is resource_pass, "resource_pass", checks, errors)

    quiet = receipt.get("quiet_cpu_evidence", {}).get("average_busy_fraction", {})
    quiet_pass = bool(quiet) and all(
        isinstance(value, (int, float))
        and value <= float(plan["admission"]["maximum_average_busy_fraction"])
        for value in quiet.values()
    )
    check(quiet_pass, "quiet_cpu_admission", checks, errors)
    check(receipt.get("preflight", {}).get("blockers") == [], "initial_preflight", checks, errors)
    check(
        receipt.get("post_quiet_preflight", {}).get("blockers") == [],
        "post_quiet_preflight",
        checks,
        errors,
    )

    lease = receipt.get("lease", {})
    transition = verify_binding(lease.get("transition"), "lease transition")
    terminal = verify_binding(lease.get("terminal"), "terminal lease")
    lease_args = argparse.Namespace(transition_log=transition, terminal_lease=terminal, output=None)
    independent_lease, lease_verified = managed_exclusive_lease_verify.verify(lease_args)
    stored_lease_path = verify_binding(lease.get("verification"), "lease verification")
    _, stored_lease = load_json(stored_lease_path, "lease verification")
    check(lease_verified and stored_lease == independent_lease, "lease_verification", checks, errors)
    lease_path = Path(plan["paths"]["lease_path"])
    check(
        not lease_path.exists() and not lease_path.with_name(f"{lease_path.name}.lock").exists(),
        "canonical_lease_released",
        checks,
        errors,
    )

    expected_authority = bool(
        worker_pass
        and resource_pass
        and quiet_pass
        and lease_verified
        and receipt.get("worker_returncode") == 0
        and not errors
    )
    check(
        receipt.get("terminal_authority") is expected_authority,
        "terminal_authority_consistency",
        checks,
        errors,
    )
    check(
        receipt.get("selected_single_core_score") == (selected[1] if selected else None),
        "producer_selected_score",
        checks,
        errors,
    )
    verification = {
        "$schema": VERIFY_SCHEMA,
        "candidate_id": CANDIDATE,
        "source_receipt": artifact(receipt_path),
        "checks": checks,
        "errors": errors,
        "evidence_valid": not errors,
        "authority_verified": expected_authority and not errors,
        "selected_single_core_score": selected[1] if selected and not errors else None,
        "runtime_limit_seconds": 252000000 / selected[1] if selected and not errors else None,
        "objective_credit_bytes": 0,
        "cmix_100m_successor_authorized": False,
    }
    write_new(args.output, verification)
    print(json.dumps(artifact(args.output), sort_keys=True))
    return 0 if verification["authority_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
