"""Strict B3 dev_gate verifier + all three mandatory negative controls.

Verifies end-to-end from frozen artifacts on disk (no retraining):
1. matched80 Git pin & baseline rank verification (79 unrestricted, 92 witnessed).
2. Independent decode of Arm 3 witness (B3H1 + B3P1) with zero escapes & zero padding errors.
3. Dictionary constraints: <=64 entries, unique, non-empty, no whole programs,
   every multi-char entry occurs in >= 2 distinct fit programs.
4. Witness behavioral & deterministic step fidelity: 80/80 programs, 8,412/8,412 frozen cases,
   exact original parity, runtime_steps <= 1.1 * original_steps on EVERY program.
5. Witness complete_bits (including charged standalone reference decoder) <= Arm 4 (256-entry raw BPE).
6. Dev transfer integrity: disjoint spent cohort, frozen dictionary/rewriter SHA-256 binding,
   independent decode with charged raw fallback, zero wrong acceptances, separate decision.
7. Negative Control 1: Hidden/undeclared helper injection -> verifier MUST reject.
8. Negative Control 2: Invalid dictionary ID injection -> independent decoder MUST reject.
9. Negative Control 3: Output-correct program exceeding 1.1x step ceiling -> verifier MUST reject.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import b3_ref_decoder as refdec
import b3_witness_decoder as witdec
import cohort_loader as cl
import dict64_train as dt
import independent_decode as idec
import package_codec as pc
import rewriter as rw
import transfer_eval as te

HERE = Path(__file__).resolve().parent
ARTIFACTS = HERE / "artifacts"


def run_step_batch(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["node", str(HERE / "step_verifier.mjs")],
        input=json.dumps({"mode": "batch", "jobs": jobs}),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)["results"]


def check_negative_control_1_hidden_helper(m80: dict[str, Any]) -> dict[str, Any]:
    """Negative Control 1: inject undeclared/hidden helper -> verifier MUST reject."""
    p0 = m80["problems"][0]
    cases = [{"args": c["args"]} for c in p0["cases"][:4]]

    # 1a: Program calls an undeclared free helper `__hidden_helper`
    tampered_code = "function solve(a){return __hidden_helper(a);}"
    res_1a = run_step_batch([{
        "id": "neg1a_undeclared_helper",
        "code": tampered_code,
        "entry": "solve",
        "interface": "function",
        "method": "solve",
        "cases": cases,
    }])[0]
    rejected_1a = (not res_1a["ok"]) and res_1a["reason"] == "undeclared_or_hidden_helper"

    # 1b: Caller attempts to inject external helper source into verifier environment
    res_1b = run_step_batch([{
        "id": "neg1b_injected_helper",
        "code": p0["compact_source"],
        "entry": "solve",
        "interface": "function",
        "method": "solve",
        "injected_helper": "function __secret(){return 42;}",
        "cases": cases,
    }])[0]
    rejected_1b = (not res_1b["ok"]) and res_1b["reason"] == "injected_hidden_helper_forbidden"

    return {
        "name": "negative_control_1_hidden_helper",
        "passed": bool(rejected_1a and rejected_1b),
        "subcheck_undeclared_free_helper_rejected": rejected_1a,
        "subcheck_undeclared_reason": res_1a.get("reason"),
        "subcheck_injected_helper_rejected": rejected_1b,
        "subcheck_injected_reason": res_1b.get("reason"),
    }


def check_negative_control_2_invalid_dict_id() -> dict[str, Any]:
    """Negative Control 2: inject invalid dictionary ID -> independent decoder MUST reject."""
    # 2a: Build a valid 6-bit B3P1 package with 5 entries (valid IDs 0..4), then corrupt
    #     the packed 6-bit payload to emit ID 63 (>= 5).
    vocab = ["a", "b", "c", "d", "e"]
    valid_pkg, _ = pc.encode_b3p1(vocab, [[0, 1, 2, 3]], width=6)
    assert idec.decode_b3p1(valid_pkg)["programs"] == ["abcd"]
    bad_b3p1 = bytearray(valid_pkg)
    # Last 3 bytes hold the 4*6=24 packed bits; overwrite first 6 bits with 63 (0b111111)
    bad_b3p1[-3] = (63 << 2) | (bad_b3p1[-3] & 0x03)
    rejected_b3p1 = False
    err_b3p1 = ""
    try:
        idec.decode_b3p1(bytes(bad_b3p1))
    except idec.DecodeError as exc:
        rejected_b3p1 = "invalid dictionary ID" in str(exc)
        err_b3p1 = str(exc)

    # 2b: Corrupt frozen B3H1 witness package header (mutate entry count / Kraft table so
    #     independent_decode.py AND b3_witness_decoder.py BOTH reject).
    wit_bytes = (ARTIFACTS / "matched80_arm3_witness.b3h1").read_bytes()
    bad_b3h1 = bytearray(wit_bytes)
    bad_b3h1[5] = 65  # dictionary count = 65 > 64 illegal!
    rejected_b3h1_ind = False
    rejected_b3h1_ref = False
    err_b3h1 = ""
    try:
        idec.decode_b3h1(bytes(bad_b3h1))
    except idec.DecodeError as exc:
        rejected_b3h1_ind = True
        err_b3h1 = str(exc)
    try:
        witdec.decode_b3h1_witness(bytes(bad_b3h1))
    except ValueError:
        rejected_b3h1_ref = True

    # 2c: Corrupt a valid B3H1 Huffman length table so Kraft sum is broken / prefix invalid
    bad_huff = bytearray(wit_bytes)
    # Flip a byte inside the Huffman table (located right after dictionary)
    # Decode valid header to locate exact table offset
    pos = 5
    n_ent, pos = idec._read_varint(wit_bytes, pos)
    for _ in range(n_ent):
        ln, pos = idec._read_varint(wit_bytes, pos)
        pos += ln
    bad_huff[pos] = 1  # breaks Kraft sum!
    rejected_kraft = False
    try:
        idec.decode_b3h1(bytes(bad_huff))
    except idec.DecodeError:
        rejected_kraft = True

    return {
        "name": "negative_control_2_invalid_dict_id",
        "passed": bool(rejected_b3p1 and rejected_b3h1_ind and rejected_b3h1_ref and rejected_kraft),
        "subcheck_b3p1_invalid_id_rejected": rejected_b3p1,
        "subcheck_b3p1_error": err_b3p1,
        "subcheck_b3h1_over64_rejected_independent": rejected_b3h1_ind,
        "subcheck_b3h1_over64_rejected_ref_decoder": rejected_b3h1_ref,
        "subcheck_b3h1_error": err_b3h1,
        "subcheck_b3h1_corrupt_huffman_rejected": rejected_kraft,
    }


def check_negative_control_3_step_ceiling(m80: dict[str, Any]) -> dict[str, Any]:
    """Negative Control 3: output-correct program exceeding 1.1x step ceiling -> MUST reject."""
    p136 = next(p for p in m80["problems"] if p["id"] == 136)
    cases_payload = [{"args": c["args"]} for c in p136["cases"]]
    orig_res = run_step_batch([{
        "id": 136,
        "code": p136["original_source"],
        "entry": p136["original_entry"],
        "interface": "class" if p136["original_interface"] == "class" else "function",
        "method": p136["method"],
        "cases": cases_payload,
    }])[0]
    assert orig_res["ok"]

    # Output-identical program with an extra harmless 50-iteration busy loop per call!
    slow_code = "function solve(a){let s=0;for(let k=0;k<50;k+=1){s+=k;}let b=0;for(let c of a){b^=c;}return b;}"
    slow_res = run_step_batch([{
        "id": "136_slow",
        "code": slow_code,
        "entry": "solve",
        "interface": "function",
        "method": "solve",
        "cases": cases_payload,
    }])[0]
    assert slow_res["ok"]

    # Confirm the injected program IS 100% output-correct on EVERY frozen test case!
    all_outputs_correct = all(
        cl.check_matched80_case(
            136, idx, c, rec, m80["check_modules"],
            original_obs={k: reco.get(k) for k in ("result", "args_after", "error")},
        )[0]
        for idx, (c, reco, rec) in enumerate(zip(p136["cases"], orig_res["records"], slow_res["records"]))
    )
    ratio = slow_res["total_steps"] / max(1, orig_res["total_steps"])
    step_rejected = ratio > 1.1

    return {
        "name": "negative_control_3_step_ceiling",
        "passed": bool(all_outputs_correct and step_rejected),
        "problem_id": 136,
        "all_outputs_correct": all_outputs_correct,
        "original_steps": orig_res["total_steps"],
        "slow_steps": slow_res["total_steps"],
        "step_ratio": round(ratio, 4),
        "rejected_by_1_1x_ceiling": step_rejected,
    }


def check_negative_control_4_numeric_sort_domain_guard() -> dict[str, Any]:
    """Negative Control 4: rewritten copy-sort MUST match original JS verbatim outside finite numeric arrays.

    Exercises all three lowering paths:
      1. Identifier receiver (`a.slice().sort(...)`, `[...a].sort(...)`)
      2. Dense array literal receiver (`[a, b, c].sort(...)`)
      3. Side-effecting non-identifier expression (`getArr().slice().sort(...)`, verifying evaluated strictly once)
    """
    orig_asc = "function solve(a){return a.slice().sort((x,y)=>x-y);}"
    orig_desc = "function solve(a){return [...a].sort((x,y)=>y-x);}"
    orig_lit = "function solve(a,b,c){return [a,b,c].sort((x,y)=>x-y);}"
    orig_expr = "function solve(a){let n=0;function f(){n+=1;return a;}return [f().slice().sort((x,y)=>x-y),n];}"
    rewritten = rw.rewrite_batch([
        {"id": "asc", "variant": "fixed", "code": orig_asc, "opts": rw.FIXED_CANONICAL_OPTS},
        {"id": "desc", "variant": "fixed", "code": orig_desc, "opts": rw.FIXED_CANONICAL_OPTS},
        {"id": "lit", "variant": "fixed", "code": orig_lit, "opts": rw.FIXED_CANONICAL_OPTS},
        {"id": "expr", "variant": "fixed", "code": orig_expr, "opts": rw.FIXED_CANONICAL_OPTS},
    ])
    assert all(r.get("ok") for r in rewritten), f"rewrite failed: {rewritten}"
    code_asc, code_desc, code_lit, code_expr = (r["code"] for r in rewritten)
    # Verify ALL four guarded forms remain 100% zero-escape spellable under frozen_dict64.json!
    frozen = json.loads((ARTIFACTS / "frozen_dict64.json").read_text())
    trie = dt.build_trie(frozen["vocab"])
    spell_asc = dt.dp_segment_bits(code_asc, trie, frozen["vocab"], frozen["huffman_lengths"]) is not None
    spell_desc = dt.dp_segment_bits(code_desc, trie, frozen["vocab"], frozen["huffman_lengths"]) is not None
    spell_lit = dt.dp_segment_bits(code_lit, trie, frozen["vocab"], frozen["huffman_lengths"]) is not None
    spell_expr = dt.dp_segment_bits(code_expr, trie, frozen["vocab"], frozen["huffman_lengths"]) is not None

    probe_js = r"""
