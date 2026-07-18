from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "cmix_aux_bucket_calibration", TOOLS / "cmix_aux_bucket_calibration.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_context_ids_include_probability_pairs_and_bit_position() -> None:
    base = np.array([1000, 1000, 60000, 60000], dtype=np.uint16)
    endpoint = np.array([2000, 2000, 50000, 50000], dtype=np.uint16)
    ids = MODULE.context_ids(base, endpoint, 0, 8, 8)
    assert ids[0] != ids[1]
    assert ids[0] != ids[2]
    assert ids[2] != ids[3]


def test_choose_weights_requires_support_and_margin() -> None:
    losses = np.array([[1000, 500], [1000, 999], [1000, 100]], dtype=np.int64)
    support = np.array([100, 100, 1], dtype=np.uint32)
    selected = MODULE.choose_weights(losses, support, min_support=2, min_advantage_qbits=512)
    assert selected.tolist() == [0, 0, 0]
    selected = MODULE.choose_weights(losses, support, min_support=2, min_advantage_qbits=256)
    assert selected.tolist() == [1, 0, 0]


def test_mixed_grid_preserves_base_for_zero_weight() -> None:
    base = np.array([10000, 50000], dtype=np.uint16)
    endpoint = np.array([50000, 10000], dtype=np.uint16)
    mixed = MODULE.mixed_grid(base, endpoint, (0, 100000))
    assert np.array_equal(mixed[:, 0], base)
    assert np.all((mixed[:, 1] > 0) & (mixed[:, 1] < 65536))
