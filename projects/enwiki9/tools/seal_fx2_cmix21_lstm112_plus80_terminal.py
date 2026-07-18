#!/usr/bin/env python3
"""Seal the constructive 112+80 proof and its disjoint-scope retirement."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_SCOPE_1M = 1_000_000
EXPECTED_SCOPE_10M = 10_000_000
REQUIRED_GROSS_BYTES_PER_1M = 786.375


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    path = path.resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object: {path}")
    return value


def require_artifact(entry: dict[str, Any]) -> dict[str, Any]:
    observed = artifact(Path(entry["path"]))
    for key in ("bytes", "sha256"):
        if observed[key] != entry[key]:
            raise RuntimeError(
                f"artifact {key} mismatch for {observed['path']}: "
                f"{observed[key]} != {entry[key]}"
            )
    return observed


def summarize_metrics(
    *,
    fx2_1m_archive: int,
    native112_1m_archive: int,
    pair_1m_archive: int,
    fx2_10m_archive: int,
    native112_10m_archive: int,
    pair_10m_archive: int,
    disjoint_fx2_archive: int,
    disjoint_native112_archive: int,
    disjoint_pair_archive: int,
) -> dict[str, int | float | bool]:
    pair_1m_gain = fx2_1m_archive - pair_1m_archive
    pair_10m_gain = fx2_10m_archive - pair_10m_archive
    tail_gain = pair_10m_gain - pair_1m_gain
    tail_rate = tail_gain / 9
    projected_tail_gross = pair_1m_gain + 999 * tail_rate
    disjoint_pair_gain = disjoint_fx2_archive - disjoint_pair_archive
    disjoint_native_gain = disjoint_fx2_archive - disjoint_native112_archive
    disjoint_increment = disjoint_native112_archive - disjoint_pair_archive
    return {
        "pair_first_1m_gross_saved_bytes": pair_1m_gain,
        "pair_first_1m_increment_over_native112_bytes": (
            native112_1m_archive - pair_1m_archive
        ),
        "pair_cumulative_10m_gross_saved_bytes": pair_10m_gain,
        "pair_cumulative_10m_gross_saved_bytes_per_1m": pair_10m_gain / 10,
        "pair_cumulative_10m_increment_over_native112_bytes": (
            native112_10m_archive - pair_10m_archive
        ),
        "pair_1m_to_10m_tail_bytes_per_1m": tail_rate,
        "pair_tail_projected_1g_gross_saved_bytes": projected_tail_gross,
        "disjoint_native112_gross_saved_bytes": disjoint_native_gain,
        "disjoint_pair_gross_saved_bytes": disjoint_pair_gain,
        "disjoint_pair_increment_over_native112_bytes": disjoint_increment,
        "disjoint_pair_clears_required_rate": (
            disjoint_pair_gain >= REQUIRED_GROSS_BYTES_PER_1M
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--wrapper-receipt",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "fx2_cmix21_lstm112_plus80_wrapper_proof_10m_v1/receipt.json"
        ),
    )
    parser.add_argument(
        "--native112-1m",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/fx2_cmix21_runtime_frontier_1m_v1/"
            "no_paq_lstm112x2_ofast_native_lto_geometry_1m/receipt.json"
        ),
    )
    parser.add_argument(
        "--pair-1m",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/fx2_cmix21_recurrent_ensemble_1m_v1/"
            "nopaq_lstm112x2_plus80x2_native_source_geometry_1m/receipt.json"
        ),
    )
    parser.add_argument(
        "--native112-10m",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/fx2_cmix21_runtime_frontier_10m_v1/"
            "nopaq_lstm112x2_native_source_geometry_title_10m/receipt.json"
        ),
    )
    parser.add_argument(
        "--pair-10m",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/fx2_cmix21_recurrent_ensemble_10m_v1/"
            "nopaq_lstm112x2_plus80x2_native_source_geometry_title_10m/receipt.json"
        ),
    )
    disjoint_root = Path(
        "/home/x/enwiki9-nonproof/results/fx2_cmix21_disjoint_1m_v2/"
        "offset500000000"
    )
    parser.add_argument(
        "--disjoint-native112",
        type=Path,
        default=disjoint_root
        / "nopaq_lstm112x2_native_source_geometry_offset500m_1m/receipt.json",
    )
    parser.add_argument(
        "--disjoint-pair",
        type=Path,
        default=disjoint_root
        / "nopaq_lstm112x2_plus80x2_native_source_geometry_offset500m_1m/receipt.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "projects/enwiki9/results/"
            "fx2_cmix21_lstm112_plus80_terminal_v1/receipt.json"
        ),
    )
    args = parser.parse_args()

    paths = (
        args.wrapper_receipt,
        args.native112_1m,
        args.pair_1m,
        args.native112_10m,
        args.pair_10m,
        args.disjoint_native112,
        args.disjoint_pair,
    )
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)

    wrapper = load_object(args.wrapper_receipt)
    native112_1m = load_object(args.native112_1m)
    pair_1m = load_object(args.pair_1m)
    native112_10m = load_object(args.native112_10m)
    pair_10m = load_object(args.pair_10m)
    disjoint_native = load_object(args.disjoint_native112)
    disjoint_pair = load_object(args.disjoint_pair)

    required_wrapper = {
        "archive_payload_identity": True,
        "roundtrip_ok": True,
        "determinism_ok": True,
        "proof_complete": True,
    }
    for key, expected in required_wrapper.items():
        if wrapper.get("result", {}).get(key) is not expected:
            raise RuntimeError(f"wrapper proof did not pass {key}")
    if wrapper.get("scope_raw_bytes") != EXPECTED_SCOPE_10M:
        raise RuntimeError("wrapper proof is not exact 10M")
    for key in ("archive_a", "archive_b", "restored", "source_archive"):
        require_artifact(wrapper["artifacts"][key])
    if wrapper["artifacts"]["archive_a"]["sha256"] != wrapper["artifacts"]["archive_b"]["sha256"]:
        raise RuntimeError("wrapper archives are not deterministic")

    for name, row in (
        ("native112_1m", native112_1m),
        ("pair_1m", pair_1m),
        ("disjoint_native112", disjoint_native),
        ("disjoint_pair", disjoint_pair),
    ):
        if row.get("scope_raw_bytes") != EXPECTED_SCOPE_1M:
            raise RuntimeError(f"{name} is not exact 1M")
        if row.get("clean_guard") is not True:
            raise RuntimeError(f"{name} did not finish under a clean guard")
        require_artifact(row["archive"])
        require_artifact(row["input"])
        require_artifact(row["baseline"]["artifact"])
    for name, row in (("native112_10m", native112_10m), ("pair_10m", pair_10m)):
        if row.get("scope_raw_bytes") != EXPECTED_SCOPE_10M:
            raise RuntimeError(f"{name} is not exact 10M")
        if row.get("clean_guard") is not True:
            raise RuntimeError(f"{name} did not finish under a clean guard")
        require_artifact(row["archive"])
        require_artifact(row["input"])
        require_artifact(row["baseline"]["artifact"])

    for key in ("input",):
        if disjoint_native[key]["sha256"] != disjoint_pair[key]["sha256"]:
            raise RuntimeError("disjoint candidates used different inputs")
    if (
        disjoint_native["baseline"]["artifact"]["sha256"]
        != disjoint_pair["baseline"]["artifact"]["sha256"]
    ):
        raise RuntimeError("disjoint candidates used different FX2 baselines")

    metrics = summarize_metrics(
        fx2_1m_archive=pair_1m["baseline"]["artifact"]["bytes"],
        native112_1m_archive=native112_1m["archive"]["bytes"],
        pair_1m_archive=pair_1m["archive"]["bytes"],
        fx2_10m_archive=pair_10m["baseline"]["artifact"]["bytes"],
        native112_10m_archive=native112_10m["archive"]["bytes"],
        pair_10m_archive=pair_10m["archive"]["bytes"],
        disjoint_fx2_archive=disjoint_pair["baseline"]["artifact"]["bytes"],
        disjoint_native112_archive=disjoint_native["archive"]["bytes"],
        disjoint_pair_archive=disjoint_pair["archive"]["bytes"],
    )
    if metrics["disjoint_pair_increment_over_native112_bytes"] != 4:
        raise RuntimeError("unexpected disjoint 112+80 increment")
    if metrics["disjoint_pair_clears_required_rate"] is not False:
        raise RuntimeError("disjoint pair unexpectedly clears the counted rate")

    receipt = {
        "schema": "fx2_cmix21_lstm112_plus80_terminal_decision_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "exact_constructive_10m_wrapper_plus_reset_disjoint_1m",
        "artifacts": {
            "wrapper_receipt": artifact(args.wrapper_receipt),
            "native112_first_1m_receipt": artifact(args.native112_1m),
            "pair_first_1m_receipt": artifact(args.pair_1m),
            "native112_cumulative_10m_receipt": artifact(args.native112_10m),
            "pair_cumulative_10m_receipt": artifact(args.pair_10m),
            "disjoint_native112_receipt": artifact(args.disjoint_native112),
            "disjoint_pair_receipt": artifact(args.disjoint_pair),
        },
        "wrapper_proof": wrapper["result"],
        "metrics": metrics,
        "decision": {
            "verdict": "retire_unchanged_112_plus80_from_promotion",
            "promotion_authorized": False,
            "larger_gate_authorized": False,
            "secondary_width_search_authorized": False,
            "preserve_constructive_wrapper_proof": True,
            "next_endpoint_family": "decoder_built_wrt_phrase_page_memory",
            "reason": (
                "The exact source wrapper is constructive, but the untouched "
                "offset-500M reset slice retains only 4 B/M increment over "
                "native 112 and 353 B/M total versus FX2, below the counted "
                "786.375 B/M requirement."
            ),
        },
        "claim_boundary": (
            "This receipt proves a deterministic, roundtripping 10M wrapper and "
            "a matched reset-slice generalization failure. It is not a cumulative "
            "1G score or proof that all recurrent mechanisms are ineffective."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(args.output.resolve())
    print(json.dumps(receipt["decision"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
