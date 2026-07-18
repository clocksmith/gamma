from __future__ import annotations

import importlib.util
from pathlib import Path
import struct
import sys


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
TOOL = TOOLS / "wrt_title_support_backoff.py"
SPEC = importlib.util.spec_from_file_location("wrt_title_support_backoff", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


RAW = (
    b"<mediawiki>"
    b"<page><title>Alpha Beta</title><text>"
    b"Alpha Beta is Alpha Beta. Alpha Beta repeats."
    b"</text></page>"
    b"<page><title>Gamma Delta</title><text>"
    b"Gamma Delta is Gamma Delta. Gamma Delta repeats."
    b"</text></page>"
    b"</mediawiki>"
)


def literal_store(raw: bytes) -> tuple[bytes, bytes]:
    stream = (
        bytes((MODULE.TEXT_SEGMENT,))
        + len(raw).to_bytes(4, "big")
        + bytes((MODULE.TEXT_SEGMENT,))
        + bytes(MODULE.wrt_byte_transform(value) for value in raw)
    )
    return bytes((0x80, 0, 0, 0, 0)) + stream, stream


def write_uniform_trace(path: Path, stream: bytes) -> None:
    record = struct.Struct("<HB")
    payload = bytearray(MODULE.TRACE_MAGIC)
    for value in stream:
        for shift in range(7, -1, -1):
            payload.extend(record.pack(32_768, (value >> shift) & 1))
    path.write_bytes(payload)


def test_hierarchical_probability_uses_longer_context() -> None:
    model = MODULE.SupportTitleModel(max_context=2)
    units = [
        MODULE.WrtUnit(1, b"A", b"A"),
        MODULE.WrtUnit(2, b"B", b"B"),
        MODULE.WrtUnit(1, b"A", b"A"),
        MODULE.WrtUnit(3, b"C", b"C"),
    ]
    model.build(units)
    model.observe_unit(1)
    probability = model.probability(2, 4, 0, 0)

    assert probability is not None
    assert probability[1] == 1
    assert probability[2] == 2
    assert 1 <= probability[0] < MODULE.TOTAL


def test_exact_support_replay_reconstructs_raw_and_range_payload(tmp_path: Path) -> None:
    stored, stream = literal_store(RAW)
    store_path = tmp_path / "wrt.store"
    dictionary_path = tmp_path / "english.dic"
    trace_path = tmp_path / "trace.bin"
    store_path.write_bytes(stored)
    dictionary_path.write_bytes(b"")
    write_uniform_trace(trace_path, stream)
    parsed = MODULE.parse_store(store_path, dictionary_path)
    spec = MODULE.SupportSpec("contrast", 8, 16, 1_000_000)

    states, diagnostics = MODULE.score_trace(
        trace_path, parsed, [spec], {spec.variant_id}
    )

    assert diagnostics["decoded_bytes"] == len(RAW)
    assert diagnostics["pages"] == 2
    assert diagnostics["titles"] == 2
    assert diagnostics["events_released_after_completion"] is True
    assert diagnostics["exact"][spec.variant_id]["baseline_payload_bytes"] > 0
    assert states[spec.variant_id].eligible_bits > 0


def test_scaled_delta_is_symmetric() -> None:
    assert MODULE.scaled_delta(101, 250_000) == 25
    assert MODULE.scaled_delta(-101, 250_000) == -25
