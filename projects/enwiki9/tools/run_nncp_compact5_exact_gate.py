#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "projects" / "enwiki9" / "tools" / (
    "run_nncp_compact5_preprocessed_gate.sh"
)
SOURCE_SHA256 = (
    "7b4be2a5871186b82cd5f1c6137a8f6fed0d0c6b2bb281793db1f0be65831119"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def write_prefix(source: Path, destination: Path, limit: int) -> None:
    remaining = limit
    with source.open("rb") as src, destination.open("wb") as dst:
        while remaining:
            chunk = src.read(min(1 << 20, remaining))
            if not chunk:
                raise EOFError(f"input ended before {limit} bytes")
            dst.write(chunk)
            remaining -= len(chunk)


def run_logged(command: list[str], log_path: Path, env: dict[str, str]) -> float:
    started = time.monotonic()
    with log_path.open("wb") as log:
        subprocess.run(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
            env=env,
        )
    return time.monotonic() - started


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--archive-ceiling", type=int, required=True)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()

    if args.limit <= 0 or args.archive_ceiling <= 0 or args.threads <= 0:
        raise ValueError("limit, archive ceiling, and threads must be positive")

    args.result_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.result_dir / "input.raw"
    archive1 = args.result_dir / "archive.first.bin"
    archive2 = args.result_dir / "archive.second.bin"
    decoded = args.result_dir / "decoded.raw"
    write_prefix(args.input, prefix, args.limit)

    env = dict(os.environ)
    env["NNCP_THREADS"] = str(args.threads)
    common = ["sh", str(RUNNER), str(args.build_dir), str(prefix)]
    encode1_s = run_logged(
        [*common, str(archive1)],
        args.result_dir / "encode.first.log",
        env,
    )

    source_dir = args.build_dir / "nncp-2024-06-05"
    decode_s = run_logged(
        [
            "env",
            f"LD_LIBRARY_PATH={source_dir}",
            str(source_dir / "nncp"),
            "d",
            str(archive1),
            str(decoded),
        ],
        args.result_dir / "decode.log",
        env,
    )

    encode2_s = run_logged(
        [*common, str(archive2)],
        args.result_dir / "encode.second.log",
        env,
    )

    input_hash = sha256(prefix)
    decoded_hash = sha256(decoded)
    archive1_hash = sha256(archive1)
    archive2_hash = sha256(archive2)
    archive_bytes = archive1.stat().st_size
    roundtrip = prefix.stat().st_size == decoded.stat().st_size and (
        input_hash == decoded_hash
    )
    deterministic = (
        archive_bytes == archive2.stat().st_size
        and archive1_hash == archive2_hash
    )
    ceiling_ok = archive_bytes <= args.archive_ceiling
    receipt = {
        "schema": "nncp_compact5_preprocessed_exact_gate_v1",
        "profile": {
            "base": "enwik9",
            "batch_size": 1,
            "n_layer": 5,
            "d_model": 256,
            "d_inner": 768,
            "preprocess": "16384,512",
            "threads": args.threads,
        },
        "source_tar_sha256": SOURCE_SHA256,
        "input_bytes": prefix.stat().st_size,
        "input_sha256": input_hash,
        "archive_bytes": archive_bytes,
        "archive_sha256": archive1_hash,
        "decoded_bytes": decoded.stat().st_size,
        "decoded_sha256": decoded_hash,
        "second_archive_bytes": archive2.stat().st_size,
        "second_archive_sha256": archive2_hash,
        "archive_ceiling_bytes": args.archive_ceiling,
        "archive_ceiling_ok": ceiling_ok,
        "roundtrip_ok": roundtrip,
        "determinism_ok": deterministic,
        "compression_first_elapsed_s": encode1_s,
        "decompression_elapsed_s": decode_s,
        "compression_second_elapsed_s": encode2_s,
        "score_credit_bytes": 0,
    }
    (args.result_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    if not (roundtrip and deterministic and ceiling_ok):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
