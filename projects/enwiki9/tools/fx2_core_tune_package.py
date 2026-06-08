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
    meta = {
        "id": candidate_id,
        "family": "fx2-core-tuning",
        "status": "candidate",
        "parent": "fx2_geometry_title_sort_dictcmix_xz_zlibpy_min_v1",
        "description": (
            "Title-order fx2 package with compile-time core predictor tuning "
            "knobs applied to the rebuilt local fx2-cmix substrate."
        ),
        "build": {
            "source": "projects/enwiki9/external/fx2-cmix",
            "command": "make CC=g++ CFLAGS_DEFINES='<defines>' clean cmix",
            "defines": defines,
            "wrapper_template": TITLE_TEMPLATE.name,
            "payload_files": files,
            "program_size": sum(files.values()),
            "payload_sha256": payload_hashes,
        },
        "hypothesis": (
            "Changing mixer adaptation, context-map capacity, LSTM rate, and "
            "SSE update rate can reduce archive bytes directly without storing "
            "new side information."
        ),
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
                            "compiler": "g++",
                        },
                        "continuous": knobs,
                        "structural": {},
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

    build_dir = BUILD_ROOT / args.id / "src"
    out_dir = PROGRAMS / args.id
    copy_source(args.source, build_dir)

    knobs = {
        "mixer_context_limit": args.mixer_context_limit,
        "mixer0_lr_scale": args.mixer0_lr_scale,
        "mixer1_lr_scale": args.mixer1_lr_scale,
        "lstm_lr_scale": args.lstm_lr_scale,
        "sse_wr_scale_ppm": args.sse_wr_scale_ppm,
    }
    defines = [
        "-DSEED=923",
        "-DUPDATE_LIMIT=3000",
        f"-DFX2_MIXER_CONTEXT_LIMIT={args.mixer_context_limit}",
        f"-DFX2_MIXER0_LR_SCALE={args.mixer0_lr_scale}f",
        f"-DFX2_MIXER1_LR_SCALE={args.mixer1_lr_scale}f",
        f"-DFX2_LSTM_LR_SCALE={args.lstm_lr_scale}f",
        f"-DFX2_SSE_WR_SCALE_PPM={args.sse_wr_scale_ppm}",
    ]
    if not args.no_build:
        run(
            [
                "make",
                "CC=g++",
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
