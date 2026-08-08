#!/usr/bin/env python3
"""FRACTAL-2 QM2: recursively anti-unified punctuation-forest ceiling gate."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re

import numpy as np

import fractal2_form_echo_joint_qm1 as qm1
from wrt_exact import parse_store


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fractal2_recursive_punct_forest_qm2_v1"
QM1_DECISION = ROOT / "results/fractal2_form_echo_joint_qm1_v1/decision.json"
PUNCT_RUN = re.compile(br"[^A-Za-z0-9\x80-\xff]+")


def punctuation_occurrence(
    family: str,
    raw: bytes,
    event_map: qm1.EventMap,
    page: int,
    start: int,
    end: int,
) -> qm1.Occurrence | None:
    if not 4 <= end - start <= 4096:
        return None
    structural: list[qm1.Span] = []
    holes: list[qm1.Span | None] = []
    segments: list[bytes] = []
    cursor = start
    for match in PUNCT_RUN.finditer(raw, start, end):
        holes.append(qm1.aligned(event_map, cursor, match.start()))
        span = qm1.aligned(event_map, match.start(), match.end())
        if span is None:
            return None
        structural.append(span)
        segments.append(match.group())
        cursor = match.end()
        if len(segments) > 96:
            return None
    holes.append(qm1.aligned(event_map, cursor, end))
    if len(structural) < 2 or sum(len(segment) for segment in segments) < 3:
        return None
    if sum(span is not None for span in holes) < 2:
        return None
    return qm1.Occurrence(
        family=family,
        rule_key=qm1.signature(family, segments),
        page=page,
        raw_start=start,
        raw_end=end,
        structural=tuple(structural),
        holes=tuple(holes),
    )


def segmented_rule(
    family: str,
    raw: bytes,
    event_map: qm1.EventMap,
    page: int,
    start: int,
    end: int,
    segments: tuple[bytes, ...],
) -> qm1.Occurrence | None:
    return qm1.segmented_occurrence(family, raw, event_map, page, start, end, segments)


def recursive_occurrences(
    raw: bytes,
    event_map: qm1.EventMap,
    page: int,
    start: int,
    end: int,
) -> list[qm1.Occurrence]:
    page_bytes = raw[start:end]
    rows: list[qm1.Occurrence] = []

    for line in re.finditer(br"(?m)^.{4,4096}(?:\r?\n|$)", page_bytes):
        row = punctuation_occurrence(
            "punct_line", raw, event_map, page, start + line.start(), start + line.end()
        )
        if row is not None:
            rows.append(row)

    for sentence in re.finditer(br"[^\r\n.!?]{8,2048}[.!?]+(?:[ \t]+|$)", page_bytes):
        row = punctuation_occurrence(
            "punct_sentence",
            raw,
            event_map,
            page,
            start + sentence.start(),
            start + sentence.end(),
        )
        if row is not None:
            rows.append(row)

    special = (
        ("external_link", re.compile(br"\[([^\[\]\r\n ]+)( [^\[\]\r\n]+)?\]"), (b"[", b" ", b"]")),
        ("reference", re.compile(br"<ref(?:\s[^>]*)?>(.*?)</ref>", re.DOTALL), (b"<ref", b">", b"</ref>")),
        ("comment", re.compile(br"<!--(.*?)-->", re.DOTALL), (b"<!--", b"-->")),
        ("bold", re.compile(br"'''([^\r\n']{1,2048})'''"), (b"'''", b"'''")),
        ("italic", re.compile(br"''([^\r\n']{1,2048})''"), (b"''", b"''")),
    )
    for family, pattern, default_segments in special:
        for match in pattern.finditer(page_bytes):
            match_start = start + match.start()
            match_end = start + match.end()
            segments = default_segments
            if family == "external_link" and match.group(2) is None:
                segments = (b"[", b"]")
            if family == "reference":
                opening_end = raw.find(b">", match_start, match_end)
                if opening_end < 0:
                    continue
                segments = (raw[match_start : opening_end + 1], b"</ref>")
            row = segmented_rule(
                family, raw, event_map, page, match_start, match_end, segments
            )
            if row is not None:
                rows.append(row)

    for entity in re.finditer(br"&(?:[A-Za-z]{2,16}|#[0-9]{1,7}|#x[0-9A-Fa-f]{1,6});", page_bytes):
        absolute_start = start + entity.start()
        absolute_end = start + entity.end()
        span = qm1.aligned(event_map, absolute_start, absolute_end)
        if span is not None:
            terminal = entity.group()
            rows.append(
                qm1.Occurrence(
                    family="entity_terminal",
                    rule_key=qm1.signature("entity_terminal", (terminal,)),
                    page=page,
                    raw_start=absolute_start,
                    raw_end=absolute_end,
                    structural=(span,),
                    holes=(),
                )
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-input", type=Path, default=ROOT / "data/enwik9_10000000.bin")
    parser.add_argument("--wrt-store", type=Path, default=Path("/home/x/enwiki9-nonproof/results/fx2_order_original_10m.store"))
    parser.add_argument("--parent-p1", type=Path, default=Path("/home/x/enwiki9-nonproof/results/fx2_order_original_10m_p1.bin"))
    parser.add_argument("--dictionary", type=Path, default=ROOT / "external/fx2-cmix/dictionary/english.dic")
    parser.add_argument("--output", type=Path, default=ROOT / f"results/{CANDIDATE_ID}/decision.json")
    args = parser.parse_args()

    raw = args.raw_input.read_bytes()
    parsed = parse_store(args.wrt_store, args.dictionary)
    if parsed.decoded != raw:
        raise ValueError("exact WRT inverse differs from canonical raw input")
    event_map = qm1.EventMap(parsed)
    event_qbits = qm1.read_parent_qbits(parsed, args.parent_p1)
    pages = qm1.page_ranges(raw)
    template_parser = qm1.load_template_module()

    qm1_occurrences: list[qm1.Occurrence] = []
    recursive: list[qm1.Occurrence] = []
    for page, (start, end) in enumerate(pages):
        page_form = qm1.page_form_occurrence(raw, event_map, page, start, end)
        if page_form is not None:
            qm1_occurrences.append(page_form)
        qm1_occurrences.extend(qm1.local_occurrences(raw, event_map, template_parser, page, start, end))
        recursive.extend(recursive_occurrences(raw, event_map, page, start, end))

    selected, summaries = qm1.select_rules(qm1_occurrences + recursive)
    joint_values = qm1.values_for_rules(raw, event_map, selected)
    xml_values = qm1.ordinary_xml_values(raw, event_map, pages)
    form_intervals = [span for row in selected for span in row.structural]
    echo_intervals, echo_commands = qm1.score_values(joint_values, "slot")
    e0_intervals, e0_commands = qm1.score_values(xml_values, "slot")
    flat_intervals, flat_commands = qm1.score_values(joint_values, "flat")
    shuffle = qm1.shuffled_keys(joint_values)
    shuffled_intervals, shuffled_commands = qm1.score_values(joint_values, "slot", shuffle)

    count = len(parsed.events)
    form_mask = qm1.mask_for(count, form_intervals)
    echo_mask = qm1.mask_for(count, echo_intervals)
    masks = {
        "B0": np.zeros(count, dtype=np.bool_),
        "F0": form_mask,
        "E0": qm1.mask_for(count, e0_intervals),
        "C0": qm1.mask_for(count, flat_intervals),
        "S0": form_mask | qm1.mask_for(count, shuffled_intervals),
        "J0": form_mask | echo_mask,
    }
    arms = {
        name: qm1.summarize_arm(mask, event_qbits, event_map, len(raw))
        for name, mask in masks.items()
    }
    margins = {
        name: arms["J0"]["displaced_bytes"] - arms[name]["displaced_bytes"]
        for name in ("F0", "E0", "C0", "S0")
    }
    qm1_row = json.loads(QM1_DECISION.read_text())
    incremental = arms["J0"]["displaced_bytes"] - qm1_row["arms"]["J0"]["displaced_bytes"]
    failed: list[str] = []
    if arms["J0"]["displaced_bytes"] < 100_000:
        failed.append("J0_ceiling_below_100000_bytes")
    for name, margin in margins.items():
        if margin < 20_000:
            failed.append(f"J0_margin_over_{name}_below_20000_bytes")
    if any(row["displaced_bytes"] <= 0 for row in arms["J0"]["chronological_splits"]):
        failed.append("J0_chronological_split_nonpositive")
    recursive_admitted = {
        row.rule_key for row in selected if row.family in {
            "punct_line", "punct_sentence", "external_link", "reference",
            "comment", "bold", "italic", "entity_terminal"
        }
    }
    if not recursive_admitted:
        failed.append("no_recursive_rule_spans_three_pages")

    family_counts = Counter(row.family for row in selected)
    decision = {
        "schema": "fractal2_recursive_punct_forest_qm2_gate_minus1_v1",
        "candidate_id": CANDIDATE_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "zero_credit_exact_wrt_endpoint428_recursive_partition_ceiling",
        "claim_boundary": "Optimistic Gate -1 only: rule/source identities are free and no paid codec, decoder, framing, or package has been emitted.",
        "inputs": {
            "raw": qm1.artifact(args.raw_input),
            "wrt_store": qm1.artifact(args.wrt_store),
            "parent_p1": qm1.artifact(args.parent_p1),
            "dictionary": qm1.artifact(args.dictionary),
            "qm1_decision": qm1.artifact(QM1_DECISION),
        },
        "population": {
            "raw_bytes": len(raw),
            "wrt_events": len(parsed.events),
            "complete_pages": len(pages),
            "qm1_occurrences": len(qm1_occurrences),
            "recursive_candidate_occurrences": len(recursive),
            "selected_occurrences": len(selected),
            "selected_rules": len(summaries),
            "recursive_selected_rules": len(recursive_admitted),
            "selected_occurrences_by_family": dict(sorted(family_counts.items())),
            "joint_slot_values": len(joint_values),
        },
        "contracts": {
            "qm1_scoring_mechanism_frozen": True,
            "recursive_rules_exact_wrt_aligned": True,
            "sources_precede_completed_target_page": True,
            "same_population_controls": True,
            "parent_prediction_update_trajectory_unchanged": True,
        },
        "commands": {
            "J0_ECHO": echo_commands,
            "E0_XML_PATH": e0_commands,
            "C0_FLAT": flat_commands,
            "S0_SHUFFLED": shuffled_commands,
        },
        "arms": arms,
        "J0_control_margins_bytes": margins,
        "incremental_J0_over_QM1_bytes": incremental,
        "decision": {
            "failed_conditions": failed,
            "verdict": "authorize_fully_paid_10m_codec" if not failed else "retire_fractal2_qm2_realization",
            "promotion_authorized": not failed,
            "score_credit_bytes": 0,
            "next_action": "Freeze the recursive rule universe and implement the fully paid six-arm 10M codec." if not failed else "Preserve the negative and require a materially different source or recursive partition.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=False)
    temporary = args.output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(args.output)
    print(json.dumps({
        "output": str(args.output),
        "arms": {key: value["displaced_bytes"] for key, value in arms.items()},
        "incremental_J0_over_QM1_bytes": incremental,
        "margins": margins,
        "verdict": decision["decision"]["verdict"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
