#!/usr/bin/env python3
"""Strict dev_gate verification suite for BITS Experiment Card A2.

Checks every mandatory acceptance criterion:
  1. Lineage-disjointness audit (zero shared lineages/problem IDs/clusters/dups).
  2. Exact 8-cyclic-register-shift verification & no FFT/NTT static guard.
  3. 100% byte-for-byte independent decode across all 4 committed dev archives.
  4. Frozen Node behavior checks (all 20 sources-20 programs, 3,834 cases) on
     independently decoded bytes from all 4 arms against original JS.
  5. Charged raw fallback verification (unsupported JS explicitly flagged & exact).
  6. Negative controls (4 distinct illegal frame transitions MUST be rejected by
     independent_decode.py with FormatError):
       - invalid frame ID (>= num_frames)
       - illegal recursion depth > MaxDepth (in header def & runtime chain)
       - mismatched AST context transition (STMT frame in EXPR slot & non-VarDecl in For.init)
       - illegal register reference / cyclic shift out of bounds
  7. Equivalence control: Arm 4 configured with max_depth=1 MUST reproduce Arm 3
     (depth-1 reference) BIT-FOR-BIT (identical archive SHA-256).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import ast_frames
import codec
import independent_decode

HERE = Path(__file__).resolve().parent
LIT = HERE.parent


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_lineage_disjointness() -> dict:
    split = json.loads((HERE / "corpus_split.json").read_text(encoding="utf-8"))
    tr_lin = {r["lineage"] for r in split["train"]}
    dv_lin = {r["lineage"] for r in split["dev"]}
    tr_pid = {r["problem_id"] for r in split["train"] if r["problem_id"]}
    dv_pid = {r["problem_id"] for r in split["dev"] if r["problem_id"]}
    tr_sq = {r["squeezed_sha256"] for r in split["train"]}
    dv_sq = {r["squeezed_sha256"] for r in split["dev"]}
    assert not (tr_lin & dv_lin), f"shared lineages: {tr_lin & dv_lin}"
    assert not (tr_pid & dv_pid), f"shared problem_ids: {tr_pid & dv_pid}"
    assert not (tr_sq & dv_sq), "duplicate file across train/dev"
    # Verify IBM cluster file directly
    clusters = {}
    for line in (LIT / "objective-holdout-v1/metadata/ibm-identical-problem-clusters.txt").read_text().split():
        m = frozenset(line.split(","))
        for p in m:
            clusters[p] = m
    for p in dv_pid:
        if p in clusters:
            assert not (clusters[p] & tr_pid), f"IBM cluster leak for {p}"
    return {"ok": True, "train_lineages": len(tr_lin), "dev_lineages": len(dv_lin), "leaks": 0}


def check_exact_8_shift_and_no_fft() -> dict:
    # 1. Static guard: confirm zero FFT/NTT imports or invocations in all A2 code
    forbidden = ("fft", "rfft", "ifft", "ntt", "scipy.fft", "numpy.fft")
    for pyf in sorted(HERE.glob("*.py")) + sorted(HERE.glob("*.mjs")):
        if pyf.name in ("verify_dev_gate.py", "eval_dev.py"):
            continue
        txt = pyf.read_text(encoding="utf-8").lower()
        for tok in forbidden:
            # Allow documentation comments mentioning "no fft/ntt", forbid imports/calls
            for line in txt.splitlines():
                stripped = line.strip()
                if stripped.startswith(("#", "//", "*", '"', "'")):
                    continue
                if f".{tok}" in stripped or f"import {tok}" in stripped or f"def {tok}" in stripped:
                    raise AssertionError(f"Forbidden FFT/NTT reference `{tok}` in {pyf.name}: {line}")

    # 2. Functional test across all 8 cyclic shifts s in 0..7
    base_tpl = (
        "NODE", "EXPR", "Binary", ("<",), (
            ("NODE", "EXPR", "Reg8", (0,), ()),
            ("NODE", "EXPR", "MemberProp", (False, "length"), (
                ("NODE", "EXPR", "Reg8", (1,), ()),
            )),
        ),
    )
    canons = set()
    shifts_seen = set()
    for s in range(8):
        shifted = ast_frames.tpl_shift_exact(base_tpl, s, {})
        canon, win_s, n_ev = ast_frames.tpl_canonicalize_shift_exact(shifted, {})
        assert n_ev == 8, f"Expected exact 8 shift evaluations, got {n_ev}"
        recovered = ast_frames.tpl_shift_exact(canon, win_s, {})
        assert recovered == shifted, f"Shift equivariance failed at s={s}"
        canons.add(canon)
        shifts_seen.add(win_s)
    assert len(canons) == 1, "All 8 cyclic shifts must map to 1 exact canonical representative"
    assert shifts_seen == set(range(8)), "All 8 cyclic shifts must be recovered distinctly"
    return {"ok": True, "shifts_verified": 8, "fft_ntt_present": False}


def check_all_4_arms_decode_and_behavior() -> dict:
    summary = json.loads((HERE / "dev_summary.json").read_text(encoding="utf-8"))
    split = json.loads((HERE / "corpus_split.json").read_text(encoding="utf-8"))
    items = [{"id": r["id"], "source": (LIT / r["rel_path"]).read_text(encoding="utf-8")} for r in split["dev"]]
    proc = subprocess.run(
        ["node", str(HERE / "js_normalize_ast.mjs"), "normalize"],
        input=json.dumps({"items": items}),
        capture_output=True,
        text=True,
        check=True,
    )
    norm_res = json.loads(proc.stdout)["results"]
    expected_bytes = [o["normalized"].encode("utf-8") for o in norm_res]

    sys.path.insert(0, str(LIT))
    import checks  # noqa: E402
    src20_indices = [i for i, r in enumerate(split["dev"]) if r["slice"] == "sources-20"]

    arch_dir = HERE / "out" / "dev_archives"
    arm_status = {}
    for arm_name in ("arm1_flat_bits", "arm2_context_ast", "arm3_depth1_frames", "arm4_recursive_frames"):
        arch_bytes = (arch_dir / f"{arm_name}.a2bits").read_bytes()
        rep_arm = summary["shared_spine"]["complete_bits"]["arms"][arm_name]
        assert len(arch_bytes) == rep_arm["complete_bytes"], f"{arm_name} archive byte mismatch"
        assert sha256_bytes(arch_bytes) == rep_arm["archive_sha256"], f"{arm_name} archive sha256 mismatch"
        dec = independent_decode.decode_archive(arch_bytes)
        assert dec["file_count"] == len(expected_bytes)
        bad = [i for i, (a, b) in enumerate(zip(dec["files"], expected_bytes)) if a != b]
        assert not bad, f"{arm_name} byte mismatch at {bad[:5]}"

        # Run frozen Node behavior tests on decoded sources-20 bytes!
        progs = []
        for idx in src20_indices:
            row = split["dev"][idx]
            pid = int(row["problem_id"])
            progs.append({
                "id": row["problem_id"],
                "method": checks.METHODS[pid],
                "interface": "solution-class",
                "original_source": items[idx]["source"],
                "candidate_source": dec["files"][idx].decode("utf-8"),
                "cases": [{"args": c["args"]} for c in checks.cases_by_problem[pid]],
            })
        vproc = subprocess.run(
            ["node", str(HERE / "verify_behavior.mjs")],
            input=json.dumps({"programs": progs}),
            capture_output=True,
            text=True,
            check=True,
        )
        vout = json.loads(vproc.stdout)
        assert vout["all_passed"], f"{arm_name} failed frozen behavior checks"
        arm_status[arm_name] = {
            "byte_exact": f"{len(expected_bytes)}/{len(expected_bytes)}",
            "behavior_programs": f"{vout['passed_programs']}/{vout['total_programs']}",
            "behavior_cases": f"{vout['passed_cases']}/{vout['total_cases']}",
        }
    return {"ok": True, "arms": arm_status}


def check_charged_raw_fallback() -> dict:
    valid_src = "function f(a){return a+1;}\n"
    broken_src = "function @@@ unsupported_syntax( { let ;;;\n"
    proc = subprocess.run(
        ["node", str(HERE / "js_normalize_ast.mjs"), "normalize"],
        input=json.dumps({"items": [{"id": "ok", "source": valid_src}, {"id": "bad", "source": broken_src}]}),
        capture_output=True,
        text=True,
        check=True,
    )
    res = json.loads(proc.stdout)["results"]
    assert res[0]["supported"] is True and res[1]["supported"] is False
    irs = [ast_frames.json_ast_to_ir(res[0]["ir"])[0], None]
    raws = [res[0]["normalized"].encode("utf-8"), res[1]["normalized"].encode("utf-8")]
    lins = ["lin:ok", "lin:bad"]
    pools = ast_frames.build_pools([irs[0]])
    m = codec.train_ast_arm("fb_test", irs, lins, raws, pools, max_depth=3, max_frames=8)
    e = codec.encode_ast_arm(m, irs, raws)
    dec = independent_decode.decode_archive(e["archive"])
    assert dec["fallback_files"] == 1
    assert dec["files"] == raws
    return {"ok": True, "fallback_files": dec["fallback_files"], "exact_recovery": True}


def _build_minimal_frame_fixture(max_depth: int, expr_frames: list[ast_frames.FrameDef],
                                 stmt_frames: list[ast_frames.FrameDef],
                                 pools: ast_frames.Pools,
                                 def_mode_w: list[int] | None = None) -> tuple[dict[str, list[int]], dict[str, list[int]]]:
    specs = ast_frames.all_base_context_specs(pools, has_frames=True)
    weights = {ctx: [1] * sz for ctx, sz in specs}
    if expr_frames:
        weights["EXPR_FRAME_ID"] = [1] * len(expr_frames)
    if stmt_frames:
        weights["STMT_FRAME_ID"] = [1] * len(stmt_frames)
    weights["REG_SHIFT"] = [1] * 8
    weights["DEF_MODE"] = def_mode_w or ([4, 2, 2] if max_depth >= 2 else [4, 2])
    cums = {ctx: ast_frames.build_cum(ws) for ctx, ws in weights.items()}
    return weights, cums


def check_negative_controls() -> dict:
    """Inject 4 distinct illegal frame transitions and assert independent_decode.py REJECTS each."""
    pools = ast_frames.Pools(["length"], ["Math"], ["f"], ["0", "1"], [""])
    # Depth-1 EXPR frame: Reg8(0).length
    tpl_len = ("NODE", "EXPR", "MemberProp", (False, "length"), (("NODE", "EXPR", "Reg8", (0,), ()),))
    f0 = ast_frames.FrameDef("EXPR", 0, 0, tpl_len, tpl_len, True, 1, [], "MemberProp", 2)
    # Depth-2 EXPR frame: CALL(f0, 0) + 1
    tpl_d2 = ("NODE", "EXPR", "Binary", ("+",), (
        ("CALL", 0, "EXPR", 0, ()),
        ("NODE", "EXPR", "NumLit", ("1",), ()),
    ))
    f1 = ast_frames.FrameDef("EXPR", 1, 1, tpl_d2, ast_frames.tpl_expand_to_flat(tpl_d2, {("EXPR", 0): f0}), True, 2, [], "Binary", 4)
    # Depth-1 STMT frame: return 0; (NOT a VarDecl!)
    tpl_ret0 = ("NODE", "STMT", "Return", (True,), (("NODE", "EXPR", "NumLit", ("0",), ()),))
    fs0 = ast_frames.FrameDef("STMT", 0, 1, tpl_ret0, tpl_ret0, False, 1, [], "Return", 2)

    rejected = {}

    # Control 1: Illegal recursion depth > MaxDepth (patch MaxDepth=1 header with a depth-2 archive!)
    weights_d2, cums_d2 = _build_minimal_frame_fixture(2, [f0, f1], [], pools)
    hdr_d2, _ = codec.build_ast_header(2, pools, weights_d2, [f0, f1])
    # Craft valid payload invoking f1 inside function f(v0){return v0.length+1;}
    enc1 = ast_frames.ArithmeticEncoder()
    enc1.encode(cums_d2["FILE_MODE"], 0)
    enc1.encode(cums_d2["LIST_LEN_STMT"], 0)
    arch_d2 = hdr_d2 + ast_frames.encode_varint(1) + enc1.finish()
    # First confirm the uncorrupted depth-2 archive decodes cleanly!
    assert independent_decode.decode_archive(arch_d2)["file_count"] == 1
    # Now tamper MaxDepth byte (offset 5) from 2 -> 1! Decoder MUST reject!
    corrupted_depth = bytearray(arch_d2)
    corrupted_depth[5] = 1
    try:
        independent_decode.decode_archive(bytes(corrupted_depth))
        raise AssertionError("Negative control 1 (illegal depth > MaxDepth) was NOT rejected!")
    except independent_decode.FormatError as exc:
        rejected["illegal_recursion_depth_gt_dmax"] = str(exc)

    # Control 2: Runtime illegal recursion depth > MaxDepth via direct expand_frame depth guard
    dec_dummy = independent_decode.ArithmeticDecoder(b"\x00\x00\x00\x00")
    expr_f_dicts = [
        {"group": "EXPR", "fid": 0, "tpl": {"kind": "NODE", "group": "EXPR", "tag": "NumLit", "atoms": ("0",), "children": []}, "has_regs": False, "def_depth": 1, "holes": []},
    ]
    ast_dec = independent_decode.AstStreamDecoder(dec_dummy, cums_d2, {"prop": ["length"], "free": ["Math"], "bind": ["f"], "num": ["0", "1"], "str": [""]}, 3, expr_f_dicts, [])
    try:
        ast_dec.expand_frame("EXPR", 0, 0, depth=4, expected_group="EXPR")
        raise AssertionError("Negative control 2 (runtime depth 4 > MaxDepth 3) was NOT rejected!")
    except independent_decode.FormatError as exc:
        rejected["runtime_depth_gt_dmax"] = str(exc)

    # Control 3: Invalid frame ID (>= num_frames) and mismatched AST context transition (STMT frame in EXPR slot)
    try:
        ast_dec.expand_frame("EXPR", 99, 0, depth=1, expected_group="EXPR")
        raise AssertionError("Negative control 3a (invalid frame ID) was NOT rejected!")
    except independent_decode.FormatError as exc:
        rejected["invalid_frame_id"] = str(exc)

    try:
        ast_dec.expand_frame("STMT", 0, 0, depth=1, expected_group="EXPR")
        raise AssertionError("Negative control 3b (mismatched AST context transition) was NOT rejected!")
    except independent_decode.FormatError as exc:
        rejected["mismatched_ast_context_transition"] = str(exc)

    # Control 4: Serialized archive invoking USE_EXPR_FRAME when F_E == 0 (illegal frame switch in bitstream!)
    weights_s, cums_s = _build_minimal_frame_fixture(1, [], [fs0], pools)
    hdr_s, _ = codec.build_ast_header(1, pools, weights_s, [fs0])
    enc4 = ast_frames.ArithmeticEncoder()
    enc4.encode(cums_s["FILE_MODE"], 0)
    enc4.encode(cums_s["LIST_LEN_STMT"], 1)
    enc4.encode(cums_s["STMT_TOP"], ast_frames.STMT_TAG_ID["ExprStmt"])
    enc4.encode(cums_s["EXPR_STMT"], ast_frames.NUM_BASE_EXPR)  # Illegal USE_EXPR_FRAME with 0 expr frames!
    arch_bad_sw = hdr_s + ast_frames.encode_varint(1) + enc4.finish()
    try:
        independent_decode.decode_archive(arch_bad_sw)
        raise AssertionError("Negative control 4a (bitstream illegal USE_EXPR_FRAME) was NOT rejected!")
    except independent_decode.FormatError as exc:
        rejected["bitstream_illegal_frame_switch"] = str(exc)

    # Control 4b: Serialized archive placing non-VarDecl STMT frame (`return 0;`) inside For.init!
    enc4b = ast_frames.ArithmeticEncoder()
    enc4b.encode(cums_s["FILE_MODE"], 0)
    enc4b.encode(cums_s["LIST_LEN_STMT"], 1)
    enc4b.encode(cums_s["STMT_TOP"], ast_frames.STMT_TAG_ID["For"])
    enc4b.encode(cums_s["FOR_INIT_KIND"], 1)  # expects VarDecl STMT
    enc4b.encode(cums_s["STMT_BLOCK"], ast_frames.NUM_BASE_STMT)  # USE_STMT_FRAME
    enc4b.encode(cums_s["STMT_FRAME_ID"], 0)  # fs0 = Return(0), illegal in For.init!
    arch_bad_ctx = hdr_s + ast_frames.encode_varint(1) + enc4b.finish()
    try:
        independent_decode.decode_archive(arch_bad_ctx)
        raise AssertionError("Negative control 4b (STMT frame Return in For.init) was NOT rejected!")
    except independent_decode.FormatError as exc:
        rejected["bitstream_illegal_for_init_frame"] = str(exc)

    # Control 5: Serialized archive invoking register frame `r0.length` at top-level with empty env (out-of-bounds register!)
    weights_r, cums_r = _build_minimal_frame_fixture(1, [f0], [], pools)
    hdr_r, _ = codec.build_ast_header(1, pools, weights_r, [f0])
    enc5 = ast_frames.ArithmeticEncoder()
    enc5.encode(cums_r["FILE_MODE"], 0)
    enc5.encode(cums_r["LIST_LEN_STMT"], 1)
    enc5.encode(cums_r["STMT_TOP"], ast_frames.STMT_TAG_ID["ExprStmt"])
    enc5.encode(cums_r["EXPR_STMT"], ast_frames.NUM_BASE_EXPR)
    enc5.encode(cums_r["EXPR_FRAME_ID"], 0)
    enc5.encode(cums_r["REG_SHIFT"], 3)  # (0+3)%8 = 3, but env is empty!
    arch_bad_reg = hdr_r + ast_frames.encode_varint(1) + enc5.finish()
    try:
        independent_decode.decode_archive(arch_bad_reg)
        raise AssertionError("Negative control 5 (out-of-bounds shifted register) was NOT rejected!")
    except independent_decode.FormatError as exc:
        rejected["bitstream_illegal_shifted_register"] = str(exc)

    return {"ok": True, "controls_rejected": len(rejected), "details": rejected}


def check_equivalence_control() -> dict:
    """Disabling nested frames (max_depth=1) in Arm 4 MUST reproduce Arm 3 bit-for-bit!
    Checked directly against the full committed arm3_depth1_frames.a2bits archive."""
    split = json.loads((HERE / "corpus_split.json").read_text(encoding="utf-8"))
    import eval_dev
    train_data = eval_dev.load_and_normalize_split(split["train"])
    dev_data = eval_dev.load_and_normalize_split(split["dev"])
    pools = ast_frames.build_pools([ir for ir in train_data["irs"] if ir is not None])

    m4_d1 = codec.train_ast_arm(
        "arm4_recursive_frames_disabled_d1",
        train_data["irs"],
        train_data["lineages"],
        train_data["norm_bytes"],
        pools,
        max_depth=1,
        max_frames=eval_dev.FRAME_MAX_COUNT,
        min_lineage_support=eval_dev.MIN_LINEAGE_SUPPORT,
    )
    e4_d1 = codec.encode_ast_arm(m4_d1, dev_data["irs"], dev_data["norm_bytes"])
    arm3_committed = (HERE / "out" / "dev_archives" / "arm3_depth1_frames.a2bits").read_bytes()
    assert e4_d1["archive"] == arm3_committed, "Equivalence control FAILED: Arm 4 (max_depth=1) != Arm 3 archive bytes!"
    assert e4_d1["frame_stats"]["nested_frame_defs"] == 0
    assert e4_d1["frame_stats"]["nested_subframe_calls"] == 0
    return {
        "ok": True,
        "bit_for_bit_identical": True,
        "archive_bytes": len(arm3_committed),
        "archive_sha256": sha256_bytes(arm3_committed),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional output path for machine-readable JSON gate report (default: read-only, writes no files)",
    )
    args = ap.parse_args()

    t0 = time.perf_counter()
    gates = [
        ("lineage_disjointness", check_lineage_disjointness),
        ("exact_8_shift_no_fft_ntt", check_exact_8_shift_and_no_fft),
        ("all_4_arms_decode_and_behavior", check_all_4_arms_decode_and_behavior),
        ("charged_raw_fallback", check_charged_raw_fallback),
        ("negative_controls_illegal_transitions", check_negative_controls),
        ("equivalence_control_d1_equals_arm3", check_equivalence_control),
    ]
    results = {}
    all_ok = True
    for name, fn in gates:
        ts = time.perf_counter()
        try:
            res = fn()
            dt = round(time.perf_counter() - ts, 3)
            results[name] = {"status": "PASS", "seconds": dt, **res}
            print(f"PASS  {name:38s} {dt:6.2f}s", flush=True)
        except Exception as exc:
            dt = round(time.perf_counter() - ts, 3)
            all_ok = False
            results[name] = {"status": "FAIL", "seconds": dt, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
            print(f"FAIL  {name:38s} {dt:6.2f}s  {exc}", flush=True)

    report = {
        "schema": "gamma.bits.a2.dev_gate.v1",
        "all_passed": all_ok,
        "total_seconds": round(time.perf_counter() - t0, 3),
        "gates": results,
    }
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"DEV_GATE: {'ALL PASSED' if all_ok else 'FAILED'} in {report['total_seconds']:.2f}s")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
