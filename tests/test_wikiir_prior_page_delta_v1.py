from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/programs/wikiir_prior_page_delta_v1/program.py"
)
SPEC = importlib.util.spec_from_file_location("wikiir_prior_page_delta_v1", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_delta_commands_roundtrip_copy_add_and_run() -> None:
    reference = b"prefix-" + b"abcdef" * 20 + b"-suffix"
    target = b"prefix-" + b"abcdef" * 18 + b"XXXXXXXXXXXX" + b"-changed"

    delta, stats = MODULE._delta_encode(reference, target)

    assert MODULE._delta_decode(reference, delta) == target
    assert stats["copy_commands"] >= 1
    assert stats["run_commands"] >= 1


def test_prior_page_ir_roundtrip_and_uses_delta() -> None:
    pages = []
    for index in range(12):
        pages.append(
            b"<page><title>Example "
            + str(index).encode()
            + b"</title><text>{{infobox|name=Example|value="
            + str(index).encode()
            + b"}}"
            + b" common prose" * 30
            + b"</text></page>\n"
        )
    raw = b"<mediawiki>\n" + b"".join(pages) + b"</mediawiki>"

    ir, stats = MODULE.encode_ir(raw)

    assert MODULE.decode_ir(ir) == raw
    assert stats["complete_pages"] == len(pages)
    assert stats["delta_pages"] >= 1
    assert stats["copied_bytes"] > 0


def test_archive_roundtrip_and_determinism() -> None:
    page = b"<page><text>{{cite|url=https://example|title=A}}</text></page>\n"
    raw = b"<mediawiki>\n" + page * 20 + b"</mediawiki>"

    first = MODULE.compress(raw)
    second = MODULE.compress(raw)

    assert first == second
    assert MODULE.decompress(first) == raw
    assert MODULE.stats()["roundtrip_checked_inside_compress"] is True


def test_no_complete_pages_roundtrips_through_literal_mode() -> None:
    raw = bytes(range(256)) * 3

    archive = MODULE.compress(raw)

    assert archive[0] == MODULE.MODE_LITERAL
    assert MODULE.decompress(archive) == raw
