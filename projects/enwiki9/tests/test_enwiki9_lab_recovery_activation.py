from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest


PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import enwiki9_lab as lab  # noqa: E402


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def reference(root: Path, path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}",
    }


def recovery_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    candidate_id = "source_recovery_v1"
    result_path = tmp_path / "results" / candidate_id / "result.json"
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "candidateId": candidate_id,
        "decision": "authorize-successor",
        "promotionPass": True,
        "killPass": False,
    }
    write_json(result_path, result)
    result_reference = reference(tmp_path, result_path)
    reflection_path = (
        tmp_path
        / "operations"
        / "adaptive"
        / "reflections"
        / "job.json"
    )
    reflection = {
        "candidateId": candidate_id,
        "evidence": [result_reference],
        "validity": {"valid": True, "classification": "valid"},
        "decision": {
            "verdict": "next-gate",
            "promotionPredicatesPass": True,
            "killPredicatesPass": False,
        },
    }
    write_json(reflection_path, reflection)
    monkeypatch.setattr(lab, "ROOT", tmp_path)
    monkeypatch.setattr(
        lab.parent_qualification_v3,
        "regular_file",
        lambda path, _label: Path(path),
    )
    monkeypatch.setattr(
        lab.research_contracts, "validate_artifact", lambda _path: None
    )
    monkeypatch.setattr(
        lab,
        "artifact_reference",
        lambda path: reference(tmp_path, Path(path)),
    )
    requirement = {
        "kind": "reflected_terminal_recovery",
        "candidate_id": candidate_id,
        "result_path": result_reference["path"],
        "required_decision": "authorize-successor",
        "required_promotion_pass": True,
        "required_kill_pass": False,
        "required_valid_reflection": True,
    }
    return requirement, result_reference["path"], reflection_path.relative_to(
        tmp_path
    ).as_posix()


def test_reflected_recovery_activation_binds_result_and_reflection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    requirement, result_text, reflection_text = recovery_fixture(
        tmp_path, monkeypatch
    )
    verified = lab._verify_reflected_terminal_recovery_activation(
        requirement, {result_text, reflection_text}
    )
    assert verified["kind"] == "reflected_terminal_recovery"
    assert verified["result_decision"] == "authorize-successor"
    assert verified["reflection_decision"] == "next-gate"
    assert verified["promotion_pass"] is True
    assert verified["kill_pass"] is False


def test_reflected_recovery_activation_requires_reflection_as_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    requirement, result_text, _reflection_text = recovery_fixture(
        tmp_path, monkeypatch
    )
    with pytest.raises(ValueError, match="must include the validated recovery reflection"):
        lab._verify_reflected_terminal_recovery_activation(
            requirement, {result_text}
        )


def test_developed_dormant_proposal_can_be_activated_after_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proposal_path = tmp_path / "proposal.json"
    write_json(
        proposal_path,
        {
            "proposal_id": "recovery_successor_v1",
            "operational_status": "dormant_dependency",
            "activation_requirements": [],
        },
    )
    monkeypatch.setattr(
        lab,
        "proposal_path",
        lambda _proposal_id: ("developed", proposal_path),
    )
    activated = lab.activate_proposal(
        "recovery_successor_v1", ["results/bound-receipt.json"]
    )
    assert activated["operational_status"] == "actionable"
    assert json.loads(proposal_path.read_text())["operational_status"] == "actionable"


def test_enqueue_rejects_dormant_candidate_before_creating_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(lab, "ensure_layout", lambda: None)
    monkeypatch.setattr(lab, "require_no_exclusive_lease", lambda: None)
    monkeypatch.setattr(lab, "candidate_meta", lambda _candidate_id: {})
    monkeypatch.setattr(
        lab, "require_terminal_reflections", lambda _candidate_id, _action: None
    )
    monkeypatch.setattr(
        lab,
        "candidate_proposal",
        lambda _candidate_id: (
            Path("proposal.json"),
            {
                "proposal_id": "dormant_v1",
                "operational_status": "dormant_dependency",
            },
        ),
    )
    with pytest.raises(ValueError, match="cannot be enqueued"):
        lab.enqueue_job(
            candidate_id="dormant_v1",
            gate_size=1,
            priority=1,
            archive_ceiling=None,
            purpose="diagnostic",
            force=False,
            tags=[],
            experiment=None,
        )


@pytest.mark.parametrize("path_text", ["../outside.json", "/tmp/outside.json"])
def test_activation_evidence_must_be_project_relative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, path_text: str
) -> None:
    monkeypatch.setattr(lab, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="not project-relative"):
        lab._activation_project_file(path_text, "evidence")
