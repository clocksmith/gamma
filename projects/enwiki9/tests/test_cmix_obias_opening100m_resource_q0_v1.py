from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
sys.path.insert(0, str(TOOLS))

import cmix_obias_source_ppm_rss_env8192_opening100m_resource_q0_v1 as gate  # noqa: E402
import cmix_obias_source_ppm_rss_env8192_opening100m_resource_q0_v1_verify as verifier  # noqa: E402


PLAN_PATH = (
    PROJECT
    / "operations/planning/cmix_obias_source_ppm_rss_env8192_opening100m_resource_q0_v1.json"
)
STAGE_PATH = TOOLS / "cmix_obias_source_ppm_rss_env8192_opening100m_resource_q0_v1_stage.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_plan() -> dict:
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def load_stage():
    specification = importlib.util.spec_from_file_location("opening100m_stage_test", STAGE_PATH)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_plan_binds_every_existing_artifact() -> None:
    plan = load_plan()
    assert plan["$schema"] == gate.PLAN_SCHEMA
    assert plan["candidate_id"] == gate.CANDIDATE_ID
    for record in plan["artifacts"].values():
        path = Path(record["path"])
        if not path.is_absolute():
            path = PROJECT / path
        assert path.stat().st_size == record["bytes"]
        assert sha256(path) == record["sha256"]


def test_static_plan_accepts_exact_identity_antecedent() -> None:
    plan, paths = gate.static_plan(PLAN_PATH)
    assert plan["scope_bytes"] == 100_000_000
    assert paths["coordinator"] == Path(gate.__file__).resolve(strict=True)
    identity = json.loads(paths["identity_decision"].read_text(encoding="utf-8"))
    assert identity["terminal_pass"] is True
    assert identity["separately_frozen_100m_experiment_required"] is True


def test_decode_stage_argv_binds_fresh_archive() -> None:
    gate.V3.STAGE_PATH = STAGE_PATH
    archive = {"path": "/tmp/fresh-archive", "bytes": 123, "sha256": "a" * 64}
    mode, ppm, argv = gate.stage_argv(
        "E-decode",
        Path("/tmp/result"),
        Path("/tmp/work"),
        {"path": "/tmp/population"},
        {"path": "/tmp/package"},
        {"path": "/tmp/head"},
        archive,
    )
    assert mode == "decode"
    assert ppm == "8192"
    assert argv[-6:] == [
        "--archive",
        archive["path"],
        "--archive-bytes",
        "123",
        "--archive-sha256",
        "a" * 64,
    ]


def guard_fixture() -> tuple[dict, dict]:
    label = f"{gate.CANDIDATE_ID}-e_a"
    command = ["stage", "--arm", "E-A"]
    cgroup = Path("/sys/fs/cgroup/example-e-a")
    scratch = Path("/disk/scratch")
    result = Path("/disk/result")
    marker = result / "e_a/phase-markers.jsonl"
    value = {
        "schema": gate.BASE.GUARD_SCHEMA,
        "status": "complete",
        "returncode": 0,
        "label": label,
        "phase": "identity",
        "command": command,
        "command_sha256": gate.BASE.command_sha256(command),
        "limit_kib": gate.MEMORY_LIMIT_KIB,
        "official_decimal_limit_kib": gate.MEMORY_LIMIT_KIB,
        "temporary_disk_limit_bytes": gate.DISK_LIMIT_BYTES,
        "max_logical_cpus": 1,
        "wall_time_limit_seconds": None,
        "scratch_paths": [str(scratch), str(result)],
        "phase_marker_path": str(marker),
        "cgroup": {
            "path": str(cgroup),
            "joined_before_exec": True,
            "requested_memory_max_bytes": gate.MEMORY_MAX_BYTES,
            "memory_max_bytes": gate.MEMORY_MAX_BYTES - 1024,
            "memory_swap_max_bytes": 0,
        },
        "measurements": {"complete": True},
        "guards": {"failed": False},
        "cgroup_events": {"delta": {"max": 0, "oom": 0, "oom_kill": 0}},
        "phase_markers": [
            {"phase": "opening100m_e_a", "event": "start"},
            {"phase": "opening100m_e_a", "event": "end"},
        ],
        "peaks": {
            "max_sampled_tree_rss_kib": gate.MEMORY_LIMIT_KIB - 1,
            "max_observed_process_vmhwm_kib": gate.MEMORY_LIMIT_KIB - 1,
            "cgroup_memory_peak_bytes": gate.MEMORY_MAX_BYTES - 1,
            "max_sampled_scratch_logical_bytes": gate.DISK_LIMIT_BYTES - 1,
            "max_sampled_scratch_allocated_bytes": gate.DISK_LIMIT_BYTES - 1,
        },
    }
    arguments = {
        "label": label,
        "phase": "identity",
        "command": command,
        "cgroup": cgroup,
        "scratch": scratch,
        "result": result,
        "marker": marker,
        "score": None,
    }
    return value, arguments


