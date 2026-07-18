#!/usr/bin/env python3
"""Seal the wholesale primary-PPMD exact-1M archive-identity regression."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

if __package__:
    from .seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        artifact,
        load_object,
        require_clean_guard,
    )
    from .seal_cmix21_lstm200_fx2lite428_stats_recovery import (
        require_replay_invocation,
    )
else:
    from seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
        artifact,
        load_object,
        require_clean_guard,
    )
    from seal_cmix21_lstm200_fx2lite428_stats_recovery import (
        require_replay_invocation,
    )


def archive_delta(candidate: dict[str, object], reference: dict[str, object]) -> int:
    if candidate["sha256"] == reference["sha256"]:
        raise RuntimeError("candidate unexpectedly preserves archive identity")
    return int(candidate["bytes"]) - int(reference["bytes"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allocator-failure-receipt", type=Path, required=True)
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--guard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    failure = load_object(args.allocator_failure_receipt)
    if failure.get("schema") != "cmix21_lstm200_fx2lite428_allocator_failure_v1":
        raise RuntimeError("unexpected allocator-failure receipt")
    if failure.get("decision", {}).get("full_primary_ppmd_safety_port_replay_authorized") is not True:
        raise RuntimeError("allocator failure did not authorize the safety port")

    recovery_path = Path(failure["artifacts"]["recovery_receipt"]["path"])
    recovery = load_object(recovery_path)
    if recovery.get("schema") != "cmix21_lstm200_fx2lite428_stats_recovery_v1":
        raise RuntimeError("unexpected reference recovery receipt")

    guard = require_clean_guard(args.guard)
    require_replay_invocation(
        guard,
        backend=args.backend,
        dictionary=args.dictionary,
        store=args.store,
        archive=args.archive,
    )
    candidate = artifact(args.archive)
    reference = recovery["artifacts"]["archive"]
    delta = archive_delta(candidate, reference)

    receipt = {
        "schema": "cmix21_lstm200_fx2lite428_primaryppmd_identity_failure_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "exact_guarded_1m_archive_identity_failure",
        "scope": {"raw_bytes": 1_000_000, "article_order": "original"},
        "artifacts": {
            "allocator_failure_receipt": artifact(args.allocator_failure_receipt),
            "reference_recovery_receipt": artifact(recovery_path),
            "backend": artifact(args.backend),
            "dictionary": artifact(args.dictionary),
            "store": artifact(args.store),
            "candidate_archive": candidate,
            "reference_archive": reference,
            "guard": artifact(args.guard),
        },
        "metrics": {
            "candidate_archive_bytes": candidate["bytes"],
            "reference_archive_bytes": reference["bytes"],
            "archive_delta_bytes": delta,
            "max_sampled_tree_rss_kib": guard["max_sampled_tree_rss_kib"],
            "decimal_10gb_limit_kib": guard["official_decimal_limit_kib"],
        },
        "diagnosis": {
            "failure_class": "archive_identity_regression",
            "interpretation": (
                "the wholesale primary PPMD implementation completes safely but "
                "changes recovery semantics before exact 1M; allocator hardening "
                "must be separated from downstream model behavior"
            ),
        },
        "proof": {
            "clean_encode_tree_rss_guard": True,
            "archive_identity": False,
            "rss_guard_exceeded": False,
        },
        "decision": {
            "exact_10m_gate_authorized": False,
            "official_1g_gate_authorized": False,
            "promotion_authorized": False,
            "selective_allocator_port_replay_authorized": True,
            "verdict": "wholesale_primary_ppmd_rejected_at_exact_1m_identity",
            "next_action": (
                "retain the archive-neutral v9 context/statistics behavior and port "
                "only heap/free-list validation plus explicit zero-initialization"
            ),
        },
        "claim_boundary": (
            "This is a constructive exact-1M regression receipt, not an exact-10M "
            "score, full-corpus result, or 10.95 percent claim."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    temporary.replace(args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
