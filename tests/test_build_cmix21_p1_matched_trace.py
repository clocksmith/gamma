import importlib.util
import struct
from pathlib import Path

import numpy as np


MODULE_PATH = (
    Path(__file__).parents[1]
    / "projects/enwiki9/tools/build_cmix21_p1_matched_trace.py"
)
SPEC = importlib.util.spec_from_file_location("build_cmix21_p1_matched_trace", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_build_trace_preserves_truth_and_base_probability(tmp_path):
    p1 = tmp_path / "base.p1"
    store = tmp_path / "input.store"
    output = tmp_path / "matched.bin"
    values = np.array([1, 100, 32768, 65535, 7, 8, 9, 10], dtype="<u2")
    p1.write_bytes(MODULE.P1_MAGIC + struct.pack("<Q", len(values)) + values.tobytes())
    store.write_bytes(MODULE.WRT_HEADER + bytes([0b10110010]))

    result = MODULE.build_trace(p1, store, output)

    assert result["rows"] == 8
    dtype = np.dtype([("bit", "u1"), ("p", "<u2", (1,))])
    trace = np.memmap(output, mode="r", dtype=dtype, offset=MODULE.TRACE_HEADER.size)
    assert trace["bit"].tolist() == [1, 0, 1, 1, 0, 0, 1, 0]
    assert trace["p"][:, 0].tolist() == values.tolist()


def test_build_trace_accepts_fx2_probability_header(tmp_path):
    p1 = tmp_path / "base.p1"
    store = tmp_path / "input.store"
    output = tmp_path / "matched.bin"
    values = np.array([11, 12, 13, 14, 15, 16, 17, 18], dtype="<u2")
    p1.write_bytes(
        MODULE.FX2_P1_MAGIC + struct.pack("<Q", len(values)) + values.tobytes()
    )
    store.write_bytes(MODULE.WRT_HEADER + bytes([0b01010101]))

    result = MODULE.build_trace(p1, store, output)

    assert result["rows"] == 8
    dtype = np.dtype([("bit", "u1"), ("p", "<u2", (1,))])
    trace = np.memmap(output, mode="r", dtype=dtype, offset=MODULE.TRACE_HEADER.size)
    assert trace["bit"].tolist() == [0, 1, 0, 1, 0, 1, 0, 1]
    assert trace["p"][:, 0].tolist() == values.tolist()
