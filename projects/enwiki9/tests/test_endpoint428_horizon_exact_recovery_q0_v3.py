from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3"
PROGRAM_ROOT = PROJECT / "programs" / CANDIDATE_ID
RUNNER = PROJECT / "tools" / f"{CANDIDATE_ID}.py"
EXPERIMENT = PROJECT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
PLAN = PROJECT / "operations/planning" / f"{CANDIDATE_ID}.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_runner():
    spec = importlib.util.spec_from_file_location("_horizon_exact_recovery_v3", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    try:
        import jsonschema  # noqa: F401

        missing = {}
    except ModuleNotFoundError:
        missing = {"jsonschema": SimpleNamespace()}
    with patch.dict(sys.modules, missing):
        spec.loader.exec_module(module)
    return module


def test_experiment_binds_plan_and_unchanged_exact_analyzer() -> None:
    experiment = json.loads(EXPERIMENT.read_text(encoding="utf-8"))
    inputs = {row["id"]: row for row in experiment["inputs"]}
    assert inputs["exact-recovery-plan"]["sha256"] == f"sha256:{digest(PLAN)}"
    exact = PROGRAM_ROOT / "horizon-retained-analyze-exact.cpp"
    predecessor = (
        PROJECT
        / "programs/endpoint428_horizon_retained_parent_trace_exact_q0_v2"
        / "horizon-retained-analyze-exact.cpp"
    )
    assert exact.read_bytes() == predecessor.read_bytes()
    assert inputs["exact-v2-analyzer"]["sha256"] == f"sha256:{digest(exact)}"


def test_recovery_wrapper_uses_the_actual_cmx21p1_header() -> None:
    runner = load_runner()
    assert runner.BASE.TRACE_MAGIC == bytes.fromhex("434d583231503100")


def test_source_binding_closure_matches_checkout() -> None:
    runner = load_runner()
    receipt = runner.verify_source_binding(PROGRAM_ROOT)
    assert receipt["path"] == f"programs/{CANDIDATE_ID}/source-binding.json"


def test_nonterminal_adoption_refuses_before_any_artifact_hash(monkeypatch) -> None:
    runner = load_runner()
    monkeypatch.setattr(
        runner.BASE,
        "active_adoption_jobs",
        lambda: ["operations/adaptive/running/frozen.json"],
    )

    def forbidden_bind():
        raise AssertionError("snapshot or science binding occurred before dependency gate")

    monkeypatch.setattr(runner, "bind_candidate_snapshot", forbidden_bind)
    with pytest.raises(RuntimeError, match="adoption remains nonterminal"):
        runner.require_reflected_recovery()


def test_legacy_parity_comparison_rejects_one_changed_value() -> None:
    runner = load_runner()
    exact_runner = runner.BASE.V2
    legacy = {
        "active_bytes": runner.BASE.ACTIVE_BYTES,
        "parent_trace_rows": runner.BASE.TRACE_ROWS,
        "parent_truth_bits": 10.0,
        "parent_truth_bits_by_third": [3.0, 3.0, 4.0],
        "coordinate_fnv1a64": "0123456789abcdef",
        "minimum_third_mixture_gain_bits": 1.0,
        "minimum_control_margin_bits": 0.5,
        "arms": {},
    }
    exact = {
        **legacy,
        "legacy_minimum_third_mixture_gain_bits": 1.0,
        "legacy_minimum_control_margin_bits": 0.5,
        "arms": {},
    }
    for arm_id in ("D", "S", "R", "N"):
        legacy["arms"][arm_id] = {
            "raw_truth_bits": 2.0,
            "raw_gain_bits": 8.0,
            "raw_gain_by_third": [2.0, 3.0, 3.0],
            "mixture_truth_bits": 1.5,
            "mixture_gain_bits": 8.5,
            "mixture_gain_by_third": [2.5, 3.0, 3.0],
            "terminal_parent_weight_q63": "42",
        }
        exact["arms"][arm_id] = {
            **legacy["arms"][arm_id],
            "legacy_mixture_truth_bits": 1.5,
            "legacy_mixture_gain_bits": 8.5,
            "legacy_mixture_gain_by_third": [2.5, 3.0, 3.0],
            "terminal_legacy_parent_weight_q63": "42",
            "legacy_exact_kt_identity_pass": True,
        }
    exact_runner.compare_legacy(exact, legacy)
    exact["arms"]["D"]["legacy_mixture_gain_bits"] = 8.4
    with pytest.raises(RuntimeError, match="legacy mixture parity"):
        exact_runner.compare_legacy(exact, legacy)


def test_hash_bound_adoption_reference_is_safely_size_normalized(
    tmp_path: Path, monkeypatch
) -> None:
    runner = load_runner()
    artifact_path = tmp_path / "terminal-source.json"
    artifact_path.write_text("{}\n", encoding="utf-8")
    record = {
        "id": "terminal-source",
        "path": artifact_path.name,
        "sha256": f"sha256:{digest(artifact_path)}",
    }
    monkeypatch.setattr(runner, "PROJECT", tmp_path)
    normalized = runner.referenced_artifact_with_size(
        {"artifacts": [record]}, "terminal-source"
    )
    assert normalized["bytes"] == artifact_path.stat().st_size
    assert record.get("bytes") is None


def test_foundational_failure_invalidates_without_retiring_science(
    tmp_path: Path, monkeypatch
) -> None:
    runner = load_runner()
    monkeypatch.setattr(runner, "RESULT", tmp_path)
    monkeypatch.setattr(runner, "_reflection_artifact", {"path": "reflection.json"})
    captured = {}

    def capture(_path: Path, value: dict) -> None:
        captured.update(value)

    monkeypatch.setattr(runner, "_base_write_json_exclusive", capture)
    gates = {
        "recoveryIntegrityPass": True,
        "immutableIdentityPass": False,
        "deterministicBuildPass": True,
        "completeActivePopulationPass": True,
        "completeParentTracePass": True,
        "legacyABPass": True,
        "exactABPass": True,
        "legacyCrosscheckPass": True,
        "arbitraryPrecisionFixturePass": True,
        "analysisResourcePass": True,
    }
    runner.write_json_with_reflection(
        tmp_path / "decision.json",
        {
            "inputs": {},
            "gates": gates,
            "verdict": "retire_endpoint428_physical_horizon_a",
            "promotion_authorized": False,
        },
    )
    assert captured["verdict"] == (
        "invalidate_endpoint428_horizon_exact_recovery_attempt"
    )


def test_exact_arithmetic_fixture_matches_arbitrary_precision(tmp_path: Path) -> None:
    binary = tmp_path / "fixture"
    vectors = tmp_path / "vectors.tsv"
    receipt = tmp_path / "receipt.json"
    subprocess.run(
        [
            "/usr/bin/x86_64-linux-gnu-g++-15",
            "-std=c++17",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-fno-fast-math",
            "-ffp-contract=off",
            "-march=x86-64",
            "-mtune=generic",
            "-Wl,--build-id=none",
            str(PROGRAM_ROOT / "horizon-exact-fixture.cpp"),
            "-o",
            str(binary),
        ],
        cwd=PROJECT,
        check=True,
    )
    subprocess.run([str(binary), str(vectors)], cwd=PROJECT, check=True)
    subprocess.run(
        [
            "/usr/bin/python3",
            str(PROGRAM_ROOT / "horizon-exact-reference.py"),
            "--native",
            str(vectors),
            "--receipt",
            str(receipt),
        ],
        cwd=PROJECT,
        check=True,
    )
    value = json.loads(receipt.read_text(encoding="utf-8"))
    assert value["candidate_id"] == CANDIDATE_ID
    assert value["arbitrary_precision_identity_pass"] is True
    assert value["terminal_pass"] is True
