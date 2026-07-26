#!/usr/bin/env python3
"""Run RADIX-STC N0-N4 against one pinned cmix binary and dictionary."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import time
from pathlib import Path

from radix_stc_transform import VARIANTS, decode_frame, encode_frame


def digest(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {
        "path": str(path.resolve()),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def run_command(command: list[str], stdout_path: Path, stderr_path: Path) -> float:
    started = time.perf_counter()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(command, stdout=stdout, stderr=stderr, check=False)
    elapsed = time.perf_counter() - started
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed with {completed.returncode}: {' '.join(command)}"
        )
    return elapsed


def source_cost() -> dict[str, object]:
    paths = [
        Path(__file__).resolve(),
        Path(__file__).resolve().with_name("radix_stc_transform.py"),
    ]
    payload = b"".join(path.read_bytes() for path in paths)
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    return {
        "accounting": "research estimate only; native package accounting remains required",
        "raw_bytes": len(payload),
        "gzip9_bytes": len(compressed),
        "paths": [str(path) for path in paths],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    backend = parser.add_mutually_exclusive_group(required=True)
    backend.add_argument("--cmix")
    backend.add_argument("--wrapper")
    parser.add_argument("--dictionary")
    parser.add_argument("--baseline-archive")
    parser.add_argument("--baseline-receipt")
    parser.add_argument(
        "--variants",
        nargs="+",
        choices=tuple(VARIANTS),
        default=("n0", "n1", "n2", "n3", "n4"),
    )
    parser.add_argument(
        "--scope-role",
        choices=("opening", "offset500m", "canonical10m", "other"),
        required=True,
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output_dir).resolve()
    cmix_path = Path(args.cmix).resolve() if args.cmix else None
    wrapper_path = Path(args.wrapper).resolve() if args.wrapper else None
    dictionary_path = Path(args.dictionary).resolve() if args.dictionary else None
    if cmix_path is not None and dictionary_path is None:
        raise RuntimeError("--dictionary is required with --cmix")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = input_path.read_bytes()
    raw_sha256 = hashlib.sha256(raw).hexdigest()
    results: dict[str, dict[str, object]] = {}

    for name in args.variants:
        variant_dir = output_dir / name
        variant_dir.mkdir(exist_ok=True)
        transformed, transform_stats = encode_frame(raw, name)
        transformed_path = variant_dir / "input.transformed"
        archive_path = variant_dir / "archive.bin"
        second_archive_path = variant_dir / "archive.second.bin"
        decoded_transform_path = variant_dir / "decoded.transformed"
        decoded_raw_path = variant_dir / "decoded.raw"
        transformed_path.write_bytes(transformed)

        encode_command = (
            [
                str(cmix_path),
                "-c",
                str(dictionary_path),
                str(transformed_path),
                str(archive_path),
            ]
            if cmix_path is not None
            else [
                str(wrapper_path),
                "c",
                str(transformed_path),
                str(archive_path),
            ]
        )
        decode_command = (
            [
                str(cmix_path),
                "-d",
                str(dictionary_path),
                str(archive_path),
                str(decoded_transform_path),
            ]
            if cmix_path is not None
            else [
                str(wrapper_path),
                "d",
                str(archive_path),
                str(decoded_transform_path),
            ]
        )
        second_encode_command = list(encode_command)
        second_encode_command[-1] = str(second_archive_path)
        encode_seconds = run_command(
            encode_command,
            variant_dir / "encode.stdout",
            variant_dir / "encode.stderr",
        )
        decode_seconds = run_command(
            decode_command,
            variant_dir / "decode.stdout",
            variant_dir / "decode.stderr",
        )
        restored_transform = decoded_transform_path.read_bytes()
        restored_raw = (
            restored_transform if name == "n0" else decode_frame(restored_transform)
        )
        decoded_raw_path.write_bytes(restored_raw)
        if restored_raw != raw:
            raise RuntimeError(f"{name}: exact roundtrip failed")

        second_encode_seconds = run_command(
            second_encode_command,
            variant_dir / "encode_second.stdout",
            variant_dir / "encode_second.stderr",
        )
        deterministic = archive_path.read_bytes() == second_archive_path.read_bytes()
        if not deterministic:
            raise RuntimeError(f"{name}: deterministic archive check failed")

        results[name] = {
            "transform": transform_stats,
            "transformed": digest(transformed_path),
            "archive": digest(archive_path),
            "decoded_raw": digest(decoded_raw_path),
            "exact_roundtrip": True,
            "deterministic_second_archive": True,
            "timing_seconds": {
                "encode": encode_seconds,
                "decode": decode_seconds,
                "second_encode": second_encode_seconds,
            },
        }

    if "n0" in results:
        baseline = results["n0"]["archive"]
    elif args.baseline_archive:
        baseline = digest(Path(args.baseline_archive).resolve())
    else:
        raise RuntimeError("N0 or --baseline-archive is required")
    baseline_bytes = int(baseline["bytes"])
    cost = source_cost()
    amortized_10m_cost = (int(cost["gzip9_bytes"]) + 99) // 100
    for name, result in results.items():
        archive_bytes = int(result["archive"]["bytes"])
        gross = baseline_bytes - archive_bytes
        result["economics"] = {
            "gross_archive_gain_bytes": gross,
            "canonical_10m_net_screen_bytes": gross - amortized_10m_cost,
            "projected_full_1g_net_bytes": gross * 100 - int(cost["gzip9_bytes"]),
            "source_cost_is_research_estimate": True,
        }

    n4 = results.get("n4")
    n4_gross = (
        int(n4["economics"]["gross_archive_gain_bytes"]) if n4 is not None else None
    )
    n4_net = (
        int(n4["economics"]["canonical_10m_net_screen_bytes"])
        if n4 is not None
        else None
    )
    if n4 is None:
        decision = "incomplete_without_n4"
    elif args.scope_role in ("opening", "offset500m"):
        decision = "positive_sign" if n4_gross > 0 else "retire_nonpositive_sign"
    elif args.scope_role == "canonical10m":
        decision = (
            "promote_to_disjoint_native_integration"
            if n4_gross >= 25000 and n4_net >= 23000
            else "retire_below_canonical_gate"
        )
    else:
        decision = "informational_scope"

    receipt = {
        "schema": "radix_stc_endpoint_ablation_v1",
        "evidence_level": "adjacent_same_binary_reversible_transform_ablation",
        "claim_boundary": (
            "This receipt measures one pinned external cmix binary. It grants no "
            "endpoint428, full-corpus, official-score, or Seal credit."
        ),
        "scope_role": args.scope_role,
        "input": digest(input_path),
        "input_sha256_verified_after_roundtrip": raw_sha256,
        "backend": {
            "mode": "cmix_dictionary" if cmix_path is not None else "self_contained_wrapper",
            "executable": digest(cmix_path if cmix_path is not None else wrapper_path),
            "dictionary": digest(dictionary_path) if dictionary_path is not None else None,
        },
        "baseline_archive": baseline,
        "baseline_receipt": (
            digest(Path(args.baseline_receipt).resolve())
            if args.baseline_receipt
            else None
        ),
        "source_cost": cost,
        "variants": results,
        "decision": decision,
        "gates": {
            "opening_and_offset_positive_required": True,
            "canonical_10m_gross_bytes": 25000,
            "canonical_10m_net_bytes": 23000,
        },
    }
    decision_path = output_dir / "decision.json"
    decision_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": decision, "output": str(decision_path)}))


if __name__ == "__main__":
    main()
