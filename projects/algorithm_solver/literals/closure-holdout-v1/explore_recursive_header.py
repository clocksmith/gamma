#!/usr/bin/env python3
"""POST HOC. How much of Study 1's archive result depends on storing every dictionary entry as a literal string?

    python3 -I explore_recursive_header.py

Study 1's header stores each entry as one length byte plus its bytes. A recursive header may instead store an entry as
one count byte plus the IDs (packed at ceil(log2(n + 2)) bits) of its fewest-token spelling by earlier entries in the
same order, whichever is shorter; a BPE merge table is the familiar case. Token counts and coded payloads do not change
(same entries, same parser); only header bytes do. Applies the same rule to every dictionary and recomputes the Study 1
comparison of the byte-selected archive (first 1,408 token-gain fragments) with 3,924-fragment BPE, holding Study 1's
measured payloads. Not decoded: a header-size estimate under this storage rule. Writes out/posthoc-recursive-header.json.
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
    bits = math.ceil(math.log2(alpha + nfrag + 2))
    V, flat, rec, refs = set(order[:alpha]), 0, 0, 0
    for e in frags:
        lit, ref = 1 + len(e), 1 + math.ceil(spell(e, V) * bits / 8)
        flat += lit
        rec += min(lit, ref)
        refs += ref < lit
        V.add(e)
    return {'fragments': len(frags), 'flat_bytes': flat, 'recursive_bytes': rec, 'entries_as_references': refs}


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
