#!/usr/bin/env python3
"""Run the F32-safe named midpoint-gradient implementation retry."""

from __future__ import annotations

import lzma
from pathlib import Path
import tarfile

import nncp_delta_midas_named_midpoint_gradient as q0
import nncp_delta_midas_named_midpoint_gradient_q1 as q1
import nncp_libnc_output_head_midpoint_attribution_65536_qm0 as production_q0
import nncp_libnc_output_head_midpoint_attribution_65536_qm1 as production_q1
from materialize_nncp_named_midpoint_gradient_q2 import materialize


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "delta_midas_named_midpoint_gradient_65536_q2_v1"
MATERIALIZER = ROOT / "tools/materialize_nncp_named_midpoint_gradient_q2.py"
Q1_MATERIALIZER = ROOT / "tools/materialize_nncp_named_midpoint_gradient_q1.py"
Q0_MATERIALIZER = ROOT / "tools/materialize_nncp_named_midpoint_gradient.py"


def source_package(path: Path) -> None:
    members = [
        Path(__file__),
        Path(q1.__file__),
        Path(q0.__file__),
        MATERIALIZER,
        Q1_MATERIALIZER,
        Q0_MATERIALIZER,
        production_q0.MATERIALIZER,
        Path(production_q0.__file__),
        Path(production_q1.__file__),
    ]
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            archive.add(member, arcname=member.relative_to(ROOT))
    path.write_bytes(
        lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME)
    )
    tar_path.unlink()


def main() -> int:
    q0.CANDIDATE_ID = CANDIDATE_ID
    q0.MATERIALIZER = MATERIALIZER
    q0.materialize = materialize
    q0.execute = q1.execute
    q0.source_package = source_package
    return q0.main()


if __name__ == "__main__":
    raise SystemExit(main())
