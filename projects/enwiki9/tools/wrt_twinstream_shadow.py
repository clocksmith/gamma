#!/usr/bin/env python3
"""Exact causal-shadow screen for D02 TWINSTREAM.

The unchanged WRT stream is replayed with five controls. Raw bytes become
visible only after the complete WRT emission group that determines them.
Every reported archive is a fresh arithmetic replay, but remains a shadow:
none of its byte gains changes the source-bound Hutter frontier.
"""

from __future__ import annotations

import argparse
from collections import Counter, OrderedDict
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any

from fx2_shadow_residual_coder import BinaryArithmeticEncoder, TOTAL, clamp_p1
from wrt_exact import ParsedStore, parse_store


CONTROL_NAMES = ("P0_WRT", "P1_RAW", "P2_SHARED", "P3_REVERSE", "PX_MATCHED")
PARTITIONS = ("train", "development", "holdout")
QBIT_ZERO = tuple(
    int(-math.log2((TOTAL - p1) / TOTAL) * 256.0 + 0.5)
    for p1 in range(1, TOTAL)
)
QBIT_ONE = tuple(
    int(-math.log2(p1 / TOTAL) * 256.0 + 0.5)
    for p1 in range(1, TOTAL)
)


def fast_qbits(bit: int, p1: int) -> int:
    index = clamp_p1(p1) - 1
    return QBIT_ONE[index] if bit else QBIT_ZERO[index]


