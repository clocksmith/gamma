#!/usr/bin/env python3
"""Correct-parent ceiling for causal online FORM rule transitions."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import lzma
from pathlib import Path

import fractal2_endpoint428_paid_mdl_qp1 as qp1
import fractal2_form_echo_joint_qm1 as qm1
import fractal3_prefix_triggered_qm4 as qm4
import fractal3_shortest_unique_trigger_qm5 as qm5
import wrt_exact


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fractal3_causal_rule_transition_qm6_v1"


def chronological_nonoverlap(occurrences: list[qm1.Occurrence]) -> list[qm1.Occurrence]:
    chosen: list[qm1.Occurrence] = []
    high = -1
    for occurrence in sorted(
        occurrences,
        key=lambda item: (item.raw_start, item.raw_end, item.rule_key, item.family),
    ):
        if occurrence.raw_start < high:
            continue
        chosen.append(occurrence)
        high = occurrence.raw_end
    return chosen


def predicted_occurrences(occurrences: list[qm1.Occurrence]) -> list[qm1.Occurrence]:
    outcomes: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    history: list[str] = []
    predicted: list[qm1.Occurrence] = []
    for occurrence in chronological_nonoverlap(occurrences):
        context = tuple(history[-2:])
        learned = outcomes[context]
        if len(learned) == 1 and occurrence.rule_key in learned:
            predicted.append(occurrence)
        learned[occurrence.rule_key] += 1
        history.append(occurrence.rule_key)
    return predicted


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

    lengths, inconsistent = qm5.trigger_lengths(parsed, occurrences)
    base_form: list[qm1.Span] = []
    for occurrence in occurrences:
        if not occurrence.structural:
            continue
        first = occurrence.structural[0]
        consumed = lengths.get(occurrence.rule_key, first.hi - first.lo)
        if first.lo + consumed < first.hi:
            base_form.append(qm1.Span(first.lo + consumed, first.hi))
        base_form.extend(occurrence.structural[1:])

    predictions = predicted_occurrences(occurrences)
    predicted_first = [
        occurrence.structural[0]
        for occurrence in predictions
        if occurrence.structural
    ]
    transition_form = base_form + predicted_first

    rule_values = qm1.values_for_rules(raw, event_map, occurrences)
    ordinary_values = qm1.ordinary_xml_values(raw, event_map, pages)
    echo_rule, echo_rule_stats = qm1.score_values(rule_values, "slot")
    echo_ordinary, echo_ordinary_stats = qm1.score_values(ordinary_values, "slot")
    echo_flat, echo_flat_stats = qm1.score_values(rule_values, "flat")
    shuffled = qm1.shuffled_keys(rule_values)
    echo_shuffled, echo_shuffled_stats = qm1.score_values(rule_values, "slot", shuffled)

    arms = {
        "F0": qm4.arm(event_qbits, event_map, len(raw), transition_form),
        "E0": qm4.arm(event_qbits, event_map, len(raw), echo_ordinary),
        "C0": qm4.arm(event_qbits, event_map, len(raw), echo_flat),
        "S0": qm4.arm(event_qbits, event_map, len(raw), transition_form + echo_shuffled),
        "T0": qm4.arm(event_qbits, event_map, len(raw), base_form + echo_rule),
        "J0": qm4.arm(event_qbits, event_map, len(raw), transition_form + echo_rule),
    }
    j0 = float(arms["J0"]["displaced_bytes"])
    margins = {
        name: j0 - float(arms[name]["displaced_bytes"])
        for name in ("F0", "E0", "C0", "S0", "T0")
    }
    chronological = [
        float(row["displaced_bytes"])
        for row in arms["J0"]["chronological_splits"]
    ]
    prediction_pages = len({occurrence.page for occurrence in predictions})

    failed: list[str] = []
    if j0 < 100000:
        failed.append("J0_below_100000_bytes")
    if margins["T0"] < 10000:
        failed.append("transition_contribution_below_10000_bytes")
    if any(value <= 0 for value in chronological):
        failed.append("J0_chronological_split_nonpositive")
    for name in ("F0", "E0", "C0", "S0"):
        if margins[name] < 20000:
            failed.append(f"J0_margin_over_{name}_below_20000_bytes")
    if prediction_pages < 3:
        failed.append("predictions_span_fewer_than_three_pages")

    source_paths = [Path(__file__), Path(qp1.__file__), Path(qm1.__file__),
                    Path(qm4.__file__), Path(qm5.__file__), Path(wrt_exact.__file__)]
    source_blob = b"".join(path.name.encode("ascii") + b"\0" + path.read_bytes()
                           for path in source_paths)
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    (args.output_dir / "source_package.lzma").write_bytes(source_package)

    decision = {
        "schema": "enwiki9_fractal3_causal_rule_transition_qm6_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "correct_parent_free_ceiling_zero_credit",
        "verdict": "promote_to_paid_transition_macro" if not failed else "retire_transition_realization",
        "inputs": {
            "raw_bytes": len(raw),
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "wrt_stream_bytes": len(parsed.stream),
            "wrt_stream_sha256": hashlib.sha256(parsed.stream).hexdigest(),
            "parent_p1_bytes": args.parent_p1.stat().st_size,
            "parent_p1_sha256": hashlib.sha256(args.parent_p1.read_bytes()).hexdigest(),
        },
        "population": {
            "pages": len(pages),
            "occurrences": len(occurrences),
            "rules": len(rule_ledger),
            "inconsistent_first_terminal_rules": len(inconsistent),
            "chronological_nonoverlap_occurrences": len(chronological_nonoverlap(occurrences)),
            "causally_predicted_occurrences": len(predictions),
            "prediction_pages": prediction_pages,
            "transition_order": 2,
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
            "transition_training_uses_only_prior_nonoverlapping_completed_rules": True,
            "unpredicted_rules_fall_back_to_shortest_unique_trigger": True,
        },
        "accounting": {
            "source_package_bytes_reported_not_debited_at_free_gate": len(source_package),
            "rule_definitions_free": True,
            "macro_invocations_free": True,
            "score_credit_bytes": 0,
        },
        "failed_conditions": failed,
    }
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_id": CANDIDATE_ID,
        "J0_displaced_bytes": j0,
        "margins_bytes": margins,
        "chronological_displaced_bytes": chronological,
        "population": decision["population"],
        "failed_conditions": failed,
        "verdict": decision["verdict"],
        "output": str(args.output_dir / "decision.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
