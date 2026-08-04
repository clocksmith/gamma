#!/usr/bin/env python3
"""Proof-carrying five-segment archive assembler for enwiki9.

This program does not contain a winning compressor.  It composes five independent
segment codec packages, verifies their package identities, and creates or decodes
one deterministic container.  A segment package is a ZIP archive containing a
root-level ``codec.json`` and every file needed by its commands.

The final numerical bound is obtained only when all five supplied segment
packages and payloads satisfy the frozen budgets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Any, BinaryIO, Iterable, Sequence
import zipfile


PROGRAM_VERSION = "1.0.0"
MANIFEST_SCHEMA = "enwiki9_segment_bundle/v1"
CODEC_SCHEMA = "enwiki9_segment_codec/v1"
ARCHIVE_SCHEMA = "enwiki9_segment_archive/v1"
CERTIFICATE_SCHEMA = "enwiki9_segment_certificate/v1"
MAGIC = b"EW9BNDL1"
HEADER_LENGTH = struct.Struct(">Q")
FOOTER_BYTES = 32
MAX_HEADER_BYTES = 16 * 1024 * 1024
COPY_CHUNK = 1 << 20
PLACEHOLDERS = {"{input}", "{output}"}


class BundleError(RuntimeError):
    """Raised for invalid artifacts, manifests, or codec behavior."""


@dataclass(frozen=True)
class Artifact:
    path: Path
    size: int
    sha256: str


@dataclass(frozen=True)
class SegmentSpec:
    index: int
    codec_id: str
    package: Artifact


@dataclass(frozen=True)
class BundleSpec:
    manifest_path: Path
    manifest_size: int
    manifest_sha256: str
    profile: str
    raw_size: int
    segment_size: int
    segment_count: int
    segment_budget_bytes: int
    outer_budget_bytes: int
    target_bytes: int
    outer_package: Artifact
    segments: tuple[SegmentSpec, ...]


@dataclass(frozen=True)
class CodecSpec:
    codec_id: str
    segment_index: int
    prepare: tuple[str, ...]
    compress: tuple[str, ...]
    decompress: tuple[str, ...]
    environment: dict[str, str]


@dataclass(frozen=True)
class ArchiveLayout:
    path: Path
    header: dict[str, Any]
    header_bytes: bytes
    payload_offset: int
    payload_offsets: tuple[int, ...]
    payload_lengths: tuple[int, ...]
    archive_size: int
    archive_sha256: str


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(COPY_CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_for(path: Path) -> Artifact:
    resolved = path.resolve()
    if not resolved.is_file():
        raise BundleError(f"artifact does not exist or is not a file: {resolved}")
    return Artifact(resolved, resolved.stat().st_size, sha256_file(resolved))


def _require_int(value: Any, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise BundleError(f"{name} must be an integer >= {minimum}")
    return value


def _require_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise BundleError(f"{name} must be a nonempty string")
    return value


def _resolve_artifact(
    base: Path, obj: Any, name: str, *, require_hash: bool = True
) -> Artifact:
    if not isinstance(obj, dict):
        raise BundleError(f"{name} must be an object")
    rel = _require_str(obj.get("path"), f"{name}.path")
    path = (base / rel).resolve()
    artifact = artifact_for(path)
    expected_size = obj.get("bytes")
    if expected_size is not None and _require_int(expected_size, f"{name}.bytes") != artifact.size:
        raise BundleError(
            f"{name} size mismatch: expected {expected_size}, observed {artifact.size}"
        )
    expected_sha = obj.get("sha256")
    if expected_sha is None:
        if require_hash:
            raise BundleError(f"{name}.sha256 is required")
    else:
        expected_sha = _require_str(expected_sha, f"{name}.sha256").lower()
        if expected_sha != artifact.sha256:
            raise BundleError(
                f"{name} SHA-256 mismatch: expected {expected_sha}, observed {artifact.sha256}"
            )
    return artifact


def load_bundle_spec(path: Path, *, require_hashes: bool = True) -> BundleSpec:
    manifest_path = path.resolve()
    raw = manifest_path.read_bytes()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BundleError(f"invalid JSON manifest: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != MANIFEST_SCHEMA:
        raise BundleError(f"manifest schema must be {MANIFEST_SCHEMA!r}")

    base = manifest_path.parent
    profile = _require_str(data.get("profile"), "profile")
    raw_size = _require_int(data.get("raw_size"), "raw_size", minimum=1)
    segment_size = _require_int(data.get("segment_size"), "segment_size", minimum=1)
    segment_count = _require_int(data.get("segment_count"), "segment_count", minimum=1)
    if raw_size != segment_size * segment_count:
        raise BundleError("raw_size must equal segment_size * segment_count")
    segment_budget = _require_int(
        data.get("segment_budget_bytes"), "segment_budget_bytes", minimum=1
    )
    outer_budget = _require_int(
        data.get("outer_budget_bytes"), "outer_budget_bytes", minimum=0
    )
    target_bytes = _require_int(data.get("target_bytes"), "target_bytes", minimum=1)
    outer_package = _resolve_artifact(
        base, data.get("outer_package"), "outer_package", require_hash=require_hashes
    )

    segment_entries = data.get("segments")
    if not isinstance(segment_entries, list) or len(segment_entries) != segment_count:
        raise BundleError(f"segments must contain exactly {segment_count} entries")

    segments: list[SegmentSpec] = []
    seen_ids: set[str] = set()
    for expected_index, entry in enumerate(segment_entries):
        if not isinstance(entry, dict):
            raise BundleError(f"segments[{expected_index}] must be an object")
        index = _require_int(entry.get("index"), f"segments[{expected_index}].index")
        if index != expected_index:
            raise BundleError("segment entries must be in contiguous index order")
        codec_id = _require_str(entry.get("codec_id"), f"segments[{index}].codec_id")
        if codec_id in seen_ids:
            raise BundleError(f"duplicate codec_id: {codec_id}")
        seen_ids.add(codec_id)
        package = _resolve_artifact(
            base,
            entry.get("package"),
            f"segments[{index}].package",
            require_hash=require_hashes,
        )
        segments.append(SegmentSpec(index, codec_id, package))

    return BundleSpec(
        manifest_path=manifest_path,
        manifest_size=len(raw),
        manifest_sha256=hashlib.sha256(raw).hexdigest(),
        profile=profile,
        raw_size=raw_size,
        segment_size=segment_size,
        segment_count=segment_count,
        segment_budget_bytes=segment_budget,
        outer_budget_bytes=outer_budget,
        target_bytes=target_bytes,
        outer_package=outer_package,
        segments=tuple(segments),
    )


def validate_enwiki9_competition_profile(spec: BundleSpec) -> None:
    expected = {
        "raw_size": 1_000_000_000,
        "segment_size": 200_000_000,
        "segment_count": 5,
        "segment_budget_bytes": 20_190_000,
        "outer_budget_bytes": 100_000,
        "target_bytes": 101_101_101,
    }
    for name, value in expected.items():
        if getattr(spec, name) != value:
            raise BundleError(
                f"competition profile requires {name}={value}, observed {getattr(spec, name)}"
            )


def _safe_member_path(root: Path, name: str) -> Path:
    if not name or name.startswith(("/", "\\")):
        raise BundleError(f"unsafe ZIP member: {name!r}")
    candidate = (root / name).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise BundleError(f"ZIP path traversal is forbidden: {name!r}") from exc
    return candidate


def safe_extract_zip(package: Path, destination: Path) -> None:
    with zipfile.ZipFile(package, "r") as archive:
        for info in archive.infolist():
            mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(mode):
                raise BundleError(f"symbolic links are forbidden in codec packages: {info.filename}")
            target = _safe_member_path(destination, info.filename)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, "r") as source, target.open("wb") as output:
                shutil.copyfileobj(source, output, COPY_CHUNK)
            if mode & stat.S_IXUSR:
                target.chmod(0o755)
            else:
                target.chmod(0o644)


def _command(value: Any, name: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if value is None and allow_empty:
        return ()
    if not isinstance(value, list) or (not value and not allow_empty):
        raise BundleError(f"{name} must be a {'possibly empty ' if allow_empty else ''}list")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_require_str(item, f"{name}[{index}]"))
    return tuple(result)


def load_codec_spec(root: Path, expected: SegmentSpec) -> CodecSpec:
    codec_manifest = root / "codec.json"
    if not codec_manifest.is_file():
        raise BundleError(f"codec package {expected.codec_id} lacks root-level codec.json")
    try:
        data = json.loads(codec_manifest.read_text("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BundleError(f"invalid codec.json for {expected.codec_id}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != CODEC_SCHEMA:
        raise BundleError(f"codec schema must be {CODEC_SCHEMA!r}")
    codec_id = _require_str(data.get("codec_id"), "codec_id")
    segment_index = _require_int(data.get("segment_index"), "segment_index")
    if codec_id != expected.codec_id:
        raise BundleError(
            f"codec_id mismatch: outer manifest has {expected.codec_id}, package has {codec_id}"
        )
    if segment_index != expected.index:
        raise BundleError(
            f"segment index mismatch for {codec_id}: expected {expected.index}, package has {segment_index}"
        )
    prepare = _command(data.get("prepare", []), "prepare", allow_empty=True)
    compress = _command(data.get("compress"), "compress")
    decompress = _command(data.get("decompress"), "decompress")
    environment_obj = data.get("environment", {})
    if not isinstance(environment_obj, dict):
        raise BundleError("environment must be an object")
    environment: dict[str, str] = {}
    for key, value in environment_obj.items():
        environment[_require_str(key, "environment key")] = _require_str(
            value, f"environment[{key!r}]"
        )
    return CodecSpec(codec_id, segment_index, prepare, compress, decompress, environment)


def _expanded_command(command: Sequence[str], input_path: Path, output_path: Path) -> list[str]:
    result: list[str] = []
    used: set[str] = set()
    for token in command:
        expanded = token.replace("{input}", str(input_path)).replace(
            "{output}", str(output_path)
        )
        for placeholder in PLACEHOLDERS:
            if placeholder in token:
                used.add(placeholder)
        result.append(expanded)
    if used != PLACEHOLDERS:
        raise BundleError(
            "codec command must reference both {input} and {output} exactly through its argument list"
        )
    return result


def _clean_environment(extra: dict[str, str]) -> dict[str, str]:
    allowed = {
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "PATHEXT",
        "TMP",
        "TEMP",
        "TMPDIR",
        "HOME",
        "USERPROFILE",
        "LD_LIBRARY_PATH",
        "DYLD_LIBRARY_PATH",
    }
    env = {key: value for key, value in os.environ.items() if key in allowed}
    env.update(
        {
            "PYTHONHASHSEED": "0",
            "LC_ALL": "C",
            "LANG": "C",
            "TZ": "UTC",
        }
    )
    env.update(extra)
    return env


def _run(command: Sequence[str], cwd: Path, env: dict[str, str], label: str) -> None:
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise BundleError(f"failed to execute {label}: {exc}") from exc
    if completed.returncode != 0:
        stdout = completed.stdout.decode("utf-8", "replace")[-4000:]
        stderr = completed.stderr.decode("utf-8", "replace")[-4000:]
        raise BundleError(
            f"{label} exited with {completed.returncode}\nstdout:\n{stdout}\nstderr:\n{stderr}"
        )


def run_codec(
    segment: SegmentSpec,
    operation: str,
    input_path: Path,
    output_path: Path,
) -> None:
    if operation not in {"compress", "decompress"}:
        raise BundleError(f"unsupported operation: {operation}")
    with tempfile.TemporaryDirectory(prefix=f"ew9-{segment.index}-{operation}-") as temp_name:
        root = Path(temp_name)
        safe_extract_zip(segment.package.path, root)
        codec = load_codec_spec(root, segment)
        env = _clean_environment(codec.environment)
        if codec.prepare:
            _run(codec.prepare, root, env, f"{segment.codec_id} prepare")
        command = codec.compress if operation == "compress" else codec.decompress
        expanded = _expanded_command(command, input_path.resolve(), output_path.resolve())
        _run(expanded, root, env, f"{segment.codec_id} {operation}")
    if not output_path.is_file():
        raise BundleError(f"{segment.codec_id} {operation} did not create {output_path}")


def files_equal(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as a, right.open("rb") as b:
        while True:
            x = a.read(COPY_CHUNK)
            y = b.read(COPY_CHUNK)
            if x != y:
                return False
            if not x:
                return True


def _copy_n(source: BinaryIO, output: BinaryIO, count: int, *digests: Any) -> None:
    remaining = count
    while remaining:
        block = source.read(min(COPY_CHUNK, remaining))
        if not block:
            raise BundleError(f"input ended {remaining} bytes before the declared segment boundary")
        output.write(block)
        for digest in digests:
            digest.update(block)
        remaining -= len(block)


def _build_header(
    spec: BundleSpec,
    raw_sha256: str,
    segment_records: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema": ARCHIVE_SCHEMA,
        "version": 1,
        "profile": spec.profile,
        "raw_size": spec.raw_size,
        "raw_sha256": raw_sha256,
        "segment_size": spec.segment_size,
        "segment_count": spec.segment_count,
        "manifest_sha256": spec.manifest_sha256,
        "segments": list(segment_records),
    }


def write_archive(
    path: Path,
    header: dict[str, Any],
    payload_paths: Sequence[Path],
) -> Artifact:
    header_bytes = canonical_json_bytes(header)
    if len(header_bytes) > MAX_HEADER_BYTES:
        raise BundleError("archive header exceeds the safety limit")
    prefix = MAGIC + HEADER_LENGTH.pack(len(header_bytes))
    digest = hashlib.sha256()
    destination = path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(destination.name + ".tmp")
    try:
        with temp.open("wb") as output:
            output.write(prefix)
            output.write(header_bytes)
            digest.update(prefix)
            digest.update(header_bytes)
            for payload in payload_paths:
                with payload.open("rb") as source:
                    for block in iter(lambda: source.read(COPY_CHUNK), b""):
                        output.write(block)
                        digest.update(block)
            output.write(digest.digest())
        os.replace(temp, destination)
    finally:
        if temp.exists():
            temp.unlink()
    return artifact_for(destination)


def parse_archive(path: Path, *, verify_digest: bool = True) -> ArchiveLayout:
    archive_path = path.resolve()
    size = archive_path.stat().st_size
    with archive_path.open("rb") as source:
        magic = source.read(len(MAGIC))
        if magic != MAGIC:
            raise BundleError("invalid archive magic")
        packed_length = source.read(HEADER_LENGTH.size)
        if len(packed_length) != HEADER_LENGTH.size:
            raise BundleError("truncated archive header length")
        header_length = HEADER_LENGTH.unpack(packed_length)[0]
        if header_length > MAX_HEADER_BYTES:
            raise BundleError("archive header exceeds the safety limit")
        header_bytes = source.read(header_length)
        if len(header_bytes) != header_length:
            raise BundleError("truncated archive header")
    try:
        header = json.loads(header_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BundleError(f"invalid archive header JSON: {exc}") from exc
    if not isinstance(header, dict) or header.get("schema") != ARCHIVE_SCHEMA:
        raise BundleError(f"archive schema must be {ARCHIVE_SCHEMA!r}")
    segments = header.get("segments")
    if not isinstance(segments, list) or not segments:
        raise BundleError("archive contains no segment records")
    lengths: list[int] = []
    offsets: list[int] = []
    cursor = len(MAGIC) + HEADER_LENGTH.size + header_length
    for expected_index, record in enumerate(segments):
        if not isinstance(record, dict):
            raise BundleError("invalid segment record")
        if record.get("index") != expected_index:
            raise BundleError("archive segment records are not in contiguous order")
        length = _require_int(record.get("payload_bytes"), "payload_bytes")
        offsets.append(cursor)
        lengths.append(length)
        cursor += length
    expected_size = cursor + FOOTER_BYTES
    if expected_size != size:
        raise BundleError(f"archive size mismatch: expected {expected_size}, observed {size}")

    if verify_digest:
        digest = hashlib.sha256()
        remaining = size - FOOTER_BYTES
        with archive_path.open("rb") as source:
            while remaining:
                block = source.read(min(COPY_CHUNK, remaining))
                if not block:
                    raise BundleError("truncated archive while verifying digest")
                digest.update(block)
                remaining -= len(block)
            footer = source.read(FOOTER_BYTES)
        if digest.digest() != footer:
            raise BundleError("archive footer digest mismatch")

    return ArchiveLayout(
        path=archive_path,
        header=header,
        header_bytes=header_bytes,
        payload_offset=len(MAGIC) + HEADER_LENGTH.size + header_length,
        payload_offsets=tuple(offsets),
        payload_lengths=tuple(lengths),
        archive_size=size,
        archive_sha256=sha256_file(archive_path),
    )


def _assert_archive_matches_manifest(layout: ArchiveLayout, spec: BundleSpec) -> None:
    header = layout.header
    expected_scalar = {
        "profile": spec.profile,
        "raw_size": spec.raw_size,
        "segment_size": spec.segment_size,
        "segment_count": spec.segment_count,
        "manifest_sha256": spec.manifest_sha256,
    }
    for name, value in expected_scalar.items():
        if header.get(name) != value:
            raise BundleError(
                f"archive {name} differs from manifest: {header.get(name)!r} != {value!r}"
            )
    records = header["segments"]
    if len(records) != len(spec.segments):
        raise BundleError("archive segment count differs from manifest")
    for segment, record in zip(spec.segments, records, strict=True):
        checks = {
            "index": segment.index,
            "codec_id": segment.codec_id,
            "package_bytes": segment.package.size,
            "package_sha256": segment.package.sha256,
        }
        for name, value in checks.items():
            if record.get(name) != value:
                raise BundleError(
                    f"archive segment {segment.index} {name} differs from manifest"
                )


def _extract_payload(layout: ArchiveLayout, index: int, destination: Path) -> None:
    offset = layout.payload_offsets[index]
    length = layout.payload_lengths[index]
    digest = hashlib.sha256()
    with layout.path.open("rb") as source, destination.open("wb") as output:
        source.seek(offset)
        remaining = length
        while remaining:
            block = source.read(min(COPY_CHUNK, remaining))
            if not block:
                raise BundleError("archive ended inside a segment payload")
            output.write(block)
            digest.update(block)
            remaining -= len(block)
    expected = layout.header["segments"][index]["payload_sha256"]
    observed = digest.hexdigest()
    if observed != expected:
        raise BundleError(
            f"segment {index} payload SHA-256 mismatch: expected {expected}, observed {observed}"
        )


def compress_bundle(
    spec: BundleSpec,
    input_path: Path,
    archive_path: Path,
    *,
    verify_roundtrip: bool = False,
    verify_determinism: bool = False,
) -> tuple[Artifact, dict[str, Any]]:
    input_file = input_path.resolve()
    if not input_file.is_file():
        raise BundleError(f"input file does not exist: {input_file}")
    if input_file.stat().st_size != spec.raw_size:
        raise BundleError(
            f"input must be exactly {spec.raw_size} bytes, observed {input_file.stat().st_size}"
        )

    segment_records: list[dict[str, Any]] = []
    full_digest = hashlib.sha256()
    with tempfile.TemporaryDirectory(prefix="ew9-compress-") as temp_name:
        temp = Path(temp_name)
        payloads: list[Path] = []
        with input_file.open("rb") as source:
            for segment in spec.segments:
                raw_path = temp / f"segment-{segment.index}.raw"
                segment_digest = hashlib.sha256()
                with raw_path.open("wb") as raw_output:
                    _copy_n(
                        source,
                        raw_output,
                        spec.segment_size,
                        full_digest,
                        segment_digest,
                    )
                payload_path = temp / f"segment-{segment.index}.payload"
                run_codec(segment, "compress", raw_path, payload_path)
                payload_artifact = artifact_for(payload_path)

                if verify_determinism:
                    second = temp / f"segment-{segment.index}.payload.second"
                    run_codec(segment, "compress", raw_path, second)
                    if not files_equal(payload_path, second):
                        raise BundleError(
                            f"segment {segment.index} compressor is not deterministic"
                        )

                if verify_roundtrip:
                    restored = temp / f"segment-{segment.index}.restored"
                    run_codec(segment, "decompress", payload_path, restored)
                    if not files_equal(raw_path, restored):
                        raise BundleError(f"segment {segment.index} roundtrip failed")

                segment_records.append(
                    {
                        "index": segment.index,
                        "codec_id": segment.codec_id,
                        "package_bytes": segment.package.size,
                        "package_sha256": segment.package.sha256,
                        "raw_bytes": spec.segment_size,
                        "raw_sha256": segment_digest.hexdigest(),
                        "payload_bytes": payload_artifact.size,
                        "payload_sha256": payload_artifact.sha256,
                    }
                )
                payloads.append(payload_path)
            if source.read(1):
                raise BundleError("input contains bytes beyond the declared raw_size")

        header = _build_header(spec, full_digest.hexdigest(), segment_records)
        archive_artifact = write_archive(archive_path, header, payloads)

    layout = parse_archive(archive_artifact.path)
    _assert_archive_matches_manifest(layout, spec)
    score = score_layout(spec, layout)
    return archive_artifact, score


def decompress_bundle(spec: BundleSpec, archive_path: Path, output_path: Path) -> Artifact:
    layout = parse_archive(archive_path)
    _assert_archive_matches_manifest(layout, spec)
    destination = output_path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_output = destination.with_name(destination.name + ".tmp")
    full_digest = hashlib.sha256()
    total = 0
    try:
        with tempfile.TemporaryDirectory(prefix="ew9-decompress-") as temp_name:
            temp = Path(temp_name)
            with temp_output.open("wb") as output:
                for segment in spec.segments:
                    record = layout.header["segments"][segment.index]
                    payload = temp / f"segment-{segment.index}.payload"
                    restored = temp / f"segment-{segment.index}.raw"
                    _extract_payload(layout, segment.index, payload)
                    run_codec(segment, "decompress", payload, restored)
                    observed_size = restored.stat().st_size
                    if observed_size != record["raw_bytes"]:
                        raise BundleError(
                            f"segment {segment.index} raw size mismatch: "
                            f"expected {record['raw_bytes']}, observed {observed_size}"
                        )
                    observed_sha = sha256_file(restored)
                    if observed_sha != record["raw_sha256"]:
                        raise BundleError(f"segment {segment.index} raw SHA-256 mismatch")
                    with restored.open("rb") as source:
                        for block in iter(lambda: source.read(COPY_CHUNK), b""):
                            output.write(block)
                            full_digest.update(block)
                            total += len(block)
        if total != layout.header["raw_size"]:
            raise BundleError(
                f"full raw size mismatch: expected {layout.header['raw_size']}, observed {total}"
            )
        if full_digest.hexdigest() != layout.header["raw_sha256"]:
            raise BundleError("full raw SHA-256 mismatch")
        os.replace(temp_output, destination)
    finally:
        if temp_output.exists():
            temp_output.unlink()
    return artifact_for(destination)


def score_layout(spec: BundleSpec, layout: ArchiveLayout) -> dict[str, Any]:
    _assert_archive_matches_manifest(layout, spec)
    records = layout.header["segments"]
    payload_total = sum(record["payload_bytes"] for record in records)
    archive_overhead = layout.archive_size - payload_total
    segment_scores: list[dict[str, Any]] = []
    all_segments_pass = True
    for segment, record in zip(spec.segments, records, strict=True):
        score = segment.package.size + record["payload_bytes"]
        passed = score <= spec.segment_budget_bytes
        all_segments_pass = all_segments_pass and passed
        segment_scores.append(
            {
                "index": segment.index,
                "codec_id": segment.codec_id,
                "package_bytes": segment.package.size,
                "payload_bytes": record["payload_bytes"],
                "score_bytes": score,
                "budget_bytes": spec.segment_budget_bytes,
                "pass": passed,
            }
        )
    outer_and_framing = spec.outer_package.size + spec.manifest_size + archive_overhead
    outer_pass = outer_and_framing <= spec.outer_budget_bytes
    total_score = (
        layout.archive_size
        + spec.outer_package.size
        + spec.manifest_size
        + sum(segment.package.size for segment in spec.segments)
    )
    target_pass = total_score < spec.target_bytes
    return {
        "schema": "enwiki9_segment_score/v1",
        "profile": spec.profile,
        "archive_bytes": layout.archive_size,
        "archive_sha256": layout.archive_sha256,
        "manifest_bytes": spec.manifest_size,
        "manifest_sha256": spec.manifest_sha256,
        "outer_package_bytes": spec.outer_package.size,
        "outer_package_sha256": spec.outer_package.sha256,
        "payload_total_bytes": payload_total,
        "archive_overhead_bytes": archive_overhead,
        "outer_and_framing_bytes": outer_and_framing,
        "outer_budget_bytes": spec.outer_budget_bytes,
        "outer_pass": outer_pass,
        "segments": segment_scores,
        "all_segments_pass": all_segments_pass,
        "total_score_bytes": total_score,
        "target_bytes_exclusive": spec.target_bytes,
        "target_pass": target_pass,
        "below_107000000": total_score < 107_000_000,
        "overall_pass": all_segments_pass and outer_pass and target_pass,
    }


def make_certificate(
    spec: BundleSpec,
    input_path: Path,
    archive_path: Path,
    certificate_path: Path,
) -> dict[str, Any]:
    archive, score = compress_bundle(
        spec,
        input_path,
        archive_path,
        verify_roundtrip=True,
        verify_determinism=True,
    )
    with tempfile.TemporaryDirectory(prefix="ew9-certificate-") as temp_name:
        restored = Path(temp_name) / "restored.raw"
        restored_artifact = decompress_bundle(spec, archive.path, restored)
        input_artifact = artifact_for(input_path)
        if not files_equal(input_artifact.path, restored_artifact.path):
            raise BundleError("full archive roundtrip differs from the input")
    certificate = {
        "schema": CERTIFICATE_SCHEMA,
        "program_version": PROGRAM_VERSION,
        "profile": spec.profile,
        "manifest": {
            "bytes": spec.manifest_size,
            "sha256": spec.manifest_sha256,
            "path": str(spec.manifest_path),
        },
        "input": {
            "bytes": input_artifact.size,
            "sha256": input_artifact.sha256,
        },
        "archive": {
            "bytes": archive.size,
            "sha256": archive.sha256,
        },
        "proof": {
            "all_segment_roundtrips": True,
            "all_segment_reencodes_identical": True,
            "full_roundtrip": True,
            "archive_footer_digest": True,
            "package_hashes_bound": True,
        },
        "score": score,
    }
    data = json.dumps(certificate, indent=2, sort_keys=True) + "\n"
    target = certificate_path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data, encoding="utf-8")
    return certificate


def deterministic_zip(source_dir: Path, output_path: Path) -> Artifact:
    root = source_dir.resolve()
    if not root.is_dir():
        raise BundleError(f"source directory does not exist: {root}")
    members: list[Path] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise BundleError(f"symlinks are forbidden in deterministic packages: {path}")
        if path.is_file():
            members.append(path)
    members.sort(key=lambda item: item.relative_to(root).as_posix())
    target = output_path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    try:
        with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_STORED) as archive:
            for path in members:
                relative = path.relative_to(root).as_posix()
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                mode = 0o755 if os.access(path, os.X_OK) else 0o644
                info.external_attr = ((stat.S_IFREG | mode) & 0xFFFF) << 16
                info.compress_type = zipfile.ZIP_STORED
                archive.writestr(info, path.read_bytes())
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()
    return artifact_for(target)


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=PROGRAM_VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_manifest(p: argparse.ArgumentParser) -> None:
        p.add_argument("--manifest", type=Path, required=True)
        p.add_argument(
            "--competition-profile",
            action="store_true",
            help="require the exact five-by-200MB target profile",
        )

    compress = sub.add_parser("compress", help="create one five-segment archive")
    add_manifest(compress)
    compress.add_argument("--input", type=Path, required=True)
    compress.add_argument("--archive", type=Path, required=True)
    compress.add_argument("--verify-roundtrip", action="store_true")
    compress.add_argument("--verify-determinism", action="store_true")

    decompress = sub.add_parser("decompress", help="decode and verify one archive")
    add_manifest(decompress)
    decompress.add_argument("--archive", type=Path, required=True)
    decompress.add_argument("--output", type=Path, required=True)

    certify = sub.add_parser(
        "certify", help="double-encode, roundtrip, decode, score, and write a certificate"
    )
    add_manifest(certify)
    certify.add_argument("--input", type=Path, required=True)
    certify.add_argument("--archive", type=Path, required=True)
    certify.add_argument("--certificate", type=Path, required=True)

    inspect = sub.add_parser("inspect", help="show a verified archive header")
    inspect.add_argument("--archive", type=Path, required=True)

    score = sub.add_parser("score", help="calculate exact package-plus-archive score")
    add_manifest(score)
    score.add_argument("--archive", type=Path, required=True)

    pack = sub.add_parser(
        "pack-directory",
        help="create a deterministic stored ZIP package from a directory",
    )
    pack.add_argument("--source", type=Path, required=True)
    pack.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "pack-directory":
            artifact = deterministic_zip(args.source, args.output)
            _print_json(
                {"path": str(artifact.path), "bytes": artifact.size, "sha256": artifact.sha256}
            )
            return 0

        if args.command == "inspect":
            layout = parse_archive(args.archive)
            _print_json(
                {
                    "archive_bytes": layout.archive_size,
                    "archive_sha256": layout.archive_sha256,
                    "header": layout.header,
                }
            )
            return 0

        spec = load_bundle_spec(args.manifest)
        if args.competition_profile:
            validate_enwiki9_competition_profile(spec)

        if args.command == "compress":
            archive, score = compress_bundle(
                spec,
                args.input,
                args.archive,
                verify_roundtrip=args.verify_roundtrip,
                verify_determinism=args.verify_determinism,
            )
            _print_json(
                {
                    "archive": {
                        "path": str(archive.path),
                        "bytes": archive.size,
                        "sha256": archive.sha256,
                    },
                    "score": score,
                }
            )
            return 0

        if args.command == "decompress":
            output = decompress_bundle(spec, args.archive, args.output)
            _print_json(
                {"output": {"path": str(output.path), "bytes": output.size, "sha256": output.sha256}}
            )
            return 0

        if args.command == "certify":
            certificate = make_certificate(
                spec, args.input, args.archive, args.certificate
            )
            _print_json(certificate)
            return 0

        if args.command == "score":
            layout = parse_archive(args.archive)
            _print_json(score_layout(spec, layout))
            return 0

        parser.error("unknown command")
    except (BundleError, OSError, zipfile.BadZipFile) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
