#!/usr/bin/env python3
"""Correct-parent FRACTAL slot residual quotient free ceiling."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path

import numpy as np

import fractal2_endpoint428_paid_mdl_qp1 as qp1
import fractal2_form_echo_joint_qm1 as qm1
import janus_paid_residual_mdl_oracle as janus
import wrt_exact


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fractal4_slot_residual_quotient_qm1_v1"
PERIOD_BITS = 128
SHIFTS = np.asarray((-2.0, -1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0), dtype=np.float64)
PRIOR = np.asarray((0.01, 0.01, 0.01, 0.01, 0.92, 0.01, 0.01, 0.01, 0.01), dtype=np.float64)
QBITS_PER_BIT = 2048


def select_values(values: list[qm1.Value]) -> list[qm1.Value]:
    ordered = sorted(values, key=lambda value: (
        value.span.lo, -(value.span.hi - value.span.lo),
        value.family, value.key,
    ))
    selected: list[qm1.Value] = []
    high = -1
    for value in ordered:
        if value.span.lo < high or value.span.hi <= value.span.lo:
            continue
        selected.append(value)
        high = value.span.hi
    return selected


def labels_for(values: list[qm1.Value]) -> np.ndarray:
    keys = sorted({f"{value.family}\0{value.key}" for value in values})
    indexes = {key: index for index, key in enumerate(keys)}
    return np.asarray([
        indexes[f"{value.family}\0{value.key}"] for value in values
    ], dtype=np.int32)


def shuffled_labels(values: list[qm1.Value], labels: np.ndarray) -> np.ndarray:
    result = labels.copy()
    buckets: dict[int, list[int]] = {}
    for index, value in enumerate(values):
        width = max(1, value.span.hi - value.span.lo)
        bucket = min(31, width.bit_length() - 1)
        buckets.setdefault(bucket, []).append(index)
    for indexes in buckets.values():
        if len(indexes) > 1:
            rotated = [labels[indexes[-1]], *(labels[index] for index in indexes[:-1])]
            result[np.asarray(indexes, dtype=np.int64)] = np.asarray(rotated, dtype=np.int32)
    return result


def build_rows(parsed: wrt_exact.ParsedStore, values: list[qm1.Value],
               labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    byte_spans: list[tuple[int, int]] = []
    total = 0
    for value in values:
        low, high, _ = qp1.span_bytes(parsed, value.span)
        byte_spans.append((low, high))
        total += (high - low) * 8
    rows = np.empty(total, dtype=np.int32)
    contexts = np.empty(total, dtype=np.int32)
    cursor = 0
    for label, (low, high) in zip(labels, byte_spans):
        count = (high - low) * 8
        target = slice(cursor, cursor + count)
        rows[target] = np.arange(low * 8, high * 8, dtype=np.int32)
        contexts[target] = int(label) * PERIOD_BITS + np.arange(count, dtype=np.int32) % PERIOD_BITS
        cursor += count
    return rows, contexts


def qbit_tables() -> tuple[np.ndarray, np.ndarray]:
    values = np.arange(65536, dtype=np.float64)
    one = np.empty(65536, dtype=np.int32)
    zero = np.empty(65536, dtype=np.int32)
    one[0] = 1 << 30
    zero[65535] = 1 << 30
    one[1:] = np.rint(-np.log2(values[1:] / 65536.0) * QBITS_PER_BIT).astype(np.int32)
    zero[:-1] = np.rint(-np.log2((65536.0 - values[:-1]) / 65536.0) * QBITS_PER_BIT).astype(np.int32)
    return zero, one


def evaluate(rows: np.ndarray, contexts: np.ndarray, truth: np.ndarray,
             parent_p1: np.ndarray, raw_positions: np.ndarray,
             raw_bytes: int) -> dict[str, object]:
    order = np.argsort(contexts, kind="stable")
    rows_sorted = rows[order]
    contexts_sorted = contexts[order]
    boundaries = np.flatnonzero(np.diff(contexts_sorted)) + 1
    starts = np.concatenate((np.asarray((0,), dtype=np.int64), boundaries))
    ends = np.concatenate((boundaries, np.asarray((len(rows_sorted),), dtype=np.int64)))
    zero_qbits, one_qbits = qbit_tables()
    split_qbits = np.zeros(3, dtype=np.int64)
    total_parent = 0
    total_model = 0

    log_prior = np.log(PRIOR)[:, None]
    for start, end in zip(starts, ends):
        group_rows = rows_sorted[start:end]
        base_q16 = parent_p1[group_rows]
        bits = truth[group_rows]
        base = np.clip(base_q16.astype(np.float64) / 65536.0, 1.0 / 65536.0, 65535.0 / 65536.0)
        logits = np.log(base / (1.0 - base))[None, :] + SHIFTS[:, None]
        experts = 1.0 / (1.0 + np.exp(-logits))
        likelihood = np.where(bits[None, :] != 0, experts, 1.0 - experts)
        log_likelihood = np.log(np.clip(likelihood, 1e-300, 1.0))
        cumulative = np.cumsum(log_likelihood, axis=1)
        prior_scores = np.empty_like(cumulative)
        prior_scores[:, 0] = log_prior[:, 0]
        if cumulative.shape[1] > 1:
            prior_scores[:, 1:] = log_prior + cumulative[:, :-1]
        maximum = prior_scores.max(axis=0, keepdims=True)
        weights = np.exp(prior_scores - maximum)
        weights /= weights.sum(axis=0, keepdims=True)
        mixture = np.sum(weights * experts, axis=0)
        model_q16 = np.clip(np.rint(mixture * 65536.0), 1, 65535).astype(np.uint16)
        parent_loss = np.where(bits != 0, one_qbits[base_q16], zero_qbits[base_q16]).astype(np.int64)
        model_loss = np.where(bits != 0, one_qbits[model_q16], zero_qbits[model_q16]).astype(np.int64)
        gain = parent_loss - model_loss
        positions = raw_positions[group_rows // 8]
        split = np.minimum(2, (positions.astype(np.int64) * 3) // max(1, raw_bytes))
        split_qbits += np.bincount(split, weights=gain, minlength=3).astype(np.int64)
        total_parent += int(parent_loss.sum())
        total_model += int(model_loss.sum())

    gain_qbits = total_parent - total_model
    return {
        "rows": int(len(rows)),
        "contexts": int(len(starts)),
        "parent_qbits": total_parent,
        "model_qbits": total_model,
        "gain_qbits": gain_qbits,
        "gain_bytes": gain_qbits / (QBITS_PER_BIT * 8),
        "chronological_gain_qbits": [int(value) for value in split_qbits],
        "chronological_gain_bytes": [float(value) / (QBITS_PER_BIT * 8) for value in split_qbits],
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
    if len(parent_p1) != len(truth):
        raise RuntimeError("parent trace row count mismatch")

    raw_positions = np.zeros(len(parsed.stream), dtype=np.int32)
    for event_index, event in enumerate(parsed.events):
        raw_positions[event.start:event.end] = int(event_map.raw_starts[event_index])
    raw_positions[parsed.events[-1].end:] = len(raw) - 1

    pages, occurrences, rule_ledger = qp1.build_universe(raw, event_map)
    rule_values = select_values(qm1.values_for_rules(raw, event_map, occurrences))
    ordinary_values = select_values(qm1.ordinary_xml_values(raw, event_map, pages))
    true_labels = labels_for(rule_values)
    shuffled = shuffled_labels(rule_values, true_labels)
    flat = np.zeros(len(rule_values), dtype=np.int32)
    ordinary_labels = labels_for(ordinary_values)

    rule_rows, true_contexts = build_rows(parsed, rule_values, true_labels)
    _, shuffled_contexts = build_rows(parsed, rule_values, shuffled)
    _, flat_contexts = build_rows(parsed, rule_values, flat)
    ordinary_rows, ordinary_contexts = build_rows(parsed, ordinary_values, ordinary_labels)

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
                    Path(janus.__file__), Path(wrt_exact.__file__)]
    source_blob = b"".join(path.name.encode("ascii") + b"\0" + path.read_bytes()
                           for path in source_paths)
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    (args.output_dir / "source_package.lzma").write_bytes(source_package)

    decision = {
        "schema": "enwiki9_fractal4_slot_residual_quotient_qm1_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "correct_parent_free_partition_ceiling_zero_credit",
        "verdict": "promote_to_paid_slot_quotient" if not failed else "retire_slot_quotient_realization",
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
            "period_bits": PERIOD_BITS,
            "logit_shifts": SHIFTS.tolist(),
            "prior": PRIOR.tolist(),
        },
        "arms": arms,
        "margins_bytes": margins,
        "proof": {
            "wrt_store_inverse_exact": True,
            "raw_inverse_exact": True,
            "online_bayes_uses_only_prior_same_context_truth": True,
            "q16_probabilities_and_integer_qbit_loss": True,
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
