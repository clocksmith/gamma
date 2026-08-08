#!/usr/bin/env python3
"""Opening-10M article-order screen for a causal side-free cmix-obias P0."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import tempfile
from typing import Any

import cmix_obias_geometry_order_host_repacked_qm0_v2 as host
import cmix_obias_geometry_order_substitution_qm0 as base


CANDIDATE_ID = "cmix_obias_revision_order_sidefree_qm0_v1"
SCHEMA = "cmix_obias_revision_order_sidefree_qm0_decision_v1"
FULL_SIDE_BYTES = 346_948
SOURCE_RESERVE_BYTES = 32_768
TEN_M_DAMAGE_CEILING_BYTES = (FULL_SIDE_BYTES - SOURCE_RESERVE_BYTES) // 100


def first_revision_id(page: bytes, physical_ordinal: int) -> int:
    revision_start = page.find(b"<revision>")
    if revision_start < 0:
        raise RuntimeError(f"page {physical_ordinal} has no revision opener")
    match = base.ID_RE.search(page, revision_start)
    if match is None:
        raise RuntimeError(f"page {physical_ordinal} has no first revision ID")
    return int(match.group(1))


def generate_revision_order(data: bytes) -> tuple[bytes, dict[str, Any]]:
    rows: list[tuple[int, int, int, int]] = []
    redirect_count = 0
    nonredirect_ordinal = 0
    pages = base.complete_pages(data)
    for physical_ordinal, page in enumerate(pages):
        page_id_raw = base.first_match(base.ID_RE, page)
        if not page_id_raw:
            raise RuntimeError(f"page {physical_ordinal} has no page ID")
        page_id = int(page_id_raw)
        if base.is_donor_redirect(page):
            redirect_count += 1
            continue
        revision_id = first_revision_id(page, physical_ordinal)
        rows.append((revision_id, page_id, physical_ordinal, nonredirect_ordinal))
        nonredirect_ordinal += 1
    revision_ids = [row[0] for row in rows]
    unique_revision_ids = len(set(revision_ids))
    if unique_revision_ids != len(revision_ids):
        raise RuntimeError(
            f"first revision IDs are not unique: {unique_revision_ids}/{len(revision_ids)}"
        )
    rows.sort(key=lambda row: (row[0], row[1], row[2]))
    output = b"".join(f"{row[3]}\n".encode("ascii") for row in rows)
    return output, {
        "complete_pages": len(pages),
        "redirect_pages": redirect_count,
        "ordered_nonredirect_pages": len(rows),
        "unique_revision_ids": unique_revision_ids,
        "minimum_revision_id": min(revision_ids),
        "maximum_revision_id": max(revision_ids),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor-root", type=pathlib.Path, required=True)
    parser.add_argument(
        "--input", type=pathlib.Path, default=base.PROJECT_ROOT / "data" / "enwik9"
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=base.PROJECT_ROOT / "results" / CANDIDATE_ID,
    )
    args = parser.parse_args()

    base.CANDIDATE_ID = CANDIDATE_ID
    donor_root = args.donor_root.resolve()
    input_path = args.input.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if input_path.stat().st_size != base.FULL_INPUT_BYTES:
        raise RuntimeError("full input size mismatch")
    if base.sha256_file(input_path) != base.FULL_INPUT_SHA256:
        raise RuntimeError("full input hash mismatch")
    paths, raw_executable = base.verify_donor(donor_root)
    raw_dictionary = donor_root / "cmix-obias" / "dictionary" / "english.dic"
    base.require_file(raw_dictionary, host.RAW_DICT_BYTES, host.RAW_DICT_SHA256)

    env = os.environ.copy()
    env["KH_BITLSTM32"] = str(paths["head"])
    env.pop("CMIX_PPM_RSS_MB", None)

    with tempfile.TemporaryDirectory(prefix=f"{CANDIDATE_ID}_") as temporary_text:
        temporary = pathlib.Path(temporary_text)
        prefix_path = temporary / "enwik7"
        base.write_prefix(input_path, prefix_path)
        data = prefix_path.read_bytes()
        revision_order_a, revision_counts = generate_revision_order(data)
        revision_order_b, revision_counts_b = generate_revision_order(data)
        revision_order_identity = (
            revision_order_a == revision_order_b and revision_counts == revision_counts_b
        )
        if not revision_order_identity:
            raise RuntimeError("revision order rebuild is not byte-identical")

        comp_dict = temporary / "dict" / "comp_dict"
        dictionary_receipt = host.compress_asset(
            raw_executable=raw_executable,
            source=raw_dictionary,
            output=comp_dict,
            workspace=comp_dict.parent,
            env=env,
        )
        b0_package, b0_package_receipt = host.build_host_package(
            arm="B0",
            workspace=temporary / "package_B0",
            raw_executable=raw_executable,
            comp_dict=comp_dict,
            raw_order=paths["raw_order"].read_bytes(),
            env=env,
        )
        r0_package, r0_package_receipt = host.build_host_package(
            arm="R0",
            workspace=temporary / "package_R0",
            raw_executable=raw_executable,
            comp_dict=comp_dict,
            raw_order=revision_order_a,
            env=env,
        )
        r0_package_receipt["page_counts"] = revision_counts

        b0 = base.run_arm(
            arm="B0",
            package=b0_package,
            input_path=prefix_path,
            head_path=paths["head"],
            root=temporary,
        )
        r0 = base.run_arm(
            arm="R0",
            package=r0_package,
            input_path=prefix_path,
            head_path=paths["head"],
            root=temporary,
        )
        archive_damage = r0["archive9_bytes"] - b0["archive9_bytes"]
        memory_ok = all(
            arm[guard]["official_decimal_over_limit_kib"] == 0
            for arm in (b0, r0)
            for guard in ("encode_guard", "decode_guard")
        )
        pre_repeat_pass = (
            b0["roundtrip_ok"]
            and r0["roundtrip_ok"]
            and memory_ok
            and archive_damage <= TEN_M_DAMAGE_CEILING_BYTES
        )
        repeat: dict[str, Any] | None = None
        repeat_identity = False
        if pre_repeat_pass:
            repeat = base.repeated_encode(
                package=r0_package,
                input_path=prefix_path,
                head_path=paths["head"],
                expected=r0,
                root=temporary,
            )
            repeat_identity = repeat["byte_identical"] is True

        verdict = (
            "AUTHORIZE_SOURCE_CHILD"
            if pre_repeat_pass and repeat_identity
            else "REJECT"
        )
        decision = {
            "schema": SCHEMA,
            "candidate_id": CANDIDATE_ID,
            "status": "terminal",
            "evidence_tier": "oracle",
            "scope": {
                "bytes": base.SCOPE_BYTES,
                "sha256": base.SCOPE_SHA256,
                "population": "canonical opening 10M",
            },
            "inputs": {
                "donor_commit": base.DONOR_COMMIT,
                "full_input_bytes": base.FULL_INPUT_BYTES,
                "full_input_sha256": base.FULL_INPUT_SHA256,
                "raw_dictionary_bytes": host.RAW_DICT_BYTES,
                "raw_dictionary_sha256": host.RAW_DICT_SHA256,
                "raw_public_order_bytes": base.RAW_PUBLIC_ORDER_BYTES,
                "raw_public_order_sha256": base.RAW_PUBLIC_ORDER_SHA256,
            },
            "orders": {
                "public": b0_package_receipt,
                "revision": r0_package_receipt,
                "revision_order_rebuild_identity": revision_order_identity,
            },
            "host_repack": {"dictionary": dictionary_receipt},
            "arms": {"B0": b0, "R0": r0, "R0_repeat": repeat},
            "accounting": {
                "b0_archive_bytes": b0["archive9_bytes"],
                "r0_archive_bytes": r0["archive9_bytes"],
                "r0_archive_damage_10m_bytes": archive_damage,
                "r0_archive_damage_bytes_per_million": archive_damage / 10.0,
                "conditional_full_side_bytes": FULL_SIDE_BYTES,
                "source_reserve_bytes": SOURCE_RESERVE_BYTES,
                "ten_m_damage_ceiling_bytes": TEN_M_DAMAGE_CEILING_BYTES,
                "full_1g_projection_valid": False,
                "score_credit_bytes": 0,
            },
            "causal_contract": {
                "compressor_page_order": "ascending first revision ID",
                "decoder_restore_key": "visible first D86 value in each P0 block",
                "join_key_visible_before_wrt_and_phda9_restore": True,
                "replacement_occurrence_permutation": False,
            },
            "gates": {
                "artifact_identity": True,
                "revision_ids_unique": revision_counts["unique_revision_ids"]
                == revision_counts["ordered_nonredirect_pages"],
                "revision_order_rebuild_identity": revision_order_identity,
                "parent_roundtrip": b0["roundtrip_ok"],
                "revision_order_roundtrip": r0["roundtrip_ok"],
                "memory_ok": memory_ok,
                "archive_damage_within_ceiling": archive_damage
                <= TEN_M_DAMAGE_CEILING_BYTES,
                "revision_order_repeat_identity": repeat_identity,
            },
            "decision": {
                "verdict": verdict,
                "scientific_valid": True,
                "score_credit_bytes": 0,
                "forecast_change_authorized": False,
                "source_child_authorized": verdict == "AUTHORIZE_SOURCE_CHILD",
                "next_action": (
                    "Implement one source child that omits R1ORD3 and restores P0 by D86 sort."
                    if verdict == "AUTHORIZE_SOURCE_CHILD"
                    else "Retire revision-ID article order on this donor without nearby order sweeps."
                ),
            },
        }
        base.atomic_json(output_dir / "decision.json", decision)
        print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
