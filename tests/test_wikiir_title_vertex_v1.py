from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/programs/wikiir_title_vertex_v1/program.py"
)
SPEC = importlib.util.spec_from_file_location("wikiir_title_vertex_v1", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_title_vertex_roundtrips_links_fragments_labels_and_zero() -> None:
    raw = (
        b"\x00<page><title>Alpha Article</title><text>"
        b"[[Alpha Article]] [[Alpha Article#Part|label]] [[Unknown]]"
        b"</text></page>\n"
        b"<page><title>Beta Article</title><text>[[Alpha Article]]</text></page>"
    )

    ir, stats = MODULE.encode_ir(raw)

    assert MODULE.decode_ir(ir) == raw
    assert stats["title_count"] == 2
    assert stats["matched_link_occurrences"] == 3
    assert stats["matched_link_source_bytes"] == 39


def test_duplicate_titles_use_first_vertex_but_all_title_slots_roundtrip() -> None:
    raw = (
        b"<title>Duplicate Long Title</title>"
        b"<title>Duplicate Long Title</title>"
        + b"[[Duplicate Long Title]]" * 12
    )

    ir, stats = MODULE.encode_ir(raw)

    assert MODULE.decode_ir(ir) == raw
    assert stats["title_count"] == 2
    assert stats["matched_link_occurrences"] == 12


def test_archive_roundtrip_and_determinism() -> None:
    raw = (
        b"<page><title>Alphabetic Article</title><text>"
        + b"[[Alphabetic Article|A]] " * 40
        + b"</text></page>"
    )

    first = MODULE.compress(raw)
    second = MODULE.compress(raw)

    assert first == second
    assert MODULE.decompress(first) == raw
    assert MODULE.stats()["roundtrip_checked_inside_compress"] is True


def test_arbitrary_bytes_fall_back_to_literal_archive() -> None:
    raw = bytes(range(256)) * 4

    archive = MODULE.compress(raw)

    assert archive[0] == MODULE.MODE_LITERAL
    assert MODULE.decompress(archive) == raw
