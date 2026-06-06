"""Setup, register, and benchmark all programs in index.json.

Usage:
  python3 bench.py --setup                fetch and extract enwik9
  python3 bench.py                        run every program in index.json
  python3 bench.py --only baseline_lzma   run a subset
  python3 bench.py --limit 10000000       use only the first N bytes (smoke)
  python3 bench.py --register my_attempt  add programs/my_attempt to index.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
INDEX = ROOT / "index.json"
DATA_DIR = ROOT / "data"
PROGRAMS_DIR = ROOT / "programs"

sys.path.insert(0, str(ROOT / "lib"))
import driver  # noqa: E402


def load_index() -> dict:
    return json.loads(INDEX.read_text())


def save_index(idx: dict) -> None:
    INDEX.write_text(json.dumps(idx, indent=2) + "\n")


def setup() -> None:
    idx = load_index()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DATA_DIR / "enwik9.zip"
    raw_path = DATA_DIR / "enwik9"

    if not zip_path.exists():
        url = idx["source"]
        print(f"fetching {url}")
        urllib.request.urlretrieve(url, zip_path)

    if not raw_path.exists():
        print("extracting enwik9")
        with zipfile.ZipFile(zip_path) as zf:
            with zf.open("enwik9") as src, raw_path.open("wb") as dst:
                while chunk := src.read(1 << 20):
                    dst.write(chunk)

    expected = idx["data"]["expected_size"]
    actual = raw_path.stat().st_size
    if actual != expected:
        raise SystemExit(f"size mismatch: got {actual}, expected {expected}")
    print(f"ok: {raw_path} ({actual} bytes)")


def register(program_id: str) -> None:
    p = PROGRAMS_DIR / program_id
    if not (p / "program.py").exists():
        raise SystemExit(f"no program.py at {p}")
    idx = load_index()
    if any(prog["id"] == program_id for prog in idx["programs"]):
        print(f"{program_id}: already registered")
        return
    idx["programs"].append({"id": program_id})
    save_index(idx)
    print(f"{program_id}: added to index.json")


def bench(only: list[str] | None, limit: int | None) -> int:
    idx = load_index()
    data_path = ROOT / idx["data"]["path"]
    if not data_path.exists():
        raise SystemExit("dataset missing — run bench.py --setup first")

    rows: list[dict] = []
    failed = 0
    for entry in idx["programs"]:
        pid = entry["id"]
        if only and pid not in only:
            continue
        print(f"\n=== {pid} ===")
        try:
            r = driver.run(pid, data_path, limit)
        except Exception as e:
            print(f"{pid}: ERROR {e}")
            failed += 1
            continue
        rows.append(r)
        print(f"  compressed={r['compressed_size']:>13,}  "
              f"program={r['program_size']:>5,}  "
              f"hutter={r['hutter_score']:>13,}  "
              f"t_c={r['compress_time_s']:>7.2f}s  "
              f"t_d={r['decompress_time_s']:>7.2f}s  "
              f"ok={r['roundtrip_ok']}")

    rows.sort(key=lambda r: r["hutter_score"])
    idx["leaderboard"] = [
        {
            "program_id": r["program_id"],
            "hutter_score": r["hutter_score"],
            "compressed_size": r["compressed_size"],
            "program_size": r["program_size"],
            "data_size": r["data_size"],
            "compress_time_s": r["compress_time_s"],
            "roundtrip_ok": r["roundtrip_ok"],
            "timestamp": r["timestamp"],
        }
        for r in rows
    ]
    save_index(idx)

    print("\nleaderboard:")
    for i, r in enumerate(idx["leaderboard"], 1):
        print(f"  {i:2}. {r['program_id']:<24} {r['hutter_score']:>13,}")
    return 0 if failed == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--register", metavar="ID")
    ap.add_argument("--only", nargs="+")
    ap.add_argument("--limit", type=int, default=None,
                    help="use only the first N bytes (smoke testing)")
    args = ap.parse_args()

    if args.setup:
        setup()
        return 0
    if args.register:
        register(args.register)
        return 0
    return bench(args.only, args.limit)


if __name__ == "__main__":
    sys.exit(main())
