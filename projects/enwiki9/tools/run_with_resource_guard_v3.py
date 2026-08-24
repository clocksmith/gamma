#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import signal
import stat
import subprocess
import sys
import time
from typing import Any

try:
    from projects.enwiki9.tools import research_contracts
except ModuleNotFoundError:
    import research_contracts


SCHEMA = "gamma.enwiki9.resource-guard-receipt.v3"
STRICT_DECIMAL_LIMIT_KIB = 9_765_625
STRICT_DECIMAL_LIMIT_BYTES = 10_000_000_000


def _read_text(path: pathlib.Path) -> str:
    return path.read_text(errors="replace").strip()


def _read_int(path: pathlib.Path) -> int:
    value = _read_text(path)
    if value == "max":
        raise ValueError(f"expected finite integer in {path}")
    return int(value)


def _read_events(path: pathlib.Path) -> dict[str, int]:
    events: dict[str, int] = {}
    for line in _read_text(path).splitlines():
        fields = line.split()
        if len(fields) != 2:
            raise ValueError(f"invalid cgroup event line in {path}: {line!r}")
        events[fields[0]] = int(fields[1])
    return events


def _event_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    return {
        key: max(0, after.get(key, 0) - before.get(key, 0))
        for key in sorted(set(before) | set(after))
    }


def _cgroup_pids(cgroup_path: pathlib.Path) -> list[int]:
    text = _read_text(cgroup_path / "cgroup.procs")
    return sorted({int(part) for part in text.split()}) if text else []


def _prepare_cgroup(cgroup_path: pathlib.Path, memory_max_bytes: int) -> dict[str, Any]:
    required = (
        "cgroup.procs",
        "memory.current",
        "memory.events",
        "memory.max",
        "memory.peak",
    )
    if not cgroup_path.is_dir():
        raise SystemExit(f"dedicated cgroup-v2 path does not exist: {cgroup_path}")
    missing = [name for name in required if not (cgroup_path / name).exists()]
    if missing:
        raise SystemExit(f"cgroup-v2 files missing from {cgroup_path}: {', '.join(missing)}")
    occupants = _cgroup_pids(cgroup_path)
    if occupants:
        raise SystemExit(f"dedicated cgroup is not empty: {occupants}")

    memory_max_path = cgroup_path / "memory.max"
    previous_memory_max = _read_text(memory_max_path)
    try:
        memory_max_path.write_text(f"{memory_max_bytes}\n")
    except OSError as exc:
        raise SystemExit(f"cannot set {memory_max_path}: {exc}") from exc
    effective_memory_max_bytes = _read_int(memory_max_path)
    page_size = os.sysconf("SC_PAGE_SIZE")
    rounding_bytes = memory_max_bytes - effective_memory_max_bytes
    if rounding_bytes < 0 or rounding_bytes >= page_size:
        raise SystemExit(
            "cgroup memory.max did not bind to a page-rounded safe cap: "
            f"requested={memory_max_bytes} effective={effective_memory_max_bytes}"
        )

    memory_peak_path = cgroup_path / "memory.peak"
    try:
        memory_peak_path.write_text("0\n")
    except OSError as exc:
        raise SystemExit(f"cannot reset {memory_peak_path}: {exc}") from exc
    peak_after_reset = _read_int(memory_peak_path)
    current_after_reset = _read_int(cgroup_path / "memory.current")
    if peak_after_reset > current_after_reset:
        raise SystemExit("memory.peak retained pre-run usage after reset")

    return {
        "path": str(cgroup_path),
        "inode": cgroup_path.stat().st_ino,
        "previous_memory_max": previous_memory_max,
        "requested_memory_max_bytes": memory_max_bytes,
        "memory_max_bytes": effective_memory_max_bytes,
        "memory_max_rounding_bytes": rounding_bytes,
        "memory_peak_reset": True,
        "joined_before_exec": False,
        "events_baseline": _read_events(cgroup_path / "memory.events"),
    }


def _proc_start_ticks(pid: int) -> int | None:
    try:
        suffix = (pathlib.Path("/proc") / str(pid) / "stat").read_text().rsplit(")", 1)[1]
        return int(suffix.split()[19])
    except (OSError, IndexError, ValueError):
        return None


