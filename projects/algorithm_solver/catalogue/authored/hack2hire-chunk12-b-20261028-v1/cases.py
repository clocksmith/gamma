"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h12b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _sorted_list(rng, lo, hi, size):
    return sorted(rng.randrange(lo, hi) for _ in range(size))


def _mda(rng):
    span = rng.choice([20, 100, 1000, 10**9])
    return [_sorted_list(rng, -span, span + 1, rng.randrange(1, 40)), _sorted_list(rng, -span, span + 1, rng.randrange(1, 40))]


def _mvs(rng):
    scores = [rng.randrange(-20, rng.choice([5, 30, 300]) + 1) for _ in range(rng.randrange(1, 15))]
    return [scores, rng.randrange(0, 60)]


def _mcv(rng):
    top = rng.choice([8, 100, 1000, 10**9])
    return [[rng.randrange(0, top + 1) for _ in range(rng.randrange(0, 15))], rng.randrange(0, 20)]


def _msd(rng):
    names = ['milk', 'Eggs', 'tent', 'rope', 'apple', 'Bread 2', 'rice', 'gas']; depts = ['Dairy', 'Produce', 'Pantry', 'Camping']
    chosen = rng.sample(names, rng.randrange(0, len(names) + 1))
    products = [[n, rng.choice(depts)] for n in chosen]
    shopping = [rng.choice(names + ['salt']) for _ in range(rng.randrange(0, 12))]
    return [products, shopping]


def _mcc(rng):
    coins = rng.sample(range(2, 26), rng.randrange(1, 5)) + ([1] if rng.random() < 0.4 else [])
    rng.shuffle(coins)
    return [coins, rng.randrange(0, 61)]


def _mdp(rng):
    span = rng.choice([3, 10, 1000, 10**9])
    return [[rng.randrange(-span, span + 1) for _ in range(rng.randrange(1, 30))]]


def _mfg(rng):
    n, m = rng.randrange(1, 9), rng.randrange(1, 9)
    return [[''.join(rng.choice('BW') for _ in range(m)) for _ in range(n)]]


def _mik(rng):
    n = rng.randrange(1, 11); s = ''
    while len(s) < n: s += rng.choice('ab') * rng.randrange(1, 6)
    s = s[:n]
    return [s, rng.randrange(0, min(n, 4) + 1)]


def _mmt(rng):
    tasks = []
    for _ in range(rng.randrange(0, 25)):
        s = rng.randrange(0, 20); tasks.append([s, s + rng.randrange(1, 8)])
    return [tasks]


def _binary_tree(rng, size):
    """Random binary tree with size nodes, serialised in canonical level order."""
    if size == 0: return []
    left, right = [-1] * size, [-1] * size
    for v in range(1, size):
        while True:
            p = rng.randrange(v)
            side = left if rng.random() < 0.5 else right
            if side[p] == -1: side[p] = v; break
    values = [rng.randrange(-5, 10) for _ in range(size)]
    out, queue, head = [values[0]], [0], 0
    while head < len(queue):
        node = queue[head]; head += 1
        for c in (left[node], right[node]):
            if c == -1: out.append(None)
            else: out.append(values[c]); queue.append(c)
    while out[-1] is None: out.pop()
    return out


def _mrl(rng):
    return [_binary_tree(rng, rng.randrange(0, 25))]


def _msb(rng):
    return [[rng.randrange(-9, 10) for _ in range(rng.randrange(1, 20))]]


def _msk(rng):
    top = rng.choice([2, 4, 8, 10**9])
    arr = [rng.randrange(1, top + 1) for _ in range(rng.randrange(1, 40))]
    return [arr, rng.randrange(1, 7)]


def _mse(rng):
    return [[rng.randrange(-9, 10) for _ in range(rng.randrange(0, 11))]]


def _nary(values, children):
    out = [values[0], None]
    for node in range(len(values)):
        out.extend(values[c] for c in children[node]); out.append(None)
    while out and out[-1] is None: out.pop()
    return out


