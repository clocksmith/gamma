#!/usr/bin/env python3
"""Verify conservative source-labelled CMIX memory attribution evidence.

This tool is offline and never launches or signals a codec. It verifies that a
receipt's allocation-range counts and aggregates can be recomputed from two
retained, PFN-free page-state byte streams.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


SCHEMA = "cmix-source-labelled-memory-attribution-verification.v1"
CANDIDATE = "cmix_obias_source_labelled_memory_attribution_q0_v1"
SUCCESSOR = "cmix_obias_filebacked_fxcm_allocator_strategy_q0_v1"
REQUIRED_REDUCTION_KIB = 1_472_880
UINT64_LIMIT = 1 << 64
FXCM_LABELS = {"fxcm_alloc", "fxcm_aligned_alloc"}
REQUIRED_LABELS = {
    "fxcm_alloc",
    "fxcm_aligned_alloc",
    "context_history",
    "context_shared_map",
    "context_indirect_1",
    "context_indirect_2",
    "context_indirect_3",
    "mixer_slab",
    "ppm_anonymous_arena",
    "ppm_file_backed_arena",
}


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


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def require_int(value: Any, name: str, errors: list[str], minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{name} is not an integer")
        return minimum
    if value < minimum:
        errors.append(f"{name} is below {minimum}")
    return value


def object_field(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} is not an object")
        return {}
    return value


def array_field(value: Any, name: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{name} is not an array")
        return []
    return value


def page_counts(segment_one: bytes, segment_two: bytes, name: str, errors: list[str]) -> tuple[int, int, int, int]:
    if len(segment_one) != len(segment_two):
        errors.append(f"{name} page-state segments differ in length")
        return 0, 0, 0, 0
    one = 0
    two = 0
    intersection = 0
    union = 0
    for index, (state_one, state_two) in enumerate(zip(segment_one, segment_two)):
        if state_one & ~0x03:
            errors.append(f"{name} read one page {index} has reserved bits set")
        if state_two & ~0x03:
            errors.append(f"{name} read two page {index} has reserved bits set")
        if state_one == 0x03:
            errors.append(f"{name} read one page {index} is both present and swapped")
        if state_two == 0x03:
            errors.append(f"{name} read two page {index} is both present and swapped")
        present_one = bool(state_one & 0x01)
        present_two = bool(state_two & 0x01)
        one += int(present_one)
        two += int(present_two)
        intersection += int(present_one and present_two)
        union += int(present_one or present_two)
    return one, two, intersection, union


def verify(args: argparse.Namespace) -> tuple[dict[str, Any], bool]:
    errors: list[str] = []
    receipt, _ = load_json(args.receipt)
    manifest, manifest_raw = load_json(args.manifest)
    managed_verification, managed_verification_raw = load_json(args.managed_lease_verification)
    managed_transition_raw = args.managed_lease_transition_log.read_bytes()
    terminal_managed_lease_raw = args.terminal_managed_lease.read_bytes()
    read_one = args.read_one.read_bytes()
    read_two = args.read_two.read_bytes()

    require(receipt.get("schema_version") == "cmix-source-labelled-memory-attribution-receipt.v1", "receipt schema_version mismatch", errors)
    require(receipt.get("candidate_id") == CANDIDATE, "receipt candidate_id mismatch", errors)
    require(manifest.get("schema_version") == "cmix-allocation-range-page-state-manifest.v1", "manifest schema_version mismatch", errors)
    require(manifest.get("candidate_id") == CANDIDATE, "manifest candidate_id mismatch", errors)
    require(
        manifest.get("encoding")
        == "one byte per fully contained page: bit 0 present, bit 1 swapped, bits 2 through 7 zero",
        "manifest page-state encoding mismatch",
        errors,
    )

    identity = object_field(receipt.get("identity"), "receipt.identity", errors)
    evidence = object_field(receipt.get("evidence"), "receipt.evidence", errors)
    high_water = object_field(receipt.get("high_water"), "receipt.high_water", errors)
    decision = object_field(receipt.get("decision"), "receipt.decision", errors)
    invalidity = object_field(receipt.get("invalidity"), "receipt.invalidity", errors)
    sequence = object_field(receipt.get("sequence"), "receipt.sequence", errors)
    managed_computed = object_field(
        managed_verification.get("computed"),
        "managed lease verification computed",
        errors,
    )

    managed_verification_sha256 = sha256_bytes(managed_verification_raw)
    managed_transition_sha256 = sha256_bytes(managed_transition_raw)
    terminal_managed_lease_sha256 = sha256_bytes(terminal_managed_lease_raw)
    require(
        evidence.get("managed_lease_verification_sha256") == managed_verification_sha256,
        "managed lease verification SHA-256 mismatch",
        errors,
    )
    require(
        evidence.get("managed_lease_transition_log_sha256") == managed_transition_sha256,
        "managed lease transition-log SHA-256 mismatch",
        errors,
    )
    require(
        evidence.get("terminal_managed_lease_sha256") == terminal_managed_lease_sha256,
        "terminal managed lease SHA-256 mismatch",
        errors,
    )
    require(evidence.get("managed_lease_verification_pass") is True, "receipt does not declare a passing managed lease verification", errors)
    require(
        managed_verification.get("schema_version") == "managed-exclusive-lease-verification.v1",
        "managed lease verification schema mismatch",
        errors,
    )
    require(managed_verification.get("candidate_id") == CANDIDATE, "managed lease verification candidate mismatch", errors)
    require(managed_verification.get("verified") is True, "managed lease verification did not pass", errors)
    require(managed_verification.get("errors") == [], "managed lease verification contains errors", errors)
    require(
        managed_computed.get("transition_log_sha256") == managed_transition_sha256,
        "managed lease verification transition hash mismatch",
        errors,
    )
    require(
        managed_computed.get("terminal_lease_sha256") == terminal_managed_lease_sha256,
        "managed lease verification terminal hash mismatch",
        errors,
    )

    require(evidence.get("pagemap_range_manifest_sha256") == sha256_bytes(manifest_raw), "manifest SHA-256 mismatch", errors)
    one_sha = sha256_bytes(read_one)
    two_sha = sha256_bytes(read_two)
    manifest_one = object_field(manifest.get("read_one"), "manifest.read_one", errors)
    manifest_two = object_field(manifest.get("read_two"), "manifest.read_two", errors)
    require(manifest_one.get("sha256") == one_sha, "read one SHA-256 mismatch", errors)
    require(manifest_two.get("sha256") == two_sha, "read two SHA-256 mismatch", errors)
    require(high_water.get("pagemap_read_one_sha256") == one_sha, "receipt read one SHA-256 mismatch", errors)
    require(high_water.get("pagemap_read_two_sha256") == two_sha, "receipt read two SHA-256 mismatch", errors)
    require(manifest_one.get("basename") == os.path.basename(args.read_one), "read one basename mismatch", errors)
    require(manifest_two.get("basename") == os.path.basename(args.read_two), "read two basename mismatch", errors)
    require_int(manifest_one.get("bytes"), "manifest.read_one.bytes", errors)
    require_int(manifest_two.get("bytes"), "manifest.read_two.bytes", errors)
    require(manifest_one.get("bytes") == len(read_one), "read one byte length mismatch", errors)
    require(manifest_two.get("bytes") == len(read_two), "read two byte length mismatch", errors)

    total_entries = require_int(manifest.get("total_page_entries"), "manifest.total_page_entries", errors)
    require(len(read_one) == total_entries, "read one length does not equal total_page_entries", errors)
    require(len(read_two) == total_entries, "read two length does not equal total_page_entries", errors)
    page_size = require_int(manifest.get("page_size_bytes"), "manifest.page_size_bytes", errors, 1)
    require(page_size % 1024 == 0, "page_size_bytes is not an integral KiB count", errors)
    page_kib = page_size // 1024 if page_size else 0
    require(high_water.get("page_size_bytes") == page_size, "receipt page size mismatch", errors)
    require(manifest.get("codec_pid") == identity.get("codec_pid"), "codec PID mismatch", errors)
    require(manifest.get("codec_proc_start_ticks") == identity.get("codec_proc_start_ticks"), "codec proc_start_ticks mismatch", errors)
    require(manifest.get("attribution_checkpoint_index") == high_water.get("attribution_checkpoint_index"), "checkpoint index mismatch", errors)

    manifest_allocations = array_field(manifest.get("allocations"), "manifest.allocations", errors)
    receipt_ranges = array_field(receipt.get("allocation_ranges"), "receipt.allocation_ranges", errors)
    receipt_by_sequence: dict[int, dict[str, Any]] = {}
    for index, raw_range in enumerate(receipt_ranges):
        record = object_field(raw_range, f"receipt.allocation_ranges[{index}]", errors)
        sequence_id = require_int(record.get("allocation_sequence"), f"receipt range {index} sequence", errors, 1)
        if sequence_id in receipt_by_sequence:
            errors.append(f"duplicate receipt allocation sequence {sequence_id}")
        receipt_by_sequence[sequence_id] = record

    expected_offset = 0
    previous_sequence = 0
    seen_sequences: set[int] = set()
    label_aggregate: dict[str, dict[str, int]] = defaultdict(lambda: {
        "count": 0,
        "bytes": 0,
        "pages": 0,
        "lower_kib": 0,
        "upper_kib": 0,
    })
    total_lower_kib = 0
    total_upper_kib = 0
    eligible_lower_kib = 0

    for index, raw_allocation in enumerate(manifest_allocations):
        allocation = object_field(raw_allocation, f"manifest.allocations[{index}]", errors)
        prefix = f"allocation[{index}]"
        sequence_id = require_int(allocation.get("allocation_sequence"), f"{prefix}.allocation_sequence", errors, 1)
        require(sequence_id > previous_sequence, f"{prefix} is not in strictly increasing sequence order", errors)
        previous_sequence = sequence_id
        require(sequence_id not in seen_sequences, f"duplicate manifest allocation sequence {sequence_id}", errors)
        seen_sequences.add(sequence_id)
        label = allocation.get("label")
        require(label in REQUIRED_LABELS, f"{prefix}.label is unknown", errors)
        allocation_base = require_int(allocation.get("allocation_base"), f"{prefix}.allocation_base", errors, 1)
        usable_pointer = require_int(allocation.get("usable_pointer"), f"{prefix}.usable_pointer", errors, 1)
        allocation_bytes = require_int(allocation.get("allocation_bytes"), f"{prefix}.allocation_bytes", errors, 1)
        usable_bytes = require_int(allocation.get("usable_bytes"), f"{prefix}.usable_bytes", errors, 1)
        first_page = require_int(allocation.get("first_fully_contained_page"), f"{prefix}.first_fully_contained_page", errors)
        page_count = require_int(allocation.get("fully_contained_pages"), f"{prefix}.fully_contained_pages", errors)
        offset = require_int(allocation.get("entry_offset"), f"{prefix}.entry_offset", errors)
        require(offset == expected_offset, f"{prefix}.entry_offset is not contiguous", errors)
        expected_offset += page_count
        require(allocation_base < UINT64_LIMIT, f"{prefix} allocation base exceeds uint64 address space", errors)
        require(usable_pointer < UINT64_LIMIT, f"{prefix} usable pointer exceeds uint64 address space", errors)
        require(allocation_bytes <= UINT64_LIMIT - min(allocation_base, UINT64_LIMIT), f"{prefix} allocation range overflows uint64", errors)
        require(usable_bytes <= UINT64_LIMIT - min(usable_pointer, UINT64_LIMIT), f"{prefix} usable range overflows uint64", errors)
        allocation_end = allocation_base + allocation_bytes
        usable_end = usable_pointer + usable_bytes
        require(allocation_base <= usable_pointer, f"{prefix} usable pointer precedes allocation base", errors)
        require(usable_end <= allocation_end, f"{prefix} usable range exceeds allocation range", errors)
        computed_first_page = (usable_pointer + page_size - 1) // page_size
        computed_end_page = usable_end // page_size
        computed_pages = max(0, computed_end_page - computed_first_page)
        require(first_page == computed_first_page, f"{prefix} first fully contained page mismatch", errors)
        require(page_count == computed_pages, f"{prefix} fully contained page count mismatch", errors)
        require(offset + page_count <= len(read_one), f"{prefix} page-state range exceeds evidence", errors)
        segment_one = read_one[offset:offset + page_count]
        segment_two = read_two[offset:offset + page_count]
        count_one, count_two, intersection, union = page_counts(segment_one, segment_two, prefix, errors)
        lower_kib = intersection * page_kib
        upper_kib = union * page_kib
        record = receipt_by_sequence.get(sequence_id)
        require(record is not None, f"receipt lacks allocation sequence {sequence_id}", errors)
        if record is not None:
            equality_fields = (
                "label",
                "allocation_base",
                "usable_pointer",
                "allocation_bytes",
                "usable_bytes",
                "first_fully_contained_page",
                "fully_contained_pages",
                "vma_containment_pass",
                "eligible_for_memory_successor",
            )
            for field in equality_fields:
                require(record.get(field) == allocation.get(field), f"receipt allocation {sequence_id} {field} mismatch", errors)
            expected_counts = {
                "present_read_one_pages": count_one,
                "present_read_two_pages": count_two,
                "present_intersection_pages": intersection,
                "present_union_pages": union,
                "resident_lower_bound_kib": lower_kib,
                "resident_upper_bound_kib": upper_kib,
            }
            for field, expected in expected_counts.items():
                require(record.get(field) == expected, f"receipt allocation {sequence_id} {field} mismatch", errors)
            require(record.get("live_at_checkpoint") is True, f"receipt allocation {sequence_id} is not live", errors)
            require(record.get("marker_window_exact") is True, f"receipt allocation {sequence_id} marker window is not exact", errors)
            bound_valid = allocation.get("vma_containment_pass") is True
            require(record.get("conservative_range_bound_valid") is bound_valid, f"receipt allocation {sequence_id} bound-valid flag mismatch", errors)
        aggregate = label_aggregate[str(label)]
        aggregate["count"] += 1
        aggregate["bytes"] += allocation_bytes
        aggregate["pages"] += page_count
        if allocation.get("vma_containment_pass") is True:
            aggregate["lower_kib"] += lower_kib
            aggregate["upper_kib"] += upper_kib
            total_lower_kib += lower_kib
            total_upper_kib += upper_kib
            if label in FXCM_LABELS and allocation.get("eligible_for_memory_successor") is True:
                eligible_lower_kib += lower_kib

    require(expected_offset == total_entries, "allocation entry ranges do not consume total_page_entries", errors)
    require(set(receipt_by_sequence) == seen_sequences, "receipt and manifest allocation sequence sets differ", errors)

    source_labels = array_field(receipt.get("source_labels"), "receipt.source_labels", errors)
    labels_by_name: dict[str, dict[str, Any]] = {}
    for index, raw_label in enumerate(source_labels):
        label_record = object_field(raw_label, f"receipt.source_labels[{index}]", errors)
        label = label_record.get("label")
        require(label in REQUIRED_LABELS, f"source label {index} is unknown", errors)
        if label in labels_by_name:
            errors.append(f"duplicate source label {label}")
        labels_by_name[str(label)] = label_record
    require(set(labels_by_name) == REQUIRED_LABELS, "source label set is incomplete", errors)
    for label in sorted(REQUIRED_LABELS):
        record = labels_by_name.get(label, {})
        aggregate = label_aggregate[label]
        require(record.get("allocation_count") == aggregate["count"], f"source label {label} allocation_count mismatch", errors)
        require(record.get("live_at_high_water_count") == aggregate["count"], f"source label {label} live count mismatch", errors)
        require(record.get("allocation_bytes") == aggregate["bytes"], f"source label {label} allocation_bytes mismatch", errors)
        require(record.get("fully_contained_pages") == aggregate["pages"], f"source label {label} page count mismatch", errors)
        require(record.get("resident_lower_bound_at_checkpoint_kib") == aggregate["lower_kib"], f"source label {label} lower bound mismatch", errors)
        require(record.get("resident_upper_bound_at_checkpoint_kib") == aggregate["upper_kib"], f"source label {label} upper bound mismatch", errors)
        require(record.get("conservative_range_bound_valid") is True, f"source label {label} bound is not valid", errors)
        if aggregate["count"] == 0:
            require(isinstance(record.get("not_allocated_reason"), str) and bool(record.get("not_allocated_reason")), f"source label {label} lacks not-allocated reason", errors)

    require(high_water.get("labelled_resident_lower_bound_kib") == total_lower_kib, "high-water labelled lower bound mismatch", errors)
    require(high_water.get("labelled_resident_upper_bound_kib") == total_upper_kib, "high-water labelled upper bound mismatch", errors)
    codec_rss_kib = require_int(high_water.get("codec_rss_kib"), "high_water.codec_rss_kib", errors)
    unattributed_upper = max(0, codec_rss_kib - total_lower_kib)
    require(high_water.get("unattributed_codec_rss_upper_bound_kib") == unattributed_upper, "unattributed codec RSS upper bound mismatch", errors)
    require(decision.get("eligible_reclaimable_kib") == eligible_lower_kib, "decision eligible reclaimable lower bound mismatch", errors)
    require(decision.get("required_reduction_kib") == REQUIRED_REDUCTION_KIB, "decision required reduction mismatch", errors)

    require(sequence.get("contiguous") is True, "marker sequence is not contiguous", errors)
    require(sequence.get("registry_healthy") is True, "marker registry is not healthy", errors)
    require(sequence.get("unmatched_releases") == 0, "marker releases are unmatched", errors)
    for field in ("process_tree_stopped", "marker_window_exact", "pagemap_permission_pass", "smaps_reconciled", "coherent_checkpoint"):
        require(high_water.get(field) is True, f"high_water.{field} is not true", errors)
    require(high_water.get("continuous_peak_ownership_claimed") is False, "continuous peak ownership is overclaimed", errors)

    checkpoint_evidence_pass = not errors
    successor_should_be_authorized = checkpoint_evidence_pass and eligible_lower_kib >= REQUIRED_REDUCTION_KIB
    if successor_should_be_authorized:
        require(invalidity.get("invalid") is False, "receipt invalidity flag is true", errors)
        require(decision.get("status") == "attributed", "decision status is not attributed", errors)
        require(decision.get("successor_authorized") == SUCCESSOR, "file-backed FXCM successor is not authorized", errors)
    else:
        require(decision.get("successor_authorized") is None, "successor is authorized without sufficient verified evidence", errors)
        if errors:
            require(invalidity.get("invalid") is True, "invalid receipt does not set invalidity.invalid", errors)
            require(decision.get("status") == "invalid", "invalid receipt status is not invalid", errors)
        else:
            require(invalidity.get("invalid") is False, "insufficient receipt is marked invalid", errors)
            require(decision.get("status") == "insufficient_attribution", "insufficient receipt status mismatch", errors)

    verified = not errors
    output = {
        "schema_version": SCHEMA,
        "candidate_id": CANDIDATE,
        "verified": verified,
        "computed": {
            "allocation_ranges": len(manifest_allocations),
            "page_entries": total_entries,
            "labelled_resident_lower_bound_kib": total_lower_kib,
            "labelled_resident_upper_bound_kib": total_upper_kib,
            "eligible_fxcm_reclaimable_lower_bound_kib": eligible_lower_kib,
            "required_reduction_kib": REQUIRED_REDUCTION_KIB,
            "successor_should_be_authorized": successor_should_be_authorized,
        },
        "errors": errors,
    }
    return output, verified


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--read-one", required=True, type=Path)
    parser.add_argument("--read-two", required=True, type=Path)
    parser.add_argument("--managed-lease-verification", required=True, type=Path)
    parser.add_argument("--managed-lease-transition-log", required=True, type=Path)
    parser.add_argument("--terminal-managed-lease", required=True, type=Path)
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
