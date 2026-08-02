#!/usr/bin/env python3
"""Exact same-stream sleeping-continuation shadow over endpoint428.

The coded alphabet is the parent's WRT bitstream.  A structural opportunity is
opened only after the WRT event that completes its raw marker has been decoded.
Each candidate continuation was learned from an earlier completed 32-byte WRT
span.  The literal branch uses the exact parent P1 probability on every bit.
"""

from __future__ import annotations

import argparse
from array import array
from dataclasses import dataclass, field
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
RAW_PARENT = ROOT / "programs/typed_event_sleeping_trie_raw_v0/program.py"
sys.path.insert(0, str(TOOLS))

from wrt_exact import ParsedStore, WrtEvent, parse_store  # noqa: E402


def _load_raw_parent():
    spec = importlib.util.spec_from_file_location("_tesbe_raw_parent", RAW_PARENT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load TESBE-Raw parent")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RAW = _load_raw_parent()
TOTAL = 1 << 16
WEIGHT_TOTAL = RAW.WEIGHT_TOTAL
MIN_LITERAL_WEIGHT = RAW.MIN_LITERAL_WEIGHT
CONTINUATION_BYTES = RAW.CONTINUATION_BYTES
MIN_CANDIDATES = RAW.MIN_CANDIDATES
LITERAL_PRIOR = RAW.LITERAL_PRIOR
PROFILES = ("C0", "E0", "E1")
GLOBAL_LOG_SCALE = 1 << 20
GLOBAL_BASE_PRIOR = 65535
GLOBAL_EVENT_PRIOR = 1
HOLDOUT_STREAM_BYTE = 360_000


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def load_p1(path: Path, expected_rows: int) -> tuple[bytes, array]:
    raw = path.read_bytes()
    if len(raw) < 16 or raw[:8] != b"CMX21P1\0":
        raise ValueError("invalid CMX21P1 trace")
    rows = struct.unpack("<Q", raw[8:16])[0]
    values = array("H")
    values.frombytes(raw[16:])
    if sys.byteorder != "little":
        values.byteswap()
    if rows != len(values) or rows != expected_rows:
        raise ValueError("P1 row declaration differs from WRT truth")
    if 0 in values:
        raise ValueError("P1 trace contains a zero probability")
    return raw[:8], values


def truth_bits(stream: bytes) -> bytearray:
    result = bytearray(len(stream) * 8)
    row = 0
    for value in stream:
        for shift in range(7, -1, -1):
            result[row] = (value >> shift) & 1
            row += 1
    return result


def range_encode(probabilities: array, truth: bytearray) -> bytes:
    output = bytearray()
    x1 = 0
    x2 = 0xFFFFFFFF
    for probability, actual in zip(probabilities, truth):
        p1 = int(probability)
        delta = x2 - x1
        midpoint = x1 + (delta >> 16) * p1 + (
            (delta & 0xFFFF) * p1 >> 16
        )
        if actual:
            x2 = midpoint
        else:
            x1 = midpoint + 1
        while ((x1 ^ x2) & 0xFF000000) == 0:
            output.append((x2 >> 24) & 0xFF)
            x1 = (x1 << 8) & 0xFFFFFFFF
            x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
    while ((x1 ^ x2) & 0xFF000000) == 0:
        output.append((x2 >> 24) & 0xFF)
        x1 = (x1 << 8) & 0xFFFFFFFF
        x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
    output.append((x2 >> 24) & 0xFF)
    return bytes(output)


def range_decode_equal(
    payload: bytes,
    probabilities: array,
    truth: bytearray,
) -> bool:
    if len(payload) < 4:
        return False
    cursor = 4
    code = int.from_bytes(payload[:4], "big")
    x1 = 0
    x2 = 0xFFFFFFFF
    for probability, actual in zip(probabilities, truth):
        p1 = int(probability)
        delta = x2 - x1
        midpoint = x1 + (delta >> 16) * p1 + (
            (delta & 0xFFFF) * p1 >> 16
        )
        if code <= midpoint:
            decoded = 1
            x2 = midpoint
        else:
            decoded = 0
            x1 = midpoint + 1
        if decoded != actual:
            return False
        while ((x1 ^ x2) & 0xFF000000) == 0:
            x1 = (x1 << 8) & 0xFFFFFFFF
            x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
            next_byte = payload[cursor] if cursor < len(payload) else 0
            cursor += 1
            code = ((code << 8) & 0xFFFFFFFF) + next_byte
    return True


def bit_likelihood(bit: int, p1: float) -> float:
    probability = p1 / TOTAL
    return probability if bit else 1.0 - probability


def log2_ratio(bit: int, candidate_p1: float, base_p1: float) -> float:
    candidate = bit_likelihood(bit, candidate_p1)
    base = bit_likelihood(bit, base_p1)
    return math.log2(candidate / base)


def logsumexp(values: list[float]) -> float:
    maximum = max(values)
    return maximum + math.log(sum(math.exp(value - maximum) for value in values))


def bayes_mixture_gain(expert_gain_bits: float) -> float:
    base = math.log2(GLOBAL_BASE_PRIOR / TOTAL)
    event = math.log2(GLOBAL_EVENT_PRIOR / TOTAL) + expert_gain_bits
    maximum = max(base, event)
    return maximum + math.log2(2.0 ** (base - maximum) + 2.0 ** (event - maximum))


def posterior_from_log_odds(log_odds: float) -> float:
    if log_odds <= -60.0:
        return 0.0
    if log_odds >= 60.0:
        return 1.0
    odds = 2.0**log_odds
    return odds / (1.0 + odds)


@dataclass
class Candidate:
    continuation: bytes
    fixed_weight: int
    ideal_log_weight: float = 0.0


@dataclass
class Opportunity:
    key: tuple[object, ...]
    candidates: list[Candidate]
    fixed_literal_weight: int
    ideal_literal_log_weight: float
    bits_seen: int = 0
    partial_byte: int = 0
    buffer: bytearray = field(default_factory=bytearray)


class SleepingPredictor:
    def __init__(self, profile: str, stream_bytes: int) -> None:
        self.profile = profile
        self.stream_bytes = stream_bytes
        self.memory = RAW.ReceiptMemory()
        self.active: Opportunity | None = None
        self.opportunities = 0
        self.wakes = 0
        self.active_bits = 0
        self.surviving_bits = 0

    def key(
        self,
        trigger_id: int,
        marker: bytes,
        wiki: Any,
    ) -> tuple[object, ...]:
        history = bytes(wiki.tail)
        before = history[: -len(marker)]
        if self.profile == "C0":
            return (trigger_id,)
        if self.profile == "E0":
            return (trigger_id, RAW._normalized_suffix(before))
        word = RAW._previous_word(before)
        return (
            trigger_id,
            wiki.field_id,
            wiki.mode,
            wiki.slot,
            min(7, wiki.column >> 4),
            RAW._hash_word(word) & 63,
            tuple(RAW._char_class(byte) for byte in before[-3:]),
        )

    def launch(
        self,
        trigger_id: int,
        marker: bytes,
        wiki: Any,
        next_stream_byte: int,
    ) -> None:
        if self.active is not None:
            return
        if next_stream_byte + CONTINUATION_BYTES > self.stream_bytes:
            return
        key = self.key(trigger_id, marker, wiki)
        prior = self.memory.get(key)
        candidates: list[Candidate] = []
        literal_weight = WEIGHT_TOTAL
        literal_log_weight = 0.0
        if len(prior) >= MIN_CANDIDATES:
            unit = WEIGHT_TOTAL // (LITERAL_PRIOR + len(prior))
            candidates = [Candidate(value, unit) for value in prior]
            literal_weight = WEIGHT_TOTAL - unit * len(candidates)
            literal_log_weight = math.log(float(LITERAL_PRIOR))
            self.wakes += 1
        self.active = Opportunity(
            key=key,
            candidates=candidates,
            fixed_literal_weight=literal_weight,
            ideal_literal_log_weight=literal_log_weight,
        )
        self.opportunities += 1

    @staticmethod
    def _candidate_bit(candidate: Candidate, offset: int) -> int:
        return (
            candidate.continuation[offset >> 3]
            >> (7 - (offset & 7))
        ) & 1

    def fixed_probability(self, base_p1: int) -> int:
        active = self.active
        if active is None or not active.candidates:
            return base_p1
        offset = active.bits_seen
        fixed_total = active.fixed_literal_weight + sum(
            candidate.fixed_weight for candidate in active.candidates
        )
        fixed_one = sum(
            candidate.fixed_weight
            for candidate in active.candidates
            if self._candidate_bit(candidate, offset)
        )
        fixed_p1 = (
            active.fixed_literal_weight * base_p1 + fixed_one * TOTAL
        ) // fixed_total
        fixed_p1 = max(1, min(TOTAL - 1, fixed_p1))
        return fixed_p1

    def ideal_gain(self, bit: int, base_p1: int) -> float:
        active = self.active
        if active is None or not active.candidates:
            return 0.0
        offset = active.bits_seen
        base_like = (base_p1 if bit else TOTAL - base_p1) / TOTAL
        denominator = logsumexp(
            [active.ideal_literal_log_weight]
            + [candidate.ideal_log_weight for candidate in active.candidates]
        )
        numerator_terms = [
            active.ideal_literal_log_weight + math.log(base_like)
        ]
        numerator_terms.extend(
            candidate.ideal_log_weight
            for candidate in active.candidates
            if self._candidate_bit(candidate, offset) == bit
        )
        mixed_log_likelihood = logsumexp(numerator_terms) - denominator
        return (mixed_log_likelihood - math.log(base_like)) / math.log(2.0)

    def update(self, bit: int, base_p1: int) -> None:
        active = self.active
        if active is None:
            return
        offset = active.bits_seen
        if active.candidates:
            survivors = [
                candidate
                for candidate in active.candidates
                if self._candidate_bit(candidate, offset) == bit
            ]
            base_like = base_p1 if bit else TOTAL - base_p1

            active.ideal_literal_log_weight += math.log(base_like / TOTAL)
            if survivors:
                maximum = max(
                    [active.ideal_literal_log_weight]
                    + [candidate.ideal_log_weight for candidate in survivors]
                )
                active.ideal_literal_log_weight -= maximum
                for candidate in survivors:
                    candidate.ideal_log_weight -= maximum
            else:
                active.ideal_literal_log_weight = 0.0

            literal_numerator = active.fixed_literal_weight * base_like
            candidate_numerator = sum(
                candidate.fixed_weight for candidate in survivors
            ) * TOTAL
            denominator = literal_numerator + candidate_numerator
            if survivors and denominator:
                new_literal = max(
                    MIN_LITERAL_WEIGHT,
                    WEIGHT_TOTAL * literal_numerator // denominator,
                )
                budget = WEIGHT_TOTAL - new_literal
                old_total = sum(candidate.fixed_weight for candidate in survivors)
                assigned = 0
                for candidate in survivors:
                    candidate.fixed_weight = budget * candidate.fixed_weight // old_total
                    assigned += candidate.fixed_weight
                survivors[0].fixed_weight += budget - assigned
                active.fixed_literal_weight = new_literal
                self.surviving_bits += 1
            else:
                active.fixed_literal_weight = WEIGHT_TOTAL
            active.candidates = survivors
            self.active_bits += 1

        active.partial_byte = (active.partial_byte << 1) | bit
        active.bits_seen += 1
        if active.bits_seen & 7 == 0:
            active.buffer.append(active.partial_byte)
            active.partial_byte = 0
        if active.bits_seen == CONTINUATION_BYTES * 8:
            self.memory.add(active.key, bytes(active.buffer))
            self.active = None

    def receipt(self) -> dict[str, int]:
        return {
            "opportunities": self.opportunities,
            "wakes": self.wakes,
            "active_bits": self.active_bits,
            "surviving_bits": self.surviving_bits,
            "memory_keys": len(self.memory.rows),
        }


def completed_events(parsed: ParsedStore) -> dict[int, WrtEvent]:
    result: dict[int, WrtEvent] = {}
    for event in parsed.events:
        if event.end in result:
            raise ValueError("two WRT events share a completion boundary")
        result[event.end] = event
    return result


def trigger(wiki: Any) -> tuple[int, bytes] | None:
    tail = bytes(wiki.tail)
    for trigger_id, marker in enumerate(RAW.TRIGGERS):
        if tail.endswith(marker):
            return trigger_id, marker
    return None


def run_probabilities(
    parsed: ParsedStore,
    base: array,
    truth: bytearray,
) -> tuple[dict[str, array], dict[str, Any]]:
    candidates = {name: array("H", base) for name in PROFILES}
    candidates["M1"] = array("H", base)
    predictors = {
        name: SleepingPredictor(name, len(parsed.stream)) for name in PROFILES
    }
    wiki = RAW.WikiState()
    endings = completed_events(parsed)
    ideal_gain = {name: 0.0 for name in PROFILES}
    profile_ideal_holdout_gain = {name: 0.0 for name in PROFILES}
    m1_q16_gain = 0.0
    m1_q16_holdout_gain = 0.0
    e1_cumulative_gain = 0.0
    e1_gain_at_holdout = 0.0
    global_log_odds_q20 = round(
        math.log2(GLOBAL_EVENT_PRIOR / GLOBAL_BASE_PRIOR) * GLOBAL_LOG_SCALE
    )
    holdout_row = HOLDOUT_STREAM_BYTE * 8

    for row, truth_value in enumerate(truth):
        bit = int(truth_value)
        base_p1 = int(base[row])
        fixed_rows: dict[str, int] = {}
        row_ideal_gain: dict[str, float] = {}
        if row == holdout_row:
            e1_gain_at_holdout = e1_cumulative_gain
        for name, predictor in predictors.items():
            fixed_p1 = predictor.fixed_probability(base_p1)
            candidates[name][row] = fixed_p1
            fixed_rows[name] = fixed_p1
            gain = predictor.ideal_gain(bit, base_p1)
            row_ideal_gain[name] = gain
            ideal_gain[name] += gain
            if row >= holdout_row:
                profile_ideal_holdout_gain[name] += gain
        current_e1_gain = row_ideal_gain["E1"]
        e1_cumulative_gain += current_e1_gain

        e1_fixed_p1 = fixed_rows["E1"]
        if e1_fixed_p1 == base_p1:
            m1_p1 = base_p1
            fixed_increment = 0.0
        else:
            posterior = posterior_from_log_odds(
                global_log_odds_q20 / GLOBAL_LOG_SCALE
            )
            m1_p1 = round(
                (1.0 - posterior) * base_p1 + posterior * e1_fixed_p1
            )
            m1_p1 = max(1, min(TOTAL - 1, m1_p1))
            fixed_increment = log2_ratio(bit, e1_fixed_p1, base_p1)
        candidates["M1"][row] = m1_p1
        global_log_odds_q20 += round(fixed_increment * GLOBAL_LOG_SCALE)
        current_m1_gain = log2_ratio(bit, m1_p1, base_p1)
        m1_q16_gain += current_m1_gain
        if row >= holdout_row:
            m1_q16_holdout_gain += current_m1_gain

        for name, predictor in predictors.items():
            predictor.update(bit, base_p1)

        if row & 7 == 7:
            next_stream_byte = row // 8 + 1
            event = endings.get(next_stream_byte)
            if event is not None:
                for byte in event.decoded:
                    wiki.update(byte)
                fired = trigger(wiki)
                if fired is not None:
                    for predictor in predictors.values():
                        predictor.launch(*fired, wiki, next_stream_byte)

    ideal_closed_form = bayes_mixture_gain(e1_cumulative_gain)
    ideal_prefix_gain = bayes_mixture_gain(e1_gain_at_holdout)
    m0_ideal_holdout_gain = ideal_closed_form - ideal_prefix_gain
    metadata = {
        "predictors": {name: value.receipt() for name, value in predictors.items()},
        "ideal_gain_bits": ideal_gain,
        "ideal_holdout_gain_bits": profile_ideal_holdout_gain,
        "m0_ideal_gain_bits": ideal_closed_form,
        "m0_ideal_holdout_gain_bits": m0_ideal_holdout_gain,
        "m0_closed_form_gain_bits": ideal_closed_form,
        "m0_prefix_gain_bits_at_holdout": ideal_prefix_gain,
        "m1_q16_gain_bits": m1_q16_gain,
        "m1_q16_holdout_gain_bits": m1_q16_holdout_gain,
        "global_log_odds_q20_final": global_log_odds_q20,
        "wiki_state": {
            "field_id": wiki.field_id,
            "mode": wiki.mode,
            "slot": wiki.slot,
            "link_depth": wiki.link_depth,
            "template_depth": wiki.template_depth,
            "ref_depth": wiki.ref_depth,
        },
    }
    return candidates, metadata


def exact_payloads(
    base: array,
    truth: bytearray,
    candidates: dict[str, array],
    holdout_row: int,
) -> tuple[dict[str, bytes], dict[str, bytes], dict[str, bool]]:
    full = {"B0": range_encode(base, truth)}
    heldout = {"B0": range_encode(base[holdout_row:], truth[holdout_row:])}
    decoded: dict[str, bool] = {}
    for name, probabilities in candidates.items():
        full[name] = range_encode(probabilities, truth)
        heldout[name] = range_encode(
            probabilities[holdout_row:], truth[holdout_row:]
        )
        decoded[name] = (
            range_decode_equal(full[name], probabilities, truth)
            and range_decode_equal(
                heldout[name], probabilities[holdout_row:], truth[holdout_row:]
            )
        )
    return full, heldout, decoded


def build_receipt(args: argparse.Namespace) -> dict[str, Any]:
    parsed = parse_store(args.store, args.dictionary)
    raw = args.raw.read_bytes()[: parsed.raw_length]
    if raw != parsed.decoded:
        raise ValueError("WRT store does not reconstruct the declared raw input")
    truth = truth_bits(parsed.stream)
    p1_magic, base = load_p1(args.base_p1, len(truth))
    first, first_meta = run_probabilities(parsed, base, truth)
    second, second_meta = run_probabilities(parsed, base, truth)
    deterministic = {
        name: first[name] == second[name] for name in first
    }
    deterministic["metadata"] = first_meta == second_meta
    if not all(deterministic.values()):
        raise ValueError("probability replay is nondeterministic")

    holdout_row = HOLDOUT_STREAM_BYTE * 8
    full, heldout, decoded = exact_payloads(base, truth, first, holdout_row)
    if not all(decoded.values()):
        raise ValueError("candidate arithmetic decode failed")
    archive = args.parent_archive.read_bytes()
    parent_payload_identity = (
        len(archive) == args.archive_header_bytes + len(full["B0"])
        and archive[args.archive_header_bytes :] == full["B0"]
    )
    if not parent_payload_identity:
        raise ValueError("baseline replay differs from parent arithmetic payload")

    payload_bytes = {name: len(value) for name, value in full.items()}
    heldout_bytes = {name: len(value) for name, value in heldout.items()}
    full_gain = {
        name: payload_bytes["B0"] - value for name, value in payload_bytes.items()
    }
    heldout_gain = {
        name: heldout_bytes["B0"] - value for name, value in heldout_bytes.items()
    }
    selected = min(payload_bytes, key=lambda name: (payload_bytes[name], name))
    selected_framed_bytes = payload_bytes[selected] + 1
    holdout_raw_estimate = parsed.raw_length * (
        (len(parsed.stream) - HOLDOUT_STREAM_BYTE) / len(parsed.stream)
    )
    m1_holdout_per_million = (
        heldout_gain["M1"] * 1_000_000 / holdout_raw_estimate
    )
    typed_control_pass = (
        heldout_gain["E1"] > heldout_gain["C0"]
        and heldout_gain["E1"] > heldout_gain["E0"]
    )
    ideal_m0 = float(first_meta["m0_ideal_gain_bits"])
    m1_gain = float(first_meta["m1_q16_gain_bits"])
    fixed_overhead_fraction = (
        max(0.0, ideal_m0 - m1_gain) / ideal_m0 if ideal_m0 > 0.0 else None
    )
    fixed_overhead_pass = (
        fixed_overhead_fraction is not None and fixed_overhead_fraction < 0.05
    )
    bayes_safety_floor_bits = math.log2(GLOBAL_BASE_PRIOR / TOTAL)
    bayes_safety_pass = ideal_m0 + 1e-9 >= bayes_safety_floor_bits
    promotion_pass = (
        typed_control_pass
        and m1_holdout_per_million >= 2100.0
        and fixed_overhead_pass
        and bayes_safety_pass
    )
    verdict = (
        "promote_to_current_parent_native_integration_gate"
        if promotion_pass
        else "reject_frozen_endpoint428_sleeping_continuation_realization"
    )

    return {
        "schema": "typed_event_sleeping_bayes_endpoint428_v0",
        "evidence_level": "causal_shadow",
        "algorithm": (
            "same-stream completed-trigger continuation point masses with exact "
            "endpoint428 literal fallback and a 65535:1 global Bayes envelope"
        ),
        "inputs": {
            "base_p1": artifact(args.base_p1),
            "base_p1_magic": p1_magic.decode("ascii", errors="replace"),
            "wrt_store": artifact(args.store),
            "dictionary": artifact(args.dictionary),
            "raw_input": artifact(args.raw),
            "parent_archive": artifact(args.parent_archive),
        },
        "scope": {
            "raw_bytes": parsed.raw_length,
            "wrt_stream_bytes": len(parsed.stream),
            "rows": len(truth),
            "events": len(parsed.events),
            "event_kind_counts": parsed.kind_counts,
            "holdout_start_wrt_byte": HOLDOUT_STREAM_BYTE,
            "holdout_wrt_bytes": len(parsed.stream) - HOLDOUT_STREAM_BYTE,
            "holdout_raw_bytes_estimate_by_stream_fraction": holdout_raw_estimate,
        },
        "frozen_parameters": {
            "triggers_hex": [value.hex() for value in RAW.TRIGGERS],
            "continuation_bytes": CONTINUATION_BYTES,
            "max_keys": RAW.MAX_KEYS,
            "max_candidates": RAW.MAX_CANDIDATES,
            "minimum_candidates": MIN_CANDIDATES,
            "literal_prior": LITERAL_PRIOR,
            "local_weight_total": WEIGHT_TOTAL,
            "local_min_literal_weight": MIN_LITERAL_WEIGHT,
            "global_base_prior": GLOBAL_BASE_PRIOR,
            "global_event_prior": GLOBAL_EVENT_PRIOR,
            "global_log_odds_fraction_bits": 20,
        },
        "exact_arithmetic": {
            "payload_bytes": payload_bytes,
            "gain_vs_b0_bytes": full_gain,
            "heldout_payload_bytes": heldout_bytes,
            "heldout_gain_vs_b0_bytes": heldout_gain,
            "payload_sha256": {
                name: sha256_bytes(value) for name, value in full.items()
            },
            "candidate_roundtrip": decoded,
            "parent_payload_identity": parent_payload_identity,
            "parent_archive_header_bytes": args.archive_header_bytes,
            "global_selector_selected": selected,
            "global_selector_payload_bytes": payload_bytes[selected],
            "global_selector_framed_bytes_with_mode_byte": selected_framed_bytes,
            "global_selector_gain_vs_b0_after_framing": (
                payload_bytes["B0"] - selected_framed_bytes
            ),
        },
        "ideal_and_quantized": first_meta,
        "proof": {
            "raw_wrt_inverse_ok": True,
            "same_coded_bitstream": True,
            "current_event_released_only_at_completion": True,
            "fixed_continuation_length_public": True,
            "memory_updates_after_full_continuation": True,
            "literal_probability_equals_parent_when_sleeping": True,
            "all_models_update_on_every_actual_bit": True,
            "ideal_bayes_safety_floor_gain_bits": bayes_safety_floor_bits,
            "ideal_bayes_safety_pass": bayes_safety_pass,
            "determinism": deterministic,
        },
        "economics": {
            "typed_control_pass": typed_control_pass,
            "m1_holdout_saved_bytes_per_proportional_raw_1m": (
                m1_holdout_per_million
            ),
            "required_holdout_saved_bytes_per_proportional_raw_1m": 2100.0,
            "m0_ideal_gain_bits": ideal_m0,
            "m1_q16_gain_bits": m1_gain,
            "fixed_overhead_fraction_of_positive_ideal_gain": (
                fixed_overhead_fraction
            ),
            "fixed_overhead_below_5_percent": fixed_overhead_pass,
            "provisional_python_source_bytes": (
                Path(__file__).stat().st_size + RAW_PARENT.stat().st_size
            ),
            "score_credit_bytes": 0,
        },
        "decision": {
            "verdict": verdict,
            "promotion_authorized": promotion_pass,
            "native_integration_authorized": promotion_pass,
            "current_parent_source_recovered": False,
            "full_1g_authorized": False,
        },
        "claim_boundary": (
            "This is a causal_shadow over the surviving archive-identical older "
            "endpoint428 P1 stream. It is not the current pair/layer-0 parent, "
            "changes no native archive, receives zero score credit, and proves no "
            "full_corpus_official result."
        ),
        "sources": {
            "tool": artifact(Path(__file__)),
            "raw_sleeping_trie_donor": artifact(RAW_PARENT),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--base-p1", type=Path, required=True)
    parser.add_argument("--parent-archive", type=Path, required=True)
    parser.add_argument("--archive-header-bytes", type=int, default=37)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for path in (
        args.store,
        args.dictionary,
        args.raw,
        args.base_p1,
        args.parent_archive,
    ):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    receipt = build_receipt(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
