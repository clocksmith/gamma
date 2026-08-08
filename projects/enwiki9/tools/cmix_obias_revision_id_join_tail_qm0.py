#!/usr/bin/env python3
"""Certify a side-free revision-ID join for the public cmix-obias P0 tail."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

import cmix_obias_title_join_tail_qm0 as title_join


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_revision_id_join_tail_qm0_v1"
SCHEMA = "cmix_obias_revision_id_join_tail_qm0_decision_v1"
TARGET_BYTES = 105_000_000
PUBLIC_EXTERNAL_TOTAL = 108_492_825
PUBLIC_ENCODED_SIDE_BYTES = 346_948
GAMMA_FORECAST = 109_389_323


def atomic_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def digest_ints(values: list[int]) -> str:
    return title_join.sha256_bytes(
        b"".join(value.to_bytes(8, "little") for value in values)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artifact-root",
        type=pathlib.Path,
        default=pathlib.Path(
            "/home/x/enwiki9-nonproof/cmix_lex_payload_gate/"
            "cmix_lex_payload_transfer_v1_retry2"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=PROJECT_ROOT / "results" / CANDIDATE_ID,
    )
    args = parser.parse_args()

    artifact_root = args.artifact_root.resolve()
    output_dir = args.output_dir.resolve()
    original = artifact_root / "original_ready.bin"
    transformed = artifact_root / "transformed_ready.bin"
    side = artifact_root / "extracted_payload_side.bin"
    main_reordered = artifact_root / "work" / ".main_reordered"
    title_join.require_file(
        original,
        title_join.ORIGINAL_READY_BYTES,
        title_join.ORIGINAL_READY_SHA256,
    )
    title_join.require_file(
        transformed,
        title_join.TRANSFORMED_READY_BYTES,
        title_join.TRANSFORMED_READY_SHA256,
    )
    title_join.require_file(side, title_join.SIDE_BYTES, title_join.SIDE_SHA256)
    title_join.require_file(
        main_reordered,
        title_join.MAIN_REORDERED_BYTES,
        title_join.MAIN_REORDERED_SHA256,
    )

    transfer_receipt = (
        PROJECT_ROOT / "results" / "cmix_lex_payload_transfer_v1_retry2" / "decision.json"
    )
    title_receipt = (
        PROJECT_ROOT / "results" / "cmix_obias_title_join_tail_qm0_v1" / "decision.json"
    )
    if not transfer_receipt.is_file() or not title_receipt.is_file():
        raise FileNotFoundError("required predecessor decision receipt is absent")
    transfer = json.loads(transfer_receipt.read_text())
    compressed_side = transfer.get("constants", {}).get("public_compressed_side_bytes")
    if compressed_side != PUBLIC_ENCODED_SIDE_BYTES:
        raise RuntimeError(f"predecessor side accounting mismatch: {compressed_side}")

    page_titles, page_revisions = title_join.parse_pages(main_reordered)
    if len(page_revisions) != title_join.EXPECTED_PAGES:
        raise RuntimeError(f"unexpected page count: {len(page_revisions)}")

    with original.open("rb") as source:
        source.seek(title_join.REGIME1_ABSOLUTE)
        original_regime = source.read(title_join.REGIME1_LENGTH)
    with transformed.open("rb") as source:
        source.seek(title_join.REGIME1_ABSOLUTE)
        public_regime = source.read(title_join.REGIME1_LENGTH)
    if len(original_regime) != title_join.REGIME1_LENGTH:
        raise RuntimeError("short original regime read")
    if len(public_regime) != title_join.REGIME1_LENGTH:
        raise RuntimeError("short public regime read")

    original_prelude, original_blocks, original_suffix = title_join.parse_regime(
        original_regime
    )
    public_prelude, public_blocks, public_suffix = title_join.parse_regime(public_regime)
    if len(original_blocks) != title_join.EXPECTED_PAGES:
        raise RuntimeError(f"unexpected original block count: {len(original_blocks)}")
    if len(public_blocks) != title_join.EXPECTED_PAGES:
        raise RuntimeError(f"unexpected public block count: {len(public_blocks)}")

    original_revisions = [title_join.block_revision(block) for block in original_blocks]
    public_revisions = [title_join.block_revision(block) for block in public_blocks]
    page_ids_unique = len(set(page_revisions)) == len(page_revisions)
    original_ids_unique = len(set(original_revisions)) == len(original_revisions)
    public_ids_unique = len(set(public_revisions)) == len(public_revisions)
    positional_alignment = original_revisions == page_revisions
    id_sets_equal = set(page_revisions) == set(public_revisions)
    framing_equal = (
        original_prelude == public_prelude and original_suffix == public_suffix
    )
    preconditions = {
        "page_ids_unique": page_ids_unique,
        "original_block_ids_unique": original_ids_unique,
        "public_block_ids_unique": public_ids_unique,
        "positional_original_page_alignment": positional_alignment,
        "public_page_id_sets_equal": id_sets_equal,
        "framing_equal": framing_equal,
        "unique_page_id_count": len(set(page_revisions)),
        "unique_original_block_id_count": len(set(original_revisions)),
        "unique_public_block_id_count": len(set(public_revisions)),
    }
    if not all(value is True for value in preconditions.values() if isinstance(value, bool)):
        raise RuntimeError(f"revision-ID join precondition failed: {preconditions}")

    page_index_by_revision = {
        revision: index for index, revision in enumerate(page_revisions)
    }
    restored_blocks: list[bytes | None] = [None] * len(public_blocks)
    for block, revision in zip(public_blocks, public_revisions, strict=True):
        page_index = page_index_by_revision[revision]
        if restored_blocks[page_index] is not None:
            raise RuntimeError(f"duplicate public assignment for revision {revision}")
        restored_blocks[page_index] = block
    if any(block is None for block in restored_blocks):
        raise RuntimeError("revision-ID join omitted a page")
    restored_regime = b"".join(
        [
            *public_prelude,
            *(block for block in restored_blocks if block is not None),
            *public_suffix,
        ]
    )
    inverse_exact = restored_regime == original_regime

    payload_order = sorted(
        range(len(original_blocks)),
        key=lambda index: (title_join.block_sort_key(original_blocks[index]), index),
    )
    rebuilt_public = title_join.render_regime(
        original_prelude,
        original_blocks,
        original_suffix,
        payload_order,
    )
    public_rebuild_identity = rebuilt_public == public_regime
    block_identity_by_revision = all(
        restored_blocks[index] == original_blocks[index]
        for index in range(len(original_blocks))
    )
    if not inverse_exact or not public_rebuild_identity or not block_identity_by_revision:
        raise RuntimeError("revision-ID join failed exact reconstruction")

    side_free_external_total = PUBLIC_EXTERNAL_TOTAL - PUBLIC_ENCODED_SIDE_BYTES
    decision = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "status": "terminal",
        "evidence_tier": "oracle",
        "inputs": {
            "artifact_root": str(artifact_root),
            "original_ready_bytes": title_join.ORIGINAL_READY_BYTES,
            "original_ready_sha256": title_join.ORIGINAL_READY_SHA256,
            "transformed_ready_bytes": title_join.TRANSFORMED_READY_BYTES,
            "transformed_ready_sha256": title_join.TRANSFORMED_READY_SHA256,
            "side_bytes": title_join.SIDE_BYTES,
            "side_sha256": title_join.SIDE_SHA256,
            "main_reordered_bytes": title_join.MAIN_REORDERED_BYTES,
            "main_reordered_sha256": title_join.MAIN_REORDERED_SHA256,
            "transfer_receipt": transfer_receipt.relative_to(PROJECT_ROOT).as_posix(),
            "transfer_receipt_sha256": title_join.sha256_file(transfer_receipt),
            "title_join_receipt": title_receipt.relative_to(PROJECT_ROOT).as_posix(),
            "title_join_receipt_sha256": title_join.sha256_file(title_receipt),
        },
        "scope": {
            "population": "all complete pages and all public payload_lex regime-1 metadata blocks",
            "regime_bytes": title_join.REGIME1_LENGTH,
            "complete_pages": len(page_titles),
            "original_blocks": len(original_blocks),
            "public_blocks": len(public_blocks),
        },
        "association": {
            **preconditions,
            "page_revision_digest": digest_ints(page_revisions),
            "original_revision_digest": digest_ints(original_revisions),
            "public_revision_digest": digest_ints(public_revisions),
        },
        "gates": {
            "artifact_identity": True,
            "predecessor_side_accounting_bound": True,
            "framing_equal": framing_equal,
            "public_rebuild_identity": public_rebuild_identity,
            "block_identity_by_revision": block_identity_by_revision,
            "revision_join_inverse_exact": inverse_exact,
            "replacement_permutation_bytes": 0,
            "join_key_decoder_visible_at_restore_stage": False,
        },
        "decoder_stage_audit": {
            "current_restore_stage": "after arithmetic decode; before WRT decode and PHDA9 restore",
            "page_revision_observation_stage": "pre-PHDA9 .main_reordered construction artifact",
            "page_revision_ids_present_in_decoded_page_body_at_restore_stage": False,
            "causal_join_available": False,
            "reason": (
                "PHDA9 removes revision metadata into the tail being reordered; the "
                "current decoder must restore that tail before it can reconstruct page IDs."
            ),
        },
        "accounting": {
            "target_bytes": TARGET_BYTES,
            "public_external_total_bytes": PUBLIC_EXTERNAL_TOTAL,
            "public_encoded_side_bytes": PUBLIC_ENCODED_SIDE_BYTES,
            "side_free_external_total_before_source_delta_bytes": side_free_external_total,
            "side_free_external_target_distance_before_source_delta_bytes": (
                side_free_external_total - TARGET_BYTES
            ),
            "gamma_source_bound_forecast_bytes": GAMMA_FORECAST,
            "gamma_target_debt_bytes": GAMMA_FORECAST - TARGET_BYTES,
            "conditional_gross_side_opportunity_bytes": PUBLIC_ENCODED_SIDE_BYTES,
            "gross_side_removal_authorized": False,
            "gamma_forecast_change_authorized": False,
            "score_credit_bytes": 0,
        },
        "decision": {
            "verdict": "BLOCKED_DECODER_AVAILABILITY",
            "scientific_valid": True,
            "score_credit_bytes": 0,
            "forecast_change_authorized": False,
            "next_action": (
                "Do not implement the zero-side source child. First find a join key that is "
                "causally available before PHDA9 tail restoration, or transmit a cheaper "
                "source-bound mapping and prove its counted net gain."
            ),
            "blocked_reason": (
                "The exact revision-ID association uses IDs reconstructed from the same "
                "metadata blocks; they are not decoder-visible at the current restore point."
            ),
        },
    }
    atomic_json(output_dir / "decision.json", decision)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
