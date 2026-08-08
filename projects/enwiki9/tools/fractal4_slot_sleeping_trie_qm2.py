#!/usr/bin/env python3
"""Correct-parent FORM-slot sleeping continuation trie ceiling."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path

import numpy as np

import fractal2_endpoint428_paid_mdl_qp1 as qp1
import fractal2_form_echo_joint_qm1 as qm1
import fractal4_slot_residual_quotient_qm1 as base
import janus_paid_residual_mdl_oracle as janus
import wrt_exact


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fractal4_slot_sleeping_trie_qm2_v1"
PARENT_PRIOR = 0.99
KT_PRIOR = 0.01


def build_prefix_rows(parsed: wrt_exact.ParsedStore, values: list[qm1.Value],
                      labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    spans: list[tuple[int, int]] = []
    total = 0
    for value in values:
        low, high, _ = qp1.span_bytes(parsed, value.span)
        spans.append((low, high))
        total += (high - low) * 8
    rows = np.empty(total, dtype=np.int32)
    contexts = np.empty(total, dtype=np.int64)
    stream = np.frombuffer(parsed.stream, dtype=np.uint8)
    cursor = 0
    bits = np.arange(8, dtype=np.int64)
    for label, (low, high) in zip(labels, spans):
        byte_rows = np.arange(low, high, dtype=np.int32)
        offsets = byte_rows - low
        previous1 = np.where(offsets >= 1, stream[np.maximum(low, byte_rows - 1)], 256).astype(np.int64)
        previous2 = np.where(offsets >= 2, stream[np.maximum(low, byte_rows - 2)], 257).astype(np.int64)
        byte_context = (int(label) * 258 + previous2) * 258 + previous1
        count = len(byte_rows) * 8
        target = slice(cursor, cursor + count)
        rows[target] = np.arange(low * 8, high * 8, dtype=np.int32)
        contexts[target] = np.repeat(byte_context * 8, 8) + np.tile(bits, len(byte_rows))
        cursor += count
    return rows, contexts


def evaluate(rows: np.ndarray, contexts: np.ndarray, truth: np.ndarray,
             parent_p1: np.ndarray, raw_positions: np.ndarray,
             raw_bytes: int) -> dict[str, object]:
    context_order = np.argsort(contexts, kind="stable")
    sorted_contexts = contexts[context_order]
    sorted_bits = truth[rows[context_order]].astype(np.int64)
    boundaries = np.flatnonzero(np.diff(sorted_contexts)) + 1
    starts = np.concatenate((np.asarray((0,), dtype=np.int64), boundaries))
    ends = np.concatenate((boundaries, np.asarray((len(rows),), dtype=np.int64)))
    kt_sorted = np.empty(len(rows), dtype=np.float64)
    for start, end in zip(starts, ends):
        group = sorted_bits[start:end]
        ones_before = np.cumsum(group, dtype=np.int64) - group
        seen_before = np.arange(len(group), dtype=np.int64)
        kt_sorted[start:end] = (ones_before + 0.5) / (seen_before + 1.0)
    kt = np.empty(len(rows), dtype=np.float64)
    kt[context_order] = kt_sorted

    chronological_order = np.argsort(rows, kind="stable")
    ordered_rows = rows[chronological_order]
    bits = truth[ordered_rows]
    parent_q16 = parent_p1[ordered_rows]
    parent = np.clip(parent_q16.astype(np.float64) / 65536.0,
                     1.0 / 65536.0, 65535.0 / 65536.0)
    candidate = np.clip(kt[chronological_order], 1.0 / 65536.0, 65535.0 / 65536.0)
    parent_likelihood = np.where(bits != 0, parent, 1.0 - parent)
    candidate_likelihood = np.where(bits != 0, candidate, 1.0 - candidate)
    evidence_delta = np.log(candidate_likelihood) - np.log(parent_likelihood)
    cumulative = np.cumsum(evidence_delta)
    log_odds_before = np.log(KT_PRIOR / PARENT_PRIOR) + cumulative - evidence_delta
    kt_weight = np.empty_like(log_odds_before)
    positive = log_odds_before >= 0
    kt_weight[positive] = 1.0 / (1.0 + np.exp(-log_odds_before[positive]))
    exponential = np.exp(log_odds_before[~positive])
    kt_weight[~positive] = exponential / (1.0 + exponential)
    mixture = parent + kt_weight * (candidate - parent)
    model_q16 = np.clip(np.rint(mixture * 65536.0), 1, 65535).astype(np.uint16)

    zero_qbits, one_qbits = base.qbit_tables()
    parent_loss = np.where(bits != 0, one_qbits[parent_q16], zero_qbits[parent_q16]).astype(np.int64)
    model_loss = np.where(bits != 0, one_qbits[model_q16], zero_qbits[model_q16]).astype(np.int64)
    gain = parent_loss - model_loss
    positions = raw_positions[ordered_rows // 8]
    split = np.minimum(2, (positions.astype(np.int64) * 3) // max(1, raw_bytes))
    split_qbits = np.bincount(split, weights=gain, minlength=3).astype(np.int64)
    gain_qbits = int(gain.sum())
    return {
        "rows": int(len(rows)),
        "contexts": int(len(starts)),
        "parent_qbits": int(parent_loss.sum()),
        "model_qbits": int(model_loss.sum()),
        "gain_qbits": gain_qbits,
        "gain_bytes": gain_qbits / (base.QBITS_PER_BIT * 8),
        "chronological_gain_qbits": [int(value) for value in split_qbits],
        "chronological_gain_bytes": [float(value) / (base.QBITS_PER_BIT * 8) for value in split_qbits],
        "final_kt_weight": float(kt_weight[-1]) if len(kt_weight) else KT_PRIOR,
    }


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
    magic, parent_p1 = janus.read_p1(args.parent_p1, len(parsed.stream) * 8)
    truth = np.unpackbits(np.frombuffer(parsed.stream, dtype=np.uint8), bitorder="big")

    raw_positions = np.zeros(len(parsed.stream), dtype=np.int32)
    for event_index, event in enumerate(parsed.events):
        raw_positions[event.start:event.end] = int(event_map.raw_starts[event_index])
    raw_positions[parsed.events[-1].end:] = len(raw) - 1

    pages, occurrences, rule_ledger = qp1.build_universe(raw, event_map)
    rule_values = base.select_values(qm1.values_for_rules(raw, event_map, occurrences))
    ordinary_values = base.select_values(qm1.ordinary_xml_values(raw, event_map, pages))
    true_labels = base.labels_for(rule_values)
    shuffled = base.shuffled_labels(rule_values, true_labels)
    flat = np.zeros(len(rule_values), dtype=np.int32)
    ordinary_labels = base.labels_for(ordinary_values)

    rule_rows, true_contexts = build_prefix_rows(parsed, rule_values, true_labels)
    _, shuffled_contexts = build_prefix_rows(parsed, rule_values, shuffled)
    _, flat_contexts = build_prefix_rows(parsed, rule_values, flat)
    ordinary_rows, ordinary_contexts = build_prefix_rows(parsed, ordinary_values, ordinary_labels)

    arms = {
        "F0": {"rows": int(len(rule_rows)), "gain_qbits": 0, "gain_bytes": 0.0,
               "chronological_gain_bytes": [0.0, 0.0, 0.0]},
        "E0": evaluate(ordinary_rows, ordinary_contexts, truth, parent_p1, raw_positions, len(raw)),
        "C0": evaluate(rule_rows, flat_contexts, truth, parent_p1, raw_positions, len(raw)),
        "S0": evaluate(rule_rows, shuffled_contexts, truth, parent_p1, raw_positions, len(raw)),
        "J0": evaluate(rule_rows, true_contexts, truth, parent_p1, raw_positions, len(raw)),
    }
    repeat = evaluate(rule_rows, true_contexts, truth, parent_p1, raw_positions, len(raw))
    deterministic = repeat == arms["J0"]
    j0 = float(arms["J0"]["gain_bytes"])
    margins = {name: j0 - float(arms[name]["gain_bytes"])
               for name in ("F0", "E0", "C0", "S0")}
    chronological = [float(value) for value in arms["J0"]["chronological_gain_bytes"]]

    failed: list[str] = []
    if j0 < 100000:
        failed.append("J0_gain_below_100000_bytes")
    if any(value <= 0 for value in chronological):
        failed.append("J0_chronological_split_nonpositive")
    for name, value in margins.items():
        if value < 20000:
            failed.append(f"J0_margin_over_{name}_below_20000_bytes")
    if not deterministic:
        failed.append("second_computation_not_identical")

    source_paths = [Path(__file__), Path(qp1.__file__), Path(qm1.__file__),
                    Path(base.__file__), Path(janus.__file__), Path(wrt_exact.__file__)]
    source_blob = b"".join(path.name.encode("ascii") + b"\0" + path.read_bytes()
                           for path in source_paths)
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    (args.output_dir / "source_package.lzma").write_bytes(source_package)

    decision = {
        "schema": "enwiki9_fractal4_slot_sleeping_trie_qm2_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "correct_parent_free_partition_ceiling_zero_credit",
        "verdict": "promote_to_paid_slot_sleeping_trie" if not failed else "retire_slot_sleeping_trie_realization",
        "inputs": {
            "raw_bytes": len(raw),
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "wrt_stream_bytes": len(parsed.stream),
            "wrt_stream_sha256": hashlib.sha256(parsed.stream).hexdigest(),
            "parent_p1_magic": magic,
            "parent_p1_bytes": args.parent_p1.stat().st_size,
            "parent_p1_sha256": hashlib.sha256(args.parent_p1.read_bytes()).hexdigest(),
        },
        "population": {
            "pages": len(pages),
            "rules": len(rule_ledger),
            "selected_rule_values": len(rule_values),
            "selected_ordinary_values": len(ordinary_values),
            "prefix_bytes": 2,
            "parent_prior": PARENT_PRIOR,
            "kt_prior": KT_PRIOR,
        },
        "arms": arms,
        "margins_bytes": margins,
        "proof": {
            "wrt_store_inverse_exact": True,
            "raw_inverse_exact": True,
            "continuation_context_uses_only_completed_preceding_bytes": True,
            "KT_counts_use_only_prior_same_context_bits": True,
            "global_bayes_envelope_has_exact_parent_expert": True,
            "second_computation_identical": deterministic,
        },
        "accounting": {
            "source_package_bytes_reported_not_debited_at_free_gate": len(source_package),
            "form_partition_and_slot_identities_free": True,
            "score_credit_bytes": 0,
        },
        "failed_conditions": failed,
    }
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_id": CANDIDATE_ID,
        "J0_gain_bytes": j0,
        "margins_bytes": margins,
        "chronological_gain_bytes": chronological,
        "population": decision["population"],
        "failed_conditions": failed,
        "verdict": decision["verdict"],
        "output": str(args.output_dir / "decision.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
