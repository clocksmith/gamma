#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import pathlib
import signal
import subprocess
import sys
import time

try:
    from projects.enwiki9.tools import research_contracts
except ModuleNotFoundError:
    import research_contracts


def _children_of(pid: int) -> list[int]:
    task_root = pathlib.Path("/proc") / str(pid) / "task"
    try:
        child_files = [task / "children" for task in task_root.iterdir()]
    except OSError:
        return []
    out: set[int] = set()
    for path in child_files:
        try:
            text = path.read_text().strip()
        except OSError:
            continue
        for part in text.split():
            try:
                out.add(int(part))
            except ValueError:
                continue
    return sorted(out)


def _proc_tree(root: int) -> list[int]:
    seen: set[int] = set()
    stack = [root]
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        stack.extend(_children_of(pid))
    return sorted(seen)


def _rss_kib(pid: int) -> int | None:
    path = pathlib.Path("/proc") / str(pid) / "status"
    try:
        for line in path.read_text(errors="replace").splitlines():
            if line.startswith("VmRSS:"):
                fields = line.split()
                if len(fields) >= 2:
                    return int(fields[1])
    except OSError:
        return None
    return None


def _thread_state(path: pathlib.Path) -> str | None:
    try:
        suffix = path.read_text(errors="replace").rsplit(")", 1)[1].strip()
    except OSError:
        return None
    except IndexError:
        return None
    fields = suffix.split()
    return fields[0] if fields else None


def _thread_state_counts(pid: int) -> tuple[int, int]:
    task_root = pathlib.Path("/proc") / str(pid) / "task"
    live = 0
    runnable = 0
    try:
        tasks = list(task_root.iterdir())
    except OSError:
        return (0, 0)
    for task in tasks:
        state = _thread_state(task / "stat")
        if state is None:
            continue
        live += 1
        if state == "R":
            runnable += 1
    return (live, runnable)


def _allowed_cpus(pid: int) -> list[int]:
    try:
        return sorted(os.sched_getaffinity(pid))
    except (AttributeError, OSError):
        return []


def _sample(root: int) -> dict:
    processes = []
    max_single = 0
    total = 0
    live_threads = 0
    runnable_threads = 0
    allowed_cpu_union: set[int] = set()
    for pid in _proc_tree(root):
        rss = _rss_kib(pid)
        if rss is None:
            continue
        process_live_threads, process_runnable_threads = _thread_state_counts(pid)
        allowed_cpus = _allowed_cpus(pid)
        total += rss
        max_single = max(max_single, rss)
        live_threads += process_live_threads
        runnable_threads += process_runnable_threads
        allowed_cpu_union.update(allowed_cpus)
        processes.append(
            {
                "pid": pid,
                "rss_kib": rss,
                "live_threads": process_live_threads,
                "runnable_threads": process_runnable_threads,
                "allowed_cpus": allowed_cpus,
            }
        )
    return {
        "processes": processes,
        "max_single_rss_kib": max_single,
        "tree_rss_kib": total,
        "tree_live_threads": live_threads,
        "tree_runnable_threads": runnable_threads,
        "allowed_cpu_union": sorted(allowed_cpu_union),
    }


def _disk_bytes(paths: list[pathlib.Path]) -> int:
    total = 0
    for root in paths:
        try:
            if root.is_file():
                total += root.stat().st_size
                continue
        except OSError:
            continue
        try:
            descendants = root.rglob("*")
            for path in descendants:
                try:
                    if path.is_file() and not path.is_symlink():
                        total += path.stat().st_size
                except OSError:
                    continue
        except OSError:
            continue
    return total


