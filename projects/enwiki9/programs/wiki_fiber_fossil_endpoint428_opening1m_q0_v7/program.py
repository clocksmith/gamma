"""Bounded causal Fiber-FOSSIL probability construction and finite coder.

This module contains no file-system policy. The adaptive tool binds immutable
inputs, materializes the sealed GSRT2 route population, and records receipts.
"""

from __future__ import annotations

from array import array
from dataclasses import dataclass
import hashlib
import struct
import sys
from typing import Any


TOTAL = 1 << 16
KEY_BYTES = 16
MAXIMUM_EXACT_RECORDS = 1 << 20
PHYSICAL_FOSSIL_FLOOR = 100_000_000
RANDOM_ROUTE_BUCKETS = 4096
ARMS = ("D", "G", "S", "R", "N", "T")
CONTROLS = ("G", "S", "R", "N", "T")
TAPE_HEADER_BYTES = 192
TAPE_RECORD_BYTES = 88
TAPE_RECORD = struct.Struct("<10QI4B")
MASK64 = (1 << 64) - 1
FNV_OFFSET = 1469598103934665603
FNV_PRIME = 1099511628211

EVENT_TEMPLATE_ENTER = 1
EVENT_EXPLICIT_FIELD_ENTRY = 2
EVENT_FIELD_VALUE_BYTE = 3
EVENT_DEFERRED_VALUE_UPDATE = 4
EVENT_FIELD_EXIT = 5
EVENT_TEMPLATE_EXIT = 7
EVENT_OVERFLOW_ENTER = 8
EVENT_OVERFLOW_EXIT = 9
FLAG_PREDICTIVE = 2

VIRTUAL_DISTANCE_BUCKETS = (
    (1, 16),
    (17, 32),
    (33, 64),
    (65, 128),
    (129, 256),
    (257, 1 << 63),
)


@dataclass(frozen=True)
class TapeRow:
    ordinal: int
    source: int
    availability: int
    first_bit: int
    raw_before: int
    raw_after: int
    route_lo: int
    route_hi: int
    witness_lo: int
    witness_hi: int
    virtual_ordinal: int
    field_ordinal: int
    event_type: int
    flags: int
    depth: int
    key_identity: int


def _u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")


def _u64(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 8], "little")


def load_tape(data: bytes, expected_store_bytes: int, expected_wrt_bytes: int,
              expected_raw_bytes: int, expected_dictionary_bytes: int
              ) -> tuple[dict[str, int], list[TapeRow]]:
    if len(data) < TAPE_HEADER_BYTES or data[:8] != b"GSRT2\0\0\0":
        raise ValueError("invalid GSRT2 tape")
    header = {
        "version": _u32(data, 8),
        "header_bytes": _u32(data, 12),
        "record_bytes": _u32(data, 16),
        "fixture": _u32(data, 20),
        "store_bytes": _u64(data, 24),
        "wrt_bytes": _u64(data, 32),
        "raw_bytes": _u64(data, 40),
        "dictionary_bytes": _u64(data, 48),
        "record_count": _u64(data, 56),
        "descriptor_count": _u64(data, 64),
        "pretruth_violations": _u64(data, 160),
        "parser_digest": _u64(data, 168),
        "raw_digest": _u64(data, 176),
        "wrt_digest": _u64(data, 184),
    }
    expected = {
        "version": 2,
        "header_bytes": TAPE_HEADER_BYTES,
        "record_bytes": TAPE_RECORD_BYTES,
        "fixture": 1,
        "store_bytes": expected_store_bytes,
        "wrt_bytes": expected_wrt_bytes,
        "raw_bytes": expected_raw_bytes,
        "dictionary_bytes": expected_dictionary_bytes,
        "pretruth_violations": 0,
    }
    for key, value in expected.items():
        if header[key] != value:
            raise ValueError(f"GSRT2 header {key} mismatch")
    if len(data) != TAPE_HEADER_BYTES + header["record_count"] * TAPE_RECORD_BYTES:
        raise ValueError("GSRT2 record geometry mismatch")
    rows: list[TapeRow] = []
    for ordinal in range(header["record_count"]):
        start = TAPE_HEADER_BYTES + ordinal * TAPE_RECORD_BYTES
        row = TapeRow(ordinal, *TAPE_RECORD.unpack_from(data, start))
        if row.first_bit != row.availability * 8:
            raise ValueError("GSRT2 first-bit coordinate mismatch")
        if row.availability < row.source or row.availability > expected_wrt_bytes:
            raise ValueError("GSRT2 availability is noncausal")
        if row.event_type < 1 or row.event_type > 9:
            raise ValueError("GSRT2 event type out of range")
        rows.append(row)
    return header, rows


