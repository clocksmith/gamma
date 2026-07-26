#!/usr/bin/env python3
"""Run a matched archive-identity or score/runtime Pareto screen."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ORDER = ("reference", "candidate", "candidate", "reference")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


def guard_is_clean(guard: dict[str, Any], process_returncode: int) -> bool:
    return bool(
        process_returncode == 0
        and guard.get("status") == "complete"
        and guard.get("returncode") == 0
        and guard.get("rss_guard_exceeded") is False
        and guard.get("official_decimal_over_limit_kib", 0) == 0
    )


def summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    roles = {role: [] for role in ("reference", "candidate")}
    role_hashes = {role: set() for role in roles}
    role_sizes = {role: set() for role in roles}
    for run in runs:
        role = run["role"]
        roles[role].append(float(run["guard_result"]["elapsed_s"]))
        role_hashes[role].add(run["archive"]["sha256"])
        role_sizes[role].add(int(run["archive"]["bytes"]))
    reference_median = statistics.median(roles["reference"])
    candidate_median = statistics.median(roles["candidate"])
    hashes = {run["archive"]["sha256"] for run in runs}
    sizes = {run["archive"]["bytes"] for run in runs}
    all_clean = all(run["clean_guard"] for run in runs)
    archive_identity = len(hashes) == 1 and len(sizes) == 1
    role_archive_determinism = {
        role: len(role_hashes[role]) == 1 and len(role_sizes[role]) == 1
        for role in roles
    }
    role_archive_bytes = {
        role: next(iter(role_sizes[role]))
        if role_archive_determinism[role]
        else None
        for role in roles
    }
    ratio = candidate_median / reference_median
    return {
        "all_guards_clean": all_clean,
        "archive_identity": archive_identity,
        "role_archive_determinism": role_archive_determinism,
        "role_archive_bytes": role_archive_bytes,
        "archive_sha256_values": sorted(hashes),
        "archive_size_values": sorted(sizes),
        "reference_elapsed_s": roles["reference"],
        "candidate_elapsed_s": roles["candidate"],
        "reference_median_elapsed_s": reference_median,
        "candidate_median_elapsed_s": candidate_median,
        "candidate_over_reference_runtime_ratio": ratio,
        "candidate_runtime_reduction_fraction": 1.0 - ratio,
    }


def evaluate_pareto_candidate(
    metrics: dict[str, Any],
    *,
    scope_bytes: int,
    baseline_counted_forecast_bytes: int,
    calibration_factor: float,
    target_score_bytes: int,
    minimum_runtime_reduction_fraction: float,
) -> dict[str, Any]:
    deterministic = all(metrics["role_archive_determinism"].values())
    reference_bytes = metrics["role_archive_bytes"]["reference"]
    candidate_bytes = metrics["role_archive_bytes"]["candidate"]
    if not deterministic or reference_bytes is None or candidate_bytes is None:
        return {
            "verdict": "reject_nondeterministic_role_archive",
            "larger_prize_gate_authorized": False,
            "next_action": (
                "preserve the mismatched same-role archives and debug determinism "
                "before using score or runtime evidence"
            ),
        }

    archive_delta_bytes = candidate_bytes - reference_bytes
    counted_delta = (
        archive_delta_bytes * (10_000_000 / scope_bytes) * calibration_factor
    )
    projected_counted_bytes = math.ceil(
        baseline_counted_forecast_bytes + counted_delta
    )
    target_margin_bytes = target_score_bytes - projected_counted_bytes
    runtime_reduction = metrics["candidate_runtime_reduction_fraction"]
    score_pass = projected_counted_bytes <= target_score_bytes
    runtime_pass = runtime_reduction >= minimum_runtime_reduction_fraction

    if score_pass and runtime_pass:
        verdict = "pareto_prefix_screen_passed"
        next_action = (
            "preserve the candidate identity and confirm score transfer and runtime "
            "at the next governed constructive scope"
        )
    elif score_pass and archive_delta_bytes < 0:
        verdict = "score_projection_passed_runtime_screen_failed"
        next_action = (
            "preserve the provisional score gain as component evidence, but do not "
            "promote this implementation as a runtime successor"
        )
    elif score_pass and runtime_reduction > 0:
        verdict = "target_projection_passed_runtime_threshold_missed"
        next_action = (
            "preserve the measured runtime/score tradeoff, but do not promote until "
            "a composition clears the runtime threshold without exhausting target margin"
        )
    elif score_pass:
        verdict = "target_projection_passed_without_runtime_gain"
        next_action = "retire this exact candidate unchanged"
    elif runtime_pass:
        verdict = "runtime_screen_passed_score_projection_failed"
        next_action = (
            "preserve the runtime result, but do not promote without a score-paying "
            "composition or a smaller changed-stream loss"
        )
    else:
        verdict = "pareto_prefix_screen_failed"
        next_action = "retire this exact candidate unchanged"

    return {
        "verdict": verdict,
        "larger_prize_gate_authorized": score_pass and runtime_pass,
        "next_action": next_action,
        "reference_archive_bytes": reference_bytes,
        "candidate_archive_bytes": candidate_bytes,
        "candidate_archive_delta_bytes": archive_delta_bytes,
        "candidate_archive_savings_bytes": -archive_delta_bytes,
        "baseline_counted_forecast_bytes": baseline_counted_forecast_bytes,
        "calibration_factor": calibration_factor,
        "candidate_provisional_counted_forecast_bytes": projected_counted_bytes,
        "candidate_provisional_counted_forecast_percent": (
            projected_counted_bytes / 1_000_000_000 * 100
        ),
        "target_score_bytes": target_score_bytes,
        "target_score_percent": target_score_bytes / 1_000_000_000 * 100,
        "target_margin_bytes": target_margin_bytes,
        "minimum_runtime_reduction_fraction": minimum_runtime_reduction_fraction,
        "score_projection_pass": score_pass,
        "runtime_screen_pass": runtime_pass,
    }


def build_backend_command(
    *,
    binary: Path,
    dictionary: Path,
    input_path: Path,
    archive: Path,
    cpu_list: str | None,
) -> list[str]:
    command = [
        str(binary.resolve()),
        "-c",
        str(dictionary.resolve()),
        str(input_path.resolve()),
        str(archive.resolve()),
    ]
    if cpu_list:
        return ["taskset", "--cpu-list", cpu_list, *command]
    return command


def run_guarded(
    *,
    repo_root: Path,
    guard_tool: Path,
    label: str,
    command: list[str],
    guard_path: Path,
    stdout_path: Path,
    stderr_path: Path,
) -> tuple[subprocess.CompletedProcess[bytes], dict[str, Any]]:
    guarded_command = [
        sys.executable,
        str(guard_tool.resolve()),
        "--limit-kib",
        "10485760",
        "--official-decimal-limit-kib",
        "9765625",
        "--sample-interval",
        "0.25",
        "--guard-json",
        str(guard_path.resolve()),
        "--label",
        label,
        "--",
        *command,
    ]
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(
            guarded_command,
            cwd=repo_root,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    if not guard_path.is_file():
        raise RuntimeError(f"guard did not write {guard_path}")
    guard = json.loads(guard_path.read_text())
    return completed, guard


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--candidate-mode",
        choices=("identity", "pareto"),
        default="identity",
        help="identity requires one shared archive; pareto permits deterministic changed streams",
    )
    parser.add_argument("--baseline-counted-forecast-bytes", type=int)
    parser.add_argument("--calibration-factor", type=float)
    parser.add_argument("--target-score-bytes", type=int, default=109_000_000)
    parser.add_argument(
        "--minimum-runtime-reduction-fraction", type=float, default=0.0
    )
    parser.add_argument(
        "--cpu-list",
        help=(
            "optional taskset CPU list used for every matched run, for example "
            "0,2,4,6 for a four-physical-core qualification"
        ),
    )
    parser.add_argument(
        "--guard-tool",
        type=Path,
        default=Path("projects/enwiki9/tools/run_with_rss_guard.py"),
    )
    parser.add_argument("--lock", type=Path, default=Path("/tmp/enwiki9-heavy.lock"))
    args = parser.parse_args()

    if args.candidate_mode == "pareto":
        if args.baseline_counted_forecast_bytes is None:
            parser.error(
                "--baseline-counted-forecast-bytes is required in pareto mode"
            )
        if args.calibration_factor is None or args.calibration_factor <= 0:
            parser.error("a positive --calibration-factor is required in pareto mode")

    for path in (
        args.reference,
        args.candidate,
        args.dictionary,
        args.input,
        args.guard_tool,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_dir}")
    args.output_dir.mkdir(parents=True)

    runs: list[dict[str, Any]] = []
    binaries = {"reference": args.reference, "candidate": args.candidate}
    with args.lock.open("a+") as lock_stream:
        try:
            fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("enwiki9 heavy lock is already held") from error
        for index, role in enumerate(RUN_ORDER, start=1):
            archive = args.output_dir / f"{index:02d}_{role}.comp"
            guard_path = args.output_dir / f"{index:02d}_{role}_guard.json"
            command = build_backend_command(
                binary=binaries[role],
                dictionary=args.dictionary,
                input_path=args.input,
                archive=archive,
                cpu_list=args.cpu_list,
            )
            completed, guard = run_guarded(
                repo_root=repo_root,
                guard_tool=args.guard_tool,
                label=f"fx2_cmix21_backend_{args.candidate_mode}_{role}_{index}",
                command=command,
                guard_path=guard_path,
                stdout_path=args.output_dir / f"{index:02d}_{role}_stdout.log",
                stderr_path=args.output_dir / f"{index:02d}_{role}_stderr.log",
            )
            if not archive.is_file():
                raise RuntimeError(f"backend did not write {archive}")
            runs.append(
                {
                    "index": index,
                    "role": role,
                    "command": command,
                    "process_returncode": completed.returncode,
                    "clean_guard": guard_is_clean(guard, completed.returncode),
                    "archive": artifact(archive),
                    "guard": artifact(guard_path),
                    "guard_result": guard,
                }
            )

    metrics = summarize_runs(runs)
    scope_bytes = args.input.stat().st_size
    pareto_evaluation: dict[str, Any] | None = None
    if not metrics["all_guards_clean"]:
        verdict = "resource_or_process_failure"
        next_action = "preserve the failed guard evidence; do not use the candidate"
        larger_prize_gate_authorized = False
    elif args.candidate_mode == "pareto":
        pareto_evaluation = evaluate_pareto_candidate(
            metrics,
            scope_bytes=scope_bytes,
            baseline_counted_forecast_bytes=args.baseline_counted_forecast_bytes,
            calibration_factor=args.calibration_factor,
            target_score_bytes=args.target_score_bytes,
            minimum_runtime_reduction_fraction=(
                args.minimum_runtime_reduction_fraction
            ),
        )
        verdict = pareto_evaluation["verdict"]
        next_action = pareto_evaluation["next_action"]
        larger_prize_gate_authorized = pareto_evaluation[
            "larger_prize_gate_authorized"
        ]
    elif not metrics["archive_identity"]:
        verdict = "reject_nonidentical_backend"
        next_action = "retire the optimization because it changes the coded bitstream"
        larger_prize_gate_authorized = False
    elif scope_bytes < 250_000:
        verdict = "archive_identity_passed_requires_runtime_scope"
        next_action = "repeat the matched alternating screen at 250000 transformed bytes"
        larger_prize_gate_authorized = False
    elif metrics["candidate_runtime_reduction_fraction"] <= 0:
        verdict = "archive_identity_passed_no_runtime_gain"
        next_action = "retire the optimization because matched median runtime did not improve"
        larger_prize_gate_authorized = False
    else:
        verdict = "archive_identity_and_runtime_screen_passed"
        next_action = (
            "preserve the exact source delta and confirm the runtime effect at the next "
            "already-authorized constructive scope before changing package accounting"
        )
        larger_prize_gate_authorized = False

    receipt = {
        "schema": (
            "fx2_cmix21_backend_pareto_runtime_screen_v1"
            if args.candidate_mode == "pareto"
            else "fx2_cmix21_backend_identity_runtime_screen_v1"
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": (
            "matched_guarded_prefix_score_runtime_pareto_screen"
            if args.candidate_mode == "pareto"
            else "matched_guarded_prefix_archive_identity_and_runtime_screen"
        ),
        "scope_bytes": scope_bytes,
        "artifacts": {
            "reference_binary": artifact(args.reference),
            "candidate_binary": artifact(args.candidate),
            "dictionary": artifact(args.dictionary),
            "input": artifact(args.input),
        },
        "run_order": list(RUN_ORDER),
        "runtime_environment": {
            "requested_cpu_list": args.cpu_list,
            "cpu_affinity_constrained": bool(args.cpu_list),
        },
        "candidate_mode": args.candidate_mode,
        "runs": runs,
        "metrics": metrics,
        "pareto_evaluation": pareto_evaluation,
        "decision": {
            "verdict": verdict,
            "promotion_authorized": False,
            "larger_prize_gate_authorized": larger_prize_gate_authorized,
            "next_action": next_action,
        },
        "claim_boundary": (
            "This receipt proves deterministic same-prefix candidate/reference archives "
            "and matched runtime/resource behavior. Any counted changed-stream forecast "
            "is a calibrated prefix projection, not a full-corpus score."
            if args.candidate_mode == "pareto"
            else "This receipt proves only same-prefix archive identity and measured "
            "matched runtime/resource behavior. It does not prove a compression "
            "improvement, full-corpus runtime, official accounting, or the target score."
        ),
    }
    receipt_path = args.output_dir / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    valid_archive_evidence = (
        all(metrics["role_archive_determinism"].values())
        if args.candidate_mode == "pareto"
        else metrics["archive_identity"]
    )
    return 0 if metrics["all_guards_clean"] and valid_archive_evidence else 1


if __name__ == "__main__":
    raise SystemExit(main())
