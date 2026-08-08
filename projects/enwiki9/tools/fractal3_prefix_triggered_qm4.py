#!/usr/bin/env python3
"""Correct-parent free ceiling for causal prefix-triggered FRACTAL macros."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path

import numpy as np

import fractal2_endpoint428_paid_mdl_qp1 as qp1
import fractal2_form_echo_joint_qm1 as qm1
import wrt_exact


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fractal3_prefix_triggered_qm4_v1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def arm(event_qbits: np.ndarray, event_map: qm1.EventMap, raw_bytes: int,
        spans: list[qm1.Span]) -> dict[str, object]:
    mask = qm1.mask_for(len(event_qbits), spans)
    result = qm1.summarize_arm(mask, event_qbits, event_map, raw_bytes)
    result["selected_spans"] = len(spans)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-input", type=Path,
                        default=ROOT / "data/enwik9_10000000.bin")
    parser.add_argument("--wrt-store", type=Path,
                        default=Path("/home/x/enwiki9-nonproof/results/fx2_order_original_10m.store"))
    parser.add_argument("--dictionary", type=Path,
                        default=ROOT / "external/fx2-cmix/dictionary/english.dic")
    parser.add_argument("--parent-p1", type=Path,
                        default=ROOT / "results/fractal2_endpoint428_trace_10m_v1/endpoint428.p1")
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=False)
    raw = args.raw_input.read_bytes()
    parsed = wrt_exact.parse_store(args.wrt_store, args.dictionary)
    if parsed.decoded != raw:
        raise RuntimeError("canonical WRT store does not invert to raw input")
    event_map = qm1.EventMap(parsed)
    event_qbits = qm1.read_parent_qbits(parsed, args.parent_p1)

    pages, occurrences, rule_ledger = qp1.build_universe(raw, event_map)
    tail_form = [span for occurrence in occurrences
                 for span in occurrence.structural[1:]]

    rule_values = qm1.values_for_rules(raw, event_map, occurrences)
    ordinary_values = qm1.ordinary_xml_values(raw, event_map, pages)
    echo_rule, echo_rule_stats = qm1.score_values(rule_values, "slot")
    echo_ordinary, echo_ordinary_stats = qm1.score_values(ordinary_values, "slot")
    echo_flat, echo_flat_stats = qm1.score_values(rule_values, "flat")
    shuffled = qm1.shuffled_keys(rule_values)
    echo_shuffled, echo_shuffled_stats = qm1.score_values(
        rule_values, "slot", shuffled)

    arms = {
        "F0": arm(event_qbits, event_map, len(raw), tail_form),
        "E0": arm(event_qbits, event_map, len(raw), echo_ordinary),
        "C0": arm(event_qbits, event_map, len(raw), echo_flat),
        "S0": arm(event_qbits, event_map, len(raw), tail_form + echo_shuffled),
        "J0": arm(event_qbits, event_map, len(raw), tail_form + echo_rule),
    }

    def displaced(name: str) -> float:
        return float(arms[name]["displaced_bytes"])

    j0 = displaced("J0")
    margins = {name: j0 - displaced(name) for name in ("F0", "E0", "C0", "S0")}
    chronological = [
        float(row["displaced_bytes"])
        for row in arms["J0"]["chronological_splits"]
    ]
    multi_page_rules = sum(
        1 for value in rule_ledger.values()
        if int(value.get("pages", value.get("page_count", 0))) >= 3
    )
    if multi_page_rules == 0:
        page_sets: dict[str, set[int]] = {}
        for occurrence in occurrences:
            page_sets.setdefault(occurrence.rule_key, set()).add(occurrence.page)
        multi_page_rules = sum(len(value) >= 3 for value in page_sets.values())

    failed: list[str] = []
    if j0 < 100000:
        failed.append("J0_below_100000_bytes")
    if any(value <= 0 for value in chronological):
        failed.append("J0_chronological_split_nonpositive")
    for name, value in margins.items():
        if value < 20000:
            failed.append(f"J0_margin_over_{name}_below_20000_bytes")
    if multi_page_rules == 0:
        failed.append("no_rule_spans_three_pages")

    source_paths = [
        Path(__file__),
        Path(qp1.__file__),
        Path(qm1.__file__),
        Path(wrt_exact.__file__),
    ]
    source_blob = b"".join(
        path.name.encode("ascii") + b"\0" + path.read_bytes()
        for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    (args.output_dir / "source_package.lzma").write_bytes(source_package)

    decision = {
        "schema": "enwiki9_fractal3_prefix_triggered_qm4_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "correct_parent_free_ceiling_zero_credit",
        "verdict": "promote_to_paid_prefix_macro" if not failed else "retire_prefix_trigger_realization",
        "inputs": {
            "raw_bytes": len(raw),
            "raw_sha256": sha256_bytes(raw),
            "wrt_stream_bytes": len(parsed.stream),
            "wrt_stream_sha256": sha256_bytes(parsed.stream),
            "parent_p1_bytes": args.parent_p1.stat().st_size,
            "parent_p1_sha256": hashlib.sha256(args.parent_p1.read_bytes()).hexdigest(),
        },
        "population": {
            "pages": len(pages),
            "occurrences": len(occurrences),
            "rules": len(rule_ledger),
            "multi_page_rules": multi_page_rules,
            "first_form_terminal_excluded_per_occurrence": True,
        },
        "arms": arms,
        "margins_bytes": margins,
        "echo_stats": {
            "rule": echo_rule_stats,
            "ordinary": echo_ordinary_stats,
            "flat": echo_flat_stats,
            "shuffled": echo_shuffled_stats,
        },
        "proof": {
            "wrt_store_inverse_exact": True,
            "raw_inverse_exact": True,
            "decoder_contract": "first FORM terminal remains in parent stream; later identities are free only in this ceiling",
        },
        "accounting": {
            "source_package_bytes_reported_not_debited_at_free_gate": len(source_package),
            "rule_definitions_free": True,
            "macro_invocations_free": True,
            "source_identities_free": True,
            "score_credit_bytes": 0,
        },
        "failed_conditions": failed,
    }
    encoded = json.dumps(decision, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    (args.output_dir / "decision.json").write_bytes(encoded)
    print(json.dumps({
        "candidate_id": CANDIDATE_ID,
        "J0_displaced_bytes": j0,
        "margins_bytes": margins,
        "chronological_displaced_bytes": chronological,
        "failed_conditions": failed,
        "verdict": decision["verdict"],
        "output": str(args.output_dir / "decision.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
