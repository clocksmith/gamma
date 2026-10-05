from __future__ import annotations

import json
import datetime as dt
import hashlib
from pathlib import Path
import sys

import pytest


PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import enwiki9_status_receipt as status_receipt  # noqa: E402


def test_enveloped_job_views_reuse_exact_guard_identity(tmp_path, monkeypatch):
    import enwiki9_lab as lab
    import enwiki9_ledger as ledger
    running = tmp_path / "operations/adaptive/running"
    running.mkdir(parents=True)
    job = {"job_id": "guarded", "candidate_id": "candidate", "worker_pid": 1234,
           "execution_resources": {"guard_command_sha256": "bound-command"},
           "execution_mode": "discovery", "resource_budget": {"cpus": [2]}}
    (running / "guarded.json").write_text(json.dumps(job))
    seen = []
    monkeypatch.setattr(lab, "worker_pid_matches_job", lambda row: seen.append(row) or True)
    monkeypatch.setattr(status_receipt, "ROOT", tmp_path)
    monkeypatch.setattr(status_receipt, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(status_receipt.worker_identity, "worker_pid_matches_job",
                        lambda *args: pytest.fail("enveloped job used legacy matcher"))
    state = status_receipt.adaptive_running_jobs_state()
    assert state["running_jobs"][0]["liveness"] == "live"
    assert state["running_jobs"][0]["resource_budget"] == {"cpus": [2]}
    assert state["running_jobs"][0]["execution_resources"] == job["execution_resources"]
    assert ledger.live_job(job, tmp_path)["state"] == "live"
    assert seen == [job, job]


@pytest.mark.parametrize("failure", [None, "stale", "label", "cgroup", "terminal", "unverified", "escape"])
def test_live_resource_receipt_requires_registered_owner(tmp_path, monkeypatch, failure):
    monkeypatch.setattr(status_receipt, "ROOT", tmp_path)
    monkeypatch.setattr(status_receipt, "REPO_ROOT", tmp_path)
    path = tmp_path / "guard.json"
    guard = {"schema": "gamma.enwiki9.resource-guard-receipt.v3", "status": "running",
             "label": "job", "cgroup": {"inode": 7, "path": "/cgroup/job", "requested_memory_max_bytes": 12884901888},
             "peaks": {"max_sampled_single_rss_kib": 6000000},
             "guards": {"rss_guard_exceeded": False}, "sample_count": 11}
    job = {"candidate_id": "donor", "job_id": "job", "worker_pid_live": True,
           "execution_mode": "discovery", "timing_authority": "diagnostic",
           "execution_resources": {"guard_path": "guard.json", "cgroup_inode": 7, "cgroup_path": "/cgroup/job"}}
    if failure == "label": guard["label"] = "unrelated-job"
    if failure == "cgroup": guard["cgroup"]["inode"] = 8
    if failure == "terminal": guard["status"] = "completed"
    if failure == "unverified": job["worker_pid_live"] = False
    if failure == "escape": job["execution_resources"]["guard_path"] = "../guard.json"
    path.write_text(json.dumps(guard))
    if failure == "stale":
        import os
        os.utime(path, (1, 1))
    gate = status_receipt.live_adaptive_resource_gate(job)
    assert gate["verdict"] == "running"
    assert "no score or qualification" in gate["terminal_authority"]
    assert gate["timing_authority"] == "diagnostic"
    if failure is None:
        assert gate["rss_guard_status"] == "running"
        assert gate["sample_count"] == 11
        assert gate["max_sampled_single_rss_kib"] == 6000000
        assert gate["resource_guard_declared_limit_bytes"] == 12884901888
        assert gate["rss_guard_json_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    else:
        assert "rss_guard_status" not in gate
        assert "max_sampled_single_rss_kib" not in gate


def test_adaptive_status_reuses_managed_worker_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    running = tmp_path / "operations" / "adaptive" / "running"
    running.mkdir(parents=True)
    job = {
        "job_id": "job-id",
        "candidate_id": "candidate-id",
        "gate_size": 17,
        "state": "running",
        "worker_pid": 1234,
    }
    (running / "job.json").write_text(
        json.dumps(job) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(status_receipt, "ROOT", tmp_path)
    monkeypatch.setattr(status_receipt, "REPO_ROOT", tmp_path)
    observed: list[dict] = []

    def matches(_root: Path, _triage: Path, value: dict) -> bool:
        observed.append(value)
        return True

    monkeypatch.setattr(
        status_receipt.worker_identity, "worker_pid_matches_job", matches
    )
    result = status_receipt.adaptive_running_jobs_state()
    assert observed == [job]
    assert result["running_job_count"] == 1
    assert result["running_jobs"][0]["worker_pid_live"] is True


def observer_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict, Path, Path]:
    monkeypatch.setattr(status_receipt, "ROOT", tmp_path)
    monkeypatch.setattr(status_receipt, "REPO_ROOT", tmp_path)

    def write(name: str, data: dict) -> dict:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        return {"path": name, "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()}

    experiment = write("source-experiment.json", {"population": {"scopeBytes": 1000000000, "scopeSymbols": 17, "unit": "selected opportunity"}})
    source = {"candidate_id": "source", "job_id": "source-job", "gate_size": 17, "experiment": experiment, "state": "running"}
    source_ref = write("source-job.json", source)
    identities = {role: {"pid": pid, "start_ticks": 7, "cmdline_sha256": "a" * 64} for role, pid in [("wrapper", 1), ("cmix", 2)]}
    identities["boot_id"] = "fixture"
    plan = write("plan.json", {"candidate_id": "observer", "source_job": {"job_id": "source-job", "running_record": source_ref}, "adopted_processes": identities})
    observer_exp = write("observer-experiment.json", {"inputs": [{"id": "adoption-plan", **plan}]})
    progress = {"schema": "gamma.enwiki9.endpoint428-horizon-orphan-adoption-progress.v1", "candidateId": "observer", "sourceJobId": "source-job", "state": "observing", "updatedUtc": dt.datetime.now(dt.timezone.utc).isoformat(), "scienceAccessedBeforeTerminal": False, "continuousResourceProofPass": False, "traceBytes": 1234, "expectedTraceBytes": 10364777488, "lastSample": {"processes": {role: {"pid": values["pid"], "startTicks": values["start_ticks"], "cmdlineSha256": values["cmdline_sha256"]} for role, values in identities.items() if isinstance(values, dict)}}}
    progress_ref = write("results/observer/progress.json", progress)
    observer = {"candidate_id": "observer", "job_id": "observer-job", "experiment": observer_exp, "worker_pid_live": True}
    monkeypatch.setattr(status_receipt, "adopted_process_identity", lambda *_: True)
    return {"running_jobs": [source, observer]}, tmp_path / progress_ref["path"], tmp_path / source_ref["path"]


def test_existing_observer_attributes_source_without_resource_or_launch_credit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    adaptive, _, _ = observer_fixture(tmp_path, monkeypatch)
    gate = status_receipt.existing_horizon_observer_state(adaptive)
    assert gate["candidate"] == "source"
    assert gate["scope_bytes"] == 1000000000
    assert gate["verdict"] == "running"
    assert gate["observer_progress"]["continuousResourceProofPass"] is False
    action = status_receipt.operator_action({"recorded_running_job_count": 2}, gate)
    assert action["safe_to_launch_gate"] is False
    assert action["action"] == "wait_for_existing_observer"


@pytest.mark.parametrize("failure", ["stale", "source_replaced", "process_unverified"])
def test_unresolved_observer_evidence_never_authorizes_launch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    adaptive, progress_path, source_path = observer_fixture(tmp_path, monkeypatch)
    if failure == "stale":
        progress = json.loads(progress_path.read_text())
        progress["updatedUtc"] = "2000-01-01T00:00:00+00:00"
        progress_path.write_text(json.dumps(progress))
    elif failure == "source_replaced":
        source_path.write_text(source_path.read_text() + "\n")
    else:
        monkeypatch.setattr(status_receipt, "adopted_process_identity", lambda *_: False)
    gate = status_receipt.existing_horizon_observer_state(adaptive)
    assert status_receipt.operator_action({"recorded_running_job_count": 2}, gate)["safe_to_launch_gate"] is False
    if failure == "source_replaced":
        assert gate is None
    elif failure == "process_unverified":
        assert gate["verdict"] == "running_unverified"
