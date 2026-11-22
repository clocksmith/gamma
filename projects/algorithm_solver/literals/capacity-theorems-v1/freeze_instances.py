#!/usr/bin/env python3
"""Write the frozen instances and the pre-registered predictions. Solves nothing.

This script only builds strings and copies numbers that were derived by hand (see PREREGISTRATION.md).
It computes no rank, no bound, no optimum and no coverage curve.

    python3 -B freeze_instances.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def grid(left, right):
    return [x + y for x in left for y in right]


def overlap(middle):          # hub = a + middle + d, with one neighbour sharing each end
    return ['a' + middle + 'd', 'a' + middle + 'e', 'f' + middle + 'd']


def abut(middle):             # same neighbours; the hub repeats the middle so the shared pieces abut
    return ['a' + middle + middle + 'd', 'a' + middle + 'e', 'f' + middle + 'd']


INSTANCES = {
    # four permanent tiny controls
    'C1': {'family': 'tiny control', 'programs': ['abc', 'abab'], 'note': 'shared piece aligned with the repeat'},
    'C2': {'family': 'tiny control', 'programs': ['abc', 'baba'], 'note': 'same lengths and alphabet as C1, repeat misaligned'},
    'C3': {'family': 'tiny control', 'programs': ['ab', 'ac', 'bc'], 'note': 'two-character programs on a triangle of characters'},
    'C4': {'family': 'tiny control', 'programs': ['ax', 'ay', 'bx', 'by'], 'note': 'two-character programs on a 2 by 2 grid; one dependent set of four'},
    # aligned against misaligned repeats, alphabet held at three
    'P3a': {'family': 'repeat, aligned', 'programs': ['abc', 'ab' * 3]},
    'P3m': {'family': 'repeat, misaligned', 'programs': ['abc', 'ba' * 3]},
    'P4a': {'family': 'repeat, aligned', 'programs': ['abc', 'ab' * 4]},
    'P4m': {'family': 'repeat, misaligned', 'programs': ['abc', 'ba' * 4]},
    # planted overlapping motif against its abutting control
    'O1': {'family': 'overlap motif', 'programs': overlap('b')},
    'O1c': {'family': 'abutting control', 'programs': abut('b')},
    'O2': {'family': 'overlap motif', 'programs': overlap('bc'), 'note': 'the motif already in capacity-impossibility-v1; its witness-rule optimum was known beforehand'},
    'O2c': {'family': 'abutting control', 'programs': abut('bc')},
    'O3': {'family': 'overlap motif', 'programs': overlap('bcg')},
    'O3c': {'family': 'abutting control', 'programs': abut('bcg')},
    # grids of two-character programs
    'B23': {'family': 'grid', 'programs': grid('ab', 'xyz')},
    'B33': {'family': 'grid', 'programs': grid('abc', 'xyz')},
    # terminator ablation: C4 with a final character that occurs nowhere else
    'T22': {'family': 'terminator ablation of C4', 'programs': [p + '$' for p in grid('ab', 'xy')]},
    # four programs built from three two-character blocks
    'D1': {'family': 'block dictionary', 'programs': ['abcd', 'abef', 'efcd', 'cdef']},
}


def u(rank, forced, disjoint, opt, curve, cuttable):
    return {'programRank': rank, 'forcedSingletons': forced, 'disjointBound': disjoint, 'minimumEntries': opt,
            'coverageByBudget': curve, 'everyProgramHasACuttablePrefix': cuttable}


def w(forced, disjoint, block_rank, opt, curve):
    return {'forcedSingletons': forced, 'disjointBound': disjoint, 'blockRank': block_rank, 'minimumEntries': opt,
            'coverageByBudget': curve}


ALIGNED = (u(2, 0, 2, 2, [0, 1, 2], True), w(1, 2, 2, 2, [0, 1, 2]))
MISALIGNED = (u(2, 0, 3, 3, [0, 1, 1, 2], False), w(3, 3, 3, 3, [0, 0, 1, 2]))
OVERLAP = (u(3, 0, 4, 4, [0, 0, 1, 2, 3], False), w(2, 4, 5, 5, [0, 0, 1, 2, 2, 3]))
ABUT = (u(3, 0, 4, 4, [0, 0, 1, 2, 3], False), w(2, 4, 4, 4, [0, 0, 1, 2, 3]))
PREDICTIONS = {
    'C1': (3,) + ALIGNED,
    'C2': (3,) + MISALIGNED,
    'C3': (3, u(3, 3, 3, 3, [0, 0, 1, 3], True), w(3, 3, 3, 3, [0, 0, 1, 3])),
    'C4': (4, u(3, 4, 4, 4, [0, 0, 1, 2, 4], False), w(4, 4, 4, 4, [0, 0, 1, 2, 4])),
    'P3a': (3,) + ALIGNED, 'P4a': (3,) + ALIGNED,
    'P3m': (3,) + MISALIGNED, 'P4m': (3,) + MISALIGNED,
    'O1': (5,) + OVERLAP, 'O2': (6,) + OVERLAP, 'O3': (7,) + OVERLAP,
    'O1c': (5,) + ABUT, 'O2c': (6,) + ABUT, 'O3c': (7,) + ABUT,
    'B23': (5, u(4, 5, 5, 5, [0, 0, 1, 2, 4, 6], False), w(5, 5, 5, 5, [0, 0, 1, 2, 4, 6])),
    'B33': (6, u(5, 6, 6, 6, [0, 0, 1, 2, 4, 6, 9], False), w(6, 6, 6, 6, [0, 0, 1, 2, 4, 6, 9])),
    'T22': (5, u(3, 0, 4, 4, [0, 0, 1, 2, 4], False), w(2, 4, 4, 4, [0, 0, 1, 2, 4])),
    'D1': (6, u(3, 0, 3, 3, [0, 0, 2, 4], True), w(0, 3, 3, 3, [0, 0, 2, 4])),
}
# Ablation: the unrestricted rule with whole programs allowed as entries.
WHOLE_ALLOWED = {'C3': {'minimumEntries': 3, 'coverageByBudget': [0, 1, 2, 3]},
                 'C4': {'minimumEntries': 4, 'coverageByBudget': [0, 1, 2, 3, 4]}}


def random_family(count=200):
    """Frozen search family: three programs of length 3 to 5 over a, b, c from a fixed linear congruential stream."""
    state, out, seen = 20261122, [], set()
    def step():
        nonlocal state
        state = (1664525 * state + 1013904223) % (1 << 32)
        return state >> 16
    while len(out) < count:
        programs = []
        for _ in range(3):
            length = 3 + step() % 3
            programs.append(''.join('abc'[step() % 3] for _ in range(length)))
        key = tuple(sorted(programs))
        if len(set(programs)) == 3 and key not in seen:
            seen.add(key)
            out.append(sorted(programs))
    return out


assert set(INSTANCES) == set(PREDICTIONS)
for name, entry in INSTANCES.items():
    alphabet, unrestricted, witnessed = PREDICTIONS[name]
    assert len(set(entry['programs'])) == len(entry['programs'])
    assert len(set(''.join(entry['programs']))) == alphabet, name      # the only thing checked here: a character count
    assert len(unrestricted['coverageByBudget']) == unrestricted['minimumEntries'] + 1
    assert len(witnessed['coverageByBudget']) == witnessed['minimumEntries'] + 1
    assert unrestricted['coverageByBudget'][-1] == witnessed['coverageByBudget'][-1] == len(entry['programs'])
json.dump({'schema': 'capacity-theorems-instances/v1', 'instances': INSTANCES, 'randomSearchFamily': random_family()},
          open(os.path.join(HERE, 'instances.json'), 'w'), indent=1)
json.dump({'schema': 'capacity-theorems-predictions/v1', 'field': {'prime': 1000000007, 'base': 2},
           'predictions': {name: {'alphabetSize': a, 'unrestricted': un, 'witnessThreshold2': wi} for name, (a, un, wi) in PREDICTIONS.items()},
           'wholeProgramsAllowedAblation': WHOLE_ALLOWED}, open(os.path.join(HERE, 'predictions.json'), 'w'), indent=1)
print(len(INSTANCES), 'instances and', len(random_family()), 'random-family corpora written; nothing solved')
