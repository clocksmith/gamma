from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/programs/wikiir_webgraph_v1/program.py"
)
SPEC = importlib.util.spec_from_file_location("wikiir_webgraph_v1", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_id_modes_roundtrip_signed_jumps() -> None:
    ids = [900, 3, 4, 4, 800, 2, 1] * 40

    mode, payload = MODULE._encode_ids(ids)

    assert MODULE._decode_ids(mode, payload, len(ids)) == ids


def test_graph_ir_roundtrips_links_labels_malformed_and_zero() -> None:
    repeated = b"Very Long Repeated Target"
    raw = (
        b"\x00prefix [["
        + repeated
        + b"|label]] middle [[Unique]] [["
        + repeated
        + b"]] suffix\x00 [[unterminated"
    ) * 8

    ir, stats = MODULE.encode_ir(raw)

    assert MODULE.decode_ir(ir) == raw
    assert stats["selected_target_types"] >= 1
    assert stats["selected_target_occurrences"] >= 2
    assert stats["raw_ir_delta_bytes"] > 0


def test_dictionary_is_sorted_front_coded_and_deterministic() -> None:
    raw = (
        b"[[Alphabetic target one]] [[Alphabetic target two]] "
        b"[[Alphabetic target one]] [[Alphabetic target two]]"
    ) * 20

    first, first_stats = MODULE.encode_ir(raw)
    second, second_stats = MODULE.encode_ir(raw)

    assert first == second
    assert first_stats == second_stats
    assert MODULE.decode_ir(first) == raw
    assert first_stats["dictionary_bytes"] < len(b"Alphabetic target oneAlphabetic target two")


def test_archive_roundtrip_and_literal_fallback() -> None:
    raw = bytes(range(256)) * 4 + b"[[only once]]"

    first = MODULE.compress(raw)
    second = MODULE.compress(raw)

    assert first == second
    assert first[0] == MODULE.MODE_LITERAL
    assert MODULE.decompress(first) == raw
    assert MODULE.stats()["roundtrip_checked_inside_compress"] is True
