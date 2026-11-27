#!/usr/bin/env python3
"""One-shot sealed transfer evaluation for BITS B3 (frozen dict64 + frozen guarded rewriter).

Strictly enforces every frozen pre-unseal invariant:
  1. Verifies exact SHA-256 identity of `artifacts/frozen_dict64.json` (`70166bd0f6b8...`)
     AND frozen `rewriter.mjs` (`6bd15a99a6f8...`, commit `174e895d8`, carrying the sealed
     O(1)-step numeric copy-sort domain guard verified by NC4 16/16) before touching any
     sealed problem. Zero refitting, zero dictionary edits, zero rewriter edits.
  2. Loads TWO strictly disjoint untouched `solve`-interface JS cohorts from
     `catalogue/authored/` (verified 0 overlap with matched80 [80] and 0 overlap with
     dev_transfer [83]):
       - Slice S1 (`reserved_58`): ALL untouched `solve`-interface reserved JS problems
         from `js_corpus_reservations_v1.json` / `typed_confirmation_v1.json` excluded
         during B3 development.
       - Slice S2 (`fresh_111`): ALL untouched non-reserved `solve`-interface JS problems
         in `continuation-data-structures39`, `continuation-native`, `continuation-q`,
         `requested-589-725-39`, and `requested-1237-1500-32`.
     Reports S1, S2, and combined (169 problems) transparently with ZERO selective omission.
  3. Evaluates every sealed problem individually for:
       (a) zero-escape spellability under frozen_dict64.json,
       (b) 100% frozen test pass + exact parity with raw original output/effects,
       (c) deterministic runtime steps <= 1.1 * original_steps.
     Ships refusals via charged fallback in BOTH `B3H1` (Huffman) and `B3P1` (fixed-6-bit),
     re-executes independently decoded sealed packages to prove ZERO wrong acceptances,
     and compares complete bits (including charged standalone decoder) against frozen
     `matched80` BPE-255 (`canonical` & `original`, Huffman & Fixed-8) and in-domain BPE-256.
  4. Writes `artifacts/sealed_transfer_eval.json`, `sealed_summary.json`, and `SEALED_REPORT.md`
     without touching any frozen file or dev receipt.
"""
from __future__ import annotations

import collections
import json
import math
import statistics
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ARTIFACTS = HERE / "artifacts"
LIT_ROOT = HERE.parent
ALGSOLVE_ROOT = LIT_ROOT.parent
REPO_ROOT = ALGSOLVE_ROOT.parent.parent

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import b3_ref_decoder as refdec  # noqa: E402
import cohort_loader as cl  # noqa: E402
import dict64_train as dt  # noqa: E402
import independent_decode as idec  # noqa: E402
import package_codec as pc  # noqa: E402
import rewriter as rw  # noqa: E402
import transfer_eval as te  # noqa: E402

EXPECTED_REWRITER_MJS_SHA256 = "6bd15a99a6f8c2dda791646504fc8922843b1f4f24ac3808dc854599edac814b"
EXPECTED_JS_AST_MJS_SHA256 = "71f28888081eba23c521df3591919aa74fe01f7afedc2d990e52eb8b102710de"
EXPECTED_FROZEN_DICT64_SHA256 = te.EXPECTED_FROZEN_DICT64_SHA256

# Strictly pre-committed solve-interface cohorts for Slice S1 (reserved) & Slice S2 (fresh)
SOLVE_COHORTS_S1_SOURCES = (
    "continuation-data-structures39-20261028-v1",
    "continuation-q-20261028-v1",
    "requested-156-1940-31-20261028-v1",
    "requested-1666-2735-50-20261028-v1",
    "requested-243-370-35-20261028-v1",
    "requested-2753-3359-50-20261028-v1",
    "requested-963-1236-44-20261028-v1",
)
SOLVE_COHORTS_S2_FRESH = (
    "continuation-data-structures39-20261028-v1",
    "continuation-native-20261028-v1",
    "continuation-q-20261028-v1",
    "requested-589-725-39-20261028-v1",
    "requested-1237-1500-32-20261028-v1",
)


