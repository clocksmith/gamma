from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest


PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
sys.path.insert(0, str(TOOLS))

import geekbench5_tryout_calibration_q0_v1 as producer  # noqa: E402
import geekbench5_tryout_calibration_verify_q0_v1 as verifier  # noqa: E402
import geekbench5_tryout_calibration_worker_q0_v1 as worker  # noqa: E402


PLAN_PATH = PROJECT / "operations/planning/geekbench5_5_5_1_tryout_calibration_q0_v1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_plan() -> dict:
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def test_plan_binds_exact_local_implementations() -> None:
    plan = load_plan()
    assert plan["$schema"] == producer.PLAN_SCHEMA
    assert plan["candidate_id"] == producer.CANDIDATE == worker.CANDIDATE == verifier.CANDIDATE
    for name in ("producer", "worker", "verifier", "managed_lease", "lease_verifier"):
        record = plan["implementation"][name]
        path = PROJECT / record["path"]
        assert path.stat().st_size == record["bytes"]
        assert sha256(path) == record["sha256"]


def test_plan_keeps_benchmark_network_isolated_and_conservative() -> None:
    plan = load_plan()
    benchmark = plan["benchmark"]
    assert benchmark["repetitions"] == 3
    assert benchmark["selection_rule"] == "maximum valid single-core score"
    assert benchmark["command_tail"][-1] == "--cpu"
    assert "--net" in benchmark["command_tail"]
    assert plan["resources"]["selected_process_tree_allowed_cpus"] == [2]
    assert benchmark["quiet_cpus"] == [2, 18]
    assert plan["terminal_policy"]["cmix_100m_successor_authorized_directly"] is False


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Geekbench 5.5.1\nSingle-Core Score 1,234\n", [1234]),
        ("Single Core Score: 987\n", [987]),
        ("Single-Core Score 1\nSingle-Core Score 2\n", [1, 2]),
        ("Multi-Core Score 999\n", []),
    ],
)
def test_score_parser_fixture(text: str, expected: list[int]) -> None:
    assert [int(value.replace(",", "")) for value in worker.SCORE_RE.findall(text)] == expected
    assert [int(value.replace(",", "")) for value in verifier.SCORE_RE.findall(text)] == expected


def test_command_hash_is_nul_delimited() -> None:
    argv = ["alpha", "beta gamma", "delta"]
    expected = hashlib.sha256(b"alpha\0beta gamma\0delta").hexdigest()
    assert worker.command_sha256(argv) == expected
    assert producer.command_sha256(argv) == expected
    assert verifier.command_sha256(argv) == expected


def test_regular_file_rejects_symlink(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.write_bytes(b"x")
    link = tmp_path / "link"
    link.symlink_to(source)
    with pytest.raises(RuntimeError, match="symlink component forbidden"):
        worker.regular_file(link, "fixture")


def test_worker_command_is_exactly_reconstructed() -> None:
    plan = load_plan()
    plan_path = PLAN_PATH.resolve(strict=True)
    python = Path(plan["system_tools"]["python"]["path"])
    worker_path = PROJECT / plan["implementation"]["worker"]["path"]
    assert producer.worker_argv(plan_path, plan, worker_path, python) == [
        str(python),
        str(worker_path),
        "--plan",
        str(plan_path),
        "--result-root",
        plan["paths"]["result_root"],
        "--scratch-root",
        plan["paths"]["scratch_root"],
    ]
