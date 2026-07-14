from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "projects" / "enwiki9" / "tools" / "candidate_audit.py"
SPEC = importlib.util.spec_from_file_location("candidate_audit", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_missing_symlink_payload_is_reported_without_crashing() -> None:
    with tempfile.TemporaryDirectory() as directory:
        program = Path(directory)
        (program / "program.py").write_bytes(b"123")
        (program / "model.bin").symlink_to(program / "missing.bin")
        assert MODULE.missing_payload_targets(program) == ["model.bin"]
        assert MODULE.driver_program_size(program) is None


def test_present_symlink_payload_is_counted_by_target_bytes() -> None:
    with tempfile.TemporaryDirectory() as directory:
        program = Path(directory)
        payload = program / "payload.bin"
        payload.write_bytes(b"12345")
        (program / "model.bin").symlink_to(payload)
        assert MODULE.missing_payload_targets(program) == []
        assert MODULE.driver_program_size(program) == 10