def blend(base: int, endpoint: int, ppm: int) -> int:
    return clamp_p1((base * (1_000_000 - ppm) + endpoint * ppm) // 1_000_000)


def fnv64(seed: int, data: bytes) -> int:
    value = seed & 0xFFFFFFFFFFFFFFFF
    for byte in data:
        value ^= byte
        value = (value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def partition_for_page(page_index: int) -> str:
    residue = page_index % 5
    if residue in {0, 1, 2}:
        return "train"
    if residue == 3:
        return "development"
    return "holdout"


@dataclass(frozen=True)
class EmissionGroup:
    start: int
    end: int
    encoded: bytes
    decoded: bytes


def emission_groups(parsed: ParsedStore) -> tuple[EmissionGroup, ...]:
    groups: list[EmissionGroup] = []
    pending = []
    for event in parsed.events:
        pending.append(event)
        if not event.decoded:
            continue
        encoded = b"".join(row.encoded for row in pending)
        decoded = b"".join(row.decoded for row in pending)
        group = EmissionGroup(
            start=pending[0].start,
            end=pending[-1].end,
            encoded=encoded,
            decoded=decoded,
        )
        if parsed.stream[group.start : group.end] != group.encoded:
            raise RuntimeError("emission group does not cover its exact WRT bytes")
        groups.append(group)
        pending.clear()
    if pending:
        group = EmissionGroup(
            start=pending[0].start,
            end=pending[-1].end,
            encoded=b"".join(row.encoded for row in pending),
            decoded=b"",
        )
        if parsed.stream[group.start : group.end] != group.encoded:
            raise RuntimeError("trailing control group does not cover exact WRT bytes")
        groups.append(group)
    complete: list[EmissionGroup] = []
    cursor = 0
    for group in groups:
        if cursor < group.start:
            complete.append(
                EmissionGroup(
                    start=cursor,
                    end=group.start,
                    encoded=parsed.stream[cursor : group.start],
                    decoded=b"",
                )
            )
        complete.append(group)
        cursor = group.end
    if cursor < len(parsed.stream):
        complete.append(
            EmissionGroup(
                start=cursor,
                end=len(parsed.stream),
                encoded=parsed.stream[cursor:],
                decoded=b"",
            )
        )
    return tuple(complete)


class BoundedCounts:
    def __init__(self, capacity: int, alpha: int) -> None:
        self.capacity = capacity
        self.alpha = alpha
        self.rows: OrderedDict[tuple[Any, ...], list[int]] = OrderedDict()
        self.evictions = 0

    def predict(self, key: tuple[Any, ...]) -> int:
        counts = self.rows.get(key)
        if counts is None:
            return TOTAL // 2
        self.rows.move_to_end(key)
        zeros, ones = counts
        return clamp_p1(
            ((ones + self.alpha) * TOTAL)
            // (zeros + ones + 2 * self.alpha)
        )

    def update(self, key: tuple[Any, ...], bit: int) -> None:
        counts = self.rows.get(key)
        if counts is None:
            if len(self.rows) >= self.capacity:
                self.rows.popitem(last=False)
                self.evictions += 1
            counts = [0, 0]
            self.rows[key] = counts
        else:
            self.rows.move_to_end(key)
        counts[bit] += 1
        if counts[0] + counts[1] >= 1 << 15:
            counts[0] = (counts[0] + 1) // 2
            counts[1] = (counts[1] + 1) // 2

    def receipt(self) -> dict[str, int]:
        return {
            "capacity": self.capacity,
            "rows": len(self.rows),
            "evictions": self.evictions,
            "estimated_state_bytes": len(self.rows) * 40,
        }


class ReverseReconstruction:
    """Predict a completed raw signature from a causal WRT group prefix."""

    def __init__(self, capacity: int, prefix_bits: int) -> None:
        self.capacity = capacity
        self.prefix_bits = prefix_bits
        self.rows: OrderedDict[tuple[int, int], Counter[int]] = OrderedDict()
        self.evictions = 0
        self.updates = 0

    def _key(self, bit_count: int, prefix: int) -> tuple[int, int]:
        width = min(bit_count, self.prefix_bits)
        mask = (1 << width) - 1 if width else 0
        return width, prefix & mask

    def predict(self, bit_count: int, prefix: int) -> int:
        row = self.rows.get(self._key(bit_count, prefix))
        if not row:
            return 0
        return min(row, key=lambda value: (-row[value], value))

    def train(self, encoded: bytes, decoded: bytes) -> None:
        raw_signature = fnv64(0xCBF29CE484222325, decoded)
        prefix = 0
        bits = min(8 * len(encoded), self.prefix_bits)
        for bit_count in range(bits + 1):
            key = self._key(bit_count, prefix)
            row = self.rows.get(key)
            if row is None:
                if len(self.rows) >= self.capacity:
                    self.rows.popitem(last=False)
                    self.evictions += 1
                row = Counter()
                self.rows[key] = row
            else:
                self.rows.move_to_end(key)
            row[raw_signature] += 1
            self.updates += 1
            if bit_count < bits:
                byte = encoded[bit_count // 8]
                bit = (byte >> (7 - (bit_count & 7))) & 1
                prefix = ((prefix << 1) | bit) & ((1 << self.prefix_bits) - 1)

    def receipt(self) -> dict[str, int]:
        values = sum(len(row) for row in self.rows.values())
        return {
            "capacity": self.capacity,
            "rows": len(self.rows),
            "values": values,
            "evictions": self.evictions,
            "updates": self.updates,
            "estimated_state_bytes": len(self.rows) * 40 + values * 16,
        }


class TwinState:
    def __init__(self, capacity: int, alpha: int, reverse_capacity: int) -> None:
        self.tables = {
            name: BoundedCounts(capacity, alpha)
            for name in CONTROL_NAMES
        }
        self.reverse = ReverseReconstruction(reverse_capacity, prefix_bits=16)
        self.wrt_history = bytearray()
        self.raw_history = bytearray()
        self.shared_state = 0x9E3779B97F4A7C15
        self.group_prefix = 0
        self.group_prefix_bits = 0
        self.cpu_ns = {name: 0 for name in CONTROL_NAMES}
        self.predictions = {name: 0 for name in CONTROL_NAMES}

    @staticmethod
    def _suffix_hash(value: bytearray, width: int, seed: int) -> int:
        return fnv64(seed, bytes(value[-width:]))

    def keys(self, bit_position: int, byte_prefix: int) -> dict[str, tuple[Any, ...]]:
        wrt8 = self._suffix_hash(self.wrt_history, 8, 0xCBF29CE484222325)
        raw8 = self._suffix_hash(self.raw_history, 8, 0x84222325CBF29CE4)
        raw16 = self._suffix_hash(self.raw_history, 16, 0xD6E8FEB86659FD93)
        reverse_class = self.reverse.predict(
            self.group_prefix_bits,
            self.group_prefix,
        )
        common = (bit_position, byte_prefix)
        return {
            "P0_WRT": common + (wrt8,),
            "P1_RAW": common + (raw8,),
            "P2_SHARED": common + (raw8, self.shared_state),
            "P3_REVERSE": common + (raw8, self.shared_state, reverse_class),
            "PX_MATCHED": common + (raw8, raw16),
        }

    def probabilities(
        self,
        bit_position: int,
        byte_prefix: int,
    ) -> tuple[dict[str, int], dict[str, tuple[Any, ...]]]:
        keys = self.keys(bit_position, byte_prefix)
        probabilities: dict[str, int] = {}
        for name in CONTROL_NAMES:
            started = time.process_time_ns()
            probabilities[name] = self.tables[name].predict(keys[name])
            self.cpu_ns[name] += time.process_time_ns() - started
            self.predictions[name] += 1
        return probabilities, keys

    def update_bit(self, keys: dict[str, tuple[Any, ...]], bit: int) -> None:
        for name in CONTROL_NAMES:
            started = time.process_time_ns()
            self.tables[name].update(keys[name], bit)
            self.cpu_ns[name] += time.process_time_ns() - started
        self.group_prefix = ((self.group_prefix << 1) | bit) & 0xFFFF
        self.group_prefix_bits += 1

    def complete_wrt_byte(self, value: int) -> None:
        self.wrt_history.append(value)
        if len(self.wrt_history) > 32:
            del self.wrt_history[:-32]

    def begin_group(self) -> None:
        self.group_prefix = 0
        self.group_prefix_bits = 0

    def complete_group(self, group: EmissionGroup) -> None:
        self.reverse.train(group.encoded, group.decoded)
        self.shared_state = fnv64(self.shared_state, b"W" + group.encoded)
        self.shared_state = fnv64(self.shared_state, b"R" + group.decoded)
        self.raw_history.extend(group.decoded)
        if len(self.raw_history) > 64:
            del self.raw_history[:-64]

    def receipt(self) -> dict[str, Any]:
        return {
            "tables": {name: table.receipt() for name, table in self.tables.items()},
            "reverse": self.reverse.receipt(),
            "cpu_ns": self.cpu_ns,
            "predictions": self.predictions,
        }


def group_index(parsed: ParsedStore, groups: tuple[EmissionGroup, ...]) -> list[int]:
    index = [-1] * len(parsed.stream)
    for group_id, group in enumerate(groups):
        for position in range(group.start, group.end):
            if index[position] != -1:
                raise RuntimeError("overlapping emission groups")
            index[position] = group_id
    if any(value < 0 for value in index):
        raise RuntimeError("emission groups do not cover the exact WRT stream")
    return index


def scan(
    parsed: ParsedStore,
    groups: tuple[EmissionGroup, ...],
    blends: tuple[int, ...],
    *,
    capacity: int,
    alpha: int,
    reverse_capacity: int,
    exact: bool,
    selected: dict[str, int] | None = None,
) -> dict[str, Any]:
    lookup = group_index(parsed, groups)
    state = TwinState(capacity, alpha, reverse_capacity)
    qbits = {
        partition: {
            name: {ppm: 0 for ppm in blends}
            for name in CONTROL_NAMES[1:]
        }
        for partition in PARTITIONS
    }
    raw_bytes = {partition: 0 for partition in PARTITIONS}
    baseline_qbits = {partition: 0 for partition in PARTITIONS}
    coders: dict[str, dict[str, BinaryArithmeticEncoder]] = {}
    full_coders: dict[str, BinaryArithmeticEncoder] = {}
    if exact:
        if selected is None:
            raise ValueError("selected blends are required for exact replay")
        coder_names = CONTROL_NAMES
        full_coders = {name: BinaryArithmeticEncoder() for name in coder_names}
        coders = {
            partition: {
                name: BinaryArithmeticEncoder()
                for name in coder_names
            }
            for partition in PARTITIONS
        }

    page_index = 0
    active_group = -1
    byte_prefix = 0
    for position, value in enumerate(parsed.stream):
        group_id = lookup[position]
        group = groups[group_id]
        if group_id != active_group:
            active_group = group_id
            state.begin_group()
        partition = partition_for_page(page_index)
        byte_prefix = 0
        for bit_position in range(8):
            bit = (value >> (7 - bit_position)) & 1
            probabilities, keys = state.probabilities(bit_position, byte_prefix)
            base_p1 = probabilities["P0_WRT"]
            baseline_qbits[partition] += fast_qbits(bit, base_p1)
            for name in CONTROL_NAMES[1:]:
                for ppm in blends:
                    candidate_p1 = blend(base_p1, probabilities[name], ppm)
                    qbits[partition][name][ppm] += fast_qbits(bit, candidate_p1)
            if exact:
                full_coders["P0_WRT"].encode(bit, base_p1)
                coders[partition]["P0_WRT"].encode(bit, base_p1)
                for name in CONTROL_NAMES[1:]:
                    candidate_p1 = blend(
                        base_p1,
                        probabilities[name],
                        selected[name],
                    )
                    full_coders[name].encode(bit, candidate_p1)
                    coders[partition][name].encode(bit, candidate_p1)
            state.update_bit(keys, bit)
            byte_prefix = (byte_prefix << 1) | bit
        state.complete_wrt_byte(value)
        if position == group.end - 1:
            raw_bytes[partition] += len(group.decoded)
            state.complete_group(group)
            page_index += group.decoded.count(b"</page>")

    out: dict[str, Any] = {
        "qbits": qbits,
        "baseline_qbits": baseline_qbits,
        "raw_bytes": raw_bytes,
        "pages": page_index,
        "state": state.receipt(),
    }
    if exact:
        for coder in full_coders.values():
            coder.finish()
        for rows in coders.values():
            for coder in rows.values():
                coder.finish()
        out["full_bytes"] = {
            name: coder.byte_count for name, coder in full_coders.items()
        }
        out["partition_bytes"] = {
            partition: {
                name: coder.byte_count for name, coder in rows.items()
            }
            for partition, rows in coders.items()
        }
    return out


def select_blends(
    discovery: dict[str, Any],
    blends: tuple[int, ...],
) -> dict[str, int]:
    selected: dict[str, int] = {}
    baseline = discovery["baseline_qbits"]["development"]
    for name in CONTROL_NAMES[1:]:
        selected[name] = min(
            blends,
            key=lambda ppm: (
                discovery["qbits"]["development"][name][ppm] - baseline,
                ppm,
            ),
        )
    return selected


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = time.process_time_ns()
    parsed = parse_store(args.store, args.dictionary)
    raw = args.raw.read_bytes()
    if len(raw) < parsed.raw_length:
        raise RuntimeError("raw corpus is shorter than the WRT-declared scope")
    raw = raw[: parsed.raw_length]
    if raw != parsed.decoded:
        raise RuntimeError("WRT store does not exactly reconstruct the raw population")
    groups = emission_groups(parsed)
    blends = tuple(
        int(value)
        for value in args.blends_ppm.split(",")
        if value.strip()
    )
    if not blends or any(not 0 < value <= 1_000_000 for value in blends):
        raise ValueError("blend strengths must be in 1..1000000")
    discovery = scan(
        parsed,
        groups,
        blends,
        capacity=args.capacity,
        alpha=args.alpha,
        reverse_capacity=args.reverse_capacity,
        exact=False,
    )
    selected = select_blends(discovery, blends)
    replay = scan(
        parsed,
        groups,
        blends,
        capacity=args.capacity,
        alpha=args.alpha,
        reverse_capacity=args.reverse_capacity,
        exact=True,
        selected=selected,
    )
    controls: dict[str, Any] = {}
    for name in CONTROL_NAMES:
        partitions: dict[str, Any] = {}
        for partition in PARTITIONS:
            baseline = replay["partition_bytes"][partition]["P0_WRT"]
            candidate = replay["partition_bytes"][partition][name]
            population = replay["raw_bytes"][partition]
            saved = baseline - candidate
            partitions[partition] = {
                "raw_bytes": population,
                "p0_bytes": baseline,
                "candidate_bytes": candidate,
                "saved_bytes": saved,
                "saved_bytes_per_1m_raw": (
                    saved * 1_000_000 / population if population else 0.0
                ),
            }
        full_baseline = replay["full_bytes"]["P0_WRT"]
        full_candidate = replay["full_bytes"][name]
        controls[name] = {
            "selected_blend_ppm": 0 if name == "P0_WRT" else selected[name],
            "full_bytes": full_candidate,
            "full_saved_bytes": full_baseline - full_candidate,
            "partitions": partitions,
            "cpu_ns": replay["state"]["cpu_ns"][name],
            "table": replay["state"]["tables"][name],
        }
    primary = max(
        ("P2_SHARED", "P3_REVERSE"),
        key=lambda name: controls[name]["partitions"]["holdout"]["saved_bytes_per_1m_raw"],
    )
    primary_rate = controls[primary]["partitions"]["holdout"]["saved_bytes_per_1m_raw"]
    offset_required = args.population != "offset500m"
    if primary_rate >= args.primary_gate_bpm:
        verdict = (
            "primary_scale_opening_signal_requires_offset_transfer"
            if offset_required
            else "primary_scale_offset_signal_requires_joint_frozen_decision"
        )
    elif primary_rate > 0:
        verdict = "positive_but_complementary_scale"
    else:
        verdict = "nonpositive_holdout_retire_current_d02_realization"
    elapsed = time.process_time_ns() - started
    return {
        "schema": "wrt_twinstream_shadow_v1",
        "candidate_id": "twinstream_raw_wrt_dual_reconstruction_v1",
        "evidence_level": "fresh_causal_exact_arithmetic_shadow_zero_score_credit",
        "population": args.population,
        "inputs": {
            "store": artifact(args.store),
            "raw": artifact(args.raw),
            "dictionary": artifact(args.dictionary),
            "raw_scope_bytes": parsed.raw_length,
            "raw_scope_sha256": hashlib.sha256(raw).hexdigest(),
        },
        "scope": {
            "raw_bytes": parsed.raw_length,
            "wrt_stream_bytes": len(parsed.stream),
            "events": len(parsed.events),
            "emission_groups": len(groups),
            "pages_completed": replay["pages"],
            "raw_bytes_by_page_partition": replay["raw_bytes"],
        },
        "controls": {
            "P0_WRT": "fresh bounded WRT-history predictor",
            "P1_RAW": "P0 plus endpoint keyed by completed raw suffix",
            "P2_SHARED": "P0 plus endpoint keyed by completed raw suffix and paired raw/WRT recurrent hash",
            "P3_REVERSE": "P2 plus raw-signature reconstruction learned only after completed groups",
            "PX_MATCHED": "P0 plus matched-capacity endpoint keyed by two non-shared raw suffix hashes",
        },
        "causal_contract": {
            "wrt_trajectory_unchanged": True,
            "zero_output_controls_join_next_output_event": True,
            "raw_reveal_after_complete_emission_group": True,
            "reverse_training_after_complete_emission_group": True,
            "chronological_updates_cross_partitions": True,
            "partition_rule": "page_index mod 5: train 0/1/2, development 3, holdout 4",
        },
        "parameters": {
            "capacity_per_control": args.capacity,
            "alpha": args.alpha,
            "reverse_capacity": args.reverse_capacity,
            "candidate_blends_ppm": list(blends),
            "primary_gate_saved_bytes_per_1m_raw": args.primary_gate_bpm,
        },
        "selection": {
            "rule": "minimum development ideal qbits; ties choose weaker blend",
            "selected_blends_ppm": selected,
            "holdout_unopened_until_selection": True,
        },
        "exact_replay": {
            "controls": controls,
            "reverse_state": replay["state"]["reverse"],
            "primary_control": primary,
            "primary_holdout_saved_bytes_per_1m_raw": primary_rate,
        },
        "runtime": {
            "total_process_cpu_ns": elapsed,
            "per_control_predict_update_cpu_ns": replay["state"]["cpu_ns"],
            "p3_runtime_claim_rule": "P3 must beat P2 and PX after measured native cycle accounting.",
        },
        "economics": {
            "design_target_bytes": 108_000_000,
            "planning_baseline_bytes": 109_524_268,
            "design_debt_bytes": 1_524_268,
            "primary_gate_saved_bytes_per_1m_raw": args.primary_gate_bpm,
            "canonical_10m_screen_bytes": 20_000,
            "tool_source_bytes": Path(__file__).stat().st_size,
        },
        "identity": {
            "raw_roundtrip_ok": True,
            "fresh_replay": True,
            "deterministic_integer_model_state": True,
        },
        "verdict": verdict,
        "promotion_authorized": False,
        "score_credit_bytes": 0,
        "claim_boundary": (
            "This receipt compares fresh causal shadow coders. It is not a "
            "constructive submission archive and cannot change the Hutter frontier. "
            "Offset transfer, source accounting, native integration, exact roundtrip, "
            "determinism, RSS, runtime, canonical 10M, and full 1G proof remain."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--population", choices=("opening", "offset500m"), required=True)
    parser.add_argument("--capacity", type=int, default=131_072)
    parser.add_argument("--reverse-capacity", type=int, default=32_768)
    parser.add_argument("--alpha", type=int, default=1)
    parser.add_argument("--blends-ppm", default="125000,250000,500000,1000000")
    parser.add_argument("--primary-gate-bpm", type=float, default=2_000.0)
    args = parser.parse_args()
    for path in (args.store, args.raw, args.dictionary):
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
                "primary_control": receipt["exact_replay"]["primary_control"],
                "primary_holdout_saved_bytes_per_1m_raw": receipt["exact_replay"][
                    "primary_holdout_saved_bytes_per_1m_raw"
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
