#!/usr/bin/env python3
"""Frozen sealed-evaluation scorer for PREREGISTRATION_DEPTH1.md.

Compares frozen Arm 3 (Depth-1 Frames, D=1) vs frozen Arm 2 (Context AST, D=0) on an
unseen fresh-code repository manifest WITHOUT retraining any weights, pools, or frames.

Reads ONLY the frozen headers:
  - frozen/arm2_context_ast.header.a2bits
  - frozen/arm3_depth1_frames.header.a2bits
verifies their exact byte identity, encodes every file in the supplied manifest (keeping
every unsupported file in the denominator via explicit charged RAW_FALLBACK), decodes both
archives independently via independent_decode.py + js_normalize_ast.mjs, and writes all
results strictly under --out <dir>. Never modifies any tracked file in the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import resource
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

import ast_frames
import codec
import independent_decode

HERE = Path(__file__).resolve().parent
BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_SEED = 20261127
PASS_BAR_PCT = -1.0


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def peak_rss_mb() -> float:
    raw = max(
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
    )
    return round(raw / (1024.0 * 1024.0) if sys.platform == "darwin" else raw / 1024.0, 2)


def _dict_tpl_to_tuple(tpl: dict) -> tuple:
    kind = tpl["kind"]
    if kind == "HOLE":
        return ("HOLE", tpl["group"], tpl["ctx"])
    if kind == "CALL":
        return ("CALL", tpl["fid"], tpl["group"], tpl["sub_shift"], tuple(_dict_tpl_to_tuple(a) for a in tpl["args"]))
    grp = tpl["group"]
    tag = tpl["tag"]
    atoms = tpl["atoms"]
    if grp == "STMT" and tag == "VarDecl":
        # Convert independent_decode's (kind, has_init) back to codec's (kind, (has_init_int,), True)
        vkind, has_init = atoms
        atoms = (vkind, (1 if has_init else 0,), True)
    children = tuple(_dict_tpl_to_tuple(c) for c in tpl["children"])
    return ("NODE", grp, tag, atoms, children)


def load_frozen_model(header_path: Path, arm_name: str) -> codec.AstCodecModel:
    """Reconstruct an exact AstCodecModel purely from a frozen A2F1 CodecKind=1 header file
    and assert byte-for-byte header identity."""
    t0 = time.perf_counter()
    buf = header_path.read_bytes()
    if len(buf) < 6 or buf[:4] != codec.MAGIC:
        raise ValueError(f"Invalid magic in frozen header {header_path}")
    codec_kind = buf[4]
    max_depth = buf[5]
    if codec_kind != 1:
        raise ValueError(f"Expected CodecKind=1, got {codec_kind}")
    pos = 6

    pool_lists = []
    for _ in range(5):
        cnt, pos = independent_decode.read_varint(buf, pos)
        lst = []
        for _ in range(cnt):
            s, pos = independent_decode.read_ustr(buf, pos)
            lst.append(s)
        pool_lists.append(lst)
    pools = ast_frames.Pools(*pool_lists)
    pools_dict = {"prop": pool_lists[0], "free": pool_lists[1], "bind": pool_lists[2], "num": pool_lists[3], "str": pool_lists[4]}

    has_frames = max_depth >= 1
    specs = ast_frames.all_base_context_specs(pools, has_frames=has_frames)
    weights: dict[str, list[int]] = {}
    cums: dict[str, list[int]] = {}
    for ctx, sz in specs:
        cum, pos = independent_decode.read_table(buf, pos, sz)
        cums[ctx] = cum
        weights[ctx] = [cum[i + 1] - cum[i] for i in range(sz)]

    frames: list[ast_frames.FrameDef] = []
    if has_frames:
        f_e, pos = independent_decode.read_varint(buf, pos)
        f_s, pos = independent_decode.read_varint(buf, pos)
        if f_e > 0:
            cum, pos = independent_decode.read_table(buf, pos, f_e)
            cums["EXPR_FRAME_ID"] = cum
            weights["EXPR_FRAME_ID"] = [cum[i + 1] - cum[i] for i in range(f_e)]
        if f_s > 0:
            cum, pos = independent_decode.read_table(buf, pos, f_s)
            cums["STMT_FRAME_ID"] = cum
            weights["STMT_FRAME_ID"] = [cum[i + 1] - cum[i] for i in range(f_s)]
        cum, pos = independent_decode.read_table(buf, pos, 8)
        cums["REG_SHIFT"] = cum
        weights["REG_SHIFT"] = [cum[i + 1] - cum[i] for i in range(8)]
        dm_k = 3 if max_depth >= 2 else 2
        dm_cum, pos = independent_decode.read_table(buf, pos, dm_k)
        def_mode_w = [dm_cum[i + 1] - dm_cum[i] for i in range(dm_k)]
        weights["DEF_MODE"] = def_mode_w
        def_len, pos = independent_decode.read_varint(buf, pos)
        def_blob = buf[pos:pos + def_len]
        pos += def_len
        expr_f, stmt_f = independent_decode.decode_frame_definitions(def_blob, f_e, f_s, max_depth, cums, def_mode_w, pools_dict)
        # Re-read exact topological group order from def_blob so re-serialization is byte-identical
        dec_ord = independent_decode.ArithmeticDecoder(def_blob)
        # Note: for max_depth == 1, frames are independent so exact serialization order is preserved
        # directly by decoding group bits in order using a helper that mirrors decode_frame_definitions:
        frames_ordered_raw = _decode_frames_preserving_order(def_blob, f_e, f_s, max_depth, cums, def_mode_w, pools_dict)
        by_id: dict[tuple[str, int], ast_frames.FrameDef] = {}
        for order_idx, frec in enumerate(frames_ordered_raw):
            tpl = _dict_tpl_to_tuple(frec["tpl"])
            flat_tpl = ast_frames.tpl_expand_to_flat(tpl, by_id, 0)
            fd = ast_frames.FrameDef(
                group=frec["group"],
                fid=frec["fid"],
                order_idx=order_idx,
                tpl=tpl,
                flat_tpl=flat_tpl,
                has_regs=frec["has_regs"],
                def_depth=frec["def_depth"],
                holes=list(frec["holes"]),
                root_tag=flat_tpl[2],
                base_node_count=ast_frames.tpl_node_count(flat_tpl),
            )
            frames.append(fd)
            by_id[(fd.group, fd.fid)] = fd

    if pos != len(buf):
        raise ValueError(f"Trailing bytes in frozen header {header_path}: pos={pos} != len={len(buf)}")

    rebuilt_hdr, breakdown = codec.build_ast_header(max_depth, pools, weights, frames)
    if rebuilt_hdr != buf:
        raise ValueError(f"Reconstructed header for {arm_name} differs from frozen header {header_path}")

    return codec.AstCodecModel(
        arm_name=arm_name,
        max_depth=max_depth,
        pools=pools,
        weights=weights,
        frames=frames,
        header_bytes=buf,
        header_breakdown=breakdown,
        train_seconds=time.perf_counter() - t0,
        op_counts={"frozen_header_load": 1},
    )


def _decode_frames_preserving_order(
    def_blob: bytes, f_e: int, f_s: int, max_depth: int,
    cums: dict[str, list[int]], def_mode_w: list[int], pools: dict[str, list[str]],
) -> list[dict]:
    """Decode frame definitions while keeping exact global serialization order."""
    # Reuse independent_decode.decode_frame_definitions for validation, and also track order.
    expr_f, stmt_f = independent_decode.decode_frame_definitions(def_blob, f_e, f_s, max_depth, cums, def_mode_w, pools)
    if not (expr_f and stmt_f):
        return expr_f + stmt_f
    # Replay group bits strictly using the exact same decoder to recover exact interleaved order.
    dec = independent_decode.ArithmeticDecoder(def_blob)
    helper = independent_decode.AstStreamDecoder(dec, cums, pools, max_depth, [], [])
    e_idx, s_idx = 0, 0
    ordered: list[dict] = []
    prev_elig: dict[str, list[dict]] = {"EXPR": [], "STMT": []}

    def make_cum(ws: list[int]) -> list[int]:
        out = [0]
        acc = 0
        for w in ws:
            acc += w
            out.append(acc)
        return out

    def skip_tpl(group: str, ctx: str, allow_hole: bool) -> None:
        elig = prev_elig[group] if max_depth >= 2 else []
        has_elig = bool(elig)
        if allow_hole and has_elig:
            mode = dec.decode(make_cum([def_mode_w[0], def_mode_w[1], def_mode_w[2]]))
        elif allow_hole:
            mode = dec.decode(make_cum([def_mode_w[0], def_mode_w[1]]))
        elif has_elig:
            mode = dec.decode(make_cum([def_mode_w[0], def_mode_w[2]]))
        else:
            mode = 0
        if mode == 1 and allow_hole:
            return
        if (mode == 2 and allow_hole) or (mode == 1 and not allow_hole and has_elig):
            pos = dec.decode_uniform(len(elig))
            sf = elig[pos]
            if sf["has_regs"]:
                dec.decode_uniform(8)
            for hg, hctx in sf["holes"]:
                skip_tpl(hg, hctx, True)
            return
        if group == "EXPR":
            tag = independent_decode.EXPR_TAGS[helper.sym(ctx)]
            if tag == "Reg8": helper.sym("REG_SLOT")
            elif tag == "RegFar": helper.read_uint()
            elif tag == "FreeId": helper.read_pooled("FREE_ID", "free")
            elif tag == "NumLit": helper.read_pooled("NUM_LIT", "num")
            elif tag == "StrLit": helper.read_pooled("STR_LIT", "str")
            elif tag in ("BoolFalse", "BoolTrue", "NullLit", "This", "Super"): pass
            elif tag == "Binary":
                helper.sym("BIN_OP"); skip_tpl("EXPR", "EXPR_BIN_L", True); skip_tpl("EXPR", "EXPR_BIN_R", True)
            elif tag == "Logical":
                helper.sym("LOG_OP"); skip_tpl("EXPR", "EXPR_BIN_L", True); skip_tpl("EXPR", "EXPR_BIN_R", True)
            elif tag == "Assign":
                helper.sym("ASN_OP"); skip_tpl("EXPR", "EXPR_LHS", True); skip_tpl("EXPR", "EXPR_INIT", True)
            elif tag == "Unary":
                helper.sym("UN_OP"); skip_tpl("EXPR", "EXPR_OTHER", True)
            elif tag == "Update":
                helper.sym("UPD_OP"); skip_tpl("EXPR", "EXPR_LHS", True)
            elif tag == "Cond":
                skip_tpl("EXPR", "EXPR_TEST", True); skip_tpl("EXPR", "EXPR_OTHER", True); skip_tpl("EXPR", "EXPR_OTHER", True)
            elif tag == "MemberProp":
                helper.sym("OPT_CHAIN"); skip_tpl("EXPR", "EXPR_OBJ", True); helper.read_pooled("PROP_NAME", "prop")
            elif tag == "MemberComp":
                helper.sym("OPT_CHAIN"); skip_tpl("EXPR", "EXPR_OBJ", True); skip_tpl("EXPR", "EXPR_PROP_IDX", True)
            elif tag == "Call":
                helper.sym("OPT_CHAIN"); skip_tpl("EXPR", "EXPR_CALLEE", True)
                na = helper.read_list_len("LIST_LEN_ARGS", 8)
                for _ in range(na): skip_tpl("EXPR", "EXPR_ARG", True)
            elif tag == "New":
                skip_tpl("EXPR", "EXPR_CALLEE", True)
                na = helper.read_list_len("LIST_LEN_ARGS", 8)
                for _ in range(na): skip_tpl("EXPR", "EXPR_ARG", True)
            elif tag == "ArrayExpr":
                ne = helper.read_list_len("LIST_LEN_ARGS", 8)
                for _ in range(ne):
                    if helper.sym("OPT_FLAG"): skip_tpl("EXPR", "EXPR_OTHER", True)
            elif tag == "Sequence":
                ne = helper.read_list_len("LIST_LEN_ARGS", 8)
                for _ in range(ne): skip_tpl("EXPR", "EXPR_OTHER", True)
            elif tag == "Spread": skip_tpl("EXPR", "EXPR_ARG", True)
            elif tag == "Await": skip_tpl("EXPR", "EXPR_OTHER", True)
            return
        tag = independent_decode.STMT_TAGS[helper.sym(ctx)]
        if tag == "ExprStmt": skip_tpl("EXPR", "EXPR_STMT", True)
        elif tag == "VarDecl":
            helper.sym("VAR_KIND"); helper.read_list_len("LIST_LEN_DECL", 3); helper.sym("PAT_DECL")
            if helper.sym("OPT_INIT"): skip_tpl("EXPR", "EXPR_INIT", True)
        elif tag == "Block":
            ns = helper.read_list_len("LIST_LEN_STMT", 16)
            for _ in range(ns): skip_tpl("STMT", "STMT_BLOCK", True)
        elif tag == "If":
            skip_tpl("EXPR", "EXPR_TEST", True); skip_tpl("STMT", "STMT_BRANCH", True)
            if helper.sym("OPT_ELSE"): skip_tpl("STMT", "STMT_BRANCH", True)
        elif tag == "Return":
            if helper.sym("OPT_RET_ARG"): skip_tpl("EXPR", "EXPR_ARG", True)
        elif tag == "For":
            ik = helper.sym("FOR_INIT_KIND")
            if ik == 1: skip_tpl("STMT", "STMT_BLOCK", True)
            elif ik == 2: skip_tpl("EXPR", "EXPR_STMT", True)
            if helper.sym("OPT_FLAG"): skip_tpl("EXPR", "EXPR_TEST", True)
            if helper.sym("OPT_FLAG"): skip_tpl("EXPR", "EXPR_STMT", True)
            skip_tpl("STMT", "STMT_BRANCH", True)
        elif tag == "ForOf":
            helper.sym("OPT_FLAG"); ld = bool(helper.sym("OPT_FLAG"))
            skip_tpl("STMT" if ld else "EXPR", "STMT_BLOCK" if ld else "EXPR_LHS", True)
            skip_tpl("EXPR", "EXPR_OTHER", True); skip_tpl("STMT", "STMT_BRANCH", True)
        elif tag == "ForIn":
            ld = bool(helper.sym("OPT_FLAG"))
            skip_tpl("STMT" if ld else "EXPR", "STMT_BLOCK" if ld else "EXPR_LHS", True)
            skip_tpl("EXPR", "EXPR_OTHER", True); skip_tpl("STMT", "STMT_BRANCH", True)
        elif tag == "While":
            skip_tpl("EXPR", "EXPR_TEST", True); skip_tpl("STMT", "STMT_BRANCH", True)
        elif tag == "DoWhile":
            skip_tpl("STMT", "STMT_BRANCH", True); skip_tpl("EXPR", "EXPR_TEST", True)
        elif tag == "Throw": skip_tpl("EXPR", "EXPR_ARG", True)
        elif tag in ("Break", "Continue"):
            if helper.sym("OPT_FLAG"): helper.read_pooled("BIND_NAME", "bind")

    for _ in range(f_e + f_s):
        g_bit = dec.decode_uniform(2)
        group = "EXPR" if g_bit == 0 else "STMT"
        skip_tpl(group, "EXPR_OTHER" if group == "EXPR" else "STMT_BLOCK", False)
        if group == "EXPR":
            frec = expr_f[e_idx]; e_idx += 1
        else:
            frec = stmt_f[s_idx]; s_idx += 1
        ordered.append(frec)
        if frec["def_depth"] < max_depth:
            prev_elig[group].append(frec)
    return ordered


def score_manifest(manifest_path: Path, root_dir: Path, out_dir: Path) -> dict[str, Any]:
    """Score a fresh-code manifest (JSON: {'set': ..., 'files': [{'path', 'lineage'}]})
    strictly with frozen Arm 2 and Arm 3 headers and independent decoding."""
    t0 = time.perf_counter()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files_spec = manifest["files"]

    # Normalize via frozen js_normalize_ast.mjs (keeping all unsupported files in denominator!)
    t_norm0 = time.perf_counter()
    items = []
    for i, row in enumerate(files_spec):
        p = root_dir / row["path"]
        src = p.read_text(encoding="utf-8", errors="replace")
        items.append({"id": f"{i}:{row['path']}", "source": src})
    proc = subprocess.run(
        ["node", str(HERE / "js_normalize_ast.mjs"), "normalize"],
        input=json.dumps({"items": items}),
        capture_output=True,
        text=True,
        check=True,
    )
    norm_res = json.loads(proc.stdout)["results"]
    irs = []
    norm_bytes = []
    lineages = []
    supported = 0
    for row, res in zip(files_spec, norm_res):
        nb = res["normalized"].encode("utf-8")
        norm_bytes.append(nb)
        lineages.append(row["lineage"])
        if res["supported"]:
            supported += 1
            irs.append(ast_frames.json_ast_to_ir(res["ir"])[0])
        else:
            irs.append(None)
    t_norm = time.perf_counter() - t_norm0

    m2 = load_frozen_model(HERE / "frozen" / "arm2_context_ast.header.a2bits", "arm2_context_ast")
    m3 = load_frozen_model(HERE / "frozen" / "arm3_depth1_frames.header.a2bits", "arm3_depth1_frames")

    out_dir.mkdir(parents=True, exist_ok=True)
    enc = {}
    dec = {}
    for name, m in (("arm2_context_ast", m2), ("arm3_depth1_frames", m3)):
        er = codec.encode_ast_arm(m, irs, norm_bytes)
        enc[name] = er
        arch_path = out_dir / f"{name}.a2bits"
        arch_path.write_bytes(er["archive"])
        dr = independent_decode.decode_archive(arch_path.read_bytes())
        dec[name] = dr
        if dr["file_count"] != len(norm_bytes) or any(a != b for a, b in zip(dr["files"], norm_bytes)):
            raise AssertionError(f"FIDELITY FAILURE: {name} did not decode 100% byte-for-byte!")

    # Paired repository-lineage bootstrap (10,000 resamples, seed=20261127)
    lin2: dict[str, float] = defaultdict(float)
    lin3: dict[str, float] = defaultdict(float)
    for l, b2, b3 in zip(lineages, enc["arm2_context_ast"]["per_file_est_bits"], enc["arm3_depth1_frames"]["per_file_est_bits"]):
        lin2[l] += b2
        lin3[l] += b3
    keys = sorted(lin2.keys())
    a2 = np.array([lin2[k] for k in keys], dtype=np.float64)
    a3 = np.array([lin3[k] for k in keys], dtype=np.float64)
    h2 = float(enc["arm2_context_ast"]["header_bits"])
    h3 = float(enc["arm3_depth1_frames"]["header_bits"])
    c2 = enc["arm2_context_ast"]["complete_bits"]
    c3 = enc["arm3_depth1_frames"]["complete_bits"]
    if a2.sum() > 0:
        a2 *= (c2 - h2) / a2.sum()
    if a3.sum() > 0:
        a3 *= (c3 - h3) / a3.sum()
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    idx = rng.integers(0, len(keys), size=(BOOTSTRAP_SAMPLES, len(keys)))
    b2_boot = h2 + a2[idx].sum(axis=1)
    b3_boot = h3 + a3[idx].sum(axis=1)
    pct_boot = 100.0 * (b3_boot - b2_boot) / b2_boot
    point_pct = 100.0 * (c3 - c2) / c2
    ci_lo = float(np.percentile(pct_boot, 2.5))
    ci_hi = float(np.percentile(pct_boot, 97.5))

    fallback_files = len(files_spec) - supported
    fallback_bytes = sum(len(nb) for ir, nb in zip(irs, norm_bytes) if ir is None)
    total_norm_bytes = sum(len(nb) for nb in norm_bytes)
    p95_2 = float(np.percentile(dec["arm2_context_ast"]["stream_per_file_seconds"], 95)) * 1000.0
    p95_3 = float(np.percentile(dec["arm3_depth1_frames"]["stream_per_file_seconds"], 95)) * 1000.0

    killed = (
        point_pct > PASS_BAR_PCT
        or ci_hi > 0.0
        or (total_norm_bytes > 0 and (fallback_bytes / total_norm_bytes) > 0.25)
        or (p95_2 > 0 and p95_3 > 5.0 * p95_2)
    )
    passed = (point_pct <= PASS_BAR_PCT) and (ci_hi <= PASS_BAR_PCT) and (not killed)

    report = {
        "schema": "gamma.bits.a2.depth1_sealed_score.v1",
        "set": manifest.get("set", manifest_path.stem),
        "frozen_headers": {
            "arm2_context_ast": sha256_bytes(m2.header_bytes),
            "arm3_depth1_frames": sha256_bytes(m3.header_bytes),
        },
        "fidelity": {
            "files_total": len(files_spec),
            "lineages_total": len(keys),
            "ast_supported_files": supported,
            "raw_fallback_files": fallback_files,
            "raw_fallback_byte_pct": round(100.0 * fallback_bytes / max(1, total_norm_bytes), 4),
            "arm2_byte_exact": True,
            "arm3_byte_exact": True,
            "corrupt_decodes": 0,
        },
        "complete_bits": {
            "total_norm_bytes": total_norm_bytes,
            "arm2_complete_bits": c2,
            "arm2_header_bits": int(h2),
            "arm2_payload_bits": enc["arm2_context_ast"]["payload_bits"],
            "arm3_complete_bits": c3,
            "arm3_header_bits": int(h3),
            "arm3_payload_bits": enc["arm3_depth1_frames"]["payload_bits"],
            "delta_complete_bits": c3 - c2,
            "delta_complete_pct": round(point_pct, 4),
            "ci95_pct": [round(ci_lo, 4), round(ci_hi, 4)],
            "verdict": "PASS" if passed else ("KILL" if killed else "INCONCLUSIVE_CI_CROSSED_BAR"),
        },
        "measured_work": {
            "platform": platform.platform(),
            "normalize_seconds": round(t_norm, 4),
            "total_seconds": round(time.perf_counter() - t0, 4),
            "peak_rss_mb": peak_rss_mb(),
            "arm2_encode_seconds": round(enc["arm2_context_ast"]["encode_seconds"], 4),
            "arm3_encode_seconds": round(enc["arm3_depth1_frames"]["encode_seconds"], 4),
            "arm2_decode_seconds": round(dec["arm2_context_ast"]["decode_seconds"], 4),
            "arm3_decode_seconds": round(dec["arm3_depth1_frames"]["decode_seconds"], 4),
            "arm2_decode_p95_ms": round(p95_2, 4),
            "arm3_decode_p95_ms": round(p95_3, 4),
            "arm3_shift_evals": enc["arm3_depth1_frames"]["op_counts"]["shift_evaluations"],
            "arm3_frame_uses": enc["arm3_depth1_frames"]["frame_stats"]["frame_uses"],
        },
    }
    (out_dir / "sealed_score_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify-headers-only", action="store_true",
                    help="Read-only verification that frozen Arm 2 and Arm 3 headers parse and round-trip cleanly")
    ap.add_argument("--manifest", type=Path, help="Fresh-code set manifest JSON")
    ap.add_argument("--root", type=Path, help="Root directory for manifest file paths")
    ap.add_argument("--out", type=Path, help="Output directory (outside repo or scratch)")
    args = ap.parse_args()

    if args.verify_headers_only:
        m2 = load_frozen_model(HERE / "frozen" / "arm2_context_ast.header.a2bits", "arm2_context_ast")
        m3 = load_frozen_model(HERE / "frozen" / "arm3_depth1_frames.header.a2bits", "arm3_depth1_frames")
        print(json.dumps({
            "ok": True,
            "arm2_header_bytes": len(m2.header_bytes),
            "arm2_header_sha256": sha256_bytes(m2.header_bytes),
            "arm3_header_bytes": len(m3.header_bytes),
            "arm3_header_sha256": sha256_bytes(m3.header_bytes),
            "arm3_frames": len(m3.frames),
        }))
        return 0

    if not (args.manifest and args.root and args.out):
        ap.error("--manifest, --root, and --out are required unless --verify-headers-only is set")
    rep = score_manifest(args.manifest, args.root, args.out)
    print(json.dumps(rep["complete_bits"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
