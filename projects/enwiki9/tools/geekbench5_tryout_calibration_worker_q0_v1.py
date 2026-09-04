#!/usr/bin/env python3
"""Execute frozen network-isolated Geekbench 5 Tryout calibration repeats."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import time
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
PLAN_SCHEMA = "gamma.enwiki9.geekbench5-tryout-calibration-plan.v1"
RECEIPT_SCHEMA = "gamma.enwiki9.geekbench5-tryout-calibration-worker.v1"
CANDIDATE = "geekbench5_5_5_1_tryout_calibration_q0_v1"
SCORE_RE = re.compile(r"Single[- ]Core\s+Score\s*:?\s*([0-9][0-9,]*)", re.IGNORECASE)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def load_json(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(regular_file(path, label).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{label}: expected JSON object")
    return value


def verify_file(record: Any, label: str) -> Path:
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
    path = regular_file(path, "worker output")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def write_new(path: Path, payload: bytes) -> None:
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


def terminate_group(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    process.wait()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--result-root", required=True, type=Path)
    parser.add_argument("--scratch-root", required=True, type=Path)
    args = parser.parse_args()

    plan_path = args.plan if args.plan.is_absolute() else PROJECT / args.plan
    plan = load_json(plan_path, "calibration plan")
    if (
        plan.get("$schema") != PLAN_SCHEMA
        or plan.get("candidate_id") != CANDIDATE
        or plan.get("execution_authorized") is not True
        or plan.get("benchmark_authorized") is not True
    ):
        raise RuntimeError("calibration plan identity or authority mismatch")

    worker = verify_file(plan["implementation"]["worker"], "calibration worker")
    if worker != Path(__file__).resolve(strict=True):
        raise RuntimeError("plan does not bind this worker")
    launcher = verify_file(plan["geekbench"]["launcher"], "Geekbench launcher")
    verify_file(plan["geekbench"]["worker"], "Geekbench worker")
    verify_file(plan["geekbench"]["data"], "Geekbench data")
    unshare = verify_file(plan["system_tools"]["unshare"], "unshare executable")

    result_root = args.result_root.absolute()
    scratch_root = args.scratch_root.absolute()
    if result_root != Path(plan["paths"]["result_root"]):
        raise RuntimeError("worker result root mismatch")
    if scratch_root != Path(plan["paths"]["scratch_root"]):
        raise RuntimeError("worker scratch root mismatch")
    if result_root.resolve(strict=True) != result_root or scratch_root.resolve(strict=True) != scratch_root:
        raise RuntimeError("worker roots must be exact existing directories")
    if (result_root / "worker-receipt.json").exists():
        raise RuntimeError("worker receipt already exists")

    repetitions = int(plan["benchmark"]["repetitions"])
    if repetitions != 3:
        raise RuntimeError("calibration requires exactly three repeats")
    timeout_seconds = int(plan["benchmark"]["per_run_timeout_seconds"])
    if timeout_seconds <= 0:
        raise RuntimeError("invalid per-run timeout")

    run_records: list[dict[str, Any]] = []
    for index in range(1, repetitions + 1):
        run_id = f"run-{index}"
        run_scratch = scratch_root / run_id
        run_scratch.mkdir(mode=0o700)
        cache = run_scratch / "cache"
        config = run_scratch / "config"
        data_home = run_scratch / "data"
        temporary = run_scratch / "tmp"
        for path in (cache, config, data_home, temporary):
            path.mkdir(mode=0o700)
        stdout_path = result_root / f"{run_id}.stdout"
        stderr_path = result_root / f"{run_id}.stderr"
        argv = [
            str(unshare),
            "--map-current-user",
            "--net",
            str(launcher),
            "--cpu",
        ]
        environment = {
            "PATH": "/usr/bin:/bin",
            "LC_ALL": "C",
            "TMPDIR": str(temporary),
            "XDG_CACHE_HOME": str(cache),
            "XDG_CONFIG_HOME": str(config),
            "XDG_DATA_HOME": str(data_home),
        }
        started_utc = utc_now()
        started = time.monotonic_ns()
        timed_out = False
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            process = subprocess.Popen(
                argv,
                cwd=launcher.parent,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                env=environment,
                start_new_session=True,
            )
            try:
                returncode = process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                terminate_group(process)
                returncode = process.returncode
        ended = time.monotonic_ns()
        stdout_bytes = stdout_path.read_bytes()
        stderr_bytes = stderr_path.read_bytes()
        stdout_text = stdout_bytes.decode("utf-8", errors="replace")
        scores = [int(value.replace(",", "")) for value in SCORE_RE.findall(stdout_text)]
        identifies_geekbench5 = re.search(
            r"Geekbench\s+5(?:\.|\s|$)", stdout_text, re.IGNORECASE
        ) is not None
        valid_score = (
            not timed_out
            and identifies_geekbench5
            and len(scores) == 1
            and scores[0] > 0
        )
        run_records.append(
            {
                "run_id": run_id,
                "argv": argv,
                "argv_sha256": command_sha256(argv),
                "environment": environment,
                "started_utc": started_utc,
                "ended_utc": utc_now(),
                "elapsed_ns": ended - started,
                "returncode": returncode,
                "timed_out": timed_out,
                "stdout": artifact(stdout_path),
                "stderr": artifact(stderr_path),
                "stdout_identifies_geekbench5": identifies_geekbench5,
                "single_core_scores": scores,
                "valid_score": valid_score,
                "stderr_mentions_no_network_or_upload": any(
                    token in stderr_bytes.lower()
                    for token in (b"network", b"upload", b"connect", b"resolve")
                ),
            }
        )

    valid_runs = [record for record in run_records if record["valid_score"]]
    all_runs_valid = len(valid_runs) == repetitions
    valid_scores = [record["single_core_scores"][0] for record in valid_runs]
    relative_score_spread = (
        (max(valid_scores) - min(valid_scores)) / max(valid_scores)
        if all_runs_valid
        else None
    )
    score_stability_pass = (
        relative_score_spread is not None
        and relative_score_spread
        <= float(plan["benchmark"]["maximum_relative_score_spread"])
    )
    selected = (
        max(valid_runs, key=lambda record: record["single_core_scores"][0])
        if all_runs_valid and score_stability_pass
        else None
    )
    receipt = {
        "$schema": RECEIPT_SCHEMA,
        "candidate_id": CANDIDATE,
        "terminal": True,
        "plan": artifact(plan_path),
        "implementation": artifact(worker),
        "benchmark_command": "network-isolated Geekbench 5 Tryout --cpu",
        "selection_rule": "maximum single-core score across exactly three valid repeats",
        "runs": run_records,
        "all_runs_valid": all_runs_valid,
        "relative_score_spread": relative_score_spread,
        "score_stability_pass": score_stability_pass,
        "selected_run_id": selected["run_id"] if selected is not None else None,
        "selected_single_core_score": (
            selected["single_core_scores"][0] if selected is not None else None
        ),
        "selected_raw_report": selected["stdout"] if selected is not None else None,
        "worker_calibration_pass": all_runs_valid and score_stability_pass,
        "claim_authority": "worker_evidence_only",
        "objective_credit_bytes": 0,
    }
    write_new(
        result_root / "worker-receipt.json",
        json.dumps(receipt, sort_keys=True, indent=2).encode("ascii") + b"\n",
    )
    return 0 if receipt["worker_calibration_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
