#!/usr/bin/env python3
"""Run the zero-credit Route D timestamp structural-microblock Q0 gate."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import statistics
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "seal2_route_d_timestamp_microblock_rank_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID / "program.py"
PAGE_RE = re.compile(rb"  <page>\n.*?  </page>\n", re.DOTALL)
TIMESTAMP_RE = re.compile(
    rb"<timestamp>([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z)</timestamp>"
)
WIDTH_BYTES = (8, 16, 32)
DEFAULT_MAX_EXPANSIONS = 65_536
PROMOTION_BYTES_PER_MILLION = 2_100.0
MIN_BOUNDED_SUCCESS_RATE = 0.95
MAX_PARITY_TO_DIRECT_RATIO = 1.25


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_program() -> Any:
    spec = importlib.util.spec_from_file_location("route_d_timestamp_q0", PROGRAM)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Route D Q0 candidate")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract_records(data: bytes, offset_start: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    previous: bytes | None = None
    complete_pages = 0
    timestamp_pages = 0
    for page_index, page_match in enumerate(PAGE_RE.finditer(data)):
        complete_pages += 1
        page = page_match.group(0)
        timestamp = TIMESTAMP_RE.search(page)
        if timestamp is None:
            continue
        timestamp_pages += 1
        value_start = timestamp.start(1)
        envelope = page[value_start : value_start + 32]
        if len(envelope) != 32 or not envelope.endswith(b"</timestamp>"):
            raise ValueError("timestamp envelope does not match the frozen 32-byte class")
        page_start = page_match.start()
        if page_start >= offset_start:
            split = "offset"
        elif page_index % 5 == 0:
            split = "holdout"
        else:
            split = "development"
        if previous is not None:
            records.append(
                {
                    "page_index": page_index,
                    "page_start": page_start,
                    "page_bytes": len(page),
                    "prototype": previous,
                    "target": envelope,
                    "split": split,
                }
            )
        previous = envelope
    return records, {
        "complete_pages": complete_pages,
        "timestamp_pages": timestamp_pages,
        "coded_records": len(records),
        "first_record_skipped_for_prototype": timestamp_pages > 0,
    }


def explicit_edit_roundtrip(prototype: bytes, target: bytes) -> bool:
    changed = [
        (index, target[index])
        for index in range(len(target))
        if prototype[index] != target[index]
    ]
    restored = bytearray(prototype)
    for index, value in changed:
        restored[index] = value
    return bytes(restored) == target


def safe_ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def evaluate_split(
    module: Any,
    records: list[dict[str, Any]],
    width_bytes: int,
    max_expansions: int,
) -> dict[str, Any]:
    width_bits = width_bytes * 8
    residuals: list[int] = []
    ranks: list[int] = []
    expansions: list[int] = []
    parity_depths: list[int] = []
    literal_bits = 0
    direct_lower_bits = 0
    direct_delta_bits = 0
    ideal_syndrome_bits = 0
    constructive_parity_bits = 0
    explicit_edit_payload_bits = 0
    bounded_successes = 0
    direct_roundtrip_ok = True
    parity_or_literal_roundtrip_ok = True
    explicit_edit_roundtrip_ok = True
    depth_field_bits = module.ceil_log2(width_bits + 1)

    for record in records:
        prototype = record["prototype"][:width_bytes]
        target = record["target"][:width_bytes]
        residual = module.residual_mask(prototype, target)
        rank = module.energy_rank(width_bits, residual)
        if module.energy_unrank(width_bits, rank) != residual:
            direct_roundtrip_ok = False
        if module.apply_residual(prototype, residual) != target:
            direct_roundtrip_ok = False
        direct_roundtrip_ok = direct_roundtrip_ok and (
            module.energy_unrank(width_bits, rank) == residual
        )
        explicit_edit_roundtrip_ok = explicit_edit_roundtrip_ok and explicit_edit_roundtrip(
            prototype, target
        )

        certificate = module.bounded_parity_certificate(
            width_bits,
            residual,
            max_expansions,
        )
        within_budget = certificate["within_budget"] is True
        parity_exact = certificate["roundtrip_ok"] is True
        if within_budget and parity_exact:
            depth = int(certificate["depth"])
            bounded_successes += 1
            parity_depths.append(depth)
            constructive_parity_bits += 1 + depth_field_bits + depth
        else:
            constructive_parity_bits += 1 + width_bits
            parity_or_literal_roundtrip_ok = parity_or_literal_roundtrip_ok and (
                module.apply_residual(prototype, residual) == target
            )

        residuals.append(residual)
        ranks.append(rank)
        expansions.append(int(certificate["expansions"]))
        literal_bits += width_bits
        direct_lower_bits += module.ceil_log2(rank + 1)
        direct_delta_bits += module.elias_delta_length(rank + 1)
        ideal_syndrome_bits += module.ceil_log2(rank + 1)
        explicit_edit_payload_bits += module.byte_edit_bits(prototype, target)

    causal = module.causal_roundtrip(residuals, width_bits)
    causal_bits = int(causal["payload_bits"])
    raw_bytes = sum(int(record["page_bytes"]) for record in records)
    gross_bits = causal_bits - constructive_parity_bits
    gross_bytes_per_million = (
        gross_bits * 1_000_000.0 / (8.0 * raw_bytes) if raw_bytes else 0.0
    )
    success_rate = bounded_successes / len(records) if records else 0.0
    return {
        "records": len(records),
        "raw_page_bytes": raw_bytes,
        "literal_bits": literal_bits,
        "causal_control": causal,
        "direct_rank": {
            "information_lower_bound_bits": direct_lower_bits,
            "elias_delta_payload_bits": direct_delta_bits,
            "roundtrip_ok": direct_roundtrip_ok,
        },
        "ideal_syndrome_bits": ideal_syndrome_bits,
        "bounded_parity": {
            "payload_bits_with_mode_and_depth": constructive_parity_bits,
            "bounded_successes": bounded_successes,
            "fallback_records": len(records) - bounded_successes,
            "success_rate": success_rate,
            "roundtrip_ok": parity_or_literal_roundtrip_ok,
            "maximum_depth": max(parity_depths, default=0),
            "median_depth": statistics.median(parity_depths) if parity_depths else None,
            "maximum_expansions": max(expansions, default=0),
            "median_expansions": statistics.median(expansions) if expansions else None,
            "parity_to_direct_delta_ratio": safe_ratio(
                constructive_parity_bits,
                direct_delta_bits,
            ),
        },
        "explicit_byte_edit": {
            "payload_bits": explicit_edit_payload_bits,
            "roundtrip_ok": explicit_edit_roundtrip_ok,
        },
        "rank_distribution": {
            "maximum": max(ranks, default=0),
            "median": statistics.median(ranks) if ranks else None,
            "maximum_hamming_weight": max((value.bit_count() for value in residuals), default=0),
            "median_hamming_weight": (
                statistics.median(value.bit_count() for value in residuals)
                if residuals
                else None
            ),
        },
        "economics": {
            "gross_saved_bits_vs_causal": gross_bits,
            "gross_saved_bytes_vs_causal": gross_bits / 8.0,
            "gross_saved_bytes_per_raw_million": gross_bytes_per_million,
        },
        "all_roundtrips_ok": (
            causal["roundtrip_ok"] is True
            and direct_roundtrip_ok
            and parity_or_literal_roundtrip_ok
            and explicit_edit_roundtrip_ok
        ),
    }


def source_accounting() -> dict[str, Any]:
    program = PROGRAM.read_bytes()
    tool = Path(__file__).read_bytes()
    program_gzip = gzip.compress(program, compresslevel=9, mtime=0)
    tool_gzip = gzip.compress(tool, compresslevel=9, mtime=0)
    return {
        "candidate_program_path": PROGRAM.relative_to(ROOT).as_posix(),
        "candidate_program_bytes": len(program),
        "candidate_program_sha256": sha256(program),
        "candidate_program_gzip9_bytes": len(program_gzip),
        "gate_tool_path": Path(__file__).relative_to(ROOT).as_posix(),
        "gate_tool_bytes": len(tool),
        "gate_tool_sha256": sha256(tool),
        "gate_tool_gzip9_bytes": len(tool_gzip),
        "conservative_counted_source_gzip9_bytes": len(program_gzip) + len(tool_gzip),
        "proposal_source_ceiling_bytes": 40_000,
    }


def build_receipt(args: argparse.Namespace) -> dict[str, Any]:
    source = args.input.read_bytes()
    data = source[: args.limit]
    if len(data) != args.limit:
        raise ValueError("input does not cover requested limit")
    if not 0 < args.offset_start < args.limit:
        raise ValueError("offset-start must lie inside the evaluated prefix")
    module = load_program()
    records, extraction = extract_records(data, args.offset_start)
    by_split = {
        split: [record for record in records if record["split"] == split]
        for split in ("development", "holdout", "offset")
    }
    if any(not rows for rows in by_split.values()):
        raise ValueError("frozen development, holdout, and offset populations must be nonempty")

    evaluations: dict[str, dict[str, Any]] = {}
    for width_bytes in WIDTH_BYTES:
        evaluations[str(width_bytes)] = {
            split: evaluate_split(
                module,
                split_records,
                width_bytes,
                args.max_expansions,
            )
            for split, split_records in by_split.items()
        }

    selected_width = min(
        WIDTH_BYTES,
        key=lambda width: (
            -evaluations[str(width)]["development"]["economics"][
                "gross_saved_bytes_per_raw_million"
            ],
            width,
        ),
    )
    selected = evaluations[str(selected_width)]
    accounting = source_accounting()
    combined_raw_bytes = sum(row["raw_page_bytes"] for row in selected.values())
    combined_causal_bits = sum(
        int(row["causal_control"]["payload_bits"]) for row in selected.values()
    )
    combined_parity_bits = sum(
        int(row["bounded_parity"]["payload_bits_with_mode_and_depth"])
        for row in selected.values()
    )
    combined_direct_bits = sum(
        int(row["direct_rank"]["elias_delta_payload_bits"])
        for row in selected.values()
    )
    source_bits = int(accounting["conservative_counted_source_gzip9_bytes"]) * 8
    combined_net_bits = combined_causal_bits - combined_parity_bits - source_bits
    combined_net_bpm = combined_net_bits * 1_000_000.0 / (8.0 * combined_raw_bytes)
    parity_to_direct_ratio = safe_ratio(combined_parity_bits, combined_direct_bits)

    conditions = {
        "all_populations_nonempty": all(row["records"] > 0 for row in selected.values()),
        "all_roundtrips_ok": all(row["all_roundtrips_ok"] for row in selected.values()),
        "development_bounded_success_rate": (
            selected["development"]["bounded_parity"]["success_rate"]
            >= MIN_BOUNDED_SUCCESS_RATE
        ),
        "holdout_bounded_success_rate": (
            selected["holdout"]["bounded_parity"]["success_rate"]
            >= MIN_BOUNDED_SUCCESS_RATE
        ),
        "offset_bounded_success_rate": (
            selected["offset"]["bounded_parity"]["success_rate"]
            >= MIN_BOUNDED_SUCCESS_RATE
        ),
        "development_gross_positive": (
            selected["development"]["economics"]["gross_saved_bits_vs_causal"] > 0
        ),
        "holdout_gross_positive": (
            selected["holdout"]["economics"]["gross_saved_bits_vs_causal"] > 0
        ),
        "offset_gross_positive": (
            selected["offset"]["economics"]["gross_saved_bits_vs_causal"] > 0
        ),
        "parity_approaches_direct_rank": (
            parity_to_direct_ratio is not None
            and parity_to_direct_ratio <= MAX_PARITY_TO_DIRECT_RATIO
        ),
        "source_within_ceiling": (
            accounting["conservative_counted_source_gzip9_bytes"]
            <= accounting["proposal_source_ceiling_bytes"]
        ),
        "paid_rate_clears_2100_bytes_per_million": (
            combined_net_bpm >= PROMOTION_BYTES_PER_MILLION
        ),
    }
    promotion = all(conditions.values())
    failed = [name for name, passed in conditions.items() if not passed]
    verdict = (
        "promote_timestamp_microblock_to_10m"
        if promotion
        else "retire_timestamp_microblock_route_d_q0"
    )
    return {
        "schema": "seal2_route_d_timestamp_microblock_gate_v1",
        "evidence_level": "zero_credit_exact_structural_diagnostic",
        "candidate_id": CANDIDATE_ID,
        "proposal_id": "seal2_route_d_structural_microblock_v1",
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Exact opening-prefix timestamp-envelope rank, parity, edit, and "
            "causal-control evidence only. It is not a full-stream archive, "
            "forecast improvement, Seal activation, or full-corpus proof."
        ),
        "input": {
            "path": str(args.input.resolve()),
            "source_bytes": len(source),
            "scope_bytes": len(data),
            "scope_sha256": sha256(data),
            "offset_start": args.offset_start,
        },
        "structural_class": {
            "name": "mediawiki_revision_timestamp_envelope",
            "object": "20-byte timestamp value plus 12-byte closing timestamp tag",
            "prototype": "previous decoder-visible object in chronological page order",
            "candidate_order": "Hamming weight then lexicographic changed-bit positions",
            "width_bytes": list(WIDTH_BYTES),
            "development_split": "complete pages before offset with page_index mod 5 nonzero",
            "holdout_split": "complete pages before offset with page_index mod 5 zero",
            "offset_split": "complete pages beginning at or after offset-start",
            "max_expansions": args.max_expansions,
        },
        "extraction": extraction,
        "source_accounting": accounting,
        "evaluations": evaluations,
        "selection": {
            "rule": "maximum development gross bytes per raw million, then lowest width",
            "selected_width_bytes": selected_width,
        },
        "combined_selected_economics": {
            "raw_page_bytes": combined_raw_bytes,
            "causal_control_bits": combined_causal_bits,
            "parity_payload_bits": combined_parity_bits,
            "direct_rank_elias_delta_bits": combined_direct_bits,
            "source_bits": source_bits,
            "gross_saved_bits_vs_causal": combined_causal_bits - combined_parity_bits,
            "net_saved_bits_after_source": combined_net_bits,
            "net_saved_bytes_per_raw_million": combined_net_bpm,
            "parity_to_direct_delta_ratio": parity_to_direct_ratio,
        },
        "gate_contract": {
            "promotion_bytes_per_raw_million": PROMOTION_BYTES_PER_MILLION,
            "minimum_bounded_success_rate": MIN_BOUNDED_SUCCESS_RATE,
            "maximum_parity_to_direct_ratio": MAX_PARITY_TO_DIRECT_RATIO,
            "conditions": conditions,
        },
        "decision": {
            "verdict": verdict,
            "promotion_authorized": promotion,
            "failed_conditions": failed,
            "next_action": (
                "queue one exact serialized 10M diagnostic with the frozen width"
                if promotion
                else "retire this timestamp structural class without a width, matrix, or expansion ladder"
            ),
        },
    }


def write_receipt(output_dir: Path, receipt: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "decision.json"
    temporary = output_dir / f".decision.json.{os.getpid()}.tmp"
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=1_000_000)
    parser.add_argument("--offset-start", type=int, default=800_000)
    parser.add_argument("--max-expansions", type=int, default=DEFAULT_MAX_EXPANSIONS)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not args.input.is_file():
        raise SystemExit(f"missing input: {args.input}")
    if args.limit <= 0 or args.max_expansions <= 0:
        raise SystemExit("limit and max-expansions must be positive")
    receipt = build_receipt(args)
    path = write_receipt(args.output_dir, receipt)
    print(
        json.dumps(
            {
                "verdict": receipt["decision"]["verdict"],
                "selected_width_bytes": receipt["selection"]["selected_width_bytes"],
                "net_saved_bytes_per_raw_million": receipt[
                    "combined_selected_economics"
                ]["net_saved_bytes_per_raw_million"],
                "failed_conditions": receipt["decision"]["failed_conditions"],
                "output": str(path.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
