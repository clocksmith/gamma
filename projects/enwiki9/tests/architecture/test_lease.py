import os
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from gamma_enwiki9.execution import lease as leases
from gamma_enwiki9.execution.admission import admission_guard


def acquire(root, name="owner"):
    return leases.ManagedExclusiveLease.acquire(
        lease_path=root / "lease.json", transition_path=root / (name + ".transitions.json"),
        candidate_id=name, command_sha256="1" * 64, runner_sha256="2" * 64,
        guard_path="guard", result_path="result", scratch_path="scratch", claim_boundary="fixture")


def test_losing_contender_preserves_unpublished_foreign_lock(tmp_path):
    lock = tmp_path / "lease.json.lock"
    lock.write_bytes(b"foreign")
    before = lock.stat()
    with pytest.raises(leases.LeaseError):
        acquire(tmp_path)
    assert lock.read_bytes() == b"foreign"
    assert lock.stat().st_ino == before.st_ino


def test_competing_acquisitions_have_one_owner(tmp_path):
    def attempt(i):
        try:
            return acquire(tmp_path, str(i))
        except leases.LeaseError:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        owners = [x for x in pool.map(attempt, range(8)) if x is not None]
    assert len(owners) == 1
    owners[0].release(evidence_path=tmp_path / "terminal.json")
    assert not (tmp_path / "lease.json.lock").exists()


@pytest.mark.parametrize("failure", [OSError, KeyboardInterrupt])
def test_partial_publication_preserves_namespace(tmp_path, monkeypatch, failure):
    def fail(self, raw):
        (tmp_path / "lease.json").write_bytes(raw[:20])
        raise failure("publication interrupted")
    monkeypatch.setattr(leases._OwnedLock, "publish_lease", fail)
    with pytest.raises(failure):
        acquire(tmp_path)
    assert (tmp_path / "lease.json.lock").exists()
    with pytest.raises(leases.LeaseError):
        acquire(tmp_path, "contender")


def test_release_refuses_replaced_lock_and_lease(tmp_path):
    owner = acquire(tmp_path)
    try:
        lock = owner.lock_path
        lock.rename(tmp_path / "old-lock")
        lock.write_bytes(owner.owned_lock.payload)
        with pytest.raises(leases.LeaseError, match="identity changed"):
            owner.release(evidence_path=tmp_path / "terminal.json")
        assert lock.exists() and owner.lease_path.exists()
    finally:
        owner.owned_lock.detach_without_unlink()


def test_live_codec_cancellation_deauthorizes_but_does_not_release(tmp_path):
    owner = acquire(tmp_path)
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        ticks = leases.proc_identity(child.pid)[1]
        owner.activate_codec(codec_pid=child.pid, codec_proc_start_ticks=ticks, codec_command_sha256="3" * 64)
        with pytest.raises(leases.LeaseError, match="codec identity is live"):
            owner.release(evidence_path=tmp_path / "terminal.json")
        assert leases.read_object(owner.lease_path)["signal_authority"] is False
        assert owner.lock_path.exists()
    finally:
        child.terminate()
        child.wait()
    owner.release(evidence_path=tmp_path / "terminal.json")


def test_pid_reuse_does_not_authenticate_process(monkeypatch):
    monkeypatch.setattr(leases, "proc_identity", lambda pid: (1, 888))
    assert not leases.identity_is_live(123, 777)


def test_stale_recovery_requires_dead_owner_and_exact_bytes(tmp_path, monkeypatch):
    owner = acquire(tmp_path)
    lock, record = owner.lock_path.read_bytes(), owner.lease_path.read_bytes()
    owner.owned_lock.detach_without_unlink()
    with pytest.raises(leases.LeaseError, match="runner identity is live"):
        leases.recover_stale(owner.lease_path, expected_lock=lock, expected_lease=record,
                             evidence_path=tmp_path / "recovery.json")
    monkeypatch.setattr(leases, "identity_is_live", lambda pid, ticks: False)
    leases.recover_stale(owner.lease_path, expected_lock=lock, expected_lease=record,
                         evidence_path=tmp_path / "recovery.json")
    assert not owner.lock_path.exists() and not owner.lease_path.exists()


def test_queue_admission_and_lease_share_domain(tmp_path):
    owner = acquire(tmp_path)
    try:
        with pytest.raises(ValueError, match="owns admission"):
            with admission_guard(tmp_path):
                pytest.fail("admitted while lease exists")
    finally:
        owner.release(evidence_path=tmp_path / "terminal.json")


def test_same_bytes_at_replacement_lease_inode_are_not_ownership(tmp_path):
    owner = acquire(tmp_path)
    try:
        raw = owner.lease_path.read_bytes()
        owner.lease_path.rename(tmp_path / "original-lease")
        owner.lease_path.write_bytes(raw)
        with pytest.raises(leases.LeaseError, match="file identity changed"):
            owner.release(evidence_path=tmp_path / "terminal.json")
        assert owner.lease_path.exists() and owner.lock_path.exists()
    finally:
        owner.owned_lock.detach_without_unlink()


def test_recovery_refuses_live_codec_even_when_runner_is_stale(tmp_path, monkeypatch):
    owner = acquire(tmp_path)
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        owner.activate_codec(codec_pid=child.pid, codec_proc_start_ticks=leases.proc_identity(child.pid)[1],
                             codec_command_sha256="3" * 64)
        lock, record = owner.lock_path.read_bytes(), owner.lease_path.read_bytes()
        owner.owned_lock.detach_without_unlink()
        monkeypatch.setattr(leases, "identity_is_live", lambda pid, ticks: pid == child.pid)
        with pytest.raises(leases.LeaseError, match="codec identity is live"):
            leases.recover_stale(owner.lease_path, expected_lock=lock, expected_lease=record,
                                 evidence_path=tmp_path / "recovery.json")
        assert owner.lock_path.exists()
    finally:
        child.terminate()
        child.wait()


def test_transition_publication_failure_retains_recoverable_lease(tmp_path, monkeypatch):
    def fail(*args):
        raise OSError("transition publication interrupted")
    monkeypatch.setattr(leases.ManagedExclusiveLease, "_append_transition", fail)
    with pytest.raises(OSError):
        acquire(tmp_path)
    path = tmp_path / "lease.json"
    lock = tmp_path / "lease.json.lock"
    assert path.exists() and lock.exists()
    monkeypatch.setattr(leases, "identity_is_live", lambda pid, ticks: False)
    leases.recover_stale(path, expected_lock=lock.read_bytes(), expected_lease=path.read_bytes(),
                         evidence_path=tmp_path / "recovery.json")
    assert not lock.exists() and not path.exists()
