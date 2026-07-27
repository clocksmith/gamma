#!/usr/bin/env python3
"""Measure REVLOG relational headroom on exact outer-XML WRT slots."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from radix_island_oracle import (
    artifact,
    emission_groups,
    load_p1,
    load_truth,
    qbit_tables,
)
from wrt_exact import parse_store


QBITS = 256
FDAC_PRECISION = 32
FDAC_TOTAL = 1 << 16
SIDE_FINALIZATION_BITS = 128
FIELD_COUNT_BITS = 32
TIMESTAMP_RE = re.compile(
    rb"([0-9]{4})-([0-9]{2})-([0-9]{2})"
    rb"T([0-9]{2}):([0-9]{2}):([0-9]{2})Z"
)
TAG_RE = re.compile(
    rb"<\s*(/?)\s*([A-Za-z_][A-Za-z0-9_.:-]*)"
    rb"(?:\s[^<>]*?)?\s*(/?)>"
)
REGISTER_START = "<!-- REVLOG_SLOT_BYPASS_RESULT_START -->"
REGISTER_END = "<!-- REVLOG_SLOT_BYPASS_RESULT_END -->"


@dataclass(frozen=True)
class RawSlot:
    kind: str
    page_ordinal: int
    raw_start: int
    raw_end: int
    value: bytes
    username: bytes | None = None


@dataclass(frozen=True)
class WrtSlot:
    raw: RawSlot
    stream_start: int
    stream_end: int
    event_count: int


@dataclass
class PageRecord:
    ordinal: int
    page_id: RawSlot | None = None
    revision_id: RawSlot | None = None
    timestamp: RawSlot | None = None
    username: bytes | None = None
    contributor_id: RawSlot | None = None


class FdacEncoder:
    """Deterministic 32-bit binary arithmetic shadow coder."""

    def __init__(self) -> None:
        self.low = 0
        self.high = (1 << FDAC_PRECISION) - 1
        self.pending = 0
        self.bits = 0

    def _emit(self) -> None:
        self.bits += 1 + self.pending
        self.pending = 0

    def encode(self, bit: int, p1: int) -> None:
        p1 = min(FDAC_TOTAL - 1, max(1, int(p1)))
        p0 = FDAC_TOTAL - p1
        width = self.high - self.low + 1
        split = self.low + (width * p0 // FDAC_TOTAL)
        split = min(self.high, max(self.low + 1, split))
        if bit:
            self.low = split
        else:
            self.high = split - 1
        quarter = 1 << (FDAC_PRECISION - 2)
        half = 2 * quarter
        three_quarters = 3 * quarter
        mask = (1 << FDAC_PRECISION) - 1
        while True:
            if self.high < half:
                self._emit()
            elif self.low >= half:
                self._emit()
                self.low -= half
                self.high -= half
            elif self.low >= quarter and self.high < three_quarters:
                self.pending += 1
                self.low -= quarter
                self.high -= quarter
            else:
                break
            self.low = (self.low << 1) & mask
            self.high = ((self.high << 1) | 1) & mask

    def finish(self) -> int:
        self.pending += 1
        self._emit()
        return self.bits


def gamma_bits(value: int) -> int:
    if value <= 0:
        raise ValueError("Elias gamma values must be positive")
    return 2 * value.bit_length() - 1


def zigzag(value: int) -> int:
    return 2 * value if value >= 0 else -2 * value - 1


def rice_parameter(mean_q8: int) -> int:
    base = (mean_q8 >> 8) + 1
    return max(0, min(31, base.bit_length() - 2))


def rice_bits(value: int, mean_q8: int) -> int:
    encoded = zigzag(value)
    k = rice_parameter(mean_q8)
    return (encoded >> k) + 1 + k


def update_mean(mean_q8: int, value: int) -> int:
    return mean_q8 + (((abs(value) << 8) - mean_q8) >> 5)


def enumerative_bits(n: int, k: int) -> int:
    if not 0 <= k <= n:
        raise ValueError("invalid subset size")
    count = math.comb(n, k)
    return 0 if count <= 1 else (count - 1).bit_length()


def elias_fano_payload_bits(values: list[int]) -> int:
    if not values:
        return 0
    if any(value < 0 for value in values):
        raise ValueError("Elias-Fano values must be nonnegative")
    if any(right <= left for left, right in zip(values, values[1:])):
        raise ValueError("Elias-Fano values must be strictly increasing")
    universe = values[-1] + 1
    count = len(values)
    ratio = max(1, universe // count)
    lower = max(0, ratio.bit_length() - 1)
    return count * lower + (universe >> lower) + count


def signed_delta_bits(values: list[int]) -> int:
    if not values:
        return 0
    bits = gamma_bits(values[0] + 1)
    mean_q8 = 1 << 16
    for value, prior in zip(values[1:], values):
        delta = value - prior
        direct = gamma_bits(value + 1)
        delta_code = rice_bits(delta, mean_q8)
        bits += 1 + min(direct, delta_code)
        mean_q8 = update_mean(mean_q8, delta)
    return bits


def monotone_exception_bits(values: list[int]) -> tuple[int, dict[str, Any]]:
    if not values:
        return 0, {"mode": "empty", "exceptions": 0}
    kept: list[int] = []
    exceptions: list[tuple[int, int]] = []
    last = -1
    for index, value in enumerate(values):
        if value > last:
            kept.append(value)
            last = value
        else:
            exceptions.append((index, value))
    exception_bits = enumerative_bits(len(values), len(exceptions))
    exception_bits += sum(gamma_bits(value + 1) for _, value in exceptions)
    ef_bits = elias_fano_payload_bits(kept)
    ef_total = (
        2
        + gamma_bits(len(values) + 1)
        + gamma_bits(len(exceptions) + 1)
        + gamma_bits(max(values) + 2)
        + ef_bits
        + exception_bits
    )
    delta_total = 2 + gamma_bits(len(values) + 1) + signed_delta_bits(values)
    if ef_total <= delta_total:
        return ef_total, {
            "mode": "elias_fano_with_exceptions",
            "exceptions": len(exceptions),
            "kept": len(kept),
            "payload_bits": ef_bits,
            "exception_bits": exception_bits,
            "alternative_delta_bits": delta_total,
        }
    return delta_total, {
        "mode": "signed_delta_rice",
        "exceptions": len(exceptions),
        "alternative_elias_fano_bits": ef_total,
    }


def timestamp_scalar(value: bytes) -> int:
    match = TIMESTAMP_RE.fullmatch(value)
    if match is None:
        raise ValueError(f"noncanonical timestamp: {value!r}")
    year, month, day, hour, minute, second = (
        int(part) for part in match.groups()
    )
    if not (
        0 <= year <= 9999
        and 1 <= month <= 12
        and 1 <= day <= 31
        and 0 <= hour < 24
        and 0 <= minute < 60
        and 0 <= second < 60
    ):
        raise ValueError(f"timestamp component outside fixed radix: {value!r}")
    return (((((year * 12 + month - 1) * 31 + day - 1) * 24 + hour)
             * 60 + minute) * 60 + second)


def timestamp_bits(values: list[int]) -> tuple[int, dict[str, Any]]:
    if not values:
        return 0, {"records": 0, "delta_records": 0, "direct_records": 0}
    bits = 40
    previous_delta = 0
    mean_q8 = 1 << 24
    direct = 1
    delta = 0
    for index, (value, prior) in enumerate(zip(values[1:], values), start=1):
        current_delta = value - prior
        residual = current_delta if index == 1 else current_delta - previous_delta
        residual_bits = rice_bits(residual, mean_q8)
        if residual_bits < 40:
            bits += 1 + residual_bits
            delta += 1
        else:
            bits += 1 + 40
            direct += 1
        mean_q8 = update_mean(mean_q8, residual)
        previous_delta = current_delta
    return bits, {
        "records": len(values),
        "delta_records": delta,
        "direct_records": direct,
        "fixed_direct_bits": 40,
    }


def contributor_bits(
    pairs: list[tuple[bytes, int]],
) -> tuple[int, dict[str, Any]]:
    table: dict[bytes, int] = {}
    new_values: list[int] = []
    repeated: list[tuple[int, int]] = []
    contradictions: list[tuple[int, int]] = []
    for username, value in pairs:
        if username not in table:
            table[username] = value
            new_values.append(value)
            continue
        repeated.append((len(repeated), value))
        if table[username] != value:
            contradictions.append((len(repeated) - 1, value))
            table[username] = value
    bits = gamma_bits(len(pairs) + 1)
    bits += gamma_bits(len(new_values) + 1)
    bits += sum(gamma_bits(value + 1) for value in new_values)
    bits += gamma_bits(len(contradictions) + 1)
    bits += enumerative_bits(len(repeated), len(contradictions))
    bits += sum(gamma_bits(value + 1) for _, value in contradictions)
    return bits, {
        "records": len(pairs),
        "unique_usernames": len(new_values),
        "repeated_usernames": len(repeated),
        "unchanged_repeats": len(repeated) - len(contradictions),
        "contradictions": len(contradictions),
        "table_bytes_upper_bound": sum(len(key) + 8 for key in table),
    }


def scan_records(raw: bytes) -> tuple[list[PageRecord], dict[str, int]]:
    stack: list[tuple[bytes, int]] = []
    records: list[PageRecord] = []
    active: PageRecord | None = None
    page_ordinal = 0
    malformed = 0
    for match in TAG_RE.finditer(raw):
        closing, name, self_closing = match.groups()
        name = name.lower()
        if closing:
            if not stack or stack[-1][0] != name:
                malformed += 1
                continue
            path = tuple(item[0] for item in stack)
            _, content_start = stack.pop()
            value = raw[content_start : match.start()]
            if active is not None:
                slot = RawSlot(
                    kind="",
                    page_ordinal=active.ordinal,
                    raw_start=content_start,
                    raw_end=match.start(),
                    value=value,
                )
                if path[-2:] == (b"page", b"id") and value.isdigit():
                    active.page_id = RawSlot(**{**slot.__dict__, "kind": "page_id"})
                elif path[-3:] == (b"page", b"revision", b"id") and value.isdigit():
                    active.revision_id = RawSlot(
                        **{**slot.__dict__, "kind": "revision_id"}
                    )
                elif (
                    path[-3:] == (b"page", b"revision", b"timestamp")
                    and TIMESTAMP_RE.fullmatch(value)
                ):
                    active.timestamp = RawSlot(
                        **{**slot.__dict__, "kind": "timestamp"}
                    )
                elif path[-4:] == (
                    b"page",
                    b"revision",
                    b"contributor",
                    b"username",
                ):
                    active.username = value
                elif (
                    path[-4:]
                    == (b"page", b"revision", b"contributor", b"id")
                    and value.isdigit()
                ):
                    active.contributor_id = RawSlot(
                        **{
                            **slot.__dict__,
                            "kind": "contributor_id",
                            "username": active.username,
                        }
                    )
                if name == b"page":
                    records.append(active)
                    active = None
            continue
        if name == b"page":
            active = PageRecord(ordinal=page_ordinal)
            page_ordinal += 1
        if not self_closing:
            stack.append((name, match.end()))
    return records, {
        "complete_pages": len(records),
        "opened_pages": page_ordinal,
        "unclosed_tags": len(stack),
        "mismatched_closing_tags": malformed,
    }


def map_wrt_slots(
    raw_slots: Iterable[RawSlot], groups: tuple[Any, ...]
) -> list[WrtSlot]:
    starts = {group.raw_start: index for index, group in enumerate(groups)}
    ends = {group.raw_end: index + 1 for index, group in enumerate(groups)}
    result: list[WrtSlot] = []
    for slot in raw_slots:
        if slot.raw_start not in starts or slot.raw_end not in ends:
            raise ValueError(
                f"{slot.kind} raw span does not align to WRT groups: "
                f"{slot.raw_start}:{slot.raw_end}"
            )
        begin = starts[slot.raw_start]
        finish = ends[slot.raw_end]
        selected = groups[begin:finish]
        decoded = b"".join(group.decoded for group in selected)
        if decoded != slot.value:
            raise ValueError(f"{slot.kind} WRT reconstruction mismatch")
        result.append(
            WrtSlot(
                raw=slot,
                stream_start=selected[0].stream_start,
                stream_end=selected[-1].stream_end,
                event_count=len(selected),
            )
        )
    return result


def parent_cost(
    slots: list[WrtSlot],
    p1: np.ndarray,
    truth: np.ndarray,
    zero_cost: np.ndarray,
    one_cost: np.ndarray,
) -> dict[str, Any]:
    qbits = 0
    rows = 0
    coder = FdacEncoder()
    for slot in sorted(slots, key=lambda item: item.stream_start):
        start = slot.stream_start * 8
        end = slot.stream_end * 8
        probabilities = p1[start:end]
        bits = truth[start:end]
        qbits += int(
            np.where(bits != 0, one_cost[probabilities], zero_cost[probabilities])
            .sum()
        )
        rows += end - start
        for bit, probability in zip(bits, probabilities, strict=True):
            coder.encode(int(bit), int(probability))
    fdac_bits = coder.finish()
    return {
        "qbits": qbits,
        "qbit_bytes": qbits / (8 * QBITS),
        "wrt_rows": rows,
        "wrt_events": sum(slot.event_count for slot in slots),
        "shadow_fdac_bits": fdac_bits,
        "shadow_fdac_bytes": (fdac_bits + 7) // 8,
    }


def fixed_shuffle(values: list[Any], seed: int) -> list[Any]:
    output = list(values)
    random.Random(seed).shuffle(output)
    return output


def candidate(
    name: str,
    parent: dict[str, Any],
    payload_bits: int,
    raw_bytes: int,
) -> dict[str, Any]:
    framing = SIDE_FINALIZATION_BITS + FIELD_COUNT_BITS
    total_bits = payload_bits + framing
    saved_qbits = parent["qbits"] - total_bits * QBITS
    saved_bytes = saved_qbits / (8 * QBITS)
    return {
        "name": name,
        "parent": parent,
        "payload_bits": payload_bits,
        "field_count_bits": FIELD_COUNT_BITS,
        "finalization_bits": SIDE_FINALIZATION_BITS,
        "total_side_bits": total_bits,
        "saved_qbits": saved_qbits,
        "saved_bytes": saved_bytes,
        "saved_bytes_per_1m_raw": saved_bytes * 1_000_000 / raw_bytes,
    }


def artifact_optional(path: Path | None) -> dict[str, Any] | None:
    return artifact(path) if path is not None else None


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def render_register(receipt: dict[str, Any]) -> str:
    gate = receipt["gate"]
    candidates = receipt["candidates"]
    scope = receipt["scope"]
    relation = receipt["relations"]
    return f"""<!-- REVLOG_SLOT_BYPASS_RESULT_START -->
