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
