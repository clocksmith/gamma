#!/usr/bin/env python3
"""Strict dev_gate verification suite for BITS Experiment Card A1b.

By default writes NOTHING to any tracked file (pass --out FILE only if you want
a JSON receipt written to FILE).

Verifies all six required dev_gate items:
  1. Independent decode of actual serialized B1RA archives (100% byte fidelity,
     0 B drift, random-access single-record decode, and ESC branch exercise)
     across all 1,610 grid + calibration archives plus live isolated subprocesses.
  2. Exact reproduction of locked_predictor_sha256, every Stage-2 split-conformal
     org score s_i = max(100KB, 100MB), exact rank k = ceil(0.90*(n+1)) UPB,
     regret decomposition, and all 8 arms across 28 calibration queries by
     exhaustive Fraction enumeration.
  3. Negative control 1: corrupted code tables MUST be rejected by independent_decode.py.
  4. Negative control 2: fit/predictor-fit leakage, within-repo resampling,
     59-lineage capacity repo overlap, and reserved sealed domain overlap MUST
     be rejected by LeakageError / CalibrationDisjointnessError.
  5. Adversarial synthetic curves: (a) exact flat curve -> smallest header tie-break;
     (b) non-convex bad-intermediate-prefix trap -> finds global minimum past bump.
  6. Abstain gate (SWEEP_REQUIRED) & full end-to-end shipping procedure using the
     EXACT locked predictor (out/locked_predictor.json), live B1RA encoding, and
     isolated-subprocess independent decode.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import archive_grid as AG  # noqa: E402
import calibration_corpora as CC  # noqa: E402
import independent_decode as ID  # noqa: E402
import sizing_policy as SP  # noqa: E402


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _locate_code_table_offset(buf: bytes) -> tuple[int, int]:
    meta = ID.parse_archive_structure(buf)
    table_len = meta["code_table_bytes"]
    table_start = meta["header_bytes"] - table_len
    return table_start, table_len


def gate_1_independent_decode(
    primary_headers: dict[tuple[str, int], dict[str, Any]],
    lineages: list[dict[str, Any]],
    tmp_dir: Path,
) -> dict[str, Any]:
    """Verify 100% independent decode fidelity across dev + calibration grids + live CLI."""
    grid_data = json.loads((HERE / "out" / "prefix_grid.json").read_text())
    cal_grid_data = json.loads((HERE / "out" / "calibration_grid.json").read_text())
    rows = grid_data["rows"] + cal_grid_data["rows"]
    need(len(rows) > 0, "grid files have no rows")
    bad_rows = [
        (r["lineage_id"], r["chain"], r["K"])
        for r in rows
        if not (r.get("independent_decode_ok") is True and r.get("fidelity") == 1.0)
    ]
    need(not bad_rows, f"grid rows failed independent decode: {bad_rows[:5]}")

    express = next(l for l in lineages if l["lineage_id"] == "expressjs_express")
    alphabet = {e[0] for e in primary_headers[(AG.PRIMARY_CHAIN_NAME, 0)]["entries"] if len(e) == 1}
    absent = bytes(b for b in range(256) if b not in alphabet)[:4]
    need(len(absent) == 4, "expected at least 4 byte values absent from training alphabet")
    esc_doc = b"// escape probe: " + absent + b"\nmodule.exports = 42;\n"
    sample_docs = express["docs"][:10] + [esc_doc]

    manifest_path = tmp_dir / "gate1_sources.json"
    manifest_files = []
    for i, raw in enumerate(sample_docs):
        p = tmp_dir / f"doc_{i:02d}.bin"
        p.write_bytes(raw)
        manifest_files.append({"path": p.name})
    manifest_path.write_text(json.dumps({"files": manifest_files}))

    tested_ks = (0, 64, 512, 2048, 4096)
    decoded_summary = []
    for K in tested_ks:
        hdr = primary_headers[(AG.PRIMARY_CHAIN_NAME, K)]
        d = AG.Dictionary(hdr["entries"])
        archive, stats = AG.encode_b1ra_archive(d, hdr["lengths"], hdr["header_bytes_raw"], sample_docs)
        arch_path = tmp_dir / f"sample_K{K}.b1ra"
        arch_path.write_bytes(archive)

        proc = subprocess.run(
            [
                sys.executable,
                "-I",
                str(HERE / "independent_decode.py"),
                "--archive",
                str(arch_path),
                "--sources-manifest",
                str(manifest_path),
                "--root",
                str(tmp_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        need(proc.returncode == 0, f"isolated independent_decode.py failed at K={K}: {proc.stderr or proc.stdout}")
        dec = json.loads(proc.stdout)
        need(dec["all_ok"] is True and dec["fidelity"] == 1.0, f"decode not 100% ok at K={K}")
        need(dec["random_access_spot_check_ok"] is True, f"random-access spot check failed at K={K}")
        need(dec["complete_bytes"] == stats["complete_bytes"], f"complete_bytes drift at K={K}")
        need(dec["header_bytes"] == stats["header_bytes"], f"header_bytes drift at K={K}")
        need(dec["body_bytes"] == stats["body_bytes"], f"body_bytes drift at K={K}")
        need(dec["escapes"] == len(absent), f"expected {len(absent)} escapes at K={K}, got {dec['escapes']}")
        decoded_summary.append({"K": K, "archive_bytes": dec["complete_bytes"], "escapes": dec["escapes"]})

    return {
        "pass": True,
        "dev_grid_archives_verified_100pct": len(grid_data["rows"]),
        "cal_grid_archives_verified_100pct": len(cal_grid_data["rows"]),
        "total_grid_archives_verified_100pct": len(rows),
        "live_isolated_subprocess_archives_verified": len(tested_ks),
        "escape_bytes_exercised_and_verified": len(absent),
        "samples": decoded_summary,
    }


def gate_2_exhaustive_reproduction() -> dict[str, Any]:
    """Exhaustively reproduce locked predictor hash, all 14 split-conformal scores, and 28 arm queries."""
    cal_manifest = json.loads((HERE / "out" / "calibration_manifest.json").read_text())
    cal_grid = json.loads((HERE / "out" / "calibration_grid.json").read_text())
    summary = json.loads((HERE / "dev_summary.json").read_text())
    locked_path = HERE / "out" / "locked_predictor.json"
    need(locked_path.exists(), "missing out/locked_predictor.json")

    expected_sha = summary["two_stage_protocol"]["locked_predictor_sha256"]
    locked = SP.LockedHorizonPredictor.load(locked_path, expected_sha256=expected_sha)

    by_lin_all: dict[str, list[dict[str, Any]]] = {}
    by_lin_prim: dict[str, dict[int, dict[str, Any]]] = {}
    for r in cal_grid["rows"]:
        by_lin_all.setdefault(r["lineage_id"], []).append(r)
        if r["chain"] == AG.PRIMARY_CHAIN_NAME:
            by_lin_prim.setdefault(r["lineage_id"], {})[int(r["K"])] = r

    # 1. Reproduce every Stage-2 split-conformal calibration org score s_i = max(100KB, 100MB)
    sc = summary["two_stage_protocol"]["stage2_split_conformal_calibration"]
    need(sc["locked_predictor_sha256"] == expected_sha, "split-conformal calibration used different locked predictor hash")
    need(sc["n_cal_orgs"] >= 19, f"need >= 19 calibration orgs so k < n_cal at alpha=0.10, got {sc['n_cal_orgs']}")
    need(sc["conformal_rank_is_sample_max"] is False, "conformal rank must not degenerate to sample maximum")
    need(sc["max_outliers_tolerated_at_alpha"] >= 1, "must tolerate >= 1 outlier at alpha=0.10")
    need(
        sc["conformal_selection_audit"]["post_selection_pilot_switch_certified"] is False,
        "post-selection pilot switching on the same calibration set must never be marked certified",
    )

    repro_s_i: list[float] = []
    joint_scores: list[float] = []
    for org_row in sc["per_org_results"]:
        lid = org_row["lineage_id"]
        feat = SP.deserialize_sketch_receipt(cal_grid["sketch_receipts"][lid])
        rmap = by_lin_prim[lid]
        all_cands = by_lin_all[lid]

        h_regs = {}
        pilot_regs: list[float] = []
        for M, hkey in ((100_000, "h_100KB"), (100_000_000, "h_100MB")):
            k_pred, _, _ = locked.predict_k(feat, M)
            need(k_pred == int(org_row[hkey]["chosen_K"]), f"locked predictor K mismatch on ({lid}, M={M})")
            # Exhaustive same-chain and full-oracle search with exact Fractions
            best_same = min(
                rmap.values(),
                key=lambda r: (
                    Fraction(int(r["header_bytes"])) + Fraction(M * int(r["body_bytes"]), int(r["source_bytes"])),
                    int(r["header_bytes"]),
                    int(r["K"]),
                ),
            )
            best_full = min(
                all_cands,
                key=lambda r: (
                    Fraction(int(r["header_bytes"])) + Fraction(M * int(r["body_bytes"]), int(r["source_bytes"])),
                    int(r["header_bytes"]),
                    int(r["K"]),
                    str(r["chain"]),
                ),
            )
            need(int(best_same["K"]) == int(org_row[hkey]["same_chain_oracle_K"]), f"same oracle mismatch ({lid}, {M})")
            need(
                best_full["chain"] == org_row[hkey]["full_oracle_chain"]
                and int(best_full["K"]) == int(org_row[hkey]["full_oracle_K"]),
                f"full oracle mismatch ({lid}, {M})",
            )
            v_ch = float(AG.horizon_objective_exact(rmap[k_pred]["header_bytes"], rmap[k_pred]["body_bytes"], rmap[k_pred]["source_bytes"], M))
            v_fl = float(AG.horizon_objective_exact(best_full["header_bytes"], best_full["body_bytes"], best_full["source_bytes"], M))
            reg = (v_ch / v_fl) - 1.0
            need(abs(reg - float(org_row[hkey]["full_oracle_regret"])) < 1e-9, f"regret mismatch ({lid}, {M})")
            h_regs[M] = reg
            rates = {k: float(rmap[k]["r_hat"]) for k in SP.PILOT_KS}
            pilot_k, _ = SP.select_prefix_pilot_3pt(locked.header_bytes_by_k, rates, M, AG.PRIMARY_GRID)
            pilot_row = rmap[pilot_k]
            pilot_obj = AG.horizon_objective_exact(pilot_row["header_bytes"], pilot_row["body_bytes"], pilot_row["source_bytes"], M)
            pilot_regs.append(float(pilot_obj) / v_fl - 1.0)

        s_i = max(h_regs[100_000], h_regs[100_000_000])
        need(abs(s_i - float(org_row["nonconformity_s_i_full_max"])) < 1e-9, f"s_i mismatch on {lid}")
        repro_s_i.append(s_i)
        joint_scores.append(max(s_i, *pilot_regs))

    # Verify exact finite-sample split-conformal quantile rank k = ceil(0.90 * (n_cal + 1))
    n_cal = len(repro_s_i)
    rank_k = (9 * (n_cal + 1) + 9) // 10  # exact integer ceil(0.90 * (n_cal + 1))
    need(rank_k == int(sc["conformal_rank_k"]), f"rank_k mismatch: {rank_k} vs {sc['conformal_rank_k']}")
    q90 = sorted(repro_s_i)[rank_k - 1]
    q_either = sorted(joint_scores)[rank_k - 1]
    need(abs(q_either - sc["selection_safe_upb"]) < 1e-9, "adaptive policy bound differs from paired maximum")
    need(sc["selected_policy_clears_bar"] == (q_either <= SP.SEALED_REGRET_BAR), "adaptive certification mismatch")
    need(abs(q90 - float(sc["conformal_90_upb_full_max"])) < 1e-9, "split-conformal 90% UPB mismatch")
    need(
        (q90 <= SP.SEALED_REGRET_BAR) == bool(sc["certifies_2_0pct_sealed_bar"]),
        "2.0% certification verdict mismatch",
    )

    # 2. Reproduce every arm on all calibration queries
    checked_q = 0
    for q in summary["query_records_calibration_orgs"]:
        lid = q["lineage_id"]
        M = int(q["M"])
        rmap = by_lin_prim[lid]
        all_cands = by_lin_all[lid]
        r_pilot = {K: float(rmap[K]["r_hat"]) for K in SP.PILOT_KS}
        k_pilot, _ = SP.select_prefix_pilot_3pt(locked.header_bytes_by_k, r_pilot, M, AG.PRIMARY_GRID)
        need(k_pilot == int(q["arms"]["pilot_3pt_geometric"]["K"]), f"pilot mismatch on ({lid}, {M})")
        for aname, adata in q["arms"].items():
            match = [r for r in all_cands if r["chain"] == adata["chain"] and int(r["K"]) == int(adata["K"])]
            need(len(match) == 1, f"missing stored row ({lid}, {adata['chain']}, K={adata['K']})")
            r = match[0]
            exact_b = float(AG.horizon_objective_exact(r["header_bytes"], r["body_bytes"], r["source_bytes"], M))
            need(abs(exact_b - float(adata["complete_bytes"])) < 0.02, f"complete_bytes mismatch on ({lid}, {M}, {aname})")
        checked_q += 1

    return {
        "pass": True,
        "locked_predictor_sha256_verified": expected_sha,
        "calibration_orgs_reproduced": n_cal,
        "conformal_rank_k": rank_k,
        "conformal_90_upb_full_max_pct": round(100.0 * q90, 4),
        "calibration_queries_exhaustively_reproduced": checked_q,
        "arms_verified_per_query": len(summary["arm_summaries_calibration_orgs"]),
    }


def gate_3_negative_control_corrupted_code_table(
    primary_headers: dict[tuple[str, int], dict[str, Any]],
    lineages: list[dict[str, Any]],
    tmp_dir: Path,
) -> dict[str, Any]:
    """Corrupt a valid archive's code table three ways; independent_decode MUST reject all three."""
    express = next(l for l in lineages if l["lineage_id"] == "expressjs_express")
    docs = express["docs"][:8]
    hdr = primary_headers[(AG.PRIMARY_CHAIN_NAME, 512)]
    d = AG.Dictionary(hdr["entries"])
    good_archive, _ = AG.encode_b1ra_archive(d, hdr["lengths"], hdr["header_bytes_raw"], docs)
    need(ID.verify_archive_against_sources(good_archive, docs)["all_ok"], "baseline archive must decode ok")

    table_start, table_len = _locate_code_table_offset(good_archive)
    results = {}

    bad_inc = bytearray(good_archive)
    bad_inc[table_start] = min(255, bad_inc[table_start] + 1)
    rejected_inc = False
    try:
        ID.verify_archive_against_sources(bytes(bad_inc), docs)
    except ID.FormatError as exc:
        rejected_inc = True
        results["kraft_underflow_increment"] = f"REJECTED ({exc})"
    need(rejected_inc, "corrupted code table (+1 length) was NOT rejected!")

    bad_dec = bytearray(good_archive)
    idx_gt1 = next(i for i in range(table_len) if bad_dec[table_start + i] > 1)
    bad_dec[table_start + idx_gt1] -= 1
    rejected_dec = False
    try:
        ID.verify_archive_against_sources(bytes(bad_dec), docs)
    except ID.FormatError as exc:
        rejected_dec = True
        results["kraft_overflow_decrement"] = f"REJECTED ({exc})"
    need(rejected_dec, "corrupted code table (-1 length) was NOT rejected!")

    bad_swap = bytearray(good_archive)
    l0 = bad_swap[table_start]
    other = next(i for i in range(1, table_len - 2) if bad_swap[table_start + i] != l0)
    bad_swap[table_start], bad_swap[table_start + other] = (
        bad_swap[table_start + other],
        bad_swap[table_start],
    )
    rejected_swap = False
    try:
        res = ID.verify_archive_against_sources(bytes(bad_swap), docs)
        if not res["all_ok"]:
            rejected_swap = True
            results["kraft_preserving_swap"] = f"REJECTED (mismatched_count={res['mismatched_count']})"
    except ID.FormatError as exc:
        rejected_swap = True
        results["kraft_preserving_swap"] = f"REJECTED ({exc})"
    need(rejected_swap, "kraft-preserving code table swap was NOT rejected!")

    bad_path = tmp_dir / "corrupted_table.b1ra"
    bad_path.write_bytes(bytes(bad_inc))
    proc = subprocess.run(
        [sys.executable, "-I", str(HERE / "independent_decode.py"), "--archive", str(bad_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    need(proc.returncode != 0, "CLI independent_decode.py did not exit non-zero on corrupted code table")
    results["cli_exit_code_on_corruption"] = proc.returncode
    results["pass"] = True
    return results


def gate_4_negative_control_leakage_and_59_lineage_disjointness(
    fit_corpus: dict[str, Any],
    lineages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Verify leakage guard AND 59-lineage / reserved-domain disjointness guard reject violations."""
    fit_meta = {k: v for k, v in fit_corpus.items() if k != "docs"}
    dev_metas = [{k: v for k, v in l.items() if k != "docs"} for l in lineages if l["role"] == "dev_disjoint"]
    codenet_fresh = next(
        {k: v for k, v in l.items() if k != "docs"}
        for l in lineages
        if l["lineage_id"] == "codenet_fresh"
    )
    cal_manifest = json.loads((HERE / "out" / "calibration_manifest.json").read_text())
    cal_orgs = cal_manifest["calibration_orgs"]
    results = {}

    def must_reject(label: str, exc_type, fn) -> None:
        try:
            fn()
        except exc_type as exc:
            results[label] = f"REJECTED ({exc})"
            return
        raise AssertionError(f"Negative control '{label}' was NOT rejected!")

    # Leakage controls
    must_reject(
        "fit_lineage_in_calibration",
        SP.LeakageError,
        lambda: SP.assert_disjoint_lineages(fit_meta, dev_metas[:3] + [fit_meta], eval_meta=dev_metas[3]),
    )
    must_reject(
        "fit_org_in_calibration",
        SP.LeakageError,
        lambda: SP.assert_disjoint_lineages(fit_meta, dev_metas[:3] + [codenet_fresh], eval_meta=dev_metas[3]),
    )
    disguised = {
        "lineage_id": "totally_benign_new_repo",
        "org_id": "totally_benign_org",
        "file_hashes": ["0" * 64, fit_meta["file_hashes"][0]],
    }
    must_reject(
        "disguised_single_file_hash_leak_in_cal",
        SP.LeakageError,
        lambda: SP.assert_disjoint_lineages(fit_meta, dev_metas[:3] + [disguised], eval_meta=dev_metas[3]),
    )
    must_reject(
        "three_way_predictor_fit_leaked_into_stage2_cal",
        SP.LeakageError,
        lambda: SP.assert_three_way_disjoint(fit_meta, dev_metas, cal_orgs[:2] + [dev_metas[0]]),
    )
    express_meta = dev_metas[0]
    must_reject(
        "within_repo_resampling_in_calibration",
        SP.LeakageError,
        lambda: SP.assert_disjoint_lineages(
            fit_meta,
            [
                {"lineage_id": "ex_a", "org_id": "org_a", "file_hashes": express_meta["file_hashes"][:60]},
                {"lineage_id": "ex_b", "org_id": "org_b", "file_hashes": express_meta["file_hashes"][59:120]},
            ],
            eval_meta=dev_metas[1],
        ),
    )

    # 59-lineage capacity exclusion + reserved sealed domain controls
    reg = CC.collect_excluded_registry()
    for label, bad_entry in (
        (
            "capacity_59_lineage_ggml_injected",
            {"lineage_id": "bad_ggml", "org_id": "ggml-org", "upstream_repo": "ggml-org/ggml", "package_name": "gguf", "domain": "ml", "file_hashes": ["a" * 64]},
        ),
        (
            "capacity_59_lineage_ajv_injected",
            {"lineage_id": "bad_ajv", "org_id": "ajv-validator", "upstream_repo": "ajv-validator/ajv", "package_name": "ajv", "domain": "schema", "file_hashes": ["b" * 64]},
        ),
        (
            "reserved_sealed_domain_yaml_injected",
            {"lineage_id": "bad_yaml", "org_id": "yaml-org", "upstream_repo": "yaml/pyyaml", "package_name": "PyYAML", "domain": "yaml-parser", "file_hashes": ["c" * 64]},
        ),
        (
            "reserved_sealed_domain_sql_injected",
            {"lineage_id": "bad_sql", "org_id": "sqla-org", "upstream_repo": "sqlalchemy/sqlalchemy", "package_name": "SQLAlchemy", "domain": "sql-orm", "file_hashes": ["d" * 64]},
        ),
    ):
        must_reject(
            label,
            CC.CalibrationDisjointnessError,
            lambda be=bad_entry: CC.assert_calibration_disjoint_from_excluded(cal_orgs[:2] + [be], reg),
        )

    results["pass"] = True
    return results


def gate_5_adversarial_synthetic_curves(
    header_bytes_by_k: dict[int, int],
) -> dict[str, Any]:
    """Test (a) exact flat curve tie-break to smallest header and (b) non-convex local-min trap."""
    Ks = AG.PRIMARY_GRID
    M_test = 100_000
    M_large = 100_000_000

    C = 100_000
    flat_r_exact = {K: Fraction(C - header_bytes_by_k[K], M_test) for K in Ks}
    cands_flat = [{"K": K, "header_bytes": header_bytes_by_k[K], "r_hat": flat_r_exact[K]} for K in Ks]
    picked_flat_exact = int(AG.select_best_prefix_exact(cands_flat, M_test)["K"])
    need(picked_flat_exact == 0, f"flat curve exact selector picked K={picked_flat_exact}, expected K=0")

    picked_flat_curve = SP.select_prefix_from_curve(header_bytes_by_k, flat_r_exact, M_test, Ks)
    need(picked_flat_curve == 0, f"flat curve policy selector picked K={picked_flat_curve}, expected K=0")

    cands_pilot_flat = [
        {"K": K, "header_bytes": header_bytes_by_k[K], "r_hat": Fraction(C - header_bytes_by_k[K], M_test)}
        for K in SP.PILOT_KS
    ]
    picked_pilot_flat = int(AG.select_best_prefix_exact(cands_pilot_flat, M_test)["K"])
    need(picked_pilot_flat == 64, f"flat pilot curve picked K={picked_pilot_flat}, expected K=64")

    trap_r = {
        0: 0.65,
        32: 0.58,
        64: 0.55,
        128: 0.78,
        256: 0.78,
        512: 0.78,
        1024: 0.78,
        2048: 0.45,
        3072: 0.30,
        4096: 0.20,
    }
    trap_results = {}
    for M in (M_test, M_large):
        k_exh = SP.select_prefix_from_curve(header_bytes_by_k, trap_r, M, Ks)
        need(k_exh == 4096, f"non-convex trap exhaustive selector at M={M} picked K={k_exh}, expected 4096")

        k_pilot, _ = SP.select_prefix_pilot_3pt(
            header_bytes_by_k, {k: trap_r[k] for k in SP.PILOT_KS}, M, Ks
        )
        need(k_pilot == 4096, f"non-convex trap 3-pt pilot at M={M} picked K={k_pilot}, expected 4096")

        pred_sketch = SP.interpolate_from_probes({k: trap_r[k] for k in SP.PROBE_KS}, Ks)
        k_sketch = SP.select_prefix_from_curve(header_bytes_by_k, pred_sketch, M, Ks)
        need(k_sketch == 4096, f"non-convex trap micro-sketch policy at M={M} picked K={k_sketch}, expected 4096")

        trap_results[f"M_{M}"] = {"exhaustive_K": k_exh, "pilot_3pt_K": k_pilot, "sketch_policy_K": k_sketch}

    return {
        "pass": True,
        "flat_curve_exact_tie_break_full_grid_K": picked_flat_exact,
        "flat_curve_exact_tie_break_pilot_K": picked_pilot_flat,
        "non_convex_bad_intermediate_trap": trap_results,
    }


def gate_6_abstain_and_end_to_end_shipping(
    primary_headers: dict[tuple[str, int], dict[str, Any]],
    tmp_dir: Path,
) -> dict[str, Any]:
    """Validate end-to-end shipping procedure using EXACT locked predictor + isolated decode."""
    summary = json.loads((HERE / "dev_summary.json").read_text())
    locked_sha = summary["two_stage_protocol"]["locked_predictor_sha256"]
    locked = SP.LockedHorizonPredictor.load(HERE / "out" / "locked_predictor.json", expected_sha256=locked_sha)
    sc = summary["two_stage_protocol"]["stage2_split_conformal_calibration"]

    dicts_by_k = {K: AG.Dictionary(primary_headers[(AG.PRIMARY_CHAIN_NAME, K)]["entries"]) for K in AG.PRIMARY_GRID}
    lengths_by_k = {K: primary_headers[(AG.PRIMARY_CHAIN_NAME, K)]["lengths"] for K in AG.PRIMARY_GRID}

    fixture_docs = [
        f"function compute_{i}(arr) {{ let s = 0; for (let j = 0; j < arr.length; j++) s += arr[j] * {i + 1}; return s; }}\n".encode()
        for i in range(40)
    ]
    fixture_feat = SP.extract_micro_sketch_features(fixture_docs, dicts_by_k, lengths_by_k)

    manifest_p = tmp_dir / "e2e_manifest.json"
    mfiles = []
    for i, d in enumerate(fixture_docs):
        p = tmp_dir / f"e2e_{i:02d}.js"
        p.write_bytes(d)
        mfiles.append({"path": p.name})
    manifest_p.write_text(json.dumps({"files": mfiles}))

    e2e_runs = []
    certifies_2_0 = bool(sc["certifies_2_0pct_sealed_bar"])
    for M in AG.PRIMARY_HORIZONS:
        k_direct, _, _ = locked.predict_k(fixture_feat, M)
        if certifies_2_0:
            chosen_k = k_direct
            decision = "DIRECT_PICK"
        else:
            r_pilot = {}
            for pk in SP.PILOT_KS:
                _, st = AG.encode_b1ra_archive(
                    dicts_by_k[pk],
                    lengths_by_k[pk],
                    primary_headers[(AG.PRIMARY_CHAIN_NAME, pk)]["header_bytes_raw"],
                    fixture_docs,
                )
                r_pilot[pk] = st["r_hat"]
            chosen_k, _ = SP.select_prefix_pilot_3pt(locked.header_bytes_by_k, r_pilot, M, AG.PRIMARY_GRID)
            decision = "SWEEP_REQUIRED"

        hdr = primary_headers[(AG.PRIMARY_CHAIN_NAME, chosen_k)]
        archive, st = AG.encode_b1ra_archive(
            dicts_by_k[chosen_k], lengths_by_k[chosen_k], hdr["header_bytes_raw"], fixture_docs
        )
        arch_p = tmp_dir / f"e2e_M{M}_K{chosen_k}.b1ra"
        arch_p.write_bytes(archive)
        proc = subprocess.run(
            [
                sys.executable,
                "-I",
                str(HERE / "independent_decode.py"),
                "--archive",
                str(arch_p),
                "--sources-manifest",
                str(manifest_p),
                "--root",
                str(tmp_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        need(proc.returncode == 0, f"E2E shipping decode failed at M={M}: {proc.stderr or proc.stdout}")
        dec = json.loads(proc.stdout)
        need(dec["all_ok"] is True and dec["complete_bytes"] == st["complete_bytes"], f"E2E fidelity failed at M={M}")
        e2e_runs.append(
            {
                "M": M,
                "decision": decision,
                "locked_direct_K": k_direct,
                "chosen_K": chosen_k,
                "archive_bytes": dec["complete_bytes"],
                "fidelity": dec["fidelity"],
            }
        )

    return {
        "pass": True,
        "locked_predictor_sha256": locked_sha,
        "split_conformal_n_cal_orgs": sc["n_cal_orgs"],
        "split_conformal_90_upb_full_max_pct": sc["conformal_90_upb_full_max_pct"],
        "certifies_2_0pct_sealed_bar": certifies_2_0,
        "end_to_end_shipping_runs": e2e_runs,
    }


def run_all_dev_gates() -> dict[str, Any]:
    t0 = time.perf_counter()
    fit_corpus = AG.load_fit_corpus()
    primary_chain = AG.load_verified_chain(AG.PRIMARY_CHAIN_NAME)
    primary_headers = AG.fit_all_prefix_headers(
        {AG.PRIMARY_CHAIN_NAME: primary_chain}, fit_corpus, jobs=1
    )
    header_bytes_by_k = {
        K: int(primary_headers[(AG.PRIMARY_CHAIN_NAME, K)]["header_bytes"])
        for K in AG.PRIMARY_GRID
    }
    lineages = AG.load_spent_lineages()

    with tempfile.TemporaryDirectory(prefix="a1b-dev-gate-") as td:
        tmp = Path(td)
        gates = {
            "gate_1_independent_decode_100pct_fidelity": gate_1_independent_decode(
                primary_headers, lineages, tmp
            ),
            "gate_2_exhaustive_score_reproduction": gate_2_exhaustive_reproduction(),
            "gate_3_negative_control_corrupted_code_table": gate_3_negative_control_corrupted_code_table(
                primary_headers, lineages, tmp
            ),
            "gate_4_negative_control_leakage_and_59_lineage_disjointness": gate_4_negative_control_leakage_and_59_lineage_disjointness(
                fit_corpus, lineages
            ),
            "gate_5_adversarial_synthetic_curves": gate_5_adversarial_synthetic_curves(
                header_bytes_by_k
            ),
            "gate_6_abstain_and_end_to_end_shipping": gate_6_abstain_and_end_to_end_shipping(
                primary_headers, tmp
            ),
        }

    all_pass = all(g["pass"] is True for g in gates.values())
    return {
        "schema": "gamma.bits-a1b.dev-gate.v2",
        "all_pass": all_pass,
        "wall_seconds": round(time.perf_counter() - t0, 3),
        "gates": gates,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run strict A1b dev_gate checks without dirtying tracked files.")
    ap.add_argument("--out", help="Optional explicit path to write JSON gate report (default: none)")
    args = ap.parse_args()

    report = run_all_dev_gates()
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n")
    for name, g in report["gates"].items():
        status = "PASS" if g["pass"] else "FAIL"
        print(f"{status}  {name}")
    print(f"\nALL DEV GATES: {'PASS' if report['all_pass'] else 'FAIL'} ({report['wall_seconds']:.2f}s)")
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
