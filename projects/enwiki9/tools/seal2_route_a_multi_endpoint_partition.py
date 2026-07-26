#!/usr/bin/env python3
"""Measure paid page selection across aligned endpoint probability traces."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from endpoint428_page_prompt_shadow import prompt_segments, write_segments
from wrt_exact import detect_storage_header, parse_store


ROOT = Path(__file__).resolve().parents[1]
CPP = Path(__file__).with_suffix(".cpp")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
    }


def parse_expert(value: str) -> tuple[str, Path]:
    name, separator, raw_path = value.partition("=")
    if not separator or not name or not raw_path:
        raise argparse.ArgumentTypeError("expert must have NAME=PATH form")
    return name, Path(raw_path)


def compile_helper(binary: Path) -> list[str]:
    command = [
        "g++",
        "-O3",
        "-std=c++17",
        "-DNDEBUG",
        str(CPP),
        "-o",
        str(binary),
    ]
    subprocess.run(command, check=True, cwd=ROOT.parent.parent)
    return command


def run(args: argparse.Namespace) -> dict[str, Any]:
    experts = args.expert
    names = [name for name, _ in experts]
    if len(experts) < 2 or len(experts) > 16:
        raise RuntimeError("expert family must contain between two and sixteen traces")
    if len(set(names)) != len(names):
        raise RuntimeError("expert names must be unique")
    if args.baseline not in names:
        raise RuntimeError("baseline must name one supplied expert")
    baseline_index = names.index(args.baseline)

    parsed = parse_store(args.store, args.dictionary)
    raw = args.raw.read_bytes()
    if raw[: parsed.raw_length] != parsed.decoded:
        raise RuntimeError("WRT stream does not reconstruct the pinned raw population")
    stored = args.store.read_bytes()
    header_bytes = detect_storage_header(stored)
    segments = prompt_segments(parsed)

    with tempfile.TemporaryDirectory(prefix="route-a-multi-endpoint-") as temporary:
        temporary_path = Path(temporary)
        segment_path = temporary_path / "segments.bin"
        helper_path = temporary_path / "route_a_helper"
        helper_output = temporary_path / "helper.json"
        write_segments(segment_path, segments)
        compile_command = compile_helper(helper_path)
        helper_command = [
            str(helper_path),
            str(args.store.resolve()),
            str(header_bytes),
            str(segment_path),
            str(helper_output),
            str(baseline_index),
            *(str(path.resolve()) for _, path in experts),
        ]
        subprocess.run(helper_command, check=True, cwd=ROOT.parent.parent)
        exact = json.loads(helper_output.read_text())
        helper_sha256 = digest(helper_path)

    gross = exact["saved_bytes"]["ORACLE_GROSS"]
    paid = exact["saved_bytes"]["ORACLE_PAID"]
    fixed = exact["saved_bytes"]["ORACLE_FIXED_LABEL"]
    if gross < args.gross_gate_bytes:
        verdict = "retire_current_multi_endpoint_family_gross_gate_miss"
    elif max(paid, fixed) < args.net_gate_bytes:
        verdict = "retire_current_multi_endpoint_family_net_gate_miss"
    else:
        verdict = "mechanism_positive_requires_frozen_offset_transfer"

    source_bytes = CPP.stat().st_size + Path(__file__).stat().st_size
    return {
        "schema": "seal2_route_a_multi_endpoint_partition_v1",
        "candidate_id": "seal2_route_a_paid_predictor_partition_v1",
        "evidence_level": "causal_shadow",
        "trace_classification": args.trace_classification,
        "inputs": {
            "raw": artifact(args.raw),
            "wrt_store": artifact(args.store),
            "dictionary": artifact(args.dictionary),
            "experts": [
                {
                    "name": name,
                    "baseline": name == args.baseline,
                    "trace": artifact(path),
                }
                for name, path in experts
            ],
            "storage_header_bytes": header_bytes,
        },
        "scope": {
            "raw_bytes": parsed.raw_length,
            "wrt_stream_bytes": len(parsed.stream),
            "p1_rows": len(parsed.stream) * 8,
            "started_pages": parsed.decoded.count(b"<page>"),
            "promptable_pages": len(segments),
            "prompt_position": "after complete title and before selected body",
        },
        "controls": {
            "BASE": "strongest preserved phase-enhanced endpoint trajectory",
            "GLOBAL": "one expert selected only on page-index-mod-5 development pages",
            "ORACLE_GROSS": "whole-page best expert without label cost",
            "ORACLE_FIXED_LABEL": "gross oracle with fixed-width uniform labels before body",
            "ORACLE_PAID": "greedy paid assignment with adaptive bitwise labels before body",
            "SHUFFLED": "rotated paid labels with identical label multiset",
            "TITLE_PREDICTED": "causal title-feature prediction learned from prior pages",
        },
        "exact_replay": exact,
        "economics": {
            "design_target_bytes": 108_000_000,
            "planning_baseline_bytes": 109_524_268,
            "design_debt_bytes": 1_524_268,
            "gross_gate_bytes_at_scope": args.gross_gate_bytes,
            "net_gate_bytes_at_scope": args.net_gate_bytes,
            "gross_saved_bytes": gross,
            "fixed_label_saved_bytes": fixed,
            "adaptive_paid_saved_bytes": paid,
            "provisional_source_bytes": source_bytes,
            "source_amortization_bytes_at_scope": source_bytes
            * parsed.raw_length
            / 1_000_000_000,
        },
        "construction": {
            "helper_compile_command": compile_command,
            "helper_binary_sha256": helper_sha256,
            "native_probability_total": 65_536,
            "range_coder_semantics": "endpoint_uint16_byte_range_v1",
            "labels_encoded_before_selected_payload": True,
            "underlying_expert_trajectories_unchanged": True,
            "selection_reads_current_page": True,
            "selection_information_paid_by_label": True,
        },
        "verdict": verdict,
        "promotion_authorized": verdict.startswith("mechanism_positive"),
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Exact arithmetic shadow over preserved aligned probability traces. "
            "This is not a native combined codec, full-corpus score, roundtrip, "
            "runtime receipt, or Seal binding."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--expert", type=parse_expert, action="append", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--trace-classification", required=True)
    parser.add_argument("--gross-gate-bytes", type=int, default=3_000)
    parser.add_argument("--net-gate-bytes", type=int, default=2_300)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for path in (
        args.raw,
        args.store,
        args.dictionary,
        *(path for _, path in args.expert),
    ):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(
        json.dumps(
            {
                "gross_saved_bytes": receipt["economics"]["gross_saved_bytes"],
                "fixed_label_saved_bytes": receipt["economics"][
                    "fixed_label_saved_bytes"
                ],
                "adaptive_paid_saved_bytes": receipt["economics"][
                    "adaptive_paid_saved_bytes"
                ],
                "verdict": receipt["verdict"],
                "score_credit_bytes": 0,
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
