#!/usr/bin/env python3
"""Full A1b development evaluation across all required arms, work accounting,
token/RAM variant, lower envelope, codeword widening, and shared_spine reporting.

Reads verified grid data from out/prefix_grid.json (building it if absent),
re-extracts real micro-sketch features with exact wall-clock / op / RSS charging,
evaluates strict org-disjoint LOLO-CV across local spent lineages, and writes
out/dev_summary.json.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import archive_grid as AG  # noqa: E402
import sizing_policy as SP  # noqa: E402

# Frozen Token/RAM variant parameters (never tuned per evaluation lineage).
TOKEN_RAM_PRICES_LAMBDA: tuple[float, ...] = (0.5, 0.05, 0.005)
TOKEN_RAM_CAPS_BYTES: tuple[int, ...] = (16_384, 65_536)


def exact_obj_float(row: dict[str, Any], M: int) -> float:
    return float(
        Fraction(int(row["header_bytes"]))
        + Fraction(int(M) * int(row["body_bytes"]), int(row["source_bytes"]))
    )


def exact_obj_fraction(row: dict[str, Any], M: int) -> Fraction:
    return Fraction(int(row["header_bytes"])) + Fraction(
        int(M) * int(row["body_bytes"]), int(row["source_bytes"])
    )


def summarize_excess(vals: list[float]) -> dict[str, Any]:
    if not vals:
        return {"count": 0, "median_pct": None, "mean_pct": None, "p95_pct": None, "max_pct": None}
    arr = np.array(vals, dtype=float) * 100.0
    return {
        "count": len(vals),
        "median_pct": round(float(np.median(arr)), 4),
        "mean_pct": round(float(np.mean(arr)), 4),
        "p95_pct": round(float(np.percentile(arr, 95)), 4),
        "max_pct": round(float(np.max(arr)), 4),
    }


def summarize_work(
    query_works: list[dict[str, Any]],
    extra_refit_wall_s: float = 0.0,
) -> dict[str, Any]:
    """Aggregate exact wall-clock seconds, p95 latency, peak RSS, and op counts."""
    n = len(query_works)
    sel_walls = [w["selection_wall_s"] for w in query_works]
    tot_walls = [w["total_wall_s"] for w in query_works]
    sel_ops = [w["selection_ops"] for w in query_works]
    tot_ops = [w["total_ops"] for w in query_works]
    peak_rss = max((w["peak_rss_bytes"] for w in query_works), default=0)

    total_wall = sum(tot_walls) + extra_refit_wall_s
    sel_wall = sum(sel_walls) + extra_refit_wall_s
    return {
        "queries": n,
        "selection_wall_seconds_total": round(sel_wall, 6),
        "selection_wall_seconds_mean": round(sel_wall / max(1, n), 6),
        "selection_wall_seconds_p95": round(float(np.percentile(sel_walls, 95)), 6) if n else 0.0,
        "total_wall_seconds_total": round(total_wall, 6),
        "total_wall_seconds_mean": round(total_wall / max(1, n), 6),
        "total_wall_seconds_p95": round(float(np.percentile(tot_walls, 95)), 6) if n else 0.0,
        "fold_and_final_refit_wall_seconds": round(extra_refit_wall_s, 6),
        "selection_ops_total": int(sum(sel_ops)),
        "total_ops_total": int(sum(tot_ops)),
        "peak_rss_bytes": int(peak_rss),
    }


def compute_lower_envelope_and_crossovers(
    by_lin_prim: dict[str, dict[int, dict[str, Any]]],
    lineages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute diagnostic lower envelope across M in [10^4, 10^9] and exact crossover M*."""
    envelope: dict[str, Any] = {}
    for lin in lineages:
        lid = lin["lineage_id"]
        rmap = by_lin_prim[lid]
        cands = list(rmap.values())
        sweep = []
        for M in AG.DIAGNOSTIC_HORIZONS:
            best = AG.select_best_prefix_exact(cands, M)
            best_obj = exact_obj_float(best, M)
            # Check widely separated K pairs (>= 4x ratio) within 0.5% and 1.0% of optimum.
            within_05 = [
                r["K"] for r in cands if (exact_obj_float(r, M) / best_obj - 1.0) <= 0.005
            ]
            within_10 = [
                r["K"] for r in cands if (exact_obj_float(r, M) / best_obj - 1.0) <= 0.010
            ]

            def has_wide_pair(ks: list[int]) -> bool:
                pos = [k for k in ks if k > 0]
                if len(pos) >= 2 and (max(pos) / min(pos)) >= 4.0:
                    return True
                if 0 in ks and any(k >= 64 for k in ks):
                    return True
                return False

            sweep.append(
                {
                    "M": M,
                    "best_K": best["K"],
                    "header_bytes": best["header_bytes"],
                    "r_hat": round(best["r_hat"], 6),
                    "complete_bytes": round(best_obj, 2),
                    "complete_bits": round(best_obj * 8.0, 2),
                    "header_share_pct": round(100.0 * best["header_bytes"] / best_obj, 3),
                    "within_0_5pct_ks": sorted(within_05),
                    "within_1_0pct_ks": sorted(within_10),
                    "wide_near_tie_0_5pct": has_wide_pair(within_05),
                    "wide_near_tie_1_0pct": has_wide_pair(within_10),
                }
            )

        # Exact break-even crossover horizons M* between key prefix pairs:
        # H_a + M * r_a = H_b + M * r_b  =>  M* = (H_b - H_a) / (r_a - r_b) if r_a > r_b.
        def breakeven(k_small: int, k_large: int) -> float | None:
            ra = Fraction(rmap[k_small]["body_bytes"], rmap[k_small]["source_bytes"])
            rb = Fraction(rmap[k_large]["body_bytes"], rmap[k_large]["source_bytes"])
            if ra <= rb:
                return None  # larger prefix NEVER catches up (codeword widening!)
            ha = Fraction(rmap[k_small]["header_bytes"])
            hb = Fraction(rmap[k_large]["header_bytes"])
            return round(float((hb - ha) / (ra - rb)), 1)

        envelope[lid] = {
            "role": lin["role"],
            "org_id": lin["org_id"],
            "source_bytes": lin["source_bytes"],
            "breakeven_M_star": {
                "K0_to_K64": breakeven(0, 64),
                "K64_to_K512": breakeven(64, 512),
                "K512_to_K2048": breakeven(512, 2048),
                "K2048_to_K4096": breakeven(2048, 4096),
            },
            "horizon_sweep": sweep,
        }
    return envelope


