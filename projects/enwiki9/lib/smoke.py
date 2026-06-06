"""Smoke-test a program before committing it to the leaderboard.

Runs five cheap checks in order; exits non-zero on the first failure.
None of these write to results/.

  1. 1 KB roundtrip            — API sanity (sub-second)
  2. 100 KB roundtrip          — logic check (seconds)
  3. determinism diff          — compress twice, sha256-equal
  4. /dev/urandom check        — counting-argument lower bound
  5. prefix roundtrip          — pick a size that finishes in ~2 min

Usage:
  python3 lib/smoke.py <program_id>
  python3 lib/smoke.py <program_id> --prefix 1000000      # cmix-class
  python3 lib/smoke.py <program_id> --skip-prefix         # tiers 1-4 only
"""

from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DEFAULT = ROOT / "data" / "enwik9"

sys.path.insert(0, str(ROOT / "lib"))
import driver  # noqa: E402


def _row(name: str, ok: bool, elapsed: float, detail: str) -> None:
    status = "PASS" if ok else "FAIL"
    print(f"  {status}  {name:<32}  {elapsed:6.2f}s  {detail}")


def _check(name: str, fn) -> bool:
    t0 = time.perf_counter()
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        _row(name, False, time.perf_counter() - t0, f"exception: {exc!r}")
        return False
    _row(name, ok, time.perf_counter() - t0, detail)
    return ok


def smoke(program_id: str, prefix_bytes: int, data_path: pathlib.Path,
          skip_prefix: bool) -> int:
    mod, src_path = driver._load(program_id)
    print(f"smoke: {program_id}  (program.py = {src_path.stat().st_size} B)")

    needed = 100_000 if skip_prefix else max(100_000, prefix_bytes)
    if not data_path.exists():
        print(f"  WARN  data file missing at {data_path}")
        if not skip_prefix:
            print("        falling back to skip_prefix=True")
            skip_prefix = True
        head = b""
    else:
        with data_path.open("rb") as fh:
            head = fh.read(needed)

    def t1_sanity():
        sample = head[:1_000] if head else b"hello world\n" * 100
        c = mod.compress(sample)
        return mod.decompress(c) == sample, f"input=1KB archive={len(c)}B"

    def t2_logic():
        sample = head[:100_000] if head else os.urandom(100_000)
        c = mod.compress(sample)
        return mod.decompress(c) == sample, f"input=100KB archive={len(c)}B"

    def t3_determinism():
        sample = head[:100_000] if head else b"a" * 100_000
        a = mod.compress(sample)
        b = mod.compress(sample)
        ha = hashlib.sha256(a).hexdigest()[:12]
        hb = hashlib.sha256(b).hexdigest()[:12]
        return a == b, f"sha256[a]={ha} sha256[b]={hb}"

    def t4_urandom():
        rand = os.urandom(100_000)
        c = mod.compress(rand)
        # Counting argument: output >= input - O(1). 64 bytes of framing slop.
        lower = len(rand) - 64
        ok = mod.decompress(c) == rand and len(c) >= lower
        return ok, f"input=100KB random archive={len(c)}B (lower_bound={lower})"

    def t5_prefix():
        sample = head[:prefix_bytes]
        c = mod.compress(sample)
        ok = mod.decompress(c) == sample
        ratio = len(c) / len(sample) if sample else float("nan")
        bpb = (8 * len(c)) / len(sample) if sample else float("nan")
        return ok, (f"input={len(sample) / 1e6:.0f}MB "
                    f"archive={len(c) / 1e6:.2f}MB "
                    f"ratio={ratio:.4f} bpb={bpb:.3f}")

    checks = [
        ("1KB roundtrip", t1_sanity),
        ("100KB roundtrip", t2_logic),
        ("determinism (100KB x2)", t3_determinism),
        ("/dev/urandom (100KB)", t4_urandom),
    ]
    if not skip_prefix:
        mb = prefix_bytes // 1_000_000
        checks.append((f"prefix roundtrip ({mb}MB)", t5_prefix))

    for name, fn in checks:
        if not _check(name, fn):
            print("smoke: FAIL")
            return 1

    print("smoke: PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("program_id")
    ap.add_argument("--data", type=pathlib.Path, default=DATA_DEFAULT)
    ap.add_argument("--prefix", type=int, default=100_000_000,
                    help="bytes for the prefix tier (default 100MB; "
                         "drop to 1_000_000 for cmix-class programs)")
    ap.add_argument("--skip-prefix", action="store_true",
                    help="run only tiers 1-4 (~30 sec total)")
    args = ap.parse_args()
    return smoke(args.program_id, args.prefix, args.data, args.skip_prefix)


if __name__ == "__main__":
    sys.exit(main())
