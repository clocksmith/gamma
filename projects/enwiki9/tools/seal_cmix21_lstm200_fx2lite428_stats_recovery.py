#!/usr/bin/env python3
"""Seal archive-neutral FX2-lite PPMD statistics-span recovery at exact 1M."""

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
else:
    from seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        artifact,
        calculate_repaired_economics,
        load_object,
        require_clean_guard,
    )


def require_same_payload(first: dict[str, Any], second: dict[str, Any]) -> None:
    if any(first[key] != second[key] for key in ("bytes", "sha256")):
        raise RuntimeError("artifact payloads differ")


def require_replay_invocation(
    guard: dict[str, Any],
    *,
    backend: Path,
    dictionary: Path,
    store: Path,
    archive: Path,
) -> None:
    command = guard.get("command")
    if not isinstance(command, list):
        raise RuntimeError("guard command is missing")
    direct = [
        str(backend.resolve()),
        "-r",
        str(dictionary.resolve()),
        str(store.resolve()),
        str(archive.resolve()),
    ]
    if any(
        command[index : index + len(direct)] == direct
        for index in range(len(command) - len(direct) + 1)
    ):
        return

    # run_with_rss_guard records the outer shell invocation. In that form the
    # replay mode is part of the fixed shell program and the artifact paths are
    # positional arguments, so there is no literal ``-r`` list element.
    shell_program = 'exec "$1" -r "$2" "$3" "$4" >"$5" 2>"$6"'
    shell_arguments = [
        "_",
        str(backend.resolve()),
        str(dictionary.resolve()),
        str(store.resolve()),
        str(archive.resolve()),
    ]
    if (
        len(command) >= 3 + len(shell_arguments)
        and Path(str(command[0])).name == "bash"
        and command[1] == "-c"
        and command[2] == shell_program
        and command[3 : 3 + len(shell_arguments)] == shell_arguments
    ):
        return

    raise RuntimeError(f"guard command differs from frozen WRT replay: {command}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-native-receipt", type=Path, required=True)
    parser.add_argument("--stats-failure-receipt", type=Path, required=True)
    parser.add_argument("--source-package-receipt", type=Path, required=True)
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--wrapper", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--encode-guard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    prior = load_object(args.prior_native_receipt)
    failure = load_object(args.stats_failure_receipt)
    package = load_object(args.source_package_receipt)
    if prior.get("schema") != "cmix21_lstm200_fx2lite428_native_v1":
        raise RuntimeError("unexpected prior native receipt")
    if failure.get("schema") != "cmix21_lstm200_fx2lite428_stats_failure_v1":
        raise RuntimeError("unexpected statistics-failure receipt")
    if failure.get("decision", {}).get("stats_span_recovery_replay_authorized") is not True:
        raise RuntimeError("terminal failure does not authorize statistics recovery")
    if package.get("schema") != "reproducible_source_shar_package_v1":
        raise RuntimeError("unexpected source-package receipt")
    if not (
        package.get("proof", {}).get("proof_complete") is True
        and package.get("proof", {}).get("clean_build_complete") is True
    ):
        raise RuntimeError("statistics recovery lacks clean source proof")

    package_artifacts = package["artifacts"]
    backend = artifact(args.backend)
    wrapper = artifact(args.wrapper)
    require_same_payload(backend, package_artifacts["clean_backend_a"])
    require_same_payload(backend, package_artifacts["clean_backend_b"])
    require_same_payload(backend, package_artifacts["reference_backend"])
    require_same_payload(wrapper, package_artifacts["clean_program_a"])
    require_same_payload(wrapper, package_artifacts["clean_program_b"])
    require_same_payload(artifact(args.dictionary), package_artifacts["dictionary"])

    guard = require_clean_guard(args.encode_guard)
    require_replay_invocation(
        guard,
        backend=args.backend,
        dictionary=args.dictionary,
        store=args.store,
        archive=args.archive,
    )
    archive = artifact(args.archive)
    require_same_payload(archive, prior["artifacts"]["archive"])

    source_zip = package_artifacts["zip_a"]
    require_same_payload(source_zip, package_artifacts["zip_b"])
    economics = calculate_repaired_economics(
        prior_economics=prior["economics"],
        repaired_package_bytes=int(source_zip["bytes"]),
    )
    authorized = bool(economics["full_and_holdout_forecasts_below_target"])

    receipt = {
        "schema": "cmix21_lstm200_fx2lite428_stats_recovery_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "constructive_archive_neutral_statistics_recovery_1m",
        "scope": {
            "raw_bytes": 1_000_000,
            "stored_wrt_bytes_including_header": args.store.stat().st_size,
            "article_order": "original",
        },
        "artifacts": {
            "prior_native_receipt": artifact(args.prior_native_receipt),
            "stats_failure_receipt": artifact(args.stats_failure_receipt),
            "source_package_receipt": artifact(args.source_package_receipt),
            "source_package": source_zip,
            "backend": backend,
            "wrapper": wrapper,
            "dictionary": artifact(args.dictionary),
            "store": artifact(args.store),
            "archive": archive,
            "encode_guard": artifact(args.encode_guard),
        },
        "mechanism": {
            "recovery": (
                "validate FX2-lite PPMD context pointers, statistics spans, suffix "
                "walks, and successors before dereference; reset deterministically "
                "when state is malformed"
            ),
            "valid_state_probability_change": "none through exact 1M",
        },
        "metrics": {
            "archive_bytes": archive["bytes"],
            "max_encode_single_rss_kib": guard["max_sampled_single_rss_kib"],
            "max_encode_tree_rss_kib": guard["max_sampled_tree_rss_kib"],
            "decimal_10gb_limit_kib": guard["official_decimal_limit_kib"],
        },
        "economics": economics,
        "proof": {
            "exact_1m_archive_identity": True,
            "clean_encode_tree_rss_guard": True,
            "source_package_deterministic": True,
            "source_package_reconstructs_backend_and_wrapper": True,
        },
        "decision": {
            "exact_10m_confirmation_authorized": authorized,
            "official_1g_gate_authorized": False,
            "promotion_authorized": False,
            "verdict": (
                "stats_recovery_identity_pass_authorize_strict_10m"
                if authorized
                else "stats_recovery_identity_pass_but_counted_economics_fail"
            ),
            "next_action": (
                "run the unchanged clean-built wrapper on canonical exact 10M and "
                f"require archive <= {economics['strict_candidate_archive_ceiling_bytes_10m']} bytes"
            ),
        },
        "claim_boundary": (
            "This proves counted exact-1M archive identity and authorizes only the "
            "strict exact-10M gate. It is not a full-corpus score claim."
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
