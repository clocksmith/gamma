"""Actual retained fixture framing must not silently change the trained alphabet."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fx2_static_adapter", ROOT / "tools/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def fixture():
    storage = (ROOT / "results/fx2_cmix_transformer_gcc_fixture50051_q0_v4/work/fixture.stored").read_bytes()
    vocabulary = json.loads((ROOT / "operations/provenance/public_fx2_authenticated_vocabulary_20260905.json").read_text())
    return storage[5:], vocabulary


def test_authenticated_map_accepts_body_without_inventing_symbols_for_framing():
    payload, vocabulary = fixture()
    assert 0 not in vocabulary["vocabulary_bytes"]
    assert [index for index, byte in enumerate(payload) if byte == 0] == [1, 2]
    assert len(set(payload)) == 202
    report = runner.check_population(payload, vocabulary)
    assert report["mapping_gate_pass"] is True
    assert report["coded_population_bytes"] == 32478
    assert report["first_separator_indices"] == runner.SEPARATOR


def test_out_of_alphabet_body_and_changed_separator_are_rejected():
    payload, vocabulary = fixture()
    for changed in (payload[:100] + b"\0" + payload[101:], payload[:6] + b"\3" + payload[7:]):
        assert runner.check_population(changed, vocabulary)["mapping_gate_pass"] is False
    with pytest.raises(ValueError, match="truncated"):
        runner.check_population(payload[:8], vocabulary)


def test_counted_envelope_rejects_wrong_map_scope_and_literal_bytes():
    payload, vocabulary = fixture()
    header = b"GFV1" + payload[:5] + ((1 << 39) | (len(payload) - 5)).to_bytes(5, "big") + bytes.fromhex(vocabulary["vocabulary_bitmap_hex"])
    runner.check_archive_header(header, payload, vocabulary)
    for position in (0, 5, 9, 13, 14, 45):
        changed = bytearray(header)
        changed[position] ^= 1
        with pytest.raises(ValueError):
            runner.check_archive_header(bytes(changed), payload, vocabulary)
    with pytest.raises(ValueError):
        runner.check_archive_header(header[:-1], payload, vocabulary)
