from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "programs" / "wikiir_url_prefix_dict_v1" / "program.py"
SPEC = importlib.util.spec_from_file_location("wikiir_url_prefix_dict_v1", PROGRAM)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_roundtrip_rebuilds_hosts_and_prefixes_from_prior_urls() -> None:
    raw = (
        b"http://example.test/first/a "
        b"https://example.test/first/b "
        b"http://example.test/second/c "
        b"http://other.test/first/d "
        b"http://example.test/first/e\x00"
    )
    ir, stats = MODULE.encode_ir(raw)
    assert stats["learned_hosts"] == 2
    assert stats["prefix_references"] == 2
    assert stats["host_references"] == 1
    assert MODULE.decode_ir(ir) == raw
    assert MODULE.decompress(MODULE.compress(raw)) == raw


def test_decoder_rejects_unknown_prefix_reference() -> None:
    stream = MODULE.MAGIC + b"http://" + bytes(
        (MODULE.ESCAPE, MODULE.PREFIX_REF, 0)
    )
    with pytest.raises(ValueError, match="unknown URL-prefix"):
        MODULE.decode_ir(stream)


def test_no_first_segment_uses_host_dictionary_only() -> None:
    raw = b"http://x.test/ http://x.test/"
    ir, stats = MODULE.encode_ir(raw)
    assert stats["prefix_references"] == 0
    assert stats["host_references"] == 1
    assert MODULE.decode_ir(ir) == raw


def test_encoding_is_deterministic() -> None:
    raw = b"http://x.test/a/z http://x.test/a/y"
    assert MODULE.encode_ir(raw) == MODULE.encode_ir(raw)
