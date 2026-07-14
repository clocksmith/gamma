from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "projects/enwiki9/tools/cmix21_gate_decider.py"
SPEC = importlib.util.spec_from_file_location("cmix21_gate_decider", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_nonzero_terminal_guard_without_driver_result_is_a_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    candidate = "cmix21_ppmd20352k_test_v1"
    scope = 100_000_000
    results = tmp_path / "projects/enwiki9/results"
    programs = tmp_path / "projects/enwiki9/programs"
    guard_path = results / candidate / "ppmd20352k_100000000_determinism_rss_guard.json"
    guard_path.parent.mkdir(parents=True)
    guard_path.write_text(
        json.dumps(
            {
                "status": "complete",
                "returncode": -15,
                "rss_guard_exceeded": False,
                "limit_kib": 10_485_760,
                "max_sampled_single_rss_kib": 8_897_320,
                "max_sampled_tree_rss_kib": 9_017_948,
                "command": ["driver.py", "--limit", str(scope)],
            }
        )
    )
    monkeypatch.setattr(MODULE, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(MODULE, "RESULTS", results)
    monkeypatch.setattr(MODULE, "PROGRAMS", programs)

    decision = MODULE.decide(candidate, scope, guard_path, 128)

    assert decision["verdict"] == "guard_returncode_fail"
    assert decision["next_action"] == "record_guard_failure"
    command = decision["record_failure_command"]
    assert "--guard-only" in command
    assert command[command.index("--scope") + 1] == str(scope)
    assert "--result" not in command
    assert decision["apply_terminal_command"][-2:] == ["--apply-terminal", "--normalize"]


def test_zero_terminal_guard_without_driver_result_remains_incomplete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    candidate = "cmix21_ppmd20352k_test_v1"
    scope = 100_000_000
    results = tmp_path / "projects/enwiki9/results"
    guard_path = results / candidate / "ppmd20352k_100000000_determinism_rss_guard.json"
    guard_path.parent.mkdir(parents=True)
    guard_path.write_text(
        json.dumps(
            {
                "status": "complete",
                "returncode": 0,
                "rss_guard_exceeded": False,
                "command": ["driver.py", "--limit", str(scope)],
            }
        )
    )
    monkeypatch.setattr(MODULE, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(MODULE, "RESULTS", results)
    monkeypatch.setattr(MODULE, "PROGRAMS", tmp_path / "projects/enwiki9/programs")

    decision = MODULE.decide(candidate, scope, guard_path, 128)

    assert decision["verdict"] == "incomplete"
    assert decision["next_action"] == "wait_for_gate_receipts"
