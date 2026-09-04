#!/usr/bin/env python3
"""Exact CMX21P1 plus GSRT2 to HSP1 sparse-parent materialization.

The module owns no probability model.  It copies already emitted Endpoint428
counts at the causal byte coordinates selected by the semantic route tape.  A
production caller must first satisfy the separately frozen HORIZON terminal
barrier; this candidate itself is authorized only for generated fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat
import struct
import tempfile
from typing import Iterator


CMX21P1_MAGIC = b"CMX21P1\0"
CMX21P1_HEADER_BYTES = 16
CMX21P1_COUNT_BYTES = 2

GSRT2_MAGIC = b"GSRT2\0\0\0"
GSRT2_VERSION = 2
GSRT2_HEADER_BYTES = 192
GSRT2_RECORD = struct.Struct("<10QI4B")
GSRT2_RECORD_BYTES = GSRT2_RECORD.size

HSP1_MAGIC = b"HSP1\0\0\0\0"
HSP1_VERSION = 1
HSP1_HEADER_BYTES = 256
HSP1_RECORD = struct.Struct("<Q8H")
HSP1_HEADER = struct.Struct("<8sIIII6Q32s32s32s32s32s")

EVENT_FIELD_VALUE_BYTE = 3
EVENT_DEFERRED_VALUE_UPDATE = 4
EXPECTED_FLAGS = {
    1: 128,
    2: 137,
    3: 11,
    4: 77,
    5: 137,
    6: 144,
    7: 128,
    8: 160,
    9: 160,
}
EXPECTED_KEY_IDENTITY = {1: 0, 2: 1, 3: 1, 4: 1, 5: 1, 6: 2, 7: 0, 8: 0, 9: 0}
FNV_OFFSET = 1469598103934665603
FNV_PRIME = 1099511628211
MASK64 = (1 << 64) - 1
UINT64_MAX = MASK64
TRANSCRIPT_DOMAIN = b"GAMMA-HSP1-PARENT-TRANSCRIPT-WITNESS-V1\0"


class MaterializationError(RuntimeError):
    """An input, binding, extraction, or atomic-output invariant failed."""


@dataclass(frozen=True)
class TapeHeader:
    fixture_flags: int
    store_bytes: int
    wrt_bytes: int
    raw_bytes: int
    dictionary_bytes: int
    record_count: int
    descriptor_count: int
    event_counts: tuple[int, ...]
    deferred_updates: int
    positional_predictive_events: int
    pretruth_violations: int
    parser_digest: int
    raw_digest: int
    wrt_digest: int


@dataclass(frozen=True)
class Materialization:
    trace_sha256: str
    wrt_sha256: str
    route_sha256: str
    output_sha256: str
    output_bytes: int
    record_count: int
    first_coordinate: int
    last_coordinate: int
    payload_sha256: str
    coordinate_union_sha256: str
    parent_observer_sha256: str
    parent_state_begin_sha256: str
    parent_state_end_sha256: str

    def semantic_identity(self) -> dict[str, object]:
        return {
            "traceSha256": self.trace_sha256,
            "wrtSha256": self.wrt_sha256,
            "routeSha256": self.route_sha256,
            "outputSha256": self.output_sha256,
            "outputBytes": self.output_bytes,
            "recordCount": self.record_count,
            "firstCoordinate": self.first_coordinate,
            "lastCoordinate": self.last_coordinate,
            "payloadSha256": self.payload_sha256,
            "coordinateUnionSha256": self.coordinate_union_sha256,
            "parentObserverSha256": self.parent_observer_sha256,
            "parentStateBeginSha256": self.parent_state_begin_sha256,
            "parentStateEndSha256": self.parent_state_end_sha256,
        }


def _require_hex_digest(value: str, label: str) -> str:
    if (
        len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise MaterializationError(f"{label} is not a lowercase SHA-256")
    return value


def _regular(path: Path, label: str) -> Path:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise MaterializationError(f"{label} is unavailable") from error
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise MaterializationError(f"{label} must be a regular non-symlink file")
    return path


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256_path(path),
    }


def _require_identity(path: Path, expected_sha256: str, label: str) -> str:
    _regular(path, label)
    expected = _require_hex_digest(expected_sha256, f"{label} expected digest")
    observed = sha256_path(path)
    if observed != expected:
        raise MaterializationError(f"{label} SHA-256 differs")
    return observed


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def _u64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def _fnv_byte(value: int, byte: int) -> int:
    return ((value ^ byte) * FNV_PRIME) & MASK64


def _fnv_u64(value: int, word: int) -> int:
    for index in range(8):
        value = _fnv_byte(value, (word >> (8 * index)) & 0xFF)
    return value


def _priority(event: int) -> int:
    if event == EVENT_DEFERRED_VALUE_UPDATE:
        return 0
    if event == EVENT_FIELD_VALUE_BYTE:
        return 2
    return 1


def _trace_header(path: Path, wrt_bytes: int) -> bytes:
    expected_rows = wrt_bytes * 8
    expected_bytes = CMX21P1_HEADER_BYTES + expected_rows * CMX21P1_COUNT_BYTES
    if path.stat().st_size != expected_bytes:
        raise MaterializationError("CMX21P1 file length differs from WRT geometry")
    with path.open("rb") as stream:
        header = stream.read(CMX21P1_HEADER_BYTES)
    if (
        len(header) != CMX21P1_HEADER_BYTES
        or header[:8] != CMX21P1_MAGIC
        or _u64(header, 8) != expected_rows
    ):
        raise MaterializationError("CMX21P1 header or row count differs")
    return header


def _tape_header(path: Path, wrt_bytes: int) -> TapeHeader:
    with path.open("rb") as stream:
        header = stream.read(GSRT2_HEADER_BYTES)
    if len(header) != GSRT2_HEADER_BYTES or header[:8] != GSRT2_MAGIC:
        raise MaterializationError("GSRT2 magic or header length differs")
    version, header_bytes, record_bytes, flags = struct.unpack_from("<IIII", header, 8)
    if (version, header_bytes, record_bytes) != (
        GSRT2_VERSION,
        GSRT2_HEADER_BYTES,
        GSRT2_RECORD_BYTES,
    ):
        raise MaterializationError("GSRT2 ABI geometry differs")
    if flags not in (0, 1):
        raise MaterializationError("GSRT2 fixture flags differ")
    geometry = struct.unpack_from("<6Q", header, 24)
    event_counts = struct.unpack_from("<9Q", header, 72)
    result = TapeHeader(
        fixture_flags=flags,
        store_bytes=geometry[0],
        wrt_bytes=geometry[1],
        raw_bytes=geometry[2],
        dictionary_bytes=geometry[3],
        record_count=geometry[4],
        descriptor_count=geometry[5],
        event_counts=tuple(event_counts),
        deferred_updates=_u64(header, 144),
        positional_predictive_events=_u64(header, 152),
        pretruth_violations=_u64(header, 160),
        parser_digest=_u64(header, 168),
        raw_digest=_u64(header, 176),
        wrt_digest=_u64(header, 184),
    )
    if result.wrt_bytes != wrt_bytes:
        raise MaterializationError("GSRT2 and WRT populations differ")
    if path.stat().st_size != GSRT2_HEADER_BYTES + result.record_count * GSRT2_RECORD_BYTES:
        raise MaterializationError("GSRT2 file length differs from record count")
    if (
        sum(result.event_counts) != result.record_count
        or result.event_counts[EVENT_DEFERRED_VALUE_UPDATE - 1] != result.deferred_updates
        or result.positional_predictive_events != 0
        or result.pretruth_violations != 0
    ):
        raise MaterializationError("GSRT2 header event accounting differs")
    return result


def _iter_predictive_coordinates(
    path: Path, header: TapeHeader, replay_begin: int, replay_end: int
) -> Iterator[int]:
    counts = [0] * 9
    digest = FNV_OFFSET
    previous_order: tuple[int, int, int] | None = None
    previous_predictive: int | None = None
    with path.open("rb") as stream:
        if len(stream.read(GSRT2_HEADER_BYTES)) != GSRT2_HEADER_BYTES:
            raise MaterializationError("short GSRT2 header")
        for index in range(header.record_count):
            payload = stream.read(GSRT2_RECORD_BYTES)
            if len(payload) != GSRT2_RECORD_BYTES:
                raise MaterializationError(f"short GSRT2 record {index}")
            values = GSRT2_RECORD.unpack(payload)
            (
                source,
                availability,
                first_bit,
                raw_before,
                raw_after,
                route_lo,
                route_hi,
                witness_lo,
                witness_hi,
                virtual_ordinal,
                _field_ordinal,
                event,
                flags,
                depth,
                key_identity,
            ) = values
            if event not in EXPECTED_FLAGS:
                raise MaterializationError("GSRT2 event type differs")
            if flags != EXPECTED_FLAGS[event] or key_identity != EXPECTED_KEY_IDENTITY[event]:
                raise MaterializationError("GSRT2 event flags or key identity differ")
            if source >= header.wrt_bytes or first_bit != availability * 8:
                raise MaterializationError("GSRT2 coordinate arithmetic differs")
            if not source <= availability <= header.wrt_bytes:
                raise MaterializationError("GSRT2 availability is outside population")
            if not 0 <= raw_before <= raw_after <= header.raw_bytes:
                raise MaterializationError("GSRT2 raw frontier differs")
            if event == EVENT_FIELD_VALUE_BYTE:
                if availability != source:
                    raise MaterializationError("GSRT2 predictive timing differs")
            elif event == EVENT_DEFERRED_VALUE_UPDATE:
                ordinary = availability == source + 2
                terminal = availability == header.wrt_bytes == source + 1
                if not (ordinary or terminal):
                    raise MaterializationError("GSRT2 deferred timing differs")
            elif availability != source + 1:
                raise MaterializationError("GSRT2 structural timing differs")
            if depth > 16:
                raise MaterializationError("GSRT2 route depth exceeds bound")
            routed = bool(flags & 1)
            route_zero = route_lo == 0 and route_hi == 0
            witness_zero = witness_lo == 0 and witness_hi == 0
            if routed:
                if route_zero or witness_zero or depth == 0:
                    raise MaterializationError("GSRT2 routed identity differs")
            elif not route_zero or not witness_zero or virtual_ordinal != 0:
                raise MaterializationError("GSRT2 unrouted record carries route state")
            order = (availability, _priority(event), source)
            if previous_order is not None and order < previous_order:
                raise MaterializationError("GSRT2 causal order regresses")
            previous_order = order
            counts[event - 1] += 1
            for word in (source, availability, route_lo, route_hi, virtual_ordinal):
                digest = _fnv_u64(digest, word)
            digest = _fnv_byte(digest, event)
            digest = _fnv_byte(digest, flags)
            if event == EVENT_FIELD_VALUE_BYTE and replay_begin <= source < replay_end:
                if previous_predictive is not None and source <= previous_predictive:
                    raise MaterializationError("GSRT2 predictive coordinates are not unique")
                previous_predictive = source
                yield source
        if stream.read(1):
            raise MaterializationError("trailing GSRT2 bytes")
    if tuple(counts) != header.event_counts:
        raise MaterializationError("GSRT2 body and header event counts differ")
    if digest != header.parser_digest:
        raise MaterializationError("GSRT2 parser digest differs")


def transcript_witnesses(
    trace_path: Path,
    wrt_path: Path,
    *,
    trace_header: bytes,
    wrt_sha256: str,
    observer_sha256: str,
    wrt_bytes: int,
    replay_begin: int,
    replay_end: int,
) -> tuple[str, str]:
    if replay_begin != 0 or not 0 < replay_end <= wrt_bytes:
        raise MaterializationError("HARM transcript replay must start at WRT zero")
    digest = hashlib.sha256()
    digest.update(TRANSCRIPT_DOMAIN)
    digest.update(bytes.fromhex(_require_hex_digest(observer_sha256, "parent observer")))
    digest.update(trace_header)
    digest.update(bytes.fromhex(_require_hex_digest(wrt_sha256, "WRT digest")))
    digest.update(struct.pack("<3Q", wrt_bytes, replay_begin, replay_end))
    begin = digest.hexdigest()
    with trace_path.open("rb") as trace, wrt_path.open("rb") as wrt:
        trace.seek(CMX21P1_HEADER_BYTES + replay_begin * 16)
        wrt.seek(replay_begin)
        for coordinate in range(replay_begin, replay_end):
            truth = wrt.read(1)
            probabilities = trace.read(16)
            if len(truth) != 1 or len(probabilities) != 16:
                raise MaterializationError("short transcript while building state witness")
            digest.update(struct.pack("<Q", coordinate))
            digest.update(truth)
            digest.update(probabilities)
    return begin, digest.hexdigest()


def _parse_hsp(path: Path) -> dict[str, object]:
    with path.open("rb") as stream:
        header = stream.read(HSP1_HEADER_BYTES)
        if len(header) != HSP1_HEADER_BYTES:
            raise MaterializationError("short HSP1 header")
        fields = HSP1_HEADER.unpack(header[: HSP1_HEADER.size])
        if (
            fields[0] != HSP1_MAGIC
            or fields[1:5] != (HSP1_VERSION, HSP1_HEADER_BYTES, HSP1_RECORD.size, 65536)
            or any(header[HSP1_HEADER.size :])
        ):
            raise MaterializationError("HSP1 output geometry differs")
        record_count = fields[8]
        if record_count <= 0 or path.stat().st_size != HSP1_HEADER_BYTES + record_count * HSP1_RECORD.size:
            raise MaterializationError("HSP1 output count or length differs")
        payload_digest = hashlib.sha256()
        coordinate_digest = hashlib.sha256()
        previous: int | None = None
        first: int | None = None
        last: int | None = None
        for _ in range(record_count):
            payload = stream.read(HSP1_RECORD.size)
            payload_digest.update(payload)
            coordinate, *probabilities = HSP1_RECORD.unpack(payload)
            if previous is not None and coordinate <= previous:
                raise MaterializationError("HSP1 output coordinates regress")
            if any(not 0 < value < 65536 for value in probabilities):
                raise MaterializationError("HSP1 output probability is outside Q16 interior")
            coordinate_digest.update(struct.pack("<Q", coordinate))
            first = coordinate if first is None else first
            last = coordinate
            previous = coordinate
        if stream.read(1):
            raise MaterializationError("trailing HSP1 output bytes")
    if (
        payload_digest.digest() != fields[11]
        or coordinate_digest.digest() != fields[12]
        or first != fields[9]
        or last != fields[10]
    ):
        raise MaterializationError("HSP1 output header does not bind its payload")
    return {
        "wrtBytes": fields[5],
        "replayBegin": fields[6],
        "replayEnd": fields[7],
        "recordCount": record_count,
        "firstCoordinate": fields[9],
        "lastCoordinate": fields[10],
        "payloadSha256": fields[11].hex(),
        "coordinateUnionSha256": fields[12].hex(),
        "parentObserverSha256": fields[13].hex(),
        "parentStateBeginSha256": fields[14].hex(),
        "parentStateEndSha256": fields[15].hex(),
    }


def materialize(
    *,
    trace_path: Path,
    wrt_path: Path,
    route_path: Path,
    output_path: Path,
    expected_trace_sha256: str,
    expected_wrt_sha256: str,
    expected_route_sha256: str,
    parent_observer_sha256: str,
    replay_begin: int,
    replay_end: int,
    expected_state_begin_sha256: str | None = None,
    expected_state_end_sha256: str | None = None,
) -> Materialization:
    """Create one exact HSP1 file after all supplied identities validate."""

    trace_path = _regular(trace_path, "CMX21P1 trace").resolve()
    wrt_path = _regular(wrt_path, "WRT truth stream").resolve()
    route_path = _regular(route_path, "GSRT2 route tape").resolve()
    if output_path.parent.is_symlink():
        raise MaterializationError("HSP1 output parent must not be a symlink")
    output_path = output_path.resolve()
    if output_path.exists() or output_path.is_symlink():
        raise MaterializationError("HSP1 output already exists")
    if not output_path.parent.is_dir() or output_path.parent.is_symlink():
        raise MaterializationError("HSP1 output parent must be a non-symlink directory")

    trace_sha = _require_identity(trace_path, expected_trace_sha256, "CMX21P1 trace")
    wrt_sha = _require_identity(wrt_path, expected_wrt_sha256, "WRT truth stream")
    route_sha = _require_identity(route_path, expected_route_sha256, "GSRT2 route tape")
    observer_sha = _require_hex_digest(parent_observer_sha256, "parent observer")
    wrt_bytes = wrt_path.stat().st_size
    trace_header = _trace_header(trace_path, wrt_bytes)
    tape_header = _tape_header(route_path, wrt_bytes)
    begin_witness, end_witness = transcript_witnesses(
        trace_path,
        wrt_path,
        trace_header=trace_header,
        wrt_sha256=wrt_sha,
        observer_sha256=observer_sha,
        wrt_bytes=wrt_bytes,
        replay_begin=replay_begin,
        replay_end=replay_end,
    )
    if expected_state_begin_sha256 is not None and begin_witness != _require_hex_digest(
        expected_state_begin_sha256, "expected parent state begin"
    ):
        raise MaterializationError("parent transcript begin witness differs")
    if expected_state_end_sha256 is not None and end_witness != _require_hex_digest(
        expected_state_end_sha256, "expected parent state end"
    ):
        raise MaterializationError("parent transcript end witness differs")

    temporary_path: Path | None = None
    payload_digest = hashlib.sha256()
    coordinate_digest = hashlib.sha256()
    record_count = 0
    first_coordinate = UINT64_MAX
    last_coordinate = UINT64_MAX
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "w+b") as output, trace_path.open("rb") as trace:
            output.write(bytes(HSP1_HEADER_BYTES))
            for coordinate in _iter_predictive_coordinates(
                route_path, tape_header, replay_begin, replay_end
            ):
                trace.seek(CMX21P1_HEADER_BYTES + coordinate * 16)
                probabilities = trace.read(16)
                if len(probabilities) != 16:
                    raise MaterializationError("short selected CMX21P1 byte row")
                values = struct.unpack("<8H", probabilities)
                if any(not 0 < value < 65536 for value in values):
                    raise MaterializationError("selected parent probability is outside Q16 interior")
                payload = struct.pack("<Q", coordinate) + probabilities
                output.write(payload)
                payload_digest.update(payload)
                coordinate_digest.update(struct.pack("<Q", coordinate))
                if record_count == 0:
                    first_coordinate = coordinate
                last_coordinate = coordinate
                record_count += 1
            if record_count == 0:
                raise MaterializationError("HARM sparse parent population is empty")
            header = HSP1_HEADER.pack(
                HSP1_MAGIC,
                HSP1_VERSION,
                HSP1_HEADER_BYTES,
                HSP1_RECORD.size,
                65536,
                wrt_bytes,
                replay_begin,
                replay_end,
                record_count,
                first_coordinate,
                last_coordinate,
                payload_digest.digest(),
                coordinate_digest.digest(),
                bytes.fromhex(observer_sha),
                bytes.fromhex(begin_witness),
                bytes.fromhex(end_witness),
            )
            output.seek(0)
            output.write(header)
            output.write(bytes(HSP1_HEADER_BYTES - len(header)))
            output.flush()
            os.fsync(output.fileno())
        parsed = _parse_hsp(temporary_path)
        expected_parsed = {
            "wrtBytes": wrt_bytes,
            "replayBegin": replay_begin,
            "replayEnd": replay_end,
            "recordCount": record_count,
            "firstCoordinate": first_coordinate,
            "lastCoordinate": last_coordinate,
            "payloadSha256": payload_digest.hexdigest(),
            "coordinateUnionSha256": coordinate_digest.hexdigest(),
            "parentObserverSha256": observer_sha,
            "parentStateBeginSha256": begin_witness,
            "parentStateEndSha256": end_witness,
        }
        if parsed != expected_parsed:
            raise MaterializationError("HSP1 self-verification differs")
        os.link(temporary_path, output_path, follow_symlinks=False)
        temporary_path.unlink()
        temporary_path = None
        directory_descriptor = os.open(output_path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass

    return Materialization(
        trace_sha256=trace_sha,
        wrt_sha256=wrt_sha,
        route_sha256=route_sha,
        output_sha256=sha256_path(output_path),
        output_bytes=output_path.stat().st_size,
        record_count=record_count,
        first_coordinate=first_coordinate,
        last_coordinate=last_coordinate,
        payload_sha256=payload_digest.hexdigest(),
        coordinate_union_sha256=coordinate_digest.hexdigest(),
        parent_observer_sha256=observer_sha,
        parent_state_begin_sha256=begin_witness,
        parent_state_end_sha256=end_witness,
    )
