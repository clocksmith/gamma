from __future__ import annotations

import numpy as np
import pytest

from projects.enwiki9.tools.compact_layer0_blend_screen import (
    mix_signed_native_q16,
)
from projects.enwiki9.tools.compact_layer0_sparse_blend_screen import (
    fit_newton_coefficients,
    mix_sparse_native_q16,
    quantized_sparse_candidates,
)


def test_sparse_single_endpoint_matches_signed_blend() -> None:
    base = np.asarray([8192, 16384, 32768, 49152, 60000], dtype=np.uint16)
    endpoint = np.asarray([12000, 12000, 40000, 42000, 62000], dtype=np.uint16)
    endpoints = endpoint[:, None]

    expected = mix_signed_native_q16(base, endpoint, -225_000)
    actual = mix_sparse_native_q16(
        base, endpoints, np.asarray([-225_000], dtype=np.int64)
    )

    assert np.array_equal(actual, expected)


def test_training_recovers_useful_endpoint_direction() -> None:
    rows = 4000
    base = np.full(rows, 32768, dtype=np.uint16)
    truth = np.asarray([(index % 4) != 0 for index in range(rows)], dtype=np.uint8)
    useful = np.where(truth, 50000, 15536).astype(np.uint16)
    noise = np.where(np.arange(rows) % 2, 45000, 20536).astype(np.uint16)
    endpoints = np.column_stack((useful, noise))

    fitted = fit_newton_coefficients(
        base,
        endpoints,
        truth,
        ridge=0.1,
        iterations=4,
        chunk_rows=500,
    )

    assert fitted[0] > 0.5
    assert abs(fitted[1]) < 0.1


def test_sparse_candidates_are_nested_and_quantized() -> None:
    fitted = np.asarray([0.3014, -0.2026, 0.1002, 0.0501])
    candidates = quantized_sparse_candidates(
        fitted,
        ridge=0.1,
        sparsities=(1, 2, 4),
        quantum_ppm=1_000,
    )

    assert [candidate["nonzero_count"] for candidate in candidates] == [1, 2, 4]
    assert np.array_equal(
        candidates[0]["coefficients_ppm"],
        np.asarray([301_000, 0, 0, 0]),
    )
    assert all(
        np.all(candidate["coefficients_ppm"] % 1_000 == 0)
        for candidate in candidates
    )


def test_sparse_mixer_rejects_bad_dimensions() -> None:
    with pytest.raises(ValueError, match="align"):
        mix_sparse_native_q16(
            np.asarray([32768], dtype=np.uint16),
            np.asarray([[32768, 32768]], dtype=np.uint16),
            np.asarray([1], dtype=np.int64),
        )
