#!/usr/bin/env python3
"""Seal the exact static-WRT-swap comparison against the 112+80 codec."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib


TARGET_SCORE = 108_000_000
CURRENT_TAIL_PROJECTED_SCORE = 109_522_498
SCOPE_BYTES = 10_000_000
FULL_SCOPE_BYTES = 1_000_000_000


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: pathlib.Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def clean_guard(receipt: dict[str, object]) -> bool:
    return bool(
        receipt.get("status") == "complete"
        and receipt.get("returncode") == 0
        and receipt.get("rss_guard_exceeded") is False
        and receipt.get("official_decimal_over_limit_kib", 0) == 0
    )


def economics(
    *,
    baseline_archive_bytes: int,
    candidate_archive_bytes: int,
    baseline_source_zip_bytes: int,
    candidate_source_zip_bytes: int,
) -> dict[str, int | float]:
    archive_saved_bytes = baseline_archive_bytes - candidate_archive_bytes
    package_delta_bytes = candidate_source_zip_bytes - baseline_source_zip_bytes
    net_saved_10m = archive_saved_bytes - package_delta_bytes
    scale = FULL_SCOPE_BYTES // SCOPE_BYTES
    projected_score = (
        CURRENT_TAIL_PROJECTED_SCORE - archive_saved_bytes * scale + package_delta_bytes
    )
    return {
        "baseline_archive_bytes": baseline_archive_bytes,
        "candidate_archive_bytes": candidate_archive_bytes,
        "archive_saved_bytes": archive_saved_bytes,
        "archive_saved_bytes_per_1m": archive_saved_bytes / 10.0,
        "source_package_delta_bytes": package_delta_bytes,
        "net_saved_bytes_at_10m": net_saved_10m,
        "tail_projected_score_bytes": projected_score,
        "tail_projected_margin_to_108000000_bytes": TARGET_SCORE - projected_score,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-receipt", type=pathlib.Path, required=True)
    parser.add_argument("--candidate-archive", type=pathlib.Path, required=True)
    parser.add_argument("--candidate-guard", type=pathlib.Path, required=True)
    parser.add_argument("--proxy-receipt", type=pathlib.Path, required=True)
    parser.add_argument("--baseline-source-zip", type=pathlib.Path, required=True)
    parser.add_argument("--candidate-source-zip", type=pathlib.Path, required=True)
    parser.add_argument("--source-package-receipt", type=pathlib.Path, required=True)
    parser.add_argument("--candidate-dictionary", type=pathlib.Path, required=True)
    parser.add_argument("--restored", type=pathlib.Path)
    parser.add_argument("--decode-guard", type=pathlib.Path)
    parser.add_argument("--second-archive", type=pathlib.Path)
    parser.add_argument("--second-guard", type=pathlib.Path)
    parser.add_argument("--expected-input-sha256")
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    baseline = json.loads(args.baseline_receipt.read_text())
    guard = json.loads(args.candidate_guard.read_text())
    proxy = json.loads(args.proxy_receipt.read_text())
    source_package = json.loads(args.source_package_receipt.read_text())
    if baseline.get("scope_raw_bytes") != SCOPE_BYTES:
        raise SystemExit("baseline is not the exact 10M receipt")
    if baseline.get("archive", {}).get("bytes") != 1_635_670:
        raise SystemExit("unexpected baseline archive")
    if baseline.get("binary", {}).get("sha256") != (
        "b9d2ee92b45d2a0f28735e558fd68650c378734d83210429fe524927d10ecee6"
    ):
        raise SystemExit("unexpected baseline binary")
    if proxy.get("schema") != "wrt_static_boundary_swap_geometry_title_proxy_v1":
        raise SystemExit("unexpected proxy receipt")
    if not proxy.get("economics", {}).get("exact_112_plus_80_screen_authorized"):
        raise SystemExit("proxy did not authorize the exact screen")
    if source_package.get("schema") != "reproducible_source_shar_package_v1":
        raise SystemExit("unexpected source-package receipt")
    source_proof = source_package.get("proof", {})
    if not source_proof.get("proof_complete") or not source_proof.get(
        "clean_build_complete"
    ):
        raise SystemExit("source package has not passed reconstruction and clean build")
    sealed_zip = source_package.get("artifacts", {}).get("zip_a", {})
    sealed_dictionary = source_package.get("artifacts", {}).get("dictionary", {})
    observed_zip = artifact(args.candidate_source_zip)
    observed_dictionary = artifact(args.candidate_dictionary)
    for label, sealed, observed in (
        ("source ZIP", sealed_zip, observed_zip),
        ("candidate dictionary", sealed_dictionary, observed_dictionary),
    ):
        if any(sealed.get(key) != observed[key] for key in ("bytes", "sha256")):
            raise SystemExit(f"{label} differs from the source-package receipt")

    metrics = economics(
        baseline_archive_bytes=baseline["archive"]["bytes"],
        candidate_archive_bytes=args.candidate_archive.stat().st_size,
        baseline_source_zip_bytes=args.baseline_source_zip.stat().st_size,
        candidate_source_zip_bytes=args.candidate_source_zip.stat().st_size,
    )
    archive_saved_bytes = metrics["archive_saved_bytes"]
    net_saved_10m = metrics["net_saved_bytes_at_10m"]
    projected_score = metrics["tail_projected_score_bytes"]

    candidate_guard_clean = clean_guard(guard)
    replay_requested = any(
        value is not None
        for value in (
            args.restored,
            args.decode_guard,
            args.second_archive,
            args.second_guard,
        )
    )
    replay_complete = all(
        value is not None and value.exists()
        for value in (
            args.restored,
            args.decode_guard,
            args.second_archive,
            args.second_guard,
        )
    )
    roundtrip_ok = None
    determinism_ok = None
    decode_guard_clean = None
    second_guard_clean = None
    replay_artifacts: dict[str, object] = {}
    if replay_requested and not replay_complete:
        raise SystemExit("replay arguments must be supplied as a complete set")
    if replay_complete:
        decode_guard = json.loads(args.decode_guard.read_text())
        second_guard = json.loads(args.second_guard.read_text())
        decode_guard_clean = clean_guard(decode_guard)
        second_guard_clean = clean_guard(second_guard)
        roundtrip_ok = (
            args.expected_input_sha256 is not None
            and sha256(args.restored) == args.expected_input_sha256
            and args.restored.stat().st_size == SCOPE_BYTES
        )
        determinism_ok = args.candidate_archive.read_bytes() == args.second_archive.read_bytes()
        replay_artifacts = {
            "restored": artifact(args.restored),
            "decode_guard": artifact(args.decode_guard),
            "second_archive": artifact(args.second_archive),
            "second_guard": artifact(args.second_guard),
        }

    target_closing_screen = candidate_guard_clean and projected_score <= TARGET_SCORE
    if not candidate_guard_clean:
        verdict = "invalid_candidate_guard"
        next_action = "record resource failure; do not replay or promote"
    elif archive_saved_bytes <= 0:
        verdict = "retire_static_boundary_swap_negative_exact_transfer"
        next_action = (
            "preserve the negative dictionary receipt; keep the independently "
            "paying source-package representation separate"
        )
    elif net_saved_10m <= 0:
        verdict = "retire_static_boundary_swap_negative_counted_net"
        next_action = "preserve receipt; the exact archive gain does not pay package cost"
    elif not target_closing_screen:
        verdict = "positive_exact_transfer_but_not_tail_target_closing"
        next_action = "preserve as a small component; do not authorize a larger recurrent gate"
    elif not replay_complete:
        verdict = "target_closing_10m_screen_requires_source_wrapper_proof"
        next_action = (
            "build the counted source package in a clean tree, then run exact wrapper "
            "archive identity, decode, and unchanged second encode under the guard"
        )
    elif not all((decode_guard_clean, second_guard_clean, roundtrip_ok, determinism_ok)):
        verdict = "replay_proof_failed"
        next_action = "record the failed proof boundary; do not promote"
    else:
        verdict = "target_closing_10m_replay_passed_requires_independent_scope_and_runtime"
        next_action = (
            "freeze the package; confirm the fixed dictionary on an independent scope and "
            "resolve official runtime before any full-corpus gate"
        )

    receipt = {
        "schema": "wrt_static_boundary_swap_112plus80_gate_v1",
        "evidence_level": (
            "exact_10m_archive_screen_with_replay"
            if replay_complete
            else "exact_10m_archive_screen"
        ),
        "artifacts": {
            "baseline_receipt": artifact(args.baseline_receipt),
            "candidate_archive": artifact(args.candidate_archive),
            "candidate_guard": artifact(args.candidate_guard),
            "proxy_receipt": artifact(args.proxy_receipt),
            "baseline_source_zip": artifact(args.baseline_source_zip),
            "candidate_source_zip": artifact(args.candidate_source_zip),
            "source_package_receipt": artifact(args.source_package_receipt),
            "candidate_dictionary": artifact(args.candidate_dictionary),
            **replay_artifacts,
        },
        "metrics": metrics,
        "proof": {
            "candidate_guard_clean": candidate_guard_clean,
            "replay_complete": replay_complete,
            "decode_guard_clean": decode_guard_clean,
            "second_guard_clean": second_guard_clean,
            "roundtrip_ok": roundtrip_ok,
            "determinism_ok": determinism_ok,
        },
        "decision": {
            "verdict": verdict,
            "target_closing_screen": target_closing_screen,
            "replay_authorized": target_closing_screen and not replay_complete,
            "wrapper_proof_authorized": target_closing_screen and not replay_complete,
            "selected_source_artifact_key": "candidate_source_zip",
            "larger_gate_authorized": False,
            "promotion_authorized": False,
            "next_action": next_action,
        },
        "claim_boundary": (
            "This receipt is at most exact 10M constructive evidence. The projected "
            "score assumes the measured 10M dictionary effect persists over 1G; only a "
            "counted full-corpus archive at or below 108000000 with roundtrip can prove "
            "the target."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
