from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pytest


PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import enwiki9_lab as lab  # noqa: E402
import enwiki9_worker_identity as worker_identity  # noqa: E402


def managed_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict, dict[str, str]]:
    candidate_id = "managed_fixture_q0_v1"
    job_id = "20260904T000000Z_deadbeef00"
    snapshot = (
        tmp_path / f"gamma-enwiki9-{job_id}-suffix" / candidate_id
    )
    snapshot.mkdir(parents=True)
    revision = {
        "candidateId": candidate_id,
        "candidateTreeSha256": "sha256:" + "1" * 64,
        "receipt": {
            "path": "operations/adaptive/candidate-revisions/revision.json",
            "sha256": "sha256:" + "2" * 64,
        },
    }
    experiment = {
        "path": "operations/adaptive/experiments/experiment.json",
        "sha256": "sha256:" + "3" * 64,
    }
    job = {
        "candidate_id": candidate_id,
        "candidate_tree_sha256": revision["candidateTreeSha256"],
        "candidate_revision": revision["receipt"],
        "experiment": experiment,
        "job_id": job_id,
        "tool": "tools/example.py",
    }
    environment = {
        "GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID": candidate_id,
        "GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT": str(snapshot),
        "GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON": json.dumps(revision),
        "GAMMA_ENWIKI9_EXPERIMENT_JSON": json.dumps(experiment),
    }
    monkeypatch.setattr(
        worker_identity.tempfile, "gettempdir", lambda: str(tmp_path)
    )
    return job, environment


def test_managed_snapshot_environment_authenticates_execed_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    job, environment = managed_fixture(tmp_path, monkeypatch)
    assert worker_identity.managed_snapshot_environment_matches_job(
        job, environment, temporary_directory=tmp_path
    )


@pytest.mark.parametrize(
    "field",
    [
        "GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID",
        "GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT",
        "GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON",
        "GAMMA_ENWIKI9_EXPERIMENT_JSON",
    ],
)
def test_managed_snapshot_environment_rejects_identity_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    job, environment = managed_fixture(tmp_path, monkeypatch)
    environment[field] += "-drift"
    assert not worker_identity.managed_snapshot_environment_matches_job(
        job, environment, temporary_directory=tmp_path
    )


def test_worker_liveness_accepts_snapshot_exec_and_binds_start_ticks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    job, environment = managed_fixture(tmp_path, monkeypatch)
    job["worker_pid"] = os.getpid()
    ticks = worker_identity.proc_start_ticks(os.getpid())
    assert ticks is not None
    job["worker_proc_start_ticks"] = ticks
    monkeypatch.setattr(
        worker_identity, "proc_environment", lambda _pid: environment
    )
    assert worker_identity.worker_pid_matches_job(
        PROJECT, PROJECT / "tools" / "candidate_triage.py", job
    )

    job["worker_proc_start_ticks"] = ticks + 1
    assert not worker_identity.worker_pid_matches_job(
        PROJECT, PROJECT / "tools" / "candidate_triage.py", job
    )


def test_managed_snapshot_environment_rejects_symlink_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    job, environment = managed_fixture(tmp_path, monkeypatch)
    original = Path(environment["GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT"])
    alternate = original.with_name(original.name + "-real")
    original.rename(alternate)
    original.symlink_to(alternate, target_is_directory=True)
    environment["GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT"] = str(original)
    assert not worker_identity.managed_snapshot_environment_matches_job(
        job, environment, temporary_directory=tmp_path
    )


def configure_queue(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lab, "ROOT", tmp_path)
    monkeypatch.setattr(lab, "QUEUE_DIRS", {state: tmp_path / state for state in lab.QUEUE_STATES})
    monkeypatch.setattr(lab, "EXCLUSIVE_FULL1G_PATH", tmp_path / "exclusive.json")
    for path in lab.QUEUE_DIRS.values():
        path.mkdir()


def test_vanished_and_zombie_workers_remain_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    process = subprocess.Popen([sys.executable, "-c", "pass"])
    try:
        os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOWAIT)
        job = {"candidate_id": "gone", "job_id": "gone", "worker_pid": process.pid,
               "worker_proc_start_ticks": worker_identity.proc_start_ticks(process.pid),
               "tool": sys.executable}
        assert lab.running_job_liveness(job) == "unknown"
        process.wait()
        assert lab.running_job_liveness(job) == "unknown"
    finally:
        process.wait()


