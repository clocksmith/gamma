#!/usr/bin/env python3
"""Build and certify the full-corpus NNCP symbol-to-raw map."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import tarfile


EXPECTED_SOURCE_SHA256 = (
    "7b4be2a5871186b82cd5f1c6137a8f6fed0d0c6b2bb281793db1f0be65831119"
)
EXPECTED_INPUT_BYTES = 1_000_000_000
MINIMUM_FREE_BYTES = 30_000_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command: list[str], *, cwd: Path, environment: dict[str, str]) -> None:
    subprocess.run(command, cwd=cwd, env=environment, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--result-dir", required=True, type=Path)
    args = parser.parse_args()

    if sha256(args.source_package) != EXPECTED_SOURCE_SHA256:
        raise ValueError("source package differs from frozen NNCP v3.3 object")
    if args.input.stat().st_size != EXPECTED_INPUT_BYTES:
        raise ValueError("input is not the complete 1,000,000,000-byte corpus")
    if args.work_dir.exists():
        raise ValueError("work directory already exists")
    if shutil.disk_usage(args.work_dir.parent).free < MINIMUM_FREE_BYTES:
        raise ValueError("insufficient free storage for bound mapping artifacts")

    args.work_dir.mkdir(parents=True)
    args.result_dir.mkdir(parents=True, exist_ok=True)
    source_parent = args.work_dir / "source"
    source_parent.mkdir()
    with tarfile.open(args.source_package, "r:*") as archive:
        archive.extractall(source_parent)
    roots = [path for path in source_parent.iterdir() if path.is_dir()]
    if len(roots) != 1:
        raise ValueError("unexpected source archive layout")
    source = roots[0]

    project = Path(__file__).resolve().parents[1]
    patch = project / "patches" / "nncp_symbol_raw_map_v1.patch"
    run(
        ["patch", "-p1", "-i", str(patch)],
        cwd=source,
        environment=os.environ.copy(),
    )
    run(["make", "-j2"], cwd=source, environment=os.environ.copy())

    binary = source / "nncp"
    dictionary = args.work_dir / "dictionary.bin"
    preprocessed = args.work_dir / "preprocessed.bin"
    restored = args.work_dir / "restored.raw"
    symbol_map = args.work_dir / "symbol_raw_map.bin"

    base_environment = os.environ.copy()
    base_environment["LD_LIBRARY_PATH"] = str(source)
    run(
        [
            str(binary),
            "--preprocess",
            "16384,512",
            "--dict",
            str(dictionary),
            "pc",
            str(args.input),
            str(preprocessed),
        ],
        cwd=source,
        environment=base_environment,
    )
    map_environment = base_environment.copy()
    map_environment["NNCP_SYMBOL_MAP_TRACE"] = str(symbol_map)
    run(
        [
            str(binary),
            "--dict",
            str(dictionary),
            "pd",
            str(preprocessed),
            str(restored),
        ],
        cwd=source,
        environment=map_environment,
    )

    receipt = args.result_dir / "map_receipt.json"
    verifier = project / "tools" / "verify_nncp_symbol_map.py"
    run(
        [
            "python3",
            str(verifier),
            "--source-tar",
            str(args.source_package),
            "--patch",
            str(patch),
            "--binary",
            str(binary),
            "--raw-input",
            str(args.input),
            "--dictionary",
            str(dictionary),
            "--preprocessed",
            str(preprocessed),
            "--symbol-map",
            str(symbol_map),
            "--restored",
            str(restored),
            "--output",
            str(receipt),
        ],
        cwd=project,
        environment=base_environment,
    )

    manifest = args.result_dir / "window_manifest.json"
    manifest_tool = project / "tools" / "nncp_native_window_manifest.py"
    run(
        [
            "python3",
            str(manifest_tool),
            "--symbol-map",
            str(symbol_map),
            "--map-receipt",
            str(receipt),
            "--output",
            str(manifest),
        ],
        cwd=project,
        environment=base_environment,
    )

    map_receipt = json.loads(receipt.read_text())
    window_manifest = json.loads(manifest.read_text())
    decision = {
        "artifacts": {
            "map_receipt": {
                "bytes": receipt.stat().st_size,
                "path": str(receipt.resolve()),
                "sha256": sha256(receipt),
            },
            "window_manifest": {
                "bytes": manifest.stat().st_size,
                "path": str(manifest.resolve()),
                "sha256": sha256(manifest),
            },
        },
        "claim_boundary": (
            "Exact full-corpus reversible preprocessing and raw-to-symbol "
            "window binding only. No teacher probabilities or score credit."
        ),
        "full_corpus_dictionary": map_receipt["artifacts"]["dictionary"],
        "input": map_receipt["artifacts"]["raw_input"],
        "maximum_child_rss_kib": resource.getrusage(
            resource.RUSAGE_CHILDREN
        ).ru_maxrss,
        "preprocessed_symbols": map_receipt["artifacts"][
            "preprocessed_symbols"
        ],
        "proof": map_receipt["proof"],
        "schema": "nncp_full_symbol_map_gate_v1",
        "score_credit_bytes": 0,
        "state": "PASS",
        "symbol_map": map_receipt["artifacts"]["symbol_map"],
        "windows": window_manifest["windows"],
    }
    decision_path = args.result_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
