"""Frozen dev-transfer evaluation on disjoint spent JS problems with charged raw fallback.

Strict protocol:
- Loads ONLY the frozen rewriter and frozen <=64-entry dictionary + frozen Huffman lengths
  from `artifacts/frozen_dict64.json` (zero refitting, zero dictionary edits, zero tuning).
- Evaluates every separate disjoint spent JS transfer problem individually for:
    (a) zero-escape spellability under the frozen <=64-entry dictionary,
    (b) 100% frozen behavior test pass + exact parity with raw original output/effects,
    (c) deterministic runtime steps <= 1.1 * original_steps.
- Every refusal is shipped via the charged raw fallback (explicitly charging selector
  bitmap + any required fallback tables + fallback payload + standalone decoder bytes).
- Verifies ZERO wrong acceptances by re-executing the independently decoded transfer package.
- Reports witness and dev transfer as completely separate decisions, plus full diagnostics:
  rewrite yield, unspellable syntax and literals, runtime tails, dictionary utilization,
  and every uncovered problem family.
"""
from __future__ import annotations

import collections
import json
import math
import re
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import b3_ref_decoder as refdec
import cohort_loader as cl
import dict64_train as dt
import independent_decode as idec
import package_codec as pc
import rewriter as rw

HERE = Path(__file__).resolve().parent
ARTIFACTS = HERE / "artifacts"

MIN_TRANSFER_COVERAGE = 0.90
EXPECTED_FROZEN_DICT64_SHA256 = "70166bd0f6b84af31ab9bc5479cab5bae50b6fe3bb000fdeca85b8e0bb87c135"

PASS1_HISTORICAL_RECEIPT: dict[str, Any] = {
    "pass_name": "pass1_initial_rewriter",
    "rewriter_mjs_sha256": "3dd7d6e114ee2a9870dddde4aa7d62b649a1d06bd7936da00923e8c68337d17f",
    "frozen_dict64_sha256": EXPECTED_FROZEN_DICT64_SHA256,
    "step_ceiling": 1.1,
    "accepted_programs": 72,
    "refused_programs": 11,
    "total_programs": 83,
    "coverage_rate": 0.8675,
    "wrong_acceptances": 0,
    "b3h1_complete_bits": 165496,
    "b3h1_package_bits_excluding_decoder": 149888,
    "frozen_matched80_bpe255_canonical_huffman_bits": 219656,
    "refusal_reasons": {
        "step_ceiling_exceeded": 9,
        "unspellable_zero_escape": 2,
    },
    "status": "FAIL",
    "note": "Initial Pass-1 transfer achieved 72/83 (86.75%) < 90.0% minimum bar (75/83); corrected from erroneous PASS label to FAIL under programmatic contract.",
}


def compute_transfer_decision(
    accepted: int,
    total: int,
    wrong_acceptances: int,
    complete_bits: int,
    baseline_complete_bits: int,
    min_coverage: float = MIN_TRANSFER_COVERAGE,
) -> dict[str, Any]:
    """Programmatic dev transfer decision contract (strict PASS/FAIL, never hand-labeled)."""
    cov = accepted / max(1, total)
    coverage_ok = cov >= min_coverage
    zero_wrong_ok = wrong_acceptances == 0
    bits_ok = complete_bits <= baseline_complete_bits
    passed = coverage_ok and zero_wrong_ok and bits_ok
    return {
        "status": "PASS" if passed else "FAIL",
        "min_coverage_threshold": min_coverage,
        "min_covered_programs_required": math.ceil(min_coverage * total),
        "covered_programs": accepted,
        "refused_programs": total - accepted,
        "total_programs": total,
        "coverage_rate": round(cov, 4),
        "coverage_meets_90pct_bar": coverage_ok,
        "zero_wrong_acceptances": zero_wrong_ok,
        "complete_bits": complete_bits,
        "baseline_complete_bits": baseline_complete_bits,
        "complete_bits_le_baseline": bits_ok,
    }


def peak_rss_bytes() -> int:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss if sys.platform == "darwin" else rss * 1024


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return s[max(0, math.ceil(0.95 * len(s)) - 1)]


def run_step_batch(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["node", str(HERE / "step_verifier.mjs")],
        input=json.dumps({"mode": "batch", "jobs": jobs}),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)["results"]


