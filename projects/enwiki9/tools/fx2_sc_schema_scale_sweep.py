#!/usr/bin/env python3
"""Build and measure FX2-SC schema-template scale variants.

This tool implements the immediate FX2_SC.md sweep:

  SIDECAR_SCHEMA_TEMPLATE_SCALE in [180, 260] step 10

Each scale is compiled from external/cmix21-sidecar with the raw-stream
SIDECAR_SCHEMA_TEMPLATE_ONLY path, packaged as a normal programs/<id>
candidate, measured with lib/driver.py, and summarized with archive/program/S
deltas against the recorded fx2 geometry frontier control when available.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIB = ROOT / "lib"
sys.path.insert(0, str(LIB))
import driver  # noqa: E402

EXTERNAL = ROOT / "external" / "cmix21-sidecar"
PROGRAMS = ROOT / "programs"
OUT_DEFAULT = ROOT / "results" / "fx2_sc_schema_scale_sweep"
DATA_DEFAULT = ROOT / "data" / "enwik9"
DICT_SOURCE = PROGRAMS / "fx2_structural_sidecar_v1" / "english.dic.gz"
WRAPPER_SOURCE = PROGRAMS / "fx2_schema_template_only_v1" / "program.py"

RECORDED_BASELINES = {
    10_000_000: {
        "program_id": "fx2_geometry_sort_dictcmix_xz_min_v1",
        "compressed_size": 1_642_858,
        "program_size": 183_761,
        "hutter_score": 1_826_619,
    },
    100_000_000: {
        "program_id": "fx2_geometry_sort_dictcmix_xz_min_v1",
        "compressed_size": 14_857_781,
        "program_size": 183_761,
        "hutter_score": 15_041_542,
    },
}

SOURCES = [
    "src/coder/decoder.cpp",
    "src/coder/encoder.cpp",
    "src/context-manager.cpp",
    "src/contexts/bit-context.cpp",
    "src/contexts/bracket-context.cpp",
    "src/contexts/combined-context.cpp",
    "src/contexts/context-hash.cpp",
    "src/contexts/indirect-hash.cpp",
    "src/contexts/interval-hash.cpp",
    "src/contexts/interval.cpp",
    "src/contexts/sparse.cpp",
    "src/mixer/byte-mixer.cpp",
    "src/mixer/lstm-layer.cpp",
    "src/mixer/lstm.cpp",
    "src/mixer/mixer-input.cpp",
    "src/mixer/mixer.cpp",
    "src/mixer/sigmoid.cpp",
    "src/mixer/sse.cpp",
    "src/models/bracket.cpp",
    "src/models/byte-model.cpp",
    "src/models/direct-hash.cpp",
    "src/models/direct.cpp",
    "src/models/indirect.cpp",
    "src/models/fxcmv1.cpp",
    "src/models/match.cpp",
    "src/models/paq8.cpp",
    "src/models/ppmd.cpp",
    "src/predictor.cpp",
    "src/preprocess/dictionary.cpp",
    "src/preprocess/preprocessor.cpp",
    "src/runner.cpp",
    "src/states/nonstationary.cpp",
    "src/states/run-map.cpp",
]


def ensure_prefix(data_path: pathlib.Path, size: int) -> pathlib.Path:
    out = data_path.with_name(f"{data_path.name}_{size}.bin")
    if out.exists() and out.stat().st_size == size:
        return out
    with data_path.open("rb") as src, out.open("wb") as dst:
        remaining = size
        while remaining:
            chunk = src.read(min(1 << 20, remaining))
            if not chunk:
                raise SystemExit(f"{data_path} ended before {size} bytes")
            dst.write(chunk)
            remaining -= len(chunk)
    return out


def scale_program_id(scale: int) -> str:
    return f"fx2_schema_template_s{scale}_v1"


def compile_binary(scale: int, build_dir: pathlib.Path, cxx: str) -> pathlib.Path:
    out = build_dir / f"cmix_schema_template_s{scale}"
    cmd = [
        cxx,
        "-std=c++14",
        "-Wall",
        "-Ofast",
        "-march=native",
        "-DSIDECAR_SCHEMA_TEMPLATE_ONLY",
        f"-DSIDECAR_SCHEMA_TEMPLATE_SCALE={scale}",
        *SOURCES,
        "-o",
        str(out),
    ]
    subprocess.run(cmd, cwd=EXTERNAL, check=True)
    return out


def gzip_deterministic(src: pathlib.Path, dst: pathlib.Path) -> None:
    with src.open("rb") as inp, dst.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            shutil.copyfileobj(inp, gz)


def package_program(scale: int, binary: pathlib.Path) -> str:
    program_id = scale_program_id(scale)
    dst = PROGRAMS / program_id
    dst.mkdir(parents=True, exist_ok=True)
    gzip_deterministic(binary, dst / "cmix.bin.gz")
    shutil.copy2(DICT_SOURCE, dst / "english.dic.gz")
    shutil.copy2(WRAPPER_SOURCE, dst / "program.py")
    meta = {
        "id": program_id,
        "description": (
            "FX2-SC raw-stream schema-template-only sidecar ablation with "
            f"SIDECAR_SCHEMA_TEMPLATE_SCALE={scale}."
        ),
        "added": "2026-06-06",
        "deps": ["C++ runtime for bundled cmix/fx2 binary"],
        "source_tree": "external/cmix21-sidecar",
        "build_flags": (
            "-DSIDECAR_SCHEMA_TEMPLATE_ONLY "
            f"-DSIDECAR_SCHEMA_TEMPLATE_SCALE={scale}"
        ),
        "fx2_sc_concepts": ["raw_stream_preserved", "schema_template_ctx"],
    }
    (dst / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return program_id


def write_jsonl(path: pathlib.Path, row: dict) -> None:
    with path.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def refresh_wrapper(program_id: str) -> None:
    dst = PROGRAMS / program_id / "program.py"
    if not dst.parent.exists():
        raise SystemExit(f"program missing: {dst.parent}")
    shutil.copy2(WRAPPER_SOURCE, dst)


def measure(
    program_id: str,
    data_path: pathlib.Path,
    scale: int,
    as_limit_bytes: int | None,
) -> dict:
    prior_limit = os.environ.get("FX2_SC_AS_LIMIT_BYTES")
    if as_limit_bytes:
        os.environ["FX2_SC_AS_LIMIT_BYTES"] = str(as_limit_bytes)
    else:
        os.environ.pop("FX2_SC_AS_LIMIT_BYTES", None)
    try:
        row = driver.run(program_id, data_path, None, False)
        row["scale"] = scale
        row["error"] = None
    except Exception as exc:
        row = {
            "program_id": program_id,
            "data_path": str(data_path),
            "data_size": data_path.stat().st_size,
            "scale": scale,
            "roundtrip_ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        if prior_limit is None:
            os.environ.pop("FX2_SC_AS_LIMIT_BYTES", None)
        else:
            os.environ["FX2_SC_AS_LIMIT_BYTES"] = prior_limit
    if as_limit_bytes:
        row["as_limit_bytes"] = as_limit_bytes
    baseline = RECORDED_BASELINES.get(int(row["data_size"]))
    if baseline and row.get("hutter_score") is not None:
        row["baseline"] = baseline
        row["ledger"] = {
            "archive_delta": baseline["compressed_size"] - row["compressed_size"],
            "program_delta": row["program_size"] - baseline["program_size"],
            "score_delta": baseline["hutter_score"] - row["hutter_score"],
            "verdict": (
                "PREPROCESSOR_WINS"
                if baseline["hutter_score"] - row["hutter_score"] > 0
                else "PREPROCESSOR_LOSES"
            ),
        }
    return row


def summarize(rows: Iterable[dict], out_dir: pathlib.Path) -> None:
    rows = list(rows)
    valid = [row for row in rows if row.get("roundtrip_ok") and row.get("hutter_score")]
    valid.sort(key=lambda row: (row["data_size"], row["hutter_score"]))
    lines = ["# FX2-SC Schema Template Scale Sweep", ""]
    lines.append("| scope | scale | program | hutter_score | archive | program_size | b/B | score_delta | verdict |")
    lines.append("|---:|---:|---|---:|---:|---:|---:|---:|---|")
    for row in valid:
        ledger = row.get("ledger", {})
        lines.append(
            f"| {row['data_size']} | {row['scale']} | `{row['program_id']}` | "
            f"{row['hutter_score']} | {row['compressed_size']} | "
            f"{row['program_size']} | {row['bits_per_byte']} | "
            f"{ledger.get('score_delta', '')} | {ledger.get('verdict', '')} |"
        )
    failed = [
        row for row in rows
        if row.get("measured") is not False and not row.get("roundtrip_ok")
    ]
    if failed:
        lines.append("")
        lines.append("Failures:")
        for row in failed:
            lines.append(f"- scale {row.get('scale')}: `{row.get('program_id')}` {row.get('error')}")
    packaged = [row for row in rows if row.get("measured") is False]
    if packaged:
        lines.append("")
        lines.append("Packaged without measurement:")
        for row in sorted(packaged, key=lambda item: item["scale"]):
            lines.append(f"- scale {row['scale']}: `{row['program_id']}`")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")


def parse_scales(text: str) -> list[int]:
    if ":" in text:
        start, stop, step = (int(x) for x in text.split(":"))
        return list(range(start, stop + 1, step))
    return [int(x) for x in text.split(",") if x]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=pathlib.Path, default=DATA_DEFAULT)
    parser.add_argument("--out-dir", type=pathlib.Path, default=OUT_DEFAULT)
    parser.add_argument("--build-dir", type=pathlib.Path, default=ROOT / "build" / "fx2_sc_schema_scale")
    parser.add_argument("--scales", default="180:260:10")
    parser.add_argument("--scope-size", type=int, default=10_000_000)
    parser.add_argument("--cxx", default="g++")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-measure", action="store_true")
    parser.add_argument("--refresh-wrapper", action="store_true")
    parser.add_argument("--as-limit-bytes", type=int, default=10_000_000_000)
    args = parser.parse_args()

    if not args.data.exists():
        raise SystemExit(f"data missing: {args.data}")
    if not DICT_SOURCE.exists():
        raise SystemExit(f"dictionary missing: {DICT_SOURCE}")
    if not WRAPPER_SOURCE.exists():
        raise SystemExit(f"wrapper missing: {WRAPPER_SOURCE}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.build_dir.mkdir(parents=True, exist_ok=True)
    jsonl = args.out_dir / "runs.jsonl"
    if jsonl.exists():
        jsonl.unlink()
    data_path = None if args.skip_measure else ensure_prefix(args.data, args.scope_size)
    rows: list[dict] = []
    for scale in parse_scales(args.scales):
        program_id = scale_program_id(scale)
        if not args.skip_build:
            print(f"[build] scale={scale}", flush=True)
            binary = compile_binary(scale, args.build_dir, args.cxx)
            program_id = package_program(scale, binary)
        elif args.refresh_wrapper:
            refresh_wrapper(program_id)
        if args.skip_measure:
            row = {
                "program_id": program_id,
                "data_size": args.scope_size,
                "scale": scale,
                "built": not args.skip_build,
                "measured": False,
                "roundtrip_ok": None,
                "error": None,
            }
            rows.append(row)
            write_jsonl(jsonl, row)
            print(f"[package] scale={scale} program={program_id}", flush=True)
            summarize(rows, args.out_dir)
            continue
        assert data_path is not None
        print(f"[measure] scale={scale} program={program_id} data={data_path}", flush=True)
        row = measure(program_id, data_path, scale, args.as_limit_bytes)
        row["measured"] = True
        rows.append(row)
        write_jsonl(jsonl, row)
        if row.get("roundtrip_ok"):
            ledger = row.get("ledger", {})
            print(
                f"[measure] scale={scale} S={row['hutter_score']} "
                f"archive={row['compressed_size']} "
                f"score_delta={ledger.get('score_delta', '')}",
                flush=True,
            )
        else:
            print(f"[measure] scale={scale} ERROR {row.get('error')}", flush=True)
        summarize(rows, args.out_dir)
    print(f"[done] summary={args.out_dir / 'summary.md'} jsonl={jsonl}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
