from __future__ import annotations

import importlib.util
from pathlib import Path
import struct

import pytest


PROJECT = Path(__file__).resolve().parents[1]
PROGRAM = (
    PROJECT
    / "programs/endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1/program.py"
)
LAUNCHER = (
    PROJECT
    / "tools/endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1.py"
)


def load_program():
    spec = importlib.util.spec_from_file_location(
        "_endpoint428_horizon_orphan_adoption_test", PROGRAM
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_live_zero_row_header_and_terminal_header_are_distinguished(
    tmp_path: Path,
) -> None:
    observer = load_program()
    trace = tmp_path / "parent.p1"
    trace.write_bytes(observer.TRACE_MAGIC + struct.pack("<Q", 0) + b"\x00\x01")
    live = observer.read_trace_header(trace)
    assert live == {
        "magicHex": observer.TRACE_MAGIC.hex(),
        "declaredRows": 0,
        "magicValid": True,
        "terminalRowCountValid": False,
        "valid": False,
    }

    trace.write_bytes(
        observer.TRACE_MAGIC + struct.pack("<Q", observer.TRACE_ROWS)
    )
    terminal = observer.read_trace_header(trace)
    assert terminal["declaredRows"] == observer.TRACE_ROWS
    assert terminal["terminalRowCountValid"] is True
    assert terminal["valid"] is True


def test_namespace_allows_only_frozen_ephemeral_removal() -> None:
    observer = load_program()
    baseline = {
        name: {"kind": "directory" if name.startswith(".cmix9-") else "file"}
        for name in observer.REQUIRED_SOURCE_NAMES
        | observer.EPHEMERAL_SOURCE_NAMES
    }
    terminal = {
        name: row
        for name, row in baseline.items()
        if name not in observer.EPHEMERAL_SOURCE_NAMES
    }
    observer.check_namespace(baseline, terminal)

    added = {**terminal, "analysis-a.json": {"kind": "file"}}
    with pytest.raises(observer.SourceMutationError, match="added"):
        observer.check_namespace(baseline, added)

    missing = dict(terminal)
    missing.pop("manifest-a.bin")
    with pytest.raises(observer.SourceMutationError, match="missing_required"):
        observer.check_namespace(baseline, missing)


def test_recovery_predicates_authorize_only_complete_integrity() -> None:
    observer = load_program()
    experiment = {
        "promotionPredicates": [
            {
                "id": "geometry",
                "measurement": "traceGeometryPass",
                "operator": "eq",
                "threshold": True,
            },
            {
                "id": "archive",
                "measurement": "archiveBytes",
                "operator": "gt",
                "threshold": 0,
            },
        ],
        "killPredicates": [
            {
                "id": "integrity-failure",
                "measurement": "recoveryIntegrityPass",
                "operator": "eq",
                "threshold": False,
            }
        ],
    }
    passing = {
        "traceGeometryPass": True,
        "archiveBytes": 1,
        "recoveryIntegrityPass": True,
    }
    promotion = observer.evaluate(experiment["promotionPredicates"], passing)
    kill = observer.evaluate(experiment["killPredicates"], passing)
    assert all(row["passed"] for row in promotion)
    assert not any(row["passed"] for row in kill)

    failing = {**passing, "traceGeometryPass": False, "recoveryIntegrityPass": False}
    promotion = observer.evaluate(experiment["promotionPredicates"], failing)
    kill = observer.evaluate(experiment["killPredicates"], failing)
    assert not all(row["passed"] for row in promotion)
    assert all(row["passed"] for row in kill)


def test_observer_has_no_process_control_or_scientific_analyzer_surface() -> None:
    source = PROGRAM.read_text(encoding="utf-8")
    for forbidden in (
        "import subprocess",
        "os.kill(",
        "os.setpriority(",
        "sched_setaffinity(",
        "horizon-retained-analyze",
        "analysis-a.json",
        "analysis-b.json",
    ):
        assert forbidden not in source
    assert "os.execve(" not in source
    assert "os.execve(" in LAUNCHER.read_text(encoding="utf-8")


def test_output_creation_is_no_clobber(tmp_path: Path) -> None:
    observer = load_program()
    output = tmp_path / "receipt.json"
    observer.create_new_json(output, {"first": True})
    with pytest.raises(FileExistsError):
        observer.create_new_json(output, {"second": True})
    assert output.read_text(encoding="ascii") == '{\n  "first": true\n}\n'
