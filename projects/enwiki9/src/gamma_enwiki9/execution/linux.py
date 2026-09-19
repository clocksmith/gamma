"""Linux execution envelopes and owned cleanup, independent of research decisions."""
from __future__ import annotations
import hashlib
import os
import pathlib
import subprocess
import sys
import time
from typing import Any

def validate_execution_budget(job: dict[str, Any], *, objective=None) -> dict[str, Any]:
    mode = job.get("execution_mode")
    budget = job.get("resource_budget")
    if mode not in {"discovery", "qualification"} or not isinstance(budget, dict):
        raise ValueError("explicit discovery/qualification mode and resource budget are required")
    cpus = budget.get("cpus")
    if (not isinstance(cpus, list) or not cpus
            or any(not isinstance(cpu, int) or isinstance(cpu, bool) or cpu < 0 for cpu in cpus)
            or len(set(cpus)) != len(cpus)):
        raise ValueError("resource budget requires a unique explicit CPU set")
    for key in ("memory_bytes", "scratch_bytes", "wall_seconds"):
        value = budget.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"resource budget requires positive {key}")
    if budget["memory_bytes"] < 1024 or budget.get("swap_bytes") != 0:
        raise ValueError("resource budget requires at least 1024 memory bytes and zero swap")
    parent = pathlib.Path(str(budget.get("cgroup_parent", "")))
    if not parent.is_absolute() or not parent.is_relative_to("/sys/fs/cgroup"):
        raise ValueError("cgroup parent must be an absolute delegated cgroup-v2 directory")
    existing = budget.get("existing_guard")
    if existing is not None:
        if not isinstance(existing, dict):
            raise ValueError("existing guard declaration must be an object")
        path = pathlib.Path(str(existing.get("path", "")))
        memory = existing.get("memory_bytes")
        if (path.parent != parent or not isinstance(existing.get("inode"), int)
                or not isinstance(memory, int) or memory <= 0 or memory % 1024
                or budget["memory_bytes"] - memory < 16 * 1024 * 1024):
            raise ValueError("existing guard requires one sibling cgroup and a separate coordinator memory budget")
        if mode != "discovery":
            raise ValueError("existing nested guard adoption currently supports diagnostic discovery only")
    if mode == "qualification":
        if not isinstance(budget.get("calibration"), dict):
            raise ValueError("qualification requires source-bound verified host calibration")
        if objective is None:
            raise ValueError("qualification requires explicit verified resource limits")
        if len(cpus) != 1:
            raise ValueError("qualification requires one assigned CPU")
        if (budget["memory_bytes"] > objective["resources"]["memory"]["maximumBytes"]
                or budget["scratch_bytes"] > objective["resources"]["temporaryDisk"]["maximumBytes"]):
            raise ValueError("qualification budget exceeds the active objective resource limits")
    return budget


def parse_cpu_set(value: str) -> set[int]:
    result: set[int] = set()
    for part in value.strip().split(","):
        bounds = part.split("-")
        if len(bounds) == 1:
            result.add(int(bounds[0]))
        elif len(bounds) == 2 and int(bounds[0]) <= int(bounds[1]):
            result.update(range(int(bounds[0]), int(bounds[1]) + 1))
        else:
            raise ValueError("invalid CPU set")
    return result


def _group_write(descriptor: int, name: str, value: str) -> None:
    fd = os.open(name, os.O_WRONLY | os.O_NOFOLLOW, dir_fd=descriptor)
    try:
        os.write(fd, value.encode())
    finally:
        os.close(fd)


def _group_read(descriptor: int, name: str) -> str:
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=descriptor)
    try:
        with os.fdopen(fd) as stream:
            return stream.read()
    except BaseException:
        raise


def _group_populated(descriptor: int) -> bool:
    return dict(line.split() for line in _group_read(descriptor, "cgroup.events").splitlines()).get("populated") != "0"


def cleanup_unstarted(handles):
    """Rollback only groups created by this attempt, before child launch."""
    errors = []
    for handle in reversed(handles):
        try:
            fd = handle["descriptor"]
            path = pathlib.Path(handle["path"])
            observed = os.fstat(fd)
            if not os.path.samestat(observed, path.stat()) or observed.st_ino != handle["inode"]:
                raise RuntimeError("unstarted cgroup identity changed")
            if _group_populated(fd):
                raise RuntimeError("unstarted cgroup unexpectedly contains processes")
            if handle.get("created", True):
                path.rmdir()
        except Exception as exc:
            errors.append(str(exc))
        finally:
            os.close(handle["descriptor"])
    if errors:
        raise RuntimeError("unstarted cleanup incomplete: " + "; ".join(errors))


