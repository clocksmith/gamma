from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/wikiir_title_vertex_tail_layout.py"
)
SPEC = importlib.util.spec_from_file_location("wikiir_title_vertex_tail_layout", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_tail_layout_preserves_selected_information_and_raw_bytes() -> None:
    raw = (
        b"<page><title>Alpha Long Title</title><text>"
        + b"[[Alpha Long Title|A]] " * 20
        + b"</text></page>\x00"
    )

    front, _front_stats = MODULE.BASE.encode_ir(raw)
    tail, stats = MODULE._pack_tail(front)

    assert tail[:2] == b"<p"
    assert tail[-4:] == MODULE.TAIL_MAGIC
    assert MODULE.decode_ir(tail) == raw
    assert stats["tail_layout_delta_vs_front_bytes"] > 0


def test_run_is_deterministic_and_roundtrips(tmp_path: Path) -> None:
    raw = (
        b"<title>Repeated Vertex Title</title>"
        + b"[[Repeated Vertex Title]]" * 30
    )
    input_path = tmp_path / "input"
    input_path.write_bytes(raw)

    ir, receipt = MODULE.run(input_path, len(raw))

    assert MODULE.decode_ir(ir) == raw
    assert receipt["identity"]["raw_ir_roundtrip_ok"] is True
    assert receipt["identity"]["selected_information_identical_to_front_layout"] is True