Status: **{gate["verdict"]}**, zero score credit.

The opening-1M exact WRT/P1 oracle found {scope["selected_fields"]} selected
outer-XML fields across {scope["complete_pages"]} complete pages. Their combined
parent ceiling is {gate["combined_parent_ceiling_bytes_per_1m"]:.3f} B/M
against the predeclared 4,000 B/M Gate 0. The fully charged C5 oracle is
{candidates["C5_combined"]["saved_bytes_per_1m_raw"]:.3f} B/M against the
3,000 B/M Gate 1.

Class results:

- C1 page ID: {candidates["C1_page_id"]["saved_bytes_per_1m_raw"]:.3f} B/M.
- C2 timestamp: {candidates["C2_timestamp"]["saved_bytes_per_1m_raw"]:.3f} B/M.
- C3 revision ID: {candidates["C3_revision_id"]["saved_bytes_per_1m_raw"]:.3f} B/M.
- C4 contributor ID: {candidates["C4_contributor_id"]["saved_bytes_per_1m_raw"]:.3f} B/M.
- CS shuffled timestamp control: {candidates["CS_shuffled_timestamp"]["total_side_bits"]} side bits versus C3's {candidates["C3_revision_id"]["total_side_bits"]}.
- CU shuffled username control: {candidates["CU_shuffled_username"]["total_side_bits"]} side bits versus C4's {candidates["C4_contributor_id"]["total_side_bits"]}.

