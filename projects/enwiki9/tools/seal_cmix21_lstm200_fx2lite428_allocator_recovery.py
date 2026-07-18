#!/usr/bin/env python3
"""Seal selective FX2-lite PPMD allocator recovery at exact 1M."""

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
    )
    from .seal_cmix21_lstm200_fx2lite428_stats_recovery import (
        require_replay_invocation,
        require_same_payload,
    )
else:
    from seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        artifact,
        calculate_repaired_economics,
        load_object,
        require_clean_guard,
    )
    from seal_cmix21_lstm200_fx2lite428_stats_recovery import (
        require_replay_invocation,
        require_same_payload,
    )


def require_source_package(package: dict[str, Any]) -> None:
    if package.get("schema") != "reproducible_source_shar_package_v1":
        raise RuntimeError("unexpected source-package receipt")
    proof = package.get("proof", {})
    if not (
        proof.get("proof_complete") is True
        and proof.get("clean_build_complete") is True
        and proof.get("clean_backend_identity") is True
        and proof.get("clean_program_identity") is True
        and proof.get("reference_backend_identity") is True
    ):
        raise RuntimeError("allocator recovery lacks complete clean source proof")


def require_dictionary_codec_invocation(
    guard: dict[str, Any],
    *,
    backend: Path,
    mode: str,
    dictionary: Path,
    source: Path,
    target: Path,
) -> None:
    command = guard.get("command")
    if not isinstance(command, list):
        raise RuntimeError("guard command is missing")
    direct = [
        str(backend.resolve()),
        mode,
        str(dictionary.resolve()),
        str(source.resolve()),
        str(target.resolve()),
    ]
    if any(
        command[index : index + len(direct)] == direct
        for index in range(len(command) - len(direct) + 1)
    ):
        return
    shell_program = (
        f'exec "$1" {mode} "$2" "$3" "$4" >"$5" 2>"$6"'
    )
    shell_arguments = [
        "_",
        str(backend.resolve()),
        str(dictionary.resolve()),
        str(source.resolve()),
        str(target.resolve()),
    ]
    if (
        len(command) >= 3 + len(shell_arguments)
        and Path(str(command[0])).name == "bash"
        and command[1] == "-c"
        and command[2] == shell_program
        and command[3 : 3 + len(shell_arguments)] == shell_arguments
    ):
        return
    raise RuntimeError(f"guard command differs from frozen dictionary codec: {command}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-native-receipt", type=Path, required=True)
    parser.add_argument("--allocator-failure-receipt", type=Path, required=True)
    parser.add_argument("--primaryppmd-failure-receipt", type=Path, required=True)
    parser.add_argument("--source-package-receipt", type=Path, required=True)
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--wrapper", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-second", type=Path, required=True)
    parser.add_argument("--restored", type=Path, required=True)
    parser.add_argument("--encode-guard", type=Path, required=True)
    parser.add_argument("--decode-guard", type=Path, required=True)
    parser.add_argument("--determinism-guard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    prior = load_object(args.prior_native_receipt)
    allocator_failure = load_object(args.allocator_failure_receipt)
    primary_failure = load_object(args.primaryppmd_failure_receipt)
    package = load_object(args.source_package_receipt)
    if prior.get("schema") != "cmix21_lstm200_fx2lite428_native_v1":
        raise RuntimeError("unexpected prior native receipt")
    if allocator_failure.get("schema") != "cmix21_lstm200_fx2lite428_allocator_failure_v1":
        raise RuntimeError("unexpected allocator-failure receipt")
    if primary_failure.get("schema") != "cmix21_lstm200_fx2lite428_primaryppmd_identity_failure_v1":
        raise RuntimeError("unexpected wholesale-primary failure receipt")
    if primary_failure.get("decision", {}).get("selective_allocator_port_replay_authorized") is not True:
        raise RuntimeError("wholesale-primary failure did not authorize selective recovery")
    require_source_package(package)

    package_artifacts = package["artifacts"]
    backend = artifact(args.backend)
    wrapper = artifact(args.wrapper)
    for key in ("reference_backend", "clean_backend_a", "clean_backend_b"):
        require_same_payload(backend, package_artifacts[key])
    for key in ("clean_program_a", "clean_program_b"):
        require_same_payload(wrapper, package_artifacts[key])
    dictionary = artifact(args.dictionary)
    require_same_payload(dictionary, package_artifacts["dictionary"])

    guards = {
        "encode": require_clean_guard(args.encode_guard),
        "decode": require_clean_guard(args.decode_guard),
        "determinism": require_clean_guard(args.determinism_guard),
    }
    require_replay_invocation(
        guards["encode"],
        backend=args.backend,
        dictionary=args.dictionary,
        store=args.store,
        archive=args.archive,
    )
    require_dictionary_codec_invocation(
        guards["decode"],
        backend=Path(package_artifacts["clean_backend_a"]["path"]),
        mode="-d",
        dictionary=args.dictionary,
        source=args.archive,
        target=args.restored,
    )
    require_replay_invocation(
        guards["determinism"],
        backend=Path(package_artifacts["clean_backend_b"]["path"]),
        dictionary=args.dictionary,
        store=args.store,
        archive=args.archive_second,
    )

    archive = artifact(args.archive)
    archive_second = artifact(args.archive_second)
    require_same_payload(archive, archive_second)
    require_same_payload(archive, prior["artifacts"]["archive"])
    input_artifact = artifact(args.input)
    restored = artifact(args.restored)
    require_same_payload(input_artifact, restored)

    source_zip = package_artifacts["zip_a"]
    require_same_payload(source_zip, package_artifacts["zip_b"])
    economics = calculate_repaired_economics(
        prior_economics=prior["economics"],
        repaired_package_bytes=int(source_zip["bytes"]),
    )
    authorized = bool(economics["full_and_holdout_forecasts_below_target"])
    max_tree_rss = max(
        int(guard["max_sampled_tree_rss_kib"]) for guard in guards.values()
    )

    receipt = {
        "schema": "cmix21_lstm200_fx2lite428_allocator_recovery_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "constructive_selective_allocator_recovery_exact_1m",
        "scope": {
            "raw_bytes": 1_000_000,
            "stored_wrt_bytes_including_header": args.store.stat().st_size,
            "article_order": "original",
        },
        "artifacts": {
            "prior_native_receipt": artifact(args.prior_native_receipt),
            "allocator_failure_receipt": artifact(args.allocator_failure_receipt),
            "primaryppmd_failure_receipt": artifact(args.primaryppmd_failure_receipt),
            "source_package_receipt": artifact(args.source_package_receipt),
            "source_package": source_zip,
            "backend": backend,
            "wrapper": wrapper,
            "dictionary": dictionary,
            "store": artifact(args.store),
            "input": input_artifact,
            "archive": archive,
            "archive_second": archive_second,
            "restored": restored,
            "encode_guard": artifact(args.encode_guard),
            "decode_guard": artifact(args.decode_guard),
            "determinism_guard": artifact(args.determinism_guard),
        },
        "mechanism": {
            "recovery": (
                "retain v9 context/statistics/suffix/successor/reset behavior; add "
                "heap and free-list index validation, bounded glue/expansion walks, "
                "failed-removal handling, checked unit copies, and explicit "
                "zero-initialization of the 20 MiB auxiliary PPMD heap"
            ),
            "valid_state_probability_change": "none through exact 1M",
            "wholesale_primary_ppmd_imported": False,
        },
        "metrics": {
            "archive_bytes": archive["bytes"],
            "max_tree_rss_kib_across_replays": max_tree_rss,
            "decimal_10gb_limit_kib": guards["encode"]["official_decimal_limit_kib"],
        },
        "economics": economics,
        "proof": {
            "exact_1m_archive_identity": True,
            "exact_1m_roundtrip": True,
            "exact_1m_archive_determinism": True,
            "all_tree_rss_guards_clean": True,
            "source_package_deterministic": True,
            "source_package_reconstructs_backend_and_wrapper": True,
        },
        "decision": {
            "exact_10m_confirmation_authorized": authorized,
            "official_1g_gate_authorized": False,
            "promotion_authorized": False,
            "verdict": (
                "selective_allocator_recovery_pass_authorize_strict_10m"
                if authorized
                else "selective_allocator_recovery_pass_but_counted_economics_fail"
            ),
            "next_action": (
                "run the unchanged clean-built wrapper on canonical exact 10M and "
                f"require archive <= {economics['strict_candidate_archive_ceiling_bytes_10m']} bytes"
            ),
        },
        "claim_boundary": (
            "This proves a counted, deterministic, round-tripping exact-1M allocator "
            "recovery and authorizes only the strict exact-10M gate. It is not a "
            "full-corpus score or 10.95 percent claim."
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
