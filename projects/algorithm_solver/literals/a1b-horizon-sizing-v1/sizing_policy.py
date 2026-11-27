#!/usr/bin/env python3
"""Repository-disjoint horizon-dependent vocabulary sizing policy for A1b.

Implements:
- Exact lineage / organization / file-hash leakage detection (`LeakageError`).
- Deterministic strided micro-sketch feature extractor (<=3.5% bytes, capped at 12 KiB).
- Frozen 3-point geometric pilot fallback (K in {64, 512, 4096} with clamped
  quadratic interpolation in log(K + 32)).
- Repository-disjoint curve calibration + 90% upper prediction bound (UPB) on
  excess archive bytes:
    * `strict_conformal` mode: requires >= 9 independent calibration orgs so
      ceil(0.90 * (n + 1)) <= n yields a finite distribution-free 90% conformal
      UPB; otherwise deterministically emits `SWEEP_REQUIRED`.
    * `dev_calibrated` mode: one-sided Student-t 90% prediction bound on
      independent org-level inner-LOLO residuals + query sketch sampling margin;
      emits `SWEEP_REQUIRED` whenever UPB_90 > 2.5% (0.025).
- Token/RAM variant sizing policy under frozen RAM price lambda or hard RAM cap.
"""

from __future__ import annotations

import json
import math
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

import archive_grid as AG

# Frozen hyperparameters (never tuned per evaluation lineage).
SKETCH_FRAC = 0.035
SKETCH_MAX_BYTES = 12_288
SKETCH_MIN_BYTES = 4_096
PROBE_KS: tuple[int, ...] = (64, 512, 2048, 4096)
PILOT_KS: tuple[int, ...] = AG.PILOT_GRID_K  # (64, 512, 4096)
UPB_ALPHA = 0.10  # 90% upper prediction bound
SEALED_REGRET_BAR = 0.020  # 2.0% sealed breach bar on max(full_oracle_regret_100KB, full_oracle_regret_100MB)
EXCESS_ABSTAIN_THRESHOLD = 0.025  # Legacy dev-mode threshold kept for Stage-1 diagnostic continuity
MIN_CONFORMAL_ORGS = 9  # ceil(0.90 * (n + 1)) <= n  <=>  n >= 9
FRAMING_EOF_BYTES_EST = 1.5  # ~1 B varint + ~0.5 B byte-alignment/EOF overhead per record


class LeakageError(RuntimeError):
    """Raised immediately when fit, calibration, or evaluation lineages overlap."""


def assert_disjoint_lineages(
    fit_meta: dict[str, Any],
    cal_metas: list[dict[str, Any]],
    eval_meta: dict[str, Any] | None = None,
    allow_same_collection_eval_diagnostic: bool = False,
) -> None:
    """Enforce strict fit vs calibration vs evaluation separation.

    Checks lineage IDs, organization IDs, AND exact file SHA-256 hashes.
    Also rejects duplicate lineages or shared file hashes inside calibration
    (prevents file-level resampling within a repository).
    """
    fit_lid = fit_meta["lineage_id"]
    fit_org = fit_meta["org_id"]
    fit_hashes = set(fit_meta["file_hashes"])

    seen_cal_lids: set[str] = set()
    seen_cal_hashes: dict[str, str] = {}
    cal_orgs: set[str] = set()

    for cm in cal_metas:
        clid = cm["lineage_id"]
        corg = cm["org_id"]
        chashes = set(cm["file_hashes"])
        if clid == fit_lid or corg == fit_org:
            raise LeakageError(
                f"fit lineage/org leaked into calibration: {clid} (org={corg}) matches fit {fit_lid} (org={fit_org})"
            )
        shared_fit = chashes & fit_hashes
        if shared_fit:
            raise LeakageError(
                f"fit file hash leaked into calibration lineage {clid}: {len(shared_fit)} shared files"
            )
        if clid in seen_cal_lids:
            raise LeakageError(f"duplicate calibration lineage_id: {clid}")
        seen_cal_lids.add(clid)
        cal_orgs.add(corg)
        for h in chashes:
            prev = seen_cal_hashes.get(h)
            if prev is not None:
                raise LeakageError(
                    f"calibration lineages {prev} and {clid} share exact file hash {h[:12]} (resampling/duplication forbidden)"
                )
            seen_cal_hashes[h] = clid

    if eval_meta is not None:
        elid = eval_meta["lineage_id"]
        eorg = eval_meta["org_id"]
        ehashes = set(eval_meta["file_hashes"])
        if elid == fit_lid:
            raise LeakageError(f"fit lineage {fit_lid} leaked into evaluation")
        if (not allow_same_collection_eval_diagnostic) and eorg == fit_org:
            raise LeakageError(
                f"fit organization {fit_org} leaked into evaluation lineage {elid}"
            )
        shared_fit = ehashes & fit_hashes
        if shared_fit:
            raise LeakageError(
                f"fit file hash leaked into evaluation lineage {elid}: {len(shared_fit)} shared files"
            )
        if elid in seen_cal_lids:
            raise LeakageError(f"calibration lineage {elid} leaked into evaluation")
        if eorg in cal_orgs:
            raise LeakageError(
                f"calibration organization {eorg} leaked into evaluation lineage {elid}"
            )
        shared_cal = ehashes & set(seen_cal_hashes.keys())
        if shared_cal:
            raise LeakageError(
                f"calibration file hash leaked into evaluation lineage {elid}: {len(shared_cal)} shared files"
            )