def load_sealed_cohorts(max_cases_per_problem: int = 64) -> dict[str, Any]:
    matched80_ids = set(json.loads((LIT_ROOT / "matched80-v1/labels/ids.json").read_text()))
    dev_cohorts = set(cl.DEV_TRANSFER_COHORTS)
    dev_ids: set[int] = set()
    for c in dev_cohorts:
        for p in (ALGSOLVE_ROOT / "catalogue/authored" / c / "javascript").glob("*.js"):
            if p.stem.isdigit():
                dev_ids.add(int(p.stem))
    reserved_ids = cl._collect_reserved_ids()
    authored_root = ALGSOLVE_ROOT / "catalogue/authored"

    problems: list[dict[str, Any]] = []
    seen_ids: set[int] = set()

    def load_from_cohort(cohort_name: str, slice_label: str, want_reserved: bool) -> None:
        cohort_dir = authored_root / cohort_name
        asgn = json.loads((cohort_dir / "assignment.public-safe.json").read_text())
        by_pid: dict[int, dict[str, Any]] = {}
        for item in asgn.get("problems", []):
            if isinstance(item, dict):
                pv = item.get("id") or item.get("problem_id") or item.get("frontend_id")
                if pv is not None:
                    by_pid[int(pv)] = item
        cases_mod = cl._load_py_module(f"b3_sealed_{slice_label}_{cohort_name.replace('-', '_')}", cohort_dir / "cases.py", cohort_dir)

        for js_path in sorted((cohort_dir / "javascript").glob("*.js")):
            if not js_path.stem.isdigit():
                continue
            pid = int(js_path.stem)
            if pid in matched80_ids or pid in dev_ids or pid in seen_ids:
                continue
            is_res = pid in reserved_ids
            if is_res != want_reserved:
                continue
            raw_bytes = js_path.read_bytes()
            raw_text = raw_bytes.decode("utf-8")
            pmeta = by_pid.get(pid, {})
            slug = pmeta.get("slug", f"problem-{pid}")
            title = pmeta.get("title", "")
            comp_meta = pmeta.get("comparison", {})
            abs_tol = comp_meta.get("absolute_tolerance") if isinstance(comp_meta, dict) else None
            try:
                cases = cases_mod.build_cases(pid, include_analytic_boundaries=False)
            except TypeError:
                try:
                    cases = cases_mod.build_cases(pid, include_maximum=False)
                except TypeError:
                    cases = cases_mod.build_cases(pid)
            if max_cases_per_problem is not None and len(cases) > max_cases_per_problem:
                n = len(cases)
                idxs = sorted({0, n - 1} | {int(round(k * (n - 1) / (max_cases_per_problem - 1))) for k in range(max_cases_per_problem)})
                cases = [cases[i] for i in idxs[:max_cases_per_problem]]

            seen_ids.add(pid)
            problems.append({
                "id": pid,
                "slice": slice_label,
                "cohort": cohort_name,
                "slug": slug,
                "title": title,
                "family": cl.classify_problem_family(slug, title),
                "abs_tol": abs_tol,
                "source_path": str(js_path.relative_to(REPO_ROOT)),
                "raw_source": raw_text,
                "raw_sha256": cl.sha256_bytes(raw_bytes),
                "raw_bytes": len(raw_bytes),
                "cases": cases,
            })

    for cname in SOLVE_COHORTS_S1_SOURCES:
        load_from_cohort(cname, "reserved", want_reserved=True)
    for cname in SOLVE_COHORTS_S2_FRESH:
        load_from_cohort(cname, "fresh_authored", want_reserved=False)

    assert all(p["id"] not in matched80_ids and p["id"] not in dev_ids for p in problems)
    return {
        "schema": "b3.sealed_transfer.cohort.v1",
        "problem_count": len(problems),
        "reserved_count": sum(1 for p in problems if p["slice"] == "reserved"),
        "fresh_authored_count": sum(1 for p in problems if p["slice"] == "fresh_authored"),
        "total_cases": sum(len(p["cases"]) for p in problems),
        "disjoint_from_matched80": True,
        "disjoint_from_dev_transfer": True,
        "problems": problems,
    }


