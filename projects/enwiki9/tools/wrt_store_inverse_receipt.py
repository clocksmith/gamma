#!/usr/bin/env python3
"""Bind a stored WRT stream to its exact raw inverse."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", required=True, type=Path)
    parser.add_argument("--dictionary", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--raw-input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    for path in (args.backend, args.dictionary, args.store, args.raw_input):
        if not path.is_file():
            raise SystemExit(f"missing required artifact: {path}")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    restored = args.output_dir / "restored.raw"
    stdout_path = args.output_dir / "decode_stdout.log"
    stderr_path = args.output_dir / "decode_stderr.log"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        subprocess.run(
            [
                str(args.backend),
                "-d",
                str(args.dictionary),
                str(args.store),
                str(restored),
            ],
            stdout=stdout,
            stderr=stderr,
            check=True,
        )
    exact = (
        restored.stat().st_size == args.raw_input.stat().st_size
        and sha256(restored) == sha256(args.raw_input)
    )
    decision = {
        "schema": "gamma.wrt_store_inverse_receipt.v1",
        "artifacts": {
            "backend": artifact(args.backend),
            "dictionary": artifact(args.dictionary),
            "wrt_store": artifact(args.store),
            "raw_input": artifact(args.raw_input),
            "restored_raw": artifact(restored),
        },
        "proof": {"exact_raw_inverse": exact},
        "verdict": "PASS" if exact else "FAIL",
        "score_credit_bytes": 0,
    }
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