def test_existing_running_claim_is_never_overwritten(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_queue(tmp_path, monkeypatch)
    original = {"job_id": "same", "candidate_id": "candidate", "state": "running", "worker_pid": 42}
    pending = {"job_id": "same", "candidate_id": "candidate", "state": "pending"}
    running_path = lab.QUEUE_DIRS["running"] / "job.json"
    running_path.write_text(json.dumps(original))
    pending_path = lab.QUEUE_DIRS["pending"] / "job.json"
    pending_path.write_text(json.dumps(pending))
    assert lab.claim_jobs(1) == []
    assert json.loads(running_path.read_text()) == original
    assert pending_path.exists()


def test_concurrent_claimers_claim_candidate_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_queue(tmp_path, monkeypatch)
    for index in range(2):
        (lab.QUEUE_DIRS["pending"] / f"job-{index}.json").write_text(json.dumps(
            {"job_id": f"job-{index}", "candidate_id": "candidate", "state": "pending",
             "execution_mode": "discovery", "resource_budget": discovery_budget()}))
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda _: lab.claim_jobs(1), range(2)))
    assert sum(map(len, claims)) == 1
    assert len(list(lab.QUEUE_DIRS["running"].glob("*.json"))) == 1
    assert len(list(lab.QUEUE_DIRS["pending"].glob("*.json"))) == 1


@pytest.mark.parametrize("lease", ["malformed", json.dumps({"pid": 999999999, "resource_class": "exclusive_full1g"})])
def test_unresolved_lease_blocks_claim_and_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, lease: str) -> None:
    configure_queue(tmp_path, monkeypatch)
    lab.EXCLUSIVE_FULL1G_PATH.write_text(lease)
    monkeypatch.setattr(lab, "resource_ready", lambda **_: (True, {}))
    assert lab.exclusive_lease_state()["state"] == "unknown"
    with pytest.raises(ValueError, match="cannot be validated"):
        lab.claim_jobs(1)
    status = lab.status_payload()
    assert status["safe_to_launch_candidate_gate"] is False
    assert status["exclusive_lease_state"]["state"] == "unknown"


def test_missing_controller_does_not_mean_idle_or_launchable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_queue(tmp_path, monkeypatch)
    (lab.QUEUE_DIRS["running"] / "job.json").write_text(json.dumps(
        {"job_id": "missing", "candidate_id": "candidate", "state": "running", "worker_pid": 999999999}))
    monkeypatch.setattr(lab, "resource_ready", lambda **_: (True, {}))
    status = lab.status_payload()
    assert len(status["unknown_running_jobs"]) == 1
    assert status["active_jobs"] == []
    assert status["safe_to_launch_candidate_gate"] is False


def discovery_budget() -> dict:
    return {"cpus": [2], "memory_bytes": 512 * 1024 * 1024, "scratch_bytes": 1024 * 1024 * 1024,
            "wall_seconds": 5, "swap_bytes": 0, "cgroup_parent": "/sys/fs/cgroup/example"}


def test_unknown_running_ownership_blocks_different_candidate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_queue(tmp_path, monkeypatch)
    (lab.QUEUE_DIRS["running"] / "unknown.json").write_text(json.dumps(
        {"job_id": "unknown", "candidate_id": "old", "state": "running"}))
    pending = lab.QUEUE_DIRS["pending"] / "next.json"
    pending.write_text(json.dumps({"job_id": "next", "candidate_id": "new", "state": "pending",
                                   "execution_mode": "discovery", "resource_budget": discovery_budget()}))
    assert lab.claim_jobs(1) == []
    assert pending.exists()


def test_verified_existing_observer_allows_disjoint_discovery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_queue(tmp_path, monkeypatch)
    (lab.QUEUE_DIRS["running"] / "old.json").write_text(json.dumps(
        {"job_id": "old", "candidate_id": "old", "state": "running"}))
    monkeypatch.setattr(lab, "existing_observer_live_jobs", lambda _rows: ({"old"}, {}))
    (lab.QUEUE_DIRS["pending"] / "next.json").write_text(json.dumps(
        {"job_id": "next", "candidate_id": "new", "state": "pending",
         "execution_mode": "discovery", "resource_budget": discovery_budget()}))
    assert len(lab.claim_jobs(1)) == 1


def test_qualification_requires_calibration() -> None:
    with pytest.raises(ValueError, match="verified host calibration"):
        lab.validate_execution_budget({"execution_mode": "qualification", "resource_budget": discovery_budget()})


def test_existing_guard_must_leave_coordinator_memory() -> None:
    budget = discovery_budget()
    budget["existing_guard"] = {"path": "/sys/fs/cgroup/example/inner", "inode": 12,
                                "memory_bytes": budget["memory_bytes"]}
    with pytest.raises(ValueError, match="coordinator memory budget"):
        lab.validate_execution_budget({"execution_mode": "discovery", "resource_budget": budget})


