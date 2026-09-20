"""Bounded command execution with explicit environment and owned cancellation."""
from __future__ import annotations
from dataclasses import dataclass
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time

from gamma_enwiki9.evidence.artifacts import replace_derived_view
from gamma_enwiki9.types import ExecutionContext, RunOutcome
from gamma_enwiki9.execution.memory import CgroupMemoryGuard


@dataclass(frozen=True)
class PhaseLimits:
    cpu_seconds: int
    wall_seconds: int
    address_bytes: int
    file_bytes: int

    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in vars(self).values()):
            raise ValueError("positive phase limits are required")


class CommandExecutor:
    def __init__(self, context: ExecutionContext, *, resident_guard: CgroupMemoryGuard | None = None):
        self.context = context
        self.resident_guard = resident_guard
        self.started = time.monotonic()
        self.phases = set()

    def run(self, name: str, argv: list[str], limits: PhaseLimits) -> tuple[RunOutcome, dict]:
        if not name or Path(name).name != name or name in self.phases:
            raise ValueError("invalid or repeated phase")
        if not argv or any(not isinstance(a, str) or not a for a in argv):
            raise ValueError("an explicit command array is required")
        self.phases.add(name)
        ctx = self.context
        remaining = ctx.budget.wall_seconds - (time.monotonic() - self.started)
        if remaining <= 0:
            return RunOutcome(None, "budget_exhausted", True), {"phase": name, "argv": argv}
        guard = self.resident_guard
        memory_observation = guard.verify(ctx.budget.memory_bytes) if guard else None
        # Without an inherited resident-memory guard, retain the conservative
        # address cap. A verified cgroup permits sparse file mappings larger
        # than the resident budget without increasing that resident budget.
        address_limit = (limits.address_bytes if guard else
                         min(limits.address_bytes, ctx.budget.memory_bytes))

        def child_limits():
            os.sched_setaffinity(0, ctx.budget.cpus)
            resource.setrlimit(resource.RLIMIT_CPU, (limits.cpu_seconds, limits.cpu_seconds))
            if guard:
                guard.verify(ctx.budget.memory_bytes)
            resource.setrlimit(resource.RLIMIT_AS, (address_limit, address_limit))
            file_limit = min(limits.file_bytes, ctx.budget.scratch_bytes)
            resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))

        row = {"phase": name, "argv": argv, "returncode": None, "timeout": False, "error": None,
               "address_limit_bytes": address_limit, "resident_memory_guard": memory_observation}
        started = time.monotonic()
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        child = None
        cleanup = True
        try:
            with (ctx.workspace / (name + ".stdout")).open("xb") as out, (ctx.workspace / (name + ".stderr")).open("xb") as err:
                child = subprocess.Popen(argv, cwd=ctx.workspace, stdout=out, stderr=err,
                    env=dict(ctx.environment), preexec_fn=child_limits, start_new_session=True,
                    pass_fds=(guard.descriptor,) if guard else ())
                deadline = time.monotonic() + min(limits.wall_seconds, remaining)
                # Keep the leader unreaped until group cleanup. WNOWAIT prevents
                # PID/PGID reuse between observing exit and owned cancellation.
                while True:
                    exited = os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                    if exited is not None:
                        break
                    if time.monotonic() >= deadline:
                        row["timeout"] = True
                        break
                    time.sleep(0.01)
        except (OSError, subprocess.SubprocessError) as exc:
            row["error"] = str(exc)
        finally:
            if child is not None:
                # Own only the session created for this invocation, including on
                # KeyboardInterrupt. Lab jobs additionally have inode-bound cgroups.
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except OSError:
                    cleanup = False
                child.wait()
                row["returncode"] = child.returncode
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            if guard:
                try:
                    guard.verify(ctx.budget.memory_bytes)
                except (OSError, ValueError) as exc:
                    row["error"] = str(exc)
            row.update(elapsed_seconds=time.monotonic() - started,
                user_cpu_seconds=after.ru_utime - before.ru_utime,
                system_cpu_seconds=after.ru_stime - before.ru_stime,
                timing_authority="shared-host diagnostic", cleanup_complete=cleanup)
            replace_derived_view(ctx.workspace / (name + ".execution.json"),
                                 (json.dumps(row, indent=2, sort_keys=True) + "\n").encode())
        classification = ("budget_exhausted" if row["timeout"] else "execution_failed"
            if row["returncode"] != 0 or row["error"] or not cleanup else "completed")
        return RunOutcome(row["returncode"], classification, cleanup), row
