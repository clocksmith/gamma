from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import enwiki9_status_receipt as status_receipt  # noqa: E402


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

    def matches(value: dict) -> bool:
        observed.append(value)
        return True

    monkeypatch.setattr(
        status_receipt.enwiki9_lab, "worker_pid_matches_job", matches
    )
    result = status_receipt.adaptive_running_jobs_state()
    assert observed == [job]
    assert result["running_job_count"] == 1
    assert result["running_jobs"][0]["worker_pid_live"] is True