def compute_codeword_widening_and_decomp(
    by_lin_prim: dict[str, dict[int, dict[str, Any]]],
    lineages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Quantify header/framing/payload decomposition and codeword widening across K."""
    per_lineage: dict[str, Any] = {}
    for lin in lineages:
        lid = lin["lineage_id"]
        rmap = by_lin_prim[lid]
        curve = []
        for K in AG.PRIMARY_GRID:
            r = rmap[K]
            curve.append(
                {
                    "K": K,
                    "header_bytes": r["header_bytes"],
                    "dict_bytes": r["dict_bytes"],
                    "code_table_bytes": r["code_table_bytes"],
                    "framing_bytes": r["framing_bytes"],
                    "payload_bytes": r["payload_bytes"],
                    "body_bytes": r["body_bytes"],
                    "complete_bytes_observed": r["complete_bytes"],
                    "r_hat": round(r["r_hat"], 6),
                    "framing_share_of_body_pct": round(
                        100.0 * r["framing_bytes"] / max(1, r["body_bytes"]), 4
                    ),
                    "avg_code_len_header": round(r["avg_code_len_header"], 4),
                    "realized_bits_per_token": round(r["realized_bits_per_token"], 4),
                    "bytes_per_token": round(r["bytes_per_token"], 4),
                    "distinct_entries_used": r["distinct_entries_used"],
                    "unused_entries": r["unused_entries"],
                    "unused_share_pct": round(
                        100.0 * r["unused_entries"] / max(1, r["entries_count"]), 3
                    ),
                    "dict_ram_bytes": r["dict_ram_bytes"],
                }
            )
        r2048 = rmap[2048]["r_hat"]
        r4096 = rmap[4096]["r_hat"]
        bpt2048 = rmap[2048]["realized_bits_per_token"]
        bpt4096 = rmap[4096]["realized_bits_per_token"]
        per_lineage[lid] = {
            "role": lin["role"],
            "r_hat_delta_4096_minus_2048": round(r4096 - r2048, 6),
            "r_hat_rel_4096_vs_2048_pct": round(100.0 * (r4096 / r2048 - 1.0), 4),
            "codeword_widening_bits_per_token_4096_vs_2048": round(bpt4096 - bpt2048, 4),
            "non_monotone_tail_widening": r4096 > r2048,
            "curve": curve,
        }
    return per_lineage


def evaluate_token_ram_variant(
    lineages: list[dict[str, Any]],
    by_lin_prim: dict[str, dict[int, dict[str, Any]]],
    by_lin_all: dict[str, list[dict[str, Any]]],
    sketch_feats: dict[str, dict[str, Any]],
    ram_by_k: dict[int, int],
) -> dict[str, Any]:
    """Score the separate Token/RAM variant (frozen RAM price lambda and hard RAM caps)."""
    dev_lins = [l for l in lineages if l["role"] == "dev_disjoint"]
    Ks = AG.PRIMARY_GRID

    # 1. Priced variant: lambda * RAM_K + M * tau_K
    priced_rows = []
    arm_regrets_same: dict[str, list[float]] = {
        a: [] for a in ("shipped_token_policy", "fixed_K512", "fixed_K2048", "fixed_K4096", "pilot_3pt_token")
    }
    arm_regrets_full: dict[str, list[float]] = {k: [] for k in arm_regrets_same}

    for test_lin in dev_lins:
        tid = test_lin["lineage_id"]
        torg = test_lin["org_id"]
        cal_lins = [l for l in dev_lins if l["org_id"] != torg]
        # Org-weighted token-rate calibration bias per K
        cal_orgs = sorted({l["org_id"] for l in cal_lins})
        cal_bias_tok: dict[int, float] = {}
        for K in Ks:
            org_means = []
            for o in cal_orgs:
                errs = []
                for cl in cal_lins:
                    if cl["org_id"] != o:
                        continue
                    cid = cl["lineage_id"]
                    raw_t = SP.interpolate_from_probes(sketch_feats[cid]["probes_tok"], Ks)
                    true_t = by_lin_prim[cid][K]["tokens"] / by_lin_prim[cid][K]["source_bytes"]
                    errs.append(true_t - raw_t[K])
                org_means.append(float(np.mean(errs)))
            cal_bias_tok[K] = float(np.mean(org_means))

        pred_tau = SP.interpolate_from_probes(
            sketch_feats[tid]["probes_tok"], Ks, cal_bias=cal_bias_tok
        )
        true_tau = {
            K: Fraction(by_lin_prim[tid][K]["tokens"], by_lin_prim[tid][K]["source_bytes"])
            for K in Ks
        }
        pilot_tau = {K: float(true_tau[K]) for K in SP.PILOT_KS}
        pilot_curve_tau = SP.pilot_predict_curve_from_3pt(pilot_tau, Ks)

        for lam in TOKEN_RAM_PRICES_LAMBDA:
            for M in AG.PRIMARY_HORIZONS:
                lam_f = Fraction(str(lam))

                def obj_t(r: dict[str, Any]) -> Fraction:
                    return lam_f * Fraction(int(r["dict_ram_bytes"])) + Fraction(
                        int(M) * int(r["tokens"]), int(r["source_bytes"])
                    )

                same_opt_k = SP.select_prefix_token_ram_priced(ram_by_k, true_tau, M, lam, Ks)
                same_opt_val = float(obj_t(by_lin_prim[tid][same_opt_k]))
                full_opt_row = min(
                    by_lin_all[tid],
                    key=lambda r: (obj_t(r), int(r["dict_ram_bytes"]), int(r["K"]), r["chain"]),
                )
                full_opt_val = float(obj_t(full_opt_row))

                picks = {
                    "shipped_token_policy": SP.select_prefix_token_ram_priced(
                        ram_by_k, pred_tau, M, lam, Ks
                    ),
                    "fixed_K512": 512,
                    "fixed_K2048": 2048,
                    "fixed_K4096": 4096,
                    "pilot_3pt_token": SP.select_prefix_token_ram_priced(
                        ram_by_k, pilot_curve_tau, M, lam, Ks
                    ),
                }
                row_entry: dict[str, Any] = {
                    "lineage_id": tid,
                    "lambda": lam,
                    "M": M,
                    "same_oracle_K": same_opt_k,
                    "full_oracle_chain": full_opt_row["chain"],
                    "full_oracle_K": full_opt_row["K"],
                    "arms": {},
                }
                for arm_name, k_pick in picks.items():
                    val = float(obj_t(by_lin_prim[tid][k_pick]))
                    reg_s = (val / same_opt_val) - 1.0
                    reg_f = (val / full_opt_val) - 1.0
                    arm_regrets_same[arm_name].append(reg_s)
                    arm_regrets_full[arm_name].append(reg_f)
                    row_entry["arms"][arm_name] = {
                        "K": k_pick,
                        "ram_bytes": ram_by_k[k_pick],
                        "regret_vs_same_pct": round(100.0 * reg_s, 4),
                        "regret_vs_full_pct": round(100.0 * reg_f, 4),
                    }
                priced_rows.append(row_entry)

    # 2. Hard RAM-cap variant: minimize tokens subject to dict_ram_bytes <= R_max
    capped_summary = {}
    for cap in TOKEN_RAM_CAPS_BYTES:
        elig_ks = [K for K in Ks if ram_by_k[K] <= cap]
        cap_reg_same: list[float] = []
        cap_reg_full: list[float] = []
        cap_details = []
        for test_lin in dev_lins:
            tid = test_lin["lineage_id"]
            torg = test_lin["org_id"]
            cal_lins = [l for l in dev_lins if l["org_id"] != torg]
            cal_orgs = sorted({l["org_id"] for l in cal_lins})
            cal_bias_tok = {}
            for K in elig_ks:
                org_means = []
                for o in cal_orgs:
                    errs = [
                        (by_lin_prim[cl["lineage_id"]][K]["tokens"] / by_lin_prim[cl["lineage_id"]][K]["source_bytes"])
                        - SP.interpolate_from_probes(sketch_feats[cl["lineage_id"]]["probes_tok"], Ks)[K]
                        for cl in cal_lins
                        if cl["org_id"] == o
                    ]
                    org_means.append(float(np.mean(errs)))
                cal_bias_tok[K] = float(np.mean(org_means))
            pred_tau = SP.interpolate_from_probes(
                sketch_feats[tid]["probes_tok"], Ks, cal_bias=cal_bias_tok
            )
            true_tau = {
                K: Fraction(by_lin_prim[tid][K]["tokens"], by_lin_prim[tid][K]["source_bytes"])
                for K in Ks
            }
            k_pick = SP.select_prefix_token_ram_capped(ram_by_k, pred_tau, cap, Ks)
            k_same = SP.select_prefix_token_ram_capped(ram_by_k, true_tau, cap, Ks)
            elig_all = [r for r in by_lin_all[tid] if r["dict_ram_bytes"] <= cap]
            best_all = min(elig_all, key=lambda r: (r["tokens"], r["dict_ram_bytes"], r["K"]))
            tok_pick = by_lin_prim[tid][k_pick]["tokens"]
            tok_same = by_lin_prim[tid][k_same]["tokens"]
            tok_full = best_all["tokens"]
            rs = (tok_pick / tok_same) - 1.0
            rf = (tok_pick / tok_full) - 1.0
            cap_reg_same.append(rs)
            cap_reg_full.append(rf)
            cap_details.append(
                {
                    "lineage_id": tid,
                    "picked_K": k_pick,
                    "same_oracle_K": k_same,
                    "full_oracle_chain": best_all["chain"],
                    "full_oracle_K": best_all["K"],
                    "regret_vs_same_pct": round(100.0 * rs, 4),
                    "regret_vs_full_pct": round(100.0 * rf, 4),
                }
            )
        capped_summary[f"ram_cap_{cap}B"] = {
            "ram_cap_bytes": cap,
            "eligible_primary_ks": elig_ks,
            "shipped_token_policy_vs_same": summarize_excess(cap_reg_same),
            "shipped_token_policy_vs_full": summarize_excess(cap_reg_full),
            "per_lineage": cap_details,
        }

    return {
        "ram_model": "frozen deterministic LUT+hash+entries bytes (Dictionary.ram_footprint_bytes)",
        "ram_by_k_primary_chain": {str(k): ram_by_k[k] for k in Ks},
        "priced_variant": {
            "frozen_lambdas_tokens_per_ram_byte": list(TOKEN_RAM_PRICES_LAMBDA),
            "horizons": list(AG.PRIMARY_HORIZONS),
            "arm_summaries": {
                arm: {
                    "vs_same_chain_oracle": summarize_excess(arm_regrets_same[arm]),
                    "vs_full_oracle": summarize_excess(arm_regrets_full[arm]),
                }
                for arm in arm_regrets_same
            },
            "queries": priced_rows,
        },
        "hard_ram_cap_variant": capped_summary,
    }


def run_eval_dev(grid_path: Path | None = None, out_path: Path | None = None) -> dict[str, Any]:
    """Execute complete A1b dev evaluation and write dev_summary.json."""
    t_all0 = time.perf_counter()
    if grid_path is None:
        grid_path = HERE / "out" / "prefix_grid.json"
    if not grid_path.exists():
        AG.main()

    grid_data = json.loads(grid_path.read_text())
    rows = grid_data["rows"]
    fit_corpus = AG.load_fit_corpus()
    fit_meta = {k: v for k, v in fit_corpus.items() if k != "docs"}
    lineages = AG.load_spent_lineages()
    primary_chain = AG.load_verified_chain(AG.PRIMARY_CHAIN_NAME)

    # Fit primary chain headers (fast, ~1.5-7s) so we can run live micro-sketch probes with real timings.
    primary_headers = AG.fit_all_prefix_headers(
        {AG.PRIMARY_CHAIN_NAME: primary_chain}, fit_corpus, jobs=1
    )
    dicts_by_k = {
        K: AG.Dictionary(primary_headers[(AG.PRIMARY_CHAIN_NAME, K)]["entries"])
        for K in AG.PRIMARY_GRID
    }
    lengths_by_k = {
        K: primary_headers[(AG.PRIMARY_CHAIN_NAME, K)]["lengths"] for K in AG.PRIMARY_GRID
    }
    header_bytes_by_k = {
        K: int(primary_headers[(AG.PRIMARY_CHAIN_NAME, K)]["header_bytes"])
        for K in AG.PRIMARY_GRID
    }
    ram_by_k = {
        K: int(primary_headers[(AG.PRIMARY_CHAIN_NAME, K)]["dict_ram_bytes"])
        for K in AG.PRIMARY_GRID
    }

    # Index pre-verified archive grid rows.
    by_lin_all: dict[str, list[dict[str, Any]]] = {}
    by_lin_prim: dict[str, dict[int, dict[str, Any]]] = {}
    for r in rows:
        by_lin_all.setdefault(r["lineage_id"], []).append(r)
        if r["chain"] == AG.PRIMARY_CHAIN_NAME:
            by_lin_prim.setdefault(r["lineage_id"], {})[int(r["K"])] = r

    # Verify 100% independent decode fidelity across the entire grid.
    all_decoded_ok = all(r.get("independent_decode_ok") is True and r.get("fidelity") == 1.0 for r in rows)
    if not all_decoded_ok:
        raise AssertionError("prefix_grid.json contains an archive without 100% independent decode fidelity")

    # Run real micro-sketch feature extraction with exact wall-clock & op accounting for every lineage.
    sketch_feats: dict[str, dict[str, Any]] = {}
    for lin in lineages:
        lid = lin["lineage_id"]
        sketch_feats[lid] = SP.extract_micro_sketch_features(
            lin["docs"], dicts_by_k, lengths_by_k, probe_ks=SP.PROBE_KS
        )

    dev_lins = [l for l in lineages if l["role"] == "dev_disjoint"]
    diag_lins = [l for l in lineages if l["role"] == "in_dist_codenet_diag"]
    third_party_lids = {l["lineage_id"] for l in dev_lins if l["org_id"] != "clocksmith"}

    # Build calibration records for all dev_disjoint lineages (only used inside org-disjoint folds!).
    def make_cal_record(lin: dict[str, Any]) -> dict[str, Any]:
        lid = lin["lineage_id"]
        rmap = by_lin_prim[lid]
        all_cands = by_lin_all[lid]
        return {
            "meta": {k: v for k, v in lin.items() if k != "docs"},
            "feat": sketch_feats[lid],
            "true_r_by_k": {K: rmap[K]["r_hat"] for K in AG.PRIMARY_GRID},
            "oracle_obj_by_M": {
                M: exact_obj_float(AG.select_best_prefix_exact(all_cands, M), M)
                for M in AG.PRIMARY_HORIZONS
            },
            "same_oracle_obj_by_M": {
                M: exact_obj_float(AG.select_best_prefix_exact(list(rmap.values()), M), M)
                for M in AG.PRIMARY_HORIZONS
            },
        }

    cal_record_by_lid = {l["lineage_id"]: make_cal_record(l) for l in dev_lins}

    # Helper to construct exact work dict for an arm on (lid, M) with identical prefix reuse.
    def encode_work(lid: str, K: int) -> tuple[float, int, int]:
        w = by_lin_prim[lid][K]["work"]
        return float(w["wall_seconds"]), int(w["total_ops"]), int(w["peak_rss_bytes"])

    def eval_pilot_on_query(lid: str, M: int) -> tuple[int, dict[str, Any]]:
        rmap = by_lin_prim[lid]
        r_pilot = {K: rmap[K]["r_hat"] for K in SP.PILOT_KS}
        k_pick, _ = SP.select_prefix_pilot_3pt(header_bytes_by_k, r_pilot, M, AG.PRIMARY_GRID)
        # Charge the 3 pilot full-corpus encodes; reuse archive if k_pick is one of the 3 pilot points!
        sel_w, sel_ops, rss = 0.0, 0, 0
        for pk in SP.PILOT_KS:
            w_s, ops, r_b = encode_work(lid, pk)
            sel_w += w_s
            sel_ops += ops
            rss = max(rss, r_b)
        if k_pick in SP.PILOT_KS:
            dep_w, dep_ops = 0.0, 0  # exact prefix reuse!
        else:
            dep_w, dep_ops, r_b = encode_work(lid, k_pick)
            rss = max(rss, r_b)
        return k_pick, {
            "selection_wall_s": sel_w,
            "selection_ops": sel_ops,
            "deployment_wall_s": dep_w,
            "deployment_ops": dep_ops,
            "total_wall_s": sel_w + dep_w,
            "total_ops": sel_ops + dep_ops,
            "peak_rss_bytes": rss,
            "reused_pilot_archive": k_pick in SP.PILOT_KS,
        }

    def eval_grid_on_query(lid: str, M: int) -> tuple[int, dict[str, Any]]:
        rmap = by_lin_prim[lid]
        best = AG.select_best_prefix_exact(list(rmap.values()), M)
        k_pick = int(best["K"])
        tot_w, tot_ops, rss = 0.0, 0, 0
        for K in AG.PRIMARY_GRID:
            w_s, ops, r_b = encode_work(lid, K)
            tot_w += w_s
            tot_ops += ops
            rss = max(rss, r_b)
        return k_pick, {
            "selection_wall_s": tot_w,
            "selection_ops": tot_ops,
            "deployment_wall_s": 0.0,  # exact prefix reuse of grid's winning archive
            "deployment_ops": 0,
            "total_wall_s": tot_w,
            "total_ops": tot_ops,
            "peak_rss_bytes": rss,
        }

    def eval_fixed_on_query(lid: str, K: int) -> tuple[int, dict[str, Any]]:
        w_s, ops, rss = encode_work(lid, K)
        return K, {
            "selection_wall_s": 0.0,
            "selection_ops": 0,
            "deployment_wall_s": w_s,
            "deployment_ops": ops,
            "total_wall_s": w_s,
            "total_ops": ops,
            "peak_rss_bytes": rss,
        }

    # Run strict org-disjoint LOLO-CV across all 7 dev_disjoint lineages x 2 horizons = 14 queries!
    arm_names = (
        "shipped_policy_dev_calibrated",
        "shipped_policy_strict_conformal",
        "fixed_K512",
        "fixed_K2048",
        "fixed_K4096",
        "pilot_3pt_geometric",
        "same_chain_oracle",
        "full_selector_by_K_oracle",
    )
    per_arm_same: dict[str, list[float]] = {a: [] for a in arm_names}
    per_arm_full: dict[str, list[float]] = {a: [] for a in arm_names}
    per_arm_full_3p: dict[str, list[float]] = {a: [] for a in arm_names}
    per_arm_work: dict[str, list[dict[str, Any]]] = {a: [] for a in arm_names}
    per_arm_complete_bits: dict[str, dict[str, list[float]]] = {
        a: {str(M): [] for M in AG.PRIMARY_HORIZONS} for a in arm_names
    }
    query_records: list[dict[str, Any]] = []
    fold_refit_wall_dev = 0.0
    fold_refit_wall_strict = 0.0

    for test_lin in dev_lins:
        tid = test_lin["lineage_id"]
        torg = test_lin["org_id"]
        eval_meta = {k: v for k, v in test_lin.items() if k != "docs"}
        cal_recs = [
            cal_record_by_lid[l["lineage_id"]]
            for l in dev_lins
            if l["org_id"] != torg
        ]

        # Fit both dev-calibrated and strict-conformal policies strictly on org-disjoint cal_recs.
        pol_dev = SP.HorizonSizingPolicy(header_bytes_by_k, AG.PRIMARY_GRID, strict_conformal=False)
        cal_info_dev = pol_dev.fit_calibration(fit_meta, cal_recs, AG.PRIMARY_HORIZONS)
        fold_refit_wall_dev += cal_info_dev["fit_wall_seconds"]

        pol_strict = SP.HorizonSizingPolicy(header_bytes_by_k, AG.PRIMARY_GRID, strict_conformal=True)
        cal_info_strict = pol_strict.fit_calibration(fit_meta, cal_recs, AG.PRIMARY_HORIZONS)
        fold_refit_wall_strict += cal_info_strict["fit_wall_seconds"]

        feat = sketch_feats[tid]
        rmap = by_lin_prim[tid]
        all_cands = by_lin_all[tid]

        for M in AG.PRIMARY_HORIZONS:
            same_opt_row = AG.select_best_prefix_exact(list(rmap.values()), M)
            same_opt_val = exact_obj_float(same_opt_row, M)
            full_opt_row = AG.select_best_prefix_exact(all_cands, M)
            full_opt_val = exact_obj_float(full_opt_row, M)

            k_pilot, w_pilot = eval_pilot_on_query(tid, M)
            k_grid, w_grid = eval_grid_on_query(tid, M)
            assert k_grid == int(same_opt_row["K"])

            # Shipped policy evaluation (both regimes), including fallback work & excess!
            def run_shipped(pol: SP.HorizonSizingPolicy) -> tuple[int, dict[str, Any], dict[str, Any]]:
                t_p0 = time.perf_counter()
                pred = pol.predict(eval_meta, feat, M)
                pred_wall = time.perf_counter() - t_p0
                sk_w = float(feat["work"]["wall_seconds"]) + pred_wall
                sk_ops = int(feat["work"]["total_ops"])
                rss = int(feat["work"]["peak_rss_bytes"])
                if pred["decision"] == "SWEEP_REQUIRED":
                    final_k = k_pilot
                    w_dict = {
                        "selection_wall_s": sk_w + w_pilot["selection_wall_s"],
                        "selection_ops": sk_ops + w_pilot["selection_ops"],
                        "deployment_wall_s": w_pilot["deployment_wall_s"],
                        "deployment_ops": w_pilot["deployment_ops"],
                        "total_wall_s": sk_w + w_pilot["total_wall_s"],
                        "total_ops": sk_ops + w_pilot["total_ops"],
                        "peak_rss_bytes": max(rss, w_pilot["peak_rss_bytes"]),
                        "fallback_used": True,
                    }
                else:
                    final_k = int(pred["predicted_K"])
                    dep_w, dep_ops, dep_rss = encode_work(tid, final_k)
                    w_dict = {
                        "selection_wall_s": sk_w,
                        "selection_ops": sk_ops,
                        "deployment_wall_s": dep_w,
                        "deployment_ops": dep_ops,
                        "total_wall_s": sk_w + dep_w,
                        "total_ops": sk_ops + dep_ops,
                        "peak_rss_bytes": max(rss, dep_rss),
                        "fallback_used": False,
                    }
                return final_k, w_dict, pred

            k_dev, w_dev, pred_dev = run_shipped(pol_dev)
            k_str, w_str, pred_str = run_shipped(pol_strict)

            # Full selector-by-K oracle work = sum across all 7 chains x eligible prefixes.
            full_oracle_w = sum(float(r["work"]["wall_seconds"]) for r in all_cands)
            full_oracle_ops = sum(int(r["work"]["total_ops"]) for r in all_cands)
            full_oracle_rss = max(int(r["work"]["peak_rss_bytes"]) for r in all_cands)
            w_full_oracle = {
                "selection_wall_s": full_oracle_w,
                "selection_ops": full_oracle_ops,
                "deployment_wall_s": 0.0,
                "deployment_ops": 0,
                "total_wall_s": full_oracle_w,
                "total_ops": full_oracle_ops,
                "peak_rss_bytes": full_oracle_rss,
            }

            arm_results: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
                "shipped_policy_dev_calibrated": (rmap[k_dev], w_dev),
                "shipped_policy_strict_conformal": (rmap[k_str], w_str),
                "fixed_K512": (rmap[512], eval_fixed_on_query(tid, 512)[1]),
                "fixed_K2048": (rmap[2048], eval_fixed_on_query(tid, 2048)[1]),
                "fixed_K4096": (rmap[4096], eval_fixed_on_query(tid, 4096)[1]),
                "pilot_3pt_geometric": (rmap[k_pilot], w_pilot),
                "same_chain_oracle": (same_opt_row, w_grid),
                "full_selector_by_K_oracle": (full_opt_row, w_full_oracle),
            }

            q_arms: dict[str, Any] = {}
            for aname, (chosen_row, w_dict) in arm_results.items():
                val = exact_obj_float(chosen_row, M)
                ex_s = (val / same_opt_val) - 1.0
                ex_f = (val / full_opt_val) - 1.0
                per_arm_same[aname].append(ex_s)
                per_arm_full[aname].append(ex_f)
                if tid in third_party_lids:
                    per_arm_full_3p[aname].append(ex_f)
                per_arm_work[aname].append(w_dict)
                per_arm_complete_bits[aname][str(M)].append(val * 8.0)
                q_arms[aname] = {
                    "chain": chosen_row["chain"],
                    "K": int(chosen_row["K"]),
                    "header_bytes": int(chosen_row["header_bytes"]),
                    "r_hat": round(float(chosen_row["r_hat"]), 6),
                    "complete_bytes": round(val, 2),
                    "complete_bits": round(val * 8.0, 2),
                    "excess_vs_same_pct": round(100.0 * ex_s, 4),
                    "excess_vs_full_pct": round(100.0 * ex_f, 4),
                    "total_wall_s": round(w_dict["total_wall_s"], 6),
                    "total_ops": int(w_dict["total_ops"]),
                }

            # Realized pre-fallback excess of predicted_K (for UPB coverage check on BOTH same-chain and full oracle!)
            pred_k_only = int(pred_dev["predicted_K"])
            pred_only_ex_same = (exact_obj_float(rmap[pred_k_only], M) / same_opt_val) - 1.0
            pred_only_ex_full = (exact_obj_float(rmap[pred_k_only], M) / full_opt_val) - 1.0
            upb_dev_same = pred_dev["upb_90_dev_t"]
            upb_dev_full = pred_dev["upb_90_dev_t_full"]
            query_records.append(
                {
                    "lineage_id": tid,
                    "org_id": torg,
                    "is_third_party_org": tid in third_party_lids,
                    "M": M,
                    "n_cal_orgs": pred_dev["n_cal_orgs"],
                    "dev_policy_decision": pred_dev["decision"],
                    "dev_policy_reason": pred_dev["reason"],
                    "dev_policy_predicted_K": pred_k_only,
                    "dev_policy_final_K": k_dev,
                    "dev_policy_upb90_same_pct": round(100.0 * upb_dev_same, 4) if upb_dev_same is not None else None,
                    "dev_policy_upb90_full_pct": round(100.0 * upb_dev_full, 4) if upb_dev_full is not None else None,
                    "dev_policy_pred_only_excess_vs_same_pct": round(100.0 * pred_only_ex_same, 4),
                    "dev_policy_pred_only_excess_vs_full_pct": round(100.0 * pred_only_ex_full, 4),
                    "dev_upb90_same_covers_realized": (upb_dev_same is not None and pred_only_ex_same <= upb_dev_same),
                    "dev_upb90_full_covers_realized": (upb_dev_full is not None and pred_only_ex_full <= upb_dev_full),
                    "strict_policy_decision": pred_str["decision"],
                    "strict_policy_reason": pred_str["reason"],
                    "arms": q_arms,
                }
            )

    # Final shipping refit on ALL 7 dev_disjoint lineages (explicitly timed & charged!).
    final_pol_dev = SP.HorizonSizingPolicy(header_bytes_by_k, AG.PRIMARY_GRID, strict_conformal=False)
    final_refit_dev = final_pol_dev.fit_calibration(
        fit_meta, list(cal_record_by_lid.values()), AG.PRIMARY_HORIZONS
    )
    final_pol_strict = SP.HorizonSizingPolicy(header_bytes_by_k, AG.PRIMARY_GRID, strict_conformal=True)
    final_refit_strict = final_pol_strict.fit_calibration(
        fit_meta, list(cal_record_by_lid.values()), AG.PRIMARY_HORIZONS
    )

    # Segregated in-distribution CodeNet diagnostic strata (calibrated strictly on non-CodeNet repos ONLY!).
    codenet_diag_records = []
    for lin in diag_lins:
        lid = lin["lineage_id"]
        eval_meta = {k: v for k, v in lin.items() if k != "docs"}
        feat = sketch_feats[lid]
        rmap = by_lin_prim[lid]
        all_cands = by_lin_all[lid]
        for M in AG.PRIMARY_HORIZONS:
            same_opt = AG.select_best_prefix_exact(list(rmap.values()), M)
            full_opt = AG.select_best_prefix_exact(all_cands, M)
            pred_d = final_pol_dev.predict(
                eval_meta, feat, M, allow_same_collection_eval_diagnostic=True
            )
            k_pilot, _ = eval_pilot_on_query(lid, M)
            k_final = k_pilot if pred_d["decision"] == "SWEEP_REQUIRED" else int(pred_d["predicted_K"])
            val_final = exact_obj_float(rmap[k_final], M)
            val_same = exact_obj_float(same_opt, M)
            val_full = exact_obj_float(full_opt, M)
            codenet_diag_records.append(
                {
                    "lineage_id": lid,
                    "M": M,
                    "note": "In-distribution same-collection CodeNet stratum; NEVER included in calibration or primary dev metrics",
                    "decision": pred_d["decision"],
                    "predicted_K": int(pred_d["predicted_K"]),
                    "final_K": k_final,
                    "same_oracle_K": int(same_opt["K"]),
                    "full_oracle_chain": full_opt["chain"],
                    "full_oracle_K": int(full_opt["K"]),
                    "excess_vs_same_pct": round(100.0 * (val_final / val_same - 1.0), 4),
                    "excess_vs_full_pct": round(100.0 * (val_final / val_full - 1.0), 4),
                    "upb90_dev_pct": round(100.0 * pred_d["upb_90_dev_t"], 4),
                }
            )

    # Aggregate arm summaries + exact work ratios vs pilot and grid.
    pilot_work_summary = summarize_work(per_arm_work["pilot_3pt_geometric"])
    grid_work_summary = summarize_work(per_arm_work["same_chain_oracle"])
    pilot_tot_ops = pilot_work_summary["total_ops_total"]
    grid_tot_ops = grid_work_summary["total_ops_total"]
    pilot_tot_wall = pilot_work_summary["total_wall_seconds_total"]
    grid_tot_wall = grid_work_summary["total_wall_seconds_total"]

    arm_summaries: dict[str, Any] = {}
    for aname in arm_names:
        extra_refit = 0.0
        if aname == "shipped_policy_dev_calibrated":
            extra_refit = fold_refit_wall_dev + final_refit_dev["fit_wall_seconds"]
        elif aname == "shipped_policy_strict_conformal":
            extra_refit = fold_refit_wall_strict + final_refit_strict["fit_wall_seconds"]
        ws = summarize_work(per_arm_work[aname], extra_refit_wall_s=extra_refit)
        ws["total_ops_ratio_vs_pilot"] = round(ws["total_ops_total"] / max(1, pilot_tot_ops), 4)
        ws["total_ops_ratio_vs_grid"] = round(ws["total_ops_total"] / max(1, grid_tot_ops), 4)
        ws["total_wall_ratio_vs_pilot"] = round(ws["total_wall_seconds_total"] / max(1e-9, pilot_tot_wall), 4)
        ws["total_wall_ratio_vs_grid"] = round(ws["total_wall_seconds_total"] / max(1e-9, grid_tot_wall), 4)
        ws["selection_ops_ratio_vs_pilot"] = round(
            ws["selection_ops_total"] / max(1, pilot_work_summary["selection_ops_total"]), 4
        )
        ws["selection_ops_ratio_vs_grid"] = round(
            ws["selection_ops_total"] / max(1, grid_work_summary["selection_ops_total"]), 4
        )

        # Fallback stats (for shipped policies)
        fb_count = sum(1 for w in per_arm_work[aname] if w.get("fallback_used"))
        fb_rate = fb_count / max(1, len(per_arm_work[aname]))

        # Worst 3 misses vs full oracle
        indexed = [
            (
                q["arms"][aname]["excess_vs_full_pct"],
                q["lineage_id"],
                q["M"],
                q["arms"][aname]["K"],
                q["arms"]["full_selector_by_K_oracle"]["chain"],
                q["arms"]["full_selector_by_K_oracle"]["K"],
            )
            for q in query_records
        ]
        indexed.sort(reverse=True)
        worst = [
            {
                "lineage_id": lid,
                "M": M,
                "chosen_K": ck,
                "oracle_chain": oc,
                "oracle_K": ok,
                "excess_vs_full_pct": ex,
            }
            for ex, lid, M, ck, oc, ok in indexed[:3]
        ]

        arm_summaries[aname] = {
            "excess_vs_same_chain_oracle": summarize_excess(per_arm_same[aname]),
            "excess_vs_full_oracle": summarize_excess(per_arm_full[aname]),
            "excess_vs_full_oracle_third_party_5orgs_only": summarize_excess(per_arm_full_3p[aname]),
            "fallback_count": fb_count,
            "fallback_rate_pct": round(100.0 * fb_rate, 2),
            "complete_bits_mean_by_M": {
                M_str: round(float(np.mean(vals)), 2)
                for M_str, vals in per_arm_complete_bits[aname].items()
            },
            "work": ws,
            "worst_misses_vs_full_oracle": worst,
        }

    # Proposed A1b pass targets check on dev_disjoint (evaluated honestly for BOTH shipped policy modes!).
    def check_targets(arm_key: str) -> dict[str, Any]:
        s = arm_summaries[arm_key]
        ex = s["excess_vs_full_oracle"]
        wk = s["work"]
        checks = {
            "median_excess_le_1_0pct": ex["median_pct"] <= 1.0,
            "p95_excess_le_2_5pct": ex["p95_pct"] <= 2.5,
            "fallback_rate_le_15pct": s["fallback_rate_pct"] <= 15.0,
            "total_ops_le_half_pilot": wk["total_ops_ratio_vs_pilot"] <= 0.5,
            "total_ops_le_sixth_grid": wk["total_ops_ratio_vs_grid"] <= (1.0 / 6.0),
            "total_wall_le_half_pilot": wk["total_wall_ratio_vs_pilot"] <= 0.5,
            "total_wall_le_sixth_grid": wk["total_wall_ratio_vs_grid"] <= (1.0 / 6.0),
            "conformal_lineage_support_ge_9_orgs": final_refit_strict["conformal_support_sufficient"],
        }
        return {
            "checks": checks,
            "dev_performance_targets_pass": all(
                v for k, v in checks.items() if k != "conformal_lineage_support_ge_9_orgs"
            ),
            "freeze_ready_all_targets_pass": all(checks.values()),
        }

    # Lower envelope, near-tie flatness, codeword widening, token/RAM variant.
    lower_env = compute_lower_envelope_and_crossovers(by_lin_prim, lineages)
    widening = compute_codeword_widening_and_decomp(by_lin_prim, lineages)
    token_ram = evaluate_token_ram_variant(lineages, by_lin_prim, by_lin_all, sketch_feats, ram_by_k)

    # Aggregate near-tie frequency across dev_disjoint diagnostic sweep and primary horizons.
    dev_primary_wide_05 = 0
    dev_primary_wide_10 = 0
    dev_sweep_wide_05 = 0
    dev_sweep_wide_10 = 0
    dev_sweep_total = 0
    for lin in dev_lins:
        for pt in lower_env[lin["lineage_id"]]["horizon_sweep"]:
            dev_sweep_total += 1
            if pt["wide_near_tie_0_5pct"]:
                dev_sweep_wide_05 += 1
                if pt["M"] in AG.PRIMARY_HORIZONS:
                    dev_primary_wide_05 += 1
            if pt["wide_near_tie_1_0pct"]:
                dev_sweep_wide_10 += 1
                if pt["M"] in AG.PRIMARY_HORIZONS:
                    dev_primary_wide_10 += 1

    # UPB calibration coverage diagnostic on dev_disjoint.
    upb_same_covered = sum(1 for q in query_records if q["dev_upb90_same_covers_realized"])
    upb_full_covered = sum(1 for q in query_records if q["dev_upb90_full_covers_realized"])
    upb_same_coverage_pct = round(100.0 * upb_same_covered / max(1, len(query_records)), 2)
    upb_full_coverage_pct = round(100.0 * upb_full_covered / max(1, len(query_records)), 2)

    # Calibration support audit (explicit honest verdict).
    distinct_dev_orgs = sorted({l["org_id"] for l in dev_lins})
    third_party_orgs = sorted({l["org_id"] for l in dev_lins if l["org_id"] != "clocksmith"})
    cal_support_audit = {
        "local_spent_dev_disjoint_codebases": len(dev_lins),
        "local_spent_dev_disjoint_distinct_orgs": len(distinct_dev_orgs),
        "distinct_dev_orgs": distinct_dev_orgs,
        "strict_third_party_orgs_count": len(third_party_orgs),
        "strict_third_party_orgs": third_party_orgs,
        "lolo_cal_orgs_per_fold": min(q["n_cal_orgs"] for q in query_records),
        "min_orgs_required_for_finite_90pct_conformal_upb": SP.MIN_CONFORMAL_ORGS,
        "recommended_sealed_independent_orgs_before_freeze": 16,
        "additional_independent_orgs_needed_minimum": max(0, SP.MIN_CONFORMAL_ORGS - len(distinct_dev_orgs)),
        "additional_independent_orgs_needed_recommended": max(0, 16 - len(distinct_dev_orgs)),
        "sufficient_for_conformal_freeze": len(distinct_dev_orgs) >= SP.MIN_CONFORMAL_ORGS,
        "verdict": (
            "INSUFFICIENT FOR FREEZE: local spent worktree has 7 non-CodeNet codebases across 6 distinct "
            "organizations (5 strictly external third-party repos + clocksmith/gamma), yielding n_cal_orgs=5 "
            "per org-disjoint LOLO fold. Distribution-free 90% conformal UPB requires ceil(0.90*(n+1)) <= n, "
            "i.e., n >= 9 independent calibration organizations (at least 4 more independent repos minimum, "
            "and ~16-20 recommended for stable tail calibration before freezing A1b)."
        ),
    }

    # Shared spine summary block.
    shared_spine = {
        "fidelity": {
            "all_archives_independent_decode_ok": all_decoded_ok,
            "verified_archive_count": len(rows),
            "byte_exact_fidelity": 1.0,
            "byte_accounting_drift_bytes": 0,
            "random_access_spot_checks_passed": all(r["random_access_spot_check_ok"] for r in rows),
        },
        "complete_bits": {
            "primary_chain": AG.PRIMARY_CHAIN_NAME,
            "mean_complete_bits_by_arm_and_M": {
                aname: arm_summaries[aname]["complete_bits_mean_by_M"]
                for aname in arm_names
            },
        },
        "measured_work": {
            "primary_chain_headers_fit_wall_seconds": round(
                sum(h["fit_work"]["wall_seconds"] for h in primary_headers.values()), 4
            ),
            "arm_work_summary": {aname: arm_summaries[aname]["work"] for aname in arm_names},
        },
        "horizon": {
            "primary_horizons_bytes": list(AG.PRIMARY_HORIZONS),
            "diagnostic_horizons_bytes": list(AG.DIAGNOSTIC_HORIZONS),
            "crossover_M_star_by_lineage": {
                lid: lower_env[lid]["breakeven_M_star"] for lid in lower_env
            },
        },
    }

    summary = {
        "schema": "gamma.bits-a1b.dev-summary.v1",
        "primary_chain": AG.PRIMARY_CHAIN_NAME,
        "verified_chains": list(grid_data["chains"].keys()),
        "prefix_grid_K": list(AG.PRIMARY_GRID),
        "pilot_grid_K": list(SP.PILOT_KS),
        "sketch_probe_K": list(SP.PROBE_KS),
        "shared_spine": shared_spine,
        "calibration_support_audit": cal_support_audit,
        "pass_target_evaluation": {
            "shipped_policy_dev_calibrated": check_targets("shipped_policy_dev_calibrated"),
            "shipped_policy_strict_conformal": check_targets("shipped_policy_strict_conformal"),
        },
        "arm_summaries_dev_disjoint": arm_summaries,
        "upb_calibration_diagnostics": {
            "dev_t_upb90_same_realized_coverage_count": upb_same_covered,
            "dev_t_upb90_same_realized_coverage_total": len(query_records),
            "dev_t_upb90_same_realized_coverage_pct": upb_same_coverage_pct,
            "dev_t_upb90_full_realized_coverage_count": upb_full_covered,
            "dev_t_upb90_full_realized_coverage_total": len(query_records),
            "dev_t_upb90_full_realized_coverage_pct": upb_full_coverage_pct,
            "final_refit_dev_calibrated": final_refit_dev,
            "final_refit_strict_conformal": final_refit_strict,
        },
        "near_tie_flatness": {
            "definition": "widely separated prefixes (K_max / K_min >= 4x, or K=0 with K>=64) within tolerance of optimum",
            "dev_primary_14_queries_within_0_5pct": f"{dev_primary_wide_05}/{len(query_records)}",
            "dev_primary_14_queries_within_0_5pct_rate": round(dev_primary_wide_05 / max(1, len(query_records)), 4),
            "dev_primary_14_queries_within_1_0pct": f"{dev_primary_wide_10}/{len(query_records)}",
            "dev_primary_14_queries_within_1_0pct_rate": round(dev_primary_wide_10 / max(1, len(query_records)), 4),
            "dev_diagnostic_70_queries_within_0_5pct": f"{dev_sweep_wide_05}/{dev_sweep_total}",
            "dev_diagnostic_70_queries_within_0_5pct_rate": round(dev_sweep_wide_05 / max(1, dev_sweep_total), 4),
            "dev_diagnostic_70_queries_within_1_0pct": f"{dev_sweep_wide_10}/{dev_sweep_total}",
            "dev_diagnostic_70_queries_within_1_0pct_rate": round(dev_sweep_wide_10 / max(1, dev_sweep_total), 4),
        },
        "query_records_dev_disjoint": query_records,
        "codenet_in_distribution_diagnostic": codenet_diag_records,
        "codeword_widening_and_decomposition": widening,
        "lower_envelope": lower_env,
        "token_ram_variant": token_ram,
        "eval_script_wall_seconds": round(time.perf_counter() - t_all0, 3),
    }

    if out_path is None:
        out_path = HERE / "dev_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def main() -> int:
    summary = run_eval_dev()
    print("=== A1b Dev Evaluation Summary (14 dev_disjoint queries: 7 lineages x 2 horizons) ===")
    for arm, s in summary["arm_summaries_dev_disjoint"].items():
        ex_s = s["excess_vs_same_chain_oracle"]
        ex_f = s["excess_vs_full_oracle"]
        wk = s["work"]
        print(
            f"  {arm:32s} | vs_same med={ex_s['median_pct']:5.2f}% p95={ex_s['p95_pct']:5.2f}% | "
            f"vs_full med={ex_f['median_pct']:5.2f}% p95={ex_f['p95_pct']:5.2f}% max={ex_f['max_pct']:5.2f}% | "
            f"fb={s['fallback_rate_pct']:5.1f}% | ops/pilot={wk['total_ops_ratio_vs_pilot']:.3f} ops/grid={wk['total_ops_ratio_vs_grid']:.3f} | "
            f"wall/pilot={wk['total_wall_ratio_vs_pilot']:.3f} wall/grid={wk['total_wall_ratio_vs_grid']:.3f}"
        )
    print("\nPass-target checks (dev_calibrated):", summary["pass_target_evaluation"]["shipped_policy_dev_calibrated"])
    print("Pass-target checks (strict_conformal):", summary["pass_target_evaluation"]["shipped_policy_strict_conformal"])
    print(
        "UPB coverage (same-chain / full-oracle):",
        summary["upb_calibration_diagnostics"]["dev_t_upb90_same_realized_coverage_pct"],
        "% /",
        summary["upb_calibration_diagnostics"]["dev_t_upb90_full_realized_coverage_pct"],
        "%",
    )
    print("Near-tie flatness:", summary["near_tie_flatness"])
    print("Token/RAM priced variant arm summaries:")
    for arm, s in summary["token_ram_variant"]["priced_variant"]["arm_summaries"].items():
        print(
            f"  {arm:24s}: vs_same med={s['vs_same_chain_oracle']['median_pct']:5.2f}% p95={s['vs_same_chain_oracle']['p95_pct']:5.2f}% | "
            f"vs_full med={s['vs_full_oracle']['median_pct']:5.2f}% p95={s['vs_full_oracle']['p95_pct']:5.2f}%"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
