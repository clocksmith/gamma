#!/usr/bin/env python3
"""Identity-bracketed sampled IO/fault telemetry for the opening-1M envelope."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
from typing import Any


SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-diskbacked-stage.v1"
CHUNK = 8 << 20


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if not resolved.is_file() or resolved.is_symlink():
        raise RuntimeError(f"artifact is not a regular file: {resolved}")
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def verify(path: Path, expected_bytes: int, expected_sha256: str, label: str) -> Path:
    resolved = path.resolve(strict=True)
    observed = artifact(resolved)
    if observed["bytes"] != expected_bytes or observed["sha256"] != expected_sha256:
        raise RuntimeError(f"{label} identity mismatch")
    return resolved


def write_new(path: Path, raw: bytes, mode: int = 0o600) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        mode,
    )
    try:
        cursor = 0
        while cursor < len(raw):
            written = os.write(descriptor, raw[cursor:])
            if written <= 0:
                raise OSError(f"short write: {path}")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_json_new(path: Path, value: dict[str, Any]) -> None:
    write_new(
        path,
        json.dumps(value, indent=2, sort_keys=True).encode("ascii") + b"\n",
    )


def copy_new(source: Path, destination: Path, mode: int = 0o600) -> None:
    source_descriptor = os.open(source, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        destination_descriptor = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            mode,
        )
        try:
            while chunk := os.read(source_descriptor, CHUNK):
                cursor = 0
                while cursor < len(chunk):
                    written = os.write(destination_descriptor, chunk[cursor:])
                    if written <= 0:
                        raise OSError(f"short write: {destination}")
                    cursor += written
            os.fsync(destination_descriptor)
        finally:
            os.close(destination_descriptor)
    finally:
        os.close(source_descriptor)


def append_phase(phase: str, event: str) -> None:
    marker = os.environ.get("GAMMA_RESOURCE_PHASE_MARKERS")
    if not marker:
        raise RuntimeError("GAMMA_RESOURCE_PHASE_MARKERS is required")
    raw = json.dumps(
        {"event": event, "phase": phase}, sort_keys=True, separators=(",", ":")
    ).encode("ascii") + b"\n"
    descriptor = os.open(
        marker,
        os.O_WRONLY | os.O_APPEND | os.O_CLOEXEC | os.O_NOFOLLOW,
    )
    try:
        if os.write(descriptor, raw) != len(raw):
            raise OSError("short phase-marker write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def proc_stat(pid: int) -> tuple[int, int, int] | None:
    try:
        suffix = (Path("/proc") / str(pid) / "stat").read_text(encoding="ascii").rsplit(")", 1)[1]
        fields = suffix.split()
        return int(fields[1]), int(fields[7]), int(fields[9])
    except (OSError, IndexError, ValueError):
        return None


def descendants(root_pid: int) -> list[int]:
    parents: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        value = proc_stat(int(entry.name))
        if value is not None:
            parents[int(entry.name)] = value[0]
    selected = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, parent in parents.items():
            if parent in selected and pid not in selected:
                selected.add(pid)
                changed = True
    return sorted(selected)


def proc_io(pid: int) -> tuple[int, int] | None:
    values: dict[str, int] = {}
    try:
        for line in (Path("/proc") / str(pid) / "io").read_text(encoding="ascii").splitlines():
            name, raw = line.split(":", 1)
            if name in {"read_bytes", "write_bytes"}:
                values[name] = int(raw.strip())
    except (OSError, ValueError):
        return None
    if set(values) != {"read_bytes", "write_bytes"}:
        return None
    return values["read_bytes"], values["write_bytes"]


def ppm_smaps(pid: int) -> dict[str, int] | None:
    """Aggregate the file-backed ppm.temp mappings without faulting their pages."""
    keys = ("Size", "Rss", "Pss", "Referenced", "Shared_Dirty", "Private_Dirty")
    totals = {key: 0 for key in keys}
    selected = False
    active = False
    try:
        for line in (Path("/proc") / str(pid) / "smaps").read_text(errors="replace").splitlines():
            if line and line[0].isdigit() and "-" in line.split(maxsplit=1)[0]:
                active = line.endswith("/ppm.temp") or line.endswith(" ppm.temp")
                selected = selected or active
                continue
            if not active or ":" not in line:
                continue
            name, raw = line.split(":", 1)
            if name in totals:
                fields = raw.split()
                if fields and fields[0].isdigit():
                    totals[name] += int(fields[0])
    except OSError:
        return None
    return totals if selected else None


def terminate(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()



def read_identity(pid: int) -> dict[str, Any]:
    try:
        fields = (Path("/proc") / str(pid) / "stat").read_text(encoding="ascii").rsplit(")", 1)[1].split()
        return {"ok": True, "pid": pid, "state": fields[0], "start_ticks": int(fields[19]),
                "minor_faults": int(fields[7]), "major_faults": int(fields[9])}
    except OSError as exc:
        return {"ok": False, "pid": pid, "errno": exc.errno, "error": type(exc).__name__}
    except (IndexError, ValueError, UnicodeError) as exc:
        return {"ok": False, "pid": pid, "errno": None, "error": "malformed_stat:" + type(exc).__name__}


def read_io(pid: int) -> dict[str, Any]:
    try:
        values = {}
        for line in (Path("/proc") / str(pid) / "io").read_text(encoding="ascii").splitlines():
            name, raw = line.split(":", 1)
            if name in {"read_bytes", "write_bytes"}:
                values[name] = int(raw.strip())
        if set(values) != {"read_bytes", "write_bytes"} or any(v < 0 for v in values.values()):
            raise ValueError("missing_or_negative_counter")
        return {"ok": True, **values}
    except OSError as exc:
        return {"ok": False, "errno": exc.errno, "error": type(exc).__name__}
    except (ValueError, UnicodeError) as exc:
        return {"ok": False, "errno": None, "error": "malformed_io:" + type(exc).__name__}


def classify_observation(before: dict[str, Any], io: dict[str, Any], after: dict[str, Any]) -> str:
    """Never accept missing telemetry for a live, unreadable, or reused identity."""
    missing = {errno.ENOENT, errno.ESRCH}
    before_gone = not before.get("ok") and before.get("errno") in missing
    after_gone = not after.get("ok") and after.get("errno") in missing
    if not before.get("ok"):
        return "exit_race" if before_gone and after_gone else "invalid_identity"
    if after.get("ok") and (after.get("pid"), after.get("start_ticks")) != (before.get("pid"), before.get("start_ticks")):
        return "identity_reused"
    if not io.get("ok"):
        if io.get("errno") not in missing:
            return "io_unreadable"
        if after_gone or (after.get("ok") and after.get("state") in {"Z", "X", "x"}):
            return "exit_race"
        return "live_io_missing" if after.get("ok") else "invalid_identity"
    if after_gone:
        return "exit_race"
    if not after.get("ok"):
        return "invalid_identity"
    return "sample"


def observe_identity_io(pid: int) -> dict[str, Any]:
    before = read_identity(pid)
    io = read_io(pid) if before.get("ok") else {"ok": False, "errno": None, "error": "identity_unavailable"}
    after = read_identity(pid)
    return {"pid": pid, "before": before, "io": io, "after": after,
            "classification": classify_observation(before, io, after)}


def lifecycle_validation() -> dict[str, Any]:
    live = {"ok": True, "pid": 7, "start_ticks": 11, "state": "R", "minor_faults": 1, "major_faults": 0}
    missing = {"ok": False, "errno": errno.ENOENT}
    denied = {"ok": False, "errno": errno.EACCES}
    valid_io = {"ok": True, "read_bytes": 0, "write_bytes": 0}
    cases = [
        ("stable", live, valid_io, live, "sample"),
        ("vanished_during_io", live, missing, missing, "exit_race"),
        ("vanished_after_io", live, valid_io, missing, "exit_race"),
        ("enumerated_then_vanished", missing, missing, missing, "exit_race"),
        ("same_identity_zombie", live, missing, {**live, "state": "Z"}, "exit_race"),
        ("missing_io_still_live", live, missing, live, "live_io_missing"),
        ("reused_missing_io", live, missing, {**live, "start_ticks": 12}, "identity_reused"),
        ("reused_successful_io", live, valid_io, {**live, "start_ticks": 12}, "identity_reused"),
        ("permission_denied_then_exit", live, denied, missing, "io_unreadable"),
        ("permission_denied_live", live, denied, live, "io_unreadable"),
        ("malformed_io_then_exit", live, {"ok": False, "errno": None}, missing, "io_unreadable"),
        ("unreadable_after_identity", live, missing, denied, "invalid_identity"),
        ("unreadable_before_identity", denied, missing, missing, "invalid_identity"),
    ]
    rows = [{"case": name, "observed": classify_observation(a,b,c), "expected": expected} for name,a,b,c,expected in cases]
    passed = all(row["observed"] == row["expected"] for row in rows)
    if not passed:
        raise RuntimeError("deterministic lifecycle validation failed")
    return {"schema": "gamma.enwiki9.cmix-v14-lifecycle-validation.v1", "validation_only": True,
            "corpus_accessed": False, "processes_launched": False, "passed": passed, "cases": rows}


def run_observed(
    command: list[str],
    cwd: Path,
    environment: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    observations: dict[tuple[int, int], dict[str, int]] = {}
    sample_count = 0
    observation_errors: list[str] = []
    exit_races: list[dict[str, Any]] = []
    diagnostic_errors: list[dict[str, Any]] = []
    ppm_observation_count = 0
    ppm_min_rss_kib: int | None = None
    ppm_max_rss_kib = 0
    ppm_max_referenced_kib = 0
    ppm_max_dirty_kib = 0
    ppm_previous_rss: dict[tuple[int, int], int] = {}
    ppm_residency_events: list[dict[str, Any]] = []
    ppm_events_truncated = False
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=environment,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        try:
            while True:
                for pid in descendants(process.pid):
                    observation = observe_identity_io(pid)
                    classification = observation["classification"]
                    if classification == "exit_race":
                        exit_races.append(observation)
                        continue
                    if classification != "sample":
                        observation_errors.append(f"{classification}:pid={pid}")
                        diagnostic_errors.append(observation)
                        continue
                    before = observation["before"]
                    start_ticks = before["start_ticks"]
                    minor_faults, major_faults = before["minor_faults"], before["major_faults"]
                    io_value = (observation["io"]["read_bytes"], observation["io"]["write_bytes"])
                    key = (pid, start_ticks)
                    current = observations.setdefault(
                        key,
                        {
                            "minor_faults": 0,
                            "major_faults": 0,
                            "read_bytes": 0,
                            "write_bytes": 0,
                        },
                    )
                    current["minor_faults"] = max(current["minor_faults"], minor_faults)
                    current["major_faults"] = max(current["major_faults"], major_faults)
                    current["read_bytes"] = max(current["read_bytes"], io_value[0])
                    current["write_bytes"] = max(current["write_bytes"], io_value[1])
                    ppm = ppm_smaps(pid) if sample_count % 20 == 0 else None
                    if ppm is not None:
                        ppm_observation_count += 1
                        previous_rss = ppm_previous_rss.get(key)
                        event_type: str | None = None
                        if previous_rss is not None and previous_rss - ppm["Rss"] >= 32_768:
                            event_type = "observed_rss_drop"
                        elif previous_rss is not None and ppm["Rss"] - previous_rss >= 32_768:
                            event_type = "observed_refault_growth"
                        if event_type is not None:
                            if len(ppm_residency_events) < 4096:
                                ppm_residency_events.append(
                                    {
                                        "event": event_type,
                                        "observed_elapsed_seconds": round(
                                            time.monotonic() - started, 6
                                        ),
                                        "pid": pid,
                                        "start_ticks": start_ticks,
                                        "previous_rss_kib": previous_rss,
                                        "rss_kib": ppm["Rss"],
                                        "delta_rss_kib": ppm["Rss"] - previous_rss,
                                    }
                                )
                            else:
                                ppm_events_truncated = True
                        ppm_previous_rss[key] = ppm["Rss"]
                        ppm_min_rss_kib = (
                            ppm["Rss"]
                            if ppm_min_rss_kib is None
                            else min(ppm_min_rss_kib, ppm["Rss"])
                        )
                        ppm_max_rss_kib = max(ppm_max_rss_kib, ppm["Rss"])
                        ppm_max_referenced_kib = max(
                            ppm_max_referenced_kib, ppm["Referenced"]
                        )
                        ppm_max_dirty_kib = max(
                            ppm_max_dirty_kib,
                            ppm["Shared_Dirty"] + ppm["Private_Dirty"],
                        )
                sample_count += 1
                if process.poll() is not None:
                    break
                time.sleep(0.25)
        except Exception as exc:
            observation_errors.append(f"observer_exception:{type(exc).__name__}:{exc}")
        finally:
            terminate(process)
        return_code = process.wait()
    rows = [
        {"pid": pid, "start_ticks": ticks, **values}
        for (pid, ticks), values in sorted(observations.items())
    ]
    totals = {
        name: sum(row[name] for row in rows)
        for name in ("minor_faults", "major_faults", "read_bytes", "write_bytes")
    }
    raw_io_counter_sum = {name: totals[name] for name in ("read_bytes", "write_bytes")}
    totals["read_bytes"] = None
    totals["write_bytes"] = None
    return {
        "argv": command,
        "returncode": return_code,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "sample_count": sample_count,
        "processes": rows,
        "process_tree_totals": totals,
        "raw_sum_of_sampled_process_io_counters": raw_io_counter_sum,
        "raw_io_sum_authority": "None: per-process IO may include waited-for children, so this sum can overlap and is not unique-tree IO or a physical-IO bound.",
        "measurement_complete": bool(rows) and not observation_errors,
        "measurement_errors": sorted(set(observation_errors)),
        "identity_errors": diagnostic_errors,
        "proven_exit_races": exit_races,
        "final_process_accounting_complete": False,
        "measurement_scope": "Identity-stable per-process sampled counters only. Unique-tree IO totals are unavailable because parent IO can include waited-for children. Fault totals are sampled and not exhaustive child coverage or final lifetime totals.",
        "ppm_residency": {
            "observation_count": ppm_observation_count,
            "minimum_rss_kib": ppm_min_rss_kib,
            "maximum_rss_kib": ppm_max_rss_kib,
            "maximum_referenced_kib": ppm_max_referenced_kib,
            "maximum_dirty_kib": ppm_max_dirty_kib,
            "event_threshold_kib": 32_768,
            "observed_drop_count": sum(
                event["event"] == "observed_rss_drop"
                for event in ppm_residency_events
            ),
            "observed_refault_growth_count": sum(
                event["event"] == "observed_refault_growth"
                for event in ppm_residency_events
            ),
            "events": ppm_residency_events,
            "events_truncated": ppm_events_truncated,
            "claim_boundary": (
                "Observed mapping-RSS drops and regrowth plus process-tree faults and IO "
                "quantify purge/refault effects; they are not a direct madvise call count."
            ),
        },
        "stdout": artifact(stdout_path),
        "stderr": artifact(stderr_path),
    }



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation-only", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(lifecycle_validation(), indent=2, sort_keys=True))
