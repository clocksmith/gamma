#!/usr/bin/env python3
"""Strict dev_gate verification suite for BITS Experiment Card A1b.

Verifies all six required dev_gate items:
  1. Independent decode of actual serialized B1RA archives (100% byte fidelity,
     0 B drift, random-access single-record decode, and ESC branch exercise).
  2. Exact reproduction of policy/pilot/oracle chosen prefixes by exhaustive
     enumeration of stored prefix scores.
  3. Negative control 1: corrupted code tables MUST be rejected by independent_decode.py.
  4. Negative control 2: fit-to-calibration/eval repository or file-hash leakage
     and within-repo resampling MUST be rejected by LeakageError.
  5. Adversarial synthetic curves: (a) exact flat curve -> smallest header tie-break;
     (b) non-convex bad-intermediate-prefix trap -> finds global minimum past bump.
  6. Abstain gate (SWEEP_REQUIRED) & full end-to-end shipping procedure including
     final refit, live archive encoding, and isolated-subprocess independent decode.
"""

from __future__ import annotations

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
import independent_decode as ID  # noqa: E402
import sizing_policy as SP  # noqa: E402


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _locate_code_table_offset(buf: bytes) -> tuple[int, int]:
    """Locate the byte offset and length (n + 2) of the code table inside a B1RA archive."""
    meta = ID.parse_archive_structure(buf)
    table_len = meta["code_table_bytes"]
    table_start = meta["header_bytes"] - table_len
    return table_start, table_len


def gate_1_independent_decode(
    primary_headers: dict[tuple[str, int], dict[str, Any]],
    lineages: list[dict[str, Any]],
    tmp_dir: Path,
) -> dict[str, Any]:
    """Serialize real B1RA archives (plus ESC-exercising fixture) and independently decode."""
    grid_data = json.loads((HERE / "out" / "prefix_grid.json").read_text())
    rows = grid_data["rows"]
    need(len(rows) > 0, "prefix_grid.json has no rows")
    bad_rows = [
        (r["lineage_id"], r["chain"], r["K"])
        for r in rows
        if not (r.get("independent_decode_ok") is True and r.get("fidelity") == 1.0)
    ]
    need(not bad_rows, f"grid rows failed independent decode: {bad_rows[:5]}")

    # Actually serialize real archives to disk for expressjs_express at 5 prefixes + ESC synthetic doc
    # and decode them with `python -I independent_decode.py` in an isolated subprocess!
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
        "grid_archives_verified_100pct": len(rows),
        "live_isolated_subprocess_archives_verified": len(tested_ks),
        "escape_bytes_exercised_and_verified": len(absent),
        "samples": decoded_summary,
    }