def diagnose_unspellable(code: str, vocab: list[str]) -> dict[str, Any]:
    """Identify the exact characters and syntax/literal tokens that prevented zero-escape spelling."""
    trie = dt.build_trie(vocab)
    n = len(code)
    # Forward reachability DP to locate exact blocking offsets
    reach = [False] * (n + 1)
    reach[0] = True
    for i in range(n):
        if not reach[i]:
            continue
        node = trie
        j = i
        while j < n:
            nxt = node.children.get(code[j])
            if nxt is None:
                break
            node = nxt
            j += 1
            if node.entry_id >= 0:
                reach[j] = True
    farthest = max((i for i, ok in enumerate(reach) if ok), default=0)
    snippet = code[max(0, farthest - 12) : min(n, farthest + 24)]
    # Also find all characters absent from single-char vocab that appear outside matching multi-char entries
    vocab_singles = {e for e in vocab if len(e) == 1}
    vocab_multis = [e for e in vocab if len(e) >= 2]
    uncovered_positions = []
    for i, ch in enumerate(code):
        if ch in vocab_singles:
            continue
        # Check if any multi-char entry covers position i
        covered = False
        for m in vocab_multis:
            ml = len(m)
            for st in range(max(0, i - ml + 1), min(i + 1, n - ml + 1)):
                if code.startswith(m, st):
                    covered = True
                    break
            if covered:
                break
        if not covered:
            uncovered_positions.append((i, ch, code[max(0, i - 6) : min(n, i + 12)]))
    # Group uncovered words/tokens
    blocking_tokens: collections.Counter[str] = collections.Counter()
    seen_spans: set[tuple[int, int]] = set()
    for i, ch, _ in uncovered_positions:
        # Expand to surrounding word/operator token
        if ch.isalpha():
            l = i
            while l > 0 and (code[l - 1].isalpha() or code[l - 1] == "."):
                l -= 1
            r = i + 1
            while r < n and (code[r].isalpha() or code[r] in "(;"):
                r += 1
            if (l, r) not in seen_spans:
                seen_spans.add((l, r))
                blocking_tokens[code[l:r]] += 1
        else:
            blocking_tokens[ch] += 1
    return {
        "farthest_reachable_offset": farthest,
        "code_length": n,
        "first_blocking_snippet": snippet,
        "blocking_tokens": dict(blocking_tokens.most_common(10)),
    }


def compute_horizon(
    fixed_overhead_bits: int,
    stream_bits_b3: int,
    baseline_total_bits: int,
    n_programs: int,
    total_raw_bytes: int,
) -> dict[str, Any]:
    marginal_b3 = stream_bits_b3 / max(1, n_programs)
    baseline_per = baseline_total_bits / max(1, n_programs)
    savings = baseline_per - marginal_b3
    if savings > 0:
        h_progs = math.ceil(fixed_overhead_bits / savings)
        h_bytes = round(h_progs * (total_raw_bytes / max(1, n_programs)), 1)
    else:
        h_progs = None
        h_bytes = None
    return {
        "fixed_overhead_bits": fixed_overhead_bits,
        "b3_marginal_bits_per_program": round(marginal_b3, 2),
        "baseline_bits_per_program": round(baseline_per, 2),
        "marginal_savings_bits_per_program": round(savings, 2),
        "break_even_programs": h_progs,
        "break_even_raw_bytes": h_bytes,
    }


