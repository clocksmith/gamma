from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "programs" / "wikiir_page_list_delta_v1" / "program.py"
SPEC = importlib.util.spec_from_file_location("wikiir_page_list_delta_v1", PROGRAM)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_roundtrip_selects_reversible_prior_page_delta() -> None:
    alpha = b"Alpha_" * 12
    beta = b"Beta_" * 12
    gamma = b"Gamma_" * 12
    delta = b"Delta_" * 12
    raw = (
        b"prefix\x00"
        b"<page><title>A</title>[[" + alpha + b"]][[" + beta + b"]][[" + gamma
        + b"]]</page>\n<page><title>B</title>[[" + alpha + b"]][[" + beta
        + b"]][[" + delta + b"]]</page>"
        b"suffix"
    )
    ir, stats = MODULE.encode_ir(raw)
    assert MODULE.decode_ir(ir) == raw
    assert stats["delta_pages"] == 1
    assert stats["literal_pages"] == 1


def test_encoding_is_deterministic_and_compressor_roundtrips() -> None:
    raw = (
        b"<page><title>A</title>[[One]][[Two]][[Three]]</page>"
        b"<page><title>B</title>[[One]][[Two]][[Four]]</page>"
    )
    first, first_stats = MODULE.encode_ir(raw)
    second, second_stats = MODULE.encode_ir(raw)
    assert first == second
    assert first_stats == second_stats
    assert MODULE.decompress(MODULE.compress(raw)) == raw


def test_decoder_rejects_forward_reference() -> None:
    raw = b"<page><title>A</title>[[One]]</page>"
    ir, _stats = MODULE.encode_ir(raw)
    prefix_end = len(MODULE.MAGIC) + 1 + 0 + 1
    malformed = bytearray(ir)
    malformed[prefix_end] = MODULE.MODE_DELTA
    malformed.insert(prefix_end + 1, 1)
    with pytest.raises(ValueError, match="reference distance"):
        MODULE.decode_ir(bytes(malformed))
