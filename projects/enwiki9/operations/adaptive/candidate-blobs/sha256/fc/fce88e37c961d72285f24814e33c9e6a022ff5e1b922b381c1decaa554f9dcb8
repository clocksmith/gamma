#!/usr/bin/env python3
"""Independent ABI and repeat verifier for the Endpoint428 semantic route tape."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
from pathlib import Path
from typing import BinaryIO


TAPE_HEADER_BYTES = 192
TAPE_RECORD_BYTES = 88
SIDE_HEADER_BYTES = 64
SIDE_RECORD_BYTES = 232
FNV_OFFSET = 1469598103934665603
FNV_PRIME = 1099511628211
MASK64 = (1 << 64) - 1
FULL_STORE_BYTES = 647_798_597
FULL_WRT_BYTES = 647_798_592
FULL_RAW_BYTES = 1_000_000_000
FULL_DICTIONARY_BYTES = 411_996
FULL_STORE_SHA256 = "fe6ab5b96ad7bf2b6f7bd9f7cd3b3212ffc7320ae290e098f68e97b53295ceb9"
FULL_RAW_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
FULL_DICTIONARY_SHA256 = "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a"

VALID_ROUTE = 1
PREDICTIVE = 2
UPDATE_ONLY = 4
EXPLICIT_KEY = 8
POSITIONAL_AUDIT = 16
OVERFLOW = 32
DEFERRED = 64
POSTTRUTH = 128

EXPECTED_FLAGS = {
    1: POSTTRUTH,
    2: VALID_ROUTE | EXPLICIT_KEY | POSTTRUTH,
    3: VALID_ROUTE | PREDICTIVE | EXPLICIT_KEY,
    4: VALID_ROUTE | UPDATE_ONLY | EXPLICIT_KEY | DEFERRED,
    5: VALID_ROUTE | EXPLICIT_KEY | POSTTRUTH,
    6: POSITIONAL_AUDIT | POSTTRUTH,
    7: POSTTRUTH,
    8: OVERFLOW | POSTTRUTH,
    9: OVERFLOW | POSTTRUTH,
}
EXPECTED_KEY_IDENTITY = {1: 0, 2: 1, 3: 1, 4: 1, 5: 1, 6: 2, 7: 0, 8: 0, 9: 0}


class VerificationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def u64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def fnv_byte(value: int, byte: int) -> int:
    return ((value ^ byte) * FNV_PRIME) & MASK64


def fnv_u64(value: int, item: int) -> int:
    for shift in range(0, 64, 8):
        value = fnv_byte(value, (item >> shift) & 0xFF)
    return value


def mix64(value: int) -> int:
    value ^= value >> 30
    value = (value * 0xBF58476D1CE4E5B9) & MASK64
    value ^= value >> 27
    value = (value * 0x94D049BB133111EB) & MASK64
    value ^= value >> 31
    return value & MASK64


def hash_descriptor(name: bytes, key: bytes, seed_a: int, seed_b: int) -> tuple[int, int]:
    a = fnv_u64(FNV_OFFSET ^ seed_a, len(name))
    b = fnv_u64(FNV_OFFSET ^ seed_b, len(name))
    for byte in name:
        a = fnv_byte(a, byte)
        b = fnv_byte(b, byte)
    a = fnv_byte(a, 1)
    b = fnv_byte(b, 1)
    a = fnv_u64(a, len(key))
    b = fnv_u64(b, len(key))
    for byte in key:
        a = fnv_byte(a, byte)
        b = fnv_byte(b, byte)
    a = mix64(a)
    b = mix64(b)
    if (a | b) == 0:
        a = 1
    return a, b


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1 << 20)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def read_exact(handle: BinaryIO, count: int, context: str) -> bytes:
    data = handle.read(count)
    require(len(data) == count, f"short {context}")
    return data


def parse_tape_header(path: Path) -> dict[str, object]:
    with path.open("rb") as handle:
        header = read_exact(handle, TAPE_HEADER_BYTES, "tape header")
    require(header[:8] == b"GSRT2\0\0\0", "tape magic")
    require(u32(header, 8) == 2, "tape version")
    require(u32(header, 12) == TAPE_HEADER_BYTES, "tape header bytes")
    require(u32(header, 16) == TAPE_RECORD_BYTES, "tape record bytes")
    fixture_flags = u32(header, 20)
    require((fixture_flags & ~1) == 0, "tape reserved flags")
    result: dict[str, object] = {
        "fixture": bool(fixture_flags & 1),
        "store_bytes": u64(header, 24),
        "wrt_bytes": u64(header, 32),
        "raw_bytes": u64(header, 40),
        "dictionary_bytes": u64(header, 48),
        "record_count": u64(header, 56),
        "descriptor_count": u64(header, 64),
        "event_counts": [u64(header, 72 + 8 * index) for index in range(9)],
        "deferred_updates": u64(header, 144),
        "positional_predictive_events": u64(header, 152),
        "pretruth_violations": u64(header, 160),
        "parser_digest": u64(header, 168),
        "raw_digest": u64(header, 176),
        "wrt_digest": u64(header, 184),
    }
    expected_size = TAPE_HEADER_BYTES + TAPE_RECORD_BYTES * int(result["record_count"])
    require(path.stat().st_size == expected_size, "tape file size")
    require(sum(result["event_counts"]) == result["record_count"], "tape event sum")
    return result


def parse_sidecar(path: Path, tape_header: dict[str, object]) -> dict[str, object]:
    with path.open("rb") as handle:
        header = read_exact(handle, SIDE_HEADER_BYTES, "sidecar header")
        require(header[:8] == b"GSRD2\0\0\0", "sidecar magic")
        require(u32(header, 8) == 2, "sidecar version")
        require(u32(header, 12) == SIDE_HEADER_BYTES, "sidecar header bytes")
        require(u32(header, 16) == SIDE_RECORD_BYTES, "sidecar record bytes")
        fixture_flags = u32(header, 20)
        require((fixture_flags & ~1) == 0, "sidecar reserved flags")
        require(bool(fixture_flags & 1) == tape_header["fixture"], "sidecar fixture flag")
        descriptor_count = u64(header, 24)
        require(descriptor_count == tape_header["descriptor_count"], "sidecar descriptor count")
        require(u64(header, 32) == tape_header["parser_digest"], "sidecar parser digest")
        require(header[40:] == bytes(24), "sidecar reserved header bytes")
        require(path.stat().st_size == SIDE_HEADER_BYTES + SIDE_RECORD_BYTES * descriptor_count,
                "sidecar file size")

        by_route: dict[tuple[int, int], tuple[tuple[int, int], bytes, bytes]] = {}
        by_witness: dict[tuple[int, int], tuple[tuple[int, int], bytes, bytes]] = {}
        for index in range(descriptor_count):
            record = read_exact(handle, SIDE_RECORD_BYTES, f"sidecar record {index}")
            route = (u64(record, 0), u64(record, 8))
            witness = (u64(record, 16), u64(record, 24))
            name_size = u16(record, 32)
            key_size = u16(record, 34)
            require(1 <= name_size <= 96 and 1 <= key_size <= 96, "descriptor atom size")
            require(record[36] == 1 and record[37:40] == bytes(3), "descriptor marker/padding")
            name = record[40:40 + name_size]
            key = record[136:136 + key_size]
            require(record[40 + name_size:136] == bytes(96 - name_size), "descriptor name padding")
            require(record[136 + key_size:232] == bytes(96 - key_size), "descriptor key padding")
            require(route != (0, 0) and witness != (0, 0), "zero descriptor digest")
            expected_route = hash_descriptor(name, key, 0x5254554C455F3031, 0x5254554C455F3032)
            expected_witness = hash_descriptor(name, key, 0x5749544E45535331, 0x5749544E45535332)
            require(route == expected_route, "route digest mismatch")
            require(witness == expected_witness, "witness digest mismatch")
            descriptor = (witness, name, key)
            require(route not in by_route, "duplicate route descriptor")
            require(witness not in by_witness, "duplicate witness descriptor")
            by_route[route] = descriptor
            by_witness[witness] = (route, name, key)
        require(handle.read(1) == b"", "sidecar trailing byte")
    return {"by_route": by_route, "by_witness": by_witness}


def record_priority(event: int) -> int:
    if event == 4:
        return 0
    if event == 3:
        return 2
    return 1


def verify_tape_records(
    path: Path,
    header: dict[str, object],
    sidecar: dict[str, object],
    fixture_wrt: bytes | None,
) -> dict[str, object]:
    event_counts = [0] * 9
    parser_digest = FNV_OFFSET
    last_availability = -1
    last_priority = -1
    last_route_ordinal: dict[tuple[int, int], int] = {}
    predicted_fixture_truths = {ord("P"): 0, ord("Q"): 0, ord("R"): 0}
    with path.open("rb") as handle:
        read_exact(handle, TAPE_HEADER_BYTES, "tape header")
        for index in range(int(header["record_count"])):
            data = read_exact(handle, TAPE_RECORD_BYTES, f"tape record {index}")
            source = u64(data, 0)
            availability = u64(data, 8)
            physical = u64(data, 16)
            raw_before = u64(data, 24)
            raw_after = u64(data, 32)
            route = (u64(data, 40), u64(data, 48))
            witness = (u64(data, 56), u64(data, 64))
            virtual_ordinal = u64(data, 72)
            event = data[84]
            flags = data[85]
            depth = data[86]
            key_identity = data[87]

            require(1 <= event <= 9, "record event type")
            require(source < int(header["wrt_bytes"]), "record source coordinate")
            require(source <= availability <= int(header["wrt_bytes"]), "record availability")
            require(availability <= MASK64 // 8 and physical == availability * 8,
                    "record physical coordinate")
            require(raw_before <= raw_after <= int(header["raw_bytes"]), "record raw frontier")
            require(flags == EXPECTED_FLAGS[event], "record flags")
            require(key_identity == EXPECTED_KEY_IDENTITY[event], "record key identity")
            require(depth <= 16, "record template depth")

            priority = record_priority(event)
            require(availability >= last_availability, "record availability order")
            if availability == last_availability:
                require(priority >= last_priority, "equal-availability causal order")
            else:
                last_availability = availability
                last_priority = -1
            last_priority = priority

            if event == 3:
                require(availability == source, "predictive availability")
                if fixture_wrt is not None and fixture_wrt[source] in predicted_fixture_truths:
                    predicted_fixture_truths[fixture_wrt[source]] += 1
            elif event == 4:
                require(availability == source + 2 or
                        (availability == int(header["wrt_bytes"]) and availability == source + 1),
                        "deferred availability")
                if fixture_wrt is not None:
                    require(fixture_wrt[source] in (ord("P"), ord("R")),
                            "deferred non-delimiter source")
            else:
                require(availability == source + 1, "posttruth availability")

            if flags & VALID_ROUTE:
                require(route != (0, 0) and witness != (0, 0), "zero routed digest")
                descriptor = sidecar["by_route"].get(route)
                require(descriptor is not None and descriptor[0] == witness, "unknown route/witness")
                reverse = sidecar["by_witness"].get(witness)
                require(reverse is not None and reverse[0] == route, "unknown witness/route")
                previous = last_route_ordinal.get(route)
                require(previous is None or virtual_ordinal >= previous, "route ordinal regression")
                last_route_ordinal[route] = virtual_ordinal
            else:
                require(route == (0, 0) and witness == (0, 0), "route on unrouted record")
                require(virtual_ordinal == 0, "ordinal on unrouted record")

            event_counts[event - 1] += 1
            parser_digest = fnv_u64(parser_digest, source)
            parser_digest = fnv_u64(parser_digest, availability)
            parser_digest = fnv_u64(parser_digest, route[0])
            parser_digest = fnv_u64(parser_digest, route[1])
            parser_digest = fnv_u64(parser_digest, virtual_ordinal)
            parser_digest = fnv_byte(parser_digest, event)
            parser_digest = fnv_byte(parser_digest, flags)
        require(handle.read(1) == b"", "tape trailing byte")

    require(event_counts == header["event_counts"], "event count mismatch")
    require(event_counts[3] == header["deferred_updates"], "deferred count mismatch")
    require(header["positional_predictive_events"] == 0, "positional predictive event")
    require(header["pretruth_violations"] == 0, "pretruth eligibility violation")
    require(parser_digest == header["parser_digest"], "parser digest mismatch")
    return {
        "event_counts": event_counts,
        "parser_digest": parser_digest,
        "predicted_fixture_truths": predicted_fixture_truths,
    }


def fnv_and_sha(path: Path, skip: int = 0) -> tuple[int, str, bytes]:
    digest = hashlib.sha256()
    fnv = FNV_OFFSET
    prefix = b""
    with path.open("rb") as handle:
        if skip:
            skipped = read_exact(handle, skip, "input prefix")
            digest.update(skipped)
        while True:
            block = handle.read(1 << 20)
            if not block:
                break
            digest.update(block)
            if len(prefix) < 6:
                prefix += block[:6 - len(prefix)]
            for byte in block:
                fnv = fnv_byte(fnv, byte)
    return fnv, digest.hexdigest(), prefix


def verify_inputs(store: Path, raw: Path, dictionary: Path, header: dict[str, object]) -> dict[str, str]:
    require(store.stat().st_size == header["store_bytes"], "store geometry")
    require(raw.stat().st_size == header["raw_bytes"], "raw geometry")
    require(dictionary.stat().st_size == header["dictionary_bytes"], "dictionary geometry")
    with store.open("rb") as handle:
        require(read_exact(handle, 5, "store wrapper") == b"\x80\0\0\0\0", "store wrapper")
    wrt_fnv, store_sha, wrt_prefix = fnv_and_sha(store, 5)
    raw_fnv, raw_sha, _ = fnv_and_sha(raw)
    _, dictionary_sha, _ = fnv_and_sha(dictionary)
    require(len(wrt_prefix) == 6 and wrt_prefix[0] == 7 and wrt_prefix[5] == 7,
            "WRT stream header")
    require(int.from_bytes(wrt_prefix[1:5], "big") == header["raw_bytes"], "WRT raw length header")
    require(wrt_fnv == header["wrt_digest"], "WRT digest mismatch")
    require(raw_fnv == header["raw_digest"], "raw digest mismatch")
    if not header["fixture"]:
        require(header["store_bytes"] == FULL_STORE_BYTES, "full store bytes")
        require(header["wrt_bytes"] == FULL_WRT_BYTES, "full WRT bytes")
        require(header["raw_bytes"] == FULL_RAW_BYTES, "full raw bytes")
        require(header["dictionary_bytes"] == FULL_DICTIONARY_BYTES, "full dictionary bytes")
        require(store_sha == FULL_STORE_SHA256, "full store SHA-256")
        require(raw_sha == FULL_RAW_SHA256, "full raw SHA-256")
        require(dictionary_sha == FULL_DICTIONARY_SHA256, "full dictionary SHA-256")
    return {"store_sha256": store_sha, "raw_sha256": raw_sha,
            "dictionary_sha256": dictionary_sha}


def verify_summary(path: Path, header: dict[str, object]) -> dict[str, object]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    require(summary["schema"] == "gamma.enwiki9.endpoint428-semantic-route-tape-summary.v2",
            "summary schema")
    require(summary["candidate_id"] == "endpoint428_semantic_route_tape_q0_v2",
            "summary candidate")
    expected = {
        "fixture": header["fixture"],
        "store_bytes": header["store_bytes"],
        "wrt_stream_bytes": header["wrt_bytes"],
        "reconstructed_raw_bytes": header["raw_bytes"],
        "dictionary_bytes": header["dictionary_bytes"],
        "record_bytes": TAPE_RECORD_BYTES,
        "record_count": header["record_count"],
        "descriptor_count": header["descriptor_count"],
        "event_counts": header["event_counts"],
        "deferred_update_events": header["deferred_updates"],
        "positional_predictive_events": header["positional_predictive_events"],
        "pretruth_eligibility_violations": header["pretruth_violations"],
        "parser_fnv1a64": f"{int(header['parser_digest']):016x}",
        "raw_fnv1a64": f"{int(header['raw_digest']):016x}",
        "wrt_fnv1a64": f"{int(header['wrt_digest']):016x}",
        "archive_authority": False,
        "score_credit_bytes": 0,
    }
    for key, value in expected.items():
        require(summary.get(key) == value, f"summary field {key}")
    require(set(summary) == {"schema", "candidate_id", *expected.keys()}, "summary extra/missing fields")
    return summary


def require_regular(path: Path, label: str) -> None:
    require(path.exists() and path.is_file() and not path.is_symlink(), f"{label} regular file")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--dictionary", required=True, type=Path)
    parser.add_argument("--tape-a", required=True, type=Path)
    parser.add_argument("--tape-b", required=True, type=Path)
    parser.add_argument("--sidecar-a", required=True, type=Path)
    parser.add_argument("--sidecar-b", required=True, type=Path)
    parser.add_argument("--summary-a", required=True, type=Path)
    parser.add_argument("--summary-b", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()

    paths = [args.store, args.raw, args.dictionary, args.tape_a, args.tape_b,
             args.sidecar_a, args.sidecar_b, args.summary_a, args.summary_b]
    for path in paths:
        require_regular(path, str(path))
    require(not args.receipt.exists() and not args.receipt.is_symlink(), "exclusive receipt path")

    header_a = parse_tape_header(args.tape_a)
    header_b = parse_tape_header(args.tape_b)
    require(header_a == header_b, "A/B tape header identity")
    fixture_wrt = args.store.read_bytes()[5:] if header_a["fixture"] else None
    if fixture_wrt is not None:
        require(len(fixture_wrt) == header_a["wrt_bytes"], "fixture WRT geometry")
    side_a = parse_sidecar(args.sidecar_a, header_a)
    side_b = parse_sidecar(args.sidecar_b, header_b)
    records_a = verify_tape_records(args.tape_a, header_a, side_a, fixture_wrt)
    records_b = verify_tape_records(args.tape_b, header_b, side_b, fixture_wrt)
    require(records_a == records_b, "A/B parsed record identity")
    summary_a = verify_summary(args.summary_a, header_a)
    summary_b = verify_summary(args.summary_b, header_b)
    require(summary_a == summary_b, "A/B normalized summary identity")

    hashes = {
        "tape_a_sha256": hash_file(args.tape_a),
        "tape_b_sha256": hash_file(args.tape_b),
        "sidecar_a_sha256": hash_file(args.sidecar_a),
        "sidecar_b_sha256": hash_file(args.sidecar_b),
        "summary_a_sha256": hash_file(args.summary_a),
        "summary_b_sha256": hash_file(args.summary_b),
    }
    require(hashes["tape_a_sha256"] == hashes["tape_b_sha256"], "A/B tape bytes")
    require(hashes["sidecar_a_sha256"] == hashes["sidecar_b_sha256"], "A/B sidecar bytes")
    require(hashes["summary_a_sha256"] == hashes["summary_b_sha256"], "A/B summary bytes")
    input_hashes = verify_inputs(args.store, args.raw, args.dictionary, header_a)

    if header_a["fixture"]:
        events = header_a["event_counts"]
        require(events[1] > 0 and events[2] > 0, "fixture explicit route coverage")
        require(events[3] > 0, "fixture deferred coverage")
        require(events[5] > 0, "fixture positional coverage")
        require(events[7] > 0 and events[8] > 0, "fixture overflow coverage")
        require(all(count > 0 for count in records_a["predicted_fixture_truths"].values()),
                "fixture current-delimiter prediction coverage")

    receipt = {
        "schema": "gamma.enwiki9.endpoint428-semantic-route-tape-verification.v2",
        "candidate_id": "endpoint428_semantic_route_tape_q0_v2",
        "verification_pass": True,
        "fixture": header_a["fixture"],
        "scanned_wrt_bytes": header_a["wrt_bytes"],
        "reconstructed_raw_bytes": header_a["raw_bytes"],
        "record_count": header_a["record_count"],
        "descriptor_count": header_a["descriptor_count"],
        "event_counts": header_a["event_counts"],
        "causal_abi_pass": True,
        "repeat_identity_pass": True,
        "descriptor_alias_count": 0,
        "positional_predictive_events": 0,
        "pretruth_eligibility_violations": 0,
        "input_hashes": input_hashes,
        "artifact_hashes": hashes,
        "archive_authority": False,
        "score_credit_bytes": 0,
        "claim": "source-validation-only" if header_a["fixture"] else "zero-credit-population-infrastructure",
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as error:
        print(f"verification failed: {error}", file=__import__("sys").stderr)
        raise SystemExit(1)
