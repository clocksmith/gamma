#!/usr/bin/env python3
"""Seal the archive-neutral RAM-PPMD plus context-recovery combination."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__:
    from .seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        artifact,
        calculate_repaired_economics,
        load_object,
        require_clean_guard,
        require_guard_invocation,
    )
else:
    from seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        artifact,
        calculate_repaired_economics,
        load_object,
        require_clean_guard,
        require_guard_invocation,
    )


def require_same_payload(first: dict[str, Any], second: dict[str, Any]) -> None:
    if any(first[key] != second[key] for key in ("bytes", "sha256")):
        raise RuntimeError("archive payloads differ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-native-receipt", type=Path, required=True)
    parser.add_argument("--v6-recovery-receipt", type=Path, required=True)
    parser.add_argument("--v6-10m-failure-receipt", type=Path, required=True)
    parser.add_argument("--source-package-receipt", type=Path, required=True)
    parser.add_argument("--wrapper", type=Path, required=True)
    parser.add_argument("--ram-1m-archive", type=Path, required=True)
    parser.add_argument("--ram-1m-guard", type=Path, required=True)
    parser.add_argument("--boundary-input", type=Path, required=True)
    parser.add_argument("--boundary-archive", type=Path, required=True)
    parser.add_argument("--boundary-guard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    prior = load_object(args.prior_native_receipt)
    recovery = load_object(args.v6_recovery_receipt)
    failure = load_object(args.v6_10m_failure_receipt)
    package = load_object(args.source_package_receipt)
    if prior.get("schema") != "cmix21_lstm200_fx2lite428_native_v1":
        raise RuntimeError("unexpected prior native receipt")
    if recovery.get("schema") != "cmix21_lstm200_fx2lite428_ppmd_recovery_v1":
        raise RuntimeError("unexpected v6 recovery receipt")
    if failure.get("schema") != "cmix21_lstm200_fx2lite428_10m_codec_failure_v1":
        raise RuntimeError("unexpected v6 terminal failure receipt")
    if failure.get("decision", {}).get(
        "combined_ram_ppmd_context_guard_boundary_replay_authorized"
    ) is not True:
        raise RuntimeError("v6 failure does not authorize the combined repair")
    if package.get("schema") != "reproducible_source_shar_package_v1":
        raise RuntimeError("unexpected source package receipt")
    if not (
        package.get("proof", {}).get("proof_complete") is True
        and package.get("proof", {}).get("clean_build_complete") is True
    ):
        raise RuntimeError("combined repair lacks clean source proof")

    wrapper = artifact(args.wrapper)
    for key in ("clean_program_a", "clean_program_b"):
        require_same_payload(wrapper, package["artifacts"][key])
    ram_1m_guard = require_clean_guard(args.ram_1m_guard)
    ram_1m_archive = artifact(args.ram_1m_archive)
    require_same_payload(ram_1m_archive, prior["artifacts"]["archive"])

    boundary_guard = require_clean_guard(args.boundary_guard)
    require_guard_invocation(
        boundary_guard,
        wrapper=args.wrapper,
        mode="c",
        source=args.boundary_input,
        target=args.boundary_archive,
    )
    boundary_input = artifact(args.boundary_input)
    boundary_archive = artifact(args.boundary_archive)
    require_same_payload(boundary_input, recovery["artifacts"]["input"])
    require_same_payload(boundary_archive, recovery["artifacts"]["archive"])

    package_zip = package["artifacts"]["zip_a"]
    require_same_payload(package_zip, package["artifacts"]["zip_b"])
    economics = calculate_repaired_economics(
        prior_economics=prior["economics"],
        repaired_package_bytes=int(package_zip["bytes"]),
    )
    authorized = bool(economics["full_and_holdout_forecasts_below_target"])
    receipt = {
        "schema": "cmix21_lstm200_fx2lite428_ram_recovery_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "constructive_archive_neutral_combined_recovery_prefix",
        "artifacts": {
            "prior_native_receipt": artifact(args.prior_native_receipt),
            "v6_recovery_receipt": artifact(args.v6_recovery_receipt),
            "v6_10m_failure_receipt": artifact(args.v6_10m_failure_receipt),
            "source_package_receipt": artifact(args.source_package_receipt),
            "source_package": package_zip,
            "wrapper": wrapper,
            "ram_1m_archive": ram_1m_archive,
            "ram_1m_guard": artifact(args.ram_1m_guard),
            "boundary_input": boundary_input,
            "boundary_archive": boundary_archive,
            "boundary_guard": artifact(args.boundary_guard),
        },
        "mechanism": {
            "context_recovery": (
                "deterministic invalid/cyclic FX2-lite PPMD context reset"
            ),
            "storage_recovery": (
                "stable anonymous 20 MiB FX2-lite PPMD heap instead of periodic "
                "disk-backed fixed-address unmap/remap"
            ),
            "probability_change_through_boundary": "none",
        },
        "scope": {
            "ram_storage_identity_raw_bytes": 1_000_000,
            "combined_boundary_identity_raw_bytes": boundary_input["bytes"],
        },
        "metrics": {
            "ram_1m_archive_bytes": ram_1m_archive["bytes"],
            "boundary_archive_bytes": boundary_archive["bytes"],
            "max_boundary_tree_rss_kib": boundary_guard[
                "max_sampled_tree_rss_kib"
            ],
            "max_ram_1m_tree_rss_kib": ram_1m_guard[
                "max_sampled_tree_rss_kib"
            ],
            "decimal_10gb_limit_kib": boundary_guard[
                "official_decimal_limit_kib"
            ],
        },
        "economics": economics,
        "proof": {
            "ram_ppmd_1m_archive_identity": True,
            "combined_boundary_archive_identity": True,
            "combined_boundary_guard_clean": True,
            "source_package_deterministic": True,
            "source_package_reconstructs_wrapper": True,
        },
        "decision": {
            "exact_10m_confirmation_authorized": authorized,
            "official_1g_gate_authorized": False,
            "promotion_authorized": False,
            "verdict": (
                "combined_recovery_proven_authorize_strict_10m_economics_gate"
                if authorized
                else "combined_recovery_proven_but_counted_economics_fail"
            ),
            "next_action": (
                "run the unchanged clean-built combined recovery wrapper on canonical "
                "original-order 10M; reject if its archive exceeds "
                f"{economics['strict_candidate_archive_ceiling_bytes_10m']} bytes"
            ),
        },
        "claim_boundary": (
            "This receipt proves archive-neutral repair composition through 1.5M. "
            "It authorizes only exact 10M and is not a full-corpus score claim."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    temporary.replace(args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if authorized else 1


if __name__ == "__main__":
    raise SystemExit(main())