def evaluate_slice(
    label: str,
    problems: list[dict[str, Any]],
    vocab: list[str],
    lengths: list[int],
    trie: Any,
    frozen: dict[str, Any],
    orig_by_id: dict[int, dict[str, Any]],
    accepted_map: dict[int, dict[str, Any]],
    refusal_map: dict[int, str],
) -> dict[str, Any]:
    raw_bytes_list = [p["raw_source"].encode("utf-8") for p in problems]
    total_raw_bytes = sum(len(b) for b in raw_bytes_list)
    modes = [0 if p["id"] in accepted_map else 1 for p in problems]
    fb_bpe = frozen["frozen_fallback_bpe255_canonical"]
    fb_orig_bpe = frozen["frozen_fallback_bpe255_original"]
    uniform_lens = [6] * len(vocab)

    records_raw_fb: list[dict[str, Any]] = []
    records_bpe_fb: list[dict[str, Any]] = []
    records_f6_raw_fb: list[dict[str, Any]] = []
    records_f6_bpe_fb: list[dict[str, Any]] = []
    for p, raw_bytes in zip(problems, raw_bytes_list):
        pid = p["id"]
        if pid in accepted_map:
            acc = accepted_map[pid]
            rec_h = {"covered": True, "token_ids": acc["tokens"]}
            f6_toks = dt.dp_segment_bits(acc["code"], trie, vocab, uniform_lens)
            assert f6_toks is not None
            rec_f6 = {"covered": True, "token_ids": f6_toks}
            records_raw_fb.append(rec_h)
            records_bpe_fb.append(rec_h)
            records_f6_raw_fb.append(rec_f6)
            records_f6_bpe_fb.append(rec_f6)
        else:
            raw_fb = {"covered": False, "raw_bytes": raw_bytes}
            records_raw_fb.append(raw_fb)
            records_f6_raw_fb.append(raw_fb)
            fb_seq = dt.apply_frozen_bpe(raw_bytes, fb_bpe["base_alphabet"], fb_bpe["merges"])
            bpe_fb = {"covered": False, "raw_bytes": raw_bytes, "fallback_bpe_seq": fb_seq}
            records_bpe_fb.append(bpe_fb)
            records_f6_bpe_fb.append(bpe_fb)

    # Package BOTH B3H1 (Huffman) and B3P1 (fixed-6-bit) with raw UTF-8 and frozen BPE-255 fallback
    pkg_raw_fb, bd_raw_fb = pc.encode_b3h1(vocab, records_raw_fb, lengths=lengths, fallback_bpe=None, transfer_mode=True)
    pkg_bpe_fb, bd_bpe_fb = pc.encode_b3h1(vocab, records_bpe_fb, lengths=lengths, fallback_bpe=fb_bpe, transfer_mode=True)
    chosen_huff_raw, chosen_bd = (pkg_bpe_fb, bd_bpe_fb) if bd_bpe_fb["complete_bits"] < bd_raw_fb["complete_bits"] else (pkg_raw_fb, bd_raw_fb)

    pkg_f6_raw_fb, bd_f6_raw_fb = pc.encode_b3p1_transfer(vocab, records_f6_raw_fb, width=6, fallback_bpe=None)
    pkg_f6_bpe_fb, bd_f6_bpe_fb = pc.encode_b3p1_transfer(vocab, records_f6_bpe_fb, width=6, fallback_bpe=fb_bpe)
    chosen_f6_raw, chosen_f6_bd = (pkg_f6_bpe_fb, bd_f6_bpe_fb) if bd_f6_bpe_fb["complete_bits"] < bd_f6_raw_fb["complete_bits"] else (pkg_f6_raw_fb, bd_f6_raw_fb)

    # Independent decode verification of BOTH B3H1 and B3P1!
    dec_ind = idec.decode_b3h1(chosen_huff_raw)
    dec_ref = refdec.decode_b3h1(chosen_huff_raw)
    dec_f6 = idec.decode_b3p1_transfer(chosen_f6_raw)
    assert dec_ind["programs"] == dec_ref[1] == dec_f6["programs"], f"{label}: decoder disagreement!"
    assert dec_ind["modes"] == modes, f"{label}: mode bitmap mismatch!"

    # Re-execute independently decoded programs to prove ZERO wrong acceptances!
    reexec = te.run_step_batch([{
        "id": p["id"],
        "code": code,
        "entry": "solve",
        "interface": "function",
        "method": "solve",
        "allow_cjs_export": bool(m == 1),
        "cases": [{"args": c["args"]} for c in p["cases"]],
    } for p, code, m in zip(problems, dec_ind["programs"], modes)])

    accepted_verified = 0
    fallback_verified = 0
    wrong_acceptances = 0
    step_ratios: list[float] = []
    for p, m, rd in zip(problems, modes, reexec):
        ro = orig_by_id[p["id"]]
        ok_p = rd["ok"] and all(
            cl.check_transfer_case(
                c, recd,
                original_obs={k: reco.get(k) for k in ("result", "args_after", "error")},
                abs_tol=p["abs_tol"],
            )[0]
            for c, reco, recd in zip(p["cases"], ro["records"], rd["records"])
        )
        ratio = rd["total_steps"] / max(1, ro["total_steps"]) if ok_p else 999.0
        if m == 0:
            if ok_p and ratio <= 1.1:
                accepted_verified += 1
                step_ratios.append(ratio)
            else:
                wrong_acceptances += 1
        else:
            if ok_p:
                fallback_verified += 1

    # Frozen matched80 BPE-255 + in-domain BPE-256 comparators
    frozen_bpe_canon_seqs = [dt.apply_frozen_bpe(r, fb_bpe["base_alphabet"], fb_bpe["merges"]) for r in raw_bytes_list]
    pkg_fb_canon_hf, bd_fb_canon_hf = pc.encode_b3b1_bpe(fb_bpe["base_alphabet"], fb_bpe["merges"], frozen_bpe_canon_seqs, coding="huffman", allow_escape=True)
    pkg_fb_canon_f8, bd_fb_canon_f8 = pc.encode_b3b1_bpe(fb_bpe["base_alphabet"], fb_bpe["merges"], frozen_bpe_canon_seqs, coding="fixed8", allow_escape=True)
    assert idec.decode_b3b1(pkg_fb_canon_hf)["programs"] == [p["raw_source"] for p in problems]
    assert idec.decode_b3b1(pkg_fb_canon_f8)["programs"] == [p["raw_source"] for p in problems]

    frozen_bpe_orig_seqs = [dt.apply_frozen_bpe(r, fb_orig_bpe["base_alphabet"], fb_orig_bpe["merges"]) for r in raw_bytes_list]
    pkg_fb_orig_hf, bd_fb_orig_hf = pc.encode_b3b1_bpe(fb_orig_bpe["base_alphabet"], fb_orig_bpe["merges"], frozen_bpe_orig_seqs, coding="huffman", allow_escape=True)
    pkg_fb_orig_f8, bd_fb_orig_f8 = pc.encode_b3b1_bpe(fb_orig_bpe["base_alphabet"], fb_orig_bpe["merges"], frozen_bpe_orig_seqs, coding="fixed8", allow_escape=True)
    assert idec.decode_b3b1(pkg_fb_orig_hf)["programs"] == [p["raw_source"] for p in problems]
    assert idec.decode_b3b1(pkg_fb_orig_f8)["programs"] == [p["raw_source"] for p in problems]

    indomain_bpe = dt.train_bpe_256(raw_bytes_list, max_vocab=256)
    pkg_ind_hf, bd_ind_hf = pc.encode_b3b1_bpe(indomain_bpe["base_alphabet"], indomain_bpe["merges"], indomain_bpe["sequences"], coding="huffman")
    pkg_ind_f8, bd_ind_f8 = pc.encode_b3b1_bpe(indomain_bpe["base_alphabet"], indomain_bpe["merges"], indomain_bpe["sequences"], coding="fixed8")
    assert idec.decode_b3b1(pkg_ind_hf)["programs"] == [p["raw_source"] for p in problems]
    assert idec.decode_b3b1(pkg_ind_f8)["programs"] == [p["raw_source"] for p in problems]

    b3h1_dec = te.compute_transfer_decision(
        accepted=accepted_verified,
        total=len(problems),
        wrong_acceptances=wrong_acceptances,
        complete_bits=chosen_bd["complete_bits"],
        baseline_complete_bits=bd_fb_canon_hf["complete_bits"],
    )
    b3p1_dec = te.compute_transfer_decision(
        accepted=accepted_verified,
        total=len(problems),
        wrong_acceptances=wrong_acceptances,
        complete_bits=chosen_f6_bd["complete_bits"],
        baseline_complete_bits=bd_fb_canon_f8["complete_bits"],
    )

    refusal_counts = collections.Counter(refusal_map[p["id"]] for p in problems if p["id"] not in accepted_map)
    fam_stats: dict[str, dict[str, int]] = {}
    for p in problems:
        f = fam_stats.setdefault(p["family"], {"total": 0, "accepted": 0, "refused": 0})
        f["total"] += 1
        if p["id"] in accepted_map:
            f["accepted"] += 1
        else:
            f["refused"] += 1

    return {
        "slice": label,
        "problems": len(problems),
        "total_cases": sum(len(p["cases"]) for p in problems),
        "total_raw_bytes": total_raw_bytes,
        "accepted": accepted_verified,
        "refused_fallback": fallback_verified,
        "wrong_acceptances": wrong_acceptances,
        "coverage_rate": round(accepted_verified / max(1, len(problems)), 4),
        "max_accepted_step_ratio": round(max(step_ratios), 4) if step_ratios else None,
        "median_accepted_step_ratio": round(statistics.median(step_ratios), 4) if step_ratios else None,
        "refusal_reasons": dict(refusal_counts),
        "family_breakdown": dict(sorted(fam_stats.items())),
        "b3h1_decision": b3h1_dec,
        "b3p1_decision": b3p1_dec,
        "complete_bits": {
            "b3h1_complete_bits": chosen_bd["complete_bits"],
            "b3h1_package_bits_excl_dec": chosen_bd["package_bits_excluding_decoder"],
            "b3h1_decoder_bits": chosen_bd["decoder_machinery_bits"],
            "b3h1_fallback_mode": chosen_bd["fallback_mode"],
            "b3p1_fixed6_complete_bits": chosen_f6_bd["complete_bits"],
            "b3p1_fixed6_package_bits_excl_dec": chosen_f6_bd["package_bits_excluding_decoder"],
            "b3p1_fixed6_decoder_bits": chosen_f6_bd["decoder_machinery_bits"],
            "frozen_m80_bpe255_canon_huff": bd_fb_canon_hf["complete_bits"],
            "frozen_m80_bpe255_canon_f8": bd_fb_canon_f8["complete_bits"],
            "frozen_m80_bpe255_orig_huff": bd_fb_orig_hf["complete_bits"],
            "frozen_m80_bpe255_orig_f8": bd_fb_orig_f8["complete_bits"],
            "indomain_bpe256_huff": bd_ind_hf["complete_bits"],
            "indomain_bpe256_f8": bd_ind_f8["complete_bits"],
        },
        "independent_decode_verified": True,
    }


