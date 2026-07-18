from __future__ import annotations

import importlib.util
from pathlib import Path
import struct
import sys

import numpy as np


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
TOOL = TOOLS / "wrt_typed_skip_cts_trace.py"
SPEC = importlib.util.spec_from_file_location("wrt_typed_skip_cts_trace", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


RAW = (
    b"<mediawiki><page><title>Alpha</title>"
    b'<text xml:space="preserve">{{cite|title=Alpha}} Alpha</text>'
    b"</page></mediawiki>"
)


def literal_store(raw: bytes) -> bytes:
    stream = (
        bytes((MODULE.TEXT_SEGMENT,))
        + len(raw).to_bytes(4, "big")
        + bytes((MODULE.TEXT_SEGMENT,))
        + bytes(MODULE.wrt_byte_transform(value) for value in raw)
    )
    return bytes((0x80, 0, 0, 0, 0)) + stream


def write_uniform_p1(path: Path, rows: int) -> None:
    with path.open("wb") as stream:
        stream.write(MODULE.P1_MAGIC)
        stream.write(struct.pack("<Q", rows))
        stream.write((32_768).to_bytes(2, "little") * rows)


def test_regime_hierarchy_is_coarse_to_specific() -> None:
    state = MODULE.WikiState(field_id=6, mode=2, slot=8, page_kind=4)

    assert MODULE.regime_keys(state, "plain") == ()
    assert MODULE.regime_keys(state, "phase") == ()
    assert MODULE.regime_keys(state, "global") == ()
    assert MODULE.regime_keys(state, "field") == (("field", 6),)
    assert MODULE.regime_keys(state, "slot") == (
        ("field", 6),
        ("field_mode", 6, 2),
        ("field_mode_slot", 6, 2, 8),
    )


def test_typed_trace_binds_exact_raw_store_and_base(tmp_path: Path) -> None:
    store = tmp_path / "wrt.store"
    dictionary = tmp_path / "english.dic"
    raw = tmp_path / "raw.bin"
    base = tmp_path / "base.p1"
    pair_path = tmp_path / "typed.pair"
    store.write_bytes(literal_store(RAW))
    dictionary.write_bytes(b"")
    raw.write_bytes(RAW)
    rows = (store.stat().st_size - 5) * 8
    write_uniform_p1(base, rows)

    receipt = MODULE.run(
        store=store,
        dictionary=dictionary,
        raw_input=raw,
        base_p1=base,
        output_trace=pair_path,
        max_order=2,
        max_contexts=10_000,
        p_buckets=8,
        profile="slot",
    )

    pair = np.memmap(
        pair_path,
        dtype="<u2",
        mode="r",
        offset=MODULE.PAIR_HEADER_BYTES,
        shape=(rows, 2),
    )
    assert np.all(pair[:, 0] == 32_768)
    assert np.all((pair[:, 1] > 0) & (pair[:, 1] < MODULE.TOTAL))
    assert receipt["scope"]["raw_bytes"] == len(RAW)
    assert receipt["identity"]["raw_matches_exact_wrt_decode"] is True
    assert receipt["identity"]["events_released_after_final_encoded_byte"] is True
    assert receipt["identity"]["total_event_length_never_exposed"] is True
    assert receipt["identity"]["current_event_key_uses_completed_bytes_only"] is True
    assert receipt["model"]["events_completed"] > 0
    assert receipt["model"]["contexts_used"] <= 10_000
    del pair


def test_probability_bucket_clamps_top_endpoint() -> None:
    assert MODULE.probability_bucket(1, 16) == 0
    assert MODULE.probability_bucket(65_535, 16) == 15


def test_event_prefix_uses_only_completed_encoded_bytes() -> None:
    left = MODULE.WrtEvent(6, 8, b"\xf7\xa6", b"left", "token")
    right = MODULE.WrtEvent(6, 9, b"\xf7\xd6\x80", b"right", "token")

    assert MODULE.causal_event_prefix(left, 0) == 0
    assert MODULE.causal_event_prefix(right, 0) == 0
    assert MODULE.causal_event_prefix(left, 1) == MODULE.causal_event_prefix(right, 1)
    assert MODULE.causal_event_prefix(right, 2) != MODULE.causal_event_prefix(right, 1)
