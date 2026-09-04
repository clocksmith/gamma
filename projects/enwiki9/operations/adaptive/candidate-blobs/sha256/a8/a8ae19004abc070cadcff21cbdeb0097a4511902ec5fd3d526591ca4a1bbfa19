#!/usr/bin/env python3
"""Generated source-only fixtures for the HARM sparse-input ABI."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import struct
from typing import Any, Callable

import abi


WRT = b"MabQMabQ"
PARENT_COORDINATES = (1, 2, 3, 5, 6, 7)
PARENT_ROW = tuple([32768] * 8)
PARENT_OBSERVER_SHA = hashlib.sha256(b"fixture-parent-observer").hexdigest()
PARENT_STATE_BEGIN_SHA = hashlib.sha256(b"fixture-parent-state-begin").hexdigest()
PARENT_STATE_END_SHA = hashlib.sha256(b"fixture-parent-state-end").hexdigest()
FRONTEND_STATE_BEGIN_SHA = hashlib.sha256(b"fixture-frontend-begin").hexdigest()
FRONTEND_STATE_END_SHA = hashlib.sha256(b"fixture-frontend-end").hexdigest()


def _u64_label(label: bytes) -> int:
    return int.from_bytes(hashlib.sha256(label).digest()[:8], "little")


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _route_rows(adapter: Any) -> list[Any]:
    route = (101, 202, 303, 404)

    def row(source: int, availability: int, virtual: int, event: int):
        return adapter.TapeRow(
            source=source,
            availability=availability,
            first_bit=availability * 8,
            raw_before=source,
            raw_after=min(len(WRT), source + 1),
            route_lo=route[0],
            route_hi=route[1],
            witness_lo=route[2],
            witness_hi=route[3],
            virtual_ordinal=virtual,
            field_ordinal=0,
            event_type=event,
            flags=adapter.EXPECTED_FLAGS[event],
            depth=1,
            key_identity=adapter.EXPECTED_KEY_IDENTITY[event],
        )

    return [
        row(0, 1, 0, adapter.EVENT_EXPLICIT_FIELD_ENTRY),
        row(1, 1, 0, adapter.EVENT_FIELD_VALUE_BYTE),
        row(2, 2, 1, adapter.EVENT_FIELD_VALUE_BYTE),
        row(3, 3, 2, adapter.EVENT_FIELD_VALUE_BYTE),
        row(3, 4, 2, adapter.EVENT_FIELD_EXIT),
        row(4, 5, 2, adapter.EVENT_EXPLICIT_FIELD_ENTRY),
        row(5, 5, 2, adapter.EVENT_FIELD_VALUE_BYTE),
        row(6, 6, 3, adapter.EVENT_FIELD_VALUE_BYTE),
        row(7, 7, 4, adapter.EVENT_FIELD_VALUE_BYTE),
        row(7, 8, 4, adapter.EVENT_FIELD_EXIT),
    ]


def _write_gsrt2(path: Path, adapter: Any) -> dict[str, object]:
    rows = _route_rows(adapter)
    counts = [0] * 9
    for row in rows:
        counts[row.event_type - 1] += 1
    header = bytearray(adapter.TAPE_HEADER_BYTES)
    header[:8] = b"GSRT2\0\0\0"
    struct.pack_into(
        "<IIII", header, 8, 2, adapter.TAPE_HEADER_BYTES,
        adapter.TAPE_RECORD_BYTES, 1,
    )
    values = {
        24: len(WRT),
        32: len(WRT),
        40: len(WRT),
        48: 0,
        56: len(rows),
        64: 1,
        144: 0,
        152: 0,
        160: 0,
        168: _u64_label(b"fixture-parser"),
        176: _u64_label(b"fixture-raw"),
        184: _u64_label(b"fixture-wrt"),
    }
    for index, count in enumerate(counts):
        values[72 + 8 * index] = count
    for offset, value in values.items():
        struct.pack_into("<Q", header, offset, value)
    body = b"".join(
        adapter.TAPE_RECORD.pack(*row.__dict__.values()) for row in rows
    )
    path.write_bytes(bytes(header) + body)
    return {
        "fixtureFlags": 1,
        "storeBytes": len(WRT),
        "wrtBytes": len(WRT),
        "rawBytes": len(WRT),
        "dictionaryBytes": 0,
        "recordCount": len(rows),
        "descriptorCount": 1,
        "eventCounts": counts,
        "deferredUpdates": 0,
        "positionalPredictiveEvents": 0,
        "parserDigest": values[168],
        "rawDigest": values[176],
        "wrtDigest": values[184],
    }


def _replace_parent_rows(
    project_root: Path,
    manifest: dict[str, Any],
    rows: list[tuple[int, tuple[int, ...]]],
    *,
    validate: bool = True,
) -> None:
    a_path = project_root / manifest["parentTape"]["a"]["path"]
    b_path = project_root / manifest["parentTape"]["b"]["path"]
    metadata = abi.write_hsp1(
        a_path,
        rows,
        wrt_bytes=len(WRT),
        replay_begin=0,
        replay_end=len(WRT),
        parent_observer_sha256=PARENT_OBSERVER_SHA,
        parent_state_begin_sha256=PARENT_STATE_BEGIN_SHA,
        parent_state_end_sha256=PARENT_STATE_END_SHA,
        validate=validate,
    )
    shutil.copyfile(a_path, b_path)
    manifest["parentTape"]["a"] = abi.artifact_record(project_root, a_path)
    manifest["parentTape"]["b"] = abi.artifact_record(project_root, b_path)
    manifest["parentTape"]["binding"] = metadata.manifest_binding()


def build_fixture(project_root: Path, root: Path, adapter: Any) -> Path:
    root.mkdir(parents=True, exist_ok=False)
    wrt_path = root / "fixture.wrt"
    wrt_path.write_bytes(WRT)
    mapping_path = root / "raw-wrt-map.json"
    _write_json(
        mapping_path,
        {
            "schema": "gamma.enwiki9.generated-identity-coordinate-map.v1",
            "rawHalfOpen": [0, len(WRT)],
            "wrtHalfOpen": [0, len(WRT)],
            "coderBitHalfOpen": [0, len(WRT) * 8],
            "fixtureOnly": True,
        },
    )

    route_a = root / "route-a.gsrt2"
    route_b = root / "route-b.gsrt2"
    route_binding = _write_gsrt2(route_a, adapter)
    shutil.copyfile(route_a, route_b)

    parent_a = root / "parent-a.hsp1"
    parent_b = root / "parent-b.hsp1"
    parent_metadata = abi.write_hsp1(
        parent_a,
        [(coordinate, PARENT_ROW) for coordinate in PARENT_COORDINATES],
        wrt_bytes=len(WRT),
        replay_begin=0,
        replay_end=len(WRT),
        parent_observer_sha256=PARENT_OBSERVER_SHA,
        parent_state_begin_sha256=PARENT_STATE_BEGIN_SHA,
        parent_state_end_sha256=PARENT_STATE_END_SHA,
    )
    shutil.copyfile(parent_a, parent_b)

    source_binding = project_root / abi.HARM_SOURCE_BINDING_PATH
    manifest = {
        "schema": "gamma.enwiki9.harm-delta-sparse-input.v1",
        "candidateId": abi.CANDIDATE_ID,
        "harmSourceBinding": abi.artifact_record(project_root, source_binding),
        "scope": {
            "scopeId": "fixture",
            "rawPopulationBytes": len(WRT),
            "wrtPopulationBytes": len(WRT),
            "replayWrtBegin": 0,
            "replayWrtEnd": len(WRT),
            "measureRawBegin": 0,
            "measureRawEnd": len(WRT),
            "measureWrtBegin": 0,
            "measureWrtEnd": len(WRT),
            "coderBitBegin": 0,
            "coderBitEnd": len(WRT) * 8,
            "frontendStateBeginSha256": FRONTEND_STATE_BEGIN_SHA,
            "frontendStateEndSha256": FRONTEND_STATE_END_SHA,
            "parentStateBeginSha256": PARENT_STATE_BEGIN_SHA,
            "parentStateEndSha256": PARENT_STATE_END_SHA,
        },
        "wrt": abi.artifact_record(project_root, wrt_path),
        "rawToWrtMap": abi.artifact_record(project_root, mapping_path),
        "routeTape": {
            "a": abi.artifact_record(project_root, route_a),
            "b": abi.artifact_record(project_root, route_b),
            "binding": route_binding,
        },
        "parentTape": {
            "a": abi.artifact_record(project_root, parent_a),
            "b": abi.artifact_record(project_root, parent_b),
            "binding": parent_metadata.manifest_binding(),
        },
        "physicalSeedTape": None,
    }
    manifest_path = root / "manifest.json"
    _write_json(manifest_path, manifest)
    return manifest_path


def verify_physical_binding(
    project_root: Path, root: Path, adapter: Any
) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=False)
    target = 100_000_700
    source = 100
    context = b"0123456789abcdef"
    donor = bytes(range(256)) * 2
    transition_hash = 0x1020304050607080
    observer_sha = hashlib.sha256(b"fixture-physical-observer").hexdigest()
    config_sha = hashlib.sha256(b"fixture-physical-config").hexdigest()
    rows = [
        (
            target,
            source,
            adapter.horizon_context_hash(context),
            transition_hash,
        )
    ]
    path_a = root / "physical-a.hgs1"
    path_b = root / "physical-b.hgs1"
    metadata = abi.write_hgs1(
        path_a,
        rows,
        wrt_bytes=100_000_800,
        terminal_transition_hash=transition_hash,
        observer_sha256=observer_sha,
        observer_config_sha256=config_sha,
    )
    shutil.copyfile(path_a, path_b)
    value = {
        "a": abi.artifact_record(project_root, path_a),
        "b": abi.artifact_record(project_root, path_b),
        "binding": metadata.manifest_binding(),
    }
    tape, loaded = abi.load_physical_pair(project_root, value, adapter)

    class SparseHistory:
        def __getitem__(self, key):
            spans = {
                (target - 16, target): context,
                (source - 16, source): context,
                (source, source + 512): donor,
            }
            return spans[(key.start, key.stop)]

    observed = adapter._physical_donor(SparseHistory(), target, tape)
    if observed != donor or loaded != metadata:
        raise AssertionError("valid HGS1 did not reproduce its causal donor")
    return {
        "record_count": metadata.record_count,
        "payload_sha256": metadata.payload_sha256,
        "observer_sha256": metadata.observer_sha256,
        "target_union_sha256": metadata.target_union_sha256,
        "causal_donor_sha256": hashlib.sha256(observed).hexdigest(),
    }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("fixture manifest is not an object")
    return value


def _save_manifest(path: Path, value: dict[str, Any]) -> None:
    _write_json(path, value)


def run_negative_controls(
    project_root: Path, root: Path, adapter: Any
) -> dict[str, str]:
    rejected: dict[str, str] = {}

    def expect(label: str, mutation: Callable[[Path, dict[str, Any]], None]) -> None:
        case_root = root / label
        manifest_path = build_fixture(project_root, case_root, adapter)
        manifest = _load_json(manifest_path)
        mutation(manifest_path, manifest)
        try:
            abi.execute_manifest(manifest_path, project_root)
        except ValueError as error:
            rejected[label] = str(error)
        else:
            raise AssertionError(f"negative control escaped: {label}")

    def parent_repeat_drift(path: Path, manifest: dict[str, Any]) -> None:
        target = project_root / manifest["parentTape"]["b"]["path"]
        payload = bytearray(target.read_bytes())
        payload[-1] ^= 1
        target.write_bytes(payload)
        manifest["parentTape"]["b"] = abi.artifact_record(project_root, target)
        _save_manifest(path, manifest)

    expect("parent-repeat-drift", parent_repeat_drift)

    def missing_parent(path: Path, manifest: dict[str, Any]) -> None:
        rows = [
            (coordinate, PARENT_ROW)
            for coordinate in PARENT_COORDINATES
            if coordinate != 2
        ]
        _replace_parent_rows(project_root, manifest, rows)
        _save_manifest(path, manifest)

    expect("missing-parent-coordinate", missing_parent)

    def extra_parent(path: Path, manifest: dict[str, Any]) -> None:
        coordinates = sorted((*PARENT_COORDINATES, 4))
        _replace_parent_rows(
            project_root, manifest,
            [(coordinate, PARENT_ROW) for coordinate in coordinates],
        )
        _save_manifest(path, manifest)

    expect("extra-parent-coordinate", extra_parent)

    def duplicate_parent(path: Path, manifest: dict[str, Any]) -> None:
        coordinates = [1, 2, 2, 3, 5, 6, 7]
        _replace_parent_rows(
            project_root, manifest,
            [(coordinate, PARENT_ROW) for coordinate in coordinates],
            validate=False,
        )
        _save_manifest(path, manifest)

    expect("duplicate-parent-coordinate", duplicate_parent)

    def zero_probability(path: Path, manifest: dict[str, Any]) -> None:
        bad = (0, *PARENT_ROW[1:])
        rows = [(coordinate, bad if coordinate == 3 else PARENT_ROW)
                for coordinate in PARENT_COORDINATES]
        _replace_parent_rows(project_root, manifest, rows, validate=False)
        _save_manifest(path, manifest)

    expect("zero-parent-probability", zero_probability)

    def parent_payload_digest_drift(path: Path, manifest: dict[str, Any]) -> None:
        path_a = project_root / manifest["parentTape"]["a"]["path"]
        path_b = project_root / manifest["parentTape"]["b"]["path"]
        payload = bytearray(path_a.read_bytes())
        payload_offset = abi.HSP1_HEADER.size - 5 * 32
        payload[payload_offset : payload_offset + 32] = bytes(32)
        path_a.write_bytes(payload)
        shutil.copyfile(path_a, path_b)
        manifest["parentTape"]["a"] = abi.artifact_record(project_root, path_a)
        manifest["parentTape"]["b"] = abi.artifact_record(project_root, path_b)
        _save_manifest(path, manifest)

    expect("parent-payload-digest-drift", parent_payload_digest_drift)

    def route_repeat_drift(path: Path, manifest: dict[str, Any]) -> None:
        target = project_root / manifest["routeTape"]["b"]["path"]
        payload = bytearray(target.read_bytes())
        payload[-1] ^= 1
        target.write_bytes(payload)
        manifest["routeTape"]["b"] = abi.artifact_record(project_root, target)
        _save_manifest(path, manifest)

    expect("route-repeat-drift", route_repeat_drift)

    def source_binding_drift(path: Path, manifest: dict[str, Any]) -> None:
        manifest["harmSourceBinding"]["sha256"] = abi.SHA256_ZERO
        _save_manifest(path, manifest)

    expect("source-binding-drift", source_binding_drift)

    physical_root = root / "physical-observer-repeat-drift"
    physical_root.mkdir(parents=True, exist_ok=False)
    target = 100_000_700
    source = 100
    context_hash = adapter.horizon_context_hash(b"0123456789abcdef")
    transition = 77
    observer_a = hashlib.sha256(b"physical-a").hexdigest()
    observer_b = hashlib.sha256(b"physical-b").hexdigest()
    config = hashlib.sha256(b"physical-config").hexdigest()
    path_a = physical_root / "a.hgs1"
    path_b = physical_root / "b.hgs1"
    metadata = abi.write_hgs1(
        path_a,
        [(target, source, context_hash, transition)],
        wrt_bytes=100_000_800,
        terminal_transition_hash=transition,
        observer_sha256=observer_a,
        observer_config_sha256=config,
    )
    abi.write_hgs1(
        path_b,
        [(target, source, context_hash, transition)],
        wrt_bytes=100_000_800,
        terminal_transition_hash=transition,
        observer_sha256=observer_b,
        observer_config_sha256=config,
    )
    physical_value = {
        "a": abi.artifact_record(project_root, path_a),
        "b": abi.artifact_record(project_root, path_b),
        "binding": metadata.manifest_binding(),
    }
    try:
        abi.load_physical_pair(project_root, physical_value, adapter)
    except ValueError as error:
        rejected["physical-observer-repeat-drift"] = str(error)
    else:
        raise AssertionError("negative control escaped: physical observer drift")

    def scope_drift(path: Path, manifest: dict[str, Any]) -> None:
        manifest["scope"]["coderBitEnd"] += 1
        _save_manifest(path, manifest)

    expect("scope-arithmetic-drift", scope_drift)
    return rejected


def run_fixture(project_root: Path, work_root: Path) -> dict[str, object]:
    source_reference = abi.artifact_record(
        project_root, project_root / abi.HARM_SOURCE_BINDING_PATH
    )
    _, adapter = abi.load_frozen_harm(project_root, source_reference)
    valid_manifest = build_fixture(project_root, work_root / "valid", adapter)
    replay = abi.execute_manifest(valid_manifest, project_root)
    physical = verify_physical_binding(
        project_root, work_root / "physical-valid", adapter
    )
    negative = run_negative_controls(
        project_root, work_root / "negative", adapter
    )
    run = replay["run_a"]
    return {
        "schema": "gamma.enwiki9.harm-delta-sparse-input-fixture.v1",
        "candidate_id": abi.CANDIDATE_ID,
        "input_manifest_sha256": replay["manifest_sha256"],
        "repeat_identity_pass": replay["repeat_identity_pass"],
        "sparse_parent_record_count": run["sparse_parent_records_consumed"],
        "active_bytes": run["active_bytes"],
        "e_awake_bytes": run["arm_awake_bytes"]["E"],
        "g_awake_bytes": run["arm_awake_bytes"]["G"],
        "p_k_probability_identity_pass": run["p_k_probability_identity_pass"],
        "physical_g_comparator_admissible": run[
            "physical_g_comparator_admissible"
        ],
        "probability_sha256": run["probability_sha256"],
        "terminal_state_sha256": run["terminal_state_sha256"],
        "physical_seed_binding": physical,
        "negative_controls": negative,
        "negative_control_reject_count": len(negative),
        "corpus_access_count": 0,
        "active_horizon_scientific_output_access_count": 0,
        "archive_authority": False,
        "objective_credit_bytes": 0,
    }
