#!/usr/bin/env python3
"""Build and package an fx2 core-tuning candidate.

This creates a score-honest candidate by rebuilding the local fx2-cmix source
with compile-time predictor knobs, compressing the resulting executable, and
dropping it into an existing wrapper template.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
PROGRAMS = ROOT / "programs"
BUILD_ROOT = ROOT / "build" / "fx2_core_tune"
SOURCE_DEFAULT = ROOT / "external" / "fx2-cmix"
TITLE_TEMPLATE = PROGRAMS / "fx2_geometry_title_sort_dictcmix_xz_zlibpy_min_v1"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args: list[str], cwd: pathlib.Path) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def copy_source(src: pathlib.Path, dst: pathlib.Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)

    def ignore(_dir: str, names: list[str]) -> set[str]:
        return {
            name
            for name in names
            if name
            in {
                ".git",
                "pgo_data",
                "cmix",
                "remap",
                "prof_comp",
                "prof_output",
                "run",
            }
            or name.endswith(".o")
        }

    shutil.copytree(src, dst, ignore=ignore)


def xz_bytes(data: bytes) -> bytes:
    return lzma.compress(
        data,
        format=lzma.FORMAT_XZ,
        check=lzma.CHECK_NONE,
        preset=9 | lzma.PRESET_EXTREME,
    )


def write_title_wrapper_candidate(
    *,
    candidate_id: str,
    build_dir: pathlib.Path,
    out_dir: pathlib.Path,
    compiler: str,
    defines: list[str],
    knobs: dict[str, Any],
) -> None:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    shutil.copy2(TITLE_TEMPLATE / "program.py", out_dir / "program.py")
    shutil.copy2(TITLE_TEMPLATE / "p", out_dir / "p")

    cmix = build_dir / "cmix"
    dictionary = build_dir / "dictionary" / "english.dic"
    if not cmix.exists():
        raise SystemExit(f"missing built cmix: {cmix}")
    if not dictionary.exists():
        raise SystemExit(f"missing dictionary: {dictionary}")

    (out_dir / "c").write_bytes(xz_bytes(cmix.read_bytes()))
    os.chmod(cmix, 0o755)
    run([str(cmix), "-c", str(dictionary), str(out_dir / "d")], cwd=build_dir)

    files = {
        child.name: child.stat().st_size
        for child in sorted(out_dir.iterdir())
        if child.is_file()
    }
    payload_hashes = {
        child.name: sha256(child)
        for child in sorted(out_dir.iterdir())
        if child.is_file()
    }
    if knobs.get("manifold_outer_sse"):
        family = "fx2-manifold-outer-sse"
        description = (
            "Title-order fx2 package with a fixed causal sphere-torus outer "
            "SSE correction compiled into the rebuilt local fx2-cmix substrate."
        )
        hypothesis = (
            "A decoder-recomputable manifold bucket over causal wiki/XML state "
            "can correct systematic fx2 residual bias after the native SSE "
            "without rewriting bytes or hard-splitting primary context tables."
        )
    elif knobs.get("typed_anchor_soft_sse"):
        family = "fx2-typed-anchor-soft-state"
        description = (
            "Title-order fx2 package with a narrow typed-anchor soft "
            "coordinate compiled into the rebuilt local fx2-cmix substrate."
        )
        hypothesis = (
            "Typed-anchor field and slot state can act as a weak learned "
            "fx2 coordinate without rewriting the byte stream or hard-mutating "
            "mature contexts."
        )
    else:
        family = "fx2-core-tuning"
        description = (
            "Title-order fx2 package with compile-time core predictor tuning "
            "knobs applied to the rebuilt local fx2-cmix substrate."
        )
        hypothesis = (
            "Changing mixer adaptation, context-map capacity, LSTM rate, and "
            "SSE update rate can reduce archive bytes directly without storing "
            "new side information."
        )
    meta = {
        "id": candidate_id,
        "family": family,
        "status": "candidate",
        "parent": "fx2_geometry_title_sort_dictcmix_xz_zlibpy_min_v1",
        "description": description,
        "build": {
            "source": "projects/enwiki9/external/fx2-cmix",
            "command": f"make CC={compiler} CFLAGS_DEFINES='<defines>' clean cmix",
            "defines": defines,
            "compiler": compiler,
            "wrapper_template": TITLE_TEMPLATE.name,
            "payload_files": files,
            "program_size": sum(files.values()),
            "payload_sha256": payload_hashes,
        },
        "hypothesis": hypothesis,
        "deps": [
            "stdlib:zlib",
            "C++ runtime for the bundled cmix/fx2 binary",
        ],
        "pgsg": {
            "nodes": [
                {
                    "id": "page_order",
                    "type": "transform",
                    "payload": {
                        "discrete": {"mode": "geometry_title"},
                        "continuous": {},
                        "structural": {},
                    },
                },
                {
                    "id": "core_tuning",
                    "type": "parameter_controller",
                    "payload": {
                        "discrete": {
                            "substrate": "fx2-cmix",
                            "compiler": compiler,
                        },
                        "continuous": knobs,
                        "structural": {},
                    },
                },
                {
                    "id": "typed_anchor_soft_state",
                    "type": "sidecar",
                    "payload": {
                        "discrete": {
                            "mode": "raw_stream_field_slot_soft_coordinate",
                            "enabled": bool(knobs.get("typed_anchor_soft_sse")),
                            "context_mode": knobs.get("typed_anchor_context_mode", 0),
                            "manifold_outer_sse": bool(knobs.get("manifold_outer_sse")),
                            "manifold_correction": knobs.get("manifold_correction", "kt"),
                        },
                        "continuous": {
                            "weight": knobs.get("typed_anchor_soft_sse_weight", 0.0),
                            "manifold_blend_ppm": knobs.get("manifold_blend_ppm", 0),
                        },
                        "structural": {
                            "state": [
                                "prediction_bucket",
                                "bit_prefix",
                                "field",
                                "slot",
                                "sphere_bucket",
                                "torus_bucket",
                            ]
                        },
                    },
                },
                {
                    "id": "backend",
                    "type": "codec",
                    "payload": {
                        "discrete": {
                            "codec": "fx2-cmix",
                            "dictionary_codec": "cmix_self_compressed",
                            "binary_codec": "xz_extreme_check_none",
                        },
                        "continuous": {},
                        "structural": {},
                    },
                },
            ],
            "edges": [
                {"from": "page_order", "to": "backend", "stream": "reordered_raw_xml"},
                {"from": "core_tuning", "to": "backend", "stream": "compiled_constants"},
                {
                    "from": "typed_anchor_soft_state",
                    "to": "backend",
                    "stream": "learned_internal_context",
                },
            ],
        },
        "measured": {},
        "verdict": "Unmeasured core-tuning candidate. Run Lane 0 gates before promotion.",
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="candidate id to create")
    parser.add_argument("--source", type=pathlib.Path, default=SOURCE_DEFAULT)
    parser.add_argument("--mixer-context-limit", type=int, default=10000)
    parser.add_argument("--mixer0-lr-scale", type=float, default=1.0)
    parser.add_argument("--mixer1-lr-scale", type=float, default=1.0)
    parser.add_argument("--lstm-lr-scale", type=float, default=1.0)
    parser.add_argument("--sse-wr-scale-ppm", type=int, default=1000)
    parser.add_argument("--mixer-decay-t0", type=int, default=1000000)
    parser.add_argument("--mixer-decay-t1", type=int, default=5000000)
    parser.add_argument("--mixer-decay-t2", type=int, default=25000000)
    parser.add_argument("--mixer-decay-p0", type=int, default=1000000)
    parser.add_argument("--mixer-decay-p1", type=int, default=700000)
    parser.add_argument("--mixer-decay-p2", type=int, default=300000)
    parser.add_argument("--mixer-decay-p3", type=int, default=200000)
    parser.add_argument("--typed-anchor-soft-sse", action="store_true")
    parser.add_argument("--typed-anchor-soft-sse-weight", type=float, default=0.0002)
    parser.add_argument("--typed-anchor-context-mode", type=int, default=0)
    parser.add_argument("--manifold-outer-sse", action="store_true")
    parser.add_argument("--manifold-correction", choices=["kt", "bias"], default="kt")
    parser.add_argument("--manifold-blend-ppm", type=int, default=50000)
    parser.add_argument("--manifold-p-buckets", type=int, default=32)
    parser.add_argument("--manifold-sphere-bins", type=int, default=4)
    parser.add_argument("--manifold-torus-bins", type=int, default=4)
    parser.add_argument("--manifold-pos-shift", type=int, default=10)
    parser.add_argument(
        "--extra-define",
        action="append",
        default=[],
        help="additional raw -D macro for search-selected manifold constants",
    )
    parser.add_argument("--compiler", default="g++")
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"source not found: {args.source}")
    if not TITLE_TEMPLATE.exists():
        raise SystemExit(f"title wrapper template not found: {TITLE_TEMPLATE}")
    if args.mixer_context_limit <= 0:
        raise SystemExit("--mixer-context-limit must be positive")
    if args.sse_wr_scale_ppm <= 0:
        raise SystemExit("--sse-wr-scale-ppm must be positive")
    decay_thresholds = [
        args.mixer_decay_t0,
        args.mixer_decay_t1,
        args.mixer_decay_t2,
    ]
    if any(value < 0 for value in decay_thresholds):
        raise SystemExit("--mixer-decay-t* values must be non-negative")
    if decay_thresholds != sorted(decay_thresholds):
        raise SystemExit("--mixer-decay-t* values must be sorted")
    decay_ppm = [
        args.mixer_decay_p0,
        args.mixer_decay_p1,
        args.mixer_decay_p2,
        args.mixer_decay_p3,
    ]
    if any(value < 0 for value in decay_ppm):
        raise SystemExit("--mixer-decay-p* values must be non-negative")
    if args.typed_anchor_soft_sse_weight < 0:
        raise SystemExit("--typed-anchor-soft-sse-weight must be non-negative")
    if args.typed_anchor_context_mode < 0 or args.typed_anchor_context_mode > 6:
        raise SystemExit("--typed-anchor-context-mode must be between 0 and 6")
    if args.manifold_blend_ppm < 0 or args.manifold_blend_ppm > 1000000:
        raise SystemExit("--manifold-blend-ppm must be between 0 and 1000000")
    if args.manifold_p_buckets <= 0:
        raise SystemExit("--manifold-p-buckets must be positive")
    if args.manifold_sphere_bins <= 0:
        raise SystemExit("--manifold-sphere-bins must be positive")
    if args.manifold_torus_bins <= 0:
        raise SystemExit("--manifold-torus-bins must be positive")
    if args.manifold_pos_shift < 0:
        raise SystemExit("--manifold-pos-shift must be non-negative")

    build_dir = BUILD_ROOT / args.id / "src"
    out_dir = PROGRAMS / args.id
    copy_source(args.source, build_dir)

    knobs = {
        "mixer_context_limit": args.mixer_context_limit,
        "mixer0_lr_scale": args.mixer0_lr_scale,
        "mixer1_lr_scale": args.mixer1_lr_scale,
        "lstm_lr_scale": args.lstm_lr_scale,
        "sse_wr_scale_ppm": args.sse_wr_scale_ppm,
        "mixer_decay_t0": args.mixer_decay_t0,
        "mixer_decay_t1": args.mixer_decay_t1,
        "mixer_decay_t2": args.mixer_decay_t2,
        "mixer_decay_p0": args.mixer_decay_p0,
        "mixer_decay_p1": args.mixer_decay_p1,
        "mixer_decay_p2": args.mixer_decay_p2,
        "mixer_decay_p3": args.mixer_decay_p3,
        "typed_anchor_soft_sse": args.typed_anchor_soft_sse,
        "typed_anchor_soft_sse_weight": args.typed_anchor_soft_sse_weight,
        "typed_anchor_context_mode": args.typed_anchor_context_mode,
        "manifold_outer_sse": args.manifold_outer_sse,
        "manifold_correction": args.manifold_correction,
        "manifold_blend_ppm": args.manifold_blend_ppm,
        "manifold_p_buckets": args.manifold_p_buckets,
        "manifold_sphere_bins": args.manifold_sphere_bins,
        "manifold_torus_bins": args.manifold_torus_bins,
        "manifold_pos_shift": args.manifold_pos_shift,
        "extra_defines": args.extra_define,
    }
    defines = [
        "-DSEED=923",
        "-DUPDATE_LIMIT=3000",
        f"-DFX2_MIXER_CONTEXT_LIMIT={args.mixer_context_limit}",
        f"-DFX2_MIXER0_LR_SCALE={args.mixer0_lr_scale}f",
        f"-DFX2_MIXER1_LR_SCALE={args.mixer1_lr_scale}f",
        f"-DFX2_LSTM_LR_SCALE={args.lstm_lr_scale}f",
        f"-DFX2_SSE_WR_SCALE_PPM={args.sse_wr_scale_ppm}",
        f"-DFX2_MIXER_DECAY_T0={args.mixer_decay_t0}ULL",
        f"-DFX2_MIXER_DECAY_T1={args.mixer_decay_t1}ULL",
        f"-DFX2_MIXER_DECAY_T2={args.mixer_decay_t2}ULL",
        f"-DFX2_MIXER_DECAY_P0={args.mixer_decay_p0}",
        f"-DFX2_MIXER_DECAY_P1={args.mixer_decay_p1}",
        f"-DFX2_MIXER_DECAY_P2={args.mixer_decay_p2}",
        f"-DFX2_MIXER_DECAY_P3={args.mixer_decay_p3}",
    ]
    if args.typed_anchor_soft_sse or args.manifold_outer_sse:
        defines.append("-DFX2_STRUCT_SIDECAR=5")
    if args.typed_anchor_soft_sse:
        defines.extend(
            [
                "-DFX2_TYPED_ANCHOR_SOFT_SSE=1",
                f"-DFX2_TYPED_ANCHOR_SOFT_SSE_WEIGHT={args.typed_anchor_soft_sse_weight}f",
                f"-DFX2_TYPED_ANCHOR_CONTEXT_MODE={args.typed_anchor_context_mode}",
            ]
        )
    if args.manifold_outer_sse:
        defines.extend(
            [
                "-DFX2_MANIFOLD_OUTER_SSE=1",
                f"-DFX2_MANIFOLD_BLEND_PPM={args.manifold_blend_ppm}u",
                f"-DFX2_MANIFOLD_P_BUCKETS={args.manifold_p_buckets}u",
                f"-DFX2_MANIFOLD_SPHERE_BINS={args.manifold_sphere_bins}u",
                f"-DFX2_MANIFOLD_TORUS_BINS={args.manifold_torus_bins}u",
                f"-DFX2_MANIFOLD_POS_SHIFT={args.manifold_pos_shift}",
            ]
        )
        if args.manifold_correction == "bias":
            defines.append("-DFX2_MANIFOLD_CORRECTION_BIAS=1")
    defines.extend(args.extra_define)
    if not args.no_build:
        run(
            [
                "make",
                f"CC={args.compiler}",
                "CFLAGS_DEFINES=" + " ".join(defines),
                "clean",
                "cmix",
            ],
            cwd=build_dir,
        )
        write_title_wrapper_candidate(
            candidate_id=args.id,
            build_dir=build_dir,
            out_dir=out_dir,
            compiler=args.compiler,
            defines=defines,
            knobs=knobs,
        )

    print(
        json.dumps(
            {
                "candidate_id": args.id,
                "build_dir": str(build_dir.relative_to(REPO_ROOT)),
                "program_dir": str(out_dir.relative_to(REPO_ROOT)),
                "defines": defines,
                "built": not args.no_build,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
