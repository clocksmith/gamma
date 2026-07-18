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


def wrt_literal_stream(raw: bytes) -> bytes:
    return bytes(MODULE.char_swap(value) for value in raw)


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


def test_wrt_tokenizer_decodes_literals_controls_and_dictionary_codes() -> None:
    tokenizer = MODULE.WrtTokenizer([b"alpha"] * 81)
    literal = tokenizer.feed(MODULE.char_swap(ord("z")))
    assert literal is not None and literal.decoded == b"z"

    capital = tokenizer.feed(MODULE.char_swap(0x40))
    assert capital is not None and capital.decoded == b""
    word = tokenizer.feed(MODULE.char_swap(0x80))
    assert word is not None and word.signature == 0 and word.decoded == b"Alpha"

    assert tokenizer.feed(MODULE.char_swap(0xD0)) is None
    wide = tokenizer.feed(MODULE.char_swap(0x80))
    assert wide is not None and wide.signature == 80 and wide.decoded == b"alpha"


def test_compact_trace_reconstructs_wrt_bytes_and_title_endpoint_wins(tmp_path: Path) -> None:
    stream = wrt_literal_stream(RAW)
    trace = tmp_path / "trace.bin"
    dictionary_path = tmp_path / "english.dic"
    write_uniform_trace(trace, stream)
    dictionary_path.write_bytes(b"")

    specs = [
        MODULE.VariantSpec("current", 1, 200_000, True, "always"),
        MODULE.VariantSpec("previous", 1, 200_000, True, "always"),
    ]
    stats, diagnostics = MODULE.score_trace(
        trace, MODULE.load_dictionary(dictionary_path), specs
    )
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
    stream = wrt_literal_stream(RAW)
    trace = tmp_path / "trace.bin"
    write_uniform_trace(trace, stream)
    spec = MODULE.VariantSpec("current", 1, 100_000, True, "regret12")
    stats, _ = MODULE.score_trace(trace, [], [spec])
    row = stats[spec.variant_id]

    assert row.eligible_bits > row.applied_bits > 0
    assert row.counterfactual_qbits >= row.qbits_saved > 0


def test_fx2_range_counter_matches_uniform_payload_contract() -> None:
    stream = wrt_literal_stream(RAW)
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
    stream = wrt_literal_stream(RAW)
    trace = tmp_path / "trace.bin"
    archive = tmp_path / "archive.cmix"
    payload = tmp_path / "archive.payload"
    store = tmp_path / "wrt.store"
    dictionary = tmp_path / "english.dic"
    output = tmp_path / "receipt.json"
    write_uniform_trace(trace, stream)
    payload_bytes = write_archive(archive, stream)
    payload.write_bytes(bytes(payload_bytes))
    store.write_bytes(bytes(5) + stream)
    dictionary.write_bytes(b"")

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
            "--payload",
            str(payload),
            "--wrt-store",
            str(store),
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
    assert receipt["validations"]["payload"]["baseline_range_match"] is True
    assert receipt["validations"]["wrt_store"]["trace_matches_store"] is True
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
