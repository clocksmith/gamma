"""Explicit timestamped host observations; unavailable observations grant no authority."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import math
import os
import time
import re
import shutil


def text(value):
    return value if isinstance(value, str) else ""


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def cpu_ticks(value):
    """Exclude guest ticks, which Linux already includes in user/nice."""
    result = {}
    for line in value.splitlines():
        fields = line.split()
        if fields and re.fullmatch(r"cpu\d+", fields[0]):
            ticks = tuple(map(int, fields[1:9]))
            if len(ticks) == 8 and min(ticks) >= 0:
                result[int(fields[0][3:])] = ticks
    return result

def cpu_usage(before, after, cpus):
    rows = []
    for cpu in cpus:
        a, b = before.get(cpu), after.get(cpu)
        delta = [y - x for x, y in zip(a, b)] if a and b else []
        valid = len(delta) == 8 and min(delta) >= 0 and sum(delta) > 0
        total = sum(delta) if valid else None
        rows.append({"cpu": cpu,
                     "busy_percent": round(100 * (total - delta[3] - delta[4]) / total, 2) if valid else None,
                     "iowait_percent": round(100 * delta[4] / total, 2) if valid else None})
    return rows

def visible_cgroup_limits(proc=Path("/proc")):
    """Read visible v2 ancestors; this does not reserve capacity or audit guards."""
    member = next(line[3:] for line in (proc / "self/cgroup").read_text().splitlines()
                  if line.startswith("0::"))
    mounts = []
    for line in (proc / "self/mountinfo").read_text().splitlines():
        left, right = line.split(" - ", 1)
        fields = left.split()
        if right.split()[0] == "cgroup2":
            # mountinfo escapes spaces, tabs, newlines, and backslashes as octal.
            decode = lambda s: re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), s)
            mount_root, mount = Path(decode(fields[3])), Path(decode(fields[4]))
            if Path(member).is_relative_to(mount_root):
                mounts.append((mount_root, mount))
    mount_root, mount = max(mounts, key=lambda row: len(row[0].parts))
    current = mount / Path(member).relative_to(mount_root)
    rows = []
    while True:
        row = {"path": str(current), "memory_limit_bytes": None,
               "memory_current_bytes": None, "cpu_quota_cores": None}
        controllers = set((current / "cgroup.controllers").read_text().split())
        row["available_controllers"] = sorted(controllers)
        for name in ("memory.max", "memory.current", "cpu.max"):
            path = current / name
            # The hierarchy root has no limit files.
            if current == mount and mount_root == Path("/") and not path.exists():
                continue
            # A controller disabled below an ancestor has no local limit files.
            # Keep walking: that ancestor can still impose an effective ceiling.
            if not path.exists() and name.split(".")[0] not in controllers:
                continue
            value = path.read_text().strip()
            if name == "cpu.max":
                quota, period = value.split()
                if int(period) <= 0 or (quota != "max" and int(quota) <= 0):
                    raise ValueError("invalid CPU quota")
                row["cpu_quota_cores"] = None if quota == "max" else int(quota) / int(period)
            else:
                number = None if value == "max" and name == "memory.max" else int(value)
                if number is not None and number < 0:
                    raise ValueError("invalid memory counter")
                row["memory_limit_bytes" if name == "memory.max" else "memory_current_bytes"] = number
        rows.append(row)
        if current == mount:
            return {"state": "observed", "membership": member, "ancestors": rows,
                    "note": "Visible hierarchy only; hidden ancestors and other job cgroups are not audited."}
        current = current.parent

def resource_snapshot(proc=Path("/proc"), *, scratch=Path(".")):
    """One bounded operational sample, without starting another monitor."""
    issues = []
    def probe(label, operation):
        try:
            return operation()
        except (OSError, ValueError, AttributeError, StopIteration, IndexError) as exc:
            issues.append(f"{label}: {type(exc).__name__}: {exc}")
            return None

    cpus = probe("affinity", lambda: sorted(os.sched_getaffinity(0)))
    memory = probe("memory", lambda: {line.split()[0].rstrip(":"): int(line.split()[1]) * 1024
                                      for line in (proc / "meminfo").read_text().splitlines()
                                      if line.startswith(("MemTotal:", "MemAvailable:"))}) or {}
    total, available = memory.get("MemTotal"), memory.get("MemAvailable")
    if total is None or available is None or not 0 <= available <= total:
        issues.append("memory: total/available counters missing or inconsistent")
        total = available = None
    before = probe("CPU initial sample", lambda: cpu_ticks((proc / "stat").read_text()))
    started = time.monotonic()
    time.sleep(0.1)
    after = probe("CPU final sample", lambda: cpu_ticks((proc / "stat").read_text()))
    interval = time.monotonic() - started
    rows = cpu_usage(before or {}, after or {}, cpus or [])
    if not rows or any(row["busy_percent"] is None for row in rows):
        issues.append("CPU usage: missing, reset, or unchanged sampled counters")
    cgroup = probe("cgroup limits", lambda: visible_cgroup_limits(proc))
    bounds = [available] if available is not None else []
    quotas = []
    for row in (cgroup or {}).get("ancestors", []):
        if row["memory_limit_bytes"] is not None:
            bounds.append(max(0, row["memory_limit_bytes"] - row["memory_current_bytes"]))
        if row["cpu_quota_cores"] is not None:
            quotas.append(row["cpu_quota_cores"])
    return {"observed_at": utc(), "logical_cpus": os.cpu_count(), "allowed_cpus": cpus,
            "cpu_sample_seconds": round(interval, 4), "cpu_usage": rows,
            "load_average_1_5_15": probe("load average", os.getloadavg),
            "host_memory_total_bytes": total, "host_memory_available_bytes": available,
            "host_memory_unavailable_bytes": total - available if total is not None else None,
            "cgroup": cgroup or {"state": "unknown"},
            "visible_cpu_capacity_ceiling": min([len(cpus)] + quotas) if cpus and cgroup else None,
            "visible_memory_headroom_bytes": min(bounds) if available is not None and cgroup else None,
        "scratch_available_bytes": probe("scratch filesystem", lambda: shutil.disk_usage(scratch).free),
            "issues": issues, "launch_authorized": False,
            "meaning": "Instantaneous diagnostics, not free CPU assignments or reservations. Memory uses MemAvailable, not free pages. Account for other jobs, remaining reservations, affinity, cgroups, and headroom before admission; concurrent timing is diagnostic."}

def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result.astimezone(timezone.utc) if result.tzinfo is not None else None
    except (AttributeError, TypeError, ValueError):
        return None

def job_timeline(run, previous=None, now=None):
    """Keep recorded starts, budget deadlines, and progress predictions distinct."""
    now = now or datetime.now(timezone.utc)
    started = timestamp(run.get("started_at"))
    budget = run.get("resource_budget")
    wall = budget.get("wall_seconds") if isinstance(budget, dict) else None
    valid_wall = type(wall) in (int, float) and math.isfinite(wall) and wall > 0
    result = {key: run.get(key) for key in ("submitted_at", "started_at", "worker_started_at")}
    result.update({"elapsed_since_recorded_start_seconds": round((now - started).total_seconds(), 1)
                   if started and started <= now else None,
                   "budget_seconds": wall if valid_wall else None,
                   "budget_stop_reference_at": None,
                   "budget_note": "Recorded job start plus declared wall budget; consult the owning guard for its actual enforcement timebase. This is not a completion prediction.",
                   "expected_job_finish_at": None, "phase_estimate": {"state": "unknown",
                       "reason": "Two comparable fresh identity-bound operational samples are required; job completion may include later phases."}})
    if started and started <= now and valid_wall:
        try:
            result["budget_stop_reference_at"] = (started + timedelta(seconds=wall)).isoformat()
        except OverflowError:
            pass
    current = run.get("progress_observation") or {}
    previous = previous or {}
    if not isinstance(current, dict) or not isinstance(previous, dict):
        return result
    if (run.get("state") != "running" or (run.get("liveness") or {}).get("state") != "live"
            or run.get("id") not in {current.get("adaptive_job_id"), current.get("observer_job_id")}):
        return result
    binding = ("adaptive_job_id", "adaptive_job_path", "observer_job_id", "observer_candidate", "observer_progress_path")
    def bound_value(observation, key):
        value = observation.get(key)
        return text(value).removeprefix("projects/enwiki9/") if key.endswith("_path") else value
    if not all(bound_value(current, k) and bound_value(current, k) == bound_value(previous, k) for k in binding):
        return result
    for observation in (current, previous):
        if (observation.get("source") != "bound_existing_horizon_observer"
                or not all(observation.get(k) is True for k in ("observer_progress_fresh", "observer_sample_identities_match", "source_processes_live", "observer_worker_live"))):
            return result
    a, b = previous.get("observer_progress") or {}, current.get("observer_progress") or {}
    if not isinstance(a, dict) or not isinstance(b, dict):
        return result
    t0, t1 = timestamp(a.get("updatedUtc")), timestamp(b.get("updatedUtc"))
    if not t0 or not t1 or not 0 < (t1 - t0).total_seconds() <= 3600 or not 0 <= (now - t1).total_seconds() <= 120:
        return result
    values = [p.get(k) for p in (a, b) for k in ("traceBytes", "expectedTraceBytes", "sampleCount")]
    if not all(type(value) is int and value >= 0 for value in values):
        return result
    if (a.get("state") != "observing" or b.get("state") != "observing"
            or a["expectedTraceBytes"] != b["expectedTraceBytes"]
            or not 0 <= a["traceBytes"] < b["traceBytes"] < b["expectedTraceBytes"]
            or a["sampleCount"] >= b["sampleCount"]):
        return result
    interval = (t1 - t0).total_seconds()
    rate = (b["traceBytes"] - a["traceBytes"]) / interval
    remaining = (b["expectedTraceBytes"] - b["traceBytes"]) / rate
    try:
        finish = (t1 + timedelta(seconds=remaining)).isoformat()
    except OverflowError:
        return result
    result["phase_estimate"] = {"state": "estimated", "phase": "trace production",
        "basis": "Current existing observer and prior docs/status_receipt.json gate_decision; matching job bindings and reported exact process identity checks.",
        "sample_start_at": a["updatedUtc"], "sample_end_at": b["updatedUtc"],
        "sample_window_seconds": interval, "units": "transformed trace bytes",
        "bytes_per_second": round(rate, 3), "remaining_bytes": b["expectedTraceBytes"] - b["traceBytes"],
        "expected_phase_finish_at": finish,
        "uncertainty": "Linear extrapolation of two operational counters, not a confidence interval or job finish promise. Throughput and subsequent phases can change; refresh before acting."}
    return result
