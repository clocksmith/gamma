#!/usr/bin/env python3
"""Verify EPT-1 identity for a gzip-to-XZ tar payload substitution."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import lzma
import pathlib


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-payload", type=pathlib.Path, required=True)
    parser.add_argument("--new-payload", type=pathlib.Path, required=True)
    parser.add_argument("--old-wrapper", type=pathlib.Path, required=True)
    parser.add_argument("--new-wrapper", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    old_tar = gzip.decompress(args.old_payload.read_bytes())
    new_tar = lzma.decompress(args.new_payload.read_bytes())
    if old_tar != new_tar:
        raise AssertionError("recovered tar payload mismatch")

    old_source = args.old_wrapper.read_text()
    expected_source = (
        old_source.replace("nncp_cpu_source.tar.gz", "nncp_cpu_source.tar.xz")
        .replace('"r:gz"', '"r:xz"')
        .replace("'r:gz'", "'r:xz'")
    )
    new_source = args.new_wrapper.read_text()
    if new_source != expected_source:
        raise AssertionError("wrapper edit exceeds frozen tar substitution grammar")

    old_package = args.old_payload.stat().st_size + args.old_wrapper.stat().st_size
    new_package = args.new_payload.stat().st_size + args.new_wrapper.stat().st_size
    receipt = {
        "schema": "exact_tar_transcoding_receipt_v1",
        "recovered_tar": {
            "bytes": len(old_tar),
            "sha256": hashlib.sha256(old_tar).hexdigest(),
        },
        "wrapper_grammar_match": True,
        "old_package_bytes": old_package,
        "new_package_bytes": new_package,
        "exact_score_delta_bytes": new_package - old_package,
        "archive_identity_theorem_applies": True,
        "resource_eligibility": "unmeasured",
        "score_credit_bytes": 0,
        "verdict": "pass",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