def load_p1(data: bytes, expected_rows: int) -> array:
    if len(data) < 16 or data[:8] != b"CMX21P1\0":
        raise ValueError("invalid CMX21P1 trace")
    rows = _u64(data, 8)
    probabilities = array("H")
    probabilities.frombytes(data[16:])
    if sys.byteorder != "little":
        probabilities.byteswap()
    if rows != expected_rows or len(probabilities) != expected_rows:
        raise ValueError("CMX21P1 row count mismatch")
    if any(value == 0 for value in probabilities):
        raise ValueError("CMX21P1 contains zero probability")
    return probabilities


def truth_bits(stream: bytes) -> bytearray:
    result = bytearray(len(stream) * 8)
    row = 0
    for value in stream:
        for shift in range(7, -1, -1):
            result[row] = (value >> shift) & 1
            row += 1
    return result


def range_encode(probabilities: array, truth: bytearray) -> bytes:
    if len(probabilities) != len(truth):
        raise ValueError("probability/truth length mismatch")
    output = bytearray()
    low = 0
    high = 0xFFFFFFFF
    for probability, actual in zip(probabilities, truth):
        p1 = int(probability)
        delta = high - low
        midpoint = low + (delta >> 16) * p1 + ((delta & 0xFFFF) * p1 >> 16)
        if actual:
            high = midpoint
        else:
            low = midpoint + 1
        while ((low ^ high) & 0xFF000000) == 0:
            output.append((high >> 24) & 0xFF)
            low = (low << 8) & 0xFFFFFFFF
            high = ((high << 8) & 0xFFFFFFFF) + 255
    while ((low ^ high) & 0xFF000000) == 0:
        output.append((high >> 24) & 0xFF)
        low = (low << 8) & 0xFFFFFFFF
        high = ((high << 8) & 0xFFFFFFFF) + 255
    output.append((high >> 24) & 0xFF)
    return bytes(output)


def range_decode_equal(payload: bytes, probabilities: array,
                       truth: bytearray) -> bool:
    if len(payload) < 4 or len(probabilities) != len(truth):
        return False
    cursor = 4
    code = int.from_bytes(payload[:4], "big")
    low = 0
    high = 0xFFFFFFFF
    for probability, actual in zip(probabilities, truth):
        p1 = int(probability)
        delta = high - low
        midpoint = low + (delta >> 16) * p1 + ((delta & 0xFFFF) * p1 >> 16)
        if code <= midpoint:
            decoded = 1
            high = midpoint
        else:
            decoded = 0
            low = midpoint + 1
        if decoded != actual:
            return False
        while ((low ^ high) & 0xFF000000) == 0:
            low = (low << 8) & 0xFFFFFFFF
            high = ((high << 8) & 0xFFFFFFFF) + 255
            next_byte = payload[cursor] if cursor < len(payload) else 0
            cursor += 1
            code = ((code << 8) & 0xFFFFFFFF) + next_byte
    return True


def splitmix64(value: int) -> int:
    value = (value + 0x9E3779B97F4A7C15) & MASK64
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK64
    return (value ^ (value >> 31)) & MASK64


def _fnv_update(digest: int, value: int, width: int = 8) -> int:
    for offset in range(width):
        digest = ((digest ^ ((value >> (8 * offset)) & 0xFF)) * FNV_PRIME) & MASK64
    return digest


class ExactContinuation:
    """Collision-free bounded scientific state, not a native table claim."""

    def __init__(self) -> None:
        self.histories: dict[object, bytearray] = {}
        self.continuations: dict[tuple[object, bytes], tuple[int, int]] = {}
        self.digest = FNV_OFFSET

    def predict(self, route: object) -> tuple[int, int] | None:
        history = self.histories.get(route)
        if history is None or len(history) < KEY_BYTES:
            return None
        found = self.continuations.get((route, bytes(history[-KEY_BYTES:])))
        if found is None:
            return None
        ordinal, donor = found
        return donor, len(history) - ordinal

    def observe(self, route: object, truth: int) -> None:
        history = self.histories.setdefault(route, bytearray())
        if len(history) >= KEY_BYTES:
            key = (route, bytes(history[-KEY_BYTES:]))
            if key not in self.continuations and len(self.continuations) >= MAXIMUM_EXACT_RECORDS:
                raise MemoryError("bounded exact continuation record ceiling exceeded")
            self.continuations[key] = (len(history), truth)
        history.append(truth)
        self.digest = _fnv_update(self.digest, truth, 1)
        self.digest = _fnv_update(self.digest, len(history))


