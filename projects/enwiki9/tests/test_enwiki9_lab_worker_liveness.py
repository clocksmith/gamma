from __future__ import annotations

import json
import os
from pathlib import Path
import sys

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
