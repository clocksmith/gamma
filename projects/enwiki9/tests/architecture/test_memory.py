"""Memory-guard identity and conservative behavior without a resident guard."""
import os
from pathlib import Path
import sys

import pytest

from gamma_enwiki9.execution import memory
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget


@pytest.fixture
def simulated_cgroup(tmp_path, monkeypatch):
    group = tmp_path / "group"
    group.mkdir()
    (group / "memory.max").write_text("67108864")
    (group / "memory.swap.max").write_text("0")
    monkeypatch.setattr(memory, "CGROUP_ROOT", tmp_path)
    monkeypatch.setattr(memory, "current_cgroup", lambda: group)
    return group


def test_memory_guard_checks_identity_limit_and_swap(simulated_cgroup):
    group = simulated_cgroup
    with memory.CgroupMemoryGuard.current(64 * 1024**2) as guard:
        assert guard.verify(64 * 1024**2)["memory_max_bytes"] == 64 * 1024**2
        (group / "memory.max").write_text("max")
        with pytest.raises(ValueError, match="resident"):
            guard.verify(64 * 1024**2)
        (group / "memory.max").write_text(str(128 * 1024**2))
        with pytest.raises(ValueError, match="resident"):
            guard.verify(64 * 1024**2)
        (group / "memory.max").write_text(str(64 * 1024**2))
        (group / "memory.swap.max").write_text("1")
        with pytest.raises(ValueError, match="swap"):
            guard.verify(64 * 1024**2)


def test_memory_guard_rejects_replaced_directory(simulated_cgroup):
    group = simulated_cgroup
    with memory.CgroupMemoryGuard.current(64 * 1024**2) as guard:
        group.rename(group.with_name("old"))
        group.mkdir()
        with pytest.raises(ValueError, match="identity"):
            guard.verify(64 * 1024**2)


def test_memory_guard_rejects_process_migration(simulated_cgroup, monkeypatch):
    with memory.CgroupMemoryGuard.current(64 * 1024**2) as guard:
        monkeypatch.setattr(memory, "current_cgroup", lambda: simulated_cgroup.parent / "elsewhere")
        with pytest.raises(ValueError, match="left"):
            guard.verify(64 * 1024**2)


def test_unguarded_commands_keep_conservative_address_limit(tmp_path):
    context = ExecutionContext("memory-fixture", tmp_path, tmp_path,
        ResourceBudget((min(os.sched_getaffinity(0)),), 64 * 1024**2, 1024**2, 10),
        BuildProfile((), ()), (("PATH", "/usr/bin:/bin"),))
    outcome, record = CommandExecutor(context).run("mapping", [sys.executable, "-c",
        "import mmap; mmap.mmap(-1, 256*1024**2)"], PhaseLimits(5, 5, 512 * 1024**2, 1024**2))
    assert outcome.classification == "execution_failed"
    assert record["address_limit_bytes"] == 64 * 1024**2
    assert record["resident_memory_guard"] is None
