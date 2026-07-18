from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


TOOLS = Path(__file__).resolve().parents[1] / "projects/enwiki9/tools"
sys.path.insert(0, str(TOOLS))


def load(name: str):
    path = TOOLS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CONVERTER = load("p1_wrt_to_fx2pt_trace")
AUTOMATON = load("wrt_title_token_automaton")


def test_build_trace_preserves_probabilities_and_msb_truth(tmp_path: Path) -> None:
    values = bytes((0xA5, 0x0F))
    probabilities = tuple(1000 + index * 17 for index in range(16))
    p1 = tmp_path / "input.p1"
    store = tmp_path / "input.store"
    output = tmp_path / "output.trace"
    p1.write_bytes(
        CONVERTER.P1_MAGICS[0]
        + len(probabilities).to_bytes(8, "little")
        + b"".join(value.to_bytes(2, "little") for value in probabilities)
    )
    store.write_bytes(CONVERTER.WRT_HEADER + values)

    receipt = CONVERTER.build_trace(p1, store, output, chunk_bytes=1)
    rows = list(AUTOMATON.iter_trace_bytes(output))

    assert receipt["rows"] == 16
    assert [row.value for row in rows] == list(values)
    assert tuple(value for row in rows for value in row.probabilities) == probabilities
    assert tuple(bit for row in rows for bit in row.bits) == tuple(
        (value >> shift) & 1 for value in values for shift in range(7, -1, -1)
    )


def test_converter_rejects_store_length_mismatch(tmp_path: Path) -> None:
    p1 = tmp_path / "input.p1"
    store = tmp_path / "input.store"
    output = tmp_path / "output.trace"
    p1.write_bytes(
        CONVERTER.P1_MAGICS[1]
        + (8).to_bytes(8, "little")
        + (32768).to_bytes(2, "little") * 8
    )
    store.write_bytes(CONVERTER.WRT_HEADER + b"too long")

    try:
        CONVERTER.build_trace(p1, store, output)
    except ValueError as error:
        assert "size" in str(error)
    else:
        raise AssertionError("mismatched store unexpectedly accepted")
