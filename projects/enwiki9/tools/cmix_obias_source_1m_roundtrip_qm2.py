#!/usr/bin/env python3
"""Normalize q1 package telemetry, then run its unchanged source proof."""

from __future__ import annotations

from pathlib import Path

import cmix_obias_source_1m_roundtrip_qm1 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_1m_roundtrip_qm2_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
ORIGINAL_PACKAGE_BINARY = parent.parent.package_binary


def package_binary(
    binary: Path, source: Path, directory: Path
) -> tuple[Path, list[dict[str, object]]]:
    packaged, receipts = ORIGINAL_PACKAGE_BINARY(binary, source, directory)
    for receipt in receipts:
        receipt.setdefault(
            "scratch_usage_before_cleanup",
            parent.parent.scratch_usage(directory.parent),
        )
    return packaged, receipts


def main() -> int:
    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.RESULT = RESULT
    parent.parent.package_binary = package_binary
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
