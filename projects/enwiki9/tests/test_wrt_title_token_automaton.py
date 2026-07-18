from __future__ import annotations

import importlib.util
import json
import struct
import sys
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "wrt_title_token_automaton.py"
)
sys.path.insert(0, str(TOOL.parent))
SPEC = importlib.util.spec_from_file_location("wrt_title_token_automaton", TOOL)
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


def wrt_literal_store(raw: bytes) -> tuple[bytes, bytes]:
    stream = (
        bytes((MODULE.TEXT_SEGMENT,))
        + len(raw).to_bytes(4, "big")
        + bytes((MODULE.TEXT_SEGMENT,))
        + bytes(MODULE.char_swap(value) for value in raw)
    )
    return bytes((0x80, 0, 0, 0, 0)) + stream, stream


def parse_synthetic_store(tmp_path: Path) -> tuple[MODULE.ParsedStore, Path, bytes]:
    stored, stream = wrt_literal_store(RAW)
    store_path = tmp_path / "wrt.store"
    dictionary_path = tmp_path / "english.dic"
    store_path.write_bytes(stored)
    dictionary_path.write_bytes(b"")
    return MODULE.parse_store(store_path, dictionary_path), dictionary_path, stream


def write_uniform_trace(path: Path, stream: bytes) -> None:
    payload = bytearray(MODULE.TRACE_MAGIC)
    for value in stream:
        for shift in range(7, -1, -1):
            payload.extend(MODULE.TRACE_RECORD.pack(32_768, (value >> shift) & 1))
    path.write_bytes(payload)


def write_archive(path: Path, stream: bytes) -> int:
    coder = MODULE.Fx2RangeCounter()
    for value in stream:
        for shift in range(7, -1, -1):
            coder.encode((value >> shift) & 1, 32_768)
    coder.finish()
    length = len(stream)
    header = bytearray()
    for shift in range(32, -1, -8):
        header.append((length >> shift) & 0xFF)
    if length >= 10_000:
        header.extend(bytes(32))
    path.write_bytes(bytes(header) + bytes(coder.bytes))
    return coder.bytes


def test_char_swap_is_an_involution() -> None:
    assert all(MODULE.char_swap(MODULE.char_swap(value)) == value for value in range(256))


def test_exact_wrt_events_map_to_title_units() -> None:
    literal = MODULE.unit_from_event(
        MODULE.WrtEvent(6, 7, bytes((MODULE.char_swap(ord("z")),)), b"z", "literal")
    )
    assert literal.signature == 0x10000 + ord("z")
    assert literal.decoded == b"z"

    token = MODULE.unit_from_event(
        MODULE.WrtEvent(7, 8, bytes((MODULE.char_swap(0x80),)), b"Alpha", "token")
    )
    assert token.signature == 0
    assert token.decoded == b"Alpha"


def test_compact_trace_reconstructs_wrt_bytes_and_title_endpoint_wins(tmp_path: Path) -> None:
    parsed, _, stream = parse_synthetic_store(tmp_path)
    trace = tmp_path / "trace.bin"
    write_uniform_trace(trace, stream)

    specs = [
        MODULE.VariantSpec("current", 1, 200_000, True, "always"),
        MODULE.VariantSpec("previous", 1, 200_000, True, "always"),
    ]
    stats, diagnostics = MODULE.score_trace(trace, parsed, specs)
    current = stats[specs[0].variant_id]
    previous = stats[specs[1].variant_id]

    assert diagnostics["wrt_bytes"] == len(stream)
    assert diagnostics["decoded_bytes"] == len(RAW)
    assert diagnostics["pages"] == 2
    assert diagnostics["titles"] == 2
    assert current.eligible_bits > 0
    assert current.qbits_saved > 0
    assert current.qbits_saved > previous.qbits_saved
    assert current.eligible_byte_events > 0
    assert current.positive_byte_events > 0
    assert current.positive_byte_oracle_qbits >= current.qbits_saved


