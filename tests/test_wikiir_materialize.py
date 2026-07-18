from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/wikiir_materialize.py"
)
SPEC = importlib.util.spec_from_file_location("wikiir_materialize", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_materializes_reversible_deterministic_program(tmp_path: Path) -> None:
    input_path = tmp_path / "input"
    program_path = tmp_path / "program.py"
    input_path.write_bytes(b"abcdef")
    program_path.write_text(
        "def encode_ir(data): return b'X' + data, {'rows': len(data)}\n"
        "def decode_ir(data): return data[1:] if data.startswith(b'X') else b''\n"
    )

    ir, receipt = MODULE.run(input_path, 6, program_path)

    assert ir == b"Xabcdef"
    assert receipt["identity"] == {
        "raw_ir_roundtrip_ok": True,
        "encode_ir_deterministic": True,
    }
    assert receipt["stats"] == {"rows": 6}
