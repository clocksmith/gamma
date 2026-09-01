from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


PROGRAM = (
    Path(__file__).resolve().parents[1]
    / "programs/wiki_fiber_fossil_endpoint428_opening1m_q0_v4/program.py"
)


def load_core():
    spec = importlib.util.spec_from_file_location("_fiber_fossil_negated_test", PROGRAM)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def truth_probability(total: int, p1: int, truth: int) -> int:
    return p1 if truth else total - p1


def test_independent_symmetric_kt_mirrors_complemented_donor() -> None:
    core = load_core()
    d_counts = [[0, 0]]
    n_counts = [[0, 0]]
    rows = [(1, 1), (1, 1), (1, 0), (0, 0), (1, 1), (0, 1)] * 8
    for d_bit, truth in rows:
        n_bit = d_bit ^ 1
        d_p1 = core._assign_reliability(core._kt_reliability(d_counts, 0), d_bit)
        n_p1 = core._assign_reliability(core._kt_reliability(n_counts, 0), n_bit)
        assert abs(
            truth_probability(core.TOTAL, d_p1, truth)
            - truth_probability(core.TOTAL, n_p1, truth)
        ) <= 1
        d_counts[0][0 if d_bit == truth else 1] += 1
        n_counts[0][0 if n_bit == truth else 1] += 1


def test_shared_d_reliability_makes_negation_directional() -> None:
    core = load_core()
    d_counts = [[0, 0]]
    observed_strict_separation = False
    for d_bit, truth in [(1, 1)] * 16 + [(0, 0)] * 16:
        n_bit = d_bit ^ 1
        reliability = core._kt_reliability(d_counts, 0)
        d_p1 = core._assign_reliability(reliability, d_bit)
        n_p1 = core._assign_reliability(reliability, n_bit)
        d_truth = truth_probability(core.TOTAL, d_p1, truth)
        n_truth = truth_probability(core.TOTAL, n_p1, truth)
        assert d_truth + n_truth == core.TOTAL
        if reliability > core.TOTAL // 2:
            assert d_truth > n_truth
            observed_strict_separation = True
        d_counts[0][0 if d_bit == truth else 1] += 1
    assert observed_strict_separation