def test_mode_cli_preserves_explicit_cpu_and_limits() -> None:
    args = lab.build_parser().parse_args(["enqueue", "example", "--mode", "discovery", "--cpu-set", "4-7",
                                         "--memory-limit-bytes", "9999998976", "--disk-limit-bytes", "20000000000",
                                         "--wall-time-limit-seconds", "600"])
    options = lab.execution_options(args)
    assert options["execution_mode"] == "discovery"
    assert options["resource_budget"]["cpus"] == [4, 5, 6, 7]
    assert options["resource_budget"]["memory_bytes"] == 9999998976
    assert options["resource_budget"]["wall_seconds"] == 600


def test_cleanup_failure_preserves_unknown_running_claim(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_queue(tmp_path, monkeypatch)
    job = {"job_id": "still-owned", "candidate_id": "example", "state": "running", "worker_pid": 123,
           "execution_resources": {"cleanup_complete": False}}
    path = lab.QUEUE_DIRS["running"] / "job.json"
    path.write_text(json.dumps(job))
    def fail(*_):
        raise ValueError("owned execution group remains populated")
    monkeypatch.setattr(lab, "_execute_job", fail)
    result = lab.execute_job(path, job)
    assert result["state"] == "running"
    assert result["worker_liveness"] == "unknown"
    assert path.exists()
    assert not list(lab.QUEUE_DIRS["failed"].glob("*.json"))


def calibration_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, wall_seconds: int) -> tuple[dict, dict]:
    import hashlib

    monkeypatch.setattr(lab, "ROOT", tmp_path)
    files = {"plan": tmp_path / "plan.json", "receipt": tmp_path / "receipt.json",
             "verifier": tmp_path / "tools/geekbench5_tryout_calibration_verify_q0_v1.py"}
    for path in files.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n")

    def reference(path: Path) -> dict:
        return {"path": path.relative_to(tmp_path).as_posix(),
                "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()}

    monkeypatch.setattr(lab, "artifact_reference", reference)
    budget = discovery_budget()
    budget.update(wall_seconds=wall_seconds, calibration={role: reference(path) for role, path in files.items()})
    observed: dict = {}

    def verify(argv: list[str], **_kwargs):
        observed["plan_sha256"] = argv[argv.index("--plan-sha256") + 1]
        output = Path(argv[argv.index("--output") + 1])
        output.write_text(json.dumps({"authority_verified": True, "runtime_limit_seconds": 5.0}))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(lab.subprocess, "run", verify)
    return {"execution_mode": "qualification", "resource_budget": budget}, observed


def test_calibration_verifier_receives_bare_sha256(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    job, observed = calibration_fixture(tmp_path, monkeypatch, wall_seconds=5)
    result = lab.validate_qualification_calibration(job)
    assert result["authority_verified"] is True
    bound_digest = job["resource_budget"]["calibration"]["plan"]["sha256"]
    assert bound_digest.startswith("sha256:")
    assert observed["plan_sha256"] == bound_digest.removeprefix("sha256:")


def test_qualification_rejects_wall_budget_above_verified_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    job, _ = calibration_fixture(tmp_path, monkeypatch, wall_seconds=6)
    with pytest.raises(ValueError, match="(?i)(wall|runtime|calibrat)"):
        lab.validate_qualification_calibration(job)


def execution_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, mode: str) -> tuple[dict, Path, dict]:
    from types import SimpleNamespace

    configure_queue(tmp_path, monkeypatch)
    logs = tmp_path / "run_logs"
    logs.mkdir()
    monkeypatch.setattr(lab, "RUN_LOGS", logs)
    monkeypatch.setattr(lab, "validate_qualification_calibration", lambda _job: {})
    monkeypatch.setattr(lab.candidate_revisions, "verify_job_binding", lambda _job: (None, {}))
    monkeypatch.setattr(lab.candidate_revisions, "materialize_revision", lambda _revision, path: path.mkdir())
    monkeypatch.setattr(lab, "materialize_job_scratch_directories", lambda _job: None)
    monkeypatch.setattr(lab, "artifact_reference", lambda _path: {"path": "tools/enwiki9_lab.py", "sha256": "sha256:" + "a" * 64})
    observed: dict = {"waits": [], "releases": []}

    def prepare(job: dict, command: list[str], snapshot: Path):
        observed["snapshot"] = snapshot
        job["execution_resources"] = {"guard_path": "run_logs/guard.json"}
        return command, []

    def wait(_process, job: dict, _handles, *, abort_reason=None) -> int:
        observed["waits"].append({"abort_reason": abort_reason, "snapshot_present": observed["snapshot"].is_dir()})
        job["execution_resources"]["cleanup_complete"] = True
        return 125 if abort_reason else 0

    def acquire(**kwargs):
        observed["lease"] = kwargs
        return SimpleNamespace(record={"lease_id": "lease-id"},
                               release=lambda **release: observed["releases"].append(release))

    monkeypatch.setattr(lab, "prepare_execution_envelope", prepare)
    monkeypatch.setattr(lab, "wait_for_budgeted_worker", wait)
    monkeypatch.setattr(lab.managed_exclusive_lease.ManagedExclusiveLease, "acquire", acquire)
    monkeypatch.setattr(lab.subprocess, "Popen", lambda *_args, **_kwargs: SimpleNamespace(pid=1234))
    monkeypatch.setattr(lab, "_proc_start_ticks", lambda _pid: 9876)
    budget = discovery_budget()
    if mode == "qualification":
        budget["calibration"] = {}
    job = {"candidate_id": "example", "job_id": "example-job", "state": "running", "gate_size": 1,
           "candidate_tree_sha256": "sha256:" + "1" * 64, "candidate_revision": {}, "experiment": {},
           "execution_mode": mode, "resource_budget": budget}
    path = lab.QUEUE_DIRS["running"] / "job.json"
    path.write_text(json.dumps(job))
    return job, path, observed


def test_qualification_lease_receives_bare_runner_sha256(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    job, path, observed = execution_fixture(tmp_path, monkeypatch, mode="qualification")
    result = lab._execute_job(path, job)
    assert result["state"] == "completed"
    assert observed["lease"]["runner_sha256"] == "a" * 64
    assert len(observed["releases"]) == 1
    assert observed["waits"] == [{"abort_reason": None, "snapshot_present": True}]


def test_post_spawn_bookkeeping_failure_cleans_up_before_snapshot_removal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    job, path, observed = execution_fixture(tmp_path, monkeypatch, mode="discovery")
    original_write = lab.atomic_json

    def fail_worker_identity_write(destination: Path, record: dict) -> None:
        if record.get("worker_pid") and not record.get("execution_resources", {}).get("cleanup_complete"):
            raise OSError("injected worker identity receipt failure")
        original_write(destination, record)

    monkeypatch.setattr(lab, "atomic_json", fail_worker_identity_write)
    with pytest.raises(OSError, match="worker identity receipt failure"):
        lab._execute_job(path, job)
    assert observed["waits"] == [{"abort_reason": "worker-bookkeeping-failure", "snapshot_present": True}]
    assert not observed["snapshot"].exists()


@pytest.mark.parametrize("failure", ["read", "kill"])
def test_cleanup_attempts_every_owned_group_after_one_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    from types import SimpleNamespace

    handles = []
    for index in range(2):
        group = tmp_path / str(index)
        group.mkdir()
        descriptor = os.open(group, os.O_RDONLY | os.O_DIRECTORY)
        handles.append({"path": str(group), "descriptor": descriptor, "inode": group.stat().st_ino,
                        "memory_bytes": 1024, "created": True})
    first, second = (handle["descriptor"] for handle in handles)
    killed: list[int] = []
    seen: list[int] = []
    terminated: list[bool] = []

    def populated(descriptor: int) -> bool:
        seen.append(descriptor)
        if descriptor == first and failure == "read":
            raise OSError("injected cgroup read failure")
        return descriptor not in killed

    def write(descriptor: int, name: str, value: str) -> None:
        assert name == "cgroup.kill" and value == "1\n"
        if descriptor == first and failure == "kill":
            raise OSError("injected cgroup kill failure")
        killed.append(descriptor)

    class Worker:
        stopped = False

        def poll(self):
            return 143 if self.stopped else None

        def wait(self, timeout=None):
            if not self.stopped:
                raise subprocess.TimeoutExpired("worker", timeout)
            return 143

        def terminate(self):
            self.stopped = True
            terminated.append(True)

        def kill(self):
            self.stopped = True
            terminated.append(True)

    clock = iter(range(1000))
    monkeypatch.setattr(lab.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(lab.time, "sleep", lambda _delay: None)
    monkeypatch.setattr(lab, "_group_populated", populated)
    monkeypatch.setattr(lab, "_group_write", write)
    job = {"resource_budget": discovery_budget(), "execution_resources": {}}
    try:
        with pytest.raises(RuntimeError):
            lab.wait_for_budgeted_worker(Worker(), job, handles, abort_reason="worker-bookkeeping-failure")
        assert second in seen and second in killed
        assert terminated
        assert job["execution_resources"]["cleanup_complete"] is False
    finally:
        for handle in handles:
            try:
                os.close(handle["descriptor"])
            except OSError:
                pass
