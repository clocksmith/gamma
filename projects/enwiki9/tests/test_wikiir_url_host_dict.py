from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "programs" / "wikiir_url_host_dict_v1" / "program.py"
SPEC = importlib.util.spec_from_file_location("wikiir_url_host_dict_v1", PROGRAM)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_roundtrip_rebuilds_hosts_only_from_prior_literal_urls() -> None:
    raw = (
        b"http://example.test/a https://example.test/b "
        b"http://other.test/c http://example.test/d\x00"
    )
    ir, stats = MODULE.encode_ir(raw)
    assert stats["learned_hosts"] == 2
    assert stats["host_references"] == 2
    assert MODULE.decode_ir(ir) == raw
    assert MODULE.decompress(MODULE.compress(raw)) == raw


def test_decoder_rejects_reference_before_any_literal_host() -> None:
    stream = MODULE.MAGIC + b"http://" + bytes((MODULE.ESCAPE, MODULE.HOST_REF, 0))
    with pytest.raises(ValueError, match="unknown URL-host"):
        MODULE.decode_ir(stream)


def test_encoding_is_deterministic() -> None:
    raw = b"http://x.test/a http://x.test/b"
    assert MODULE.encode_ir(raw) == MODULE.encode_ir(raw)