def test_regret_router_updates_only_after_observed_truth(tmp_path: Path) -> None:
    parsed, _, stream = parse_synthetic_store(tmp_path)
    trace = tmp_path / "trace.bin"
    write_uniform_trace(trace, stream)
    spec = MODULE.VariantSpec("current", 1, 100_000, True, "regret12")
    stats, _ = MODULE.score_trace(trace, parsed, [spec])
    row = stats[spec.variant_id]

    assert row.eligible_bits > row.applied_bits > 0
    assert row.counterfactual_qbits >= row.qbits_saved > 0


def test_sparse_discovery_path_matches_exact_replay_stats(tmp_path: Path) -> None:
    parsed, _, stream = parse_synthetic_store(tmp_path)
    trace = tmp_path / "trace.bin"
    write_uniform_trace(trace, stream)
    specs = [
        MODULE.VariantSpec("current", 1, 200_000, True, "always"),
        MODULE.VariantSpec("previous", 1, 100_000, False, "regret12"),
    ]
    discovery, _ = MODULE.score_trace(trace, parsed, specs)
    exact_ids = {spec.variant_id for spec in specs}
    replay, diagnostics = MODULE.score_trace(trace, parsed, specs, exact_ids)

    for variant_id in exact_ids:
        assert discovery[variant_id].__dict__ == replay[variant_id].__dict__
        assert diagnostics["exact"][variant_id]["baseline_payload_bytes"] > 0


def test_fx2_range_counter_matches_uniform_payload_contract() -> None:
    _, stream = wrt_literal_store(RAW)
    first = MODULE.Fx2RangeCounter()
    second = MODULE.Fx2RangeCounter()
    for value in stream:
        for shift in range(7, -1, -1):
            bit = (value >> shift) & 1
            first.encode(bit, 32_768)
            second.encode(bit, 32_768)
    first.finish()
    second.finish()
    assert first.bytes == second.bytes
    assert first.bytes > 0


def test_cli_receipt_binds_trace_archive_and_store(tmp_path: Path) -> None:
    stored, stream = wrt_literal_store(RAW)
    trace = tmp_path / "trace.bin"
    archive = tmp_path / "archive.cmix"
    store = tmp_path / "wrt.store"
    dictionary = tmp_path / "english.dic"
    raw_input = tmp_path / "raw.bin"
    output = tmp_path / "receipt.json"
    write_uniform_trace(trace, stream)
    payload_bytes = write_archive(archive, stream)
    store.write_bytes(stored)
    dictionary.write_bytes(b"")
    raw_input.write_bytes(RAW)

    exit_code = MODULE.main(
        [
            "--trace",
            str(trace),
            "--dictionary",
            str(dictionary),
            "--scope-bytes",
            str(len(RAW)),
            "--archive",
            str(archive),
            "--wrt-store",
            str(store),
            "--raw-input",
            str(raw_input),
            "--window-id",
            "selection-synthetic",
            "--phase",
            "selection",
            "--exact-top",
            "2",
            "--substrate-id",
            "endpoint428",
            "--state-contract",
            "continuous_original_order",
            "--target-gap-bytes",
            "57404",
            "--incremental-program-bytes",
            "12000",
            "--output",
            str(output),
        ]
    )
    receipt = json.loads(output.read_text())

    assert exit_code == 0
    assert receipt["diagnostics"]["wrt_bytes"] == len(stream)
    assert receipt["validations"]["archive"]["payload_bytes"] == payload_bytes
    assert receipt["validations"]["archive"]["baseline_range_match"] is True
    assert receipt["validations"]["archive"]["trace_wrt_bytes_match"] is True
    assert receipt["validations"]["wrt_store"]["trace_matches_store"] is True
    assert receipt["validations"]["raw_input"]["matches_exact_wrt_decode"] is True
    assert receipt["best"]["source"] == "current"
    assert receipt["substrate"] == {
        "id": "endpoint428",
        "receipt": None,
        "state_contract": "continuous_original_order",
    }
    assert receipt["economics"]["required_gain_bytes_per_million"] == 69.404
    assert receipt["best_positive_byte_oracle"][
        "positive_byte_oracle_bytes_per_million"
    ] >= receipt["best"]["qbit_gain_bytes_per_million"]
