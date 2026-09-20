"""Only uses a cgroup parent explicitly provisioned for this test invocation."""
import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest

pytestmark = pytest.mark.linux_resource


def test_owned_cgroup_kill_and_memory_boundary():
    provisioned = os.environ.get("GAMMA_ENWIKI9_TEST_CGROUP_PARENT")
    if not provisioned:
        pytest.skip("no delegated test cgroup provided")
    parent = Path(provisioned)
    assert parent.is_absolute() and parent.is_relative_to("/sys/fs/cgroup")
    group = parent / ("gamma-architecture-" + uuid.uuid4().hex)
    group.mkdir()
    descriptor = os.open(group, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    identity = os.fstat(descriptor)
    child = None
    try:
        (group / "memory.max").write_text(str(128 * 1024**2))
        (group / "memory.swap.max").write_text("0")
        code = "import os,time; from pathlib import Path; Path(%r).write_text(str(os.getpid())); time.sleep(60)" % str(group / "cgroup.procs")
        child = subprocess.Popen([sys.executable, "-c", code])
        import time
        deadline = time.monotonic() + 5
        while str(child.pid) not in (group / "cgroup.procs").read_text().split() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert str(child.pid) in (group / "cgroup.procs").read_text().split()
        assert (group / "memory.max").read_text().strip() == str(128 * 1024**2)
        kill_fd = os.open("cgroup.kill", os.O_WRONLY | os.O_NOFOLLOW, dir_fd=descriptor)
        try:
            os.write(kill_fd, b"1\n")
        finally:
            os.close(kill_fd)
        assert child.wait(timeout=5) != 0
        assert "populated 0" in (group / "cgroup.events").read_text()
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            child.wait()
        assert os.stat(group).st_ino == identity.st_ino
        os.close(descriptor)
        group.rmdir()


def test_sparse_mapping_can_exceed_resident_budget(tmp_path):
    provisioned = os.environ.get("GAMMA_ENWIKI9_TEST_CGROUP_PARENT")
    if not provisioned:
        pytest.skip("no delegated test cgroup provided")
    parent = Path(provisioned)
    assert parent.is_absolute() and parent.is_relative_to("/sys/fs/cgroup")
    group = parent / ("gamma-memory-" + uuid.uuid4().hex)
    group.mkdir()
    inode = group.stat().st_ino
    child = None
    source = Path(__file__).resolve().parents[2] / "src"
    try:
        (group / "memory.max").write_text(str(64 * 1024**2))
        (group / "memory.swap.max").write_text("0")
        code = '''
import os, sys
from pathlib import Path
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget
group, work = map(Path, sys.argv[1:])
(group / 'cgroup.procs').write_text(str(os.getpid()))
context = ExecutionContext('sparse-memory', work, work,
    ResourceBudget((min(os.sched_getaffinity(0)),), 64*1024**2, 1024**2, 10),
    BuildProfile((), ()), (('PATH', '/usr/bin:/bin'),))
with CgroupMemoryGuard.current(context.budget.memory_bytes) as guard:
    outcome, row = CommandExecutor(context, resident_guard=guard).run('sparse',
        [sys.executable, '-c', 'import mmap; m=mmap.mmap(-1,256*1024**2); m[0]=1; print(len(m))'],
        PhaseLimits(5, 5, 512*1024**2, 1024**2))
    assert outcome.classification == 'completed', row
    assert row['address_limit_bytes'] == 512*1024**2
    assert row['resident_memory_guard']['memory_max_bytes'] == 64*1024**2
'''
        child = subprocess.Popen([sys.executable, "-c", code, str(group), str(tmp_path)],
                                 env={**os.environ, "PYTHONPATH": str(source)})
        assert child.wait(timeout=20) == 0
        assert int((group / "memory.peak").read_text()) <= 64 * 1024**2
        assert "populated 0" in (group / "cgroup.events").read_text()
    finally:
        if child is not None and child.poll() is None:
            (group / "cgroup.kill").write_text("1")
            child.wait()
        assert group.stat().st_ino == inode
        group.rmdir()
