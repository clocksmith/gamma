#!/usr/bin/env python3
"""Run one source-native mature train_len=32 NNCP encode-only screen."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_trainlen32_mature_1998848_qm2_v1"
BINARY = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/nncp")
LIBRARY = BINARY.parent / "libnc.so"
PREPROCESSED = Path(
    "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
    "preprocessed.bin"
)
DICTIONARY = PREPROCESSED.parent / "dictionary.bin"
BASELINE = (
    ROOT
    / "results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/"
    "teacher_complete_block.nncp"
)
PARENT_DECISION = (
    ROOT / "results/nncp_libnc_trainlen32_surrogate_qm1_v1/decision.json"
)
EXPECTED = {
    "binary": "c3f6ee27f5ac69b58b3fc3d487d18fb2ef949f6eb197d6e709a972d80a65f34c",
    "library": "1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e",
    "preprocessed": "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5",
    "dictionary": "950683b44e6c7696f6daa896296365eb54bce8cc05ae15fff7acb5715936a0a1",
    "baseline": "00b173f3a5d964bc8f1ab8e0f07d790a891d45f7b011b1a78da86c4c96e65507",
    "parent_decision": "05a19d64ab9610c37e6772bf9b5f0304cb3dc9e264456750c92c14dd2cf40853",
}
BASELINE_BYTES = 2_042_820
SYMBOL_COUNT = 1_998_848
GAIN_GATE_BYTES = 30_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    inputs = {
        "binary": BINARY,
        "library": LIBRARY,
        "preprocessed": PREPROCESSED,
        "dictionary": DICTIONARY,
        "baseline": BASELINE,
        "parent_decision": PARENT_DECISION,
    }
    for name, path in inputs.items():
        if not path.is_file() or sha256(path) != EXPECTED[name]:
            raise ValueError(f"{name} identity mismatch")
    if BASELINE.stat().st_size != BASELINE_BYTES:
        raise ValueError("faithful mature baseline size mismatch")

    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    archive = output_dir / "candidate_encode_only.nncp"
    environment = os.environ.copy()
    environment["LD_LIBRARY_PATH"] = str(BINARY.parent)
    command = [
        str(BINARY),
        "-q",
        "-T",
        "4",
        "--profile",
        "enwik9",
        "--encode_only",
        "--n_symb",
        "16392",
        "--dict",
        str(DICTIONARY),
        "--train_len",
        "32",
        "--d_pos",
        "288",
        "--max_size",
        str(SYMBOL_COUNT),
        "c",
        str(PREPROCESSED),
        str(archive),
    ]
    print(json.dumps({"event": "mature_encode_start"}), flush=True)
    started = time.monotonic()
    completed = subprocess.run(
        command,
        check=True,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    elapsed = time.monotonic() - started
    candidate_bytes = archive.stat().st_size
    actual_gain = BASELINE_BYTES - candidate_bytes
    promotion = actual_gain >= GAIN_GATE_BYTES
    failed = [] if promotion else ["actual_mature_gain_below_30000"]
    decision = {
        "schema": "enwiki9_nncp_libnc_trainlen32_mature_1998848_qm2_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "AUTHORIZED_MATURE_CONFIRMATION" if promotion else "REJECT",
        "verdict": (
            "authorize_repeated_decodable_mature_confirmation"
            if promotion
            else "retire_mature_builtin_trainlen32_surrogate"
        ),
        "score_credit_bytes": 0,
        "claim_boundary": (
            "One exact source-native encode-only archive on a mature "
            "1,998,848-symbol population. Encode-only output is not a "
            "submission archive; no deterministic replay, decode, published "
            "score, or full-corpus credit is claimed."
        ),
        "configuration": {
            "profile": "enwik9",
            "threads": 4,
            "batch_size": 32,
            "train_len": 32,
            "relative_positions": 288,
            "symbols": SYMBOL_COUNT,
            "vocabulary": 16_392,
            "encode_only": True,
            "program_delta_bytes": 0,
        },
        "comparison": {
            "faithful_archive_bytes": BASELINE_BYTES,
            "faithful_archive_sha256": EXPECTED["baseline"],
            "candidate_archive_bytes": candidate_bytes,
            "candidate_archive_sha256": sha256(archive),
            "actual_gain_bytes": actual_gain,
            "required_actual_gain_bytes": GAIN_GATE_BYTES,
            "gain_bytes_per_million_symbols": (
                actual_gain * 1_000_000.0 / SYMBOL_COUNT
            ),
        },
        "execution": {
            "command": command,
            "elapsed_seconds": elapsed,
            "returncode": completed.returncode,
            "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        },
        "inputs": {
            name: {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": EXPECTED[name],
            }
            for name, path in inputs.items()
        },
        "failed_conditions": failed,
        "decision": {
            "promotion_authorized": promotion,
            "verified_full_1g_score_bytes": None,
            "forecast_bytes": 109_389_323,
        },
    }
    decision["inputs"]["driver_script"] = {
        "path": str(Path(__file__).resolve()),
        "bytes": Path(__file__).stat().st_size,
        "sha256": sha256(Path(__file__)),
    }
    decision_path = output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"nncp-libnc-trainlen32-mature-qm2: {error}", file=sys.stderr)
        raise