def test_strict_guard_accepts_exact_100m_fixture_and_rejects_swap() -> None:
    value, arguments = guard_fixture()
    passed, errors = gate.strict_guard_pass(value, **arguments)
    assert passed and errors == []
    value["cgroup"]["memory_swap_max_bytes"] = 1
    passed, errors = gate.strict_guard_pass(value, **arguments)
    assert not passed and "zero-swap" in errors


def test_terminal_empty_affinity_sample_is_valid_only_after_clean_success() -> None:
    live = {
        "allowed_cpu_union": [2],
        "processes": [{"allowed_cpus": [2], "comm": "cmix"}],
    }
    empty = {
        "allowed_cpu_union": [],
        "processes": [],
        "tree_rss_kib": 0,
        "tree_live_threads": 0,
    }
    guard = {
        "peak_sample": live,
        "peak_tree_sample": live,
        "latest_sample": empty,
        "status": "complete",
        "returncode": 0,
        "measurements": {"affinity_complete": True, "process_tree_rss_complete": True},
        "guards": {"measurement_incomplete": False},
        "peaks": {"max_sampled_allowed_cpu_count": 1},
    }
    assert gate.affinity_samples_pass(guard, 2, "encode")
    guard["returncode"] = 1
    assert not gate.affinity_samples_pass(guard, 2, "encode")


def test_manifest_contract_includes_zombie_safe_execution_receipts() -> None:
    expected = gate.expected_result_paths()
    for arm in ("p", "e_a", "e_b", "e_decode"):
        assert f"{arm}/execution.json" in expected
    assert "e_decode/enwik9_uncompressed" in expected
    assert len(expected) == 42
    assert verifier.expected_paths() == expected


def test_plan_binds_independent_verifier_and_explicit_digest_command() -> None:
    plan = load_plan()
    record = plan["artifacts"]["verifier"]
    assert record == {
        "path": "tools/cmix_obias_source_ppm_rss_env8192_opening100m_resource_q0_v1_verify.py",
        "bytes": Path(verifier.__file__).stat().st_size,
        "sha256": sha256(Path(verifier.__file__)),
    }
    command = plan["commands"]["verify"]
    assert command[1] == record["path"]
    assert command[command.index("--plan-sha256") + 1] == "<required-committed-plan-sha256>"


def test_independent_verifier_accepts_only_singleton_stage_affinity() -> None:
    live = {
        "allowed_cpu_union": [2],
        "processes": [{"allowed_cpus": [2], "comm": "cmix"}],
    }
    empty = {
        "allowed_cpu_union": [],
        "processes": [],
        "tree_rss_kib": 0,
        "tree_live_threads": 0,
    }
    guard = {
        "peak_sample": live,
        "peak_tree_sample": live,
        "latest_sample": empty,
        "status": "complete",
        "returncode": 0,
        "measurements": {"affinity_complete": True, "process_tree_rss_complete": True},
        "guards": {"measurement_incomplete": False},
        "peaks": {"max_sampled_allowed_cpu_count": 1},
    }
    assert verifier.affinity_samples_pass(guard, 2, "encode")
    guard["peak_tree_sample"] = {
        "allowed_cpu_union": [2, 3],
        "processes": [{"allowed_cpus": [2, 3], "comm": "cmix"}],
    }
    assert not verifier.affinity_samples_pass(guard, 2, "encode")


def test_stage_reuses_passed_zombie_lifecycle_classifier() -> None:
    stage = load_stage()
    telemetry = stage.load_base()
    result = telemetry.lifecycle_validation()
    assert result["passed"] is True
    assert len(result["cases"]) == 25


def test_plan_never_claims_100m_full_corpus_authority() -> None:
    plan = load_plan()
    assert plan["objective_credit_bytes"] == 0
    assert plan["runtime_gate"]["projection_authority"] == "reject_only"
    assert plan["runtime_gate"]["full_corpus_qualification"] is False
    assert plan["terminal_policy"]["promotion_authorized_directly"] is False