def _proc_status(pid: int) -> tuple[int, int] | None:
    path = pathlib.Path("/proc") / str(pid) / "status"
    values: dict[str, int] = {}
    try:
        for line in path.read_text(errors="replace").splitlines():
            if line.startswith(("VmRSS:", "VmHWM:")):
                fields = line.split()
                if len(fields) >= 2:
                    values[fields[0].rstrip(":")] = int(fields[1])
    except OSError:
        return None
    if "VmRSS" not in values or "VmHWM" not in values:
        return None
    return values["VmRSS"], values["VmHWM"]


def _thread_state(path: pathlib.Path) -> str | None:
    try:
        suffix = path.read_text(errors="replace").rsplit(")", 1)[1].strip()
    except (OSError, IndexError):
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
        return 0, 0
    for task in tasks:
        state_name = _thread_state(task / "stat")
        if state_name is None:
            continue
        live += 1
        if state_name == "R":
            runnable += 1
    return live, runnable


def _allowed_cpus(pid: int) -> list[int]:
    try:
        return sorted(os.sched_getaffinity(pid))
    except (AttributeError, OSError):
        return []


def _comm(pid: int) -> str | None:
    try:
        return _read_text(pathlib.Path("/proc") / str(pid) / "comm")
    except OSError:
        return None


def _sample_processes(cgroup_path: pathlib.Path) -> dict[str, Any]:
    initial_pids = _cgroup_pids(cgroup_path)
    processes: list[dict[str, Any]] = []
    missing_status: list[int] = []
    allowed_cpu_union: set[int] = set()
    tree_rss_kib = 0
    max_single_rss_kib = 0
    tree_live_threads = 0
    tree_runnable_threads = 0

    for pid in initial_pids:
        status_values = _proc_status(pid)
        start_ticks = _proc_start_ticks(pid)
        if status_values is None or start_ticks is None:
            missing_status.append(pid)
            continue
        rss_kib, vmhwm_kib = status_values
        live_threads, runnable_threads = _thread_state_counts(pid)
        allowed_cpus = _allowed_cpus(pid)
        tree_rss_kib += rss_kib
        max_single_rss_kib = max(max_single_rss_kib, rss_kib)
        tree_live_threads += live_threads
        tree_runnable_threads += runnable_threads
        allowed_cpu_union.update(allowed_cpus)
        processes.append(
            {
                "pid": pid,
                "start_ticks": start_ticks,
                "comm": _comm(pid),
                "rss_kib": rss_kib,
                "vmhwm_kib": vmhwm_kib,
                "live_threads": live_threads,
                "runnable_threads": runnable_threads,
                "allowed_cpus": allowed_cpus,
            }
        )

    remaining_pids = set(_cgroup_pids(cgroup_path))
    persistent_status_misses = sorted(pid for pid in missing_status if pid in remaining_pids)
    return {
        "processes": processes,
        "max_single_rss_kib": max_single_rss_kib,
        "tree_rss_kib": tree_rss_kib,
        "tree_live_threads": tree_live_threads,
        "tree_runnable_threads": tree_runnable_threads,
        "allowed_cpu_union": sorted(allowed_cpu_union),
        "persistent_status_misses": persistent_status_misses,
    }


def _scratch_usage(paths: list[pathlib.Path]) -> dict[str, Any]:
    seen: set[tuple[int, int]] = set()
    logical_bytes = 0
    allocated_bytes = 0
    file_count = 0
    race_count = 0
    errors: list[str] = []

    def visit(path: pathlib.Path) -> None:
        nonlocal logical_bytes, allocated_bytes, file_count, race_count
        try:
            info = path.lstat()
        except FileNotFoundError:
            race_count += 1
            return
        except OSError as exc:
            errors.append(f"{path}: {exc}")
            return
        if stat.S_ISLNK(info.st_mode):
            return
        identity = (info.st_dev, info.st_ino)
        if identity in seen:
            return
        seen.add(identity)
        allocated_bytes += info.st_blocks * 512
        if stat.S_ISREG(info.st_mode):
            logical_bytes += info.st_size
            file_count += 1
            return
        if not stat.S_ISDIR(info.st_mode):
            return
        try:
            children = list(path.iterdir())
        except FileNotFoundError:
            race_count += 1
            return
        except OSError as exc:
            errors.append(f"{path}: {exc}")
            return
        for child in children:
            visit(child)

    for root in paths:
        visit(root)
    return {
        "logical_bytes": logical_bytes,
        "allocated_bytes": allocated_bytes,
        "file_count": file_count,
        "race_count": race_count,
        "errors": errors,
    }


