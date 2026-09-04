#!/usr/bin/env python3
"""Run and validate the snapshot-bound HARM sparse-input source fixture.

This tool cannot launch a compressor, open corpus data, or read the active
HORIZON scientific output.  It executes only generated fixture inputs.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "harm_delta_sparse_input_abi_q0_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot_text = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT")
    snapshot_id = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID")
    if snapshot_text is None or snapshot_id != CANDIDATE_ID:
        raise RuntimeError("exact adaptive candidate snapshot is required")
    snapshot = Path(snapshot_text).resolve()
    program = snapshot / "program.py"
    if not program.is_file():
        raise FileNotFoundError("snapshot candidate program is absent")
    output = args.output_dir.resolve()
    required_output = (PROJECT_ROOT / "results" / CANDIDATE_ID).resolve()
    if output != required_output:
        raise ValueError(f"output must be results/{CANDIDATE_ID}")
    execution = subprocess.run(
        [
            sys.executable,
            str(program),
            "--fixture",
            "--project-root",
            str(PROJECT_ROOT),
            "--output-dir",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if execution.returncode != 0:
        return execution.returncode
    decision = output / "decision.json"
    validation = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/research_contracts.py"),
            str(decision.relative_to(PROJECT_ROOT)),
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )
    return validation.returncode


if __name__ == "__main__":
    raise SystemExit(main())