def _nary_random(rng, size):
    """Random N-ary tree whose node ids are in breadth-first order, so children lists serialise directly."""
    if size == 0: return []
    parent = [-1] + [0] * (size - 1)
    for v in range(1, size): parent[v] = rng.randrange(max(0, v - 4), v)  # non-decreasing parents keep BFS order
    for v in range(2, size): parent[v] = max(parent[v], parent[v - 1])
    children = [[] for _ in range(size)]
    for v in range(1, size): children[parent[v]].append(v)
    values = [rng.randrange(-3, 10) for _ in range(size)]
    return _nary(values, children)


def _ntl(rng):
    return [_nary_random(rng, rng.randrange(0, 25))]


def _nsb1(rng):
    if rng.random() < 0.5:
        out, open_ = '', 0
        for _ in range(rng.randrange(0, 20)):
            ch = rng.choice('(()a,') if open_ else rng.choice('(a,')
            open_ += {'(': 1, ')': -1}.get(ch, 0); out += ch
        return [out + ')' * open_ if rng.random() < 0.8 else out]
    alphabet = rng.choice(['()', '()a,', '(()))(ab,'])
    return [''.join(rng.choice(alphabet) for _ in range(rng.randrange(0, 20)))]


def _nested(rng, depth):
    items = []
    for _ in range(rng.randrange(0, 4)):
        if depth < 4 and rng.random() < 0.35: items.append(_nested(rng, depth + 1))
        else: items.append(''.join(rng.choice('abz') for _ in range(rng.randrange(1, 4))))
    return '(' + ','.join(items) + ')'


def _nsb2(rng):
    return [_nested(rng, 0)]


def _ngp(rng):
    if rng.random() < 0.3:
        half = str(rng.randrange(1, 1000)); s = half + half[::-1][rng.randrange(0, 2):]
        return [s[:7]]
    return [str(rng.randrange(1, 10 ** rng.randrange(1, 8)))]


GEN = {_o.MDA: _mda, _o.MVS: _mvs, _o.MCV: _mcv, _o.MSD: _msd, _o.MCC: _mcc, _o.MDP: _mdp, _o.MFG: _mfg, _o.MIK: _mik, _o.MMT: _mmt,
       _o.MRL: _mrl, _o.MSB: _msb, _o.MSK: _msk, _o.MSE: _mse, _o.NTL: _ntl, _o.NSB1: _nsb1, _o.NSB2: _nsb2, _o.NGP: _ngp}

