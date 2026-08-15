#!/usr/bin/env python3
"""Reduce named-gradient squared energy directly into an F32 scalar."""

from __future__ import annotations

import argparse
from pathlib import Path

from materialize_nncp_named_midpoint_gradient_q2 import materialize as materialize_q2
from materialize_nncp_output_head_attribution import replace_once


def materialize(source_root: Path) -> None:
    materialize_q2(source_root)
    path = source_root / "nncp.c"
    source = path.read_text()
    source = replace_once(
        source,
        "sum = nc_convert(nc_sum(nc_mul(nc_dup_tensor(gradient), "
        "nc_dup_tensor(gradient))), NC_TYPE_F32);",
        "sum = nc_reduce_sum_sqr(nc_dup_tensor(gradient));",
        "direct F32 named-gradient energy reduction",
    )
    source = replace_once(
        source,
        "    NCTensor *sum;\n"
        "    float energy;\n"
        "    BOOL finite;",
        "    NCTensor *sum, *reference_sum;\n"
        "    float energy, reference_energy, relative_delta;\n"
        "    BOOL finite, reference_finite;",
        "direct F32 named-gradient reference declarations",
    )
    source = replace_once(
        source,
        "    energy = nc_get_scalar_f32(sum);\n"
        "    nc_free_tensor(sum);",
        "    energy = nc_get_scalar_f32(sum);\n"
        "    nc_free_tensor(sum);\n"
        "    reference_sum = nc_convert(nc_dup_tensor(gradient), NC_TYPE_F32);\n"
        "    reference_sum = nc_sum(nc_mul(nc_dup_tensor(reference_sum), "
        "reference_sum));\n"
        "    reference_energy = nc_get_scalar_f32(reference_sum);\n"
        "    nc_free_tensor(reference_sum);\n"
        "    relative_delta = fabsf(energy - reference_energy) /\n"
        "        fmaxf(fabsf(reference_energy), 0x1p-126f);\n"
        "    reference_finite = isfinite(energy) && isfinite(reference_energy) &&\n"
        "        isfinite(relative_delta);",
        "direct F32 named-gradient cross-path reference",
    )
    source = replace_once(
        source,
        '            "param_elems=%zu energy=%a finite=%d\\n",',
        '            "param_elems=%zu energy=%a finite=%d reference_energy=%a "\n'
        '            "reference_finite=%d relative_delta=%a\\n",',
        "direct F32 named-gradient reference format",
    )
    source = replace_once(
        source,
        "            energy, finite);",
        "            energy, finite, reference_energy, reference_finite,\n"
        "            relative_delta);",
        "direct F32 named-gradient reference values",
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
