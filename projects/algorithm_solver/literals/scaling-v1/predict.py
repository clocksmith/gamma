#!/usr/bin/env python3
"""Frozen predictions of K* for the confirmatory sizes, from training files and training chains only.

    python3 -I predict.py CHAIN_DIR

Rule (PREREGISTRATION.md): along the lazy open chain trained on the first n catalogue training problems, K_0.6 is the
first k at which at least 60% of the 200 fragments ending at k occur in exactly one training problem; the prediction
is round(K_0.6 / 0.913). Baselines: B1 = round(N / 123.6) (constant training bytes per slot, fitted on the eight
development points); B2 = round(exp(-1.810) * N^0.743) (power law fitted on the four catalogue development sizes).
Writes out/predictions.json with each chain's SHA-256.
"""
import collections
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAMMA = HERE.parents[3]
SIZES = (800, 1600, 2269)
T, WIN, SCALE = 0.6, 200, 0.913
B1_BYTES_PER_SLOT = 123.6
B2_LOG_A, B2_BETA = -1.810, 0.743


def main():
    cdir = Path(sys.argv[1])
    train = json.loads((HERE / 'sets' / 'catalogue-train.json').read_text())['files']
    out = {'rule': {'threshold': T, 'window': WIN, 'scale': SCALE}, 'sizes': {}}
    for n in SIZES:
        sel = [f for f in train if f['rank'] < n]
        units = collections.defaultdict(list)
        for f in sel:
            units[f['unit']].append((GAMMA / f['path']).read_bytes())
        N = sum(f['bytes'] for f in sel)
        chain_path = cdir / f'open-u{n}.txt'
        raw = chain_path.read_bytes()
        frags = [bytes.fromhex(ln.split()[5]) for ln in raw.decode().splitlines()
                 if ln.startswith('E ') and len(ln.split()) == 6 and len(ln.split()[5]) > 2]
        texts = list(units.values())
        one = [sum(1 for t in texts if any(fr in r for r in t)) == 1 for fr in frags]
        k_t, run = None, sum(one[:WIN])
        for k in range(WIN, len(one) + 1):
            if k > WIN:
                run += one[k - 1] - one[k - 1 - WIN]
            if run >= T * WIN:
                k_t = k
                break
        out['sizes'][str(n)] = {'train_bytes': N, 'chain_sha256': hashlib.sha256(raw).hexdigest(), 'chain_fragments': len(frags),
                                'k_0.6': k_t, 'onset_prediction': round(k_t / SCALE) if k_t else None,
                                'B1_prediction': round(N / B1_BYTES_PER_SLOT), 'B2_prediction': round(math.exp(B2_LOG_A) * N ** B2_BETA)}
        print(n, out['sizes'][str(n)], flush=True)
    (HERE / 'out' / 'predictions.json').write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main()
