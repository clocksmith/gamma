#!/usr/bin/env python3
"""Execute the sealed orphan-adoption observer from its candidate snapshot."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1"
RESULT = PROJECT / "results" / CANDIDATE_ID


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    output = args.output_dir
    if not output.is_absolute():
        output = PROJECT / output
    if output.resolve(strict=True) != RESULT.resolve(strict=True):
        raise RuntimeError("output directory differs from the frozen result root")

    snapshot_id = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID")
    snapshot_text = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT")
    revision_text = os.environ.get("GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON")
    experiment_text = os.environ.get("GAMMA_ENWIKI9_EXPERIMENT_JSON")
    if not all((snapshot_id, snapshot_text, revision_text, experiment_text)):
        raise RuntimeError("adaptive snapshot and evidence bindings are required")
    if snapshot_id != CANDIDATE_ID:
        raise RuntimeError("adaptive snapshot identifies another candidate")
    revision = json.loads(revision_text)
    if revision.get("candidateId") != CANDIDATE_ID:
        raise RuntimeError("adaptive revision identifies another candidate")
    if not isinstance(json.loads(experiment_text), dict):
        raise RuntimeError("adaptive experiment reference is malformed")

    snapshot = Path(snapshot_text).resolve(strict=True)
    program = snapshot / "program.py"
    info = os.lstat(program)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise RuntimeError("sealed observer program is not a regular file")

    environment = os.environ.copy()
    arguments = [
        sys.executable,
        str(program),
        "--project-root",
        str(PROJECT),
        "--output-dir",
        str(output),
    ]
    os.execve(sys.executable, arguments, environment)
    raise AssertionError("execve returned")


if __name__ == "__main__":
    raise SystemExit(main())
