from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/programs/wikiir_template_grammar_v1/program.py"
)
SPEC = importlib.util.spec_from_file_location("wikiir_template_grammar_v1", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_template_ir_preserves_ordered_named_and_positional_arguments() -> None:
    template = b"{{cite web|url=https://x?a=b|title=[[A|B]]|loose}}"

    parsed = MODULE._template_ir(template)

    assert parsed is not None
    segments, holes = parsed
    assert segments == (b"{{cite web", b"|url=", b"|title=", b"|", b"}}")
    assert holes == (b"https://x?a=b", b"[[A|B]]", b"loose")


def test_ir_roundtrip_with_repeated_nested_templates() -> None:
    rows = [
        b"{{cite web|url=https://example/" + str(i).encode() + b"|title={{lang|en|Title}}}}"
        for i in range(12)
    ]
    raw = b"prefix\n" + b"\n".join(rows) + b"\nsuffix"

    ir, stats = MODULE.encode_ir(raw)

    assert MODULE.decode_ir(ir) == raw
    assert stats["rules_admitted"] >= 1
    assert stats["rule_references"] >= 1
    assert stats["raw_ir_delta_bytes"] > 0


def test_archive_roundtrip_and_determinism() -> None:
    raw = (
        b"<page>{{infobox|name=A|value=1}}</page>\n"
        b"<page>{{infobox|name=B|value=2}}</page>\n"
        b"<page>{{infobox|name=C|value=3}}</page>\n"
    ) * 30

    first = MODULE.compress(raw)
    second = MODULE.compress(raw)

    assert first == second
    assert MODULE.decompress(first) == raw
    assert MODULE.stats()["roundtrip_checked_inside_compress"] is True


def test_arbitrary_non_template_bytes_use_literal_fallback() -> None:
    raw = bytes(range(256)) * 4 + b"{{unterminated"

    archive = MODULE.compress(raw)

    assert archive[0] == MODULE.MODE_LITERAL
    assert MODULE.decompress(archive) == raw
