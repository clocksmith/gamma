#!/usr/bin/env python3
"""Replay every plotted point of the witness-rule coverage curve. Python 3.8+ and Git; no solver.

For each budget it reads the stored dictionary behind the lower end and checks, against the source bytes
at the pinned commit, that the dictionary is legal under the witness rule, has no more entries than the
budget, and spells exactly the programs recorded for it. It recomputes the upper end from its two stated
sources and checks the single-character value from its stored character set.

The upper ends rest on two results proved elsewhere and not re-proved here:
  - the unrestricted exact maximum (check_unrestricted.py in this folder), and
  - all 80 programs need 92 entries under the witness rule (rank of the forced blocks).

    python3 -B check_coverage.py /path/to/gamma [coverage.json]
"""
import collections
import json
import os
import subprocess
import sys

REPO = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'coverage.json')
PIN, ROOT = '59ff04415ff2afd04ff2ed451340f4f02852bf18', 'projects/algorithm_solver/literals/'


def check(value, message):
    if not value:
        raise SystemExit('FAILED: ' + message)


def blob(path):
    return subprocess.check_output(['git', '-C', REPO, 'show', f'{PIN}:{ROOT}{path}'])


ids = sorted(json.loads(blob('matched80-v1/labels/ids.json')))
wanted = set(ids)
src = {r['id']: blob('scale-v2/generated/' + r['file']) for r in json.loads(blob('scale-v2/generated/manifest.json'))['rows']
       if r['variant'] == 'compact' and r['id'] in wanted}
check(len(src) == 80 and len(set(src.values())) == 80, 'cohort is not 80 distinct sources')
whole = set(src.values())
alphabet = frozenset().union(*(frozenset(s) for s in whole))
TOP = len(alphabet)
data = json.load(open(DATA))
check(data['pin'] == PIN, 'coverage.json names another commit')


def spelled(words):
    by_first = collections.defaultdict(list)
    for w in words:
        by_first[w[0]].append(w)
    out = []
    for p in ids:
        s = src[p]
        reach = [False] * (len(s) + 1)
        reach[0] = True
        for i in range(len(s)):
            if reach[i]:
                for w in by_first.get(s[i], ()):
                    if s.startswith(w, i):
                        reach[i + len(w)] = True
        if reach[len(s)]:
            out.append(p)
    return out


def unrestricted(k):
    return 0 if k == 0 else k - 1 if k <= 60 else k if k <= 67 else k + 1 if k <= 79 else 80


# ---- every stored dictionary: legal, sized as stated, spells exactly the recorded programs
replayed = {}
for key, d in data['dictionaries'].items():
    words = [e.encode('latin-1') for e in d['entries']]
    check(len(set(words)) == len(words) == d['entryCount'], f'{key}: entry count')
    for w in words:
        check(w and w not in whole, f'{key}: empty entry or whole program')
        check(len(w) == 1 or sum(w in s for s in whole) >= 2, f'{key}: {w!r} occurs in fewer than two programs')
    got = spelled(words)
    check(got == d['spells'], f'{key}: spells {len(got)} programs, recorded {len(d["spells"])}')
    check(d['multiCharacterEntries'] == sum(len(w) > 1 for w in words), f'{key}: multi-character count')
    replayed[key] = (len(words), len(got))

# ---- every budget
rows = data['rows']
check([r['slots'] for r in rows] == list(range(TOP + 1)), 'budgets are not 0..alphabet size')
previous_lower, previous_upper = 0, 0
for r in rows:
    k = r['slots']
    if r['lowerDictionary'] is None:
        check(r['lower'] == 0, f'{k}: lower end without a dictionary')
    else:
        entries, programs = replayed[r['lowerDictionary']]
        check(entries <= k and programs == r['lower'], f'{k}: lower end does not match its dictionary')
    cap = 80 if k >= TOP else 79
    upper = min(unrestricted(k), cap)
    check(r['upper'] == upper and r['unrestrictedMaximum'] == unrestricted(k), f'{k}: upper end')
    check(r['lower'] <= r['upper'] and r['exact'] == (r['lower'] == r['upper']), f'{k}: interval')
    check(r['singleCharacters'] <= r['lower'], f'{k}: single characters above the lower end')
    check(r['lower'] >= previous_lower and r['upper'] >= previous_upper, f'{k}: not monotone')
    previous_lower, previous_upper = r['lower'], r['upper']

# ---- single characters: the stored character set at each budget attains the stated value
for r in rows:
    k = r['slots']
    held = data['singleCharacterSets'][str(k)]
    letters = frozenset(held['characters'].encode('latin-1'))
    check(len(letters) == len(held['characters']) <= k, f'{k}: single-character set size')
    got = sum(1 for s in whole if frozenset(s) <= letters)
    check(got == held['spells'] == r['singleCharacters'], f'{k}: single-character value')
exact = [r['slots'] for r in rows if r['exact']]
print(f'{len(data["dictionaries"])} dictionaries replayed against {PIN[:8]}: all legal, all spell exactly the recorded programs.')
print(f'{len(rows)} budgets checked. Exact at {len(exact)}: {exact}')
print('Single-character value attained by its stored character set at every budget (its optimality is from an integer program, not rechecked here).')
for k in (8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 92):
    r = rows[k]
    print(f"  {k:2d} slots: {r['lower']}" + ('' if r['exact'] else f" to {r['upper']}") + f"   (single characters {r['singleCharacters']}; ceiling: {r['upperSource']})")
