#!/usr/bin/env python3
"""Offline verifier for Gamma parent-fallback archive selection receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO


SCHEMA = "gamma-parent-fallback-archive-select-verification.v1"
CANDIDATE = "gamma_parent_fallback_archive_select_q0_v1"
MAGIC = b"GAFS"
VERSION = 1
HEADER_BYTES = 14
SCORE_LIMIT_BYTES = 105_000_000
MEMORY_LIMIT_BYTES = 10_000_000_000
CHUNK_BYTES = 8 * 1024 * 1024


class VerificationError(Exception):
    pass


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"JSON root is not an object: {path}")
    return value, raw


def sha256_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return size, digest.hexdigest()


def equal_streams(left: BinaryIO, right: BinaryIO, length: int | None = None) -> bool:
    remaining = length
    while remaining is None or remaining > 0:
        request = CHUNK_BYTES if remaining is None else min(CHUNK_BYTES, remaining)
        left_chunk = left.read(request)
        right_chunk = right.read(request)
        if left_chunk != right_chunk:
            return False
        if not left_chunk:
            return remaining in (None, 0)
        if remaining is not None:
            remaining -= len(left_chunk)
    return True


def files_equal(left_path: Path, right_path: Path) -> bool:
    if left_path.stat().st_size != right_path.stat().st_size:
        return False
    with left_path.open("rb") as left, right_path.open("rb") as right:
        return equal_streams(left, right)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def object_field(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} is not an object")
        return {}
    return value


def normalized_package_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return None
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        return None
    if not encoded or value.startswith("/") or "//" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        return None
    return path.as_posix() if path.as_posix() == value else None


def verify_package_root(root: Path, manifest: dict[str, Any], errors: list[str]) -> int:
    require(manifest.get("schema_version") == "gamma-union-package-manifest.v1", "union manifest schema mismatch", errors)
    require(manifest.get("candidate_id") == CANDIDATE, "union manifest candidate mismatch", errors)
    require(manifest.get("symlinks_allowed") is False, "union manifest permits symlinks", errors)
    require(manifest.get("hardlinks_allowed") is False, "union manifest permits hardlinks", errors)
    require(manifest.get("special_files_allowed") is False, "union manifest permits special files", errors)
    if root.is_symlink() or not root.is_dir():
        errors.append("package root is not a real directory")
        return 0

    actual: dict[str, Path] = {}
    inode_owners: dict[tuple[int, int], str] = {}
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            children = list(os.scandir(directory))
        except OSError as exc:
            errors.append(f"cannot scan package directory {directory}: {exc}")
            continue
        for child in children:
            child_path = Path(child.path)
            try:
                metadata = child.stat(follow_symlinks=False)
            except OSError as exc:
                errors.append(f"cannot stat package entry {child_path}: {exc}")
                continue
            if stat.S_ISLNK(metadata.st_mode):
                errors.append(f"package contains symlink {child_path}")
                continue
            if stat.S_ISDIR(metadata.st_mode):
                stack.append(child_path)
                continue
            if not stat.S_ISREG(metadata.st_mode):
                errors.append(f"package contains special file {child_path}")
                continue
            try:
                relative = child_path.relative_to(root).as_posix()
                relative.encode("utf-8")
            except (ValueError, UnicodeEncodeError):
                errors.append(f"package path is not canonical UTF-8: {child_path}")
                continue
            if normalized_package_path(relative) is None:
                errors.append(f"package path is unsafe: {relative!r}")
                continue
            if relative in actual:
                errors.append(f"duplicate package path {relative}")
                continue
            inode = (metadata.st_dev, metadata.st_ino)
            if metadata.st_nlink != 1 or inode in inode_owners:
                errors.append(f"package hardlink is forbidden: {relative}")
            inode_owners[inode] = relative
            if metadata.st_mode & (stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX):
                errors.append(f"package special permission bits are forbidden: {relative}")
            actual[relative] = child_path

    raw_entries = manifest.get("entries")
    if not isinstance(raw_entries, list):
        errors.append("union manifest entries is not an array")
        raw_entries = []
    manifest_entries: dict[str, dict[str, Any]] = {}
    ordered_paths: list[str] = []
    for index, raw_entry in enumerate(raw_entries):
        if not isinstance(raw_entry, dict):
            errors.append(f"union manifest entry {index} is not an object")
            continue
        path_value = raw_entry.get("path")
        normalized = normalized_package_path(path_value)
        if normalized is None:
            errors.append(f"union manifest entry {index} has unsafe path")
            continue
        if normalized in manifest_entries:
            errors.append(f"union manifest duplicates path {normalized}")
            continue
        manifest_entries[normalized] = raw_entry
        ordered_paths.append(normalized)
    try:
        byte_sorted_paths = sorted(ordered_paths, key=lambda item: item.encode("utf-8"))
    except UnicodeEncodeError:
        byte_sorted_paths = []
        errors.append("union manifest path order contains non-UTF-8 text")
    require(ordered_paths == byte_sorted_paths, "union manifest paths are not in strict UTF-8 byte order", errors)
    require(set(actual) == set(manifest_entries), "package root file set differs from union manifest", errors)

    total_bytes = 0
    for relative in sorted(set(actual) & set(manifest_entries), key=lambda item: item.encode("utf-8")):
        path = actual[relative]
        entry = manifest_entries[relative]
        before = path.stat(follow_symlinks=False)
        logical_bytes, digest = sha256_file(path)
        after = path.stat(follow_symlinks=False)
        require(
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
            f"package file changed while hashing: {relative}",
            errors,
        )
        require(entry.get("logical_bytes") == logical_bytes, f"package file size mismatch: {relative}", errors)
        require(entry.get("sha256") == digest, f"package file SHA-256 mismatch: {relative}", errors)
        executable = bool(before.st_mode & 0o111)
        require(entry.get("executable") is executable, f"package executable mode mismatch: {relative}", errors)
        roles = entry.get("roles")
        require(isinstance(roles, list) and bool(roles), f"package roles missing: {relative}", errors)
        total_bytes += logical_bytes

    require(manifest.get("file_count") == len(manifest_entries), "union manifest file_count mismatch", errors)
    require(manifest.get("total_logical_bytes") == total_bytes, "union manifest total_logical_bytes mismatch", errors)
    return total_bytes


def verify(args: argparse.Namespace) -> tuple[dict[str, Any], bool]:
    errors: list[str] = []
    receipt, _ = load_json(args.receipt)
    union_manifest, union_manifest_raw = load_json(args.union_manifest)
    verified_union_bytes = verify_package_root(args.package_root, union_manifest, errors)

    require(receipt.get("schema_version") == "gamma-parent-fallback-archive-select-receipt.v1", "receipt schema mismatch", errors)
    require(receipt.get("candidate_id") == CANDIDATE, "receipt candidate mismatch", errors)
    population = object_field(receipt.get("population"), "receipt.population", errors)
    alternatives = object_field(receipt.get("alternatives"), "receipt.alternatives", errors)
    parent = object_field(alternatives.get("P"), "receipt.alternatives.P", errors)
    candidate = object_field(alternatives.get("C"), "receipt.alternatives.C", errors)
    selection = object_field(receipt.get("selection"), "receipt.selection", errors)
    package = object_field(receipt.get("package"), "receipt.package", errors)
    resources = object_field(receipt.get("resources"), "receipt.resources", errors)
    controls = object_field(receipt.get("controls"), "receipt.controls", errors)
    decision = object_field(receipt.get("decision"), "receipt.decision", errors)

    input_size, input_sha = sha256_file(args.input)
    parent_size, parent_sha = sha256_file(args.parent_payload)
    candidate_size, candidate_sha = sha256_file(args.candidate_payload)
    frame_size, frame_sha = sha256_file(args.framed_archive)
    repeat_size, repeat_sha = sha256_file(args.repeat_framed_archive)
    parent_decoded_size, parent_decoded_sha = sha256_file(args.parent_decoded)
    candidate_decoded_size, candidate_decoded_sha = sha256_file(args.candidate_decoded)
    selected_decoded_size, selected_decoded_sha = sha256_file(args.selected_decoded)

    require(population.get("input_bytes") == input_size, "population input size mismatch", errors)
    require(population.get("input_sha256") == input_sha, "population input SHA-256 mismatch", errors)
    require(parent.get("payload_bytes") == parent_size, "parent payload size mismatch", errors)
    require(parent.get("payload_sha256") == parent_sha, "parent payload SHA-256 mismatch", errors)
    require(candidate.get("payload_bytes") == candidate_size, "candidate payload size mismatch", errors)
    require(candidate.get("payload_sha256") == candidate_sha, "candidate payload SHA-256 mismatch", errors)

    for name, record, decoded_size, decoded_sha, decoded_path in (
        ("parent", parent, parent_decoded_size, parent_decoded_sha, args.parent_decoded),
        ("candidate", candidate, candidate_decoded_size, candidate_decoded_sha, args.candidate_decoded),
    ):
        require(record.get("decoded_bytes") == decoded_size, f"{name} decoded size mismatch", errors)
        require(record.get("decoded_sha256") == decoded_sha, f"{name} decoded SHA-256 mismatch", errors)
        require(decoded_size == input_size and decoded_sha == input_sha, f"{name} decoded output is not the sealed input", errors)
        require(files_equal(decoded_path, args.input), f"{name} decoded output is not byte-identical to the sealed input", errors)

    expected_mode = "P" if parent_size <= candidate_size else "C"
    expected_mode_byte = 0 if expected_mode == "P" else 1
    selected_path = args.parent_payload if expected_mode == "P" else args.candidate_payload
    selected_size = parent_size if expected_mode == "P" else candidate_size
    selected_sha = parent_sha if expected_mode == "P" else candidate_sha

    require(frame_size >= HEADER_BYTES, "framed archive is shorter than its header", errors)
    parsed_mode: str | None = None
    payload_length = -1
    if frame_size >= HEADER_BYTES:
        with args.framed_archive.open("rb") as framed:
            header = framed.read(HEADER_BYTES)
            require(header[:4] == MAGIC, "frame magic mismatch", errors)
            require(header[4] == VERSION, "frame version mismatch", errors)
            mode_byte = header[5]
            if mode_byte == 0:
                parsed_mode = "P"
            elif mode_byte == 1:
                parsed_mode = "C"
            else:
                errors.append("frame mode byte is invalid")
            payload_length = int.from_bytes(header[6:14], "little", signed=False)
            require(payload_length == frame_size - HEADER_BYTES, "frame payload length or trailing bytes mismatch", errors)
            with selected_path.open("rb") as selected_handle:
                require(equal_streams(framed, selected_handle, payload_length), "framed payload differs from selected payload", errors)
                require(framed.read(1) == b"", "framed archive has trailing bytes", errors)
                require(selected_handle.read(1) == b"", "selected payload has bytes beyond framed payload length", errors)

    require(parsed_mode == expected_mode, "framed mode does not select the smaller payload with parent tie-break", errors)
    require(selection.get("mode") == expected_mode, "receipt selected mode mismatch", errors)
    require(selection.get("mode_byte") == expected_mode_byte, "receipt mode byte mismatch", errors)
    require(selection.get("tie_break") == "P", "receipt tie-break mismatch", errors)
    require(selection.get("selected_payload_bytes") == selected_size, "receipt selected payload size mismatch", errors)
    require(selection.get("selected_payload_sha256") == selected_sha, "receipt selected payload SHA-256 mismatch", errors)
    require(selection.get("fixed_header_bytes") == HEADER_BYTES, "receipt fixed header size mismatch", errors)
    require(frame_size == HEADER_BYTES + selected_size, "framed archive size arithmetic mismatch", errors)
    require(selection.get("framed_archive_bytes") == frame_size, "receipt framed archive size mismatch", errors)
    require(selection.get("framed_archive_sha256") == frame_sha, "receipt framed archive SHA-256 mismatch", errors)
    require(selection.get("repeat_mode") == expected_mode, "receipt repeat mode mismatch", errors)
    require(selection.get("repeat_archive_sha256") == repeat_sha, "receipt repeat archive SHA-256 mismatch", errors)
    require(repeat_size == frame_size and repeat_sha == frame_sha, "repeat archive identity mismatch", errors)
    require(files_equal(args.framed_archive, args.repeat_framed_archive), "repeat archive is not byte-identical", errors)

    require(selection.get("decoded_bytes") == selected_decoded_size, "selected decoded size mismatch", errors)
    require(selection.get("decoded_sha256") == selected_decoded_sha, "selected decoded SHA-256 mismatch", errors)
    require(selected_decoded_size == input_size and selected_decoded_sha == input_sha, "selected decoded output is not the sealed input", errors)
    require(files_equal(args.selected_decoded, args.input), "selected decoded output is not byte-identical to the sealed input", errors)

    require(package.get("union_manifest_sha256") == hashlib.sha256(union_manifest_raw).hexdigest(), "union package manifest SHA-256 mismatch", errors)
    union_bytes = package.get("union_package_bytes")
    require(isinstance(union_bytes, int) and not isinstance(union_bytes, bool) and union_bytes >= 0, "union package bytes are invalid", errors)
    require(union_bytes == verified_union_bytes, "receipt union package bytes differ from verified package root", errors)
    require(package.get("selected_archive_bytes") == frame_size, "package selected archive size mismatch", errors)
    complete_score = frame_size + verified_union_bytes
    require(package.get("complete_counted_score_bytes") == complete_score, "complete counted score arithmetic mismatch", errors)

    receipt_claims = (
        selection.get("mode_matches_recomputed") is True,
        selection.get("selection_arithmetic_pass") is True,
        selection.get("repeat_identity") is True,
        selection.get("decode_return_code") == 0,
        selection.get("exact_inverse") is True,
        parent.get("encode_return_code") == 0,
        parent.get("decode_return_code") == 0,
        parent.get("exact_inverse") is True,
        parent.get("dependency_closure_pass") is True,
        candidate.get("encode_return_code") == 0,
        candidate.get("decode_return_code") == 0,
        candidate.get("exact_inverse") is True,
        candidate.get("dependency_closure_pass") is True,
        package.get("dependencies_sealed") is True,
        package.get("untracked_inputs_empty") is True,
        resources.get("single_logical_cpu") is True,
        resources.get("process_tree_limit_bytes") == MEMORY_LIMIT_BYTES,
        isinstance(resources.get("process_tree_peak_bytes"), int),
        resources.get("process_tree_peak_bytes", MEMORY_LIMIT_BYTES + 1) <= MEMORY_LIMIT_BYTES,
        resources.get("temporary_disk_pass") is True,
        resources.get("runtime_measured") is True,
        resources.get("runtime_eligible") is True,
        resources.get("cleanup_pass") is True,
        resources.get("resource_pass") is True,
        controls.get("parent_frame_identity_pass") is True,
        controls.get("mode_flip_rejected") is True,
        controls.get("length_tamper_rejected") is True,
        controls.get("repeat_selection_pass") is True,
    )
    externally_eligible = all(receipt_claims) and complete_score <= SCORE_LIMIT_BYTES
    internally_valid = not errors
    promotion_should_be_authorized = internally_valid and externally_eligible
    if promotion_should_be_authorized:
        require(decision.get("promotion_authorized") is True, "promotion is not authorized despite passing evidence", errors)
        require(decision.get("status") == "pass", "passing decision status mismatch", errors)
    else:
        require(decision.get("promotion_authorized") is False, "promotion is authorized without passing evidence", errors)
        if errors:
            require(decision.get("status") == "invalid", "internally invalid receipt status mismatch", errors)
        else:
            require(decision.get("status") == "fail", "eligible-evidence failure status mismatch", errors)

    verified = not errors
    output = {
        "schema_version": SCHEMA,
        "candidate_id": CANDIDATE,
        "verified": verified,
        "computed": {
            "parent_payload_bytes": parent_size,
            "candidate_payload_bytes": candidate_size,
            "selected_mode": expected_mode,
            "selected_payload_bytes": selected_size,
            "framed_archive_bytes": frame_size,
            "union_package_bytes": verified_union_bytes,
            "complete_counted_score_bytes": complete_score,
            "score_limit_bytes": SCORE_LIMIT_BYTES,
            "promotion_should_be_authorized": promotion_should_be_authorized,
        },
        "errors": errors,
    }
    return output, verified


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--parent-payload", required=True, type=Path)
    parser.add_argument("--candidate-payload", required=True, type=Path)
    parser.add_argument("--framed-archive", required=True, type=Path)
    parser.add_argument("--repeat-framed-archive", required=True, type=Path)
    parser.add_argument("--parent-decoded", required=True, type=Path)
    parser.add_argument("--candidate-decoded", required=True, type=Path)
    parser.add_argument("--selected-decoded", required=True, type=Path)
    parser.add_argument("--union-manifest", required=True, type=Path)
    parser.add_argument("--package-root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        output, verified = verify(args)
    except (OSError, VerificationError) as exc:
        output = {
            "schema_version": SCHEMA,
            "candidate_id": CANDIDATE,
            "verified": False,
            "computed": None,
            "errors": [str(exc)],
        }
        verified = False
    encoded = json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n"
    if args.output is None:
        sys.stdout.write(encoded)
    else:
        args.output.write_text(encoded, encoding="utf-8")
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
