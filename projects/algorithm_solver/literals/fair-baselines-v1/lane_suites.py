"""Rebuild the record suites of `../rung2-short-ra-bench-v1/run_ra_pareto_bench.py`.

The lane samples its short, medium and long suites from source files of the surrounding
workspace: every eligible file is deduplicated by SHA-256 and ranked by
SHA-256("<seed tag>:<file sha>"); the first N of a pool are used, the first half for training
and the second half held out. This module repeats that selection without importing the lane's
code (its sampler lives in a module that also imports the BIT3 encoder).

`digests_from_lane_code()` runs the lane's own `sample_band_pool` in a separate process and
returns only pool digests, so the two can be compared.

The sampled files belong to other repositories. They are written only to a work directory
outside this repository; results record counts, byte totals and digests, never contents or paths.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

HERE = Path(__file__).resolve().parent
LANE_PRESEARCH_DIR = HERE.parent / 'rung2-presearch-v1'
LANE_CODENET_DIR = HERE.parent / 'codenet-replication-v1'
DEFAULT_WORKSPACE_ROOT = HERE.parents[4]   # the directory that holds the gamma checkout and its siblings

# Copied from the lane's sampler so the same files are eligible.
SAFE_ROOTS = ['simulatte', 'hatch', 'fawn', 'doppler', 'reploid', 'gamma/tests', 'gamma/gamma', 'gamma/apps']
SKIP_DIRS = {
    '.git', 'node_modules', '.venv', 'venv', 'target', 'dist', 'build',
    '.zig-cache', 'zig-out', '__pycache__', 'third_party', 'vendor',
    'enwiki9', 'codenet-replication-v1', 'rung2-presearch-v1', 'rung3-archive-search-v1',
    'runs', 'receipts',
}
ALLOWED_EXTS = {'.md', '.py', '.json', '.wgsl', '.css', '.h', '.ts', '.mjs', '.cjs', '.c', '.js'}

# pool name -> (suffixes, needed, min_bytes, max_bytes, seed_tag), as in the lane's main()
POOLS = {
    'wgsl_short': (['.wgsl'], 160, 64, 240, 'r2b-ws'),
    'json_short': (['.json'], 160, 64, 240, 'r2b-js'),
    'ts_short': (['.ts'], 160, 64, 260, 'r2b-tss'),
    'mjs_short': (['.mjs', '.cjs', '.js'], 160, 64, 280, 'r2b-mjss'),
    'ts_med': (['.ts'], 100, 400, 850, 'r2b-tsm'),
    'json_med': (['.json'], 100, 350, 850, 'r2b-jmed'),
    'js_long': (['.js'], 80, 1400, 3400, 'r2b-jsl'),
    'wgsl_long': (['.wgsl'], 80, 1400, 3400, 'r2b-wl'),
}

# suite label -> (pool 1, pool 2, records per pool per side)
SUITES = {
    'short_wgsl_vs_json_80_to_80': ('wgsl_short', 'json_short', 80),
    'short_ts_vs_mjs_80_to_80': ('ts_short', 'mjs_short', 80),
    'med_ts_vs_json_50_to_50': ('ts_med', 'json_med', 50),
    'long_js_vs_wgsl_40_to_40': ('js_long', 'wgsl_long', 40),
}
DEFAULT_SUITES = ['short_wgsl_vs_json_80_to_80', 'short_ts_vs_mjs_80_to_80', 'med_ts_vs_json_50_to_50']


def _file_index(workspace_root: Path) -> list[tuple[str, int, Path]]:
    entries = []
    for rel_root in SAFE_ROOTS:
        base = workspace_root / rel_root
        if not base.is_dir():
            continue
        for cur, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.'))
            for fn in sorted(files):
                ext = os.path.splitext(fn)[1].lower()
                if ext not in ALLOWED_EXTS:
                    continue
                fp = Path(cur) / fn
                try:
                    sz = fp.stat().st_size
                except OSError:
                    continue
                if 64 <= sz <= 3600:
                    entries.append((ext, sz, fp))
    return entries


def sample_pool(index: Sequence[tuple[str, int, Path]], suffixes: Sequence[str], needed: int, min_bytes: int,
                max_bytes: int, seed_tag: str) -> list[bytes]:
    by_sha: dict[str, bytes] = {}
    suf = {s.lower() for s in suffixes}
    for ext, sz, fp in index:
        if ext not in suf or sz < min_bytes or sz > max_bytes:
            continue
        try:
            raw = fp.read_bytes()
        except OSError:
            continue
        if b'\x00' in raw or not (min_bytes <= len(raw) <= max_bytes):
            continue
        by_sha.setdefault(hashlib.sha256(raw).hexdigest(), raw)
    ranked = sorted(by_sha.items(), key=lambda kv: hashlib.sha256(f'{seed_tag}:{kv[0]}'.encode('ascii')).hexdigest())
    if len(ranked) < needed:
        raise RuntimeError(f'only {len(ranked)} eligible files for pool {seed_tag} (need {needed})')
    return [raw for _, raw in ranked[:needed]]


def pool_digest(records: Sequence[bytes]) -> str:
    h = hashlib.sha256()
    for r in records:
        h.update(hashlib.sha256(r).digest())
    return h.hexdigest()


def build_pools(workspace_root: Path, names: Sequence[str]) -> dict[str, list[bytes]]:
    index = _file_index(workspace_root)
    return {name: sample_pool(index, *POOLS[name]) for name in names}


def suite_records(pools: dict[str, list[bytes]], label: str) -> dict:
    p1, p2, half = SUITES[label]
    a, b = pools[p1], pools[p2]
    g1, g2 = f'1-{p1}', f'2-{p2}'
    return {
        'train': [(g1, r) for r in a[:half]] + [(g2, r) for r in b[:half]],
        'test': [(g1, r) for r in a[half:2 * half]] + [(g2, r) for r in b[half:2 * half]],
    }


def export_suite(suite: dict, out_dir: Path) -> None:
    """Write one record per file: <out_dir>/<train|test>/<group>/<NNNN>.bin"""
    for side in ('train', 'test'):
        counters: dict[str, int] = {}
        for group, rec in suite[side]:
            k = counters.get(group, 0)
            counters[group] = k + 1
            d = out_dir / side / group
            d.mkdir(parents=True, exist_ok=True)
            (d / f'{k:04d}.bin').write_bytes(rec)


_LANE_PROBE = r'''
import hashlib, json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
import run_completed_chain_and_regime_eval as R
pools = json.loads(sys.argv[3])
roots = [R.DECO_ROOT / p for p in json.loads(sys.argv[4])]
out = {}
for name, (suffixes, needed, lo, hi, tag) in pools.items():
    recs = [b for _, b in R.sample_band_pool(roots, suffixes, needed, min_bytes=lo, max_bytes=hi, seed_tag=tag)]
    h = hashlib.sha256()
    for r in recs:
        h.update(hashlib.sha256(r).digest())
    out[name] = h.hexdigest()
print(json.dumps(out))
'''


def digests_from_lane_code(names: Sequence[str]) -> dict[str, str]:
    """Pool digests computed by the lane's own sampler, in a child process (nothing is written)."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    proc = subprocess.run(
        [sys.executable, '-B', '-c', _LANE_PROBE, str(LANE_CODENET_DIR), str(LANE_PRESEARCH_DIR),
         json.dumps({n: POOLS[n] for n in names}), json.dumps(SAFE_ROOTS)],
        capture_output=True, text=True, env=env, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError('the lane sampler could not be run: ' + proc.stderr.strip().splitlines()[-1][:200])
    return json.loads(proc.stdout.strip().splitlines()[-1])