def prepare_execution_envelope(job: dict[str, Any], command: list[str], snapshot: pathlib.Path, *, root: pathlib.Path, run_logs: pathlib.Path, artifact_reference, objective=None) -> tuple[list[str], list[dict[str, Any]]]:
    budget = validate_execution_budget(job, objective=objective)
    guard = root / "tools/run_with_resource_guard_v3.py"
    if artifact_reference(guard) != job.get("execution_guard"):
        raise ValueError("execution guard source differs from queued binding")
    if not set(budget["cpus"]).issubset(os.sched_getaffinity(0)):
        raise ValueError("assigned CPU set is unavailable to this worker")
    parent = pathlib.Path(budget["cgroup_parent"])
    if parent.is_symlink() or parent.resolve() != parent or not parent.is_dir():
        raise ValueError("delegated cgroup parent is unavailable or redirected")
    group = parent / f"gamma-enwiki9-{job['job_id']}"
    existing = budget.get("existing_guard")
    memory = budget["memory_bytes"] // 1024 * 1024
    coordinator_memory = memory - (existing["memory_bytes"] if existing else 0)
    handles: list[dict[str, Any]] = []
    try:
        if existing:
            existing_path = pathlib.Path(existing["path"])
            if existing_path.is_symlink() or existing_path.resolve() != existing_path:
                raise ValueError("declared existing guard cgroup was redirected")
            descriptor = os.open(existing_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            handles.append({"path": str(existing_path), "descriptor": descriptor, "created": False,
                            "inode": os.fstat(descriptor).st_ino, "memory_bytes": existing["memory_bytes"]})
            if os.fstat(descriptor).st_ino != existing["inode"] or _group_populated(descriptor):
                raise ValueError("declared existing guard cgroup changed or is occupied")
        group.mkdir()
        descriptor = os.open(group, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        handles.append({"path": str(group), "descriptor": descriptor, "created": True,
                        "inode": os.fstat(descriptor).st_ino, "memory_bytes": coordinator_memory})
        for handle in handles:
            fd = handle["descriptor"]
            _group_write(fd, "memory.swap.max", "0\n")
            handle["kernel_cpuset"] = (parent / "cpuset.mems.effective").is_file()
            if handle["kernel_cpuset"]:
                _group_write(fd, "cpuset.mems", (parent / "cpuset.mems.effective").read_text())
                _group_write(fd, "cpuset.cpus", ",".join(map(str, budget["cpus"])) + "\n")
            _group_write(fd, "memory.max", str(handle["memory_bytes"]) + "\n")
            # Open the kill interface before launching; lack of termination authority fails admission.
            kill_fd = os.open("cgroup.kill", os.O_WRONLY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(kill_fd)
        resources = run_logs / f"{job['job_id']}.resources"
        resources.mkdir()
        marker = resources / "phases.jsonl"
        marker.touch(exist_ok=False)
        receipt = resources / "guard.json"
        scratch = root / "results" / job["candidate_id"]
        scratch.mkdir(parents=True, exist_ok=True)
        limit_kib = coordinator_memory // 1024
        wrapped = [sys.executable, str(guard), "--limit-kib", str(limit_kib),
                   "--official-decimal-limit-kib", str(limit_kib), "--limit-mode", "tree",
                   "--cgroup-path", str(group), "--cgroup-memory-max-bytes", str(limit_kib * 1024),
                   "--temporary-disk-limit-bytes", str(budget["scratch_bytes"]),
                   "--phase-marker-path", str(marker), "--max-logical-cpus", str(len(budget["cpus"])),
                   "--guard-json", str(receipt), "--label", job["job_id"], "--phase", "diagnostic"]
        log_path = run_logs / f"{job['job_id']}.log"
        log_path.touch(exist_ok=False)
        for path in sorted({scratch, snapshot, resources, log_path}):
            wrapped.extend(["--scratch-path", str(path)])
        marker_script = 'printf \'%s\\n\' \'{"phase":"diagnostic","event":"worker_start","detail":"operational envelope only; no codec phase credit"}\' >> "$GAMMA_RESOURCE_PHASE_MARKERS" || exit 125; exec "$@"'
        wrapped.extend(["--", "/usr/bin/taskset", "--cpu-list", ",".join(map(str, budget["cpus"])),
                        "/bin/sh", "-c", marker_script, "enwiki9-discovery-envelope", *command])
        job["execution_resources"] = {"cgroup_path": str(group), "cgroup_inode": handles[-1]["inode"],
                                      "groups": [{k: v for k, v in h.items() if k != "descriptor"} for h in handles],
                                      "guard_path": str(receipt.relative_to(root)),
                                      "guard_command_sha256": hashlib.sha256(b"\0".join(os.fsencode(x) for x in wrapped)).hexdigest(),
                                      "boot_id": pathlib.Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                                      "cpu_enforcement": "kernel-cpuset-and-taskset" if all(h["kernel_cpuset"] for h in handles) else "taskset-and-sampled-affinity-guard",
                                      "missing_diagnostics": [] if all(h["kernel_cpuset"] for h in handles) else ["kernel cpuset controller is not delegated; taskset assignment and existing affinity guard remain active"],
                                      "budget": budget, "timing_authority": job.get("timing_authority")}
        return wrapped, handles
    except BaseException:
        for handle in reversed(handles):
            os.close(handle["descriptor"])
            if handle["created"]:
                pathlib.Path(handle["path"]).rmdir()
        raise


def wait_for_budgeted_worker(process: subprocess.Popen[Any], job: dict[str, Any], handles: list[dict[str, Any]], *, abort_reason: str | None = None, read_group=None, write_group=None, group_populated=None) -> int:
    read_group = read_group or _group_read
    write_group = write_group or _group_write
    group_populated = group_populated or _group_populated
    deadline = time.monotonic() + job["resource_budget"]["wall_seconds"]
    returncode = 125 if abort_reason is not None else None
    if abort_reason is not None:
        job["execution_resources"]["abort_reason"] = abort_reason
    try:
        while returncode is None:
            for handle in handles:
                descriptor = handle["descriptor"]
                maximum = read_group(descriptor, "memory.max").strip()
                if (maximum == "max" or int(maximum) > handle["memory_bytes"]
                        or read_group(descriptor, "memory.swap.max").strip() != "0"
                        or (handle.get("kernel_cpuset") and parse_cpu_set(read_group(descriptor, "cpuset.cpus")) != set(job["resource_budget"]["cpus"]))):
                    raise ValueError("owned cgroup memory or swap budget changed")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                job["wall_budget_exceeded"] = True
                returncode = 124
                break
            try:
                returncode = process.wait(timeout=min(0.25, remaining))
            except subprocess.TimeoutExpired:
                continue
    finally:
        # A root process exit does not prove all descendants exited. Kill residuals
        # through already-open, inode-bound directories before recording terminal state.
        errors = []
        for handle in handles:
            populated = True
            try:
                populated = group_populated(handle["descriptor"])
            except Exception as exc:
                errors.append(f"{handle['path']}: read population: {exc}")
            if populated:
                job["residual_processes_terminated"] = True
                try:
                    write_group(handle["descriptor"], "cgroup.kill", "1\n")
                except Exception as exc:
                    errors.append(f"{handle['path']}: terminate group: {exc}")
        try:
            if process.poll() is None:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
        except Exception as exc:
            errors.append(f"worker termination: {exc}")
        cleanup_deadline = time.monotonic() + 5
        for handle in reversed(handles):
            try:
                while group_populated(handle["descriptor"]) and time.monotonic() < cleanup_deadline:
                    time.sleep(0.05)
                if group_populated(handle["descriptor"]):
                    raise RuntimeError("owned group still has live members")
                path = pathlib.Path(handle["path"])
                if path.stat().st_ino != handle["inode"]:
                    raise RuntimeError("owned cgroup identity changed")
                path.rmdir()
            except Exception as exc:
                errors.append(f"{handle['path']}: remove group: {exc}")
            finally:
                try:
                    os.close(handle["descriptor"])
                except Exception as exc:
                    errors.append(f"{handle['path']}: close handle: {exc}")
        job["execution_resources"]["cleanup_complete"] = not errors
        if errors:
            job["execution_resources"]["cleanup_errors"] = errors
            raise RuntimeError("owned execution cleanup incomplete: " + "; ".join(errors))
    if returncode == 0 and job.get("residual_processes_terminated"):
        return 125
    return int(returncode)