HAND = {
    _o.MDA: [[[1], [1]], [[1, 3], [23]], [[1, 2, 11, 15], [4, 12, 19, 23, 127, 235]], [[1, 5], [3]], [[-5, -5, 0], [-5, 7]]],
    _o.MVS: [[[0, -3], 0], [[5], 0], [[5], 1], [[5, 5, 5], 3], [[7, 3], 4], [[10, 1, 1], 6]],
    _o.MCV: [[[], 3], [[10, 6], 0], [[10, 6], 1], [[10, 6], 3], [[1, 1, 1], 100], [[9], 2]],
    _o.MSD: [[[], []], [[['milk', 'Dairy'], ['cheese', 'Dairy'], ['apple', 'Produce']], ['milk', 'apple', 'cheese', 'milk', 'tent']]],
    _o.MCC: [[[1], 0], [[2], 3], [[1, 2, 5], 11], [[1, 3, 4], 6], [[5, 3], 7], [[2, 4], 9]],
    _o.MDP: [[[5]], [[1, 2]], [[2, 1]], [[1, 2, 3, 100]], [[-1, -1, 5]], [[3, 3, 1, 1]]],
    _o.MFG: [[['B']], [['BW']], [['BW', 'WB']], [['BBW', 'WBW', 'BWB']]],
    _o.MIK: [['a', 0], ['aab', 0], ['aaaa', 1], ['aaaaa', 1], ['abab', 0], ['aaabbb', 2], ['aaaa', 2]],
    _o.MMT: [[[]], [[[0, 30], [5, 10], [15, 20]]], [[[1, 2], [2, 3]]], [[[1, 5], [1, 5], [1, 5]]]],
    _o.MRL: [[[]], [[1]], [[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1]], [[1, 2, 2]], [[-1, None, -2, None, -3]], [[1, 2, 3, 4]]],
    _o.MSB: [[[1]], [[3, -2, 4]], [[-5, 1]], [[0, 0]], [[2, 2, -10, 1]]],
    _o.MSK: [[[1], 1], [[1], 2], [[1, 2, 1, 3, 4], 3], [[5, 5, 5], 1], [[1, 2, 2, 2, 3, 1], 3]],
    _o.MSE: [[[]], [[2, 4, 1]], [[1, 2]], [[1, 3, 2, 4]], [[-3, -2, 7, 8, 0]]],
    _o.NTL: [[[]], [[1]], [[1, None, 3, 2, 4, None, 5, 6]], [[1, None, 2, None, 3, None, 4]], [[7, None, 7, 7, None, 7]]],
    _o.NSB1: [[''], ['()'], [')('], ['(a,(b,c))'], ['((a)'], ['abc,d'], ['(()'], ['())']],
    _o.NSB2: [['()'], ['(a)'], ['(a,b)'], ['(a,(b,c),d)'], ['((),(()),xyz)'], ['(((deep)))']],
    _o.NGP: [['1'], ['9'], ['11'], ['99'], ['123'], ['808'], ['1299'], ['9999'], ['12921'], ['10']],
}


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode()))
    args = [list(a) for a in HAND[uid]] + [GEN[uid](rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []; n = 100000
    if uid == o.MDA:
        out.append(([list(range(0, 2 * n, 2)), list(range(1, 2 * n, 2))], [0, 1]))
        A = [-10**9 + 3 * i for i in range(n)]; B = [10**9 - 3 * (n - 1 - i) for i in range(n)]
        out.append(([A, B], [A[-1], B[0]]))
        out.append(([[5] * n, [5] * n], [5, 5]))
        out.append(([[10**9] * n, [-10**9] * (n - 1) + [10**9 - 1]], [10**9, 10**9 - 1]))
    elif uid == o.MVS:
        out.append(([[10**9] * n, 10**9], 100000))  # n * ceil(1e9 / x) <= 1e9  <=>  ceil(1e9 / x) <= 1e4
        out.append(([[1] * n, n - 1], -1))
        out.append(([[0] * (n - 1) + [-10**9], 0], 1))
        out.append(([list(range(1, n + 1)), n], n))
    elif uid == o.MCV:
        out.append(([[10**9] * n, n], 5 * 10**8 * n))
        out.append(([[10**9] * n, 0], 10**14))
        out.append(([[1] * n, n], 0))
        out.append(([[2**29] + [1] * (n - 1), 30], n - 1))  # 30 halvings take 2**29 to 0; the ones never beat a larger saving
    elif uid == o.MSD:
        prods = [[f'p{i}', f'd{i % 100}'] for i in range(n)]
        out.append(([prods, [f'p{i}' for i in range(n)]], 100))
        out.append(([prods, ['missing'] * n], 0))
        out.append(([[[f'item {i}', f'dept {i}'] for i in range(n)], [f'item {n - 1 - i}' for i in range(n)]], n))
    elif uid == o.MCC:
        coins = list(range(1, 51)); exp = [0] * 50; exp[49] = 200
        out.append(([coins, 10000], exp))
        out.append(([[3, 7], 10000], [6, 1426]))  # 7a + 3b = 10000: a = 1426, b = 6 is the largest a
        out.append(([[2, 4], 9999], []))
        out.append(([[10000, 9999, 1], 10000], [1, 0, 0]))
        out.append(([list(range(9951, 10001)), 0], [0] * 50))
    elif uid == o.MDP:
        nums = [(i * 7919) % n for i in range(n)]  # a permutation of 0 .. n - 1
        out.append(([nums], [49999, sum(abs(v - 49999) for v in range(n))]))
        out.append(([[10**9] * n], [10**9, 0]))
        out.append(([[-10**9, 10**9] * (n // 2)], [-10**9, (n // 2) * 2 * 10**9]))
    elif uid == o.MFG:
        out.append(([['B' * 500] * 500], 0))
        out.append(([[('BW' * 250) if i % 2 == 0 else ('WB' * 250) for i in range(500)]], 125000))
        out.append(([['B' * 125000 + 'W' * 125000]], 125000))
        out.append(([['W'] * 250000], 0))
    elif uid == o.MIK:
        out.append((['a' * n, 0], n))
        out.append((['a' * n, n // 2], 1))
        out.append((['a' * n, 1], 50000))
        out.append((['ab' * (n // 2), 0], 1))
        out.append((['a' * 50000 + 'b' * 50000, 4], 16666))  # 2 * floor(50000 / (L + 1)) <= 4  <=>  L + 1 >= 16667
    elif uid == o.MMT:
        out.append(([[[0, 10**9]] * n], n))
        out.append(([[[i, i + 1] for i in range(n)]], 1))
        out.append(([[[i, 2 * n - i] for i in range(n)]], n))
        out.append(([[[2 * i, 2 * i + 3] for i in range(n)]], 2))
    elif uid == o.MRL:
        chain = [1]
        for v in range(2, n + 1): chain += [v, None]
        chain.pop()
        out.append(([chain], list(range(1, n + 1))))
        perfect = [7] * (2**16 - 1)  # every leaf at depth 15: leftmost path of 16 sevens
        out.append(([perfect], [7] * 16))
        right = [10**9]
        for _ in range(n - 1): right += [None, -10**9]
        out.append(([right], [10**9] + [-10**9] * (n - 1)))
    elif uid == o.MSB:
        out.append(([[10**9] * n], 10**14 + 1))
        out.append(([[-10**9] * n], 1))
        out.append(([[-10**9, 10**9] * (n // 2)], 1))
        out.append(([[10**9, -10**9] * (n // 2)], 10**9 + 1))
    elif uid == o.MSK:
        out.append(([list(range(1, n + 1)), n], n))
        out.append(([list(range(1, n)), n], -1))
        out.append(([[7] * n, 2], -1))
        out.append(([[(i % 1000) + 1 for i in range(n)], 1000], 1000))
        out.append(([[1] * (n - 1) + [10**9], 2], 2))
    elif uid == o.MSE:
        out.append(([[1] * n], 0))
        out.append(([[1] * (n // 2) + [2] * (n // 2)], n // 2))
        out.append(([[-10**9 + 1] * (n // 2) + [-10**9] * (n // 2)], n // 2))
        out.append(([[0] * n], 0))
    elif uid == o.NTL:
        star = [0, None] + list(range(1, n))
        out.append(([star], [list(range(1, n)), [0]]))
        chain = [1, None]
        for v in range(2, n + 1): chain += [v, None]
        chain.pop()
        out.append(([chain], [[v] for v in range(n, 0, -1)]))
        out.append(([[5, None] + [9] * (n - 1)], [[9] * (n - 1), [5]]))
    elif uid == o.NSB1:
        out.append((['(' * 50000 + ')' * 50000], True))
        out.append((['(' * 50000 + ')' * 49999 + ','], False))
        out.append((['(a,b)' * 20000], True))
        out.append(([')' + '(' * 99999], False))
        out.append((['abc,' * 25000], True))
    elif uid == o.NSB2:
        words = ['w' + chr(97 + i % 26) for i in range(33333)]
        out.append((['(' + ','.join(words) + ')'], words))
        deep = '(' * 100 + 'x' + ')' * 100
        expected = 'x'
        for _ in range(100): expected = [expected]
        out.append(([deep], expected))
        out.append((['(' + ','.join(['()'] * 33333) + ')'], [[] for _ in range(33333)]))
    elif uid == o.NGP:
        out.append((['9' * n], '1' + '0' * (n - 1) + '1'))
        out.append((['1' + '0' * (n - 1)], '1' + '0' * (n - 2) + '1'))
        out.append((['1' * n], '1' * (n // 2 - 1) + '22' + '1' * (n // 2 - 1)))
        out.append((['1' + '9' * (n - 1)], '2' + '0' * (n - 2) + '2'))
    return out
