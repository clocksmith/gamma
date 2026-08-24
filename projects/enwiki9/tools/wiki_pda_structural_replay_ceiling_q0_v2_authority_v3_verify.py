#!/usr/bin/env python3
"""Independently verify frozen WIKI-PDA v2 under q1-v3 authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import wiki_pda_structural_replay_ceiling_q0_v2_authority_v3 as contract
import wiki_pda_structural_replay_ceiling_q0_v2_verify as legacy_verify


PROJECT = Path(__file__).resolve().parents[1]
RESULT = contract.RESULT


def verify(args: argparse.Namespace) -> tuple[dict[str, object], bool]:
    """Reuse the frozen scientific verifier and add the v3 authority proof."""

    original_contract = legacy_verify.contract
    original_validate_parent = contract.validate_parent

    def three_part_parent(
        receipt: Path, verification: Path
    ) -> tuple[dict[str, object], dict[str, object], bytes]:
        values = original_validate_parent(receipt, verification)
        return values[0], values[1], values[2]

    contract.validate_parent = three_part_parent
    legacy_verify.contract = contract
    try:
        output, verified = legacy_verify.verify(args)
    finally:
        contract.validate_parent = original_validate_parent
        legacy_verify.contract = original_contract

    prior_parent_check = output["checks"].pop(
        "parent_v4_qualification_pass", False
    )
    authority_check = False
    if verified:
        try:
            decision = legacy_verify.load_json(args.decision.resolve(strict=True))
            manifest = legacy_verify.load_json(args.manifest.resolve(strict=True))
            roles = legacy_verify.verify_manifest(manifest)
            receipt_path = (
                args.parent_qualification_receipt
                if args.parent_qualification_receipt.is_absolute()
                else PROJECT / args.parent_qualification_receipt
            )
            verification_path = (
                args.parent_qualification_verification
                if args.parent_qualification_verification.is_absolute()
                else PROJECT / args.parent_qualification_verification
            )
            (
                parent_receipt,
                parent_verification,
                reverified_raw,
                active_policy,
                _,
            ) = original_validate_parent(receipt_path, verification_path)
            parent = decision["parent_qualification"]
            authority_check = bool(
                prior_parent_check
                and parent["receipt"] == parent_receipt
                and parent["verification"] == parent_verification
                and parent["independent_reverification"]
                == contract.artifact(roles["parent_reverification"])
                and roles["parent_reverification"].read_bytes() == reverified_raw
                and parent["active_policy"] == active_policy
                and parent["authority_design_policy"]
                == contract.artifact(contract.PARENT_DESIGN_POLICY)
                and parent["fully_positive"] is True
            )
            if not authority_check:
                raise RuntimeError("q1-v3 authority binding mismatch")
        except Exception as error:
            output["errors"].append(f"{type(error).__name__}: {error}")
            verified = False
            output["scientific_verdict"] = "none_verification_failure"
            output["promotion_authorized"] = False
    output["checks"]["parent_v3_active_policy_qualification_pass"] = (
        authority_check
    )
    output["verified"] = verified and all(output["checks"].values())
    if not output["verified"]:
        output["scientific_verdict"] = "none_verification_failure"
        output["promotion_authorized"] = False
    contract.validate_with_schema(output, contract.VERIFICATION_SCHEMA)
    return output, bool(output["verified"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--parent-qualification-receipt", required=True, type=Path)
    parser.add_argument(
        "--parent-qualification-verification", required=True, type=Path
    )
    parser.add_argument("--verification", required=True, type=Path)
    args = parser.parse_args()
    if args.verification.exists() or args.verification.is_symlink():
        raise FileExistsError(
            f"refusing to overwrite verification: {args.verification}"
        )
    try:
        if RESULT in args.verification.resolve().parents:
            raise RuntimeError(
                "verification output must remain outside the sealed result root"
            )
    except FileNotFoundError:
        if RESULT in args.verification.absolute().parents:
            raise RuntimeError(
                "verification output must remain outside the sealed result root"
            )
    output, verified = verify(args)
    contract.write_json_exclusive(args.verification, output)
    print(json.dumps(output, sort_keys=True, indent=2))
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