def run_transfer_eval(max_cases_per_problem: int = 64) -> dict[str, Any]:
    t0 = time.monotonic()
    frozen_path = ARTIFACTS / "frozen_dict64.json"
    assert frozen_path.exists(), "Run eval_dev.py first to freeze matched80 dictionary!"
    frozen_bytes = frozen_path.read_bytes()
    frozen_sha256 = pc.sha256_bytes(frozen_bytes)
    assert frozen_sha256 == EXPECTED_FROZEN_DICT64_SHA256, (
        f"artifacts/frozen_dict64.json SHA-256 drifted: got {frozen_sha256}, expected {EXPECTED_FROZEN_DICT64_SHA256}"
    )
    frozen = json.loads(frozen_bytes)
    current_rewriter_fp = rw.rewriter_fingerprint()
    m80_eval_path = ARTIFACTS / "matched80_eval.json"
    if m80_eval_path.exists():
        m80_eval_data = json.loads(m80_eval_path.read_text())
        if "rewriter_fingerprint" in m80_eval_data:
            assert m80_eval_data["rewriter_fingerprint"] == current_rewriter_fp, (
                "Rewriter fingerprint mismatch between matched80_eval.json and transfer_eval.py!"
            )

    vocab: list[str] = frozen["vocab"]
    lengths: list[int] = frozen["huffman_lengths"]
    assert len(vocab) <= 64 and len(lengths) == len(vocab) + 1
    trie = dt.build_trie(vocab)

    # Load separate disjoint spent JS dev transfer problems
    dt_cohort = cl.load_dev_transfer_cohort(max_cases_per_problem=max_cases_per_problem)
    problems = dt_cohort["problems"]
    pids = [p["id"] for p in problems]
    raw_by_id = {p["id"]: p["raw_source"] for p in problems}
    prob_by_id = {p["id"]: p for p in problems}

    # 1. Execute raw original transfer programs via step_verifier.mjs (baseline steps + parity)
    t_orig0 = time.monotonic()
    orig_jobs = [{
        "id": p["id"],
        "code": p["raw_source"],
        "entry": "solve",
        "interface": "function",
        "method": "solve",
        "allow_cjs_export": True,
        "cases": [{"args": c["args"]} for c in p["cases"]],
    } for p in problems]
    orig_results = run_step_batch(orig_jobs)
    orig_by_pid: dict[int, dict[str, Any]] = {}
    for p, ro in zip(problems, orig_results):
        assert ro["ok"], f"Raw dev transfer #{p['id']} failed execution: {ro}"
        for idx, (case, rec) in enumerate(zip(p["cases"], ro["records"])):
            ok, msg = cl.check_transfer_case(case, rec, abs_tol=p["abs_tol"])
            assert ok, f"Raw dev transfer #{p['id']} case {idx} failed: {msg}"
        orig_by_pid[p["id"]] = ro
    orig_verify_seconds = time.monotonic() - t_orig0

    # 2. Apply FROZEN canonical rewriter (both single fixed canonical AND frozen joint-variant set)
    #    using ZERO dictionary refitting or transfer feedback!
    t_rw0 = time.monotonic()
    fixed_rw = rw.rewrite_fixed(raw_by_id, opts=frozen["fixed_canonical_opts"])
    all_cands = rw.generate_joint_candidates(raw_by_id)
    rewrite_seconds = time.monotonic() - t_rw0

    # 3. For each transfer problem, evaluate zero-escape spellability under FROZEN dict64
    #    and run frozen behavior tests + <=1.1x step check on every spellable candidate!
    t_sel0 = time.monotonic()
    fixed_spellable_count = 0
    candidate_to_verify: list[dict[str, Any]] = []
    cand_meta: dict[int, dict[str, Any]] = {}
    unspellable_diagnostics: list[dict[str, Any]] = []

    for p in problems:
        pid = p["id"]
        # Check single fixed canonical first (for diagnostic comparison)
        fx = fixed_rw[pid]
        fx_seg = dt.dp_segment_bits(fx["code"], trie, vocab, lengths) if fx.get("ok") else None
        if fx_seg is not None:
            fixed_spellable_count += 1

        # Pick lowest Huffman-bit zero-escape spelling among frozen legal rewrite variants
        best_choice = None
        for vname, info in sorted(all_cands.get(pid, {}).items()):
            seg = dt.dp_segment_bits(info["code"], trie, vocab, lengths)
            if seg is not None:
                bit_cost = sum(lengths[t] for t in seg)
                if best_choice is None or (bit_cost, len(seg), vname) < (best_choice[0], best_choice[1], best_choice[2]):
                    best_choice = (bit_cost, len(seg), vname, info["code"], seg)

        if best_choice is None:
            diag = (
                diagnose_unspellable(fx["code"], vocab)
                if fx.get("ok")
                else {"rewrite_error": fx.get("error", "unknown")}
            )
            unspellable_diagnostics.append({
                "id": pid,
                "slug": p["slug"],
                "family": p["family"],
                **diag,
            })
            cand_meta[pid] = {
                "spellable": False,
                "fixed_spellable": False,
                "refusal_reason": "unspellable_zero_escape" if fx.get("ok") else "rewrite_parse_error",
                "diagnostic": diag,
            }
        else:
            bit_cost, ntok, vname, code, seg = best_choice
            f6_seg = dt.dp_segment(code, trie, vocab)
            assert f6_seg is not None
            cand_meta[pid] = {
                "spellable": True,
                "fixed_spellable": fx_seg is not None,
                "chosen_variant": vname,
                "code": code,
                "token_ids": seg,
                "fixed6_token_ids": f6_seg,
                "coded_bits": bit_cost + lengths[len(vocab)],
            }
            candidate_to_verify.append({
                "id": pid,
                "code": code,
                "entry": "solve",
                "interface": "function",
                "method": "solve",
                "cases": [{"args": c["args"]} for c in p["cases"]],
            })
    selection_seconds = time.monotonic() - t_sel0

    # 4. Run deterministic step_verifier.mjs on EVERY spellable candidate
    t_ver0 = time.monotonic()
    ver_results = run_step_batch(candidate_to_verify) if candidate_to_verify else []
    ver_by_pid = {r["id"]: r for r in ver_results}
    verify_seconds = time.monotonic() - t_ver0

    # 5. Individual acceptance / refusal decisions (strict: tests 100% AND parity AND steps <= 1.1x!)
    per_problem: list[dict[str, Any]] = []
    records_raw_fb: list[dict[str, Any]] = []
    records_bpe_fb: list[dict[str, Any]] = []
    records_f6_raw_fb: list[dict[str, Any]] = []
    records_f6_bpe_fb: list[dict[str, Any]] = []
    fb_bpe = frozen["frozen_fallback_bpe255_canonical"]

    accepted_step_ratios: list[float] = []
    family_stats: dict[str, dict[str, int]] = collections.defaultdict(lambda: {"total": 0, "accepted": 0, "refused": 0})
    refusal_reasons: collections.Counter[str] = collections.Counter()
    blocking_token_totals: collections.Counter[str] = collections.Counter()
    used_transfer_ids: set[int] = set()
    accepted_texts_by_id: dict[int, str] = {}

    for p in problems:
        pid = p["id"]
        fam = p["family"]
        family_stats[fam]["total"] += 1
        meta = cand_meta[pid]
        raw_bytes = p["raw_source"].encode("utf-8")
        ro = orig_by_pid[pid]

        accepted = False
        reason = "ok"
        cases_passed = 0
        rw_steps = None
        step_ratio = None

        if not meta["spellable"]:
            reason = meta["refusal_reason"]
            for bt, cnt in meta.get("diagnostic", {}).get("blocking_tokens", {}).items():
                blocking_token_totals[bt] += cnt
        else:
            rv = ver_by_pid[pid]
            if not rv["ok"]:
                reason = f"exec_fail:{rv['reason']}"
            else:
                for idx, (case, reco, rec) in enumerate(zip(p["cases"], ro["records"], rv["records"])):
                    oo = {k: reco.get(k) for k in ("result", "args_after", "error")}
                    ok, _ = cl.check_transfer_case(case, rec, original_obs=oo, abs_tol=p["abs_tol"])
                    if ok:
                        cases_passed += 1
                rw_steps = rv["total_steps"]
                step_ratio = rw_steps / max(1, ro["total_steps"])
                if cases_passed != len(p["cases"]):
                    reason = f"behavior_mismatch:{cases_passed}/{len(p['cases'])}"
                elif step_ratio > 1.1:
                    reason = f"step_ceiling_exceeded:{step_ratio:.4f}"
                else:
                    accepted = True

        if accepted:
            family_stats[fam]["accepted"] += 1
            accepted_step_ratios.append(step_ratio)
            used_transfer_ids.update(meta["token_ids"])
            accepted_texts_by_id[pid] = meta["code"]
            rec_entry = {"covered": True, "token_ids": meta["token_ids"]}
            records_raw_fb.append(rec_entry)
            records_bpe_fb.append(rec_entry)
            f6_entry = {"covered": True, "token_ids": meta["fixed6_token_ids"]}
            records_f6_raw_fb.append(f6_entry)
            records_f6_bpe_fb.append(f6_entry)
        else:
            family_stats[fam]["refused"] += 1
            refusal_reasons[reason.split(":")[0]] += 1
            raw_fb_rec = {"covered": False, "raw_bytes": raw_bytes}
            records_raw_fb.append(raw_fb_rec)
            records_f6_raw_fb.append(raw_fb_rec)
            fb_seq = dt.apply_frozen_bpe(raw_bytes, fb_bpe["base_alphabet"], fb_bpe["merges"])
            bpe_fb_rec = {"covered": False, "raw_bytes": raw_bytes, "fallback_bpe_seq": fb_seq}
            records_bpe_fb.append(bpe_fb_rec)
            records_f6_bpe_fb.append(bpe_fb_rec)

        per_problem.append({
            "id": pid,
            "slug": p["slug"],
            "cohort": p["cohort"],
            "family": fam,
            "raw_bytes": len(raw_bytes),
            "accepted": accepted,
            "refusal_reason": None if accepted else reason,
            "fixed_canonical_spellable": meta["fixed_spellable"],
            "chosen_variant": meta.get("chosen_variant"),
            "rewritten_bytes": len(meta["code"].encode("utf-8")) if meta["spellable"] else None,
            "tokens": len(meta["token_ids"]) if accepted else None,
            "fixed6_tokens": len(meta["fixed6_token_ids"]) if accepted else None,
            "cases_passed": cases_passed if meta["spellable"] else None,
            "cases_total": len(p["cases"]),
            "original_steps": ro["total_steps"],
            "rewritten_steps": rw_steps,
            "step_ratio": round(step_ratio, 6) if step_ratio is not None else None,
        })

    # 6. Encode BOTH B3H1 (Huffman) and B3P1-transfer (Fixed-6-bit, B3PT) packages
    #    (charging selector bitmap + fallback table + fallback stream + 15,608-bit decoder!)
    pkg_raw_fb, bd_raw_fb = pc.encode_b3h1(vocab, records_raw_fb, lengths=lengths, fallback_bpe=None, transfer_mode=True)
    pkg_bpe_fb, bd_bpe_fb = pc.encode_b3h1(vocab, records_bpe_fb, lengths=lengths, fallback_bpe=fb_bpe, transfer_mode=True)
    if bd_bpe_fb["complete_bits"] < bd_raw_fb["complete_bits"]:
        chosen_pkg, chosen_bd = pkg_bpe_fb, bd_bpe_fb
    else:
        chosen_pkg, chosen_bd = pkg_raw_fb, bd_raw_fb

    pkg_f6_raw_fb, bd_f6_raw_fb = pc.encode_b3p1_transfer(vocab, records_f6_raw_fb, width=6, fallback_bpe=None)
    pkg_f6_bpe_fb, bd_f6_bpe_fb = pc.encode_b3p1_transfer(vocab, records_f6_bpe_fb, width=6, fallback_bpe=fb_bpe)
    if bd_f6_bpe_fb["complete_bits"] < bd_f6_raw_fb["complete_bits"]:
        chosen_f6_pkg, chosen_f6_bd = pkg_f6_bpe_fb, bd_f6_bpe_fb
    else:
        chosen_f6_pkg, chosen_f6_bd = pkg_f6_raw_fb, bd_f6_raw_fb

    transfer_pkg_path = ARTIFACTS / "dev_transfer_b3.b3h1"
    transfer_pkg_path.write_bytes(chosen_pkg)
    transfer_f6_pkg_path = ARTIFACTS / "dev_transfer_b3_fixed6.b3p1"
    transfer_f6_pkg_path.write_bytes(chosen_f6_pkg)

    # 7. Independent decode of BOTH B3H1 and B3P1-transfer packages + ZERO wrong-acceptance verification!
    t_dec0 = time.monotonic()
    tr_pkg_bytes = transfer_pkg_path.read_bytes()
    tr_f6_bytes = transfer_f6_pkg_path.read_bytes()
    dec_ind = idec.decode_b3h1(tr_pkg_bytes)
    dec_ref = refdec.decode_b3h1(tr_pkg_bytes)
    dec_f6_ind = idec.decode_b3p1_transfer(tr_f6_bytes)
    decode_seconds = time.monotonic() - t_dec0
    assert dec_ind["programs"] == dec_ref[1]
    assert dec_ind["modes"] == dec_ref[2]
    assert dec_ind["programs"] == dec_f6_ind["programs"], "B3P1-transfer decoded programs differ from B3H1!"
    assert dec_ind["modes"] == dec_f6_ind["modes"], "B3P1-transfer selector modes differ from B3H1!"

    per_prog_decode_ms: list[float] = []
    for _ in range(5):
        t_d = time.perf_counter()
        idec.decode_b3h1(tr_pkg_bytes)
        per_prog_decode_ms.append((time.perf_counter() - t_d) * 1000.0 / len(problems))

    # Re-verify EVERY independently decoded program (accepted AND fallback!) in step_verifier.mjs
    t_reexec0 = time.monotonic()
    reexec_jobs = []
    for p, code, mode in zip(problems, dec_ind["programs"], dec_ind["modes"]):
        reexec_jobs.append({
            "id": p["id"],
            "code": code,
            "entry": "solve",
            "interface": "function",
            "method": "solve",
            "allow_cjs_export": bool(mode == 1),
            "cases": [{"args": c["args"]} for c in p["cases"]],
        })
    reexec_res = run_step_batch(reexec_jobs)
    reexec_seconds = time.monotonic() - t_reexec0

    wrong_acceptances = 0
    fallback_verified = 0
    accepted_verified = 0
    for p, mode, rr in zip(problems, dec_ind["modes"], reexec_res):
        ro = orig_by_pid[p["id"]]
        ok_prog = rr["ok"]
        if ok_prog:
            for idx, (case, reco, rec) in enumerate(zip(p["cases"], ro["records"], rr["records"])):
                oo = {k: reco.get(k) for k in ("result", "args_after", "error")}
                ok_c, _ = cl.check_transfer_case(case, rec, original_obs=oo, abs_tol=p["abs_tol"])
                if not ok_c:
                    ok_prog = False
                    break
        ratio = rr["total_steps"] / max(1, ro["total_steps"]) if ok_prog else 999.0
        if mode == 0:
            if ok_prog and ratio <= 1.1:
                accepted_verified += 1
            else:
                wrong_acceptances += 1
        else:
            assert ok_prog, f"Decoded fallback program #{p['id']} failed execution!"
            fallback_verified += 1

    assert wrong_acceptances == 0, f"WRONG ACCEPTANCES DETECTED: {wrong_acceptances}"

    # 8. Baselines on the EXACT same 83 dev transfer raw programs:
    #    (a) Frozen matched80 255-entry raw BPE + escape (truly frozen transfer baseline!)
    #    (b) In-domain 256-entry raw BPE trained directly on dev_transfer (strongest ceiling!)
    raw_bytes_list = [p["raw_source"].encode("utf-8") for p in problems]
    total_raw_bytes = sum(len(x) for x in raw_bytes_list)

    # Frozen matched80 BPE-255 + escape applied to transfer raw bytes
    fb_orig_bpe = frozen["frozen_fallback_bpe255_original"]
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

    # In-domain 256-entry raw BPE fit directly on dev_transfer (oracle upper-bound baseline!)
    indomain_bpe = dt.train_bpe_256(raw_bytes_list, max_vocab=256)
    pkg_ind_hf, bd_ind_hf = pc.encode_b3b1_bpe(indomain_bpe["base_alphabet"], indomain_bpe["merges"], indomain_bpe["sequences"], coding="huffman")
    pkg_ind_f8, bd_ind_f8 = pc.encode_b3b1_bpe(indomain_bpe["base_alphabet"], indomain_bpe["merges"], indomain_bpe["sequences"], coding="fixed8")
    assert idec.decode_b3b1(pkg_ind_hf)["programs"] == [p["raw_source"] for p in problems]
    assert idec.decode_b3b1(pkg_ind_f8)["programs"] == [p["raw_source"] for p in problems]

    # Measure helper bits on accepted transfer programs
    hoist_bytes = sum(
        len(code[: code.find("function ")].encode("utf-8")) if code.find("function ") > 0 else 0
        for code in accepted_texts_by_id.values()
    )

    # Uncovered problem families
    uncovered_families = sorted(fam for fam, st in family_stats.items() if st["refused"] > 0)
    completely_uncovered_families = sorted(fam for fam, st in family_stats.items() if st["accepted"] == 0)

    # Programmatic dev transfer decisions (STRICTLY separate from matched80 witness decision!)
    # PASS iff (accepted / total >= 0.90) AND (wrong_acceptances == 0) AND (complete_bits <= baseline_complete_bits)
    b3h1_decision_core = compute_transfer_decision(
        accepted_verified, len(problems), wrong_acceptances,
        chosen_bd["complete_bits"], bd_fb_canon_hf["complete_bits"],
    )
    b3p1_decision_core = compute_transfer_decision(
        accepted_verified, len(problems), wrong_acceptances,
        chosen_f6_bd["complete_bits"], bd_fb_canon_f8["complete_bits"],
    )

    beats_frozen_bpe_canon_huff = chosen_bd["complete_bits"] <= bd_fb_canon_hf["complete_bits"]
    beats_frozen_bpe_orig_huff = chosen_bd["complete_bits"] <= bd_fb_orig_hf["complete_bits"]
    beats_indomain_bpe256_huff = chosen_bd["complete_bits"] <= bd_ind_hf["complete_bits"]
    beats_indomain_bpe256_f8 = chosen_bd["complete_bits"] <= bd_ind_f8["complete_bits"]

    f6_beats_frozen_bpe_canon_f8 = chosen_f6_bd["complete_bits"] <= bd_fb_canon_f8["complete_bits"]
    f6_beats_frozen_bpe_canon_huff = chosen_f6_bd["complete_bits"] <= bd_fb_canon_hf["complete_bits"]
    f6_beats_indomain_bpe256_f8 = chosen_f6_bd["complete_bits"] <= bd_ind_f8["complete_bits"]
    f6_beats_indomain_bpe256_huff = chosen_f6_bd["complete_bits"] <= bd_ind_hf["complete_bits"]

    # Horizon H* on dev transfer (for BOTH B3H1 Huffman and B3P1 Fixed-6-bit)
    fixed_oh = chosen_bd["header_bits"] + chosen_bd["decoder_machinery_bits"]
    stream_b3 = chosen_bd["coded_stream_bits"]
    f6_fixed_oh = chosen_f6_bd["header_bits"] + chosen_f6_bd["decoder_machinery_bits"]
    f6_stream_b3 = chosen_f6_bd["coded_stream_bits"]
    horizons = {
        "vs_frozen_matched80_bpe255_canonical_huffman": compute_horizon(
            fixed_oh, stream_b3, bd_fb_canon_hf["complete_bits"], len(problems), total_raw_bytes
        ),
        "vs_indomain_dev_bpe256_huffman": compute_horizon(
            fixed_oh, stream_b3, bd_ind_hf["complete_bits"], len(problems), total_raw_bytes
        ),
        "vs_raw_utf8": compute_horizon(
            fixed_oh, stream_b3, total_raw_bytes * 8, len(problems), total_raw_bytes
        ),
        "b3p1_fixed6_vs_frozen_matched80_bpe255_canonical_fixed8": compute_horizon(
            f6_fixed_oh, f6_stream_b3, bd_fb_canon_f8["complete_bits"], len(problems), total_raw_bytes
        ),
        "b3p1_fixed6_vs_frozen_matched80_bpe255_canonical_huffman": compute_horizon(
            f6_fixed_oh, f6_stream_b3, bd_fb_canon_hf["complete_bits"], len(problems), total_raw_bytes
        ),
        "b3p1_fixed6_vs_indomain_dev_bpe256_fixed8": compute_horizon(
            f6_fixed_oh, f6_stream_b3, bd_ind_f8["complete_bits"], len(problems), total_raw_bytes
        ),
    }

    summary = {
        "schema": "b3.dev_transfer.eval.v2",
        "frozen_dict_sha256": frozen_sha256,
        "frozen_dict_byte_identical_verified": frozen_sha256 == EXPECTED_FROZEN_DICT64_SHA256,
        "rewriter_fingerprint": current_rewriter_fp,
        "pass1_rewriter_fingerprint": frozen["rewriter_fingerprint"],
        "pass_comparison": {
            "pass1_initial": PASS1_HISTORICAL_RECEIPT,
            "pass2_single_general_transform": {
                "pass_name": "pass2_guarded_numeric_copy_sort_specialization",
                "transform_summary": "General AST lowering of non-mutating numeric copy-sort (<expr>.slice().sort((a,b)=>a-b) and fresh [...].sort((a,b)=>a-b)) to a runtime-guarded Float64Array fast path (verifying Array.isArray, pristine .slice / [Symbol.iterator], dense copy c.every(Number.isFinite), and !c.some(Object.is.bind(null,-0)), falling back verbatim to the original JS comparator sort outside finite non-negative-zero numeric arrays) without changing frozen_dict64.json or the 1.1x step ceiling.",
                "rewriter_mjs_sha256": current_rewriter_fp["rewriter_mjs_sha256"],
                "frozen_dict64_sha256": frozen_sha256,
                "step_ceiling": 1.1,
                "accepted_programs": accepted_verified,
                "refused_programs": fallback_verified,
                "total_programs": len(problems),
                "coverage_rate": round(accepted_verified / len(problems), 4),
                "wrong_acceptances": wrong_acceptances,
                "b3h1_complete_bits": chosen_bd["complete_bits"],
                "b3h1_package_bits_excluding_decoder": chosen_bd["package_bits_excluding_decoder"],
                "b3p1_fixed6_complete_bits": chosen_f6_bd["complete_bits"],
                "b3p1_fixed6_package_bits_excluding_decoder": chosen_f6_bd["package_bits_excluding_decoder"],
                "refusal_reasons": dict(refusal_reasons),
                "status": b3h1_decision_core["status"],
                "delta_accepted_vs_pass1": accepted_verified - PASS1_HISTORICAL_RECEIPT["accepted_programs"],
                "delta_b3h1_complete_bits_vs_pass1": chosen_bd["complete_bits"] - PASS1_HISTORICAL_RECEIPT["b3h1_complete_bits"],
            },
        },
        "cohort": {
            "name": "spent_dev_transfer_continuation_a_d_f_h_j_l_n_o",
            "cohorts": dt_cohort["cohorts"],
            "problems": len(problems),
            "total_cases": dt_cohort["total_cases"],
            "total_raw_bytes": total_raw_bytes,
            "disjoint_from_matched80": True,
            "disjoint_from_reserved": True,
            "family_counts": dt_cohort["family_counts"],
        },
        "transfer_decision": {
            "independent_from_witness_decision": True,
            **b3h1_decision_core,
            "beats_frozen_matched80_bpe255_canonical_huffman_with_decoder": beats_frozen_bpe_canon_huff,
            "beats_frozen_matched80_bpe255_original_huffman_with_decoder": beats_frozen_bpe_orig_huff,
            "beats_indomain_dev_bpe256_huffman_with_decoder": beats_indomain_bpe256_huff,
            "beats_indomain_dev_bpe256_fixed8_with_decoder": beats_indomain_bpe256_f8,
            "earns_sealed_transfer_evaluation": b3h1_decision_core["status"] == "PASS",
            "b4_gate_note": (
                "PASS on spent dev transfer earns sealed transfer evaluation only; "
                "B4 still requires sealed transfer success AND explicit compute approval."
                if b3h1_decision_core["status"] == "PASS"
                else "FAIL on spent dev transfer; sealed transfer not earned."
            ),
        },
        "b3p1_fixed6_transfer_decision": {
            "independent_from_witness_decision": True,
            **b3p1_decision_core,
            "beats_frozen_matched80_bpe255_canonical_fixed8_with_decoder": f6_beats_frozen_bpe_canon_f8,
            "beats_frozen_matched80_bpe255_canonical_huffman_with_decoder": f6_beats_frozen_bpe_canon_huff,
            "beats_indomain_dev_bpe256_fixed8_with_decoder": f6_beats_indomain_bpe256_f8,
            "beats_indomain_dev_bpe256_huffman_with_decoder": f6_beats_indomain_bpe256_huff,
        },
        "shared_spine": {
            "fidelity": {
                "accepted_programs": accepted_verified,
                "refused_fallback_programs": fallback_verified,
                "total_programs": len(problems),
                "fixed_canonical_spellable": fixed_spellable_count,
                "wrong_acceptances": wrong_acceptances,
                "independent_decode_verified": len(problems),
                "independent_decode_b3p1_fixed6_verified": len(problems),
                "step_compliant_accepted": accepted_verified,
                "max_accepted_step_ratio": round(max(accepted_step_ratios), 6) if accepted_step_ratios else None,
                "p95_accepted_step_ratio": round(p95(accepted_step_ratios), 6) if accepted_step_ratios else None,
                "median_accepted_step_ratio": round(statistics.median(accepted_step_ratios), 6) if accepted_step_ratios else None,
                "changed_algorithms": 0,
            },
            "complete_bits": {
                "b3h1_huffman_transfer_complete_bits": chosen_bd["complete_bits"],
                "b3h1_huffman_transfer_package_bits_excluding_decoder": chosen_bd["package_bits_excluding_decoder"],
                "b3p1_fixed6_transfer_complete_bits": chosen_f6_bd["complete_bits"],
                "b3p1_fixed6_transfer_package_bits_excluding_decoder": chosen_f6_bd["package_bits_excluding_decoder"],
                "b3p1_fixed6_transfer_raw_utf8_fallback_complete_bits": bd_f6_raw_fb["complete_bits"],
                "b3p1_fixed6_transfer_bpe255_fallback_complete_bits": bd_f6_bpe_fb["complete_bits"],
                "b3p1_fixed6_transfer_breakdown": chosen_f6_bd,
                "b3_transfer_chosen_complete_bits": chosen_bd["complete_bits"],
                "b3_transfer_chosen_package_bits_excluding_decoder": chosen_bd["package_bits_excluding_decoder"],
                "b3_transfer_chosen_fallback_mode": chosen_bd["fallback_mode"],
                "b3_transfer_raw_utf8_fallback_complete_bits": bd_raw_fb["complete_bits"],
                "b3_transfer_bpe255_fallback_complete_bits": bd_bpe_fb["complete_bits"],
                "b3_transfer_breakdown": chosen_bd,
                "explicit_hoisted_source_bytes_accepted": hoist_bytes,
                "hidden_helper_bits": 0,
                "baseline_frozen_matched80_bpe255_canonical_huffman": bd_fb_canon_hf,
                "baseline_frozen_matched80_bpe255_canonical_fixed8": bd_fb_canon_f8,
                "baseline_frozen_matched80_bpe255_original_huffman": bd_fb_orig_hf,
                "baseline_frozen_matched80_bpe255_original_fixed8": bd_fb_orig_f8,
                "baseline_indomain_dev_bpe256_huffman": bd_ind_hf,
                "baseline_indomain_dev_bpe256_fixed8": bd_ind_f8,
            },
            "measured_work": {
                "orig_verify_seconds": round(orig_verify_seconds, 4),
                "rewrite_seconds": round(rewrite_seconds, 4),
                "selection_seconds": round(selection_seconds, 4),
                "verify_candidates_seconds": round(verify_seconds, 4),
                "decode_seconds": round(decode_seconds, 6),
                "decode_p95_ms_per_program": round(p95(per_prog_decode_ms), 4),
                "reexec_decoded_seconds": round(reexec_seconds, 4),
                "total_wall_seconds": round(time.monotonic() - t0, 4),
                "peak_rss_bytes": peak_rss_bytes(),
                "measured_step_counts": {
                    "total_original_steps": sum(orig_by_pid[p["id"]]["total_steps"] for p in problems),
                    "accepted_original_steps": sum(orig_by_pid[r["id"]]["total_steps"] for r in per_problem if r["accepted"]),
                    "accepted_rewritten_steps": sum(r["rewritten_steps"] for r in per_problem if r["accepted"]),
                    "max_accepted_step_ratio": round(max(accepted_step_ratios), 6) if accepted_step_ratios else None,
                },
            },
            "horizon": horizons,
        },
        "diagnostics": {
            "family_breakdown": dict(sorted(family_stats.items())),
            "uncovered_problem_families_any_refusal": uncovered_families,
            "completely_uncovered_problem_families": completely_uncovered_families,
            "refusal_reason_counts": dict(refusal_reasons),
            "unspellable_syntax_and_literals_top_blockers": dict(blocking_token_totals.most_common(25)),
            "unspellable_problem_details": unspellable_diagnostics,
            "dictionary_utilization_on_transfer": {
                "total_entries": len(vocab),
                "used_entries_on_transfer": len(used_transfer_ids),
                "utilization_fraction": round(len(used_transfer_ids) / len(vocab), 4),
                "unused_entries_on_transfer": [vocab[i] for i in range(len(vocab)) if i not in used_transfer_ids],
            },
            "runtime_tails_accepted": {
                "top_5_step_ratios": sorted([r for r in per_problem if r["accepted"]], key=lambda r: (-r["step_ratio"], r["id"]))[:5],
            },
        },
        "per_program_transfer": per_problem,
    }

    (ARTIFACTS / "dev_transfer_eval.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    res = run_transfer_eval()
    print(json.dumps({
        "transfer_decision": res["transfer_decision"],
        "fidelity": res["shared_spine"]["fidelity"],
        "b3_complete_bits": res["shared_spine"]["complete_bits"]["b3_transfer_chosen_complete_bits"],
        "b3_excl_dec_bits": res["shared_spine"]["complete_bits"]["b3_transfer_chosen_package_bits_excluding_decoder"],
        "b3_fallback_mode": res["shared_spine"]["complete_bits"]["b3_transfer_chosen_fallback_mode"],
        "frozen_m80_bpe255_canon_huff": res["shared_spine"]["complete_bits"]["baseline_frozen_matched80_bpe255_canonical_huffman"]["complete_bits"],
        "frozen_m80_bpe255_orig_huff": res["shared_spine"]["complete_bits"]["baseline_frozen_matched80_bpe255_original_huffman"]["complete_bits"],
        "indomain_dev_bpe256_huff": res["shared_spine"]["complete_bits"]["baseline_indomain_dev_bpe256_huffman"]["complete_bits"],
        "family_breakdown": res["diagnostics"]["family_breakdown"],
        "refusal_reasons": res["diagnostics"]["refusal_reason_counts"],
        "top_blockers": res["diagnostics"]["unspellable_syntax_and_literals_top_blockers"],
    }, indent=2))
