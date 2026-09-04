#!/usr/bin/env python3
"""Streaming sparse-input boundary for the frozen HARM-Delta shadow.

This module owns no compression mechanism.  It validates prospectively bound
WRT, GSRT2, HSP1, HGS1, and coordinate-state evidence, then feeds the exact
frozen callback adapter one parent row at a time.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
import mmap
import os
from pathlib import Path, PurePosixPath
import struct
import sys
from typing import Any, Iterator


CANDIDATE_ID = "harm_delta_sparse_input_abi_q0_v1"
HARM_SOURCE_BINDING_PATH = (
    "programs/harm_route_edit_residual_shadow_q0_v1/source-binding.json"
)
HARM_SOURCE_BINDING_SHA256 = (
    "e20bf8d95cd37ea767f0ebe1b8d9c8efa0d8e9546852cf93439ab5e9e8df24ba"
)
HARM_CORE_PATH = "programs/harm_route_edit_residual_shadow_q0_v1/core.py"
HARM_ADAPTER_PATH = (
    "programs/harm_route_edit_residual_shadow_q0_v1/callback_adapter.py"
)

HSP1_MAGIC = b"HSP1\0\0\0\0"
HSP1_VERSION = 1
HSP1_HEADER_BYTES = 256
HSP1_RECORD = struct.Struct("<Q8H")
HSP1_HEADER = struct.Struct("<8sIIII6Q32s32s32s32s32s")

HGS1_MAGIC = b"HGS1\0\0\0\0"
HGS1_VERSION = 1
HGS1_HEADER_BYTES = 192
HGS1_RECORD = struct.Struct("<4Q")
HGS1_HEADER = struct.Struct("<8sIIII3Q32s32s32s32s")

SHA256_ZERO = "0" * 64
UINT64_MAX = (1 << 64) - 1


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _require_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} is not an object")
    return value


def _require_keys(value: dict[str, Any], keys: set[str], label: str) -> None:
    observed = set(value)
    if observed != keys:
        missing = sorted(keys - observed)
        extra = sorted(observed - keys)
        raise ValueError(
            f"{label} fields differ; missing={missing!r} extra={extra!r}"
        )


def _require_sha256(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} is not a lowercase SHA-256")
    return value


def artifact_record(project_root: Path, path: Path) -> dict[str, object]:
    path = path.resolve()
    root = project_root.resolve()
    if path != root and root not in path.parents:
        raise ValueError("artifact is outside the project root")
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_path(path),
    }


def resolve_artifact(
    project_root: Path, value: object, label: str
) -> Path:
    record = _require_object(value, label)
    _require_keys(record, {"path", "bytes", "sha256"}, label)
    path_text = record["path"]
    size = record["bytes"]
    digest = _require_sha256(record["sha256"], f"{label} digest")
    if (
        not isinstance(path_text, str)
        or not path_text
        or not isinstance(size, int)
        or isinstance(size, bool)
        or size < 0
    ):
        raise ValueError(f"{label} has malformed path or byte count")
    relative = PurePosixPath(path_text)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{label} path is not project-relative")
    root = project_root.resolve()
    lexical = root.joinpath(*relative.parts)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"{label} path traverses a symlink")
    path = lexical.resolve()
    if path == root or root not in path.parents or not path.is_file():
        raise ValueError(f"{label} is not a regular project file")
    if path.stat().st_size != size or sha256_path(path) != digest:
        raise ValueError(f"{label} content binding mismatch")
    return path


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_frozen_harm(project_root: Path, source_reference: object):
    source_path = resolve_artifact(
        project_root, source_reference, "HARM source binding"
    )
    if (
        source_path.relative_to(project_root.resolve()).as_posix()
        != HARM_SOURCE_BINDING_PATH
        or sha256_path(source_path) != HARM_SOURCE_BINDING_SHA256
    ):
        raise ValueError("HARM source-binding identity differs from frozen v1")
    binding = _require_object(
        json.loads(source_path.read_text()), "HARM source binding payload"
    )
    if (
        binding.get("schema") != "gamma.enwiki9.source-binding.v1"
        or binding.get("candidate_id")
        != "harm_route_edit_residual_shadow_q0_v1"
        or binding.get("archive_authority") is not False
        or binding.get("score_credit_bytes") != 0
        or binding.get("retained_parent_execution_authority") is not False
    ):
        raise ValueError("HARM source-binding authority differs")
    artifacts = binding.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("HARM source-binding artifact list is empty")
    observed_paths: set[str] = set()
    for index, artifact in enumerate(artifacts):
        record = _require_object(artifact, f"HARM artifact {index}")
        _require_keys(record, {"path", "bytes", "sha256"}, f"HARM artifact {index}")
        path = resolve_artifact(project_root, record, f"HARM artifact {index}")
        relative = path.relative_to(project_root.resolve()).as_posix()
        if relative in observed_paths:
            raise ValueError("HARM source-binding contains a duplicate path")
        observed_paths.add(relative)
    if HARM_CORE_PATH not in observed_paths or HARM_ADAPTER_PATH not in observed_paths:
        raise ValueError("HARM source binding omits executable core or adapter")

    core = _load_module(
        "_harm_delta_sparse_abi_core", project_root / HARM_CORE_PATH
    )
    previous_core = sys.modules.get("core")
    sys.modules["core"] = core
    try:
        adapter = _load_module(
            "_harm_delta_sparse_abi_adapter", project_root / HARM_ADAPTER_PATH
        )
    finally:
        if previous_core is None:
            sys.modules.pop("core", None)
        else:
            sys.modules["core"] = previous_core
    return core, adapter


@dataclass(frozen=True)
class HspMetadata:
    wrt_bytes: int
    replay_begin: int
    replay_end: int
    record_count: int
    first_coordinate: int
    last_coordinate: int
    payload_sha256: str
    coordinate_union_sha256: str
    parent_observer_sha256: str
    parent_state_begin_sha256: str
    parent_state_end_sha256: str

    def manifest_binding(self) -> dict[str, object]:
        return {
            "wrtBytes": self.wrt_bytes,
            "replayWrtBegin": self.replay_begin,
            "replayWrtEnd": self.replay_end,
            "recordCount": self.record_count,
            "firstCoordinate": self.first_coordinate,
            "lastCoordinate": self.last_coordinate,
            "payloadSha256": self.payload_sha256,
            "coordinateUnionSha256": self.coordinate_union_sha256,
            "parentObserverSha256": self.parent_observer_sha256,
            "parentStateBeginSha256": self.parent_state_begin_sha256,
            "parentStateEndSha256": self.parent_state_end_sha256,
        }


HSP_BINDING_KEYS = {
    "wrtBytes",
    "replayWrtBegin",
    "replayWrtEnd",
    "recordCount",
    "firstCoordinate",
    "lastCoordinate",
    "payloadSha256",
    "coordinateUnionSha256",
    "parentObserverSha256",
    "parentStateBeginSha256",
    "parentStateEndSha256",
}


def _hsp_metadata(path: Path) -> HspMetadata:
    with path.open("rb") as stream:
        header = stream.read(HSP1_HEADER_BYTES)
        if len(header) != HSP1_HEADER_BYTES:
            raise ValueError("short HSP1 header")
        fields = HSP1_HEADER.unpack(header[: HSP1_HEADER.size])
        (
            magic,
            version,
            header_bytes,
            record_bytes,
            probability_scale,
            wrt_bytes,
            replay_begin,
            replay_end,
            record_count,
            first_coordinate,
            last_coordinate,
            payload_sha,
            coordinate_sha,
            observer_sha,
            state_begin_sha,
            state_end_sha,
        ) = fields
        if (
            magic != HSP1_MAGIC
            or version != HSP1_VERSION
            or header_bytes != HSP1_HEADER_BYTES
            or record_bytes != HSP1_RECORD.size
            or probability_scale != 65536
            or any(header[HSP1_HEADER.size :])
        ):
            raise ValueError("invalid HSP1 header geometry")
        if not 0 <= replay_begin < replay_end <= wrt_bytes:
            raise ValueError("invalid HSP1 replay interval")
        if record_count <= 0:
            raise ValueError("HSP1 population is empty")
        if path.stat().st_size != HSP1_HEADER_BYTES + record_count * HSP1_RECORD.size:
            raise ValueError("HSP1 file length differs from record count")
        payload_digest = hashlib.sha256()
        coordinate_digest = hashlib.sha256()
        previous: int | None = None
        observed_first: int | None = None
        observed_last: int | None = None
        for _ in range(record_count):
            payload = stream.read(HSP1_RECORD.size)
            if len(payload) != HSP1_RECORD.size:
                raise ValueError("short HSP1 record")
            payload_digest.update(payload)
            coordinate, *probabilities = HSP1_RECORD.unpack(payload)
            coordinate_digest.update(struct.pack("<Q", coordinate))
            if not replay_begin <= coordinate < replay_end:
                raise ValueError("HSP1 coordinate is outside replay interval")
            if previous is not None and coordinate <= previous:
                raise ValueError("HSP1 coordinates are not strictly increasing")
            if any(not 0 < probability < 65536 for probability in probabilities):
                raise ValueError("HSP1 probability is outside Q16 interior")
            previous = coordinate
            observed_first = coordinate if observed_first is None else observed_first
            observed_last = coordinate
        if stream.read(1):
            raise ValueError("trailing HSP1 bytes")
    if (
        payload_digest.digest() != payload_sha
        or coordinate_digest.digest() != coordinate_sha
        or observed_first != first_coordinate
        or observed_last != last_coordinate
    ):
        raise ValueError("HSP1 header binding differs from record payload")
    if any(
        value == bytes(32)
        for value in (observer_sha, state_begin_sha, state_end_sha)
    ):
        raise ValueError("HSP1 observer or parent-state binding is empty")
    return HspMetadata(
        wrt_bytes=wrt_bytes,
        replay_begin=replay_begin,
        replay_end=replay_end,
        record_count=record_count,
        first_coordinate=first_coordinate,
        last_coordinate=last_coordinate,
        payload_sha256=payload_sha.hex(),
        coordinate_union_sha256=coordinate_sha.hex(),
        parent_observer_sha256=observer_sha.hex(),
        parent_state_begin_sha256=state_begin_sha.hex(),
        parent_state_end_sha256=state_end_sha.hex(),
    )


class SparseParentProvider:
    """Monotonic exact-coverage reader for one HSP1 stream."""

    def __init__(self, path: Path, expected_binding: object):
        binding = _require_object(expected_binding, "HSP1 binding")
        _require_keys(binding, HSP_BINDING_KEYS, "HSP1 binding")
        self.metadata = _hsp_metadata(path)
        if self.metadata.manifest_binding() != binding:
            raise ValueError("HSP1 manifest/header binding mismatch")
        self.path = path
        self.stream = path.open("rb")
        self.stream.seek(HSP1_HEADER_BYTES)
        self.consumed = 0
        self._next = self._read_next()

    def _read_next(self) -> tuple[int, tuple[int, ...]] | None:
        if self.consumed >= self.metadata.record_count:
            return None
        payload = self.stream.read(HSP1_RECORD.size)
        if len(payload) != HSP1_RECORD.size:
            raise ValueError("short HSP1 record during replay")
        coordinate, *probabilities = HSP1_RECORD.unpack(payload)
        return coordinate, tuple(probabilities)

    def __call__(self, coordinate: int) -> tuple[int, ...]:
        if self._next is None:
            raise ValueError(f"missing HSP1 parent row at coordinate {coordinate}")
        observed, probabilities = self._next
        if observed < coordinate:
            raise ValueError(
                f"unused HSP1 parent row at coordinate {observed} before {coordinate}"
            )
        if observed > coordinate:
            raise ValueError(f"missing HSP1 parent row at coordinate {coordinate}")
        self.consumed += 1
        self._next = self._read_next()
        return probabilities

    def finish(self) -> None:
        if self._next is not None:
            raise ValueError(
                f"unused terminal HSP1 parent row at coordinate {self._next[0]}"
            )
        if self.consumed != self.metadata.record_count:
            raise ValueError("HSP1 consumed-record count mismatch")
        if self.stream.read(1):
            raise ValueError("trailing HSP1 replay bytes")

    def close(self) -> None:
        self.stream.close()


@dataclass(frozen=True)
class HgsMetadata:
    wrt_bytes: int
    record_count: int
    terminal_transition_hash: int
    payload_sha256: str
    observer_sha256: str
    observer_config_sha256: str
    target_union_sha256: str
    seeds: tuple[tuple[int, int, int, int], ...]

    def manifest_binding(self) -> dict[str, object]:
        return {
            "wrtBytes": self.wrt_bytes,
            "recordCount": self.record_count,
            "terminalAnchorTransitionHash": self.terminal_transition_hash,
            "payloadSha256": self.payload_sha256,
            "observerSha256": self.observer_sha256,
            "observerConfigSha256": self.observer_config_sha256,
            "targetUnionSha256": self.target_union_sha256,
        }


HGS_BINDING_KEYS = {
    "wrtBytes",
    "recordCount",
    "terminalAnchorTransitionHash",
    "payloadSha256",
    "observerSha256",
    "observerConfigSha256",
    "targetUnionSha256",
}


def _hgs_metadata(path: Path) -> HgsMetadata:
    with path.open("rb") as stream:
        header = stream.read(HGS1_HEADER_BYTES)
        if len(header) != HGS1_HEADER_BYTES:
            raise ValueError("short HGS1 header")
        (
            magic,
            version,
            header_bytes,
            record_bytes,
            flags,
            wrt_bytes,
            record_count,
            terminal_transition_hash,
            payload_sha,
            observer_sha,
            config_sha,
            target_sha,
        ) = HGS1_HEADER.unpack(header[: HGS1_HEADER.size])
        if (
            magic != HGS1_MAGIC
            or version != HGS1_VERSION
            or header_bytes != HGS1_HEADER_BYTES
            or record_bytes != HGS1_RECORD.size
            or flags != 0
            or any(header[HGS1_HEADER.size :])
        ):
            raise ValueError("invalid HGS1 header geometry")
        if record_count <= 0:
            raise ValueError("HGS1 population is empty")
        if path.stat().st_size != HGS1_HEADER_BYTES + record_count * HGS1_RECORD.size:
            raise ValueError("HGS1 file length differs from record count")
        payload_digest = hashlib.sha256()
        target_digest = hashlib.sha256()
        previous: int | None = None
        seeds: list[tuple[int, int, int, int]] = []
        for _ in range(record_count):
            payload = stream.read(HGS1_RECORD.size)
            if len(payload) != HGS1_RECORD.size:
                raise ValueError("short HGS1 record")
            payload_digest.update(payload)
            target, source, context_hash, transition_hash = HGS1_RECORD.unpack(payload)
            target_digest.update(struct.pack("<Q", target))
            if previous is not None and target <= previous:
                raise ValueError("HGS1 targets are not strictly increasing")
            if (
                target >= wrt_bytes
                or source < 16
                or target < 16
                or target - source <= 100_000_000
                or source + 512 > target
            ):
                raise ValueError("HGS1 seed violates frozen causal age geometry")
            previous = target
            seeds.append((target, source, context_hash, transition_hash))
        if stream.read(1):
            raise ValueError("trailing HGS1 bytes")
    if payload_digest.digest() != payload_sha or target_digest.digest() != target_sha:
        raise ValueError("HGS1 header binding differs from record payload")
    if observer_sha == bytes(32) or config_sha == bytes(32):
        raise ValueError("HGS1 observer or configuration binding is empty")
    return HgsMetadata(
        wrt_bytes=wrt_bytes,
        record_count=record_count,
        terminal_transition_hash=terminal_transition_hash,
        payload_sha256=payload_sha.hex(),
        observer_sha256=observer_sha.hex(),
        observer_config_sha256=config_sha.hex(),
        target_union_sha256=target_sha.hex(),
        seeds=tuple(seeds),
    )


def load_physical_pair(
    project_root: Path, value: object, adapter: Any
):
    physical = _require_object(value, "physicalSeedTape")
    _require_keys(physical, {"a", "b", "binding"}, "physicalSeedTape")
    path_a = resolve_artifact(project_root, physical["a"], "HGS1 A")
    path_b = resolve_artifact(project_root, physical["b"], "HGS1 B")
    artifact_a = _require_object(physical["a"], "HGS1 A")
    artifact_b = _require_object(physical["b"], "HGS1 B")
    if (
        artifact_a["bytes"] != artifact_b["bytes"]
        or artifact_a["sha256"] != artifact_b["sha256"]
    ):
        raise ValueError("HGS1 A/B lack exact repeat identity")
    binding = _require_object(physical["binding"], "HGS1 binding")
    _require_keys(binding, HGS_BINDING_KEYS, "HGS1 binding")
    metadata_a = _hgs_metadata(path_a)
    metadata_b = _hgs_metadata(path_b)
    if (
        metadata_a != metadata_b
        or metadata_a.manifest_binding() != binding
    ):
        raise ValueError("HGS1 repeat or manifest binding mismatch")
    seeds = {
        target: adapter.PhysicalSeed(target, source, context, transition)
        for target, source, context, transition in metadata_a.seeds
    }
    tape = adapter.PhysicalSeedTape(
        metadata_a.observer_sha256,
        metadata_b.observer_sha256,
        metadata_a.payload_sha256,
        metadata_b.payload_sha256,
        metadata_a.terminal_transition_hash,
        metadata_b.terminal_transition_hash,
        seeds,
    )
    return tape, metadata_a


SCOPE_KEYS = {
    "scopeId",
    "rawPopulationBytes",
    "wrtPopulationBytes",
    "replayWrtBegin",
    "replayWrtEnd",
    "measureRawBegin",
    "measureRawEnd",
    "measureWrtBegin",
    "measureWrtEnd",
    "coderBitBegin",
    "coderBitEnd",
    "frontendStateBeginSha256",
    "frontendStateEndSha256",
    "parentStateBeginSha256",
    "parentStateEndSha256",
}

ROUTE_BINDING_KEYS = {
    "fixtureFlags",
    "storeBytes",
    "wrtBytes",
    "rawBytes",
    "dictionaryBytes",
    "recordCount",
    "descriptorCount",
    "eventCounts",
    "deferredUpdates",
    "positionalPredictiveEvents",
    "parserDigest",
    "rawDigest",
    "wrtDigest",
}


def _validate_scope(scope: object) -> dict[str, Any]:
    value = _require_object(scope, "scope")
    _require_keys(value, SCOPE_KEYS, "scope")
    integers = SCOPE_KEYS - {
        "scopeId",
        "frontendStateBeginSha256",
        "frontendStateEndSha256",
        "parentStateBeginSha256",
        "parentStateEndSha256",
    }
    if any(
        not isinstance(value[key], int) or isinstance(value[key], bool)
        for key in integers
    ):
        raise ValueError("scope has noninteger coordinates")
    for key in SCOPE_KEYS & {
        "frontendStateBeginSha256",
        "frontendStateEndSha256",
        "parentStateBeginSha256",
        "parentStateEndSha256",
    }:
        digest = _require_sha256(value[key], f"scope {key}")
        if digest == SHA256_ZERO:
            raise ValueError(f"scope {key} is empty")
    scope_id = value["scopeId"]
    if scope_id not in {"fixture", "opening", "distant"}:
        raise ValueError("unknown HARM scope")
    if not (
        value["rawPopulationBytes"] > 0
        and value["wrtPopulationBytes"] > 0
        and value["replayWrtBegin"] == 0
        and 0 < value["replayWrtEnd"] <= value["wrtPopulationBytes"]
        and 0 <= value["measureRawBegin"] < value["measureRawEnd"]
        <= value["rawPopulationBytes"]
        and 0 <= value["measureWrtBegin"] < value["measureWrtEnd"]
        <= value["replayWrtEnd"]
        and value["coderBitBegin"] == value["measureWrtBegin"] * 8
        and value["coderBitEnd"] == value["measureWrtEnd"] * 8
    ):
        raise ValueError("raw/WRT/coder scope arithmetic mismatch")
    if scope_id == "opening" and (
        value["measureRawBegin"] != 0 or value["measureRawEnd"] != 1_000_000
    ):
        raise ValueError("opening raw scope differs from frozen bounds")
    if scope_id == "distant" and (
        value["measureRawBegin"] != 500_000_000
        or value["measureRawEnd"] != 510_000_000
    ):
        raise ValueError("distant raw scope differs from frozen bounds")
    return value


def _route_binding(
    value: object, tape_a_sha: str, tape_b_sha: str, adapter: Any
):
    binding = _require_object(value, "GSRT2 binding")
    _require_keys(binding, ROUTE_BINDING_KEYS, "GSRT2 binding")
    event_counts = binding["eventCounts"]
    if (
        not isinstance(event_counts, list)
        or len(event_counts) != 9
        or any(not isinstance(item, int) or item < 0 for item in event_counts)
    ):
        raise ValueError("GSRT2 eventCounts geometry mismatch")
    integer_keys = ROUTE_BINDING_KEYS - {"eventCounts"}
    if any(
        not isinstance(binding[key], int) or isinstance(binding[key], bool)
        for key in integer_keys
    ):
        raise ValueError("GSRT2 binding has noninteger fields")
    return adapter.TapeBinding(
        tape_sha256=tape_a_sha,
        repeat_tape_sha256=tape_b_sha,
        fixture_flags=binding["fixtureFlags"],
        store_bytes=binding["storeBytes"],
        wrt_bytes=binding["wrtBytes"],
        raw_bytes=binding["rawBytes"],
        dictionary_bytes=binding["dictionaryBytes"],
        record_count=binding["recordCount"],
        descriptor_count=binding["descriptorCount"],
        event_counts=tuple(event_counts),
        deferred_updates=binding["deferredUpdates"],
        positional_predictive_events=binding["positionalPredictiveEvents"],
        parser_digest=binding["parserDigest"],
        raw_digest=binding["rawDigest"],
        wrt_digest=binding["wrtDigest"],
    )


def load_manifest(path: Path, project_root: Path) -> tuple[dict[str, Any], Any, Any]:
    manifest = _require_object(json.loads(path.read_text()), "input manifest")
    _require_keys(
        manifest,
        {
            "schema",
            "candidateId",
            "harmSourceBinding",
            "scope",
            "wrt",
            "rawToWrtMap",
            "routeTape",
            "parentTape",
            "physicalSeedTape",
        },
        "input manifest",
    )
    if (
        manifest["schema"] != "gamma.enwiki9.harm-delta-sparse-input.v1"
        or manifest["candidateId"] != CANDIDATE_ID
    ):
        raise ValueError("input manifest identity differs")
    core, adapter = load_frozen_harm(project_root, manifest["harmSourceBinding"])
    scope = _validate_scope(manifest["scope"])
    wrt_path = resolve_artifact(project_root, manifest["wrt"], "WRT stream")
    resolve_artifact(project_root, manifest["rawToWrtMap"], "raw/WRT map")
    if wrt_path.stat().st_size != scope["wrtPopulationBytes"]:
        raise ValueError("WRT artifact and scope population differ")

    route = _require_object(manifest["routeTape"], "routeTape")
    _require_keys(route, {"a", "b", "binding"}, "routeTape")
    route_a = resolve_artifact(project_root, route["a"], "GSRT2 A")
    route_b = resolve_artifact(project_root, route["b"], "GSRT2 B")
    route_a_record = _require_object(route["a"], "GSRT2 A")
    route_b_record = _require_object(route["b"], "GSRT2 B")
    if (
        route_a_record["bytes"] != route_b_record["bytes"]
        or route_a_record["sha256"] != route_b_record["sha256"]
    ):
        raise ValueError("GSRT2 A/B lack exact repeat identity")
    tape_binding = _route_binding(
        route["binding"],
        str(route_a_record["sha256"]),
        str(route_b_record["sha256"]),
        adapter,
    )
    if (
        tape_binding.wrt_bytes != scope["wrtPopulationBytes"]
        or tape_binding.raw_bytes != scope["rawPopulationBytes"]
    ):
        raise ValueError("GSRT2 population and scope differ")

    parent = _require_object(manifest["parentTape"], "parentTape")
    _require_keys(parent, {"a", "b", "binding"}, "parentTape")
    parent_a = resolve_artifact(project_root, parent["a"], "HSP1 A")
    parent_b = resolve_artifact(project_root, parent["b"], "HSP1 B")
    parent_a_record = _require_object(parent["a"], "HSP1 A")
    parent_b_record = _require_object(parent["b"], "HSP1 B")
    if (
        parent_a_record["bytes"] != parent_b_record["bytes"]
        or parent_a_record["sha256"] != parent_b_record["sha256"]
    ):
        raise ValueError("HSP1 A/B lack exact repeat identity")
    parent_binding = _require_object(parent["binding"], "HSP1 binding")
    _require_keys(parent_binding, HSP_BINDING_KEYS, "HSP1 binding")
    metadata_a = _hsp_metadata(parent_a)
    metadata_b = _hsp_metadata(parent_b)
    if metadata_a != metadata_b or metadata_a.manifest_binding() != parent_binding:
        raise ValueError("HSP1 repeat or manifest binding mismatch")
    if (
        metadata_a.wrt_bytes != scope["wrtPopulationBytes"]
        or metadata_a.replay_begin != scope["replayWrtBegin"]
        or metadata_a.replay_end != scope["replayWrtEnd"]
        or metadata_a.parent_state_begin_sha256
        != scope["parentStateBeginSha256"]
        or metadata_a.parent_state_end_sha256
        != scope["parentStateEndSha256"]
    ):
        raise ValueError("HSP1 parent state or replay scope differs")

    physical_value = manifest["physicalSeedTape"]
    physical_tape = None
    physical_metadata = None
    if physical_value is not None:
        physical_tape, physical_metadata = load_physical_pair(
            project_root, physical_value, adapter
        )
        if physical_metadata.wrt_bytes != scope["wrtPopulationBytes"]:
            raise ValueError("HGS1 population and scope differ")
    if scope["scopeId"] == "distant" and physical_tape is None:
        raise ValueError("distant HARM scope requires HGS1")
    if scope["scopeId"] in {"fixture", "opening"} and physical_tape is not None:
        raise ValueError("fixture/opening HARM scope forbids HGS1")

    loaded = {
        "manifest": manifest,
        "scope": scope,
        "wrt_path": wrt_path,
        "route_paths": {"a": route_a, "b": route_b},
        "tape_binding": tape_binding,
        "parent_paths": {"a": parent_a, "b": parent_b},
        "parent_binding": parent_binding,
        "parent_metadata": metadata_a,
        "physical_tape": physical_tape,
        "physical_metadata": physical_metadata,
    }
    return loaded, core, adapter


def _run_arm(loaded: dict[str, Any], adapter: Any, arm: str) -> dict[str, object]:
    provider = SparseParentProvider(
        loaded["parent_paths"][arm], loaded["parent_binding"]
    )
    wrt_file = loaded["wrt_path"].open("rb")
    try:
        stream = mmap.mmap(wrt_file.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            physical = loaded["physical_tape"]
            observer_sha = None if physical is None else physical.observer_sha256
            scope = loaded["scope"]
            result = adapter.replay(
                stream,
                adapter.iter_tape(
                    loaded["route_paths"][arm], loaded["tape_binding"]
                ),
                provider,
                physical_seed_tape=physical,
                expected_physical_observer_sha256=observer_sha,
                measure_start=scope["measureWrtBegin"],
                measure_end=scope["measureWrtEnd"],
                measure_raw_start=scope["measureRawBegin"],
                measure_raw_end=scope["measureRawEnd"],
            )
            provider.finish()
        finally:
            stream.close()
    finally:
        provider.close()
        wrt_file.close()
    result["sparse_parent_records_consumed"] = provider.consumed
    result["sparse_parent_coordinate_union_sha256"] = (
        provider.metadata.coordinate_union_sha256
    )
    result["parent_observer_sha256"] = provider.metadata.parent_observer_sha256
    return result


def execute_manifest(path: Path, project_root: Path) -> dict[str, object]:
    loaded, _, adapter = load_manifest(path, project_root)
    first = _run_arm(loaded, adapter, "a")
    second = _run_arm(loaded, adapter, "b")
    return {
        "manifest_sha256": sha256_path(path),
        "scope_id": loaded["scope"]["scopeId"],
        "repeat_identity_pass": first == second,
        "run_a": first,
        "run_b": second,
    }


def write_hsp1(
    path: Path,
    rows: list[tuple[int, tuple[int, ...]]],
    *,
    wrt_bytes: int,
    replay_begin: int,
    replay_end: int,
    parent_observer_sha256: str,
    parent_state_begin_sha256: str,
    parent_state_end_sha256: str,
    validate: bool = True,
) -> HspMetadata:
    observer = bytes.fromhex(_require_sha256(parent_observer_sha256, "observer"))
    state_begin = bytes.fromhex(
        _require_sha256(parent_state_begin_sha256, "parent state begin")
    )
    state_end = bytes.fromhex(
        _require_sha256(parent_state_end_sha256, "parent state end")
    )
    payload = b"".join(HSP1_RECORD.pack(coordinate, *row) for coordinate, row in rows)
    coordinates = b"".join(struct.pack("<Q", coordinate) for coordinate, _ in rows)
    first = rows[0][0] if rows else UINT64_MAX
    last = rows[-1][0] if rows else UINT64_MAX
    header = HSP1_HEADER.pack(
        HSP1_MAGIC,
        HSP1_VERSION,
        HSP1_HEADER_BYTES,
        HSP1_RECORD.size,
        65536,
        wrt_bytes,
        replay_begin,
        replay_end,
        len(rows),
        first,
        last,
        hashlib.sha256(payload).digest(),
        hashlib.sha256(coordinates).digest(),
        observer,
        state_begin,
        state_end,
    )
    path.write_bytes(header + bytes(HSP1_HEADER_BYTES - len(header)) + payload)
    metadata = HspMetadata(
        wrt_bytes=wrt_bytes,
        replay_begin=replay_begin,
        replay_end=replay_end,
        record_count=len(rows),
        first_coordinate=first,
        last_coordinate=last,
        payload_sha256=hashlib.sha256(payload).hexdigest(),
        coordinate_union_sha256=hashlib.sha256(coordinates).hexdigest(),
        parent_observer_sha256=parent_observer_sha256,
        parent_state_begin_sha256=parent_state_begin_sha256,
        parent_state_end_sha256=parent_state_end_sha256,
    )
    return _hsp_metadata(path) if validate else metadata


def write_hgs1(
    path: Path,
    rows: list[tuple[int, int, int, int]],
    *,
    wrt_bytes: int,
    terminal_transition_hash: int,
    observer_sha256: str,
    observer_config_sha256: str,
) -> HgsMetadata:
    observer = bytes.fromhex(_require_sha256(observer_sha256, "HGS observer"))
    config = bytes.fromhex(_require_sha256(observer_config_sha256, "HGS config"))
    payload = b"".join(HGS1_RECORD.pack(*row) for row in rows)
    targets = b"".join(struct.pack("<Q", row[0]) for row in rows)
    header = HGS1_HEADER.pack(
        HGS1_MAGIC,
        HGS1_VERSION,
        HGS1_HEADER_BYTES,
        HGS1_RECORD.size,
        0,
        wrt_bytes,
        len(rows),
        terminal_transition_hash,
        hashlib.sha256(payload).digest(),
        observer,
        config,
        hashlib.sha256(targets).digest(),
    )
    path.write_bytes(header + bytes(HGS1_HEADER_BYTES - len(header)) + payload)
    return _hgs_metadata(path)
