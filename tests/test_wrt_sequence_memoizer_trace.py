from __future__ import annotations

import importlib.util
import struct
import sys
from pathlib import Path

import numpy as np


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/wrt_sequence_memoizer_trace.py"
)
SPEC = importlib.util.spec_from_file_location("wrt_sequence_memoizer_trace", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_token_lengths_and_ids_are_deterministic() -> None:
    assert MODULE.token_length(0x41) == 1
    assert MODULE.token_length(0x0C) == 2
    assert MODULE.token_length(0xD0) == 2
    assert MODULE.token_length(0xF0) == 3
    assert MODULE.token_id(b"a") == MODULE.token_id(b"a")
    assert MODULE.token_id(b"a") != MODULE.token_id(b"aa")


def test_integer_sequence_memoizer_is_causal_and_bounded() -> None:
    model = MODULE.SequenceMemoizer(max_order=2, max_contexts=100)

    first = model.predict_and_observe_byte(ord("A"))
    second = model.predict_and_observe_byte(ord("A"))

    assert first == [32768] * 8
    assert second != first
    assert model.tokens_completed == 2
    assert model.contexts <= 100


def test_trace_copies_frozen_base_and_is_deterministic(tmp_path: Path) -> None:
    payload = b"abcabc" + bytes([0xD0, 0x80, 0xD0, 0x80])
    store = tmp_path / "store"
    store.write_bytes(b"HEAD!" + payload)
    rows = len(payload) * 8
    base_values = np.arange(1, rows + 1, dtype="<u2")
    base_p1 = tmp_path / "base.p1"
    base_p1.write_bytes(
        MODULE.P1_MAGIC + struct.pack("<Q", rows) + base_values.tobytes()
    )
    first_trace = tmp_path / "first.pair"
    second_trace = tmp_path / "second.pair"

    first = MODULE.run(
        store=store,
        store_offset=5,
        base_p1=base_p1,
        output_trace=first_trace,
        max_order=2,
        max_contexts=1000,
    )
    second = MODULE.run(
        store=store,
        store_offset=5,
        base_p1=base_p1,
        output_trace=second_trace,
        max_order=2,
        max_contexts=1000,
    )
    pair = np.memmap(
        first_trace,
        dtype="<u2",
        mode="r",
        offset=MODULE.PAIR_HEADER_BYTES,
        shape=(rows, 2),
    )

    assert np.array_equal(pair[:, 0], base_values)
    assert first_trace.read_bytes() == second_trace.read_bytes()
    assert first["output"]["sha256"] == second["output"]["sha256"]
    assert first["model"]["contexts_used"] <= 1000
