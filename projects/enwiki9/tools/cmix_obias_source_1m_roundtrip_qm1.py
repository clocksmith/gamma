#!/usr/bin/env python3
"""Repair q0's Git-LFS export, then run its unchanged source-build proof."""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

import cmix_obias_source_1m_roundtrip_qm0 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_1m_roundtrip_qm1_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
PROFILE_PATH = "cmix-obias/pgo_data_asbuilt/default.profdata"
ORIGINAL_COMMAND = parent.command


def materialize_profile(source: Path) -> dict[str, object]:
    pointer = subprocess.check_output(
        ["git", "-C", str(parent.DONOR), "show", f"HEAD:{PROFILE_PATH}"]
    )
    pointer_sha256 = hashlib.sha256(pointer).hexdigest()
    if not pointer.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        raise ValueError("tracked PGO object is not a Git-LFS pointer")
    target = source / "pgo_data_asbuilt/default.profdata"
    with target.open("wb") as output:
        completed = subprocess.run(
            ["git", "-C", str(parent.DONOR), "lfs", "smudge"],
            input=pointer,
            stdout=output,
            stderr=subprocess.PIPE,
            check=True,
        )
    materialized_sha256 = parent.sha256(target)
    if materialized_sha256 != parent.EXPECTED["profile"]:
        raise ValueError("materialized Git-LFS PGO object mismatch")
    return {
        "path": PROFILE_PATH,
        "pointer_bytes": len(pointer),
        "pointer_sha256": pointer_sha256,
        "materialized_bytes": target.stat().st_size,
        "materialized_sha256": materialized_sha256,
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
    }


def command(
    args: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
) -> dict[str, object]:
    receipt = ORIGINAL_COMMAND(args, cwd=cwd, environment=environment)
    if args and args[0] == "tar" and "-xf" in args and "-C" in args:
        source = Path(args[args.index("-C") + 1])
        receipt["git_lfs_materialization"] = materialize_profile(source)
    return receipt


def main() -> int:
    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.RESULT = RESULT
    parent.command = command
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
