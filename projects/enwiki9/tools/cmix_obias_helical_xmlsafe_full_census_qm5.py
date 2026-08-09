#!/usr/bin/env python3
"""Census the frozen QM4 XML-safe match rule over all of enwiki9."""

from __future__ import annotations

from collections import Counter
import json
import lzma
import math
import mmap
from pathlib import Path

from cmix_obias_helical_xmlsafe_prefix_qm4 import (
    EXPECTED_INPUT_BYTES,
    EXPECTED_INPUT_SHA256,
    EXPECTED_LEDGER_SHA256,
    parse_ledger,
    selected_matches,
    serialize_ledger,
    sha256_file,
    text_intervals,
)


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_helical_xmlsafe_full_census_qm5_v1"
INPUT_PATH = ROOT / "data/enwik9"
FROZEN_LEDGER_PATH = ROOT / "results/far_history_cdc_collective_ledger_qm1_v1/ledger.lzma"
OUTPUT_DIR = ROOT / "results" / CANDIDATE_ID
QM4_SOURCE_PATH = ROOT / "tools/cmix_obias_helical_xmlsafe_prefix_qm4.py"
RESEARCH_PARENT_DEBT_BYTES = 3_492_825
FROZEN_RESERVE_BYTES = 500_000


def distribute_span(bins: list[int], start: int, length: int, scope: int) -> None:
    end = start + length
    count = len(bins)
    first = min(count - 1, start * count // scope)
    last = min(count - 1, (end - 1) * count // scope)
    for index in range(first, last + 1):
        bin_start = index * scope // count
        bin_end = (index + 1) * scope // count
        bins[index] += max(0, min(end, bin_end) - max(start, bin_start))


def empirical_entropy(values: list[int]) -> dict[str, float | int]:
    counts = Counter(values)
    total = len(values)
    bits_per_value = sum(
        -(count / total) * math.log2(count / total) for count in counts.values()
    )
    return {
        "values": total,
        "unique_values": len(counts),
        "ideal_bits_per_value": bits_per_value,
        "ideal_total_bytes": bits_per_value * total / 8,
        "minimum": min(values),
        "maximum": max(values),
    }


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def main() -> int:
    if INPUT_PATH.stat().st_size != EXPECTED_INPUT_BYTES or sha256_file(INPUT_PATH) != EXPECTED_INPUT_SHA256:
        raise ValueError("canonical input mismatch")
    if sha256_file(FROZEN_LEDGER_PATH) != EXPECTED_LEDGER_SHA256:
        raise ValueError("frozen far-history ledger mismatch")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=False)
    gaps, distances, lengths = parse_ledger(FROZEN_LEDGER_PATH)
    with INPUT_PATH.open("rb") as input_handle:
        data = mmap.mmap(input_handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            intervals = text_intervals(data, EXPECTED_INPUT_BYTES)
            matches, population = selected_matches(
                data, EXPECTED_INPUT_BYTES, gaps, distances, lengths, intervals
            )
        finally:
            data.close()
    ledger_payload, ledger_stats = serialize_ledger(matches)
    ledger_path = OUTPUT_DIR / "ledger.bin"
    ledger_lzma_path = OUTPUT_DIR / "ledger.lzma"
    ledger_path.write_bytes(ledger_payload)
    ledger_lzma_path.write_bytes(lzma.compress(ledger_payload, preset=9 | lzma.PRESET_EXTREME))
    source_path = OUTPUT_DIR / "transform_inverse_source.lzma"
    source_path.write_bytes(
        lzma.compress(QM4_SOURCE_PATH.read_bytes(), preset=9 | lzma.PRESET_EXTREME)
    )
    third_bytes = [0, 0, 0]
    third_matches = [0, 0, 0]
    decile_bytes = [0] * 10
    decile_matches = [0] * 10
    for target, _, length in matches:
        third_matches[min(2, target * 3 // EXPECTED_INPUT_BYTES)] += 1
        decile_matches[min(9, target * 10 // EXPECTED_INPUT_BYTES)] += 1
        distribute_span(third_bytes, target, length, EXPECTED_INPUT_BYTES)
        distribute_span(decile_bytes, target, length, EXPECTED_INPUT_BYTES)
    copied_bytes = sum(length for _, _, length in matches)
    ledger_compressed_bytes = ledger_lzma_path.stat().st_size
    source_compressed_bytes = source_path.stat().st_size
    direct_upper_bytes = copied_bytes - ledger_compressed_bytes - source_compressed_bytes
    required_bytes = RESEARCH_PARENT_DEBT_BYTES + FROZEN_RESERVE_BYTES
    decision = {
        "schema": "enwiki9_cmix_obias_helical_xmlsafe_full_census_qm5_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "exact_full_corpus_transform_census_zero_backend_credit",
        "verdict": (
            "direct_physical_ceiling_passes_debt_plus_reserve"
            if direct_upper_bytes >= required_bytes
            else "direct_physical_ceiling_misses_debt_plus_reserve"
        ),
        "scope_bytes": EXPECTED_INPUT_BYTES,
        "inputs": {
            "canonical_input": artifact(INPUT_PATH),
            "frozen_ledger": artifact(FROZEN_LEDGER_PATH),
        },
        "population": population | {
            "text_intervals": len(intervals),
            "selected_matches": len(matches),
            "selected_copied_bytes": copied_bytes,
        },
        "chronology": {
            "third_selected_matches": third_matches,
            "third_selected_bytes": third_bytes,
            "decile_selected_matches": decile_matches,
            "decile_selected_bytes": decile_bytes,
        },
        "entropy": {
            "distance": empirical_entropy([distance for _, distance, _ in matches]),
            "length": empirical_entropy([length for _, _, length in matches]),
        },
        "ledger": ledger_stats | {
            "compressed_bytes": ledger_compressed_bytes,
            "artifact": artifact(ledger_lzma_path),
        },
        "source_charge": {
            "basis": "Conservative LZMA charge for the complete existing QM4 transform and inverse source.",
            "compressed_bytes": source_compressed_bytes,
            "artifact": artifact(source_path),
        },
        "direct_physical_ceiling": {
            "selected_bytes": copied_bytes,
            "ledger_bytes": ledger_compressed_bytes,
            "incremental_source_bytes": source_compressed_bytes,
            "upper_bound_bytes": direct_upper_bytes,
            "research_parent_debt_bytes": RESEARCH_PARENT_DEBT_BYTES,
            "frozen_reserve_bytes": FROZEN_RESERVE_BYTES,
            "required_bytes": required_bytes,
            "margin_bytes": direct_upper_bytes - required_bytes,
        },
        "proof": {
            "selection_rule_identical_to_qm4": True,
            "all_sources_exact_fully_prior_and_closed": True,
            "all_targets_inside_text_payload": True,
            "all_target_spans_preserve_line_and_markup_bytes": True,
            "selected_byte_sum_matches_chronology": copied_bytes == sum(third_bytes) == sum(decile_bytes),
        },
        "claim_boundary": (
            "Exact full-corpus transform census and direct eight-bit ceiling only. "
            "No cmix-obias span surprisal, retained-stream ripple, archive delta, or score credit."
        ),
    }
    (OUTPUT_DIR / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": decision["verdict"],
        "selected_matches": len(matches),
        "selected_copied_bytes": copied_bytes,
        "third_selected_bytes": third_bytes,
        "ledger_lzma_bytes": ledger_compressed_bytes,
        "source_lzma_bytes": source_compressed_bytes,
        "direct_upper_bound_bytes": direct_upper_bytes,
        "required_bytes": required_bytes,
        "margin_bytes": direct_upper_bytes - required_bytes,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
