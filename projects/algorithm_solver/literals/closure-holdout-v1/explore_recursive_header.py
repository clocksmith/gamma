#!/usr/bin/env python3
"""POST HOC. How much of Study 1's archive result depends on storing every dictionary entry as a literal string?

    python3 -I explore_recursive_header.py

Study 1's header stores each entry as one length byte plus its bytes. A recursive header instead gives each entry a
2-bit tag and the cheapest of: a literal (4-bit length, then its bytes); a pair of earlier entries (two IDs packed at
ceil(log2(n + 2)) bits each), when the entry is exactly two earlier entries, as in a BPE merge table; or a list (4-bit
count, then the IDs of its fewest-token spelling by earlier entries). Only entries already in the dictionary are
referenced; internal pieces that are not themselves entries are not modelled. The dictionary part is the bit total
rounded up to bytes. Token counts and coded payloads do not change (same entries, same parser); only header bytes do.
Applies the same rule to every dictionary. Not decoded: a header-size estimate under this storage rule. Writes out/posthoc-recursive-header.json.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OH = HERE.parent / 'objective-holdout-v1'


def spell(w, V):
    n = len(w)
    b = [0] + [10**9] * n
    for i in range(n):
        if b[i] < 10**9:
            for j in range(i + 1, n + 1):
                if w[i:j] in V and b[i] + 1 < b[j]:
                    b[j] = b[i] + 1
    return b[n]


def header_parts(order, alpha, nfrag):
    frags = [e for e in order[alpha:] if len(e) > 1][:nfrag]
    b = math.ceil(math.log2(alpha + nfrag + 2))
    V, flat, bits, kinds = set(order[:alpha]), 0, 0, {'literal': 0, 'pair': 0, 'list': 0}
    for e in frags:
        sp = spell(e, V)
        opts = {'literal': 4 + 8 * len(e), 'list': 4 + sp * b}
        if sp == 2:
            opts['pair'] = 2 * b
        kind = min(opts, key=lambda k: (opts[k], k))
        bits += 2 + opts[kind]
        kinds[kind] += 1
        flat += 1 + len(e)
        V.add(e)
    return {'fragments': len(frags), 'flat_bytes': flat, 'recursive_bytes': (bits + 7) // 8, 'entry_kinds': kinds}


def main():
    fz = json.loads((HERE / 'frozen' / 'dictionaries.json').read_text())
    A = fz['alphabet']
    orders = {a: [bytes.fromhex(h) for h in fz['dictionaries'][f'{a}-K4096']] for a in ('bpe', 'token', 'closed')}
    out = {'note': 'post hoc header-size estimate; payloads and token counts unchanged', 'dictionaries': {}}
    for a, o in orders.items():
        out['dictionaries'][a] = {str(k): header_parts(o, A, k) for k in (84, 1408, 3924)}
    r = json.loads((OH / 'out' / 'results-fresh.json').read_text())
    out['study1_inputs'] = {k: r[k] for k in ('source_bytes',) if k in r}
    (HERE / 'out' / 'posthoc-recursive-header.json').write_text(json.dumps(out, indent=1) + '\n')
    for a, v in out['dictionaries'].items():
        print(a, {k: (x['flat_bytes'], x['recursive_bytes']) for k, x in v.items()})


if __name__ == '__main__':
    main()
