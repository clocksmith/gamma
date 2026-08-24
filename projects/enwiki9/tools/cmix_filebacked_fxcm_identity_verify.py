#!/usr/bin/env python3
"""Independently rehash and rederive file-backed FXCM identity receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Iterator

import jsonschema


OUTPUT_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-identity-verification.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
RSS_LIMIT_KIB = 9_765_625
DISK_LIMIT_BYTES = 100_000_000_000
TRACE_RECORD_BYTES = 56
TRACE_BYTE_RECORD_BYTES = 5
SOURCE_SCHEMAS = {
    "gamma.enwiki9.cmix-filebacked-fxcm-scope-identity.v2": (
        "cmix-filebacked-fxcm-scope-identity-v2.schema.json",
        ((0, 250_000), (500_000_000, 250_000), (999_750_000, 250_000)),
    ),
    "gamma.enwiki9.cmix-filebacked-fxcm-cumulative-identity.v1": (
        "cmix-filebacked-fxcm-cumulative-identity.schema.json",
        ((0, 1_000_000),),
    ),
    "gamma.enwiki9.cmix-filebacked-fxcm-transfer-10m.v1": (
        "cmix-filebacked-fxcm-transfer-10m.schema.json",
        ((0, 10_000_000), (500_000_000, 10_000_000)),
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def regular_no_links(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise RuntimeError(f"{label} must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label} has symlink component: {current}")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label} must be a single-link regular file")
    return path.resolve(strict=True)


def directory_no_links(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise RuntimeError(f"{label} must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"{label} has invalid component: {current}")
    return path.resolve(strict=True)


def load_json(path: Path, label: str) -> tuple[Path, dict[str, Any]]:
    resolved = regular_no_links(path, label)
    value = json.loads(resolved.read_text(encoding="ascii"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must be a JSON object")
    return resolved, value


def is_artifact(value: Any) -> bool:
    return isinstance(value, dict) and set(value) == {"path", "bytes", "sha256"}


def artifact_records(value: Any) -> Iterator[dict[str, Any]]:
    if is_artifact(value):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from artifact_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from artifact_records(child)


def bind_artifacts(value: dict[str, Any]) -> dict[Path, dict[str, Any]]:
    unique: dict[Path, dict[str, Any]] = {}
    for index, record in enumerate(artifact_records(value)):
        path = regular_no_links(Path(str(record.get("path", ""))), f"artifact {index}")
        normalized = {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": str(record.get("sha256", "")),
        }
        if record.get("bytes") != normalized["bytes"]:
            raise RuntimeError(f"artifact byte count mismatch: {path}")
        prior = unique.get(path)
        if prior is not None and prior != normalized:
            raise RuntimeError(f"inconsistent duplicate artifact record: {path}")
        unique[path] = normalized
    return unique


def receipt_scopes(value: dict[str, Any]) -> list[dict[str, Any]]:
    if value["schema"] == "gamma.enwiki9.cmix-filebacked-fxcm-cumulative-identity.v1":
        return [
            {
                "offset": value["offset"],
                "bytes": value["bytes"],
                "slice_sha256": value["slice_sha256"],
                "arms": value["arms"],
                "raw_slice_inverse_required": True,
            }
        ]
    return value["scopes"]


def parse_meta(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        key, separator, text = line.partition("=")
        if not separator or key in result:
            raise RuntimeError(f"malformed trace metadata: {path}")
        result[key] = text
    expected = {
        "format": "res_v3",
        "record_bytes": str(TRACE_RECORD_BYTES),
        "n_stage1": "25",
        "elem": "f16",
        "endian": "little",
        "truncated": "0",
    }
    if any(result.get(key) != text for key, text in expected.items()):
        raise RuntimeError(f"trace metadata contract mismatch: {path}")
    return result


def trace_hashes(path: Path, aggregate: "hashlib._Hash") -> tuple[str, str, int]:
    full = hashlib.sha256()
    probability = hashlib.sha256()
    records = 0
    with path.open("rb") as stream:
        while block := stream.read(TRACE_RECORD_BYTES * 65_536):
            if len(block) % TRACE_RECORD_BYTES:
                raise RuntimeError(f"partial trace record: {path}")
            count = len(block) // TRACE_RECORD_BYTES
            packed = bytearray(count * 2)
            packed[0::2] = block[0::TRACE_RECORD_BYTES]
            packed[1::2] = block[1::TRACE_RECORD_BYTES]
            full.update(block)
            probability.update(packed)
            aggregate.update(packed)
            records += count
    return full.hexdigest(), probability.hexdigest(), records


def guard_pass(value: dict[str, Any]) -> bool:
    return (
        value.get("schema") == "gamma.enwiki9.resource-guard-receipt.v2"
        and value.get("status") == "complete"
        and value.get("returncode") == 0
        and value.get("rss_guard_exceeded") is False
        and value.get("official_decimal_memory_exceeded") is False
        and value.get("temporary_disk_guard_exceeded") is False
        and value.get("logical_cpu_guard_exceeded") is False
        and value.get("max_sampled_tree_rss_kib", RSS_LIMIT_KIB + 1) <= RSS_LIMIT_KIB
        and value.get("max_sampled_temporary_disk_bytes", DISK_LIMIT_BYTES + 1)
        <= DISK_LIMIT_BYTES
        and value.get("max_sampled_allowed_cpu_count") == 1
    )


def write_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    parent = directory_no_links(path.parent, "output parent")
    data = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        parent / path.name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        cursor = 0
        while cursor < len(data):
            written = os.write(descriptor, data[cursor:])
            if written <= 0:
                raise OSError("short verification write")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    receipt_path, receipt = load_json(args.receipt, "identity receipt")
    source_schema = receipt.get("schema")
    if source_schema not in SOURCE_SCHEMAS:
        raise RuntimeError(f"unsupported source schema: {source_schema}")
    if receipt.get("candidate_id") != CANDIDATE_ID or receipt.get("terminal_pass") is not True:
        raise RuntimeError("source receipt is not a terminal q1 pass")
    schema_name, expected_scopes = SOURCE_SCHEMAS[source_schema]
    schema = json.loads(
        (Path(__file__).resolve().parents[1] / "contracts/research/v1" / schema_name).read_text(
            encoding="ascii"
        )
    )
    jsonschema.Draft202012Validator(schema).validate(receipt)
    records = list(artifact_records(receipt))
    unique = bind_artifacts(receipt)
    scopes = receipt_scopes(receipt)
    actual_scopes = tuple((item["offset"], item["bytes"]) for item in scopes)
    if actual_scopes != expected_scopes:
        raise RuntimeError("source receipt scope schedule mismatch")
    if len(scopes) != len(expected_scopes):
        raise RuntimeError("source receipt scope count mismatch")

    residual_paths = {
        Path(arm["trace"]["residual_trace"]["path"]).resolve(strict=True)
        for item in scopes
        for arm in item["arms"]
    }
    for path, record in unique.items():
        if path not in residual_paths and sha256_file(path) != record["sha256"]:
            raise RuntimeError(f"artifact SHA-256 mismatch: {path}")

    aggregates = {arm: hashlib.sha256() for arm in ("parent", "candidate")}
    guards: list[dict[str, Any]] = []
    probability_identity = True
    full_trace_identity = True
    payload_identity = True
    decoded_identity = True
    opening_inverse = True
    trace_geometry = True
    for item in scopes:
        offset = item["offset"]
        length = item["bytes"]
        if [arm.get("arm") for arm in item["arms"]] != ["parent", "candidate"]:
            raise RuntimeError(f"arm ordering or identity mismatch at offset {offset}")
        for aggregate in aggregates.values():
            aggregate.update(offset.to_bytes(8, "little"))
            aggregate.update(length.to_bytes(8, "little"))
        for arm in item["arms"]:
            name = arm["arm"]
            trace = arm["trace"]
            residual_path = Path(trace["residual_trace"]["path"]).resolve(strict=True)
            full_sha, probability_sha, bit_records = trace_hashes(
                residual_path, aggregates[name]
            )
            if full_sha != trace["residual_trace"]["sha256"]:
                raise RuntimeError(f"residual trace SHA-256 mismatch: {residual_path}")
            if probability_sha != trace["integer_probability_stream_sha256"]:
                raise RuntimeError(f"integer probability SHA-256 mismatch: {residual_path}")
            metadata = parse_meta(Path(trace["metadata"]["path"]))
            byte_records = int(metadata["total_byte_records"])
            trace_geometry &= (
                bit_records == int(metadata["total_bit_records"])
                and bit_records == trace["bit_records"]
                and byte_records == trace["byte_records"]
                and bit_records == 8 * byte_records
                and trace["residual_trace"]["bytes"] == bit_records * TRACE_RECORD_BYTES
                and trace["byte_trace"]["bytes"] == byte_records * TRACE_BYTE_RECORD_BYTES
            )
            for phase in ("encode", "decode"):
                _, guard = load_json(Path(arm[f"{phase}_guard"]["path"]), f"{phase} guard")
                if not guard_pass(guard):
                    raise RuntimeError(f"{phase} guard failed independent checks at {offset}")
                guards.append(guard)
        parent, candidate = item["arms"]
        probability_identity &= (
            parent["trace"]["integer_probability_stream_sha256"]
            == candidate["trace"]["integer_probability_stream_sha256"]
        )
        full_trace_identity &= (
            parent["trace"]["residual_trace"]["sha256"]
            == candidate["trace"]["residual_trace"]["sha256"]
            and parent["trace"]["byte_trace"]["sha256"]
            == candidate["trace"]["byte_trace"]["sha256"]
        )
        payload_identity &= parent["payload"]["sha256"] == candidate["payload"]["sha256"]
        decoded_identity &= (
            parent["restored"]["bytes"] == candidate["restored"]["bytes"]
            and parent["restored"]["sha256"] == candidate["restored"]["sha256"]
        )
        if item["raw_slice_inverse_required"]:
            opening_inverse &= all(
                arm["restored"]["bytes"] == length
                and arm["restored"]["sha256"] == item["slice_sha256"]
                for arm in item["arms"]
            )

    if not all(
        (probability_identity, full_trace_identity, payload_identity, decoded_identity,
         opening_inverse, trace_geometry)
    ):
        raise RuntimeError("one or more identity predicates failed independent derivation")
    aggregate_parent = aggregates["parent"].hexdigest()
    aggregate_candidate = aggregates["candidate"].hexdigest()
    if source_schema == "gamma.enwiki9.cmix-filebacked-fxcm-scope-identity.v2":
        recorded_parent = receipt["aggregate"]["parent_scoped_probability_stream_sha256"]
        recorded_candidate = receipt["aggregate"]["candidate_scoped_probability_stream_sha256"]
    else:
        recorded_parent = receipt["aggregate"]["parent_probability_stream_sha256"]
        recorded_candidate = receipt["aggregate"]["candidate_probability_stream_sha256"]
    aggregate_pass = (
        aggregate_parent == aggregate_candidate == recorded_parent == recorded_candidate
    )
    if not aggregate_pass:
        raise RuntimeError("aggregate probability stream digest mismatch")
    maximum_rss = max(guard["max_sampled_tree_rss_kib"] for guard in guards)
    maximum_disk = max(guard["max_sampled_temporary_disk_bytes"] for guard in guards)
    maximum_cpu = max(guard["max_sampled_allowed_cpu_count"] for guard in guards)
    recorded_resources = receipt.get("resources")
    if recorded_resources is not None and (
        recorded_resources["guard_count"] != len(guards)
        or recorded_resources["maximum_tree_rss_kib"] != maximum_rss
        or recorded_resources["maximum_temporary_disk_bytes"] != maximum_disk
        or recorded_resources["maximum_allowed_cpu_count"] != maximum_cpu
    ):
        raise RuntimeError("recorded resource summary differs from guarded evidence")
    scratch_root = args.scratch_root
    scratch_absent = not scratch_root.exists() and not scratch_root.is_symlink()
    if not scratch_absent:
        raise RuntimeError("declared scratch root still exists")

    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "source_schema": source_schema,
        "source_receipt": {
            "path": str(receipt_path),
            "bytes": receipt_path.stat().st_size,
            "sha256": sha256_file(receipt_path),
        },
        "verifier": {
            "path": str(Path(__file__).resolve(strict=True)),
            "bytes": Path(__file__).stat().st_size,
            "sha256": sha256_file(Path(__file__).resolve(strict=True)),
        },
        "scope_count": len(scopes),
        "artifact_record_count": len(records),
        "unique_artifact_count": len(unique),
        "artifact_identity_pass": True,
        "trace_geometry_pass": trace_geometry,
        "integer_probability_rederivation_pass": probability_identity,
        "full_trace_identity_rederivation_pass": full_trace_identity,
        "payload_identity_rederivation_pass": payload_identity,
        "decoded_identity_rederivation_pass": decoded_identity,
        "opening_inverse_rederivation_pass": opening_inverse,
        "aggregate_probability_rederivation_pass": aggregate_pass,
        "resource_guard_rederivation_pass": True,
        "guard_count": len(guards),
        "maximum_tree_rss_kib": maximum_rss,
        "maximum_temporary_disk_bytes": maximum_disk,
        "maximum_allowed_cpu_count": maximum_cpu,
        "scratch_root": str(scratch_root),
        "scratch_root_absent_pass": scratch_absent,
        "verification_pass": True,
        "claim_authority": "independent_identity_receipt_verification_only",
        "execution_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    write_new(args.output, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
