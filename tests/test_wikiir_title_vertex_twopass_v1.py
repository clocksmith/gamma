from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/programs/wikiir_title_vertex_twopass_v1/program.py"
)
SPEC = importlib.util.spec_from_file_location(
    "wikiir_title_vertex_twopass_v1", MODULE_PATH
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_two_pass_title_graph_roundtrips_forward_links_and_surfaces() -> None:
    raw = (
        b"\x00<page><title>Alpha Article</title><text>"
        b"[[Future Article|future]] [[Alpha_Article#Part|underscore]] "
        b"[[alpha Article]] [[Unknown]]"
        b"</text></page>\n"
        b"<page><title>Future Article</title><text>done</text></page>"
    )

    ir, stats = MODULE.encode_ir(raw)

    assert MODULE.decode_ir(ir) == raw
    assert ir.startswith(b"\x00\x00<page><title>Alpha Article</title>")
    assert stats["copied_title_dictionary_bytes"] == 0
    assert stats["matched_link_occurrences"] == 3
    assert stats["matched_exact_occurrences"] == 1
    assert stats["matched_underscore_occurrences"] == 1
    assert stats["matched_ascii_lower_first_occurrences"] == 1
    assert stats["forward_title_references_supported"] is True
    assert stats["reference_mode"] == "delta_separate"


def test_underscore_mode_replaces_only_the_final_title_space() -> None:
    raw = (
        b"<title>Characters in Atlas Shrugged</title>"
        b"[[Characters in Atlas_Shrugged]]"
    )

    ir, stats = MODULE.encode_ir(raw)

    assert MODULE.decode_ir(ir) == raw
    assert stats["matched_underscore_occurrences"] == 1


def test_two_pass_title_graph_duplicate_titles_use_first_id() -> None:
    raw = (
        b"[[Duplicate Long Title]]"
        b"<title>Duplicate Long Title</title>"
        b"<title>Duplicate Long Title</title>"
        + b"[[Duplicate Long Title]]" * 20
    )

    first, first_stats = MODULE.encode_ir(raw)
    second, second_stats = MODULE.encode_ir(raw)

    assert first == second
    assert first_stats == second_stats
    assert MODULE.decode_ir(first) == raw
    assert first_stats["title_count"] == 2
    assert first_stats["matched_link_occurrences"] == 21


def test_link_like_bytes_inside_title_are_not_replaced() -> None:
    raw = b"<title>Odd [[Title]] Bytes</title>[[Odd [[Title]] Bytes]]"

    ir, _stats = MODULE.encode_ir(raw)

    assert MODULE.decode_ir(ir) == raw


def test_archive_roundtrip_and_literal_fallback() -> None:
    raw = bytes(range(256)) * 4

    archive = MODULE.compress(raw)

    assert archive[0] == MODULE.MODE_LITERAL
    assert MODULE.decompress(archive) == raw
    assert MODULE.stats()["roundtrip_checked_inside_compress"] is True
