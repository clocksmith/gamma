"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from math import comb
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h18a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _hsm(rng):
    n = rng.randrange(1, 12)
    scores = [rng.randrange(0, 8) for _ in range(n)]
    groups = [rng.sample(range(n), rng.randrange(1, n + 1)) for _ in range(rng.randrange(1, 7))]
    return [scores, groups, rng.randrange(1, 6)]


def _hwc(rng):
    plates = ['A1', 'B2', 'C', '7']
    names = ['A1', 'A5', 'B0', 'XY12', 'Q3', 'Z100']
    return [[[rng.choice(plates), rng.choice(names)] for _ in range(rng.randrange(0, 14))]]


def _mab(rng):
    n = rng.randrange(1, 11)
    arr = [rng.randrange(0, 6) for _ in range(n)]
    if max(arr) == 0: arr[rng.randrange(n)] = rng.randrange(1, 4)
    return [arr]


def _mpn(rng):
    return [[rng.randrange(1, 9) for _ in range(rng.randrange(1, 7))]]


def _mtc(rng):
    n, m = rng.randrange(1, 5), rng.randrange(1, 5)
    mat = [[rng.randrange(-9, 10) for _ in range(m)] for _ in range(n)]
    cmds = []
    for _ in range(rng.randrange(0, 9)):
        if rng.random() < 0.5: cmds.append('reverseRow %d' % rng.randrange(n))
        else: cmds.append('swap %d %d' % (rng.randrange(n), rng.randrange(n)))
    return [mat, cmds]


def _mns(rng):
    return [[rng.randrange(1, 10) for _ in range(rng.randrange(1, 12))]]


def _mts(rng):
    return [rng.randrange(1, 4), rng.randrange(1, 4), [rng.choice([1, 5, 10, 15, 20, 25, 30, 45, 59, 60, 61, 90]) for _ in range(rng.randrange(0, 15))]]


def _board(rng):
    n, m = rng.randrange(1, 7), rng.randrange(1, 5)
    return [[rng.randrange(-3, 4) for _ in range(m)] for _ in range(n)], n, m


def _mgj1(rng):
    b, n, m = _board(rng); return [b, rng.randrange(m)]


def _mgjk(rng):
    b, n, m = _board(rng); return [b, rng.randrange(m), rng.randrange(0, min(n, 3) + 1)]


def _mbs(rng):
    return [[rng.randrange(1, 5) for _ in range(rng.randrange(1, 13))]]


def _mvt(rng):
    n = rng.randrange(1, 10)
    return [n, [[rng.randrange(n), rng.randrange(n)] for _ in range(rng.randrange(0, 2 * n + 1))]]


GEN = {_o.HSM: _hsm, _o.HWC: _hwc, _o.MAB: _mab, _o.MPN: _mpn, _o.MTC: _mtc, _o.MNS: _mns, _o.MTS: _mts,
       _o.MGJ1: _mgj1, _o.MGJ2: _mgjk, _o.MGJ3: _mgjk, _o.MGJ4: _mgjk, _o.MBS: _mbs, _o.MVT: _mvt}

