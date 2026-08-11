#!/usr/bin/env python3
"""Correction-only launcher for the production attribution gate."""

from __future__ import annotations

from pathlib import Path
import tempfile

import nncp_libnc_output_head_midpoint_attribution_65536_qm0 as q0


CANDIDATE_ID = "nncp_libnc_output_head_midpoint_attribution_65536_qm1_v1"
PROGRAM = q0.ROOT / "programs" / CANDIDATE_ID
RESULT = q0.ROOT / "results" / CANDIDATE_ID


def extract_into_existing(target: Path) -> dict[str, object]:
    """Extract into q0's already-created temporary source directory."""
    return q0.bridge.run(
        ["tar", "-xzf", str(q0.SOURCE_TAR), "--strip-components=1", "-C", str(target)],
        cwd=target.parent,
    )


def source_package(path: Path) -> dict[str, object]:
    members = [
        PROGRAM / "program.py",
        PROGRAM / "nncp_midsegment32.patch",
        q0.MATERIALIZER,
        Path(__file__),
        Path(q0.__file__),
    ]
    with tempfile.TemporaryDirectory(prefix="nncp-attribution-qm1-package-") as temporary:
        tar_path = Path(temporary) / "source.tar"
        with q0.tarfile.open(tar_path, "w") as archive:
            for member in members:
                archive.add(member, arcname=member.relative_to(q0.ROOT))
        path.write_bytes(
            q0.lzma.compress(tar_path.read_bytes(), preset=9 | q0.lzma.PRESET_EXTREME)
        )
    return q0.artifact(path)


def main() -> int:
    q0.CANDIDATE_ID = CANDIDATE_ID
    q0.PROGRAM = PROGRAM
    q0.RESULT = RESULT
    q0.MIDPOINT_PATCH = PROGRAM / "nncp_midsegment32.patch"
    q0.bridge.extract_source = extract_into_existing
    q0.source_package = source_package
    return q0.main()


if __name__ == "__main__":
    raise SystemExit(main())
