#!/usr/bin/env python3
"""Seal the independent source-package saving for the unchanged 112+80 codec."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PRIOR_TAIL_FORECAST_SCORE = 109_522_498
TARGET_SCORE = 109_500_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
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


def require_artifact(entry: dict[str, Any]) -> dict[str, Any]:
    observed = artifact(Path(entry["path"]))
    for key in ("bytes", "sha256"):
        if observed[key] != entry[key]:
            raise RuntimeError(f"artifact {key} mismatch for {observed['path']}")
    return observed


def accounting_metrics(
    *, prior_package_bytes: int, replacement_package_bytes: int
) -> dict[str, int]:
    saved = prior_package_bytes - replacement_package_bytes
    forecast = PRIOR_TAIL_FORECAST_SCORE - saved
    return {
        "prior_source_package_bytes": prior_package_bytes,
        "replacement_source_package_bytes": replacement_package_bytes,
        "source_package_saved_bytes": saved,
        "prior_tail_forecast_score_bytes": PRIOR_TAIL_FORECAST_SCORE,
        "replacement_tail_forecast_score_bytes": forecast,
        "replacement_tail_forecast_margin_bytes": TARGET_SCORE - forecast,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package-receipt", type=Path, required=True)
    parser.add_argument("--terminal-receipt", type=Path, required=True)
    parser.add_argument("--wrapper-receipt", type=Path, required=True)
    parser.add_argument("--prior-source-package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    for path in (
        args.source_package_receipt,
        args.terminal_receipt,
        args.wrapper_receipt,
        args.prior_source_package,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    source = load_object(args.source_package_receipt)
    terminal = load_object(args.terminal_receipt)
    wrapper = load_object(args.wrapper_receipt)
    if source.get("schema") != "reproducible_source_shar_package_v1":
        raise RuntimeError("unexpected source-package receipt schema")
    source_proof = source.get("proof", {})
    for field in (
        "proof_complete",
        "clean_build_complete",
        "clean_backend_identity",
        "clean_program_identity",
        "reference_backend_identity",
    ):
        if source_proof.get(field) is not True:
            raise RuntimeError(f"source-package proof did not pass {field}")
    if terminal.get("schema") != "fx2_cmix21_lstm112_plus80_terminal_decision_v1":
        raise RuntimeError("unexpected terminal receipt schema")
    if terminal.get("decision", {}).get("verdict") != (
        "retire_unchanged_112_plus80_from_promotion"
    ):
        raise RuntimeError("terminal receipt no longer preserves the retirement boundary")
    wrapper_result = wrapper.get("result", {})
    for field in (
        "archive_payload_identity",
        "roundtrip_ok",
        "determinism_ok",
        "proof_complete",
    ):
        if wrapper_result.get(field) is not True:
            raise RuntimeError(f"wrapper proof did not pass {field}")

    replacement = require_artifact(source["artifacts"]["zip_a"])
    require_artifact(source["artifacts"]["zip_b"])
    clean_program = require_artifact(source["artifacts"]["clean_program_a"])
    wrapper_program = require_artifact(wrapper["artifacts"]["program"])
    if any(clean_program[key] != wrapper_program[key] for key in ("bytes", "sha256")):
        raise RuntimeError("clean-built replacement program differs from wrapper proof")
    if replacement["sha256"] != source["artifacts"]["zip_b"]["sha256"]:
        raise RuntimeError("replacement source packages are not deterministic")

    metrics = accounting_metrics(
        prior_package_bytes=args.prior_source_package.stat().st_size,
        replacement_package_bytes=replacement["bytes"],
    )
    if metrics["source_package_saved_bytes"] <= 0:
        raise RuntimeError("replacement source package does not save bytes")

    receipt = {
        "schema": "fx2_cmix21_source_package_accounting_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "counted_package_reconstruction_plus_exact_10m_wrapper_bridge",
        "artifacts": {
            "source_package_receipt": artifact(args.source_package_receipt),
            "terminal_receipt": artifact(args.terminal_receipt),
            "wrapper_receipt": artifact(args.wrapper_receipt),
            "prior_source_package": artifact(args.prior_source_package),
            "replacement_source_package": replacement,
            "clean_built_program": clean_program,
            "wrapper_proven_program": wrapper_program,
        },
        "proof": {
            "source_reconstruction_ok": True,
            "two_clean_builds_identical": True,
            "replacement_program_matches_wrapper_proof": True,
            "wrapper_archive_payload_identity": True,
            "wrapper_roundtrip_ok": True,
            "wrapper_determinism_ok": True,
        },
        "metrics": metrics,
        "decision": {
            "package_representation_accepted": True,
            "promotion_authorized": False,
            "larger_gate_authorized": False,
            "unchanged_112_plus80_remains_retired": True,
            "verdict": "accept_source_package_saving_without_reopening_codec",
            "next_action": (
                "reuse this counted source representation for any bit-identical descendant; "
                "require new disjoint compression evidence before a larger codec gate"
            ),
        },
        "claim_boundary": (
            "The replacement package saves counted source bytes and reconstructs the exact "
            "program already proven at 10M. The resulting 109498879 value is a tail forecast, "
            "not a full-corpus constructive score; weak reset-slice transfer still forbids an "
            "unchanged 1G codec gate."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