def _smaps_rollup(pid: int) -> dict[str, int] | None:
    path = pathlib.Path("/proc") / str(pid) / "smaps_rollup"
    values: dict[str, int] = {}
    try:
        for line in path.read_text(errors="replace").splitlines():
            fields = line.split()
            if len(fields) >= 2 and fields[1].isdigit():
                values[fields[0].rstrip(":")] = int(fields[1])
    except OSError:
        return None
    return values


def _smaps_checkpoint(reason: str, elapsed_s: float, sample: dict[str, Any]) -> dict[str, Any]:
    processes = []
    for process in sample["processes"]:
        rollup = _smaps_rollup(process["pid"])
        if rollup is None:
            continue
        processes.append(
            {
                "pid": process["pid"],
                "start_ticks": process["start_ticks"],
                "rollup_kib": rollup,
            }
        )
    return {
        "reason": reason,
        "elapsed_s": round(elapsed_s, 4),
        "tree_rss_kib": sample["tree_rss_kib"],
        "processes": processes,
    }


def _consume_phase_markers(
    path: pathlib.Path,
    previous_content: bytes,
    buffered: bytes,
    source_line: int,
    elapsed_s: float,
) -> tuple[bytes, bytes, int, list[dict[str, Any]], str | None]:
    try:
        content = path.read_bytes()
    except OSError as exc:
        return previous_content, buffered, source_line, [], f"cannot read phase markers: {exc}"
    if not content.startswith(previous_content):
        return previous_content, buffered, source_line, [], "phase marker stream was truncated or mutated"
    buffered += content[len(previous_content) :]
    previous_content = content
    records: list[dict[str, Any]] = []
    while b"\n" in buffered:
        raw_line, buffered = buffered.split(b"\n", 1)
        source_line += 1
        if not raw_line.strip():
            continue
        try:
            source = json.loads(raw_line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return previous_content, buffered, source_line, records, f"invalid phase marker line {source_line}: {exc}"
        if not isinstance(source, dict):
            return previous_content, buffered, source_line, records, f"phase marker line {source_line} is not an object"
        phase = source.get("phase")
        event = source.get("event")
        if not isinstance(phase, str) or not phase or not isinstance(event, str) or not event:
            return previous_content, buffered, source_line, records, f"phase marker line {source_line} lacks phase/event"
        records.append(
            {
                "source_line": source_line,
                "phase": phase,
                "event": event,
                "detail": source.get("detail"),
                "observed_elapsed_s": round(elapsed_s, 4),
            }
        )
    return previous_content, buffered, source_line, records, None


def _command_sha256(command: list[str]) -> str:
    encoded = b"\0".join(os.fsencode(part) for part in command)
    return hashlib.sha256(encoded).hexdigest()


def _write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def _terminate(proc: subprocess.Popen[Any], cgroup_path: pathlib.Path) -> int:
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            return proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cgroup_kill = cgroup_path / "cgroup.kill"
            if cgroup_kill.exists():
                try:
                    cgroup_kill.write_text("1\n")
                except OSError:
                    pass
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    return proc.wait()


def _launch_in_cgroup(
    command: list[str],
    cgroup_path: pathlib.Path,
    phase_marker_path: pathlib.Path,
) -> subprocess.Popen[Any]:
    wrapper = (
        'printf "%s\\n" "$$" > "$1/cgroup.procs" || exit 125; '
        'shift; exec "$@"'
    )
    environment = os.environ.copy()
    environment["GAMMA_RESOURCE_PHASE_MARKERS"] = str(phase_marker_path.resolve())
    return subprocess.Popen(
        ["/bin/sh", "-c", wrapper, "resource-guard-v3", str(cgroup_path), *command],
        preexec_fn=os.setsid,
        env=environment,
    )


def _wait_for_cgroup_join(
    proc: subprocess.Popen[Any], cgroup_path: pathlib.Path
) -> bool:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if proc.pid in _cgroup_pids(cgroup_path):
            return True
        if proc.poll() is not None:
            return False
        time.sleep(0.01)
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-kib", type=int, default=STRICT_DECIMAL_LIMIT_KIB)
    parser.add_argument("--limit-mode", choices=("max_single", "tree"), default="tree")
    parser.add_argument(
        "--official-decimal-limit-kib",
        type=int,
        default=STRICT_DECIMAL_LIMIT_KIB,
    )
    parser.add_argument("--sample-interval", type=float, default=0.5)
    parser.add_argument("--cgroup-path", type=pathlib.Path, required=True)
    parser.add_argument(
        "--cgroup-memory-max-bytes",
        type=int,
        default=STRICT_DECIMAL_LIMIT_BYTES,
    )
    parser.add_argument("--scratch-path", action="append", type=pathlib.Path, default=[])
    parser.add_argument("--temporary-disk-limit-bytes", type=int, required=True)
    parser.add_argument("--phase-marker-path", type=pathlib.Path, required=True)
    parser.add_argument("--smaps-growth-checkpoint-kib", type=int, default=262_144)
    parser.add_argument("--max-smaps-checkpoints", type=int, default=256)
    parser.add_argument("--max-logical-cpus", type=int, default=1)
    parser.add_argument("--guard-json", type=pathlib.Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument(
        "--phase",
        choices=("compression", "decompression", "diagnostic"),
        default="diagnostic",
    )
    parser.add_argument("--geekbench5-single-core-score", type=float)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command:
        raise SystemExit("missing command after --")
    if args.limit_kib <= 0 or args.official_decimal_limit_kib <= 0:
        raise SystemExit("memory limits must be positive")
    if args.cgroup_memory_max_bytes != args.official_decimal_limit_kib * 1024:
        raise SystemExit("cgroup memory.max must exactly equal the official KiB limit in bytes")
    if args.phase in {"compression", "decompression"} and args.limit_mode != "tree":
        raise SystemExit("prize-facing phases require --limit-mode tree")
    if args.sample_interval < 0.1:
        raise SystemExit("--sample-interval must be at least 0.1")
    if args.temporary_disk_limit_bytes <= 0:
        raise SystemExit("--temporary-disk-limit-bytes must be positive")
    if args.max_logical_cpus <= 0:
        raise SystemExit("--max-logical-cpus must be positive")
    if args.smaps_growth_checkpoint_kib <= 0 or args.max_smaps_checkpoints <= 0:
        raise SystemExit("smaps checkpoint controls must be positive")
    if not args.scratch_path:
        raise SystemExit("at least one --scratch-path is required")
    missing_scratch = [path for path in args.scratch_path if not path.exists()]
    if missing_scratch:
        raise SystemExit(f"scratch paths must exist before launch: {missing_scratch}")
    if not args.phase_marker_path.is_file():
        raise SystemExit("--phase-marker-path must be a pre-created regular file")
    if args.phase_marker_path.stat().st_size != 0:
        raise SystemExit("--phase-marker-path must be empty before launch")
    if args.phase in {"compression", "decompression"} and (
        args.geekbench5_single_core_score is None
        or args.geekbench5_single_core_score <= 0
    ):
        raise SystemExit("prize-facing phases require a positive Geekbench 5 score")

    objective = research_contracts.objective_binding()
    objective_contract = research_contracts.validate_objective()
    wall_time_limit_seconds = (
        objective_contract["resources"]["wallTime"]["maximumSecondsNumerator"]
        / args.geekbench5_single_core_score
        if args.geekbench5_single_core_score is not None
        else None
    )
    cgroup_path = args.cgroup_path.resolve()
    cgroup = _prepare_cgroup(cgroup_path, args.cgroup_memory_max_bytes)
    events_baseline = cgroup.pop("events_baseline")

    started_at = time.monotonic()
    proc = _launch_in_cgroup(command, cgroup_path, args.phase_marker_path)
    cgroup["joined_before_exec"] = _wait_for_cgroup_join(proc, cgroup_path)
    if not cgroup["joined_before_exec"] and proc.poll() is None:
        _terminate(proc, cgroup_path)
        raise SystemExit("candidate did not join the dedicated cgroup before execution")

    sample_interval_seconds = args.sample_interval
    sample_count = 0
    status_miss_count = 0
    affinity_miss_count = 0
    scratch_error_count = 0
    peak_single_rss_kib = 0
    peak_tree_rss_kib = 0
    max_process_vmhwm_kib = 0
    max_cgroup_current_bytes = 0
    max_scratch_logical_bytes = 0
    max_scratch_allocated_bytes = 0
    max_allowed_cpu_count = 0
    max_live_threads = 0
    max_runnable_threads = 0
    peak_process_vmhwm: dict[str, Any] | None = None
    peak_sample: dict[str, Any] | None = None
    peak_tree_sample: dict[str, Any] | None = None
    latest_sample: dict[str, Any] | None = None
    observed_process_hwm: dict[tuple[int, int], int] = {}
    smaps_checkpoints: list[dict[str, Any]] = []
    smaps_truncated = False
    last_smaps_tree_kib = -args.smaps_growth_checkpoint_kib
    marker_content = b""
    marker_buffer = b""
    marker_source_line = 0
    phase_markers: list[dict[str, Any]] = []
    marker_error: str | None = None
    failure: str | None = None
    guard_flags = {
        "rss_guard_exceeded": False,
        "official_decimal_memory_exceeded": False,
        "cgroup_memory_guard_exceeded": False,
        "temporary_disk_guard_exceeded": False,
        "logical_cpu_guard_exceeded": False,
        "wall_time_guard_exceeded": False,
        "phase_marker_invalid": False,
        "measurement_incomplete": False,
    }
    final_events = events_baseline
    final_cgroup_peak_bytes = _read_int(cgroup_path / "memory.peak")

    def measurements(final: bool) -> dict[str, bool]:
        return {
            "process_tree_rss_complete": sample_count > 0 and status_miss_count == 0,
            "per_process_vmhwm_sampled": bool(observed_process_hwm) and status_miss_count == 0,
            "cgroup_v2_complete": cgroup["joined_before_exec"],
            "scratch_logical_and_allocated_complete": sample_count > 0 and scratch_error_count == 0,
            "affinity_complete": sample_count > 0 and affinity_miss_count == 0,
            "smaps_rollup_complete": bool(smaps_checkpoints) and not smaps_truncated,
            "phase_markers_complete": final and marker_error is None and not marker_buffer and bool(phase_markers),
        }

    def make_payload(status: str, returncode: int | None, elapsed_s: float) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "objective": objective,
            "label": args.label,
            "phase": args.phase,
            "command": command,
            "command_sha256": _command_sha256(command),
            "sample_interval_seconds": sample_interval_seconds,
            "geekbench5_single_core_score": args.geekbench5_single_core_score,
            "wall_time_limit_seconds": wall_time_limit_seconds,
            "limit_kib": args.limit_kib,
            "limit_mode": args.limit_mode,
            "official_decimal_limit_kib": args.official_decimal_limit_kib,
            "cgroup": cgroup,
            "scratch_paths": [str(path) for path in args.scratch_path],
            "temporary_disk_limit_bytes": args.temporary_disk_limit_bytes,
            "phase_marker_path": str(args.phase_marker_path),
            "max_logical_cpus": args.max_logical_cpus,
            "measurements": measurements(status != "running"),
            "peaks": {
                "max_sampled_single_rss_kib": peak_single_rss_kib,
                "max_sampled_tree_rss_kib": peak_tree_rss_kib,
                "max_observed_process_vmhwm_kib": max_process_vmhwm_kib,
                "max_sampled_cgroup_current_bytes": max_cgroup_current_bytes,
                "cgroup_memory_peak_bytes": final_cgroup_peak_bytes,
                "max_sampled_scratch_logical_bytes": max_scratch_logical_bytes,
                "max_sampled_scratch_allocated_bytes": max_scratch_allocated_bytes,
                "max_sampled_allowed_cpu_count": max_allowed_cpu_count,
                "max_sampled_tree_live_threads": max_live_threads,
                "max_sampled_tree_runnable_threads": max_runnable_threads,
            },
            "cgroup_events": {
                "baseline": events_baseline,
                "final": final_events,
                "delta": _event_delta(events_baseline, final_events),
            },
            "peak_process_vmhwm": peak_process_vmhwm,
            "peak_sample": peak_sample,
            "peak_tree_sample": peak_tree_sample,
            "latest_sample": latest_sample,
            "smaps_rollup_checkpoints": smaps_checkpoints,
            "phase_markers": phase_markers,
            "sample_count": sample_count,
            "guards": guard_flags,
            "returncode": returncode,
            "status": status,
            "elapsed_s": round(elapsed_s, 4),
            **({"failure": failure} if failure is not None else {}),
        }

    try:
        while True:
            elapsed_s = time.monotonic() - started_at
            returncode = proc.poll()
            process_sample = _sample_processes(cgroup_path)
            scratch = _scratch_usage(args.scratch_path)
            cgroup_current_bytes = _read_int(cgroup_path / "memory.current")
            final_cgroup_peak_bytes = _read_int(cgroup_path / "memory.peak")
            final_events = _read_events(cgroup_path / "memory.events")
            sample_count += 1
            status_miss_count += len(process_sample["persistent_status_misses"])
            scratch_error_count += len(scratch["errors"])
            affinity_miss_count += sum(
                1 for process in process_sample["processes"] if not process["allowed_cpus"]
            )
            sample = {
                **process_sample,
                "elapsed_s": round(elapsed_s, 4),
                "cgroup_current_bytes": cgroup_current_bytes,
                "scratch_logical_bytes": scratch["logical_bytes"],
                "scratch_allocated_bytes": scratch["allocated_bytes"],
                "scratch_file_count": scratch["file_count"],
                "scratch_race_count": scratch["race_count"],
            }
            latest_sample = sample

            if sample["max_single_rss_kib"] > peak_single_rss_kib:
                peak_single_rss_kib = sample["max_single_rss_kib"]
                peak_sample = sample
            if sample["tree_rss_kib"] > peak_tree_rss_kib:
                peak_tree_rss_kib = sample["tree_rss_kib"]
                peak_tree_sample = sample
            max_cgroup_current_bytes = max(max_cgroup_current_bytes, cgroup_current_bytes)
            max_scratch_logical_bytes = max(max_scratch_logical_bytes, scratch["logical_bytes"])
            max_scratch_allocated_bytes = max(max_scratch_allocated_bytes, scratch["allocated_bytes"])
            max_allowed_cpu_count = max(max_allowed_cpu_count, len(sample["allowed_cpu_union"]))
            max_live_threads = max(max_live_threads, sample["tree_live_threads"])
            max_runnable_threads = max(max_runnable_threads, sample["tree_runnable_threads"])
            for process in sample["processes"]:
                key = (process["pid"], process["start_ticks"])
                observed_process_hwm[key] = max(
                    observed_process_hwm.get(key, 0), process["vmhwm_kib"]
                )
                if process["vmhwm_kib"] > max_process_vmhwm_kib:
                    max_process_vmhwm_kib = process["vmhwm_kib"]
                    peak_process_vmhwm = {
                        "pid": process["pid"],
                        "start_ticks": process["start_ticks"],
                        "comm": process["comm"],
                        "vmhwm_kib": process["vmhwm_kib"],
                        "observed_elapsed_s": round(elapsed_s, 4),
                    }

            (
                marker_content,
                marker_buffer,
                marker_source_line,
                new_markers,
                marker_error,
            ) = _consume_phase_markers(
                args.phase_marker_path,
                marker_content,
                marker_buffer,
                marker_source_line,
                elapsed_s,
            )
            phase_markers.extend(new_markers)

            checkpoint_reasons: list[str] = []
            if sample_count == 1:
                checkpoint_reasons.append("initial")
            if new_markers:
                checkpoint_reasons.append("phase_marker")
            if sample["tree_rss_kib"] >= last_smaps_tree_kib + args.smaps_growth_checkpoint_kib:
                checkpoint_reasons.append("rss_growth")
            if returncode is not None:
                checkpoint_reasons.append("terminal")
            if checkpoint_reasons:
                if len(smaps_checkpoints) < args.max_smaps_checkpoints:
                    smaps_checkpoints.append(
                        _smaps_checkpoint("+".join(checkpoint_reasons), elapsed_s, sample)
                    )
                    last_smaps_tree_kib = max(last_smaps_tree_kib, sample["tree_rss_kib"])
                else:
                    smaps_truncated = True

            measured_kib = (
                sample["tree_rss_kib"]
                if args.limit_mode == "tree"
                else sample["max_single_rss_kib"]
            )
            events_delta = _event_delta(events_baseline, final_events)
            guard_flags["rss_guard_exceeded"] = measured_kib >= args.limit_kib
            guard_flags["official_decimal_memory_exceeded"] = (
                sample["tree_rss_kib"] >= args.official_decimal_limit_kib
                or max_process_vmhwm_kib >= args.official_decimal_limit_kib
            )
            guard_flags["cgroup_memory_guard_exceeded"] = (
                final_cgroup_peak_bytes >= args.cgroup_memory_max_bytes
                or events_delta.get("max", 0) > 0
                or events_delta.get("oom", 0) > 0
                or events_delta.get("oom_kill", 0) > 0
            )
            guard_flags["temporary_disk_guard_exceeded"] = (
                max(scratch["logical_bytes"], scratch["allocated_bytes"])
                >= args.temporary_disk_limit_bytes
            )
            guard_flags["logical_cpu_guard_exceeded"] = (
                len(sample["allowed_cpu_union"]) > args.max_logical_cpus
            )
            guard_flags["wall_time_guard_exceeded"] = (
                wall_time_limit_seconds is not None and elapsed_s >= wall_time_limit_seconds
            )
            guard_flags["phase_marker_invalid"] = marker_error is not None
            guard_flags["measurement_incomplete"] = bool(scratch["errors"])

            if guard_flags["cgroup_memory_guard_exceeded"]:
                failure = "cgroup_v2_memory_limit_reached_or_oom_event"
            elif guard_flags["official_decimal_memory_exceeded"]:
                failure = "official_decimal_memory_limit_reached"
            elif guard_flags["rss_guard_exceeded"]:
                failure = "configured_rss_limit_reached"
            elif guard_flags["temporary_disk_guard_exceeded"]:
                failure = "temporary_disk_limit_reached"
            elif guard_flags["logical_cpu_guard_exceeded"]:
                failure = "logical_cpu_limit_exceeded"
            elif guard_flags["wall_time_guard_exceeded"]:
                failure = "objective_wall_time_limit_reached"
            elif guard_flags["phase_marker_invalid"]:
                failure = marker_error
            elif guard_flags["measurement_incomplete"]:
                failure = "required_resource_measurement_failed"

            _write_json(args.guard_json, make_payload("running", None, elapsed_s))
            if failure is not None:
                _terminate(proc, cgroup_path)
                break
            if returncode is not None:
                break
            time.sleep(sample_interval_seconds)
    finally:
        if proc.poll() is None:
            _terminate(proc, cgroup_path)

    returncode = proc.poll()
    final_elapsed_s = time.monotonic() - started_at
    final_events = _read_events(cgroup_path / "memory.events")
    final_cgroup_peak_bytes = _read_int(cgroup_path / "memory.peak")
    if marker_buffer.strip() and failure is None:
        failure = "phase_marker_stream_ended_with_incomplete_line"
        guard_flags["phase_marker_invalid"] = True
    final_measurements = measurements(True)
    if failure is None and not all(final_measurements.values()):
        failure = "required_resource_measurement_incomplete"
        guard_flags["measurement_incomplete"] = True

    if failure is None:
        status = "complete"
    elif guard_flags["cgroup_memory_guard_exceeded"]:
        status = "cgroup_memory_guard_exceeded"
    elif guard_flags["official_decimal_memory_exceeded"]:
        status = "official_decimal_memory_guard_exceeded"
    elif guard_flags["rss_guard_exceeded"]:
        status = "rss_guard_exceeded"
    elif guard_flags["temporary_disk_guard_exceeded"]:
        status = "temporary_disk_guard_exceeded"
    elif guard_flags["logical_cpu_guard_exceeded"]:
        status = "logical_cpu_guard_exceeded"
    elif guard_flags["wall_time_guard_exceeded"]:
        status = "wall_time_guard_exceeded"
    elif guard_flags["phase_marker_invalid"]:
        status = "phase_marker_invalid"
    else:
        status = "measurement_incomplete"

    payload = make_payload(status, returncode, final_elapsed_s)
    _write_json(args.guard_json, payload)
    print(json.dumps({"resource_guard": payload}, indent=2, sort_keys=True))
    if failure is not None:
        return 75
    return int(returncode or 0)


if __name__ == "__main__":
    sys.exit(main())