def make_deterministic_sketch(
    docs: list[bytes],
    frac: float = SKETCH_FRAC,
    max_bytes: int = SKETCH_MAX_BYTES,
    min_bytes: int = SKETCH_MIN_BYTES,
    target_min_records: int = 12,
) -> list[bytes]:
    """Select a deterministic golden-ratio strided byte-budget sketch across records.

    Caps each sampled record slice at `max(256, budget // target_min_records)` bytes
    so repositories with large files (e.g. 10 KiB average) still contribute at least
    ~12 distinct files to the sketch rather than 1-2 files.
    """
    total = sum(len(d) for d in docs)
    if total == 0 or not docs:
        return []
    budget = min(total, max(min_bytes, min(max_bytes, int(total * frac))))
    n = len(docs)
    per_rec_cap = max(256, budget // max(1, min(n, target_min_records)))
    step = max(1, int(round(n * 0.61803398875)))
    while n > 1 and math.gcd(step, n) != 1:
        step += 1

    sketch: list[bytes] = []
    acc = 0
    idx = 0
    for _ in range(n):
        d = docs[idx]
        idx = (idx + step) % n
        if not d:
            continue
        if len(d) > per_rec_cap:
            # Deterministic centered slice to avoid sampling only file headers/licenses.
            start = (len(d) - per_rec_cap) // 2
            piece = d[start : start + per_rec_cap]
        else:
            piece = d
        if acc + len(piece) <= budget or not sketch:
            sketch.append(piece)
            acc += len(piece)
            if acc >= budget:
                break
        else:
            rem = budget - acc
            if rem >= 256:
                start = max(0, (len(piece) - rem) // 2)
                sketch.append(piece[start : start + rem])
                acc += rem
            break
    return sketch


def extract_micro_sketch_features(
    docs: list[bytes],
    dicts_by_k: dict[int, AG.Dictionary],
    lengths_by_k: dict[int, list[int]],
    probe_ks: tuple[int, ...] = PROBE_KS,
) -> dict[str, Any]:
    """Extract cheap micro-sketch body-rate and token-rate probes with paired SEs.

    Returns rates, per-record paired rate vectors, and exact measured work.
    """
    t0 = time.perf_counter()
    full_S = sum(len(d) for d in docs)
    full_F = len(docs)
    sketch = make_deterministic_sketch(docs)
    sk_S = sum(len(d) for d in sketch)
    sk_F = len(sketch)
    true_mean_rec = full_S / max(1, full_F)
    sk_mean_rec = sk_S / max(1, sk_F)
    framing_delta = FRAMING_EOF_BYTES_EST * (1.0 / true_mean_rec - 1.0 / sk_mean_rec)

    edge_scans = 0
    edge_matches = 0
    dp_relaxations = 0
    probes_r: dict[int, float] = {}
    probes_tok: dict[int, float] = {}
    per_rec_r: dict[int, list[float]] = {}
    per_rec_tok: dict[int, list[float]] = {}
    rec_weights = np.array([max(1, len(d)) for d in sketch], dtype=float)
    rec_weights /= rec_weights.sum()

    for K in probe_ks:
        d = dicts_by_k[K]
        lengths = lengths_by_k[K]
        eof_bits = lengths[d.EOF]
        tot_body = AG.varint_len(sk_F)
        tot_toks = 0
        r_vec: list[float] = []
        t_vec: list[float] = []
        for raw in sketch:
            ed, sc, ma = d.edges(raw)
            syms, pb, rel = AG.parse_bits(ed, lengths, d.ESC)
            edge_scans += sc
            edge_matches += ma
            dp_relaxations += rel
            pbytes = (pb + eof_bits + 7) // 8
            rec_body = AG.varint_len(pbytes) + pbytes
            tot_body += rec_body
            tot_toks += len(syms)
            r_vec.append(rec_body / max(1, len(raw)))
            t_vec.append(len(syms) / max(1, len(raw)))
        probes_r[K] = max(0.01, (tot_body / sk_S) + framing_delta)
        probes_tok[K] = tot_toks / sk_S
        per_rec_r[K] = r_vec
        per_rec_tok[K] = t_vec

    # Compute paired SE matrix between probe points across sampled records.
    paired_se_r: dict[tuple[int, int], float] = {}
    paired_se_tok: dict[tuple[int, int], float] = {}
    m = len(sketch)
    for k1 in probe_ks:
        a_r = np.array(per_rec_r[k1], dtype=float)
        a_t = np.array(per_rec_tok[k1], dtype=float)
        for k2 in probe_ks:
            if k1 == k2:
                paired_se_r[(k1, k2)] = 0.0
                paired_se_tok[(k1, k2)] = 0.0
            elif m > 1:
                diff_r = a_r - np.array(per_rec_r[k2], dtype=float)
                diff_t = a_t - np.array(per_rec_tok[k2], dtype=float)
                paired_se_r[(k1, k2)] = float(np.std(diff_r, ddof=1) / math.sqrt(m))
                paired_se_tok[(k1, k2)] = float(np.std(diff_t, ddof=1) / math.sqrt(m))
            else:
                paired_se_r[(k1, k2)] = 0.02
                paired_se_tok[(k1, k2)] = 0.02

    elapsed = time.perf_counter() - t0
    return {
        "sketch_bytes": sk_S,
        "sketch_records": sk_F,
        "sketch_fraction": sk_S / max(1, full_S),
        "full_bytes": full_S,
        "full_records": full_F,
        "probe_ks": list(probe_ks),
        "probes_r": probes_r,
        "probes_tok": probes_tok,
        "paired_se_r": paired_se_r,
        "paired_se_tok": paired_se_tok,
        "work": {
            "wall_seconds": elapsed,
            "edge_scans": edge_scans,
            "edge_matches": edge_matches,
            "dp_relaxations": dp_relaxations,
            "bit_writes": 0,
            "total_ops": edge_scans + edge_matches + dp_relaxations,
            "peak_rss_bytes": AG.current_peak_rss_bytes(),
        },
    }


def interpolate_from_probes(
    probes: dict[int, float],
    grid_ks: tuple[int, ...] = AG.PRIMARY_GRID,
    cal_bias: dict[int, float] | None = None,
) -> dict[int, float]:
    """Piecewise linear interpolation in log(K + 32) across probe points.

    Clamps downward extrapolation below min(probe_ks) so a non-convex bump at an
    intermediate probe point can never produce an artificial sub-minimum at K=0.
    """
    pks = sorted(probes.keys())
    pxs = [math.log(k + 32.0) for k in pks]
    pys = [float(probes[k]) for k in pks]
    out: dict[int, float] = {}
    for K in grid_ks:
        x = math.log(K + 32.0)
        if K <= pks[0]:
            slope = (pys[1] - pys[0]) / (pxs[1] - pxs[0])
            # Only allow rate to increase (or stay flat) when shrinking K below pks[0].
            slope = min(0.0, slope)
            y = pys[0] + slope * (x - pxs[0])
        elif K >= pks[-1]:
            y = pys[-1]
        else:
            y = pys[-1]
            for i in range(len(pks) - 1):
                if pks[i] <= K <= pks[i + 1]:
                    t = (x - pxs[i]) / (pxs[i + 1] - pxs[i])
                    y = pys[i] + t * (pys[i + 1] - pys[i])
                    break
        if cal_bias is not None:
            y += float(cal_bias.get(K, 0.0))
        out[K] = max(0.005, y)
    return out


def pilot_predict_curve_from_3pt(
    r_pilot: dict[int, float],
    grid_ks: tuple[int, ...] = AG.PRIMARY_GRID,
) -> dict[int, float]:
    """Frozen 3-point geometric pilot curve estimator from K in {64, 512, 4096}.

    Fits the unique quadratic in x = log(K + 32) through the 3 measured points
    for interior K in [64, 4096], with safety clamps:
    - Exact agreement at the 3 measured points (K in {64, 512, 4096}).
    - Below K=64: never extrapolates below r_64 (uses non-positive secant slope).
    - Interior points cannot dip below min(r_pilot) - 0.5 * |r_512 - r_64| to
      prevent Runge overshoot on adversarial non-convex bumps.
    """
    pks = sorted(r_pilot.keys())
    if len(pks) != 3:
        raise ValueError(f"3-point geometric pilot requires exactly 3 points, got {pks}")
    xs = [math.log(k + 32.0) for k in pks]
    ys = [float(r_pilot[k]) for k in pks]
    floor_interior = min(ys) - 0.5 * abs(ys[1] - ys[0])
    out: dict[int, float] = {}
    for K in grid_ks:
        if K in r_pilot:
            out[K] = float(r_pilot[K])
            continue
        x = math.log(K + 32.0)
        if K < pks[0]:
            slope = min(0.0, (ys[1] - ys[0]) / (xs[1] - xs[0]))
            out[K] = max(ys[0], ys[0] + slope * (x - xs[0]))
        elif K > pks[-1]:
            out[K] = ys[-1]
        else:
            val = 0.0
            for i in range(3):
                li = 1.0
                for j in range(3):
                    if i != j:
                        li *= (x - xs[j]) / (xs[i] - xs[j])
                val += ys[i] * li
            # If middle point is a local bump (ys[1] > max(ys[0], ys[2])), do not bow
            # downward below min(ys[0], ys[2]) — use piecewise linear instead!
            if ys[1] > ys[0] and ys[1] > ys[2]:
                if K < pks[1]:
                    t = (x - xs[0]) / (xs[1] - xs[0])
                    val = ys[0] + t * (ys[1] - ys[0])
                else:
                    t = (x - xs[1]) / (xs[2] - xs[1])
                    val = ys[1] + t * (ys[2] - ys[1])
            else:
                val = max(floor_interior, val)
            out[K] = max(0.005, val)
    return out


def select_prefix_from_curve(
    header_bytes_by_k: dict[int, int],
    r_by_k: dict[int, float | Fraction],
    M: int,
    grid_ks: tuple[int, ...] = AG.PRIMARY_GRID,
) -> int:
    """Pick argmin_K (H_K + M * r_K) with exact tie-break toward smaller H_K, then smaller K."""
    cands = [
        {"K": K, "header_bytes": int(header_bytes_by_k[K]), "r_hat": r_by_k[K]}
        for K in grid_ks
    ]
    return int(AG.select_best_prefix_exact(cands, M)["K"])


def select_prefix_pilot_3pt(
    header_bytes_by_k: dict[int, int],
    r_pilot: dict[int, float],
    M: int,
    grid_ks: tuple[int, ...] = AG.PRIMARY_GRID,
) -> tuple[int, dict[int, float]]:
    """Run the frozen 3-point geometric pilot selection rule on measured pilot rates."""
    pred_curve = pilot_predict_curve_from_3pt(r_pilot, grid_ks=grid_ks)
    chosen_k = select_prefix_from_curve(header_bytes_by_k, pred_curve, M, grid_ks=grid_ks)
    return chosen_k, pred_curve


def compute_sketch_uncertainty_margin(
    feat: dict[str, Any],
    header_bytes_by_k: dict[int, int],
    pred_r: dict[int, float],
    chosen_k: int,
    M: int,
    grid_ks: tuple[int, ...] = AG.PRIMARY_GRID,
) -> float:
    """Compute query-specific sketch sampling uncertainty on relative archive bytes.

    Propagates paired per-record SE from the nearest probe points to evaluate
    how much a rival prefix could beat `chosen_k` under a 1-SE sampling fluctuation.
    """
    pks = sorted(feat["probes_r"].keys())
    paired_se = feat["paired_se_r"]

    def nearest_probe(k: int) -> int:
        return min(pks, key=lambda pk: abs(math.log(k + 32.0) - math.log(pk + 32.0)))

    pk_chosen = nearest_probe(chosen_k)
    j_chosen = header_bytes_by_k[chosen_k] + M * pred_r[chosen_k]
    worst_gain = 0.0
    for K in grid_ks:
        if K == chosen_k:
            continue
        pk_k = nearest_probe(K)
        se = paired_se.get((pk_k, pk_chosen), 0.0)
        if pk_k == pk_chosen:
            # Small interpolation uncertainty between adjacent non-probe prefixes.
            se = 0.0025
        j_k = header_bytes_by_k[K] + M * pred_r[K]
        # Positive if a 1-SE favorable shift in K could beat chosen_k.
        potential_better = (j_chosen - (j_k - M * se)) / max(1.0, j_chosen)
        if potential_better > worst_gain:
            worst_gain = potential_better
    return max(0.0, float(worst_gain))


class HorizonSizingPolicy:
    """Repository-disjoint calibrated sizing policy with 90% UPB abstain gate.

    Two explicit calibration regimes:
    - `strict_conformal=True`: exact finite-sample distribution-free 90% conformal
      UPB requiring >= 9 independent calibration organizations. When n_orgs < 9,
      conformal UPB is +inf and the policy emits `SWEEP_REQUIRED`.
    - `strict_conformal=False` (dev_calibrated): one-sided Student-t 90% prediction
      bound on org-disjoint inner-LOLO excess residuals + query sketch uncertainty
      margin, emitting `SWEEP_REQUIRED` whenever UPB_90 > 2.5%.
    """

    def __init__(
        self,
        header_bytes_by_k: dict[int, int],
        grid_ks: tuple[int, ...] = AG.PRIMARY_GRID,
        strict_conformal: bool = False,
        abstain_threshold: float = EXCESS_ABSTAIN_THRESHOLD,
        min_conformal_orgs: int = MIN_CONFORMAL_ORGS,
    ) -> None:
        self.header_bytes_by_k = dict(header_bytes_by_k)
        self.grid_ks = tuple(grid_ks)
        self.strict_conformal = strict_conformal
        self.abstain_threshold = abstain_threshold
        self.min_conformal_orgs = min_conformal_orgs

        self.fit_meta: dict[str, Any] | None = None
        self.cal_metas: list[dict[str, Any]] = []
        self.n_cal_lineages: int = 0
        self.n_cal_orgs: int = 0
        self.conformal_support_sufficient: bool = False
        self.cal_bias_by_k: dict[int, float] = {K: 0.0 for K in self.grid_ks}
        self.cal_residuals_by_M: dict[int, dict[str, Any]] = {}
        self.fit_wall_seconds: float = 0.0

    def fit_calibration(
        self,
        fit_meta: dict[str, Any],
        cal_records: list[dict[str, Any]],
        horizons: tuple[int, ...] = AG.PRIMARY_HORIZONS,
    ) -> dict[str, Any]:
        """Fit curve bias and calibrate 90% UPB strictly on org-disjoint calibration records.

        Each item in `cal_records` must provide:
          - meta: lineage metadata dict (lineage_id, org_id, file_hashes)
          - feat: output of `extract_micro_sketch_features`
          - true_r_by_k: {K: exact r_hat_K on primary chain}
          - oracle_obj_by_M: {M: exact full selector-by-K oracle bytes at horizon M}
          - same_oracle_obj_by_M: {M: exact same-chain oracle bytes at horizon M}
        """
        t0 = time.perf_counter()
        cal_metas = [rec["meta"] for rec in cal_records]
        assert_disjoint_lineages(fit_meta, cal_metas, eval_meta=None)

        self.fit_meta = fit_meta
        self.cal_metas = cal_metas
        self.n_cal_lineages = len(cal_records)
        orgs = sorted({rec["meta"]["org_id"] for rec in cal_records})
        self.n_cal_orgs = len(orgs)
        self.conformal_support_sufficient = self.n_cal_orgs >= self.min_conformal_orgs

        # 1. Fit mean bias per K across calibration organizations (equal weight per org!).
        org_to_recs: dict[str, list[dict[str, Any]]] = {o: [] for o in orgs}
        for rec in cal_records:
            org_to_recs[rec["meta"]["org_id"]].append(rec)

        def _fit_bias(selected_orgs: list[str]) -> dict[int, float]:
            bias: dict[int, float] = {}
            for K in self.grid_ks:
                org_means = []
                for o in selected_orgs:
                    errs = []
                    for rec in org_to_recs[o]:
                        raw_p = interpolate_from_probes(rec["feat"]["probes_r"], self.grid_ks)
                        errs.append(rec["true_r_by_k"][K] - raw_p[K])
                    org_means.append(float(np.mean(errs)))
                bias[K] = float(np.mean(org_means)) if org_means else 0.0
            return bias

        self.cal_bias_by_k = _fit_bias(orgs)

        # 2. Inner org-disjoint LOLO-CV to calibrate honest out-of-org excess residuals.
        self.cal_residuals_by_M = {}
        for M in horizons:
            org_excess_full: list[float] = []
            org_excess_same: list[float] = []
            org_margins: list[float] = []
            for hold_org in orgs:
                inner_orgs = [o for o in orgs if o != hold_org]
                inner_bias = _fit_bias(inner_orgs) if inner_orgs else {K: 0.0 for K in self.grid_ks}
                ex_f_list, ex_s_list, m_list = [], [], []
                for rec in org_to_recs[hold_org]:
                    pred_r = interpolate_from_probes(
                        rec["feat"]["probes_r"], self.grid_ks, cal_bias=inner_bias
                    )
                    k_hat = select_prefix_from_curve(
                        self.header_bytes_by_k, pred_r, M, grid_ks=self.grid_ks
                    )
                    chosen_obj = self.header_bytes_by_k[k_hat] + M * rec["true_r_by_k"][k_hat]
                    opt_f = rec["oracle_obj_by_M"][M]
                    opt_s = rec["same_oracle_obj_by_M"][M]
                    ex_f_list.append(max(0.0, (chosen_obj / opt_f) - 1.0))
                    ex_s_list.append(max(0.0, (chosen_obj / opt_s) - 1.0))
                    m_list.append(
                        compute_sketch_uncertainty_margin(
                            rec["feat"], self.header_bytes_by_k, pred_r, k_hat, M, self.grid_ks
                        )
                    )
                # Conservative aggregation per org: max across codebases in that org.
                org_excess_full.append(max(ex_f_list))
                org_excess_same.append(max(ex_s_list))
                org_margins.append(float(np.mean(m_list)))

            arr_same = np.array(org_excess_same, dtype=float)
            arr_full = np.array(org_excess_full, dtype=float)
            n = len(arr_same)
            mean_s = float(np.mean(arr_same)) if n > 0 else float("inf")
            sd_s = float(np.std(arr_same, ddof=1)) if n > 1 else float("inf")
            mean_f = float(np.mean(arr_full)) if n > 0 else float("inf")
            sd_f = float(np.std(arr_full, ddof=1)) if n > 1 else float("inf")
            med_margin = float(np.median(org_margins)) if org_margins else 0.0

            # Exact finite-sample conformal 90% quantile index: q = ceil((1 - alpha) * (n + 1))
            # Calibrated on reducible same-chain sizing excess (the excess a same-chain pilot
            # can actually eliminate); full-oracle excess stats are also logged alongside.
            q_idx = math.ceil((1.0 - UPB_ALPHA) * (n + 1))
            if q_idx <= n and n >= self.min_conformal_orgs:
                conformal_q90_same = float(np.sort(arr_same)[q_idx - 1])
                conformal_q90_full = float(np.sort(arr_full)[q_idx - 1])
            else:
                conformal_q90_same = float("inf")
                conformal_q90_full = float("inf")

            if n >= 2:
                t_crit = float(stats.t.ppf(1.0 - UPB_ALPHA, df=n - 1))
                dev_t_base_upb_same = mean_s + t_crit * sd_s * math.sqrt(1.0 + 1.0 / n)
                dev_t_base_upb_full = mean_f + t_crit * sd_f * math.sqrt(1.0 + 1.0 / n)
            else:
                t_crit = float("inf")
                dev_t_base_upb_same = float("inf")
                dev_t_base_upb_full = float("inf")

            self.cal_residuals_by_M[int(M)] = {
                "n_cal_orgs": n,
                "org_excess_same": [round(x, 6) for x in org_excess_same],
                "org_excess_full": [round(x, 6) for x in org_excess_full],
                "mean_excess_same": mean_s,
                "sd_excess_same": sd_s,
                "mean_excess_full": mean_f,
                "sd_excess_full": sd_f,
                "median_sketch_margin": med_margin,
                "conformal_q_index": q_idx,
                "conformal_90_base_upb": None if math.isinf(conformal_q90_same) else conformal_q90_same,
                "conformal_90_base_upb_full": None if math.isinf(conformal_q90_full) else conformal_q90_full,
                "student_t_crit_90": None if math.isinf(t_crit) else t_crit,
                "dev_t_90_base_upb": None if math.isinf(dev_t_base_upb_same) else dev_t_base_upb_same,
                "dev_t_90_base_upb_full": None if math.isinf(dev_t_base_upb_full) else dev_t_base_upb_full,
            }

        self.fit_wall_seconds = time.perf_counter() - t0
        return {
            "n_cal_lineages": self.n_cal_lineages,
            "n_cal_orgs": self.n_cal_orgs,
            "conformal_support_sufficient": self.conformal_support_sufficient,
            "min_conformal_orgs": self.min_conformal_orgs,
            "fit_wall_seconds": self.fit_wall_seconds,
            "cal_bias_by_k": {str(k): round(v, 6) for k, v in self.cal_bias_by_k.items()},
            "residuals_by_M": {str(k): v for k, v in self.cal_residuals_by_M.items()},
        }

    def predict(
        self,
        eval_meta: dict[str, Any],
        feat: dict[str, Any],
        M: int,
        allow_same_collection_eval_diagnostic: bool = False,
    ) -> dict[str, Any]:
        """Predict K(M), compute 90% UPB, and decide direct pick vs SWEEP_REQUIRED."""
        if self.fit_meta is None:
            raise RuntimeError("policy must be calibrated with fit_calibration() before predict()")
        assert_disjoint_lineages(
            self.fit_meta,
            self.cal_metas,
            eval_meta=eval_meta,
            allow_same_collection_eval_diagnostic=allow_same_collection_eval_diagnostic,
        )

        pred_r = interpolate_from_probes(
            feat["probes_r"], self.grid_ks, cal_bias=self.cal_bias_by_k
        )
        k_pred = select_prefix_from_curve(
            self.header_bytes_by_k, pred_r, M, grid_ks=self.grid_ks
        )
        sketch_margin = compute_sketch_uncertainty_margin(
            feat, self.header_bytes_by_k, pred_r, k_pred, M, self.grid_ks
        )

        # Look up horizon-specific calibration stats (or nearest calibrated horizon).
        cal_M = min(self.cal_residuals_by_M.keys(), key=lambda hm: abs(math.log(hm) - math.log(M)))
        cal_info = self.cal_residuals_by_M[cal_M]
        extra_margin = max(0.0, sketch_margin - cal_info["median_sketch_margin"])

        conf_base = cal_info["conformal_90_base_upb"]
        dev_base = cal_info["dev_t_90_base_upb"]
        dev_base_full = cal_info["dev_t_90_base_upb_full"]
        conformal_upb = (
            float("inf")
            if (not self.conformal_support_sufficient or conf_base is None)
            else max(conf_base + extra_margin, sketch_margin)
        )
        dev_t_upb = float("inf") if dev_base is None else max(dev_base + extra_margin, sketch_margin)
        dev_t_upb_full = (
            float("inf") if dev_base_full is None else max(dev_base_full + extra_margin, sketch_margin)
        )

        if self.strict_conformal:
            active_upb = conformal_upb
            if not self.conformal_support_sufficient:
                decision = "SWEEP_REQUIRED"
                reason = f"insufficient_lineage_support (n_cal_orgs={self.n_cal_orgs} < {self.min_conformal_orgs})"
            elif active_upb > self.abstain_threshold:
                decision = "SWEEP_REQUIRED"
                reason = f"conformal_upb90_exceeds_threshold ({active_upb:.4f} > {self.abstain_threshold:.4f})"
            else:
                decision = "DIRECT_PICK"
                reason = "conformal_upb90_within_threshold"
        else:
            active_upb = dev_t_upb
            if self.n_cal_orgs < 2:
                decision = "SWEEP_REQUIRED"
                reason = f"insufficient_lineage_support (n_cal_orgs={self.n_cal_orgs} < 2)"
            elif active_upb > self.abstain_threshold:
                decision = "SWEEP_REQUIRED"
                reason = f"dev_upb90_exceeds_threshold ({active_upb:.4f} > {self.abstain_threshold:.4f})"
            else:
                decision = "DIRECT_PICK"
                reason = "dev_upb90_within_threshold"

        return {
            "lineage_id": eval_meta["lineage_id"],
            "M": int(M),
            "decision": decision,
            "reason": reason,
            "predicted_K": int(k_pred),
            "predicted_r_by_k": {str(k): round(v, 6) for k, v in pred_r.items()},
            "sketch_uncertainty_margin": sketch_margin,
            "extra_sketch_margin": extra_margin,
            "upb_90_active": None if math.isinf(active_upb) else active_upb,
            "upb_90_conformal": None if math.isinf(conformal_upb) else conformal_upb,
            "upb_90_dev_t": None if math.isinf(dev_t_upb) else dev_t_upb,
            "upb_90_dev_t_full": None if math.isinf(dev_t_upb_full) else dev_t_upb_full,
            "abstain_threshold": self.abstain_threshold,
            "conformal_support_sufficient": self.conformal_support_sufficient,
            "n_cal_orgs": self.n_cal_orgs,
            "min_conformal_orgs": self.min_conformal_orgs,
        }


# ---- Token / RAM variant helpers -------------------------------------------

def select_prefix_token_ram_priced(
    ram_by_k: dict[int, int],
    tau_by_k: dict[int, float | Fraction],
    M: int,
    ram_price_lambda: float,
    grid_ks: tuple[int, ...] = AG.PRIMARY_GRID,
) -> int:
    """Minimize lambda * RAM_K + M * tau_K; exact ties prefer smaller RAM_K, then smaller K."""
    lam = Fraction(str(ram_price_lambda))

    def key(K: int) -> tuple[Fraction, int, int]:
        t_val = tau_by_k[K]
        t_frac = t_val if isinstance(t_val, Fraction) else Fraction(str(t_val))
        obj = lam * Fraction(int(ram_by_k[K])) + Fraction(int(M)) * t_frac
        return (obj, int(ram_by_k[K]), int(K))

    return min(grid_ks, key=key)


def select_prefix_token_ram_capped(
    ram_by_k: dict[int, int],
    tau_by_k: dict[int, float | Fraction],
    ram_cap_bytes: int,
    grid_ks: tuple[int, ...] = AG.PRIMARY_GRID,
) -> int:
    """Minimize tau_K subject to RAM_K <= ram_cap_bytes; exact ties prefer smaller RAM_K."""
    eligible = [K for K in grid_ks if ram_by_k[K] <= ram_cap_bytes]
    if not eligible:
        raise ValueError(f"no prefix satisfies RAM_K <= {ram_cap_bytes}")

    def key(K: int) -> tuple[Fraction, int, int]:
        t_val = tau_by_k[K]
        t_frac = t_val if isinstance(t_val, Fraction) else Fraction(str(t_val))
        return (t_frac, int(ram_by_k[K]), int(K))

    return min(eligible, key=key)


# ---- Strict Two-Stage Split-Conformal Protocol (Fixes Barber et al. LOO Pitfall) ----

def deserialize_sketch_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    """Convert JSON-serialized calibration sketch receipt back to integer-keyed feature dict."""
    probes_r = {int(k): float(v) for k, v in receipt["probes_r"].items()}
    probes_tok = {int(k): float(v) for k, v in receipt["probes_tok"].items()}
    paired_se_r = {}
    for pair_key, val in receipt["paired_se_r"].items():
        k1, k2 = pair_key.split(":")
        paired_se_r[(int(k1), int(k2))] = float(val)
    paired_se_tok = {}
    for pair_key, val in receipt["paired_se_tok"].items():
        k1, k2 = pair_key.split(":")
        paired_se_tok[(int(k1), int(k2))] = float(val)
    return {
        "sketch_bytes": int(receipt["sketch_bytes"]),
        "sketch_records": int(receipt["sketch_records"]),
        "sketch_fraction": float(receipt["sketch_fraction"]),
        "full_bytes": int(receipt["full_bytes"]),
        "full_records": int(receipt["full_records"]),
        "probe_ks": [int(k) for k in receipt["probe_ks"]],
        "probes_r": probes_r,
        "probes_tok": probes_tok,
        "paired_se_r": paired_se_r,
        "paired_se_tok": paired_se_tok,
        "work": dict(receipt["work"]),
    }


def assert_three_way_disjoint(
    fit_meta: dict[str, Any],
    predictor_fit_metas: list[dict[str, Any]],
    calibration_metas: list[dict[str, Any]],
) -> None:
    """Enforce strict 3-way separation: chain-fit vs predictor-fit vs split-conformal calibration."""
    # 1. Chain-fit vs predictor-fit (also checks no duplicates/hash overlap inside predictor-fit)
    assert_disjoint_lineages(fit_meta, predictor_fit_metas, eval_meta=None)
    # 2. Chain-fit vs calibration (also checks no duplicates/hash overlap inside calibration)
    assert_disjoint_lineages(fit_meta, calibration_metas, eval_meta=None)

    # 3. Predictor-fit vs calibration: zero overlap on org_id, lineage_id, OR file SHA-256!
    pf_lids = {m["lineage_id"] for m in predictor_fit_metas}
    pf_orgs = {m["org_id"].lower() for m in predictor_fit_metas}
    pf_hashes: set[str] = set()
    for m in predictor_fit_metas:
        pf_hashes.update(m["file_hashes"])

    seen_cal_orgs: set[str] = set()
    for cm in calibration_metas:
        clid = cm["lineage_id"]
        corg_l = cm["org_id"].lower()
        if corg_l in seen_cal_orgs:
            raise LeakageError(
                f"duplicate calibration organization {cm['org_id']} (each calibration unit must be an independent org)"
            )
        seen_cal_orgs.add(corg_l)
        if clid in pf_lids:
            raise LeakageError(f"predictor-fit lineage {clid} leaked into split-conformal calibration")
        if corg_l in pf_orgs:
            raise LeakageError(f"predictor-fit org {cm['org_id']} leaked into split-conformal calibration")
        shared = set(cm["file_hashes"]) & pf_hashes
        if shared:
            raise LeakageError(
                f"predictor-fit file hash leaked into calibration lineage {clid}: {len(shared)} shared files"
            )


class LockedHorizonPredictor:
    """Stage-1 locked predictor fitted strictly on predictor-fit orgs (zero calibration data).

    Serialized canonically without volatile timing fields so its SHA-256 hash
    (`locked_predictor_sha256`) uniquely pins the exact deployed function evaluated
    in Stage 2 split-conformal calibration.
    """

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.primary_chain: str = str(payload["primary_chain"])
        self.grid_ks: tuple[int, ...] = tuple(int(k) for k in payload["grid_ks"])
        self.probe_ks: tuple[int, ...] = tuple(int(k) for k in payload["probe_ks"])
        self.pilot_ks: tuple[int, ...] = tuple(int(k) for k in payload["pilot_ks"])
        self.header_bytes_by_k: dict[int, int] = {
            int(k): int(v) for k, v in payload["header_bytes_by_k"].items()
        }
        self.cal_bias_by_k: dict[int, float] = {
            int(k): float(v) for k, v in payload["cal_bias_by_k"].items()
        }

    @classmethod
    def fit_and_lock(
        cls,
        fit_meta: dict[str, Any],
        predictor_fit_records: list[dict[str, Any]],
        header_bytes_by_k: dict[int, int],
        primary_chain_sha256: str,
        grid_ks: tuple[int, ...] = AG.PRIMARY_GRID,
        probe_ks: tuple[int, ...] = PROBE_KS,
        pilot_ks: tuple[int, ...] = PILOT_KS,
    ) -> tuple["LockedHorizonPredictor", float]:
        """Stage 1: fit ONE exact predictor on predictor-fit orgs only and lock its weights."""
        t0 = time.perf_counter()
        pf_metas = [rec["meta"] for rec in predictor_fit_records]
        assert_disjoint_lineages(fit_meta, pf_metas, eval_meta=None)

        orgs = sorted({rec["meta"]["org_id"] for rec in predictor_fit_records})
        org_to_recs: dict[str, list[dict[str, Any]]] = {o: [] for o in orgs}
        for rec in predictor_fit_records:
            org_to_recs[rec["meta"]["org_id"]].append(rec)

        bias: dict[str, float] = {}
        for K in grid_ks:
            org_means = []
            for o in orgs:
                errs = []
                for rec in org_to_recs[o]:
                    raw_p = interpolate_from_probes(rec["feat"]["probes_r"], grid_ks)
                    errs.append(float(rec["true_r_by_k"][K]) - raw_p[K])
                org_means.append(float(np.mean(errs)))
            # Round to 8 decimal places for cross-platform canonical JSON determinism.
            bias[str(K)] = round(float(np.mean(org_means)), 8)

        all_pf_hashes = sorted({h for m in pf_metas for h in m["file_hashes"]})
        pf_hashes_digest = AG.sha256_bytes("\n".join(all_pf_hashes).encode("utf-8"))

        payload = {
            "schema": "gamma.bits-a1b.locked-predictor.v1",
            "primary_chain": AG.PRIMARY_CHAIN_NAME,
            "primary_chain_sha256": primary_chain_sha256,
            "chain_fit_lineage_id": fit_meta["lineage_id"],
            "chain_fit_org_id": fit_meta["org_id"],
            "predictor_fit_orgs": orgs,
            "predictor_fit_lineages": sorted(m["lineage_id"] for m in pf_metas),
            "predictor_fit_file_count": len(all_pf_hashes),
            "predictor_fit_file_hashes_sha256": pf_hashes_digest,
            "grid_ks": [int(k) for k in grid_ks],
            "probe_ks": [int(k) for k in probe_ks],
            "pilot_ks": [int(k) for k in pilot_ks],
            "sketch_config": {
                "frac": SKETCH_FRAC,
                "max_bytes": SKETCH_MAX_BYTES,
                "min_bytes": SKETCH_MIN_BYTES,
                "target_min_records": 12,
                "framing_eof_bytes_est": FRAMING_EOF_BYTES_EST,
            },
            "header_bytes_by_k": {str(int(k)): int(header_bytes_by_k[k]) for k in grid_ks},
            "cal_bias_by_k": bias,
        }
        elapsed = time.perf_counter() - t0
        return cls(payload), elapsed

    def to_canonical_bytes(self) -> bytes:
        return (json.dumps(self.payload, indent=2, sort_keys=True) + "\n").encode("utf-8")

    def sha256(self) -> str:
        return AG.sha256_bytes(self.to_canonical_bytes())

    def save(self, path: Path) -> str:
        raw = self.to_canonical_bytes()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return AG.sha256_bytes(raw)

    @classmethod
    def load(cls, path: Path, expected_sha256: str | None = None) -> "LockedHorizonPredictor":
        raw = path.read_bytes()
        digest = AG.sha256_bytes(raw)
        if expected_sha256 is not None and digest != expected_sha256:
            raise AssertionError(
                f"locked predictor SHA-256 mismatch: file={digest}, expected={expected_sha256}"
            )
        return cls(json.loads(raw.decode("utf-8")))

    def predict_k(self, feat: dict[str, Any], M: int) -> tuple[int, dict[int, float], float]:
        """Evaluate the exact locked predictor (zero refitting). Returns (k_pred, pred_r, sketch_margin)."""
        pred_r = interpolate_from_probes(
            feat["probes_r"], self.grid_ks, cal_bias=self.cal_bias_by_k
        )
        k_pred = select_prefix_from_curve(
            self.header_bytes_by_k, pred_r, M, grid_ks=self.grid_ks
        )
        margin = compute_sketch_uncertainty_margin(
            feat, self.header_bytes_by_k, pred_r, k_pred, M, self.grid_ks
        )
        return k_pred, pred_r, margin


def calibrate_locked_predictor_split_conformal(
    locked_predictor: LockedHorizonPredictor,
    fit_meta: dict[str, Any],
    predictor_fit_metas: list[dict[str, Any]],
    calibration_records: list[dict[str, Any]],
    alpha: float = UPB_ALPHA,
    sealed_regret_bar: float = SEALED_REGRET_BAR,
) -> dict[str, Any]:
    """Stage 2: exact split-conformal calibration of ONE locked predictor on untouched orgs.

    Nonconformity score per independent calibration organization i:
        s_i = max(full_oracle_regret_100KB(i), full_oracle_regret_100MB(i))
    computed strictly against the FULL multi-chain selector-by-K oracle.
    """
    t0 = time.perf_counter()
    cal_metas = [rec["meta"] for rec in calibration_records]
    assert_three_way_disjoint(fit_meta, predictor_fit_metas, cal_metas)

    M_SMALL, M_LARGE = 100_000, 100_000_000
    per_org_rows: list[dict[str, Any]] = []
    scores_full_max: list[float] = []
    scores_same_max: list[float] = []
    scores_chain_max: list[float] = []
    scores_full_100k: list[float] = []
    scores_full_100m: list[float] = []
    pilot_scores_full_max: list[float] = []

    for rec in calibration_records:
        meta = rec["meta"]
        feat = rec["feat"]
        rmap = rec["primary_rows_by_k"]
        all_cands = rec["all_chain_rows"]

        def _score_horizon(M: int) -> dict[str, Any]:
            k_pred, _, sk_margin = locked_predictor.predict_k(feat, M)
            chosen_row = rmap[k_pred]
            same_opt_row = AG.select_best_prefix_exact(list(rmap.values()), M)
            full_opt_row = AG.select_best_prefix_exact(all_cands, M)

            val_chosen = float(
                AG.horizon_objective_exact(
                    int(chosen_row["header_bytes"]),
                    int(chosen_row["body_bytes"]),
                    int(chosen_row["source_bytes"]),
                    M,
                )
            )
            val_same = float(
                AG.horizon_objective_exact(
                    int(same_opt_row["header_bytes"]),
                    int(same_opt_row["body_bytes"]),
                    int(same_opt_row["source_bytes"]),
                    M,
                )
            )
            val_full = float(
                AG.horizon_objective_exact(
                    int(full_opt_row["header_bytes"]),
                    int(full_opt_row["body_bytes"]),
                    int(full_opt_row["source_bytes"]),
                    M,
                )
            )

            full_reg = (val_chosen / val_full) - 1.0
            same_reg = (val_chosen / val_same) - 1.0
            chain_reg = (val_same / val_full) - 1.0

            # Also evaluate frozen 3-point geometric pilot fallback on this calibration org.
            r_pilot = {K: float(rmap[K]["r_hat"]) for K in locked_predictor.pilot_ks}
            k_pilot, _ = select_prefix_pilot_3pt(
                locked_predictor.header_bytes_by_k, r_pilot, M, locked_predictor.grid_ks
            )
            pilot_row = rmap[k_pilot]
            val_pilot = float(
                AG.horizon_objective_exact(
                    int(pilot_row["header_bytes"]),
                    int(pilot_row["body_bytes"]),
                    int(pilot_row["source_bytes"]),
                    M,
                )
            )
            pilot_full_reg = (val_pilot / val_full) - 1.0
            pilot_same_reg = (val_pilot / val_same) - 1.0

            return {
                "M": M,
                "chosen_K": int(k_pred),
                "same_chain_oracle_K": int(same_opt_row["K"]),
                "full_oracle_chain": str(full_opt_row["chain"]),
                "full_oracle_K": int(full_opt_row["K"]),
                "full_oracle_regret": full_reg,
                "same_chain_budget_regret": same_reg,
                "chain_choice_regret": chain_reg,
                "full_oracle_regret_pct": round(100.0 * full_reg, 4),
                "same_chain_budget_regret_pct": round(100.0 * same_reg, 4),
                "chain_choice_regret_pct": round(100.0 * chain_reg, 4),
                "sketch_margin_pct": round(100.0 * sk_margin, 4),
                "pilot_K": int(k_pilot),
                "pilot_full_oracle_regret": pilot_full_reg,
                "pilot_full_oracle_regret_pct": round(100.0 * pilot_full_reg, 4),
                "pilot_same_chain_regret_pct": round(100.0 * pilot_same_reg, 4),
            }

        h100k = _score_horizon(M_SMALL)
        h100m = _score_horizon(M_LARGE)

        s_i = max(h100k["full_oracle_regret"], h100m["full_oracle_regret"])
        s_i_same = max(h100k["same_chain_budget_regret"], h100m["same_chain_budget_regret"])
        s_i_chain = max(h100k["chain_choice_regret"], h100m["chain_choice_regret"])
        p_s_i = max(h100k["pilot_full_oracle_regret"], h100m["pilot_full_oracle_regret"])
        binding_horizon = (
            "100KB" if h100k["full_oracle_regret"] >= h100m["full_oracle_regret"] else "100MB"
        )

        scores_full_max.append(s_i)
        scores_same_max.append(s_i_same)
        scores_chain_max.append(s_i_chain)
        scores_full_100k.append(h100k["full_oracle_regret"])
        scores_full_100m.append(h100m["full_oracle_regret"])
        pilot_scores_full_max.append(p_s_i)

        per_org_rows.append(
            {
                "lineage_id": meta["lineage_id"],
                "org_id": meta["org_id"],
                "upstream_repo": meta["upstream_repo"],
                "package_name": meta["package_name"],
                "version": meta["version"],
                "domain": meta["domain"],
                "record_count": meta["record_count"],
                "source_bytes": meta["source_bytes"],
                "h_100KB": h100k,
                "h_100MB": h100m,
                "nonconformity_s_i_full_max": s_i,
                "nonconformity_s_i_full_max_pct": round(100.0 * s_i, 4),
                "binding_horizon": binding_horizon,
                "s_i_same_chain_budget_max_pct": round(100.0 * s_i_same, 4),
                "s_i_chain_choice_max_pct": round(100.0 * s_i_chain, 4),
                "breaches_2_0pct_bar": s_i > sealed_regret_bar,
                "pilot_s_i_full_max_pct": round(100.0 * p_s_i, 4),
            }
        )

    n_cal = len(scores_full_max)
    rank_k = math.ceil((1.0 - alpha) * (n_cal + 1))
    support_ok = rank_k <= n_cal
    coverage_floor = (rank_k / (n_cal + 1)) if support_ok else 0.0

    def _conformal_quantile(vals: list[float]) -> float | None:
        if not support_ok or not vals:
            return None
        return float(sorted(vals)[rank_k - 1])

    q90_full_max = _conformal_quantile(scores_full_max)
    q90_same_max = _conformal_quantile(scores_same_max)
    q90_chain_max = _conformal_quantile(scores_chain_max)
    q90_100k = _conformal_quantile(scores_full_100k)
    q90_100m = _conformal_quantile(scores_full_100m)
    q90_pilot_max = _conformal_quantile(pilot_scores_full_max)

    certifies_2_0 = (q90_full_max is not None) and (q90_full_max <= sealed_regret_bar)
    certifies_2_5 = (q90_full_max is not None) and (q90_full_max <= 0.025)
    certifies_same_2_0 = (q90_same_max is not None) and (q90_same_max <= sealed_regret_bar)
    breach_count_2_0 = sum(1 for x in scores_full_max if x > sealed_regret_bar)

    return {
        "schema": "gamma.bits-a1b.split-conformal-calibration.v1",
        "locked_predictor_sha256": locked_predictor.sha256(),
        "alpha": alpha,
        "target_coverage": round(1.0 - alpha, 4),
        "sealed_regret_bar": sealed_regret_bar,
        "sealed_regret_bar_pct": round(100.0 * sealed_regret_bar, 2),
        "nonconformity_definition": "s_i = max(full_oracle_regret_100KB(i), full_oracle_regret_100MB(i)) against full 7-chain selector-by-K oracle",
        "n_cal_orgs": n_cal,
        "conformal_rank_k": rank_k,
        "conformal_support_sufficient": support_ok,
        "finite_sample_coverage_guarantee_pct": round(100.0 * coverage_floor, 4),
        "sorted_nonconformity_s_i_pct": [round(100.0 * x, 4) for x in sorted(scores_full_max)],
        "conformal_90_upb_full_max": q90_full_max,
        "conformal_90_upb_full_max_pct": round(100.0 * q90_full_max, 4) if q90_full_max is not None else None,
        "conformal_90_upb_100KB_pct": round(100.0 * q90_100k, 4) if q90_100k is not None else None,
        "conformal_90_upb_100MB_pct": round(100.0 * q90_100m, 4) if q90_100m is not None else None,
        "conformal_90_upb_same_chain_budget_max_pct": round(100.0 * q90_same_max, 4) if q90_same_max is not None else None,
        "conformal_90_upb_chain_choice_max_pct": round(100.0 * q90_chain_max, 4) if q90_chain_max is not None else None,
        "conformal_90_upb_pilot_full_max_pct": round(100.0 * q90_pilot_max, 4) if q90_pilot_max is not None else None,
        "calibration_orgs_breaching_2_0pct_bar": breach_count_2_0,
        "certifies_2_0pct_sealed_bar": certifies_2_0,
        "certifies_2_5pct_legacy_bar": certifies_2_5,
        "certifies_same_chain_budget_2_0pct_bar": certifies_same_2_0,
        "strict_conformal_decision_at_2_0pct_bar": "DIRECT_PICK" if certifies_2_0 else "SWEEP_REQUIRED",
        "per_org_results": per_org_rows,
        "calibration_eval_wall_seconds": round(time.perf_counter() - t0, 6),
    }
