"""Paired lineage-level statistics, copied verbatim from `self_transform_neural_proposer_v3/run_study_v3.py`."""
from __future__ import annotations

import math
import statistics
from typing import Any


def _student_t_two_sided_p(t_stat: float, df: int) -> float:
    """Exact two-sided Student-t p-value via numerical Simpson integration of the t PDF."""
    if df <= 0 or not math.isfinite(t_stat):
        return 1.0
    t_abs = abs(float(t_stat))
    if t_abs == 0.0:
        return 1.0
    # Transform u = df / (df + x^2) in (0, 1]; P(|T| >= t_abs) = I_{u0}(df/2, 1/2)
    u0 = float(df) / (float(df) + t_abs * t_abs)
    a = 0.5 * float(df)
    b = 0.5
    log_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    n_steps = 2000
    h = u0 / n_steps

    def f(u: float) -> float:
        if u <= 0.0:
            return 0.0
        if u >= 1.0:
            u = 1.0 - 1e-15
        return math.exp((a - 1.0) * math.log(u) + (b - 1.0) * math.log(1.0 - u) - log_beta)

    acc = f(0.0) + f(u0)
    for i in range(1, n_steps):
        acc += (4.0 if (i % 2 == 1) else 2.0) * f(i * h)
    p = (h / 3.0) * acc
    return max(0.0, min(1.0, p))


def exact_sign_two_sided_p(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(math.comb(n, j) for j in range(k + 1)) / float(2 ** n)
    return min(1.0, 2.0 * tail)


def exact_wilcoxon_signed_rank_two_sided_p(diffs: list[float], tol: float = 1e-12) -> float:
    """Exact two-sided Wilcoxon signed-rank p-value via full 2^m sign enumeration (exact for m <= 20)."""
    nz = [float(d) for d in diffs if abs(d) > tol]
    m = len(nz)
    if m == 0:
        return 1.0
    abs_sorted = sorted((abs(d), idx) for idx, d in enumerate(nz))
    ranks = [0.0] * m
    i = 0
    while i < m:
        j = i
        while j + 1 < m and abs(abs_sorted[j + 1][0] - abs_sorted[i][0]) <= tol:
            j += 1
        avg_rank = 0.5 * ((i + 1) + (j + 1))
        for k in range(i, j + 1):
            ranks[abs_sorted[k][1]] = avg_rank
        i = j + 1

    w_pos = sum(ranks[idx] for idx, d in enumerate(nz) if d > 0.0)
    total_rank_sum = 0.5 * m * (m + 1)
    obs_dev = abs(w_pos - 0.5 * total_rank_sum)

    extreme = 0
    for mask in range(1 << m):
        s = 0.0
        for bit in range(m):
            if (mask >> bit) & 1:
                s += ranks[bit]
        if abs(s - 0.5 * total_rank_sum) >= obs_dev - 1e-12:
            extreme += 1
    return min(1.0, float(extreme) / float(1 << m))


def paired_lineage_summary(focal_vals: list[float], ref_vals: list[float], higher_is_better: bool) -> dict[str, Any]:
    assert len(focal_vals) == len(ref_vals) and len(focal_vals) >= 2
    n = len(focal_vals)
    # Signed improvement: positive means focal is better than ref
    imp = [
        (f - r) if higher_is_better else (r - f)
        for f, r in zip(focal_vals, ref_vals)
    ]
    raw_diff = [f - r for f, r in zip(focal_vals, ref_vals)]
    mean_diff = statistics.mean(raw_diff)
    sd_diff = statistics.stdev(raw_diff)
    if sd_diff > 1e-15:
        t_stat = mean_diff / (sd_diff / math.sqrt(n))
        t_p = _student_t_two_sided_p(t_stat, df=n - 1)
    elif abs(mean_diff) > 1e-15:
        t_stat = math.copysign(1e9, mean_diff)
        t_p = 0.0
    else:
        t_stat = 0.0
        t_p = 1.0
    wins = sum(1 for x in imp if x > 1e-12)
    losses = sum(1 for x in imp if x < -1e-12)
    ties = n - wins - losses
    return {
        "n_lineages": n,
        "focal_mean": statistics.mean(focal_vals),
        "focal_sd": statistics.stdev(focal_vals),
        "ref_mean": statistics.mean(ref_vals),
        "ref_sd": statistics.stdev(ref_vals),
        "mean_diff_focal_minus_ref": mean_diff,
        "sd_diff": sd_diff,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "t_stat": t_stat,
        "two_sided_t_p": t_p,
        "exact_wilcoxon_two_sided_p": exact_wilcoxon_signed_rank_two_sided_p(imp),
        "exact_sign_two_sided_p": exact_sign_two_sided_p(wins, losses),
        "per_seed_focal_minus_ref": raw_diff,
    }
