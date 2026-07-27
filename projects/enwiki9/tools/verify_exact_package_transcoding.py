#!/usr/bin/env python3
"""Verify EPT-1 recovered-payload identity and exact package delta."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import lzma
import pathlib


def digest(data: bytes) -> dict[str, object]:
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-binary", type=pathlib.Path, required=True)
    parser.add_argument("--new-binary", type=pathlib.Path, required=True)
    parser.add_argument("--old-dictionary", type=pathlib.Path, required=True)
    parser.add_argument("--new-dictionary", type=pathlib.Path, required=True)
    parser.add_argument("--old-wrapper", type=pathlib.Path, required=True)
    parser.add_argument("--new-wrapper", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    old_binary = gzip.decompress(args.old_binary.read_bytes())
    new_binary = lzma.decompress(args.new_binary.read_bytes())
    old_dictionary = gzip.decompress(args.old_dictionary.read_bytes())
    new_dictionary = lzma.decompress(args.new_dictionary.read_bytes())
    if old_binary != new_binary or old_dictionary != new_dictionary:
        raise AssertionError("recovered payload mismatch")

    old_source = args.old_wrapper.read_text()
    expected_source = (
        old_source.replace("import gzip", "import lzma")
        .replace("cmix.bin.gz", "cmix.bin.xz")
        .replace("english.dic.gz", "english.dic.xz")
        .replace("gzip.open", "lzma.open")
    )
    new_source = args.new_wrapper.read_text()
    if new_source != expected_source:
        raise AssertionError("wrapper edit exceeds frozen EPT-1 grammar")

    old_package = (
        args.old_binary.stat().st_size
        + args.old_dictionary.stat().st_size
        + args.old_wrapper.stat().st_size
    )
    new_package = (
        args.new_binary.stat().st_size
        + args.new_dictionary.stat().st_size
        + args.new_wrapper.stat().st_size
    )
    receipt = {
        "schema": "exact_package_transcoding_receipt_v1",
        "payload_identity": {
            "binary": digest(old_binary),
            "dictionary": digest(old_dictionary),
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

