from __future__ import annotations

import json
from pathlib import Path

import pytest

from projects.enwiki9.tools import enwiki9_reflections as reflections


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def configure_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    adaptive = tmp_path / "operations" / "adaptive"
    monkeypatch.setattr(reflections, "ROOT", tmp_path)
    monkeypatch.setattr(reflections, "ADAPTIVE", adaptive)
    monkeypatch.setattr(reflections, "REFLECTIONS", adaptive / "reflections")
    monkeypatch.setattr(
        reflections.research_contracts,
        "validate_search_policy",
        lambda: {"decisionRank": {"missing": 0}},
    )


def proposal(candidate_id: str | None = "candidate_v1") -> dict:
    proposal_id = candidate_id or "undeveloped_v1"
    value = {
        "schema": "gamma.enwiki9.algorithm-proposal.v2",
        "proposal_id": proposal_id,
        "parent": None,
        "experiment": {"path": f"{proposal_id}.json", "sha256": "unused"},
        "expected_savings_bytes": 1,
        "max_program_bytes": 0,
        "priority": 1,
    }
    if candidate_id is not None:
        value["candidate_id"] = candidate_id
    return value


def rank_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    value: dict,
) -> dict:
    experiment = {
        "proposalId": value["proposal_id"],
        "budget": {},
        "search": {},
    }
    monkeypatch.setattr(
        reflections.research_contracts,
        "validate_project_reference",
        lambda *_args, **_kwargs: (tmp_path / "experiment.json", experiment),
    )
    monkeypatch.setattr(reflections, "iter_reflections", lambda **_kwargs: [])
    return reflections.rank_proposals([value])[0]


def candidate_meta(
    tmp_path: Path, status: str, reflected: list[str] | None = None
) -> None:
    write_json(
        tmp_path / "programs" / "candidate_v1" / "meta.json",
        {
            "status": status,
            "measured": {
                "reflections": {job_id: {} for job_id in (reflected or [])}
            },
        },
    )


def job(tmp_path: Path, state: str, job_id: str) -> None:
    write_json(
        tmp_path
        / "operations"
        / "adaptive"
        / state
        / f"000_{job_id}.json",
        {"candidate_id": "candidate_v1", "job_id": job_id, "state": state},
    )


def bind_reflection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, job_id: str) -> Path:
    job_path = tmp_path / "operations/adaptive/failed" / f"000_{job_id}.json"
    path = tmp_path / "operations/adaptive/reflections" / f"{job_id}.json"
    write_json(path, {"candidateId": "candidate_v1", "job": reflections.reference(job_path)})
    meta_path = tmp_path / "programs/candidate_v1/meta.json"
    metadata = json.loads(meta_path.read_text())
    metadata["measured"]["reflections"][job_id] = reflections.reference(path)
    write_json(meta_path, metadata)

    def validate(receipt: Path, *, verify_files: bool) -> None:
        assert receipt == path
        assert verify_files is True

    monkeypatch.setattr(reflections.research_contracts, "validate_artifact", validate)
    return path


@pytest.mark.parametrize(
    "status", ["blocked_dependency", "measured_negative", "retired"]
)
def test_non_actionable_candidate_status_blocks_ranking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    configure_root(tmp_path, monkeypatch)
    candidate_meta(tmp_path, status)

    row = rank_one(tmp_path, monkeypatch, proposal())

    assert row["eligible"] is False
    assert row["candidateLifecycle"]["schedulingBlock"] == {
        "code": "candidate-status-non-actionable",
        "candidateStatus": status,
    }


@pytest.mark.parametrize("state", ["pending", "running"])
def test_live_job_blocks_duplicate_candidate_scheduling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    configure_root(tmp_path, monkeypatch)
    candidate_meta(tmp_path, "candidate")
    job(tmp_path, state, "20260904T000000Z_live")

    row = rank_one(tmp_path, monkeypatch, proposal())

    assert row["eligible"] is False
    assert row["candidateLifecycle"]["schedulingBlock"] == {
        "code": "candidate-already-scheduled",
        "jobId": "20260904T000000Z_live",
        "queueState": state,
    }


def test_latest_terminal_job_requires_reflection_before_rescheduling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_root(tmp_path, monkeypatch)
    candidate_meta(tmp_path, "candidate", ["20260903T000000Z_reflected"])
    job(tmp_path, "completed", "20260903T000000Z_reflected")
    job(tmp_path, "failed", "20260904T000000Z_unreflected")

    row = rank_one(tmp_path, monkeypatch, proposal())

    assert row["eligible"] is False
    assert row["candidateLifecycle"]["schedulingBlock"] == {
        "code": "terminal-job-awaiting-reflection",
        "jobId": "20260904T000000Z_unreflected",
        "queueState": "failed",
    }


@pytest.mark.parametrize("status", ["candidate", "active"])
def test_reflected_terminal_successor_remains_actionable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    configure_root(tmp_path, monkeypatch)
    job_id = "20260904T000000Z_reflected"
    candidate_meta(tmp_path, status, [job_id])
    job(tmp_path, "failed", job_id)
    bind_reflection(tmp_path, monkeypatch, job_id)

    row = rank_one(tmp_path, monkeypatch, proposal())

    assert row["eligible"] is True
    assert row["candidateLifecycle"]["schedulingBlock"] is None
    assert row["candidateLifecycle"]["latestTerminalJob"]["jobId"] == job_id


@pytest.mark.parametrize("replacement", ["reflection", "job", "validation_failure"])
def test_replaced_or_invalid_terminal_evidence_cannot_reschedule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, replacement: str,
) -> None:
    configure_root(tmp_path, monkeypatch)
    job_id = "20260904T000000Z_reflected"
    candidate_meta(tmp_path, "candidate", [job_id])
    job(tmp_path, "failed", job_id)
    path = bind_reflection(tmp_path, monkeypatch, job_id)
    if replacement == "reflection":
        path.write_text(path.read_text() + "\n")
    elif replacement == "job":
        job_path = tmp_path / "operations/adaptive/failed" / f"000_{job_id}.json"
        job_path.write_text(job_path.read_text() + "\n")
    else:
        def invalid(*_args, **_kwargs):
            raise ValueError("bound evidence digest differs")
        monkeypatch.setattr(reflections.research_contracts, "validate_artifact", invalid)
    row = rank_one(tmp_path, monkeypatch, proposal())
    assert row["eligible"] is False
    assert row["candidateLifecycle"]["schedulingBlock"]["code"] == "terminal-job-awaiting-reflection"
    assert row["candidateLifecycle"]["terminalReflectionError"]


def test_metadata_reflection_key_without_receipt_is_not_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_root(tmp_path, monkeypatch)
    candidate_meta(tmp_path, "candidate", ["job"])
    job(tmp_path, "failed", "job")
    row = rank_one(tmp_path, monkeypatch, proposal())
    assert row["eligible"] is False


def test_undeveloped_proposal_has_no_candidate_lifecycle_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_root(tmp_path, monkeypatch)

    row = rank_one(tmp_path, monkeypatch, proposal(None))

    assert row["eligible"] is True
    assert row["candidateLifecycle"] == {
        "candidateId": None,
        "candidateStatus": None,
        "schedulingBlock": None,
        "liveJobs": [],
        "latestTerminalJob": None,
    }