def gate_2_exhaustive_reproduction() -> dict[str, Any]:
    """Reproduce every chosen prefix by exhaustive enumeration of stored scores."""
    grid_data = json.loads((HERE / "out" / "prefix_grid.json").read_text())
    summary = json.loads((HERE / "dev_summary.json").read_text())
    rows = grid_data["rows"]

    by_lin_all: dict[str, list[dict[str, Any]]] = {}
    by_lin_prim: dict[str, dict[int, dict[str, Any]]] = {}
    for r in rows:
        by_lin_all.setdefault(r["lineage_id"], []).append(r)
        if r["chain"] == AG.PRIMARY_CHAIN_NAME:
            by_lin_prim.setdefault(r["lineage_id"], {})[int(r["K"])] = r

    header_bytes_by_k = {
        int(k.split(":K")[1]): int(v["header_bytes"])
        for k, v in grid_data["headers"].items()
        if k.startswith(f"{AG.PRIMARY_CHAIN_NAME}:K")
    }

    checked = 0
    for q in summary["query_records_dev_disjoint"]:
        lid = q["lineage_id"]
        M = int(q["M"])
        rmap = by_lin_prim[lid]
        all_cands = by_lin_all[lid]

        # 1. Exhaustive same-chain oracle reproduction
        best_same = None
        best_same_key = None
        for K in AG.PRIMARY_GRID:
            r = rmap[K]
            obj = Fraction(int(r["header_bytes"])) + Fraction(M * int(r["body_bytes"]), int(r["source_bytes"]))
            key = (obj, int(r["header_bytes"]), K)
            if best_same_key is None or key < best_same_key:
                best_same_key = key
                best_same = r
        need(
            int(best_same["K"]) == int(q["arms"]["same_chain_oracle"]["K"]),
            f"same-chain oracle mismatch on ({lid}, M={M})",
        )

        # 2. Exhaustive full selector-by-K oracle reproduction
        best_full = None
        best_full_key = None
        for r in all_cands:
            obj = Fraction(int(r["header_bytes"])) + Fraction(M * int(r["body_bytes"]), int(r["source_bytes"]))
            key = (obj, int(r["header_bytes"]), int(r["K"]), str(r["chain"]))
            if best_full_key is None or key < best_full_key:
                best_full_key = key
                best_full = r
        need(
            best_full["chain"] == q["arms"]["full_selector_by_K_oracle"]["chain"]
            and int(best_full["K"]) == int(q["arms"]["full_selector_by_K_oracle"]["K"]),
            f"full oracle mismatch on ({lid}, M={M})",
        )

        # 3. Exhaustive 3-point geometric pilot reproduction from stored pilot rates
        r_pilot = {K: float(rmap[K]["r_hat"]) for K in SP.PILOT_KS}
        k_pilot_repro, _ = SP.select_prefix_pilot_3pt(header_bytes_by_k, r_pilot, M, AG.PRIMARY_GRID)
        need(
            k_pilot_repro == int(q["arms"]["pilot_3pt_geometric"]["K"]),
            f"pilot mismatch on ({lid}, M={M}): got {k_pilot_repro}",
        )

        # 4. Verify shipped policy final_K matches decision rule (direct vs fallback to pilot)
        if q["dev_policy_decision"] == "SWEEP_REQUIRED":
            need(
                int(q["dev_policy_final_K"]) == k_pilot_repro,
                f"dev policy fallback K mismatch on ({lid}, M={M})",
            )
        else:
            need(
                int(q["dev_policy_final_K"]) == int(q["dev_policy_predicted_K"]),
                f"dev policy direct K mismatch on ({lid}, M={M})",
            )
        need(
            q["strict_policy_decision"] == "SWEEP_REQUIRED"
            and int(q["arms"]["shipped_policy_strict_conformal"]["K"]) == k_pilot_repro,
            f"strict policy expected SWEEP_REQUIRED -> pilot on ({lid}, M={M})",
        )

        # 5. Verify exact complete_bytes stored for every arm matches H_K + M * body/source
        for aname, adata in q["arms"].items():
            ch = adata["chain"]
            ak = int(adata["K"])
            match = [r for r in all_cands if r["chain"] == ch and int(r["K"]) == ak]
            need(len(match) == 1, f"missing stored row for ({lid}, {ch}, K={ak})")
            r = match[0]
            exact_b = float(Fraction(int(r["header_bytes"])) + Fraction(M * int(r["body_bytes"]), int(r["source_bytes"])))
            need(
                abs(exact_b - float(adata["complete_bytes"])) < 0.02,
                f"stored complete_bytes mismatch on ({lid}, M={M}, {aname})",
            )
        checked += 1

    return {
        "pass": True,
        "queries_exhaustively_reproduced": checked,
        "arms_verified_per_query": len(summary["arm_summaries_dev_disjoint"]),
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

    # 3a: +1 to one code length (Kraft sum < 1 -> incomplete code tree)
    bad_inc = bytearray(good_archive)
    bad_inc[table_start] = min(255, bad_inc[table_start] + 1)
    rejected_inc = False
    try:
        ID.verify_archive_against_sources(bytes(bad_inc), docs)
    except ID.FormatError as exc:
        rejected_inc = True
        results["kraft_underflow_increment"] = f"REJECTED ({exc})"
    need(rejected_inc, "corrupted code table (+1 length) was NOT rejected!")

    # 3b: -1 to one code length (Kraft sum > 1 -> over-subscribed / non-prefix code)
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

    # 3c: Swap two code lengths of unequal length on symbols used in docs (Kraft sum stays == 1!)
    bad_swap = bytearray(good_archive)
    # Pick two entries with different lengths
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

    # Also test via isolated subprocess CLI on 3a
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


def gate_4_negative_control_leakage_guard(
    fit_corpus: dict[str, Any],
    lineages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Deliberately leak fit repo / fit org / fit file hash / within-repo resampling -> LeakageError."""
    fit_meta = {k: v for k, v in fit_corpus.items() if k != "docs"}
    dev_metas = [{k: v for k, v in l.items() if k != "docs"} for l in lineages if l["role"] == "dev_disjoint"]
    codenet_fresh = next(
        {k: v for k, v in l.items() if k != "docs"}
        for l in lineages
        if l["lineage_id"] == "codenet_fresh"
    )
    results = {}

    def must_reject(label: str, fn) -> None:
        try:
            fn()
        except SP.LeakageError as exc:
            results[label] = f"REJECTED ({exc})"
            return
        raise AssertionError(f"Leakage control '{label}' was NOT rejected!")

    # 4a: Fit lineage itself leaked into calibration
    must_reject(
        "fit_lineage_in_calibration",
        lambda: SP.assert_disjoint_lineages(fit_meta, dev_metas[:3] + [fit_meta], eval_meta=dev_metas[3]),
    )

    # 4b: Same-org CodeNet fresh leaked into calibration
    must_reject(
        "fit_org_in_calibration",
        lambda: SP.assert_disjoint_lineages(fit_meta, dev_metas[:3] + [codenet_fresh], eval_meta=dev_metas[3]),
    )

    # 4c: Renamed disguise carrying just 1 file SHA-256 hash from codenet_primary
    disguised = {
        "lineage_id": "totally_benign_new_repo",
        "org_id": "totally_benign_org",
        "file_hashes": ["0" * 64, fit_meta["file_hashes"][0]],
    }
    must_reject(
        "disguised_single_file_hash_leak_in_cal",
        lambda: SP.assert_disjoint_lineages(fit_meta, dev_metas[:3] + [disguised], eval_meta=dev_metas[3]),
    )
    must_reject(
        "disguised_single_file_hash_leak_in_eval",
        lambda: SP.assert_disjoint_lineages(fit_meta, dev_metas[:3], eval_meta=disguised),
    )

    # 4d: File-level resampling inside one repo (two calibration units sharing a file hash)
    express_meta = dev_metas[0]
    fake_split_a = {
        "lineage_id": "express_resample_a",
        "org_id": "org_a",
        "file_hashes": express_meta["file_hashes"][:60],
    }
    fake_split_b = {
        "lineage_id": "express_resample_b",
        "org_id": "org_b",
        "file_hashes": express_meta["file_hashes"][59:120],  # shares 1 file
    }
    must_reject(
        "within_repo_resampling_in_calibration",
        lambda: SP.assert_disjoint_lineages(fit_meta, [fake_split_a, fake_split_b], eval_meta=dev_metas[1]),
    )

    # 4e: Same-org cross-codebase leak (authored_catalogue_dev in cal, clocksmith_gamma_core in eval)
    cat_meta = next(m for m in dev_metas if m["lineage_id"] == "authored_catalogue_dev")
    gam_meta = next(m for m in dev_metas if m["lineage_id"] == "clocksmith_gamma_core")
    must_reject(
        "same_org_cal_to_eval_leak",
        lambda: SP.assert_disjoint_lineages(fit_meta, [dev_metas[0], cat_meta], eval_meta=gam_meta),
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

    # (5a) Exact flat curve: H_K + M * r_K == C (exact rational constant!) for ALL K in PRIMARY_GRID.
    C = 100_000  # 100 KB total archive bytes for every K!
    flat_r_exact = {K: Fraction(C - header_bytes_by_k[K], M_test) for K in Ks}
    cands_flat = [
        {"K": K, "header_bytes": header_bytes_by_k[K], "r_hat": flat_r_exact[K]}
        for K in Ks
    ]
    picked_flat_exact = int(AG.select_best_prefix_exact(cands_flat, M_test)["K"])
    need(picked_flat_exact == 0, f"flat curve exact selector picked K={picked_flat_exact}, expected K=0 (smallest header)")

    picked_flat_curve = SP.select_prefix_from_curve(header_bytes_by_k, flat_r_exact, M_test, Ks)
    need(picked_flat_curve == 0, f"flat curve policy selector picked K={picked_flat_curve}, expected K=0")

    # Flat curve over pilot points (64, 512, 4096) with exact constant objective C2 = 200,000 at M_test,
    # and higher objective below K=64 so tie is among {64, 512, 4096}.
    # Exact tie on pilot points when interpolated linearly: choose M_large with identical constant rate r=0.5
    # and equal header? No, with real strictly increasing H_K, make exact tie on {64, 512, 4096}:
    flat_pilot_r = {K: float(Fraction(C - header_bytes_by_k[K], M_test)) for K in SP.PILOT_KS}
    # Directly verify exact-tie tie-breaking on the 3 pilot candidates
    cands_pilot_flat = [
        {"K": K, "header_bytes": header_bytes_by_k[K], "r_hat": Fraction(C - header_bytes_by_k[K], M_test)}
        for K in SP.PILOT_KS
    ]
    picked_pilot_flat = int(AG.select_best_prefix_exact(cands_pilot_flat, M_test)["K"])
    need(picked_pilot_flat == 64, f"flat pilot curve picked K={picked_pilot_flat}, expected K=64 (smallest header)")

    # (5b) Adversarial non-convex curve: good small prefix K=64 (r=0.55), TERRIBLE intermediate bump
    # at K in {128, 256, 512, 1024} (r=0.78), followed by a MUCH better global minimum at K=4096 (r=0.20)!
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
    # At M=100,000: K=64 costs 833 + 55,000 = 55,833; K=512 costs 3,788 + 78,000 = 81,788; K=4096 costs 32,325 + 20,000 = 52,325!
    # At M=100,000,000: K=4096 wins overwhelmingly!
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

        trap_results[f"M_{M}"] = {
            "exhaustive_K": k_exh,
            "pilot_3pt_K": k_pilot,
            "sketch_policy_K": k_sketch,
        }

    return {
        "pass": True,
        "flat_curve_exact_tie_break_full_grid_K": picked_flat_exact,
        "flat_curve_exact_tie_break_pilot_K": picked_pilot_flat,
        "non_convex_bad_intermediate_trap": trap_results,
    }


def gate_6_abstain_and_end_to_end_shipping(
    fit_corpus: dict[str, Any],
    primary_headers: dict[tuple[str, int], dict[str, Any]],
    lineages: list[dict[str, Any]],
    tmp_dir: Path,
) -> dict[str, Any]:
    """Validate SWEEP_REQUIRED triggers AND the full end-to-end shipping procedure (including final refit)."""
    grid_data = json.loads((HERE / "out" / "prefix_grid.json").read_text())
    fit_meta = {k: v for k, v in fit_corpus.items() if k != "docs"}
    dev_lins = [l for l in lineages if l["role"] == "dev_disjoint"]
    dicts_by_k = {K: AG.Dictionary(primary_headers[(AG.PRIMARY_CHAIN_NAME, K)]["entries"]) for K in AG.PRIMARY_GRID}
    lengths_by_k = {K: primary_headers[(AG.PRIMARY_CHAIN_NAME, K)]["lengths"] for K in AG.PRIMARY_GRID}
    header_bytes_by_k = {K: int(primary_headers[(AG.PRIMARY_CHAIN_NAME, K)]["header_bytes"]) for K in AG.PRIMARY_GRID}

    by_lin_all: dict[str, list[dict[str, Any]]] = {}
    by_lin_prim: dict[str, dict[int, dict[str, Any]]] = {}
    for r in grid_data["rows"]:
        by_lin_all.setdefault(r["lineage_id"], []).append(r)
        if r["chain"] == AG.PRIMARY_CHAIN_NAME:
            by_lin_prim.setdefault(r["lineage_id"], {})[int(r["K"])] = r

    cal_records = []
    for l in dev_lins:
        lid = l["lineage_id"]
        rmap = by_lin_prim[lid]
        all_cands = by_lin_all[lid]
        feat = SP.extract_micro_sketch_features(l["docs"], dicts_by_k, lengths_by_k)
        cal_records.append(
            {
                "meta": {k: v for k, v in l.items() if k != "docs"},
                "feat": feat,
                "true_r_by_k": {K: rmap[K]["r_hat"] for K in AG.PRIMARY_GRID},
                "oracle_obj_by_M": {
                    M: float(AG.horizon_objective_exact(
                        AG.select_best_prefix_exact(all_cands, M)["header_bytes"],
                        AG.select_best_prefix_exact(all_cands, M)["body_bytes"],
                        AG.select_best_prefix_exact(all_cands, M)["source_bytes"],
                        M,
                    ))
                    for M in AG.PRIMARY_HORIZONS
                },
                "same_oracle_obj_by_M": {
                    M: float(AG.horizon_objective_exact(
                        AG.select_best_prefix_exact(list(rmap.values()), M)["header_bytes"],
                        AG.select_best_prefix_exact(list(rmap.values()), M)["body_bytes"],
                        AG.select_best_prefix_exact(list(rmap.values()), M)["source_bytes"],
                        M,
                    ))
                    for M in AG.PRIMARY_HORIZONS
                },
            }
        )

    # Final shipping refit on all 7 dev_disjoint lineages (6 distinct orgs).
    pol_dev = SP.HorizonSizingPolicy(header_bytes_by_k, AG.PRIMARY_GRID, strict_conformal=False)
    refit_dev = pol_dev.fit_calibration(fit_meta, cal_records, AG.PRIMARY_HORIZONS)
    pol_strict = SP.HorizonSizingPolicy(header_bytes_by_k, AG.PRIMARY_GRID, strict_conformal=True)
    refit_strict = pol_strict.fit_calibration(fit_meta, cal_records, AG.PRIMARY_HORIZONS)

    # Create a brand-new unseen synthetic deployment fixture (disjoint org/hashes).
    fixture_docs = [
        f"function compute_{i}(arr) {{ let s = 0; for (let j = 0; j < arr.length; j++) s += arr[j] * {i + 1}; return s; }}\n".encode()
        for i in range(40)
    ]
    fixture_meta = {
        "lineage_id": "synthetic_shipping_fixture",
        "org_id": "synthetic_shipping_org",
        "file_hashes": [AG.sha256_bytes(d) for d in fixture_docs],
    }
    fixture_feat = SP.extract_micro_sketch_features(fixture_docs, dicts_by_k, lengths_by_k)

    # (6a) Strict conformal mode MUST emit SWEEP_REQUIRED because n_cal_orgs = 6 < 9!
    pred_strict = pol_strict.predict(fixture_meta, fixture_feat, 100_000)
    need(
        pred_strict["decision"] == "SWEEP_REQUIRED" and not pred_strict["conformal_support_sufficient"],
        f"strict_conformal should abstain when n_cal_orgs=6 < 9: {pred_strict}",
    )

    # (6b) High-uncertainty synthetic query MUST emit SWEEP_REQUIRED in dev_calibrated mode!
    noisy_feat = dict(fixture_feat)
    noisy_feat["paired_se_r"] = {k: 0.08 for k in fixture_feat["paired_se_r"]}  # huge 8% SE!
    pred_noisy = pol_dev.predict(fixture_meta, noisy_feat, 100_000_000)
    need(
        pred_noisy["decision"] == "SWEEP_REQUIRED" and pred_noisy["upb_90_active"] > SP.EXCESS_ABSTAIN_THRESHOLD,
        f"high-uncertainty query failed to trigger SWEEP_REQUIRED: {pred_noisy}",
    )

    # (6c) Synthetic 10-org calibration verifies strict_conformal transitions cleanly to finite conformal UPB!
    synth_cal = []
    for g in range(10):
        base = cal_records[g % len(cal_records)]
        synth_cal.append(
            {
                "meta": {
                    "lineage_id": f"synth_org_{g}",
                    "org_id": f"synth_org_{g}",
                    "file_hashes": [AG.sha256_bytes(f"synth_file_{g}_{j}".encode()) for j in range(5)],
                },
                "feat": base["feat"],
                "true_r_by_k": base["true_r_by_k"],
                "oracle_obj_by_M": base["oracle_obj_by_M"],
                "same_oracle_obj_by_M": base["same_oracle_obj_by_M"],
            }
        )
    pol_conf10 = SP.HorizonSizingPolicy(header_bytes_by_k, AG.PRIMARY_GRID, strict_conformal=True)
    refit_conf10 = pol_conf10.fit_calibration(fit_meta, synth_cal, AG.PRIMARY_HORIZONS)
    need(refit_conf10["conformal_support_sufficient"] is True, "10 independent orgs must satisfy conformal support")
    pred_conf10 = pol_conf10.predict(fixture_meta, fixture_feat, 100_000)
    need(pred_conf10["upb_90_conformal"] is not None, "conformal 90% UPB must be finite for n_cal_orgs=10")

    # (6d) End-to-end shipping procedure on fixture at both horizons: predict -> (fallback if needed) -> encode -> isolated independent decode!
    e2e_results = []
    manifest_p = tmp_dir / "e2e_manifest.json"
    mfiles = []
    for i, d in enumerate(fixture_docs):
        p = tmp_dir / f"e2e_{i:02d}.js"
        p.write_bytes(d)
        mfiles.append({"path": p.name})
    manifest_p.write_text(json.dumps({"files": mfiles}))

    for M in AG.PRIMARY_HORIZONS:
        pred = pol_dev.predict(fixture_meta, fixture_feat, M)
        if pred["decision"] == "SWEEP_REQUIRED":
            r_pilot = {}
            for pk in SP.PILOT_KS:
                _, st = AG.encode_b1ra_archive(
                    dicts_by_k[pk], lengths_by_k[pk], primary_headers[(AG.PRIMARY_CHAIN_NAME, pk)]["header_bytes_raw"], fixture_docs
                )
                r_pilot[pk] = st["r_hat"]
            chosen_k, _ = SP.select_prefix_pilot_3pt(header_bytes_by_k, r_pilot, M, AG.PRIMARY_GRID)
        else:
            chosen_k = int(pred["predicted_K"])
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
        need(dec["all_ok"] is True and dec["complete_bytes"] == st["complete_bytes"], f"E2E fidelity/accounting failed at M={M}")
        e2e_results.append(
            {
                "M": M,
                "decision": pred["decision"],
                "chosen_K": chosen_k,
                "archive_bytes": dec["complete_bytes"],
                "fidelity": dec["fidelity"],
            }
        )

    return {
        "pass": True,
        "final_refit_n_cal_orgs": refit_dev["n_cal_orgs"],
        "strict_conformal_abstain_on_6_orgs": pred_strict["decision"],
        "high_uncertainty_abstain": pred_noisy["decision"],
        "synthetic_10_org_conformal_finite_upb90": round(100.0 * pred_conf10["upb_90_conformal"], 4),
        "end_to_end_shipping_runs": e2e_results,
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
            "gate_4_negative_control_fit_leakage_guard": gate_4_negative_control_leakage_guard(
                fit_corpus, lineages
            ),
            "gate_5_adversarial_synthetic_curves": gate_5_adversarial_synthetic_curves(
                header_bytes_by_k
            ),
            "gate_6_abstain_and_end_to_end_shipping": gate_6_abstain_and_end_to_end_shipping(
                fit_corpus, primary_headers, lineages, tmp
            ),
        }

    all_pass = all(g["pass"] is True for g in gates.values())
    report = {
        "schema": "gamma.bits-a1b.dev-gate.v1",
        "all_pass": all_pass,
        "wall_seconds": round(time.perf_counter() - t0, 3),
        "gates": gates,
    }
    return report


def main() -> int:
    report = run_all_dev_gates()
    out_path = HERE / "out" / "dev_gate_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    for name, g in report["gates"].items():
        status = "PASS" if g["pass"] else "FAIL"
        print(f"{status}  {name}")
    print(f"\nALL DEV GATES: {'PASS' if report['all_pass'] else 'FAIL'} ({report['wall_seconds']:.2f}s)")
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