def _write_json(path: pathlib.Path | None, payload: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-kib", type=int, required=True)
    parser.add_argument(
        "--limit-mode",
        choices=("max_single", "tree"),
        default="max_single",
        help="enforce the largest process RSS or aggregate process-tree RSS",
    )
    parser.add_argument("--official-decimal-limit-kib", type=int)
    parser.add_argument("--sample-interval", type=float, default=5.0)
    parser.add_argument(
        "--scratch-path",
        action="append",
        type=pathlib.Path,
        default=[],
        help="candidate-owned temporary file or directory to measure recursively",
    )
    parser.add_argument("--temporary-disk-limit-bytes", type=int)
    parser.add_argument(
        "--max-logical-cpus",
        type=int,
        help="abort when any observed process affinity permits more logical CPUs",
    )
    parser.add_argument("--guard-json", type=pathlib.Path)
    parser.add_argument("--label", default=None)
    parser.add_argument(
        "--phase",
        choices=("compression", "decompression", "diagnostic"),
        default="diagnostic",
    )
    parser.add_argument("--geekbench5-single-core-score", type=float)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("missing command after --")
    if args.temporary_disk_limit_bytes is not None and not args.scratch_path:
        raise SystemExit("--temporary-disk-limit-bytes requires at least one --scratch-path")
    if args.max_logical_cpus is not None and args.max_logical_cpus <= 0:
        raise SystemExit("--max-logical-cpus must be positive")
    if (
        args.geekbench5_single_core_score is not None
        and args.geekbench5_single_core_score <= 0
    ):
        raise SystemExit("--geekbench5-single-core-score must be positive")
    missing_scratch_paths = [path for path in args.scratch_path if not path.exists()]
    if missing_scratch_paths:
        joined = ", ".join(str(path) for path in missing_scratch_paths)
        raise SystemExit(f"scratch paths must exist before launch: {joined}")

    objective = research_contracts.objective_binding()
    objective_contract = research_contracts.validate_objective()
    sample_interval_seconds = max(args.sample_interval, 0.1)
    wall_time_limit_seconds = (
        objective_contract["resources"]["wallTime"]["maximumSecondsNumerator"]
        / args.geekbench5_single_core_score
        if args.geekbench5_single_core_score is not None
        else None
    )
    wall_time_measurement_complete = (
        args.phase in {"compression", "decompression"}
        and wall_time_limit_seconds is not None
    )
    started_at = time.monotonic()
    proc = subprocess.Popen(command, preexec_fn=os.setsid)
    peak_single = 0
    peak_tree = 0
    peak_sample: dict | None = None
    peak_tree_sample: dict | None = None
    latest_sample: dict | None = None
    peak_temporary_disk_bytes = 0
    peak_live_threads = 0
    peak_runnable_threads = 0
    peak_allowed_cpu_count = 0
    affinity_measurement_complete = True
    sample_count = 0
    exceeded = False
    official_decimal_exceeded = False
    temporary_disk_exceeded = False
    logical_cpu_limit_exceeded = False
    wall_time_exceeded = False
    failure: str | None = None

    try:
        while True:
            rc = proc.poll()
            sample = _sample(proc.pid)
            latest_sample = sample
            sample_count += 1
            if sample["max_single_rss_kib"] > peak_single:
                peak_single = sample["max_single_rss_kib"]
                peak_sample = sample
            if sample["tree_rss_kib"] > peak_tree:
                peak_tree = sample["tree_rss_kib"]
                peak_tree_sample = sample
            temporary_disk_bytes = _disk_bytes(args.scratch_path)
            peak_temporary_disk_bytes = max(
                peak_temporary_disk_bytes,
                temporary_disk_bytes,
            )
            peak_live_threads = max(peak_live_threads, sample["tree_live_threads"])
            peak_runnable_threads = max(
                peak_runnable_threads,
                sample["tree_runnable_threads"],
            )
            peak_allowed_cpu_count = max(
                peak_allowed_cpu_count,
                len(sample["allowed_cpu_union"]),
            )
            if any(not process["allowed_cpus"] for process in sample["processes"]):
                affinity_measurement_complete = False
            elapsed_s = time.monotonic() - started_at
            _write_json(
                args.guard_json,
                {
                    "schema": "gamma.enwiki9.resource-guard-receipt.v2",
                    "objective": objective,
                    "label": args.label,
                    "phase": args.phase,
                    "command": command,
                    "sample_interval_seconds": sample_interval_seconds,
                    "geekbench5_single_core_score": args.geekbench5_single_core_score,
                    "wall_time_limit_seconds": wall_time_limit_seconds,
                    "wall_time_measurement_complete": wall_time_measurement_complete,
                    "wall_time_exceeded": False,
                    "limit_kib": args.limit_kib,
                    "limit_mode": args.limit_mode,
                    "official_decimal_limit_kib": args.official_decimal_limit_kib,
                    "official_decimal_over_limit_kib": (
                        max(0, sample["tree_rss_kib"] - args.official_decimal_limit_kib)
                        if args.official_decimal_limit_kib is not None
                        else None
                    ),
                    "scratch_paths": [str(path) for path in args.scratch_path],
                    "temporary_disk_limit_bytes": args.temporary_disk_limit_bytes,
                    "temporary_disk_measurement_complete": bool(args.scratch_path),
                    "latest_temporary_disk_bytes": temporary_disk_bytes,
                    "max_sampled_temporary_disk_bytes": peak_temporary_disk_bytes,
                    "max_logical_cpus": args.max_logical_cpus,
                    "affinity_measurement_complete": affinity_measurement_complete,
                    "max_sampled_allowed_cpu_count": peak_allowed_cpu_count,
                    "logical_cpu_guard_exceeded": False,
                    "max_sampled_tree_live_threads": peak_live_threads,
                    "max_sampled_tree_runnable_threads": peak_runnable_threads,
                    "max_sampled_single_rss_kib": peak_single,
                    "max_sampled_tree_rss_kib": peak_tree,
                    "peak_sample": peak_sample,
                    "peak_tree_sample": peak_tree_sample,
                    "latest_sample": sample,
                    "sample_count": sample_count,
                    "rss_guard_exceeded": False,
                    "official_decimal_memory_exceeded": False,
                    "temporary_disk_guard_exceeded": False,
                    "returncode": None,
                    "status": "running",
                    "elapsed_s": round(elapsed_s, 4),
                },
            )
            measured_kib = (
                sample["tree_rss_kib"]
                if args.limit_mode == "tree"
                else sample["max_single_rss_kib"]
            )
            if measured_kib > args.limit_kib:
                exceeded = True
                failure = "compression_rss_crossed_local_guard_before_archive_or_roundtrip"
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()
                break
            if (
                args.official_decimal_limit_kib is not None
                and sample["tree_rss_kib"] >= args.official_decimal_limit_kib
            ):
                official_decimal_exceeded = True
                failure = "process_tree_exceeded_official_decimal_10gb_limit"
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()
                break
            if (
                args.max_logical_cpus is not None
                and len(sample["allowed_cpu_union"]) > args.max_logical_cpus
            ):
                logical_cpu_limit_exceeded = True
                failure = "process_affinity_exceeded_logical_cpu_limit"
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()
                break
            if (
                args.temporary_disk_limit_bytes is not None
                and temporary_disk_bytes >= args.temporary_disk_limit_bytes
            ):
                temporary_disk_exceeded = True
                failure = "candidate_scratch_tree_exceeded_temporary_disk_limit"
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()
                break
            if (
                wall_time_limit_seconds is not None
                and elapsed_s >= wall_time_limit_seconds
            ):
                wall_time_exceeded = True
                failure = "command_exceeded_objective_wall_time_limit"
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()
                break
            if rc is not None:
                break
            time.sleep(sample_interval_seconds)
    finally:
        rc = proc.poll()
        if rc is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            rc = proc.wait()

    exceeded = (
        peak_tree > args.limit_kib
        if args.limit_mode == "tree"
        else peak_single > args.limit_kib
    )
    official_decimal_exceeded = (
        args.official_decimal_limit_kib is not None
        and peak_tree >= args.official_decimal_limit_kib
    )
    temporary_disk_exceeded = (
        args.temporary_disk_limit_bytes is not None
        and peak_temporary_disk_bytes >= args.temporary_disk_limit_bytes
    )
    logical_cpu_limit_exceeded = (
        args.max_logical_cpus is not None
        and peak_allowed_cpu_count > args.max_logical_cpus
    )
    final_elapsed_s = time.monotonic() - started_at
    wall_time_exceeded = (
        wall_time_limit_seconds is not None
        and final_elapsed_s >= wall_time_limit_seconds
    )
    if failure is None:
        if exceeded:
            failure = "compression_rss_crossed_local_guard_before_archive_or_roundtrip"
        elif official_decimal_exceeded:
            failure = "process_tree_exceeded_official_decimal_10gb_limit"
        elif temporary_disk_exceeded:
            failure = "candidate_scratch_tree_exceeded_temporary_disk_limit"
        elif logical_cpu_limit_exceeded:
            failure = "process_affinity_exceeded_logical_cpu_limit"
        elif wall_time_exceeded:
            failure = "command_exceeded_objective_wall_time_limit"

    payload = {
        "schema": "gamma.enwiki9.resource-guard-receipt.v2",
        "objective": objective,
        "label": args.label,
        "phase": args.phase,
        "command": command,
        "sample_interval_seconds": sample_interval_seconds,
        "geekbench5_single_core_score": args.geekbench5_single_core_score,
        "wall_time_limit_seconds": wall_time_limit_seconds,
        "wall_time_measurement_complete": wall_time_measurement_complete,
        "wall_time_exceeded": wall_time_exceeded,
        "limit_kib": args.limit_kib,
        "limit_mode": args.limit_mode,
        "official_decimal_limit_kib": args.official_decimal_limit_kib,
        "official_decimal_over_limit_kib": (
            max(0, peak_tree - args.official_decimal_limit_kib)
            if args.official_decimal_limit_kib is not None
            else None
        ),
        "scratch_paths": [str(path) for path in args.scratch_path],
        "temporary_disk_limit_bytes": args.temporary_disk_limit_bytes,
        "temporary_disk_measurement_complete": bool(args.scratch_path),
        "max_sampled_temporary_disk_bytes": peak_temporary_disk_bytes,
        "max_logical_cpus": args.max_logical_cpus,
        "affinity_measurement_complete": affinity_measurement_complete,
        "max_sampled_allowed_cpu_count": peak_allowed_cpu_count,
        "logical_cpu_guard_exceeded": logical_cpu_limit_exceeded,
        "max_sampled_tree_live_threads": peak_live_threads,
        "max_sampled_tree_runnable_threads": peak_runnable_threads,
        "max_sampled_single_rss_kib": peak_single,
        "max_sampled_tree_rss_kib": peak_tree,
        "peak_sample": peak_sample,
        "peak_tree_sample": peak_tree_sample,
        "latest_sample": latest_sample,
        "sample_count": sample_count,
        "rss_guard_exceeded": exceeded,
        "official_decimal_memory_exceeded": official_decimal_exceeded,
        "temporary_disk_guard_exceeded": temporary_disk_exceeded,
        "returncode": rc,
        "status": (
            "rss_guard_exceeded"
            if exceeded
            else "aborted_official_decimal_memory_limit"
            if official_decimal_exceeded
            else "temporary_disk_guard_exceeded"
            if temporary_disk_exceeded
            else "logical_cpu_guard_exceeded"
            if logical_cpu_limit_exceeded
            else "wall_time_guard_exceeded"
            if wall_time_exceeded
            else "complete"
        ),
        "elapsed_s": round(final_elapsed_s, 4),
    }
    if failure is not None:
        payload["failure"] = failure
    _write_json(args.guard_json, payload)
    print(json.dumps({"rss_guard": payload}, indent=2))
    if (
        exceeded
        or official_decimal_exceeded
        or temporary_disk_exceeded
        or logical_cpu_limit_exceeded
        or wall_time_exceeded
    ):
        return 75
    return int(rc or 0)


if __name__ == "__main__":
    sys.exit(main())
