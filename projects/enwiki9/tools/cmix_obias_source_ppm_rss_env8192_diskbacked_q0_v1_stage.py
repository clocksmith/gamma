#!/usr/bin/env python3
"""One guarded encode or decode stage for the disk-backed PPM-RSS envelope."""

from __future__ import annotations

import argparse
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
                    stat_value = proc_stat(pid)
                    io_value = proc_io(pid)
                    if stat_value is None:
                        continue
                    _, minor_faults, major_faults = stat_value
                    if io_value is None:
                        observation_errors.append(f"missing /proc/{pid}/io")
                        continue
                    try:
                        start_ticks = int(
                            (Path("/proc") / str(pid) / "stat")
                            .read_text(encoding="ascii")
                            .rsplit(")", 1)[1]
                            .split()[19]
                        )
                    except (OSError, IndexError, ValueError):
                        continue
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
    return {
        "argv": command,
        "returncode": return_code,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "sample_count": sample_count,
        "processes": rows,
        "process_tree_totals": totals,
        "measurement_complete": bool(rows) and not observation_errors,
        "measurement_errors": sorted(set(observation_errors)),
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("encode", "decode"), required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--input-bytes", type=int)
    parser.add_argument("--input-sha256")
    parser.add_argument("--package", type=Path)
    parser.add_argument("--package-bytes", type=int)
    parser.add_argument("--package-sha256")
    parser.add_argument("--head", type=Path)
    parser.add_argument("--head-bytes", type=int)
    parser.add_argument("--head-sha256")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--archive-bytes", type=int)
    parser.add_argument("--archive-sha256")
    parser.add_argument("--ppm-rss-mb", choices=("default", "8192"), required=True)
    args = parser.parse_args()

    work_root = args.work_root.resolve()
    result_root = args.result_root.resolve(strict=True)
    receipt = args.receipt.resolve()
    if work_root.exists() or work_root.is_symlink():
        raise RuntimeError("stage work root must be absent")
    if result_root == work_root or result_root in work_root.parents or work_root in result_root.parents:
        raise RuntimeError("stage work and result roots must be disjoint")
    if receipt.parent != result_root or receipt.exists() or receipt.is_symlink():
        raise RuntimeError("stage receipt must be an absent direct child of result root")
    work_root.mkdir(mode=0o700)
    phase_name = f"q0_{args.mode}_stage"
    append_phase(phase_name, "start")

    if args.mode == "encode":
        required = (
            args.input,
            args.input_bytes,
            args.input_sha256,
            args.package,
            args.package_bytes,
            args.package_sha256,
            args.head,
            args.head_bytes,
            args.head_sha256,
        )
        if any(value is None for value in required):
            raise RuntimeError("encode stage identity arguments are incomplete")
        input_path = verify(args.input, args.input_bytes, args.input_sha256, "input")
        package_path = verify(args.package, args.package_bytes, args.package_sha256, "package")
        head_path = verify(args.head, args.head_bytes, args.head_sha256, "head")
        local_package = work_root / "cmix"
        local_head = work_root / "head.blob"
        copy_new(package_path, local_package, 0o700)
        copy_new(head_path, local_head)
        command = [str(local_package), "-e", str(input_path), "out.cmix"]
        environment = {
            "PATH": "/usr/bin:/bin",
            "KH_BITLSTM32": str(local_head),
            "GAMMA_RESOURCE_PHASE_MARKERS": os.environ["GAMMA_RESOURCE_PHASE_MARKERS"],
        }
        if args.ppm_rss_mb == "8192":
            environment["CMIX_PPM_RSS_MB"] = "8192"
        execution = run_observed(
            command,
            work_root,
            environment,
            result_root / "codec.stdout",
            result_root / "codec.stderr",
        )
        if execution["returncode"] != 0 or not execution["measurement_complete"]:
            raise RuntimeError("encode process or process-tree IO/fault telemetry failed")
        payload = work_root / "out.cmix"
        archive = work_root / "archive9"
        if not payload.is_file() or not archive.is_file():
            raise RuntimeError("encode did not create payload and archive")
        copy_new(payload, result_root / "out.cmix")
        copy_new(archive, result_root / "archive9", 0o700)
        outputs = {
            "payload": artifact(result_root / "out.cmix"),
            "archive": artifact(result_root / "archive9"),
        }
        inputs = {
            "population": artifact(input_path),
            "package": artifact(package_path),
            "head": artifact(head_path),
        }
    else:
        required = (args.archive, args.archive_bytes, args.archive_sha256)
        if any(value is None for value in required):
            raise RuntimeError("decode stage identity arguments are incomplete")
        archive_path = verify(args.archive, args.archive_bytes, args.archive_sha256, "archive")
        local_archive = work_root / "archive9"
        copy_new(archive_path, local_archive, 0o700)
        command = [str(local_archive)]
        execution = run_observed(
            command,
            work_root,
            {
                "PATH": "/usr/bin:/bin",
                "GAMMA_RESOURCE_PHASE_MARKERS": os.environ["GAMMA_RESOURCE_PHASE_MARKERS"],
                **({"CMIX_PPM_RSS_MB": "8192"} if args.ppm_rss_mb == "8192" else {}),
            },
            result_root / "codec.stdout",
            result_root / "codec.stderr",
        )
        if execution["returncode"] != 0 or not execution["measurement_complete"]:
            raise RuntimeError("decode process or process-tree IO/fault telemetry failed")
        restored_candidates = [
            path
            for path in (work_root / "enwik9", work_root / "enwik9_uncompressed")
            if path.is_file()
        ]
        if len(restored_candidates) != 1:
            raise RuntimeError("decode did not create exactly one recognized restored output")
        copy_new(restored_candidates[0], result_root / "restored.bin")
        outputs = {"restored": artifact(result_root / "restored.bin")}
        inputs = {"archive": artifact(archive_path)}

    append_phase(phase_name, "end")
    value = {
        "schema": SCHEMA,
        "mode": args.mode,
        "ppm_rss_environment": (
            {} if args.ppm_rss_mb == "default" else {"CMIX_PPM_RSS_MB": "8192"}
        ),
        "inputs": inputs,
        "outputs": outputs,
        "execution": execution,
        "phase_marker_path": os.environ["GAMMA_RESOURCE_PHASE_MARKERS"],
        "stage_pass": True,
    }
    write_json_new(receipt, value)
    print(json.dumps(value, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
