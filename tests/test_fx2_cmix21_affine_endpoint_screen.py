from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/fx2_cmix21_affine_endpoint_screen.py"
)
SPEC = importlib.util.spec_from_file_location("affine_endpoint_screen", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_affine_fit_uses_complementary_endpoint() -> None:
    rows = 4096
    truth = np.tile(np.array([0, 1, 1, 0], dtype=np.float64), rows // 4)
    base = np.where(truth != 0, 39000, 26536).astype(np.uint16)
    endpoint = np.where(truth != 0, 50000, 15536).astype(np.uint16)
    weights, means, scales = MODULE.fit_affine(
        base,
        endpoint,
        truth,
        train_end=3072,
        chunk_rows=257,
        iterations=12,
        l2=1e-5,
    )
    assert len(weights) == 3
    result = MODULE.evaluate(
        base,
        endpoint,
        truth,
        3072,
        rows,
        weights,
        means,
        scales,
        chunk_rows=257,
        block_rows=256,
        raw_scope_bytes=512,
        total_rows=rows,
    )
    assert result["gain_qbits"] > 0
    assert result["regressing_blocks"] == 0


def test_sigmoid_is_stable_for_large_logits() -> None:
    values = np.array([-1000.0, 0.0, 1000.0])
    probabilities = MODULE.sigmoid(values)
    assert probabilities[0] == 0.0
    assert probabilities[1] == 0.5
    assert probabilities[2] == 1.0