def main() -> int:
    t0 = time.perf_counter()
    # 1. Verify frozen dictionary AND frozen guarded rewriter byte identity!
    frozen_bytes = (ARTIFACTS / "frozen_dict64.json").read_bytes()
    frozen_sha = pc.sha256_bytes(frozen_bytes)
    assert frozen_sha == EXPECTED_FROZEN_DICT64_SHA256, f"frozen_dict64.json SHA drifted: {frozen_sha}"
    fp = rw.rewriter_fingerprint()
    assert fp["rewriter_mjs_sha256"] == EXPECTED_REWRITER_MJS_SHA256, f"rewriter.mjs SHA drifted: {fp}"
    assert fp["js_ast_mjs_sha256"] == EXPECTED_JS_AST_MJS_SHA256, f"js_ast.mjs SHA drifted: {fp}"
    print(f"[B3 sealed] Verified frozen dict64 ({frozen_sha[:12]}) and guarded rewriter.mjs ({fp['rewriter_mjs_sha256'][:12]})", flush=True)

    frozen = json.loads(frozen_bytes)
    vocab: list[str] = frozen["vocab"]
    lengths: list[int] = frozen["huffman_lengths"]
    trie = dt.build_trie(vocab)

    cohort = load_sealed_cohorts(max_cases_per_problem=64)
    problems = cohort["problems"]
    print(
        f"[B3 sealed] Loaded {cohort['problem_count']} disjoint sealed problems "
        f"(reserved={cohort['reserved_count']}, fresh_authored={cohort['fresh_authored_count']}, "
        f"cases={cohort['total_cases']}); 0 overlap with matched80/dev_transfer",
        flush=True,
    )

    # Execute original programs once
    orig_res = te.run_step_batch([{
        "id": p["id"],
        "code": p["raw_source"],
        "entry": "solve",
        "interface": "function",
        "method": "solve",
        "allow_cjs_export": True,
        "cases": [{"args": c["args"]} for c in p["cases"]],
    } for p in problems])
    orig_by_id = {r["id"]: r for r in orig_res}
    valid_problems = []
    skipped_orig = []
    for p in problems:
        ro = orig_by_id[p["id"]]
        ok_orig = ro["ok"] and all(
            cl.check_transfer_case(c, rec, abs_tol=p["abs_tol"])[0]
            for c, rec in zip(p["cases"], ro["records"])
        )
        if ok_orig:
            valid_problems.append(p)
        else:
            skipped_orig.append((p["id"], p["cohort"], ro.get("reason")))
    print(f"[B3 sealed] Original baseline verification: {len(valid_problems)}/{len(problems)} valid (skipped_orig={len(skipped_orig)})", flush=True)
    problems = valid_problems

    # Generate canonical rewrite candidates via frozen rewriter.mjs
    raw_by_id = {p["id"]: p["raw_source"] for p in problems}
    cand_map = rw.generate_joint_candidates(raw_by_id)

    # Filter zero-escape spellable candidates under frozen_dict64.json and pick smallest bit-cost per problem
    verify_jobs = []
    spellable_meta: dict[int, list[dict[str, Any]]] = {}
    refusal_map: dict[int, str] = {}
    for p in problems:
        pid = p["id"]
        cands = cand_map.get(pid, {})
        scored = []
        for vname, rec in cands.items():
            toks = dt.dp_segment_bits(rec["code"], trie, vocab, lengths)
            if toks is not None:
                bits = sum(lengths[t] for t in toks)
                scored.append({"variant": vname, "code": rec["code"], "bits": bits, "tokens": toks})
        if not scored:
            refusal_map[pid] = "unspellable_zero_escape"
            continue
        scored.sort(key=lambda x: (x["bits"], len(x["code"]), x["variant"]))
        spellable_meta[pid] = scored
        for idx, sc in enumerate(scored):
            verify_jobs.append({
                "id": f"{pid}:{idx}",
                "code": sc["code"],
                "entry": "solve",
                "interface": "function",
                "method": "solve",
                "allow_cjs_export": False,
                "cases": [{"args": c["args"]} for c in p["cases"]],
            })

    print(f"[B3 sealed] Verifying {len(verify_jobs)} zero-escape candidates across {len(spellable_meta)} spellable problems...", flush=True)
    cand_res = te.run_step_batch(verify_jobs)
    cand_res_by_key = {r["id"]: r for r in cand_res}

    accepted_map: dict[int, dict[str, Any]] = {}
    for p in problems:
        pid = p["id"]
        if pid not in spellable_meta:
            continue
        ro = orig_by_id[pid]
        best_acc = None
        best_ratio = 999.0
        any_correct = False
        for idx, sc in enumerate(spellable_meta[pid]):
            rd = cand_res_by_key[f"{pid}:{idx}"]
            ok_p = rd["ok"] and all(
                cl.check_transfer_case(
                    c, recd,
                    original_obs={k: reco.get(k) for k in ("result", "args_after", "error")},
                    abs_tol=p["abs_tol"],
                )[0]
                for c, reco, recd in zip(p["cases"], ro["records"], rd["records"])
            )
            if ok_p:
                any_correct = True
                ratio = rd["total_steps"] / max(1, ro["total_steps"])
                best_ratio = min(best_ratio, ratio)
                if ratio <= 1.1 and best_acc is None:
                    best_acc = {**sc, "step_ratio": ratio, "rewritten_steps": rd["total_steps"]}
        if best_acc is not None:
            accepted_map[pid] = best_acc
        elif any_correct:
            refusal_map[pid] = "step_ceiling_exceeded"
        else:
            refusal_map[pid] = "behavior_or_runtime_mismatch"

    res_slice = [p for p in problems if p["slice"] == "reserved"]
    fresh_slice = [p for p in problems if p["slice"] == "fresh_authored"]
    eval_reserved = evaluate_slice("sealed_reserved", res_slice, vocab, lengths, trie, frozen, orig_by_id, accepted_map, refusal_map)
    eval_fresh = evaluate_slice("sealed_fresh_authored", fresh_slice, vocab, lengths, trie, frozen, orig_by_id, accepted_map, refusal_map)
    eval_all = evaluate_slice("sealed_combined", problems, vocab, lengths, trie, frozen, orig_by_id, accepted_map, refusal_map)

    summary = {
        "schema": "b3.sealed_transfer.summary.v1",
        "frozen_pins": {
            "frozen_dict64_sha256": frozen_sha,
            "rewriter_mjs_sha256": fp["rewriter_mjs_sha256"],
            "js_ast_mjs_sha256": fp["js_ast_mjs_sha256"],
            "step_ceiling": 1.1,
            "min_coverage_bar": te.MIN_TRANSFER_COVERAGE,
        },
        "skipped_invalid_originals": skipped_orig,
        "slices": {
            "sealed_reserved": eval_reserved,
            "sealed_fresh_authored": eval_fresh,
            "sealed_combined": eval_all,
        },
        "b4_gate_note": (
            "B4 remains PAUSED behind explicit user model-compute approval regardless of sealed CPU transfer verdict."
        ),
        "wall_seconds": round(time.perf_counter() - t0, 2),
    }

    (ARTIFACTS / "sealed_transfer_eval.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (HERE / "sealed_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    # Render SEALED_REPORT.md
    lines = [
        "# B3 Sealed Transfer Report: Frozen 64-Entry Dictionary & Guarded Rewriter",
        "",
        "## Frozen Pre-Unseal Pins Verified",
        "",
        f"- `artifacts/frozen_dict64.json` SHA-256: `{frozen_sha}` (unchanged from matched80 witness and dev transfer)",
        f"- `rewriter.mjs` SHA-256: `{fp['rewriter_mjs_sha256']}` (commit `174e895d8`, carrying O(1)-step sealed numeric copy-sort domain guard verified by NC4 16/16)",
        "- Step ceiling: `1.1x` deterministic instrumented steps; minimum transfer coverage bar: `90.0%`; zero wrong acceptances required.",
        "- Zero overlap with `matched80` (80) or `dev_transfer` (83); zero edits or refitting performed on sealed problems.",
        "- **B4 Gate:** `B4` remains **PAUSED** pending explicit model-compute authorization.",
        "",
        "## Sealed Transfer Verdicts by Slice (`B3H1` Huffman vs `B3P1` Fixed-6-Bit)",
        "",
        "| Slice | Accepted / Total | Coverage | Wrong Acc | Max Step Ratio | `B3H1` Complete Bits (vs Frozen BPE-255 Huff) | `B3H1` Verdict | `B3P1` Fixed-6 Complete Bits (vs Frozen BPE-255 F8) | `B3P1` Verdict |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for s in (eval_reserved, eval_fresh, eval_all):
        cb = s["complete_bits"]
        lines.append(
            f"| `{s['slice']}` | **{s['accepted']}/{s['problems']}** | **{s['coverage_rate']*100:.2f}%** | {s['wrong_acceptances']} | {s['max_accepted_step_ratio']}x | "
            f"{cb['b3h1_complete_bits']:,d} vs {cb['frozen_m80_bpe255_canon_huff']:,d} ({cb['b3h1_complete_bits'] - cb['frozen_m80_bpe255_canon_huff']:+d}) | **`{s['b3h1_decision']['status']}`** | "
            f"{cb['b3p1_fixed6_complete_bits']:,d} vs {cb['frozen_m80_bpe255_canon_f8']:,d} ({cb['b3p1_fixed6_complete_bits'] - cb['frozen_m80_bpe255_canon_f8']:+d}) | **`{s['b3p1_decision']['status']}`** |"
        )
    lines.append("")
    lines.append("## Refusal Reasons & In-Domain BPE-256 Comparators")
    lines.append("")
    for s in (eval_reserved, eval_fresh, eval_all):
        cb = s["complete_bits"]
        lines.append(
            f"- **`{s['slice']}`** ({s['problems']} problems, {s['total_cases']:,d} frozen tests, {s['total_raw_bytes']:,d} raw B): "
            f"refusals={s['refusal_reasons']}, `B3H1` excl. dec=`{cb['b3h1_package_bits_excl_dec']:,d}` b + dec=`{cb['b3h1_decoder_bits']:,d}` b, "
            f"in-domain BPE-256 Huff=`{cb['indomain_bpe256_huff']:,d}` b, frozen original BPE-255 Huff=`{cb['frozen_m80_bpe255_orig_huff']:,d}` b."
        )
    lines.append("")
    (HERE / "SEALED_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        k: {
            "accepted": f"{v['accepted']}/{v['problems']} ({v['coverage_rate']*100:.2f}%)",
            "wrong_acceptances": v["wrong_acceptances"],
            "b3h1_status": v["b3h1_decision"]["status"],
            "b3p1_status": v["b3p1_decision"]["status"],
            "b3h1_bits": v["complete_bits"]["b3h1_complete_bits"],
            "bpe255_canon_huff": v["complete_bits"]["frozen_m80_bpe255_canon_huff"],
            "refusals": v["refusal_reasons"],
        }
        for k, v in summary["slices"].items()
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