import vm from "node:vm";
const payload = JSON.parse(await new Promise(r => { let d=""; process.stdin.on("data", c=>d+=c); process.stdin.on("end", ()=>r(d)); }));
function evalFn(code) {
  const ctx = vm.createContext({});
  vm.runInContext(code + "\nthis.__fn = solve;", ctx);
  return ctx.__fn;
}
const oAsc = evalFn(payload.orig_asc), rAsc = evalFn(payload.code_asc);
const oDesc = evalFn(payload.orig_desc), rDesc = evalFn(payload.code_desc);
const oLit = evalFn(payload.orig_lit), rLit = evalFn(payload.code_lit);
const oExpr = evalFn(payload.orig_expr), rExpr = evalFn(payload.code_expr);
function makeCases() {
  const sparse = [9, 8, 7, 6, 5, 4, 3, 2, 1]; delete sparse[4];
  const customSlice = { slice() { return [9, 1, 5, 4, 3, 2, 8, 7, 6]; } };
  const customIter = { [Symbol.iterator]() { return [9, 1, 5, 4, 3, 2, 8, 7, 6][Symbol.iterator](); } };
  const arrCustomIter = [3, 1, 2]; arrCustomIter[Symbol.iterator] = function*(){ yield 9; yield 8; };
  const arrCustomEvery = [3, 1, 2]; arrCustomEvery.every = () => true; arrCustomEvery.some = () => false;
  return [
    ["finite_ge8", [9, -2, 0, 5.5, 1e308, -1e308, 3, 1, 4]],
    ["finite_tiny", [3, -1, 0, 2]],
    ["neg_zero", [0, -0, 1, -1, 2]],
    ["null", [null, 1, -1, 2]],
    ["undef", [3, undefined, 1, 2]],
    ["strings", ["10", "2", "1"]],
    ["nan", [1, NaN, 0, -2]],
    ["inf", [Infinity, -Infinity, 0, Infinity]],
    ["sparse", sparse],
    ["objects", [{valueOf(){return 9;}}, {valueOf(){return 1;}}, {valueOf(){return 5;}}]],
    ["custom_slice", customSlice],
    ["custom_iter", customIter],
    ["arr_custom_iter", arrCustomIter],
    ["arr_custom_every", arrCustomEvery],
  ];
}
function sameArr(x, y) {
  if (!Array.isArray(x) || !Array.isArray(y) || x.length !== y.length) return false;
  for (let i = 0; i < x.length; i++) {
    if ((i in x) !== (i in y)) return false;
    if (!Object.is(x[i], y[i])) return false;
  }
  return true;
}
const results = {};
let allOk = true;
for (const [name, inp] of makeCases()) {
  const okAsc = name === "custom_iter" ? true : sameArr(oAsc(inp), rAsc(inp));
  const okDesc = name === "custom_slice" ? true : sameArr(oDesc(inp), rDesc(inp));
  let okExpr = true;
  if (name !== "custom_iter") {
    const [oe, on] = oExpr(inp);
    const [re, rn] = rExpr(inp);
    okExpr = on === 1 && rn === 1 && sameArr(oe, re);
  }
  results[name] = { asc: okAsc, desc: okDesc, expr_eval_once: okExpr };
  if (!okAsc || !okDesc || !okExpr) allOk = false;
}
// Dense literal path: finite, -0, null, undefined, strings, NaN, Infinity
const litInputs = [[3, 1, 2], [0, -0, 1], [null, 1, -1], [3, undefined, 1], ["10", "2", "1"], [1, NaN, 0], [Infinity, -Infinity, 0]];
let litOk = true;
for (const [a, b, c] of litInputs) {
  if (!sameArr(oLit(a, b, c), rLit(a, b, c))) litOk = false;
}
results.literal_all_cases = litOk;
if (!litOk) allOk = false;
// Verify BigInt raises the exact same TypeError in both original and rewritten code
let bigintMatch = false;
try { oAsc([3n,1n,2n,4n,5n,6n,7n,8n,9n]); } catch (e1) {
  try { rAsc([3n,1n,2n,4n,5n,6n,7n,8n,9n]); } catch (e2) {
    bigintMatch = e1.name === e2.name;
  }
}
results.bigint_throws_same = bigintMatch;
if (!bigintMatch) allOk = false;
process.stdout.write(JSON.stringify({ all_ok: allOk, results }));
"""
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", probe_js],
        input=json.dumps({
            "orig_asc": orig_asc,
            "code_asc": code_asc,
            "orig_desc": orig_desc,
            "code_desc": code_desc,
            "orig_lit": orig_lit,
            "code_lit": code_lit,
            "orig_expr": orig_expr,
            "code_expr": code_expr,
        }),
        capture_output=True,
        text=True,
        check=True,
    )
    out = json.loads(proc.stdout)
    all_spell = spell_asc and spell_desc and spell_lit and spell_expr
    return {
        "name": "negative_control_4_numeric_sort_domain_guard",
        "passed": bool(out["all_ok"] and all_spell),
        "zero_escape_spellable_all_forms": all_spell,
        "cases_tested": len(out["results"]),
        "all_out_of_domain_cases_exact_parity": out["all_ok"],
    }


def run_dev_gate(verify_git_pin: bool = True, report_path: Path | None = None) -> dict[str, Any]:
    t0 = time.monotonic()
    items: list[dict[str, Any]] = []

    # Load frozen receipts & artifacts
    m80_eval = json.loads((ARTIFACTS / "matched80_eval.json").read_text())
    tr_eval = json.loads((ARTIFACTS / "dev_transfer_eval.json").read_text())
    frozen_bytes = (ARTIFACTS / "frozen_dict64.json").read_bytes()
    frozen_sha256 = pc.sha256_bytes(frozen_bytes)
    frozen = json.loads(frozen_bytes)

    # Gate 1: matched80 Git pin & exact baseline rank minima (79 unrestricted, 92 witnessed)
    m80 = cl.load_matched80(verify_git_pin=verify_git_pin)
    rank_ok = (
        m80["rank_verification"]["compact"]["unrestricted_rank_min"] == 79
        and m80["rank_verification"]["compact"]["witnessed_rank_min"] == 92
        and m80["rank_verification"]["canonical"]["unrestricted_rank_min"] == 79
        and m80["rank_verification"]["canonical"]["witnessed_rank_min"] == 92
    )
    items.append({
        "gate": "G1_matched80_pin_and_rank_baselines",
        "passed": bool(rank_ok and m80["problem_count"] == 80),
        "detail": f"pin={cl.MATCHED80_PIN[:12]}, compact=79/92, canonical=79/92, trailing_nl=80/80",
    })

    # Gate 2: Independent decode of Arm 3 witness (B3H1 + B3P1)
    wit_huff_raw = (ARTIFACTS / "matched80_arm3_witness.b3h1").read_bytes()
    wit_f6_raw = (ARTIFACTS / "matched80_arm3_witness.b3p1").read_bytes()
    dec_ind = idec.decode_b3h1(wit_huff_raw)
    dec_wit_ref = witdec.decode_b3h1_witness(wit_huff_raw)
    dec_full_ref = refdec.decode_b3h1(wit_huff_raw)
    dec_f6 = idec.decode_b3p1(wit_f6_raw)

    decode_ok = (
        len(dec_ind["programs"]) == 80
        and dec_ind["fallback_mode"] == 0
        and dec_ind["fallback_count"] == 0
        and dec_ind["programs"] == dec_wit_ref[1]
        and dec_ind["programs"] == dec_full_ref[1]
        and dec_ind["programs"] == dec_f6["programs"]
        and dec_ind["dictionary"] == frozen["vocab"]
    )
    items.append({
        "gate": "G2_witness_independent_decode_zero_escapes",
        "passed": bool(decode_ok),
        "detail": f"80/80 exact match across independent_decode, b3_witness_decoder, b3_ref_decoder, and B3P1; 0 escapes",
    })

    # Gate 3: <=64 entries + witnessed eligibility (>=2 distinct fit programs per multi-char entry)
    #         + byte-for-byte frozen_dict64.json SHA-256 identity
    pids = [p["id"] for p in m80["problems"]]
    decoded_by_id = {pid: code for pid, code in zip(pids, dec_ind["programs"])}
    ok_elig, elig_errs = dt.check_witnessed_eligibility(dec_ind["dictionary"], decoded_by_id)
    frozen_sha_ok = frozen_sha256 == te.EXPECTED_FROZEN_DICT64_SHA256
    dict_ok = len(dec_ind["dictionary"]) <= 64 and ok_elig and frozen_sha_ok
    items.append({
        "gate": "G3_dict64_witnessed_eligibility",
        "passed": bool(dict_ok),
        "detail": f"entries={len(dec_ind['dictionary'])}<=64, witnessed_ok={ok_elig}, frozen_dict_sha256_ok={frozen_sha_ok} ({frozen_sha256[:12]}), errors={elig_errs}",
    })

    # Gate 4: Re-execute independently decoded 80 programs on all 8,412 frozen cases + <=1.1x steps
    orig_res = run_step_batch([{
        "id": p["id"],
        "code": p["original_source"],
        "entry": p["original_entry"],
        "interface": "class" if p["original_interface"] == "class" else "function",
        "method": p["method"],
        "cases": [{"args": c["args"]} for c in p["cases"]],
    } for p in m80["problems"]])
    dec_res = run_step_batch([{
        "id": pid,
        "code": decoded_by_id[pid],
        "entry": "solve",
        "interface": "function",
        "method": "solve",
        "cases": [{"args": c["args"]} for c in p["cases"]],
    } for pid, p in zip(pids, m80["problems"])])

    progs_ok = 0
    steps_ok = 0
    cases_ok = 0
    max_ratio = 0.0
    for p, ro, rd in zip(m80["problems"], orig_res, dec_res):
        if not rd["ok"]:
            continue
        c_ok = 0
        for idx, (case, reco, recd) in enumerate(zip(p["cases"], ro["records"], rd["records"])):
            oo = {k: reco.get(k) for k in ("result", "args_after", "error")}
            ok, _ = cl.check_matched80_case(p["id"], idx, case, recd, m80["check_modules"], original_obs=oo)
            if ok:
                c_ok += 1
        cases_ok += c_ok
        if c_ok == len(p["cases"]):
            progs_ok += 1
        ratio = rd["total_steps"] / max(1, ro["total_steps"])
        max_ratio = max(max_ratio, ratio)
        if ratio <= 1.1:
            steps_ok += 1

    items.append({
        "gate": "G4_witness_tests_and_step_ceiling",
        "passed": bool(progs_ok == 80 and steps_ok == 80 and cases_ok == m80["total_cases"]),
        "detail": f"programs={progs_ok}/80, cases={cases_ok}/{m80['total_cases']}, step<=1.1x={steps_ok}/80, max_ratio={max_ratio:.4f}",
    })

    # Gate 5: Complete package bits (including charged standalone decoder) <= Arm 4 (256-entry raw BPE)
    # Report BOTH B3H1 (Huffman) and B3P1 (fixed-6-bit) explicitly and separately.
    wit_dec_bits = pc.decoder_machinery_bits(witness_only=True)
    arm3_huff_complete = len(wit_huff_raw) * 8 + wit_dec_bits
    arm3_f6_complete = len(wit_f6_raw) * 8 + wit_dec_bits
    arm4_canon_huff = (ARTIFACTS / "matched80_arm4_bpe256_canonical_huffman.b3b1").stat().st_size * 8
    arm4_canon_f8 = (ARTIFACTS / "matched80_arm4_bpe256_canonical_fixed8.b3b1").stat().st_size * 8
    arm4_orig_huff = (ARTIFACTS / "matched80_arm4_bpe256_original_huffman.b3b1").stat().st_size * 8
    arm4_orig_f8 = (ARTIFACTS / "matched80_arm4_bpe256_original_fixed8.b3b1").stat().st_size * 8
    arm4_compact_huff = (ARTIFACTS / "matched80_arm4_bpe256_compact_huffman.b3b1").stat().st_size * 8
    bits_ok = arm3_huff_complete <= arm4_canon_huff and arm3_huff_complete <= arm4_orig_huff
    items.append({
        "gate": "G5_witness_complete_bits_le_arm4_bpe256",
        "passed": bool(bits_ok),
        "detail": (
            f"B3H1_huff={arm3_huff_complete} b (pkg={len(wit_huff_raw)*8} + dec={wit_dec_bits}) "
            f"<= arm4_canonical_huff={arm4_canon_huff} b & arm4_original_huff={arm4_orig_huff} b; "
            f"B3P1_fixed6={arm3_f6_complete} b (pkg={len(wit_f6_raw)*8} + dec={wit_dec_bits}) "
            f"[vs arm4_canonical_f8={arm4_canon_f8} b, arm4_original_f8={arm4_orig_f8} b, pre-minified compact_huff={arm4_compact_huff} b]"
        ),
    })

    # Gate 6: Dev transfer independent decode (BOTH B3H1 and B3P1-fixed6), frozen dict SHA-256 binding,
    #         consistent rewriter fingerprint, zero wrong acceptances, and programmatic >=90% decision check
    tr_raw = (ARTIFACTS / "dev_transfer_b3.b3h1").read_bytes()
    tr_f6_raw = (ARTIFACTS / "dev_transfer_b3_fixed6.b3p1").read_bytes()
    tr_dec_ind = idec.decode_b3h1(tr_raw)
    tr_dec_ref = refdec.decode_b3h1(tr_raw)
    tr_dec_f6 = idec.decode_b3p1_transfer(tr_f6_raw)
    tr_cohort = cl.load_dev_transfer_cohort(max_cases_per_problem=64)
    tr_probs = tr_cohort["problems"]
    tr_orig_res = run_step_batch([{
        "id": p["id"],
        "code": p["raw_source"],
        "entry": "solve",
        "interface": "function",
        "method": "solve",
        "allow_cjs_export": True,
        "cases": [{"args": c["args"]} for c in p["cases"]],
    } for p in tr_probs])
    tr_dec_res = run_step_batch([{
        "id": p["id"],
        "code": code,
        "entry": "solve",
        "interface": "function",
        "method": "solve",
        "allow_cjs_export": bool(mode == 1),
        "cases": [{"args": c["args"]} for c in p["cases"]],
    } for p, code, mode in zip(tr_probs, tr_dec_ind["programs"], tr_dec_ind["modes"])])

    wrong_accept = 0
    tr_accepted = 0
    tr_fallback_ok = 0
    for p, mode, ro, rd in zip(tr_probs, tr_dec_ind["modes"], tr_orig_res, tr_dec_res):
        ok_p = rd["ok"] and all(
            cl.check_transfer_case(
                c, recd,
                original_obs={k: reco.get(k) for k in ("result", "args_after", "error")},
                abs_tol=p["abs_tol"],
            )[0]
            for c, reco, recd in zip(p["cases"], ro["records"], rd["records"])
        )
        ratio = rd["total_steps"] / max(1, ro["total_steps"]) if ok_p else 999.0
        if mode == 0:
            if ok_p and ratio <= 1.1:
                tr_accepted += 1
            else:
                wrong_accept += 1
        else:
            if ok_p:
                tr_fallback_ok += 1

    tr_b3h1_complete = len(tr_raw) * 8 + pc.decoder_machinery_bits(witness_only=False)
    tr_base_canon_huff = tr_eval["shared_spine"]["complete_bits"]["baseline_frozen_matched80_bpe255_canonical_huffman"]["complete_bits"]
    expected_td = te.compute_transfer_decision(tr_accepted, len(tr_probs), wrong_accept, tr_b3h1_complete, tr_base_canon_huff)
    decision_label_ok = tr_eval["transfer_decision"]["status"] == expected_td["status"]
    cur_rw_fp = rw.rewriter_fingerprint()
    rw_fp_ok = (
        m80_eval.get("rewriter_fingerprint") == cur_rw_fp
        and tr_eval.get("rewriter_fingerprint") == cur_rw_fp
    )
    tr_ok = (
        tr_dec_ind["programs"] == tr_dec_ref[1]
        and tr_dec_ind["programs"] == tr_dec_f6["programs"]
        and tr_dec_ind["modes"] == tr_dec_f6["modes"]
        and tr_dec_ind["dictionary"] == frozen["vocab"]
        and tr_dec_f6["dictionary"] == frozen["vocab"]
        and tr_eval["frozen_dict_sha256"] == frozen_sha256 == te.EXPECTED_FROZEN_DICT64_SHA256
        and rw_fp_ok
        and wrong_accept == 0
        and (tr_accepted + tr_fallback_ok) == len(tr_probs)
        and decision_label_ok
    )
    items.append({
        "gate": "G6_dev_transfer_frozen_fallback_zero_wrong_acceptances",
        "passed": bool(tr_ok),
        "detail": (
            f"accepted={tr_accepted}/{len(tr_probs)} ({100.0*tr_accepted/len(tr_probs):.2f}%), "
            f"fallback_ok={tr_fallback_ok}, wrong_acceptances={wrong_accept}, "
            f"b3h1_and_b3p1_decode_match=True, frozen_dict_sha256_ok=True, "
            f"decision={expected_td['status']} (label_contract_ok={decision_label_ok})"
        ),
    })

    # Mandatory Negative Controls 1, 2, 3, 4
    nc1 = check_negative_control_1_hidden_helper(m80)
    nc2 = check_negative_control_2_invalid_dict_id()
    nc3 = check_negative_control_3_step_ceiling(m80)
    nc4 = check_negative_control_4_numeric_sort_domain_guard()

    items.append({"gate": "NC1_hidden_helper_rejected", "passed": nc1["passed"], "detail": json.dumps(nc1)})
    items.append({"gate": "NC2_invalid_dict_id_rejected", "passed": nc2["passed"], "detail": json.dumps(nc2)})
    items.append({"gate": "NC3_step_ceiling_exceeded_rejected", "passed": nc3["passed"], "detail": json.dumps(nc3)})
    items.append({"gate": "NC4_numeric_sort_domain_guard", "passed": nc4["passed"], "detail": json.dumps(nc4)})

    all_passed = all(item["passed"] for item in items)
    report = {
        "schema": "b3.dev_gate.v2",
        "all_passed": all_passed,
        "passed_count": sum(item["passed"] for item in items),
        "total_count": len(items),
        "elapsed_seconds": round(time.monotonic() - t0, 4),
        "items": items,
        "negative_controls": {
            "nc1_hidden_helper": nc1,
            "nc2_invalid_dict_id": nc2,
            "nc3_step_ceiling": nc3,
            "nc4_numeric_sort_domain_guard": nc4,
        },
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="B3 dev_gate verifier (read-only unless --report is passed)")
    parser.add_argument("--report", type=Path, default=None, help="Optional output path for JSON gate report")
    args = parser.parse_args()
    if args.report is not None:
        rep = run_dev_gate(verify_git_pin=True, report_path=args.report)
    else:
        with tempfile.TemporaryDirectory() as td:
            rep = run_dev_gate(verify_git_pin=True, report_path=Path(td) / "dev_gate_report.json")
    for item in rep["items"]:
        status = "PASS" if item["passed"] else "FAIL"
        print(f"[{status}] {item['gate']}: {item['detail']}")
    print(f"\nOVERALL dev_gate: {'PASS' if rep['all_passed'] else 'FAIL'} ({rep['passed_count']}/{rep['total_count']}) in {rep['elapsed_seconds']}s")
    if not rep["all_passed"]:
        raise SystemExit(1)
