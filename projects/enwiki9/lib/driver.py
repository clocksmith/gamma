"""Run a single program against enwik9 and emit a result JSON.

Usage: python3 lib/driver.py <program_id> [--data PATH] [--limit BYTES]
                              [--check-determinism] [--no-save]

The driver:
  1. loads programs/<program_id>/program.py
  2. reads the dataset (or a prefix when --limit is set)
  3. compresses, decompresses, verifies the roundtrip
  4. measures sizes, times, and bits/byte
  5. (optional) compresses a second time and verifies byte-equal output
  6. writes results/<program_id>/<timestamp>.json
  7. prints the result
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import pathlib
import platform
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DEFAULT = ROOT / "data" / "enwik9"


def _load(program_id: str):
    path = ROOT / "programs" / program_id / "program.py"
    if not path.exists():
        raise SystemExit(f"program not found: {path}")
    spec = importlib.util.spec_from_file_location(f"prog_{program_id}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in ("compress", "decompress"):
        if not callable(getattr(mod, name, None)):
            raise SystemExit(f"{program_id}: missing callable {name}()")
    return mod, path


def run(
    program_id: str,
    data_path: pathlib.Path,
    limit: int | None,
    check_determinism: bool = False,
) -> dict:
    mod, src_path = _load(program_id)
    raw = data_path.read_bytes()
    if limit is not None:
        raw = raw[:limit]

    t0 = time.perf_counter()
    compressed = mod.compress(raw)
    t_compress = time.perf_counter() - t0
    stats_fn = getattr(mod, "stats", None)
    program_stats = stats_fn() if callable(stats_fn) else None

    t0 = time.perf_counter()
    decompressed = mod.decompress(compressed)
    t_decompress = time.perf_counter() - t0

    ok = decompressed == raw
    program_dir = src_path.parent
    program_files: list[tuple[str, int]] = []
    for child in sorted(program_dir.iterdir()):
        if child.name in ("meta.json", "__pycache__") or child.name.startswith("."):
            continue
        if child.is_file():
            program_files.append((child.name, child.stat().st_size))
    program_size = sum(sz for _, sz in program_files)
    compressed_size = len(compressed)
    archive_md5 = hashlib.md5(compressed).hexdigest()
    archive_sha256 = hashlib.sha256(compressed).hexdigest()

    determinism: dict | None = None
    if check_determinism:
        compressed2 = mod.compress(raw)
        det_ok = compressed == compressed2
        det_md5 = hashlib.md5(compressed2).hexdigest()
        det_sha256 = hashlib.sha256(compressed2).hexdigest()
        determinism = {
            "single_host_byte_equal": det_ok,
            "first_run_md5": archive_md5,
            "second_run_md5": det_md5,
            "first_run_sha256": archive_sha256,
            "second_run_sha256": det_sha256,
            "first_divergence_byte": None
            if det_ok
            else next(
                (i for i, (a, b) in enumerate(zip(compressed, compressed2)) if a != b),
                min(len(compressed), len(compressed2)),
            ),
        }

    bits_per_byte = (compressed_size * 8 / len(raw)) if raw else 0.0

    result = {
        "program_id": program_id,
        "data_path": str(data_path),
        "data_size": len(raw),
        "data_md5": hashlib.md5(raw).hexdigest(),
        "data_sha256": hashlib.sha256(raw).hexdigest(),
        "compressed_size": compressed_size,
        "compressed_md5": archive_md5,
        "compressed_sha256": archive_sha256,
        "program_size": program_size,
        "program_files": program_files,
        "hutter_score": compressed_size + program_size,
        "bits_per_byte": round(bits_per_byte, 6),
        "compress_time_s": round(t_compress, 4),
        "decompress_time_s": round(t_decompress, 4),
        "roundtrip_ok": ok,
        "determinism": determinism,
        "host": {
            "machine": platform.machine(),
            "system": platform.system(),
            "python": platform.python_version(),
            "node": platform.node(),
        },
        "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
    }
    if program_stats is not None:
        result["program_stats"] = program_stats
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("program_id")
    ap.add_argument("--data", type=pathlib.Path, default=DATA_DEFAULT)
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="only use the first N bytes (smoke testing)",
    )
    ap.add_argument(
        "--check-determinism",
        action="store_true",
        help="compress twice and verify byte-equal output (single-host determinism)",
    )
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()

    if not args.data.exists():
        raise SystemExit(f"dataset missing at {args.data} — run bench.py --setup first")

    result = run(args.program_id, args.data, args.limit, args.check_determinism)

    if not args.no_save:
        out_dir = ROOT / "results" / args.program_id
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = result["timestamp"].replace(":", "")
        (out_dir / f"{stamp}.json").write_text(json.dumps(result, indent=2) + "\n")

    print(json.dumps(result, indent=2))
    return 0 if result["roundtrip_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
