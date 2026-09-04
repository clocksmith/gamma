#!/usr/bin/env python3
"""Produce guarded current-host Geekbench 5 Tryout calibration evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import stat
import subprocess
import sys
import time
from typing import Any

import managed_exclusive_lease
import managed_exclusive_lease_verify


PROJECT = Path(__file__).resolve().parents[1]
PLAN_SCHEMA = "gamma.enwiki9.geekbench5-tryout-calibration-plan.v1"
RECEIPT_SCHEMA = "gamma.enwiki9.geekbench5-tryout-calibration.v1"
CANDIDATE = "geekbench5_5_5_1_tryout_calibration_q0_v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(16 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


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
    path = regular_file(path, "output artifact")
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


def proc_identity(pid: int) -> tuple[int, int]:
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    close = raw.rfind(")")
    fields = raw[close + 2 :].split()
    if close < 0 or len(fields) <= 19:
        raise RuntimeError(f"malformed process stat for {pid}")
    return int(fields[1]), int(fields[19])


def process_ancestry() -> set[int]:
    result: set[int] = set()
    cursor = os.getpid()
    while cursor > 1 and cursor not in result:
        result.add(cursor)
        try:
            cursor, _ = proc_identity(cursor)
        except (OSError, RuntimeError):
            break
    return result


def conflicting_processes(patterns: list[str]) -> list[dict[str, Any]]:
    excluded = process_ancestry()
    rows: list[dict[str, Any]] = []
    for entry in sorted(Path("/proc").iterdir(), key=lambda path: path.name):
        if not entry.name.isdigit() or int(entry.name) in excluded:
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            raw = (entry / "cmdline").read_bytes()
            command = " ".join(os.fsdecode(token) for token in raw.rstrip(b"\0").split(b"\0"))
            comm = (entry / "comm").read_text(encoding="utf-8").strip()
        except OSError:
            continue
        haystack = f"{comm}\n{command}"
        matched = [pattern for pattern in patterns if pattern in haystack]
        if matched:
            rows.append({"pid": int(entry.name), "comm": comm, "matched": matched})
    return rows


def cpu_counters(cpu: int) -> tuple[int, int]:
    prefix = f"cpu{cpu} "
    for line in Path("/proc/stat").read_text(encoding="ascii").splitlines():
        if line.startswith(prefix):
            values = [int(value) for value in line.split()[1:]]
            total = sum(values)
            idle = values[3] + (values[4] if len(values) > 4 else 0)
            return total, idle
    raise RuntimeError(f"CPU {cpu} counters are absent")


def quiet_cpu_sample(cpus: list[int], intervals: int, interval_seconds: float) -> dict[str, Any]:
    before = {cpu: cpu_counters(cpu) for cpu in cpus}
    windows: list[dict[str, Any]] = []
    for _ in range(intervals):
        time.sleep(interval_seconds)
        after = {cpu: cpu_counters(cpu) for cpu in cpus}
        row: dict[str, Any] = {}
        for cpu in cpus:
            total = after[cpu][0] - before[cpu][0]
            idle = after[cpu][1] - before[cpu][1]
            row[str(cpu)] = 1.0 if total <= 0 else (total - idle) / total
        windows.append(row)
        before = after
    averages = {
        str(cpu): sum(row[str(cpu)] for row in windows) / len(windows) for cpu in cpus
    }
    return {"cpus": cpus, "windows": windows, "average_busy_fraction": averages}


def cgroup_events(path: Path) -> dict[str, int]:
    values: dict[str, int] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        key, value = line.split()
        values[key] = int(value)
    return values


def directory_bytes(path: Path) -> int:
    return sum(entry.stat().st_size for entry in path.rglob("*") if entry.is_file())


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


def worker_argv(plan_path: Path, plan: dict[str, Any], worker: Path, python: Path) -> list[str]:
    return [
        str(python),
        str(worker),
        "--plan",
        str(plan_path),
        "--result-root",
        plan["paths"]["result_root"],
        "--scratch-root",
        plan["paths"]["scratch_root"],
    ]


def dynamic_preflight(plan: dict[str, Any]) -> dict[str, Any]:
    paths = plan["paths"]
    blockers: list[str] = []
    occupied: list[str] = []
    for key in ("result_root", "scratch_root", "cgroup_path", "lease_path", "lease_lock_path"):
        path = Path(paths[key])
        if path.exists() or path.is_symlink():
            occupied.append(key)
    if occupied:
        blockers.append(f"occupied namespaces: {occupied}")
    running = sorted(
        str(path) for path in (PROJECT / "operations/adaptive/running").glob("*.json")
    )
    if running:
        blockers.append("adaptive running directory is not empty")
    conflicts = conflicting_processes(plan["admission"]["forbidden_process_patterns"])
    if conflicts:
        blockers.append("conflicting compression or benchmark process is live")
    cpu = int(plan["benchmark"]["selected_logical_cpu"])
    allowed = sorted(os.sched_getaffinity(0))
    if cpu not in allowed:
        blockers.append("selected logical CPU is unavailable")
    parent = Path(paths["cgroup_parent"])
    parent_stat = parent.stat()
    controllers = sorted((parent / "cgroup.controllers").read_text(encoding="ascii").split())
    direct_procs = (parent / "cgroup.procs").read_text(encoding="ascii").split()
    expected_parent = plan["cgroup_parent_identity"]
    if (
        parent_stat.st_ino != expected_parent["inode"]
        or parent_stat.st_uid != expected_parent["uid"]
        or parent_stat.st_gid != expected_parent["gid"]
        or not set(plan["admission"]["required_cgroup_controllers"]).issubset(controllers)
        or direct_procs
        or not os.access(parent, os.W_OK)
    ):
        blockers.append("delegated cgroup parent contract failed")
    return {
        "blockers": blockers,
        "occupied": occupied,
        "adaptive_running": running,
        "conflicting_processes": conflicts,
        "selected_cpu": cpu,
        "caller_affinity": allowed,
        "cgroup_parent": {
            "path": str(parent),
            "inode": parent_stat.st_ino,
            "uid": parent_stat.st_uid,
            "gid": parent_stat.st_gid,
            "controllers": controllers,
            "direct_procs": direct_procs,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--validation-only", action="store_true")
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

    implementations = {
        name: verify_file(record, f"implementation {name}")
        for name, record in plan["implementation"].items()
    }
    if implementations["producer"] != Path(__file__).resolve(strict=True):
        raise RuntimeError("plan does not bind this producer")
    verify_file(plan["antecedents"]["acquisition"], "acquisition antecedent")
    verify_file(plan["antecedents"]["option_probe_audit"], "option probe audit")
    for name, record in plan["geekbench"].items():
        verify_file(record, f"Geekbench {name}")
    system_tools = {
        name: verify_file(record, f"system tool {name}")
        for name, record in plan["system_tools"].items()
    }
    if implementations["managed_lease"] != Path(managed_exclusive_lease.__file__).resolve():
        raise RuntimeError("managed lease import mismatch")
    if implementations["lease_verifier"] != Path(managed_exclusive_lease_verify.__file__).resolve():
        raise RuntimeError("lease verifier import mismatch")

    preflight = dynamic_preflight(plan)
    validation = {
        "candidate_id": CANDIDATE,
        "static_validation_pass": True,
        "dynamic_preflight": preflight,
        "execution_ready": not preflight["blockers"],
    }
    if args.validation_only:
        print(json.dumps(validation, sort_keys=True, indent=2))
        return 0
    if preflight["blockers"]:
        raise RuntimeError(f"calibration admission failed: {preflight['blockers']}")

    quiet = quiet_cpu_sample(
        plan["benchmark"]["quiet_cpus"],
        int(plan["admission"]["quiet_intervals"]),
        float(plan["admission"]["quiet_interval_seconds"]),
    )
    maximum_busy = float(plan["admission"]["maximum_average_busy_fraction"])
    if any(value > maximum_busy for value in quiet["average_busy_fraction"].values()):
        raise RuntimeError("selected physical core was not quiescent")
    second_preflight = dynamic_preflight(plan)
    if second_preflight["blockers"]:
        raise RuntimeError("calibration admission changed during quiescence sample")

    paths = plan["paths"]
    result_root = Path(paths["result_root"])
    scratch_root = Path(paths["scratch_root"])
    cgroup = Path(paths["cgroup_path"])
    lease_path = Path(paths["lease_path"])
    result_root.mkdir(mode=0o700)
    scratch_root.mkdir(mode=0o700)
    host_path = result_root / "host.json"
    transition_path = result_root / "lease-transition.json"
    terminal_lease_path = result_root / "lease-terminal.json"
    lease_verification_path = result_root / "lease-verification.json"
    receipt_path = result_root / "producer-receipt.json"
    write_new(host_path, host_fingerprint())

    python = system_tools["python"]
    worker_command = worker_argv(
        plan_path.resolve(strict=True), plan, implementations["worker"], python
    )
    worker_command_digest = command_sha256(worker_command)
    lease: managed_exclusive_lease.ManagedExclusiveLease | None = None
    child: subprocess.Popen[Any] | None = None
    ready_r = ready_w = release_r = release_w = None
    cgroup_inode: int | None = None
    cgroup_created = False
    samples: list[dict[str, Any]] = []
    affinity_violations: list[dict[str, Any]] = []
    isolated_worker_netns: set[int] = set()
    host_netns = Path("/proc/self/ns/net").stat().st_ino
    worker_returncode: int | None = None
    events_before: dict[str, int] = {}
    events_after: dict[str, int] = {}
    final_peak: int | None = None
    cleanup_pass = False
    try:
        lease = managed_exclusive_lease.ManagedExclusiveLease.acquire(
            lease_path=lease_path,
            transition_path=transition_path,
            candidate_id=CANDIDATE,
            command_sha256=worker_command_digest,
            runner_sha256=sha256_file(Path(__file__)),
            guard_path=str(Path(__file__).resolve()),
            result_path=str(result_root),
            scratch_path=str(scratch_root),
            claim_boundary="current-host Geekbench 5 Tryout calibration only",
        )
        cgroup.mkdir(mode=0o700)
        cgroup_created = True
        cgroup_inode = cgroup.stat().st_ino
        (cgroup / "memory.max").write_text(
            str(plan["resources"]["memory_max_bytes"]), encoding="ascii"
        )
        (cgroup / "memory.swap.max").write_text("0", encoding="ascii")
        events_before = cgroup_events(cgroup / "memory.events")
        if (cgroup / "cgroup.procs").read_text(encoding="ascii").split():
            raise RuntimeError("calibration cgroup is not empty before spawn")

        ready_r, ready_w = os.pipe()
        release_r, release_w = os.pipe()
        gate = (
            "import os;"
            f"open({str(cgroup / 'cgroup.procs')!r},'w').write(str(os.getpid()));"
            f"os.sched_setaffinity(0,{{{int(plan['benchmark']['selected_logical_cpu'])}}});"
            f"os.write({ready_w},b'1');os.read({release_r},1);"
            f"os.execv({worker_command[0]!r},{worker_command!r})"
        )
        launch_command = [str(python), "-c", gate]
        with (result_root / "worker-launch.stdout").open("xb") as launch_stdout, (
            result_root / "worker-launch.stderr"
        ).open("xb") as launch_stderr:
            child = subprocess.Popen(
                launch_command,
                stdin=subprocess.DEVNULL,
                stdout=launch_stdout,
                stderr=launch_stderr,
                pass_fds=(ready_w, release_r),
                start_new_session=True,
            )
        os.close(ready_w)
        ready_w = None
        os.close(release_r)
        release_r = None
        joined = os.read(ready_r, 1) == b"1" and str(child.pid) in (
            cgroup / "cgroup.procs"
        ).read_text(encoding="ascii").split()
        if not joined or sorted(os.sched_getaffinity(child.pid)) != [
            int(plan["benchmark"]["selected_logical_cpu"])
        ]:
            raise RuntimeError("calibration worker did not join and pin before release")
        _, child_start_ticks = proc_identity(child.pid)
        lease.activate_codec(
            codec_pid=child.pid,
            codec_proc_start_ticks=child_start_ticks,
            codec_command_sha256=worker_command_digest,
        )
        os.write(release_w, b"1")
        os.close(release_w)
        release_w = None

        while child.poll() is None:
            pids = [
                int(value)
                for value in (cgroup / "cgroup.procs").read_text(encoding="ascii").split()
            ]
            process_rows: list[dict[str, Any]] = []
            for pid in pids:
                try:
                    affinity = sorted(os.sched_getaffinity(pid))
                    comm = Path(f"/proc/{pid}/comm").read_text(encoding="utf-8").strip()
                    netns = Path(f"/proc/{pid}/ns/net").stat().st_ino
                except (FileNotFoundError, ProcessLookupError):
                    continue
                row = {"pid": pid, "comm": comm, "affinity": affinity, "netns_inode": netns}
                process_rows.append(row)
                if affinity != [int(plan["benchmark"]["selected_logical_cpu"])]:
                    affinity_violations.append(row)
                if comm in {"geekbench5", "geekbench_x86_64"} and netns != host_netns:
                    isolated_worker_netns.add(netns)
            samples.append(
                {
                    "monotonic_ns": time.monotonic_ns(),
                    "processes": process_rows,
                    "memory_current": int((cgroup / "memory.current").read_text(encoding="ascii")),
                    "memory_peak": int((cgroup / "memory.peak").read_text(encoding="ascii")),
                }
            )
            lease.heartbeat()
            time.sleep(float(plan["resources"]["sample_interval_seconds"]))
        worker_returncode = child.wait()
    finally:
        for descriptor in (ready_r, ready_w, release_r, release_w):
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
            worker_returncode = child.returncode
        if cgroup_created and cgroup.exists():
            occupants = (cgroup / "cgroup.procs").read_text(encoding="ascii").split()
            if occupants and (cgroup / "cgroup.kill").exists():
                (cgroup / "cgroup.kill").write_text("1", encoding="ascii")
            for _ in range(100):
                if not (cgroup / "cgroup.procs").read_text(encoding="ascii").split():
                    break
                time.sleep(0.01)
            events_after = cgroup_events(cgroup / "memory.events")
            final_peak = int((cgroup / "memory.peak").read_text(encoding="ascii"))
            if (
                not (cgroup / "cgroup.procs").read_text(encoding="ascii").split()
                and cgroup.stat().st_ino == cgroup_inode
            ):
                cgroup.rmdir()
                cleanup_pass = not cgroup.exists()
        if lease is not None:
            lease.release(evidence_path=terminal_lease_path)

    verification_args = argparse.Namespace(
        transition_log=transition_path,
        terminal_lease=terminal_lease_path,
        output=None,
    )
    lease_verification, lease_verified = managed_exclusive_lease_verify.verify(
        verification_args
    )
    write_new(lease_verification_path, lease_verification)
    worker_receipt_path = result_root / "worker-receipt.json"
    worker_receipt = load_json(worker_receipt_path, "worker receipt")
    event_delta = {
        key: events_after.get(key, 0) - events_before.get(key, 0)
        for key in set(events_before) | set(events_after)
    }
    resource_pass = (
        bool(samples)
        and not affinity_violations
        and final_peak is not None
        and final_peak < int(plan["resources"]["memory_max_bytes"])
        and event_delta.get("oom", 0) == 0
        and event_delta.get("oom_kill", 0) == 0
        and event_delta.get("max", 0) == 0
        and cleanup_pass
        and bool(isolated_worker_netns)
    )
    calibration_pass = (
        worker_returncode == 0
        and worker_receipt.get("worker_calibration_pass") is True
        and isinstance(worker_receipt.get("selected_single_core_score"), int)
        and worker_receipt["selected_single_core_score"] > 0
        and resource_pass
        and lease_verified
    )
    receipt = {
        "$schema": RECEIPT_SCHEMA,
        "candidate_id": CANDIDATE,
        "terminal": True,
        "terminal_authority": calibration_pass,
        "claim_authority": "current_host_geekbench5_single_core" if calibration_pass else "none",
        "objective_credit_bytes": 0,
        "plan": artifact(plan_path),
        "implementation": artifact(implementations["producer"]),
        "host": artifact(host_path),
        "preflight": preflight,
        "post_quiet_preflight": second_preflight,
        "quiet_cpu_evidence": quiet,
        "worker_command": worker_command,
        "worker_command_sha256": worker_command_digest,
        "worker_returncode": worker_returncode,
        "worker_receipt": artifact(worker_receipt_path),
        "selected_single_core_score": worker_receipt.get("selected_single_core_score"),
        "selected_raw_report": worker_receipt.get("selected_raw_report"),
        "network": {
            "host_netns_inode": host_netns,
            "isolated_worker_netns_inodes": sorted(isolated_worker_netns),
            "isolation_observed": bool(isolated_worker_netns),
        },
        "resources": {
            "memory_max_bytes": int(plan["resources"]["memory_max_bytes"]),
            "memory_swap_max_bytes": 0,
            "memory_peak_bytes": final_peak,
            "memory_event_delta": event_delta,
            "affinity_violations": affinity_violations,
            "sample_count": len(samples),
            "samples": samples,
            "scratch_bytes": directory_bytes(scratch_root),
            "cgroup_inode": cgroup_inode,
            "cgroup_cleanup_pass": cleanup_pass,
            "resource_pass": resource_pass,
        },
        "lease": {
            "transition": artifact(transition_path),
            "terminal": artifact(terminal_lease_path),
            "verification": artifact(lease_verification_path),
            "verified": lease_verified,
            "canonical_namespace_released": not lease_path.exists()
            and not lease_path.with_name(f"{lease_path.name}.lock").exists(),
        },
        "runtime_formula_seconds": "252000000 / selected_single_core_score",
        "runtime_limit_seconds": (
            252000000 / worker_receipt["selected_single_core_score"]
            if calibration_pass
            else None
        ),
        "cmix_100m_successor_authorized": False,
    }
    write_new(receipt_path, receipt)
    print(json.dumps(artifact(receipt_path), sort_keys=True))
    return 0 if calibration_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
