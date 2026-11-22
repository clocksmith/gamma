#!/usr/bin/env python3
"""Exploratory: block rank and nullity of a large real directory (hundreds of files), and how the nullity changes as
files are added in a seeded random order. Reads Git objects only. Needs numpy; no solver.

    python3 -B scale_probe.py REPO PIN PREFIX EXTENSION [LIMIT]
    e.g. python3 -B scale_probe.py /path/to/doppler origin/main src/ .js 400
"""
import subprocess, sys, time, collections
import numpy as np
P, B = 1_000_000_007, 2

def files(repo, pin, prefix, exts, limit, min_bytes=200, max_bytes=60_000):
    out = subprocess.check_output(['git', '-C', repo, 'ls-tree', '-r', '-l', pin, '--', prefix]).decode('utf-8', 'replace').splitlines()
    paths = []
    for line in out:
        meta, path = line.split('\t', 1); size = meta.split()[3]
        if path.endswith(exts) and size != '-' and min_bytes <= int(size) <= max_bytes and not any(x in path.split('/') for x in ('node_modules', 'vendor', 'third_party', 'dist', 'build')):
            paths.append(path)
    paths = sorted(paths)[:limit]
    proc = subprocess.Popen(['git', '-C', repo, 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    texts = []
    for path in paths:
        proc.stdin.write(f'{pin}:{path}\n'.encode()); proc.stdin.flush()
        header = proc.stdout.readline().split(); raw = proc.stdout.read(int(header[2])); proc.stdout.read(1)
        try: texts.append(raw.decode('utf-8'))
        except UnicodeDecodeError: pass
    proc.kill()
    return sorted(set(texts))

def block_rank(programs):
    owners = collections.defaultdict(set)
    for n, p in enumerate(programs):
        for bg in {p[i:i + 2] for i in range(len(p) - 1)}:
            owners[bg].add(n) if len(owners[bg]) < 2 else None
    blocks = set()
    for p in programs:
        start = 0
        for i in range(len(p) - 1):
            if len(owners[p[i:i + 2]]) < 2:
                blocks.add(p[start:i + 1]); start = i + 1
        blocks.add(p[start:])
    letters = sorted(set(''.join(programs))); col = {c: n for n, c in enumerate(letters)}
    width = len(letters)
    basis = np.zeros((0, width), dtype=np.int64); pivots = []
    for b in sorted(blocks, key=len):
        v = np.zeros(width, dtype=np.int64); w = 1
        for c in b:
            v[col[c]] = (v[col[c]] + w) % P; w = w * B % P
        for row, pv in zip(basis, pivots):
            if v[pv]:
                v = (v - v[pv] * row) % P
        nz = np.nonzero(v)[0]
        if len(nz) == 0: continue
        pv = int(nz[0]); v = v * pow(int(v[pv]), P - 2, P) % P
        for i, row in enumerate(basis):
            if row[pv]: basis[i] = (row - row[pv] * v) % P
        basis = np.vstack([basis, v]); pivots.append(pv)
        if len(pivots) == width: break
    return len(letters), len(pivots), len(blocks)

if __name__ == '__main__':
    import random
    repo, pin, prefix, ext = sys.argv[1:5]
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 400
    started = time.time()
    programs = files(repo, pin, prefix, (ext,), limit)
    alphabet, rank, blocks = block_rank(programs)
    print(f"files {len(programs)} bytes {sum(len(p) for p in programs):,} alphabet {alphabet} block rank {rank} nullity {alphabet - rank} "
          f"blocks {blocks} seconds {time.time() - started:.1f}")
    random.Random(7).shuffle(programs)
    for n in (2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 128, 256):
        if n > len(programs):
            break
        a, r, _ = block_rank(programs[:n])
        print(f"  first {n:3} files in shuffled order: alphabet {a:3} nullity {a - r}")
