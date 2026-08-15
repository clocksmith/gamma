#!/usr/bin/env python3
"""Convert named-gradient energy reductions before F32 scalar reads."""

from __future__ import annotations

import argparse
from pathlib import Path

from materialize_nncp_named_midpoint_gradient_q1 import materialize as materialize_q1
from materialize_nncp_output_head_attribution import replace_once


def materialize(source_root: Path) -> None:
    materialize_q1(source_root)
    path = source_root / "nncp.c"
    source = path.read_text()
    source = replace_once(
        source,
        "sum = nc_sum(nc_mul(nc_dup_tensor(gradient), nc_dup_tensor(gradient)));",
        "sum = nc_convert(nc_sum(nc_mul(nc_dup_tensor(gradient), "
        "nc_dup_tensor(gradient))), NC_TYPE_F32);",
        "named-gradient energy scalar type",
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
