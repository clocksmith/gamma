#!/usr/bin/env python3
"""Write the round-two search family. Builds strings only; solves nothing.

Each corpus has up to four programs over a, b, c, d. A corpus draws three two-character blocks; each program
is two of those blocks, with one random character appended a third of the time and one prepended a third
of the time. Shared blocks give shared fragments, and the stray characters give overlaps and private ends.

    python3 -B freeze_round2.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
state = 20261123


def step():
    global state
    state = (1664525 * state + 1013904223) % (1 << 32)
    return state >> 16


def letter():
    return 'abcd'[step() % 4]


corpora, seen = [], set()
while len(corpora) < 150:
    blocks = [letter() + letter() for _ in range(3)]
    programs = set()
    for _ in range(4):
        s = blocks[step() % 3] + blocks[step() % 3]
        if step() % 3 == 0:
            s = s + letter()
        if step() % 3 == 0:
            s = letter() + s
        programs.add(s)
    key = tuple(sorted(programs))
    if len(key) >= 3 and key not in seen:
        seen.add(key)
        corpora.append(list(key))
json.dump({'schema': 'capacity-theorems-round2/v1', 'corpora': corpora}, open(os.path.join(HERE, 'instances-round2.json'), 'w'), indent=1)
print(len(corpora), 'corpora written; nothing solved. First three:', corpora[:3])
