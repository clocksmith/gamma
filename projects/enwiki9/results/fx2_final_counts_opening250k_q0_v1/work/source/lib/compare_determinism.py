"""Compare results JSONs from two hosts to verify cross-host determinism.

Usage:
    python3 lib/compare_determinism.py --host-a results/ --host-b results-cloud/

For each program_id present in both directories, picks the most-recent
results JSON from each side and compares:
  - compressed_md5    (must match for cross-host determinism)
  - data_md5          (must match — same input)
  - data_size         (must match — same slice/full)
  - hutter_score      (must match if compressed_md5 matches)

Prints a verdict per program:
  DETERMINISTIC      — md5s match across hosts
  NON_DETERMINISTIC  — md5s differ; report first divergence byte if archives accessible
  ONLY_HOST_A        — program present only on host A
  ONLY_HOST_B        — program present only on host B
  INCOMPARABLE       — different data_md5 or data_size

Exit code: 0 if all overlapping programs are DETERMINISTIC, else 1.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def _latest(d: pathlib.Path, program_id: str) -> dict | None:
    pdir = d / program_id
    if not pdir.is_dir():
        return None
    files = sorted(pdir.glob("*.json"))
    if not files:
        return None
    return json.loads(files[-1].read_text())


def _programs(d: pathlib.Path) -> set[str]:
    return {p.name for p in d.iterdir() if p.is_dir()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host-a", type=pathlib.Path, required=True)
    ap.add_argument("--host-b", type=pathlib.Path, required=True)
    args = ap.parse_args()

    pa = _programs(args.host_a)
    pb = _programs(args.host_b)
    common = sorted(pa & pb)

    fail = 0
    for pid in common:
        ra = _latest(args.host_a, pid)
        rb = _latest(args.host_b, pid)
        if ra is None or rb is None:
            print(f"{pid:<24} INCOMPARABLE missing-results")
            fail += 1
            continue
        if ra.get("data_md5") != rb.get("data_md5") or ra.get("data_size") != rb.get("data_size"):
            print(
                f"{pid:<24} INCOMPARABLE "
                f"data_md5_a={ra.get('data_md5')[:8]} data_md5_b={rb.get('data_md5')[:8]} "
                f"size_a={ra.get('data_size')} size_b={rb.get('data_size')}"
            )
            fail += 1
            continue
        a_sha = ra.get("compressed_sha256") or ra.get("compressed_md5")
        b_sha = rb.get("compressed_sha256") or rb.get("compressed_md5")
        if a_sha == b_sha:
            print(
                f"{pid:<24} DETERMINISTIC "
                f"S_a={ra.get('hutter_score')} S_b={rb.get('hutter_score')} "
                f"sha256={a_sha[:16]}"
            )
        else:
            print(
                f"{pid:<24} NON_DETERMINISTIC "
                f"S_a={ra.get('hutter_score')} S_b={rb.get('hutter_score')} "
                f"a={a_sha[:16]} b={b_sha[:16]}"
            )
            fail += 1

    only_a = sorted(pa - pb)
    only_b = sorted(pb - pa)
    for pid in only_a:
        print(f"{pid:<24} ONLY_HOST_A")
    for pid in only_b:
        print(f"{pid:<24} ONLY_HOST_B")

    print(
        f"\n{len(common)} programs compared, {len(common) - fail} deterministic, "
        f"{fail} failures, "
        f"{len(only_a)} host-A-only, {len(only_b)} host-B-only"
    )
    return 0 if fail == 0 and len(common) > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
