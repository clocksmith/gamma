#!/usr/bin/env python3
"""Seal the FX2-lite PPMD recovery and authorize its exact 10M gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TARGET_SCORE_BYTES = 109_000_000
CONFIRMATION_SCOPE_BYTES = 10_000_000
FULL_SCOPE_BYTES = 1_000_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def clean_tree_guard(guard: dict[str, Any]) -> bool:
    decimal_limit = int(guard.get("official_decimal_limit_kib", 0))
    return bool(
        guard.get("status") == "complete"
        and guard.get("returncode") == 0
        and guard.get("limit_mode") == "tree"
        and guard.get("rss_guard_exceeded") is False
        and guard.get("official_decimal_over_limit_kib", 1) == 0
        and decimal_limit > 0
        and int(guard.get("max_sampled_tree_rss_kib", decimal_limit + 1))
        <= decimal_limit
    )


def calculate_repaired_economics(
    *,
    prior_economics: dict[str, Any],
    repaired_package_bytes: int,
) -> dict[str, int | float | bool]:
    prior_package_bytes = int(prior_economics["candidate_source_package_bytes"])
    package_increase = repaired_package_bytes - prior_package_bytes
    if package_increase < 0:
        raise ValueError("repaired package unexpectedly shrank")

    required_gain_1g = (
        int(prior_economics["conservative_required_endpoint_gain_bytes_1g"])
        + package_increase
    )
    scope_divisor = FULL_SCOPE_BYTES // CONFIRMATION_SCOPE_BYTES
    required_gain_10m = (required_gain_1g + scope_divisor - 1) // scope_divisor
    compact_archive_10m = int(prior_economics["compact_archive_bytes_10m"])
    strict_archive_ceiling_10m = compact_archive_10m - required_gain_10m

    full_gain_1g = int(prior_economics["projected_endpoint_full_gain_bytes_1g"])
    holdout_gain_1g = round(
        float(prior_economics["endpoint_holdout_saved_bytes_per_1m"]) * 1000
    )
    full_margin = full_gain_1g - required_gain_1g
    holdout_margin = holdout_gain_1g - required_gain_1g
    return {
        "target_score_bytes": TARGET_SCORE_BYTES,
        "prior_candidate_source_package_bytes": prior_package_bytes,
        "repaired_candidate_source_package_bytes": repaired_package_bytes,
        "source_package_increase_bytes": package_increase,
        "compact_archive_bytes_10m": compact_archive_10m,
        "conservative_required_endpoint_gain_bytes_1g": required_gain_1g,
        "conservative_required_endpoint_gain_bytes_10m": required_gain_10m,
        "strict_candidate_archive_ceiling_bytes_10m": strict_archive_ceiling_10m,
        "conservative_full_forecast_margin_bytes": full_margin,
        "conservative_full_forecast_score_bytes": TARGET_SCORE_BYTES - full_margin,
        "conservative_holdout_forecast_margin_bytes": holdout_margin,
        "conservative_holdout_forecast_score_bytes": TARGET_SCORE_BYTES
        - holdout_margin,
        "full_and_holdout_forecasts_below_target": bool(
            full_margin >= 0 and holdout_margin >= 0
        ),
    }


def require_clean_guard(path: Path) -> dict[str, Any]:
    guard = load_object(path)
    if not clean_tree_guard(guard):
        raise RuntimeError(f"guard is not a clean decimal-compliant tree guard: {path}")
    return guard


def require_guard_invocation(
    guard: dict[str, Any], *, wrapper: Path, mode: str, source: Path, target: Path
) -> None:
    command = guard.get("command")
    if not isinstance(command, list):
        raise RuntimeError("guard command is missing")
    expected = [
        str(wrapper.resolve()),
        mode,
        str(source.resolve()),
        str(target.resolve()),
    ]
    if any(
        command[index : index + len(expected)] == expected
        for index in range(len(command) - len(expected) + 1)
    ):
        return

    fixed_mode_program = (
        f'exec "$1" {mode} "$2" "$3" >"$4" 2>"$5"'
    )
    fixed_mode_arguments = [
        "_",
        str(wrapper.resolve()),
        str(source.resolve()),
        str(target.resolve()),
    ]
    positional_mode_program = (
        'exec "$1" "$2" "$3" "$4" >"$5" 2>"$6"'
    )
    positional_mode_arguments = ["_", *expected]
    shell_match = bool(
        len(command) >= 3
        and Path(str(command[0])).name == "bash"
        and command[1] == "-c"
        and (
            (
                command[2] == fixed_mode_program
                and command[3 : 3 + len(fixed_mode_arguments)]
                == fixed_mode_arguments
            )
            or (
                command[2] == positional_mode_program
                and command[3 : 3 + len(positional_mode_arguments)]
                == positional_mode_arguments
            )
        )
    )
    if shell_match:
        return

    raise RuntimeError(f"guard command differs from frozen invocation: {command}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-native-receipt", type=Path, required=True)
    parser.add_argument("--source-package-receipt", type=Path, required=True)
    parser.add_argument("--repair-wrapper", type=Path, required=True)
    parser.add_argument("--repair-source", type=Path, required=True)
    parser.add_argument("--repair-1m-archive", type=Path, required=True)
    parser.add_argument("--repair-1m-guard", type=Path, required=True)
    parser.add_argument("--failure-guard", type=Path, required=True)
    parser.add_argument("--failure-log", type=Path, required=True)
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
    package = load_object(args.source_package_receipt)
    if prior.get("schema") != "cmix21_lstm200_fx2lite428_native_v1":
        raise RuntimeError("unexpected prior native receipt schema")
    if package.get("schema") != "reproducible_source_shar_package_v1":
        raise RuntimeError("unexpected source-package receipt schema")
    package_proof = package.get("proof", {})
    if not (
        package_proof.get("proof_complete") is True
        and package_proof.get("clean_build_complete") is True
        and package_proof.get("clean_program_identity") is True
    ):
        raise RuntimeError("repaired package lacks deterministic clean-build proof")

    wrapper = artifact(args.repair_wrapper)
    package_artifacts = package["artifacts"]
    for key in ("reference_backend", "clean_backend_a", "clean_backend_b"):
        if package_artifacts[key]["sha256"] != package_artifacts["reference_backend"]["sha256"]:
            raise RuntimeError("clean backend hashes differ")
    for key in ("clean_program_a", "clean_program_b"):
        if package_artifacts[key]["sha256"] != wrapper["sha256"]:
            raise RuntimeError("repair wrapper differs from a clean source build")

    failure_guard = load_object(args.failure_guard)
    failure_log = args.failure_log.read_text(errors="replace")
    if not (
        failure_guard.get("status") == "complete"
        and failure_guard.get("returncode") != 0
        and failure_guard.get("rss_guard_exceeded") is False
        and "Fx2LitePPMD" in failure_log
        and "UpdateModel" in failure_log
    ):
        raise RuntimeError("the original PPMD failure is not reproduced and localized")

    repair_1m_guard = require_clean_guard(args.repair_1m_guard)
    prior_archive = prior["artifacts"]["archive"]
    repair_1m_archive = artifact(args.repair_1m_archive)
    if any(
        repair_1m_archive[key] != prior_archive[key]
        for key in ("bytes", "sha256")
    ):
        raise RuntimeError("recovery changes the already-proven 1M archive")
    require_guard_invocation(
        repair_1m_guard,
        wrapper=args.repair_wrapper,
        mode="c",
        source=Path(prior["artifacts"]["input"]["path"]),
        target=args.repair_1m_archive,
    )

    guards = {
        "encode": require_clean_guard(args.encode_guard),
        "decode": require_clean_guard(args.decode_guard),
        "determinism": require_clean_guard(args.determinism_guard),
    }
    require_guard_invocation(
        guards["encode"],
        wrapper=args.repair_wrapper,
        mode="c",
        source=args.input,
        target=args.archive,
    )
    require_guard_invocation(
        guards["decode"],
        wrapper=args.repair_wrapper,
        mode="d",
        source=args.archive,
        target=args.restored,
    )
    require_guard_invocation(
        guards["determinism"],
        wrapper=Path(package_artifacts["clean_program_a"]["path"]),
        mode="c",
        source=args.input,
        target=args.archive_second,
    )
    input_artifact = artifact(args.input)
    restored = artifact(args.restored)
    if any(input_artifact[key] != restored[key] for key in ("bytes", "sha256")):
        raise RuntimeError("recovery replay failed roundtrip")
    archive = artifact(args.archive)
    archive_second = artifact(args.archive_second)
    if any(archive[key] != archive_second[key] for key in ("bytes", "sha256")):
        raise RuntimeError("recovery replay is not archive-deterministic")

    package_zip = package_artifacts["zip_a"]
    if any(
        package_zip[key] != package_artifacts["zip_b"][key]
        for key in ("bytes", "sha256")
    ):
        raise RuntimeError("source package archives differ")
    economics = calculate_repaired_economics(
        prior_economics=prior["economics"],
        repaired_package_bytes=int(package_zip["bytes"]),
    )
    authorized = bool(economics["full_and_holdout_forecasts_below_target"])

    receipt = {
        "schema": "cmix21_lstm200_fx2lite428_ppmd_recovery_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "constructive_recovery_prefix_identity_and_replay",
        "artifacts": {
            "prior_native_receipt": artifact(args.prior_native_receipt),
            "source_package_receipt": artifact(args.source_package_receipt),
            "source_package": package_zip,
            "repair_wrapper": wrapper,
            "repair_source": artifact(args.repair_source),
            "failure_guard": artifact(args.failure_guard),
            "failure_log": artifact(args.failure_log),
            "repair_1m_archive": repair_1m_archive,
            "repair_1m_guard": artifact(args.repair_1m_guard),
            "input": input_artifact,
            "archive": archive,
            "archive_second": archive_second,
            "restored": restored,
            "encode_guard": artifact(args.encode_guard),
            "decode_guard": artifact(args.decode_guard),
            "determinism_guard": artifact(args.determinism_guard),
        },
        "mechanism": {
            "failure": "FX2-lite PPMD UpdateModel invalid-context crash",
            "repair": (
                "validate decoder-rebuilt PPMD context pointers and suffix walks; "
                "deterministically reset only when the context chain is invalid or cyclic"
            ),
            "normal_path_change": "none before the first invalid context",
        },
        "scope": {
            "archive_identity_raw_bytes": 1_000_000,
            "recovery_replay_raw_bytes": input_artifact["bytes"],
        },
        "metrics": {
            "repair_1m_archive_bytes": repair_1m_archive["bytes"],
            "recovery_replay_archive_bytes": archive["bytes"],
            "max_recovery_tree_rss_kib": max(
                int(guard["max_sampled_tree_rss_kib"])
                for guard in guards.values()
            ),
            "max_repair_1m_tree_rss_kib": repair_1m_guard[
                "max_sampled_tree_rss_kib"
            ],
            "decimal_10gb_limit_kib": guards["encode"][
                "official_decimal_limit_kib"
            ],
        },
        "economics": economics,
        "proof": {
            "original_failure_reproduced": True,
            "failure_localized_to_fx2lite_ppmd_update": True,
            "repair_1m_archive_identity": True,
            "recovery_roundtrip_ok": True,
            "recovery_determinism_ok": True,
            "all_tree_rss_guards_clean": True,
            "source_package_deterministic": True,
            "source_package_reconstructs_repair_wrapper": True,
        },
        "decision": {
            "exact_10m_confirmation_authorized": authorized,
            "official_1g_gate_authorized": False,
            "promotion_authorized": False,
            "verdict": (
                "recovery_proven_authorize_strict_10m_economics_gate"
                if authorized
                else "recovery_proven_but_counted_economics_fail"
            ),
            "next_action": (
                "run the unchanged clean-built repair wrapper on canonical original-order "
                "10M; reject if its archive exceeds "
                f"{economics['strict_candidate_archive_ceiling_bytes_10m']} bytes"
            ),
        },
        "claim_boundary": (
            "This receipt proves the recovery at 1.5M and preserves the proven 1M "
            "archive. It authorizes only an exact 10M economics gate. It is not a "
            "full-corpus score or a 10.95 percent claim."
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
