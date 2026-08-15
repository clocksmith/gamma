#!/usr/bin/env python3
"""Fix LibNC reference ownership in named-gradient finiteness capture."""

from __future__ import annotations

import argparse
from pathlib import Path

from materialize_nncp_named_midpoint_gradient import materialize as materialize_q0
from materialize_nncp_output_head_attribution import replace_once


def materialize(source_root: Path) -> None:
    materialize_q0(source_root)
    path = source_root / "nncp.c"
    source = path.read_text()
    source = replace_once(
        source,
        "finite = nc_tensor_isfinite(gradient);",
        "finite = nc_tensor_isfinite(nc_dup_tensor(gradient));",
        "named-gradient finiteness reference ownership",
    )
    path.write_text(source)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    args = parser.parse_args()
    materialize(args.source_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
