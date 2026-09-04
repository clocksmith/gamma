#!/usr/bin/env python3
"""Generated source fixture and corruptions for sparse parent materialization."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import shutil
import struct
import sys
from typing import Callable

import materializer


WRT = b"qMabQxyZ!"
PREDICTIVE_COORDINATES = (2, 3, 5, 8)
ROUTE = (0x101, 0x202, 0x303, 0x404)
ABI_PATH = "programs/harm_delta_sparse_input_abi_q0_v1/abi.py"
ABI_SHA256 = "5b35e4bc19fac743491a5a95831e5319764707efe4afcd41503970f38cda653d"
TRANSCRIPT_DOMAIN = b"GAMMA-HSP1-PARENT-TRANSCRIPT-WITNESS-V1\0"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _fnv_byte(value: int, byte: int) -> int:
    return ((value ^ byte) * 1099511628211) & ((1 << 64) - 1)


def _fnv_u64(value: int, word: int) -> int:
    for index in range(8):
        value = _fnv_byte(value, (word >> (8 * index)) & 0xFF)
    return value


def _parser_digest(rows: list[tuple[int, ...]]) -> int:
    digest = 1469598103934665603
    for row in rows:
        for word in (row[0], row[1], row[5], row[6], row[9]):
            digest = _fnv_u64(digest, word)
        digest = _fnv_byte(digest, row[11])
        digest = _fnv_byte(digest, row[12])
    return digest


def _row(
    source: int,
    availability: int,
    event: int,
    *,
    virtual: int = 0,
    routed: bool = False,
    field_ordinal: int = 0,
) -> tuple[int, ...]:
    route = ROUTE if routed else (0, 0, 0, 0)
    return (
        source,
        availability,
        availability * 8,
        source,
        min(len(WRT), source + 1),
        *route,
        virtual,
        field_ordinal,
        materializer.EXPECTED_FLAGS[event],
        1 if routed else 0,
        materializer.EXPECTED_KEY_IDENTITY[event],
    )[:11] + (
        event,
        materializer.EXPECTED_FLAGS[event],
        1 if routed else 0,
        materializer.EXPECTED_KEY_IDENTITY[event],
    )


def _rows(*, duplicate: bool = False) -> list[tuple[int, ...]]:
    second = 2 if duplicate else 3
    return [
        _row(0, 1, 1),
        _row(1, 2, 2, routed=True),
        _row(2, 2, 3, virtual=0, routed=True),
        _row(second, second, 3, virtual=1, routed=True),
        _row(5, 5, 3, virtual=2, routed=True),
        _row(8, 8, 3, virtual=3, routed=True),
        _row(8, 9, 5, virtual=4, routed=True),
        _row(8, 9, 7),
    ]


def _write_gsrt2(path: Path, rows: list[tuple[int, ...]]) -> None:
    counts = [0] * 9
    for row in rows:
        counts[row[11] - 1] += 1
    header = bytearray(materializer.GSRT2_HEADER_BYTES)
    header[:8] = materializer.GSRT2_MAGIC
    struct.pack_into(
        "<IIII",
        header,
        8,
        materializer.GSRT2_VERSION,
        materializer.GSRT2_HEADER_BYTES,
        materializer.GSRT2_RECORD_BYTES,
        1,
    )
    geometry = (len(WRT), len(WRT), len(WRT), 0, len(rows), 1)
    struct.pack_into("<6Q", header, 24, *geometry)
    struct.pack_into("<9Q", header, 72, *counts)
    struct.pack_into("<Q", header, 144, counts[3])
    struct.pack_into("<Q", header, 152, 0)
    struct.pack_into("<Q", header, 160, 0)
    struct.pack_into("<Q", header, 168, _parser_digest(rows))
    struct.pack_into("<Q", header, 176, 0xABCDEF01)
    struct.pack_into("<Q", header, 184, 0x12345678)
    body = b"".join(materializer.GSRT2_RECORD.pack(*row) for row in rows)
    path.write_bytes(bytes(header) + body)


def _probability(coordinate: int, bit_index: int) -> int:
    return 1000 + 113 * coordinate + 7 * bit_index


def _write_trace(path: Path) -> None:
    rows = len(WRT) * 8
    payload = bytearray(materializer.CMX21P1_MAGIC + struct.pack("<Q", rows))
    for coordinate in range(len(WRT)):
        for bit_index in range(8):
            payload.extend(struct.pack("<H", _probability(coordinate, bit_index)))
    path.write_bytes(payload)


def _reference_witness(
    trace: bytes, wrt: bytes, observer_sha256: str, replay_end: int
) -> tuple[str, str]:
    digest = hashlib.sha256()
    digest.update(TRANSCRIPT_DOMAIN)
    digest.update(bytes.fromhex(observer_sha256))
    digest.update(trace[:16])
    digest.update(hashlib.sha256(wrt).digest())
    digest.update(struct.pack("<3Q", len(wrt), 0, replay_end))
    begin = digest.hexdigest()
    for coordinate in range(replay_end):
        start = 16 + coordinate * 16
        digest.update(struct.pack("<Q", coordinate))
        digest.update(wrt[coordinate : coordinate + 1])
        digest.update(trace[start : start + 16])
    return begin, digest.hexdigest()


def _read_hsp_rows(path: Path) -> list[tuple[int, tuple[int, ...]]]:
    rows: list[tuple[int, tuple[int, ...]]] = []
    with path.open("rb") as stream:
        stream.seek(materializer.HSP1_HEADER_BYTES)
        while True:
            payload = stream.read(materializer.HSP1_RECORD.size)
            if not payload:
                break
            values = materializer.HSP1_RECORD.unpack(payload)
            rows.append((values[0], tuple(values[1:])))
    return rows


def _load_frozen_abi(project_root: Path):
    path = project_root / ABI_PATH
    if _sha256(path) != ABI_SHA256:
        raise AssertionError("measured HSP1 ABI source identity differs")
    spec = importlib.util.spec_from_file_location("_measured_hsp1_abi", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load measured HSP1 ABI")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _materialize(
    trace: Path,
    wrt: Path,
    route: Path,
    output: Path,
    observer_sha: str,
    *,
    expected_wrt_sha: str | None = None,
    expected_end: str | None = None,
) -> materializer.Materialization:
    return materializer.materialize(
        trace_path=trace,
        wrt_path=wrt,
        route_path=route,
        output_path=output,
        expected_trace_sha256=_sha256(trace),
        expected_wrt_sha256=(
            _sha256(wrt) if expected_wrt_sha is None else expected_wrt_sha
        ),
        expected_route_sha256=_sha256(route),
        parent_observer_sha256=observer_sha,
        replay_begin=0,
        replay_end=len(WRT),
        expected_state_end_sha256=expected_end,
    )


def _copy_inputs(base: Path, case: Path) -> tuple[Path, Path, Path]:
    case.mkdir()
    trace = case / "parent.p1"
    wrt = case / "truth.wrt"
    route = case / "route.gsrt2"
    shutil.copyfile(base / "parent.p1", trace)
    shutil.copyfile(base / "truth.wrt", wrt)
    shutil.copyfile(base / "route-a.gsrt2", route)
    return trace, wrt, route


def _negative_controls(base: Path, root: Path, observer_sha: str) -> dict[str, str]:
    root.mkdir()
    rejected: dict[str, str] = {}

    def expect(
        label: str,
        mutation: Callable[[Path, Path, Path], tuple[str | None, str | None]],
    ) -> None:
        case = root / label
        trace, wrt, route = _copy_inputs(base, case)
        expected_wrt, expected_end = mutation(trace, wrt, route)
        output = case / "unexpected.hsp1"
        try:
            _materialize(
                trace,
                wrt,
                route,
                output,
                observer_sha,
                expected_wrt_sha=expected_wrt,
                expected_end=expected_end,
            )
        except (ValueError, OSError, materializer.MaterializationError) as error:
            if output.exists() or output.is_symlink():
                raise AssertionError(f"{label} installed an output") from error
            rejected[label] = str(error)
            return
        raise AssertionError(f"negative control escaped: {label}")

    def mutate_bytes(path: Path, offset: int, payload: bytes) -> None:
        data = bytearray(path.read_bytes())
        data[offset : offset + len(payload)] = payload
        path.write_bytes(data)

    expect("trace_magic", lambda trace, _wrt, _route: (
        mutate_bytes(trace, 0, b"BROKEN!!") or None, None
    ))
    expect("trace_row_count", lambda trace, _wrt, _route: (
        mutate_bytes(trace, 8, struct.pack("<Q", len(WRT) * 8 - 1)) or None, None
    ))

    def truncate_trace(trace: Path, _wrt: Path, _route: Path) -> tuple[None, None]:
        trace.write_bytes(trace.read_bytes()[:-1])
        return None, None

    expect("trace_length", truncate_trace)
    expect("zero_probability", lambda trace, _wrt, _route: (
        mutate_bytes(trace, 16 + PREDICTIVE_COORDINATES[0] * 16, b"\0\0") or None,
        None,
    ))
    expect("route_magic", lambda _trace, _wrt, route: (
        mutate_bytes(route, 0, b"BROKEN!!") or None, None
    ))
    expect("route_event_accounting", lambda _trace, _wrt, route: (
        mutate_bytes(route, 72 + 2 * 8, struct.pack("<Q", 5)) or None, None
    ))

    def duplicate_route(_trace: Path, _wrt: Path, route: Path) -> tuple[None, None]:
        _write_gsrt2(route, _rows(duplicate=True))
        return None, None

    expect("duplicate_predictive_coordinate", duplicate_route)
    expect("route_wrt_population", lambda _trace, _wrt, route: (
        mutate_bytes(route, 32, struct.pack("<Q", len(WRT) + 1)) or None, None
    ))
    expect("bound_wrt_digest", lambda _trace, _wrt, _route: ("0" * 64, None))
    expect("terminal_witness", lambda _trace, _wrt, _route: (None, "1" * 64))
    return rejected


def run_fixture(project_root: Path, root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=False)
    inputs = root / "inputs"
    inputs.mkdir()
    trace = inputs / "parent.p1"
    wrt = inputs / "truth.wrt"
    route_a = inputs / "route-a.gsrt2"
    route_b = inputs / "route-b.gsrt2"
    observer = inputs / "parent-observer.txt"
    _write_trace(trace)
    wrt.write_bytes(WRT)
    _write_gsrt2(route_a, _rows())
    shutil.copyfile(route_a, route_b)
    observer.write_text("generated parent observer v1\n", encoding="utf-8")
    observer_sha = _sha256(observer)

    output_a = root / "parent-a.hsp1"
    output_b = root / "parent-b.hsp1"
    first = _materialize(trace, wrt, route_a, output_a, observer_sha)
    second = _materialize(trace, wrt, route_b, output_b, observer_sha)
    repeat_identity = output_a.read_bytes() == output_b.read_bytes()
    semantic_repeat = first.semantic_identity() == second.semantic_identity()

    expected_rows = [
        (
            coordinate,
            tuple(_probability(coordinate, bit_index) for bit_index in range(8)),
        )
        for coordinate in PREDICTIVE_COORDINATES
    ]
    observed_rows = _read_hsp_rows(output_a)
    exact_extraction = observed_rows == expected_rows
    reference_begin, reference_end = _reference_witness(
        trace.read_bytes(), WRT, observer_sha, len(WRT)
    )
    witness_pass = (
        first.parent_state_begin_sha256 == reference_begin
        and first.parent_state_end_sha256 == reference_end
        and second.parent_state_begin_sha256 == reference_begin
        and second.parent_state_end_sha256 == reference_end
    )

    abi = _load_frozen_abi(project_root)
    abi_a = abi._hsp_metadata(output_a)
    abi_b = abi._hsp_metadata(output_b)
    hsp_abi_pass = (
        abi_a == abi_b
        and abi_a.record_count == len(PREDICTIVE_COORDINATES)
        and abi_a.payload_sha256 == first.payload_sha256
        and abi_a.coordinate_union_sha256 == first.coordinate_union_sha256
        and abi_a.parent_state_begin_sha256 == reference_begin
        and abi_a.parent_state_end_sha256 == reference_end
    )
    rejected = _negative_controls(inputs, root / "negative", observer_sha)
    input_paths = [trace.resolve(), wrt.resolve(), route_a.resolve(), route_b.resolve()]
    if any(root.resolve() not in path.parents for path in input_paths):
        raise AssertionError("fixture input escaped generated root")

    return {
        "fixture_wrt_bytes": len(WRT),
        "predictive_record_count": first.record_count,
        "predictive_coordinates": list(PREDICTIVE_COORDINATES),
        "selected_probability_rows": [
            {"coordinate": coordinate, "p1": list(probabilities)}
            for coordinate, probabilities in observed_rows
        ],
        "exact_coordinate_extraction_pass": exact_extraction,
        "repeat_identity_pass": repeat_identity and semantic_repeat,
        "transcript_witness_pass": witness_pass,
        "hsp_abi_acceptance_pass": hsp_abi_pass,
        "parent_state_begin_sha256": reference_begin,
        "parent_state_end_sha256": reference_end,
        "hsp1_sha256": first.output_sha256,
        "hsp1_bytes": first.output_bytes,
        "hsp1_payload_sha256": first.payload_sha256,
        "coordinate_union_sha256": first.coordinate_union_sha256,
        "negative_control_reject_count": len(rejected),
        "negative_control_rejections": rejected,
        "corpus_access_count": 0,
        "active_trace_access_count": 0,
        "opened_fixture_inputs": [str(path) for path in input_paths],
        "abi_source_sha256": ABI_SHA256,
        "archive_authority": False,
        "retained_parent_gain_authority": False,
        "corpus_execution_authority": False,
        "objective_credit_bytes": 0,
    }
