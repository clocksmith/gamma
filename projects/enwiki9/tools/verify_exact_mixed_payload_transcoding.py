#!/usr/bin/env python3
"""Verify EPT-1 for gzip-to-XZ executable and source-tar payloads."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import lzma
import pathlib


def identity(old: pathlib.Path, new: pathlib.Path) -> dict[str, object]:
    old_data = gzip.decompress(old.read_bytes())
    new_data = lzma.decompress(new.read_bytes())
    if old_data != new_data:
        raise AssertionError(f"recovered payload mismatch: {old.name}")
    return {"bytes": len(old_data), "sha256": hashlib.sha256(old_data).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-binary", type=pathlib.Path, required=True)
    parser.add_argument("--new-binary", type=pathlib.Path, required=True)
    parser.add_argument("--old-source", type=pathlib.Path, required=True)
    parser.add_argument("--new-source", type=pathlib.Path, required=True)
    parser.add_argument("--old-wrapper", type=pathlib.Path, required=True)
    parser.add_argument("--new-wrapper", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    payloads = {
        "cmix_binary": identity(args.old_binary, args.new_binary),
        "nncp_source_tar": identity(args.old_source, args.new_source),
    }
    old_wrapper = args.old_wrapper.read_text()
    expected_wrapper = (
        old_wrapper.replace("import gzip", "import lzma")
        .replace("cmix.bin.gz", "cmix.bin.xz")
        .replace("nncp_cpu_source.tar.gz", "nncp_cpu_source.tar.xz")
        .replace("gzip.open", "lzma.open")
        .replace('"r:gz"', '"r:xz"')
        .replace("'r:gz'", "'r:xz'")
    )
    if args.new_wrapper.read_text() != expected_wrapper:
        raise AssertionError("wrapper edit exceeds frozen mixed-payload grammar")

    old_package = sum(
        path.stat().st_size
        for path in (args.old_binary, args.old_source, args.old_wrapper)
    )
    new_package = sum(
        path.stat().st_size
        for path in (args.new_binary, args.new_source, args.new_wrapper)
    )
    receipt = {
        "schema": "exact_mixed_payload_transcoding_receipt_v1",
        "payload_identity": payloads,
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