def global_continuations(stream: bytes) -> tuple[list[tuple[int, int] | None], dict[str, int | str]]:
    table: dict[bytes, tuple[int, int]] = {}
    donors: list[tuple[int, int] | None] = [None] * len(stream)
    digest = FNV_OFFSET
    for source, truth in enumerate(stream):
        if source >= KEY_BYTES:
            key = stream[source - KEY_BYTES : source]
            donors[source] = table.get(key)
            if key not in table and len(table) >= MAXIMUM_EXACT_RECORDS:
                raise MemoryError("bounded global continuation record ceiling exceeded")
            table[key] = (source, truth)
        digest = _fnv_update(digest, truth, 1)
    return donors, {"records": len(table), "transition_fnv1a64": f"{digest:016x}"}


def _kt_reliability(counts: list[list[int]], bit_position: int) -> int:
    correct, wrong = counts[bit_position]
    numerator = (2 * correct + 1) * TOTAL
    denominator = 2 * (correct + wrong + 1)
    return max(1, min(TOTAL - 1, numerator // denominator))


def _assign_reliability(reliability: int, donor_bit: int) -> int:
    return reliability if donor_bit else TOTAL - reliability


def _random_assignment(row: TapeRow) -> tuple[str, int]:
    seed = row.route_lo
    seed ^= ((row.route_hi << 17) | (row.route_hi >> 47)) & MASK64
    seed ^= (row.source << 1) & MASK64
    seed ^= (row.field_ordinal << 33) & MASK64
    seed ^= (row.depth << 57) & MASK64
    return ("R", splitmix64(seed) & (RANDOM_ROUTE_BUCKETS - 1))


def _active_key(row: TapeRow) -> tuple[int, int, int, int]:
    return (row.depth, row.route_lo, row.route_hi, row.field_ordinal)


def construct_probabilities(stream: bytes, base: array,
                            tape_rows: list[TapeRow]
                            ) -> tuple[dict[str, array], dict[str, Any], list[int]]:
    predictions: dict[int, TapeRow] = {}
    structural: dict[int, list[TapeRow]] = {}
    deferred: dict[int, int] = {}
    excluded_updates: set[int] = set()
    for row in tape_rows:
        if row.event_type == EVENT_FIELD_VALUE_BYTE and row.flags & FLAG_PREDICTIVE:
            if row.source in predictions:
                raise ValueError("duplicate predictive semantic record")
            predictions[row.source] = row
        elif row.event_type == EVENT_DEFERRED_VALUE_UPDATE:
            if row.source in deferred:
                raise ValueError("duplicate deferred semantic update")
            deferred[row.source] = row.availability
        else:
            structural.setdefault(row.availability, []).append(row)
        if row.event_type == EVENT_FIELD_EXIT:
            excluded_updates.add(row.source)
        if row.event_type in (EVENT_TEMPLATE_ENTER, EVENT_TEMPLATE_EXIT,
                              EVENT_OVERFLOW_ENTER, EVENT_OVERFLOW_EXIT):
            excluded_updates.add(row.source)
            if row.source:
                excluded_updates.add(row.source - 1)
    for source in deferred:
        if source not in predictions:
            raise ValueError("deferred update lacks predictive source")

    physical, physical_meta = global_continuations(stream)
    probabilities = {arm: array("H", base) for arm in ARMS}
    calibrated_arms = ("D", "G", "S", "R", "T")
    counts = {arm: [[0, 0] for _ in range(8)] for arm in calibrated_arms}
    active_bytes = {arm: 0 for arm in ARMS}
    correct_bytes = {arm: 0 for arm in ARMS}
    active_bits = {arm: 0 for arm in ARMS}
    route_states = {arm: ExactContinuation() for arm in ("D", "S", "R")}
    active_fields: dict[tuple[int, int, int, int], dict[str, object]] = {}
    pending_updates: dict[int, list[tuple[int, dict[str, object]]]] = {}
    last_completed_route: tuple[str, int, int] | None = None
    d_distances = [0] * len(stream)
    opportunity_digest = FNV_OFFSET

    for source in range(len(stream) + 1):
        for truth, assignments in pending_updates.pop(source, []):
            for arm in ("D", "S", "R"):
                route_states[arm].observe(assignments[arm], truth)
        for row in structural.get(source, []):
            key = _active_key(row)
            if row.event_type == EVENT_EXPLICIT_FIELD_ENTRY:
                if key in active_fields:
                    raise ValueError("semantic field entered twice")
                active_fields[key] = {
                    "D": ("D", row.route_lo, row.route_hi),
                    "S": last_completed_route or ("S-NONE", 0, 0),
                    "R": _random_assignment(row),
                }
            elif row.event_type == EVENT_FIELD_EXIT:
                if key not in active_fields:
                    raise ValueError("semantic field exit lacks active entry")
                active_fields.pop(key)
                last_completed_route = ("S", row.route_lo, row.route_hi)
        if source == len(stream):
            break
        row = predictions.get(source)
        if row is None:
            continue
        assignments = active_fields.get(_active_key(row))
        if assignments is None:
            raise ValueError("predictive semantic row lacks active field")
        truth = stream[source]
        d_prediction = route_states["D"].predict(assignments["D"])
        s_prediction = route_states["S"].predict(assignments["S"])
        r_prediction = route_states["R"].predict(assignments["R"])
        physical_prediction = physical[source]
        donors: dict[str, int | None] = {
            "D": None if d_prediction is None else d_prediction[0],
            "S": None if s_prediction is None else s_prediction[0],
            "R": None if r_prediction is None else r_prediction[0],
            "N": None if d_prediction is None else d_prediction[0] ^ 0xFF,
            "T": None if physical_prediction is None else physical_prediction[1],
            "G": None if physical_prediction is None
            or source - physical_prediction[0] <= PHYSICAL_FOSSIL_FLOOR
            else physical_prediction[1],
        }
        if d_prediction is not None:
            d_distances[source] = d_prediction[1]

        opportunity_digest = _fnv_update(opportunity_digest, source)
        opportunity_digest = _fnv_update(opportunity_digest, row.route_lo)
        opportunity_digest = _fnv_update(opportunity_digest, row.route_hi)
        # D and N share D's pretruth reliability. N complements only the
        # direction; it cannot relearn the sign through an independent KT.
        d_donor = donors["D"]
        if d_donor is not None:
            n_donor = d_donor ^ 0xFF
            active_bytes["D"] += 1
            active_bytes["N"] += 1
            if d_donor == truth:
                correct_bytes["D"] += 1
            if n_donor == truth:
                correct_bytes["N"] += 1
            row_offset = source * 8
            for bit_position in range(8):
                shift = 7 - bit_position
                d_bit = (d_donor >> shift) & 1
                n_bit = d_bit ^ 1
                actual = (truth >> shift) & 1
                reliability = _kt_reliability(counts["D"], bit_position)
                probabilities["D"][row_offset + bit_position] = (
                    _assign_reliability(reliability, d_bit)
                )
                probabilities["N"][row_offset + bit_position] = (
                    _assign_reliability(reliability, n_bit)
                )
                counts["D"][bit_position][0 if d_bit == actual else 1] += 1
                active_bits["D"] += 1
                active_bits["N"] += 1

        for arm in ("G", "S", "R", "T"):
            donor = donors[arm]
            if donor is None:
                continue
            active_bytes[arm] += 1
            if donor == truth:
                correct_bytes[arm] += 1
            row_offset = source * 8
            for bit_position in range(8):
                shift = 7 - bit_position
                donor_bit = (donor >> shift) & 1
                actual = (truth >> shift) & 1
                probabilities[arm][row_offset + bit_position] = _assign_reliability(
                    _kt_reliability(counts[arm], bit_position), donor_bit
                )
                counts[arm][bit_position][0 if donor_bit == actual else 1] += 1
                active_bits[arm] += 1

        if source in deferred:
            availability = deferred[source]
        elif source in excluded_updates:
            availability = None
        else:
            availability = source + 1
        if availability is not None:
            if availability <= source or availability > len(stream):
                raise ValueError("semantic update availability is noncausal")
            pending_updates.setdefault(availability, []).append((truth, assignments.copy()))

    if pending_updates:
        raise ValueError("semantic updates remain beyond population")
    metadata: dict[str, Any] = {
        "semantic_opportunity_bytes": len(predictions),
        "active_bytes": active_bytes,
        "correct_bytes": correct_bytes,
        "active_bits": active_bits,
        "kt_counts": counts,
        "n_calibration": "shared_D_pretruth_reliability_complemented_direction",
        "physical_global_state": physical_meta,
        "route_state": {
            arm: {
                "histories": len(state.histories),
                "records": len(state.continuations),
                "transition_fnv1a64": f"{state.digest:016x}",
            }
            for arm, state in route_states.items()
        },
        "opportunity_fnv1a64": f"{opportunity_digest:016x}",
        "physical_fossil_floor_bytes": PHYSICAL_FOSSIL_FLOOR,
        "bounded_exact_record_ceiling": MAXIMUM_EXACT_RECORDS,
        "random_route_buckets": RANDOM_ROUTE_BUCKETS,
    }
    return probabilities, metadata, d_distances


def probability_digests(probabilities: dict[str, array]) -> dict[str, str]:
    return {arm: hashlib.sha256(values.tobytes()).hexdigest()
            for arm, values in probabilities.items()}


def compress(data: bytes) -> bytes:
    raise NotImplementedError("causal-shadow candidate; use the bound adaptive tool")


def decompress(archive: bytes) -> bytes:
    raise NotImplementedError("causal-shadow candidate; use the bound adaptive tool")
