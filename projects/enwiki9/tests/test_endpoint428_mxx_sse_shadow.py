from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "endpoint428_mxx_sse_shadow.py"
)
sys.path.insert(0, str(TOOL.parent))
SPEC = importlib.util.spec_from_file_location("endpoint428_mxx_sse_shadow", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_parse_unsigned_char_array_strips_comments_and_checks_width() -> None:
    values = ",".join(str(index & 7) for index in range(256))
    source = f"const U8 wrt_2b[256]={{/* start */{values}// end\n}};"
    assert MODULE.parse_unsigned_char_array(source, "wrt_2b") == tuple(
        index & 7 for index in range(256)
    )


def test_mxx_reconstruction_uses_only_the_decoded_prefix() -> None:
    wrt_2b = tuple(index & 3 for index in range(256))
    wrt_3b = tuple(index & 7 for index in range(256))
    first, first_bpos = MODULE.reconstruct_mxx(b"\xA0\x00", wrt_2b, wrt_3b)
    second, second_bpos = MODULE.reconstruct_mxx(b"\xA1\x00", wrt_2b, wrt_3b)

    # The differing final truth bit cannot affect its own pre-bit context.
    assert np.array_equal(first[:8], second[:8])
    assert np.array_equal(first_bpos[:8], np.arange(8, dtype=np.uint8))
    # It may affect the context only after that byte has been decoded.
    assert not np.array_equal(first[8:], second[8:])
    assert np.array_equal(first_bpos[8:], second_bpos[8:])


def test_mxx_reconstruction_applies_pretraining_before_first_payload_bit() -> None:
    wrt_2b = tuple(index & 3 for index in range(256))
    wrt_3b = tuple(index & 7 for index in range(256))
    cold, _ = MODULE.reconstruct_mxx(b"\x00", wrt_2b, wrt_3b)
    warm, _ = MODULE.reconstruct_mxx(
        b"\x00", wrt_2b, wrt_3b, pretrained_bytes=b"A"
    )
    assert cold[0] == 0
    assert warm[0] != cold[0]


def test_mxx_state_matches_updatewords_special_cases() -> None:
    wrt_2b = tuple(index & 3 for index in range(256))
    wrt_3b = tuple(index & 7 for index in range(256))
    state = MODULE.MxxState(wrt_2b=wrt_2b, wrt_3b=wrt_3b)
    for shift in range(7, -1, -1):
        state.observe((ord("Q") >> shift) & 1)
    assert state.bpos == 0
    assert state.b2stream == (ord("Q") & 3)
    # Q is inserted twice into the 3-bit stream in ContextManager::UpdateWords.
    expected = ((ord("Q") & 7) * 8 + (ord("Q") & 7)) & MODULE.MASK64
    assert state.b3stream == expected


def test_online_mean_calibrator_predicts_before_learning_truth() -> None:
    config = MODULE.CalibrationConfig(
        "test", "mxx", 1, "mean", 1, minimum_observations=1
    )
    state = MODULE.OnlineCalibrator(config, context_count=1)
    assert state.predict_then_update(0, 30_000, 1) == 30_000
    assert state.predict(0, 30_000) > 30_000


def test_current_truth_cannot_change_current_prediction() -> None:
    config = MODULE.CalibrationConfig("test", "mxx", 4, "ema", 3)
    left = MODULE.OnlineCalibrator(config, context_count=2)
    right = MODULE.OnlineCalibrator(config, context_count=2)
    for state in (left, right):
        state.update(1, 20_000, 1)
    assert left.predict_then_update(1, 20_000, 0) == right.predict_then_update(
        1, 20_000, 1
    )


def test_mxx_control_and_candidate_contexts_are_distinct() -> None:
    mxx = np.asarray([3, 3, 7, 7], dtype=np.uint16)
    bpos = np.asarray([0, 1, 0, 1], dtype=np.uint8)
    bitpos_ids, bitpos_count = MODULE.context_ids("bitpos", mxx, bpos)
    mxx_ids, mxx_count = MODULE.context_ids("mxx", mxx, bpos)
    nested_ids, nested_count = MODULE.context_ids("mxx_bitpos", mxx, bpos)
    assert bitpos_count == 8
    assert mxx_count == 8
    assert nested_count == 58
    assert bitpos_ids.tolist() == [0, 1, 0, 1]
    assert mxx_ids.tolist() == [3, 3, 7, 7]
    assert nested_ids.tolist() == [24, 25, 56, 57]


def test_signed_round_div_is_symmetric() -> None:
    assert MODULE.signed_round_div(5, 2) == 3
    assert MODULE.signed_round_div(-5, 2) == -3
    assert MODULE.signed_round_div(4, 3) == 1
    assert MODULE.signed_round_div(-4, 3) == -1
