#!/usr/bin/env python3
"""Finalize a completed NNCP full symbol map after window binding."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol-map", required=True, type=Path)
    parser.add_argument("--map-receipt", required=True, type=Path)
    parser.add_argument("--result-dir", required=True, type=Path)
    parser.add_argument("--parent-job-id", required=True)
    args = parser.parse_args()

    args.result_dir.mkdir(parents=True, exist_ok=True)
    project = Path(__file__).resolve().parents[1]
    manifest = args.result_dir / "window_manifest.json"
    subprocess.run(
        [
            "python3",
            str(project / "tools" / "nncp_native_window_manifest.py"),
            "--symbol-map",
            str(args.symbol_map),
            "--map-receipt",
            str(args.map_receipt),
            "--output",
            str(manifest),
        ],
        check=True,
        env=os.environ.copy(),
        cwd=project,
    )

    receipt = json.loads(args.map_receipt.read_text())
    windows = json.loads(manifest.read_text())
    decision = {
        "artifacts": {
            "map_receipt": {
                "bytes": args.map_receipt.stat().st_size,
                "path": str(args.map_receipt.resolve()),
                "sha256": sha256(args.map_receipt),
            },
            "window_manifest": {
                "bytes": manifest.stat().st_size,
                "path": str(manifest.resolve()),
                "sha256": sha256(manifest),
            },
        },
        "claim_boundary": (
            "Exact full-corpus reversible preprocessing and raw-to-symbol "
            "window binding only. No teacher probabilities or score credit."
        ),
        "full_corpus_dictionary": receipt["artifacts"]["dictionary"],
        "input": receipt["artifacts"]["raw_input"],
        "parent_mapping_job": {
            "job_id": args.parent_job_id,
            "terminal_state": "failed_after_map_pass_before_manifest",
        },
        "preprocessed_symbols": receipt["artifacts"]["preprocessed_symbols"],
        "proof": receipt["proof"],
        "reused_completed_hash_bound_map": True,
        "schema": "nncp_full_symbol_map_gate_v1",
        "score_credit_bytes": 0,
        "state": "PASS",
        "symbol_map": receipt["artifacts"]["symbol_map"],
        "windows": windows["windows"],
    }
    decision_path = args.result_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