B3 = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [1, 1, 100]]
HAND = {
    _o.HSM: [[[5, 1, 4, 3, 2], [[0, 1], [2, 3, 4], [1, 4]], 2], [[5, 1, 4, 3, 2], [[2, 3, 4], [0, 1]], 1], [[0, 0], [[0], [1]], 3], [[7], [[0]], 1]],
    _o.HWC: [[[['CAR1', 'A1'], ['CAR2', 'B3'], ['CAR1', 'A5'], ['CAR1', 'C2'], ['BUS', 'X10']]], [[]], [[['Z', 'A0'], ['Z', 'B0']]]],
    _o.MAB: [[[1]], [[3, 3, 3]], [[1, 2, 3, 2, 1]], [[0, 5, 5, 5, 0]], [[2, 1, 4, 4, 4, 1]], [[0, 0, 7]]],
    _o.MPN: [[[3, 2, 1]], [[1, 2, 3]], [[5, 1, 5, 1]], [[2, 4, 1, 3]], [[7]]],
    _o.MTC: [[[[1, 2, 3], [4, 5, 6]], ['reverseRow 0', 'swap 0 1']], [[[1, 2], [3, 4], [5, 6]], ['swap 0 2', 'swap 1 1', 'reverseRow 2', 'reverseRow 2']], [[[9]], []]],
    _o.MNS: [[[1]], [[5, 2, 2]], [[1, 1, 1, 1]], [[3, 1, 1, 1, 5]], [[10, 9, 1]]],
    _o.MTS: [[1, 1, [30, 20, 10, 5]], [2, 1, [20, 20, 20, 30, 30]], [1, 2, [61, 70]], [3, 2, []], [1, 1, [60]]],
    _o.MGJ1: [[B3, 0], [B3, 2], [[[5, -1]], 1], [[[-5], [-5], [-5]], 0]],
    _o.MGJ2: [[B3, 0, 0], [B3, 0, 1], [[[1], [-9], [1], [-9], [1]], 0, 2], [[[1], [-9], [1], [-9], [1]], 0, 1], [[[1, 1], [1, 1]], 1, 2]],
    _o.MGJ3: [[B3, 0, 1], [[[0, 0, 0], [0, 0, 0], [0, 0, 0]], 1, 1], [[[1], [-9], [1]], 0, 1], [[[4]], 0, 0]],
    _o.MGJ4: [[[[0, 0, 0], [0, 0, 0], [0, 0, 0]], 1, 1], [[[0], [0], [0], [0]], 0, 1], [[[1, 2], [3, 3]], 0, 0], [[[4]], 0, 0]],
    _o.MBS: [[[3, 1, 2, 1]], [[1, 2, 3]], [[5, 1, 1]], [[4, 3, 2, 1]], [[2, 2]], [[1, 3, 2, 5, 4]]],
    _o.MVT: [[1, []], [3, [[0, 1], [1, 2], [2, 0]]], [4, [[0, 1], [1, 0], [2, 3]]], [5, [[0, 1], [1, 2], [2, 1], [3, 3], [4, 3]]], [2, [[0, 0], [0, 1], [0, 1]]]],
}


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode()))
    args = list(HAND[uid]) + [GEN[uid](rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []
    n = 100000
    if uid == o.HSM:
        scores = list(range(n))
        groups = [[g + 1000 * t for t in range(100)] for g in range(1000)]
        # group g scores 10 g + 945000 with k = 10; group 999 is best and its later copy loses the tie
        out.append(([scores, groups + [list(groups[999])], 10], 999))
        out.append(([scores, [list(range(n - 1, -1, -1)), [n - 1]], n], 0))
        out.append(([[10**9] * n, [[i] for i in range(n)], 1], 0))
        out.append(([[10**9] * n, [[i] for i in range(n - 1)] + [list(range(n))], n], n - 1))
    elif uid == o.HWC:
        plates = ['P' + str(i) for i in range(1000)]
        recs = [[plates[i % 1000], 'A0' if (i // 1000) % 2 == 0 else 'A999999999'] for i in range(n)]
        out.append(([recs], [[p, 99 * 9999999990] for p in sorted(plates)]))
        out.append(([[['ONE', 'X' + str(i)] for i in range(n)]], [['ONE', (n - 1) * 10]]))
        distinct = ['V' + str(i) for i in range(n)]
        out.append(([[[p, 'Q7'] for p in distinct]], [[p, 0] for p in sorted(distinct)]))
    elif uid == o.MAB:
        out.append(([[10**9] * n], 10**9 * n - 50000 * 50000))
        out.append(([list(range(1, 50001)) + list(range(49999, 0, -1))], 0))
        out.append(([[0] * (n - 1) + [5]], 4))
        out.append(([[1] * n], n - 1))
        out.append(([[10**9 - i for i in range(n)]], sum(10**9 - i for i in range(n)) - 50000 * 50000))
    elif uid == o.MPN:
        out.append(([[10**9 - i for i in range(n)]], n - 1))
        out.append(([[10**9, 1] * (n // 2)], (n // 2) * (10**9 - 1)))
        out.append(([list(range(1, n + 1))], 0))
        out.append(([[10**9] + [1] * (n - 1)], 10**9 - 1))
    elif uid == o.MTC:
        s = 316
        mat = [[i * s + j for j in range(s)] for i in range(s)]
        cmds = ['reverseRow %d' % (t % s) for t in range(n)]
        out.append(([mat, cmds], [row[::-1] if r < n % s else list(row) for r, row in enumerate(mat)]))
        chain = ['swap %d %d' % (r, r + 1) for r in range(s - 1)]
        out.append(([mat, chain * 317], [list(row) for row in mat[1:]] + [list(mat[0])]))
        out.append(([[list(range(n))], ['reverseRow 0'] * n], [list(range(n))]))
        out.append(([[[i] for i in range(n)], ['swap 0 %d' % (n - 1), 'reverseRow 5'] * (n // 2)], [[i] for i in range(n)]))
    elif uid == o.MNS:
        out.append(([[1] * n], (n - 1) // 2))
        out.append(([[10**9] + [1] * (n - 1)], n - 1))
        out.append(([[2] * n], (n - 1) // 2))
        out.append(([[10**9] * n], (n - 1) // 2))
    elif uid == o.MTS:
        out.append(([n, n, [60] * n], n))
        out.append(([n, n, [61] * n], 0))
        out.append(([1, 1, [1] * n], 60))
        out.append(([10, 10, [1] * n], 6000))
        out.append(([1, 1, list(range(n, 0, -1))], 10))
        out.append(([7, 3, [10**9] * (n - 1) + [60]], 1))
    elif uid == o.MGJ1:
        out.append(([[[i * 7 % 10001 for i in range(n)]], 77], 539))
        out.append(([[[10**4]] * n, 0], 10**4 * n))
        out.append(([[[-1] * 316 for _ in range(316)], 5], -316))
        out.append(([[list(range(316)) for _ in range(316)], 0], sum(range(316))))
    elif uid in (o.MGJ2, o.MGJ3, o.MGJ4):
        neg = [[-1] * 10 for _ in range(1000)]
        one = [[1] * 10 for _ in range(1000)]
        col = [[-1] for _ in range(20000)]
        zero = [[0] for _ in range(20000)]
        if uid == o.MGJ2:
            out.append(([neg, 3, 9], -(1000 - 9)))
            out.append(([one, 3, 9], 1000))
            out.append(([col, 0, 4], -(20000 - 4)))
            out.append(([[[10**4] * 20000], 19999, 1], 10**4))
        elif uid == o.MGJ3:
            out.append(([neg, 0, 9], [[i, 0] for i in range(982)] + [[981 + 2 * t, 0] for t in range(1, 10)]))
            out.append(([one, 0, 9], [[i, 0] for i in range(1000)]))
            out.append(([one, 9, 9], [[i, max(9 - i, 0)] for i in range(1000)]))
            out.append(([col, 0, 4], [[i, 0] for i in range(19992)] + [[19991 + 2 * t, 0] for t in range(1, 5)]))
        else:
            out.append(([col, 0, 4], comb(19995, 4) % o.MOD))
            out.append(([zero, 0, 4], sum(comb(19999 - j, j) for j in range(5)) % o.MOD))
            out.append(([[[0] * 20000], 123, 1], 1))
            out.append(([[[1]] * 20000, 0, 4], 1))
    elif uid == o.MBS:
        out.append(([list(range(n, 0, -1))], n // 2))
        out.append(([list(range(1, n + 1))], 0))
        out.append(([[7] * n], 0))
        out.append(([[2, 1] * (n // 2)], n // 2))
        out.append(([list(range(2, n + 1)) + [1]], 1))
    else:
        out.append(([n, [[i, i + 1] for i in range(n - 1)]], 1))
        out.append(([n, []], n))
        out.append(([n, [[i, (i + 1) % n] for i in range(n)]], 1))
        h = n // 2
        out.append(([n, [[i, (i + 1) % h] for i in range(h)] + [[h + i, h + (i + 1) % h] for i in range(h - 1)] + [[7, h]]], 1))
        out.append(([n, [[i, i] for i in range(n)]], n))
        out.append(([n, [[i + 1, i] for i in range(n - 1)]], 1))
    return out