Timestamp ordering leaves {relation["timestamp_order_revision_inversions"]}
revision-ID inversions. The contributor table observes
{relation["contributor"]["unchanged_repeats"]} unchanged repeated usernames and
{relation["contributor"]["contradictions"]} contradictions.

Decision: {gate["next_action"]}. Receipt:
`results/revlog_slot_bypass_opening_1m_v1/decision.json`.
<!-- REVLOG_SLOT_BYPASS_RESULT_END -->"""


def update_register(path: Path, receipt: dict[str, Any]) -> None:
    text = path.read_text()
    start = text.find(REGISTER_START)
    end = text.find(REGISTER_END)
    replacement = render_register(receipt)
    if start < 0 or end < 0 or end < start:
        raise ValueError("REVLOG register markers are missing or malformed")
    end += len(REGISTER_END)
    path.write_text(text[:start] + replacement + text[end:])


def run(args: argparse.Namespace) -> dict[str, Any]:
    p1 = load_p1(args.p1_trace)
    truth = load_truth(args.wrt_store, len(p1))
    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("WRT reconstruction differs from raw input")
    groups = emission_groups(parsed)
    records, parser_stats = scan_records(raw)

    raw_by_kind: dict[str, list[RawSlot]] = {
        "page_id": [],
        "timestamp": [],
        "revision_id": [],
        "contributor_id": [],
    }
    complete_records: list[PageRecord] = []
    for record in records:
        if record.page_id is not None:
            raw_by_kind["page_id"].append(record.page_id)
        if record.timestamp is not None:
            raw_by_kind["timestamp"].append(record.timestamp)
        if record.revision_id is not None:
            raw_by_kind["revision_id"].append(record.revision_id)
        if record.contributor_id is not None and record.username is not None:
            raw_by_kind["contributor_id"].append(record.contributor_id)
        if (
            record.page_id is not None
            and record.timestamp is not None
            and record.revision_id is not None
        ):
            complete_records.append(record)

    wrt_by_kind = {
        kind: map_wrt_slots(slots, groups)
        for kind, slots in raw_by_kind.items()
    }
    zero_cost, one_cost = qbit_tables()
    parent = {
        kind: parent_cost(slots, p1, truth, zero_cost, one_cost)
        for kind, slots in wrt_by_kind.items()
    }

    page_values = [int(slot.value) for slot in raw_by_kind["page_id"]]
    page_payload, page_model = monotone_exception_bits(page_values)

    timestamp_values = [
        timestamp_scalar(slot.value) for slot in raw_by_kind["timestamp"]
    ]
    timestamp_payload, timestamp_model = timestamp_bits(timestamp_values)

    revision_records = sorted(
        complete_records,
        key=lambda record: (
            timestamp_scalar(record.timestamp.value),
            record.ordinal,
        ),
    )
    revision_values = [
        int(record.revision_id.value) for record in revision_records
    ]
    revision_payload, revision_model = monotone_exception_bits(revision_values)

    shuffled_times = fixed_shuffle(
        [timestamp_scalar(record.timestamp.value) for record in complete_records],
        0x5245564C4F47,
    )
    shuffled_revision_records = sorted(
        zip(shuffled_times, complete_records, strict=True),
        key=lambda item: (item[0], item[1].ordinal),
    )
    shuffled_revision_values = [
        int(record.revision_id.value)
        for _, record in shuffled_revision_records
    ]
    shuffled_revision_payload, shuffled_revision_model = (
        monotone_exception_bits(shuffled_revision_values)
    )

    contributor_pairs = [
        (slot.username, int(slot.value))
        for slot in raw_by_kind["contributor_id"]
        if slot.username is not None
    ]
    contributor_payload, contributor_model = contributor_bits(contributor_pairs)
    shuffled_usernames = fixed_shuffle(
        [username for username, _ in contributor_pairs],
        0x555345524944,
    )
    shuffled_pairs = [
        (username, value)
        for username, (_, value) in zip(
            shuffled_usernames, contributor_pairs, strict=True
        )
    ]
    shuffled_contributor_payload, shuffled_contributor_model = (
        contributor_bits(shuffled_pairs)
    )

    candidates = {
        "C1_page_id": candidate(
            "C1_page_id", parent["page_id"], page_payload, len(raw)
        ),
        "C2_timestamp": candidate(
            "C2_timestamp", parent["timestamp"], timestamp_payload, len(raw)
        ),
        "C3_revision_id": candidate(
            "C3_revision_id",
            parent["revision_id"],
            revision_payload,
            len(raw),
        ),
        "C4_contributor_id": candidate(
            "C4_contributor_id",
            parent["contributor_id"],
            contributor_payload,
            len(raw),
        ),
        "CS_shuffled_timestamp": candidate(
            "CS_shuffled_timestamp",
            parent["revision_id"],
            shuffled_revision_payload,
            len(raw),
        ),
        "CU_shuffled_username": candidate(
            "CU_shuffled_username",
            parent["contributor_id"],
            shuffled_contributor_payload,
            len(raw),
        ),
    }
    combined_parent = {
        key: sum(parent[kind][key] for kind in parent)
        for key in ("qbits", "wrt_rows", "wrt_events", "shadow_fdac_bits")
    }
    combined_parent["qbit_bytes"] = combined_parent["qbits"] / (8 * QBITS)
    combined_parent["shadow_fdac_bytes"] = sum(
        parent[kind]["shadow_fdac_bytes"] for kind in parent
    )
    combined_payload = (
        page_payload
        + timestamp_payload
        + revision_payload
        + contributor_payload
    )
    combined_total = (
        combined_payload
        + SIDE_FINALIZATION_BITS
        + FIELD_COUNT_BITS * len(parent)
    )
    combined_saved_qbits = combined_parent["qbits"] - combined_total * QBITS
    combined_saved_bytes = combined_saved_qbits / (8 * QBITS)
    candidates["C5_combined"] = {
        "name": "C5_combined",
        "parent": combined_parent,
        "payload_bits": combined_payload,
        "field_count_bits": FIELD_COUNT_BITS * len(parent),
        "finalization_bits": SIDE_FINALIZATION_BITS,
        "total_side_bits": combined_total,
        "saved_qbits": combined_saved_qbits,
        "saved_bytes": combined_saved_bytes,
        "saved_bytes_per_1m_raw": (
            combined_saved_bytes * 1_000_000 / len(raw)
        ),
    }

    parent_ceiling_rate = (
        combined_parent["qbit_bytes"] * 1_000_000 / len(raw)
    )
    each_positive = all(
        candidates[name]["saved_bytes_per_1m_raw"] > 0
        for name in (
            "C1_page_id",
            "C2_timestamp",
            "C3_revision_id",
            "C4_contributor_id",
        )
    )
    c3_beats_cs = revision_payload < shuffled_revision_payload
    c4_beats_cu = contributor_payload < shuffled_contributor_payload
    gate0 = parent_ceiling_rate >= args.minimum_ceiling_rate
    gate1 = (
        candidates["C5_combined"]["saved_bytes_per_1m_raw"]
        >= args.required_rate
        and each_positive
        and c3_beats_cs
        and c4_beats_cu
    )
    passed = gate0 and gate1
    if passed:
        verdict = "oracle_pass_freeze_rules_and_run_distant_windows"
        next_action = (
            "freeze all modes and execute identical oracles near 250M, 500M, "
            "and 750M; native integration remains unauthorized"
        )
    else:
        verdict = "retire_revlog_and_close_numeric_research"
        next_action = (
            "reject native REVLOG integration, close numeric research, and "
            "move the primary lane to aligned teacher-quotient compilation"
        )

    revision_inversions = sum(
        right <= left
        for left, right in zip(revision_values, revision_values[1:])
    )
    receipt = {
        "schema": "revlog_slot_bypass_oracle_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "proposal_id": "revlog_slot_bypass_v1",
        "evidence_level": "truth_aware_integer_qbit_headroom_zero_credit",
        "artifacts": {
            "raw_input": artifact(args.raw_input),
            "wrt_store": artifact(args.wrt_store),
            "dictionary": artifact(args.dictionary),
            "p1_trace": artifact(args.p1_trace),
            "parent_archive": artifact_optional(args.parent_archive),
        },
        "scope": {
            "raw_bytes": len(raw),
            "raw_sha256": sha256_bytes(raw),
            "trace_rows": len(p1),
            "complete_pages": parser_stats["complete_pages"],
            "opened_pages": parser_stats["opened_pages"],
            "selected_fields": sum(len(value) for value in raw_by_kind.values()),
            "field_occurrences": {
                kind: len(slots) for kind, slots in raw_by_kind.items()
            },
            "field_raw_bytes": {
                kind: sum(len(slot.value) for slot in slots)
                for kind, slots in raw_by_kind.items()
            },
            "parser": parser_stats,
            "wrt_reconstruction_equal_raw": parsed.decoded == raw,
            "every_slot_wrt_aligned": True,
        },
        "parent_costs": parent,
        "side_models": {
            "page_id": page_model,
            "timestamp": timestamp_model,
            "revision_id": revision_model,
            "contributor_id": contributor_model,
            "CS_shuffled_timestamp": shuffled_revision_model,
            "CU_shuffled_username": shuffled_contributor_model,
        },
        "relations": {
            "page_id_monotonicity_violations": sum(
                right <= left for left, right in zip(page_values, page_values[1:])
            ),
            "timestamp_order_revision_inversions": revision_inversions,
            "contributor": contributor_model,
            "shuffled_contributor": shuffled_contributor_model,
            "C3_relationship_value_bits": (
                shuffled_revision_payload - revision_payload
            ),
            "C4_relationship_value_bits": (
                shuffled_contributor_payload - contributor_payload
            ),
        },
        "candidates": candidates,
        "gate": {
            "minimum_parent_ceiling_bytes_per_1m": args.minimum_ceiling_rate,
            "required_combined_gain_bytes_per_1m": args.required_rate,
            "combined_parent_ceiling_bytes_per_1m": parent_ceiling_rate,
            "gate0_information_ceiling_passed": gate0,
            "each_selected_class_positive": each_positive,
            "C3_beats_CS": c3_beats_cs,
            "C4_beats_CU": c4_beats_cu,
            "gate1_opening_oracle_passed": gate1,
            "passed": passed,
            "verdict": verdict,
            "next_action": next_action,
        },
        "accounting": {
            "qbit_denominator": QBITS,
            "fdac_precision_bits": FDAC_PRECISION,
            "side_finalization_bits": SIDE_FINALIZATION_BITS,
            "field_count_bits_per_class": FIELD_COUNT_BITS,
            "source_package_bytes_counted": 0,
            "official_score_credit_bytes": 0,
        },
        "claim_boundary": (
            "Truth-aware opening-prefix oracle only. Parent costs are exact "
            "integer qbits from the certified pre-truth trace. Shadow FDAC "
            "lengths use the declared standalone 32-bit coder and are not "
            "additive contributions to the native archive. Side lengths are "
            "constructive integer code lengths, while CS and CU are "
            "future-informed adversarial controls. No native dual stream, "
            "source package, runtime, transfer, roundtrip, or score gain is "
            "proved."
        ),
    }
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--p1-trace", type=Path, required=True)
    parser.add_argument("--parent-archive", type=Path)
    parser.add_argument("--minimum-ceiling-rate", type=float, default=4000.0)
    parser.add_argument("--required-rate", type=float, default=3000.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--register", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    if args.register is not None:
        update_register(args.register, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
