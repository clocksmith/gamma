#!/usr/bin/env python3
"""Generated native/reference fixture for the HORIZON-A field-entry observer."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from typing import Any, Callable


WRT_BYTES = 128
WRT = bytes(WRT_BYTES)
FIELD_TARGETS = (49, 80)
HASH_BASE = 0x9E3779B185EBCA87
HASH_POWER_16 = 0x6FE6EF9FBD3B9581
MASK64 = (1 << 64) - 1
FNV_OFFSET = 1469598103934665603
FNV_PRIME = 1099511628211
FIXTURE_TABLE_BITS = 8
FIXTURE_MINIMUM_AGE = 32
FIXTURE_DONOR_BYTES = 16
PRODUCTION_AGE_LIFT = 100_000_000

GSRT_HEADER_BYTES = 192
GSRT_RECORD = struct.Struct("<10QI4B")
RAW_HEADER_BYTES = 32
RAW_RECORD = struct.Struct("<4Q")
RAW_MAGIC = b"HGSR1\0\0\0"
EXPECTED_FLAGS = {1: 128, 2: 137, 3: 11, 4: 77, 5: 137, 6: 144, 7: 128, 8: 160, 9: 160}
EXPECTED_KEYS = {1: 0, 2: 1, 3: 1, 4: 1, 5: 1, 6: 2, 7: 0, 8: 0, 9: 0}
ROUTE = (0x101, 0x202, 0x303, 0x404)

HORIZON_SOURCE = "programs/endpoint428_horizon_dualclock_source_census_q0_retry_v1/horizon-dualclock-scan.cpp"
HORIZON_SOURCE_SHA256 = "ff08edea191055ceecc23ebf6008e1aaa2f0f573c1a005b61d6a48c45be68b8a"
ABI_PATH = "programs/harm_delta_sparse_input_abi_q0_v1/abi.py"
ABI_SHA256 = "5b35e4bc19fac743491a5a95831e5319764707efe4afcd41503970f38cda653d"
HARM_BINDING = "programs/harm_route_edit_residual_shadow_q0_v1/source-binding.json"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _fnv_byte(value: int, byte: int) -> int:
    return ((value ^ byte) * FNV_PRIME) & MASK64


def _fnv_u32(value: int, word: int) -> int:
    for shift in range(0, 32, 8):
        value = _fnv_byte(value, (word >> shift) & 0xFF)
    return value


def _fnv_u64(value: int, word: int) -> int:
    for shift in range(0, 64, 8):
        value = _fnv_byte(value, (word >> shift) & 0xFF)
    return value


def _row(
    source: int,
    availability: int,
    event: int,
    *,
    routed: bool = False,
    virtual: int = 0,
) -> tuple[int, ...]:
    route = ROUTE if routed else (0, 0, 0, 0)
    return (
        source,
        availability,
        availability * 8,
        source,
        min(WRT_BYTES, source + 1),
        *route,
        virtual,
        0,
        event,
        EXPECTED_FLAGS[event],
        1 if routed else 0,
        EXPECTED_KEYS[event],
    )


def route_rows() -> list[tuple[int, ...]]:
    return [
        _row(0, 1, 1),
        _row(48, 49, 2, routed=True),
        _row(49, 49, 3, routed=True),
        _row(49, 50, 5, routed=True, virtual=1),
        _row(79, 80, 2, routed=True, virtual=1),
        _row(80, 80, 3, routed=True, virtual=1),
        _row(80, 81, 5, routed=True, virtual=2),
        _row(127, 128, 7),
    ]


def _parser_digest(rows: list[tuple[int, ...]]) -> int:
    digest = FNV_OFFSET
    for row in rows:
        for word in (row[0], row[1], row[5], row[6], row[9]):
            digest = _fnv_u64(digest, word)
        digest = _fnv_byte(digest, row[11])
        digest = _fnv_byte(digest, row[12])
    return digest


def write_route(path: Path, rows: list[tuple[int, ...]] | None = None) -> None:
    selected = route_rows() if rows is None else rows
    counts = [0] * 9
    for row in selected:
        counts[row[11] - 1] += 1
    header = bytearray(GSRT_HEADER_BYTES)
    header[:8] = b"GSRT2\0\0\0"
    struct.pack_into("<IIII", header, 8, 2, GSRT_HEADER_BYTES, GSRT_RECORD.size, 1)
    struct.pack_into("<6Q", header, 24, WRT_BYTES, WRT_BYTES, WRT_BYTES, 0, len(selected), 1)
    struct.pack_into("<9Q", header, 72, *counts)
    struct.pack_into("<Q", header, 144, counts[3])
    struct.pack_into("<Q", header, 152, 0)
    struct.pack_into("<Q", header, 160, 0)
    struct.pack_into("<Q", header, 168, _parser_digest(selected))
    struct.pack_into("<Q", header, 176, 0xABCDEF01)
    struct.pack_into("<Q", header, 184, 0x12345678)
    path.write_bytes(bytes(header) + b"".join(GSRT_RECORD.pack(*row) for row in selected))


def parse_raw(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < RAW_HEADER_BYTES or data[:8] != RAW_MAGIC:
        raise AssertionError("native raw observer header differs")
    wrt_bytes, count, terminal = struct.unpack_from("<3Q", data, 8)
    if len(data) != RAW_HEADER_BYTES + count * RAW_RECORD.size:
        raise AssertionError("native raw observer length differs")
    rows = [
        RAW_RECORD.unpack_from(data, RAW_HEADER_BYTES + index * RAW_RECORD.size)
        for index in range(count)
    ]
    return {
        "wrt_bytes": wrt_bytes,
        "record_count": count,
        "terminal_transition_hash": terminal,
        "rows": rows,
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def reference() -> dict[str, Any]:
    table = [(0, 0)] * (1 << FIXTURE_TABLE_BITS)
    context = [0] * 16
    rolling = 0
    transition = FNV_OFFSET
    rows: list[tuple[int, int, int, int]] = []
    targets = set(FIELD_TARGETS)
    for coordinate, truth in enumerate(WRT):
        if coordinate in targets:
            index = rolling & ((1 << FIXTURE_TABLE_BITS) - 1)
            tag = rolling >> 32
            old_tag, continuation = table[index]
            if continuation:
                source = continuation - 1
                active = (
                    old_tag == tag
                    and 16 <= source < coordinate
                    and coordinate - source > FIXTURE_MINIMUM_AGE
                    and source + FIXTURE_DONOR_BYTES <= coordinate
                    and WRT[source - 16 : source] == bytes(context)
                )
                if active:
                    rows.append((coordinate, source, rolling, transition))
        if coordinate < 16:
            rolling = (rolling * HASH_BASE + truth) & MASK64
            context[coordinate] = truth
            continue
        index = rolling & ((1 << FIXTURE_TABLE_BITS) - 1)
        tag = rolling >> 32
        old_tag, old_continuation = table[index]
        new = (old_tag, old_continuation)
        if old_continuation == 0 or old_tag != tag:
            new = (tag, coordinate + 1)
            table[index] = new
        for word, width in (
            (coordinate, 64),
            (rolling, 64),
            (index, 32),
            (old_tag, 32),
            (old_continuation, 32),
            (new[0], 32),
            (new[1], 32),
        ):
            transition = (
                _fnv_u64(transition, word)
                if width == 64
                else _fnv_u32(transition, word)
            )
        transition = _fnv_byte(transition, truth)
        outgoing = context.pop(0)
        context.append(truth)
        rolling = (
            rolling * HASH_BASE - outgoing * HASH_POWER_16 + truth
        ) & MASK64
    anchor_hash = FNV_OFFSET
    for tag, continuation in table:
        anchor_hash = _fnv_u32(anchor_hash, tag)
        anchor_hash = _fnv_u32(anchor_hash, continuation)
    return {
        "rows": rows,
        "terminal_rolling_hash": f"{rolling:016x}",
        "terminal_anchor_table_hash": f"{anchor_hash:016x}",
        "terminal_anchor_transition_hash": f"{transition:016x}",
        "terminal_transition_integer": transition,
    }


def _run(command: list[str], *, expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if expect_success and completed.returncode != 0:
        raise RuntimeError(f"native command failed: {completed.stderr.strip()}")
    return completed


def build_native(source: Path, binary: Path, compiler: Path) -> list[str]:
    flags = [
        "-std=c++17",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-pedantic",
        "-fno-fast-math",
        "-ffp-contract=off",
        "-march=x86-64",
        "-mtune=generic",
        "-Wl,--build-id=none",
    ]
    _run([str(compiler), *flags, str(source), "-o", str(binary)])
    return flags


def _load_abi(project_root: Path):
    path = project_root / ABI_PATH
    if sha256_path(path) != ABI_SHA256:
        raise AssertionError("measured HGS1 ABI source identity differs")
    spec = importlib.util.spec_from_file_location("_measured_hgs1_abi", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load measured HGS1 ABI")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def hgs_container_bridge(project_root: Path, root: Path, raw: dict[str, Any], source: Path) -> dict[str, Any]:
    abi = _load_abi(project_root)
    source_binding = project_root / HARM_BINDING
    _, adapter = abi.load_frozen_harm(
        project_root, abi.artifact_record(project_root, source_binding)
    )
    lifted = [
        (target + PRODUCTION_AGE_LIFT, source_coordinate, context, transition)
        for target, source_coordinate, context, transition in raw["rows"]
    ]
    observer_sha = sha256_path(source)
    config_sha = hashlib.sha256(
        json.dumps(
            {
                "fixtureOnlyCoordinateLift": PRODUCTION_AGE_LIFT,
                "sourceCoordinatesUnchanged": True,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    output = root / "lifted-fixture.hgs1"
    abi.write_hgs1(
        output,
        lifted,
        wrt_bytes=100_000_200,
        terminal_transition_hash=raw["terminal_transition_hash"],
        observer_sha256=observer_sha,
        observer_config_sha256=config_sha,
    )
    metadata = abi._hgs_metadata(output)
    seeds = {
        target: adapter.PhysicalSeed(target, source_coordinate, context, transition)
        for target, source_coordinate, context, transition in metadata.seeds
    }
    tape = adapter.PhysicalSeedTape(
        observer_sha,
        observer_sha,
        metadata.payload_sha256,
        metadata.payload_sha256,
        metadata.terminal_transition_hash,
        metadata.terminal_transition_hash,
        seeds,
    )

    class ZeroHistory:
        def __getitem__(self, key: slice) -> bytes:
            if not isinstance(key, slice) or key.start is None or key.stop is None:
                raise KeyError(key)
            return bytes(key.stop - key.start)

    donors = [adapter._physical_donor(ZeroHistory(), row[0], tape) for row in lifted]
    passed = all(donor == bytes(512) for donor in donors)
    return {
        "pass": passed,
        "fixture_only_coordinate_lift": PRODUCTION_AGE_LIFT,
        "record_count": metadata.record_count,
        "payload_sha256": metadata.payload_sha256,
        "target_union_sha256": metadata.target_union_sha256,
        "observer_sha256": observer_sha,
        "config_sha256": config_sha,
        "causal_donor_sha256": hashlib.sha256(donors[0]).hexdigest(),
        "scientific_source_coordinate_authority": False,
    }


def negative_controls(binary: Path, base: Path, root: Path) -> dict[str, str]:
    root.mkdir()
    rejected: dict[str, str] = {}

    def expect(label: str, mutation: Callable[[Path, Path], None]) -> None:
        case = root / label
        case.mkdir()
        wrt = case / "truth.wrt"
        route = case / "route.gsrt2"
        shutil.copyfile(base / "truth.wrt", wrt)
        shutil.copyfile(base / "route-a.gsrt2", route)
        mutation(wrt, route)
        raw = case / "unexpected.raw"
        summary = case / "unexpected.json"
        completed = _run(
            [str(binary), "--fixture", str(wrt), str(route), str(raw), str(summary)],
            expect_success=False,
        )
        if completed.returncode == 0 or raw.exists() or summary.exists():
            raise AssertionError(f"negative control escaped or emitted output: {label}")
        rejected[label] = completed.stderr.strip()

    def mutate(path: Path, offset: int, payload: bytes) -> None:
        data = bytearray(path.read_bytes())
        data[offset : offset + len(payload)] = payload
        path.write_bytes(data)

    def wrt_symlink(wrt: Path, _route: Path) -> None:
        target = wrt.with_name("truth-target.wrt")
        wrt.rename(target)
        wrt.symlink_to(target.name)

    expect("wrt_symlink", wrt_symlink)
    expect("route_magic", lambda _wrt, route: mutate(route, 0, b"BROKEN!!"))
    expect("route_event_count", lambda _wrt, route: mutate(route, 72 + 8, struct.pack("<Q", 3)))

    def order_regression(_wrt: Path, route: Path) -> None:
        data = bytearray(route.read_bytes())
        first = GSRT_HEADER_BYTES + 2 * GSRT_RECORD.size
        second = GSRT_HEADER_BYTES + 3 * GSRT_RECORD.size
        a = bytes(data[first : first + GSRT_RECORD.size])
        b = bytes(data[second : second + GSRT_RECORD.size])
        data[first : first + GSRT_RECORD.size] = b
        data[second : second + GSRT_RECORD.size] = a
        route.write_bytes(data)

    expect("route_order", order_regression)
    expect("route_wrt_population", lambda _wrt, route: mutate(route, 32, struct.pack("<Q", WRT_BYTES + 1)))
    expect("pretruth_violation", lambda _wrt, route: mutate(route, 160, struct.pack("<Q", 1)))

    def predictive_timing(_wrt: Path, route: Path) -> None:
        offset = GSRT_HEADER_BYTES + 2 * GSRT_RECORD.size
        mutate(route, offset + 8, struct.pack("<Q", 50))
        mutate(route, offset + 16, struct.pack("<Q", 400))

    expect("predictive_timing", predictive_timing)

    def zero_route(_wrt: Path, route: Path) -> None:
        offset = GSRT_HEADER_BYTES + GSRT_RECORD.size
        mutate(route, offset + 40, bytes(32))

    expect("zero_route_identity", zero_route)
    return rejected


def run_fixture(project_root: Path, root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve().parent / "horizon-field-entry-observer.cpp"
    compiler = Path("/usr/bin/x86_64-linux-gnu-g++-15")
    horizon_source = project_root / HORIZON_SOURCE
    if sha256_path(horizon_source) != HORIZON_SOURCE_SHA256:
        raise AssertionError("frozen HORIZON-A source identity differs")

    binary = root / "observer"
    flags = build_native(source, binary, compiler)
    inputs = root / "inputs"
    inputs.mkdir()
    wrt = inputs / "truth.wrt"
    route_a = inputs / "route-a.gsrt2"
    route_b = inputs / "route-b.gsrt2"
    wrt.write_bytes(WRT)
    write_route(route_a)
    shutil.copyfile(route_a, route_b)

    raw_a = root / "observer-a.raw"
    raw_b = root / "observer-b.raw"
    summary_a = root / "summary-a.json"
    summary_b = root / "summary-b.json"
    _run([str(binary), "--fixture", str(wrt), str(route_a), str(raw_a), str(summary_a)])
    _run([str(binary), "--fixture", str(wrt), str(route_b), str(raw_b), str(summary_b)])
    first = parse_raw(raw_a)
    second = parse_raw(raw_b)
    values_a = json.loads(summary_a.read_text())
    values_b = json.loads(summary_b.read_text())
    repeated = raw_a.read_bytes() == raw_b.read_bytes() and values_a == values_b

    expected = reference()
    native_reference = (
        first["rows"] == expected["rows"]
        and values_a["terminal_rolling_hash"] == expected["terminal_rolling_hash"]
        and values_a["terminal_anchor_table_hash"] == expected["terminal_anchor_table_hash"]
        and values_a["terminal_anchor_transition_hash"]
        == expected["terminal_anchor_transition_hash"]
        and first["terminal_transition_hash"] == expected["terminal_transition_integer"]
    )
    pretruth = all(
        native[3] == reference_row[3]
        for native, reference_row in zip(first["rows"], expected["rows"], strict=True)
    )
    field_entry = (
        [row[0] for row in first["rows"]] == list(FIELD_TARGETS)
        and values_a["field_entry_events"] == 2
        and values_a["unique_field_entry_targets"] == 2
        and values_a["emitted_seeds"] == 2
        and values_a["active_lookups"] == 2
    )

    production_path = root / "production-config.json"
    _run([str(binary), "--describe-production", str(production_path)])
    production = json.loads(production_path.read_text())
    production_expected = {
        "wrt_bytes": 647798592,
        "key_bytes": 16,
        "hash_base": "9e3779b185ebca87",
        "hash_base_power_16": "6fe6ef9fbd3b9581",
        "table_bits": 24,
        "table_entries": 16777216,
        "record_bytes": 8,
        "minimum_age_bytes": 100000000,
        "donor_bytes": 512,
        "expected_terminal_rolling_hash": "01345eea197318a2",
        "expected_terminal_anchor_table_hash": "199185a886ba1064",
        "expected_terminal_anchor_transition_hash": "46e3b81f2877dde1",
    }
    production_config_pass = all(production.get(key) == value for key, value in production_expected.items())
    hgs = hgs_container_bridge(project_root, root, first, source)
    rejected = negative_controls(binary, inputs, root / "negative")
    input_paths = [wrt.resolve(), route_a.resolve(), route_b.resolve(), source.resolve()]

    return {
        "compile_flags": flags,
        "compiler_sha256": sha256_path(compiler),
        "source_sha256": sha256_path(source),
        "frozen_horizon_source_sha256": HORIZON_SOURCE_SHA256,
        "native_reference_identity_pass": native_reference,
        "repeat_identity_pass": repeated and first == second,
        "field_entry_selection_pass": field_entry,
        "pretruth_transition_pass": pretruth,
        "hgs_container_bridge": hgs,
        "production_config": production,
        "production_config_closure_pass": production_config_pass,
        "emitted_seed_count": first["record_count"],
        "native_rows": [list(row) for row in first["rows"]],
        "reference": expected,
        "native_summary": values_a,
        "native_raw_sha256": first["sha256"],
        "negative_control_reject_count": len(rejected),
        "negative_control_rejections": rejected,
        "corpus_access_count": 0,
        "active_trace_access_count": 0,
        "opened_fixture_inputs": [str(path) for path in input_paths],
        "archive_authority": False,
        "retained_parent_gain_authority": False,
        "corpus_execution_authority": False,
        "objective_credit_bytes": 0,
    }
