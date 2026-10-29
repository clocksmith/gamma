"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h17a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _code(i, width, base=97):
    s = ''
    for _ in range(width): s = chr(base + i % 26) + s; i //= 26
    return s


def _rpa(rng):
    k = rng.randrange(1, 5); n = k * rng.randrange(1, 6)
    return [[rng.randrange(-9, 10) for _ in range(n)], k, [rng.choice([0, 1, 2, rng.randrange(10**9 + 1)]) for _ in range(n - 1)]]


def _rdg(rng):
    n = rng.randrange(1, 9)
    return [[rng.randrange(1, 12) for _ in range(n)], rng.randrange(1, n + 1), rng.randrange(1, 40)]


def _rsq(rng):
    calls, live = [], []
    for _ in range(rng.randrange(0, 40)):
        r = rng.random()
        if r < 0.35:
            a = rng.randrange(0, 12); rep = (a, rng.randrange(a + 1, 14), rng.randrange(1, 9)); live.append(rep); calls.append(('addReport',) + rep)
        elif r < 0.55:
            if live and rng.random() < 0.7: rep = rng.choice(live); live.remove(rep)
            else: a = rng.randrange(0, 12); rep = (a, rng.randrange(a + 1, 14), rng.randrange(1, 9))
            calls.append(('removeReport',) + rep)
        else: calls.append(('getAverageSpeed', rng.randrange(0, 15)))
    if rng.random() < 0.1: calls.append(('addReport', 999990, 1000000, 7)); calls.append(('getAverageSpeed', 999999)); calls.append(('getAverageSpeed', 1000000))
    return _ops('RoadwaySpeedTracker', [], calls)


def _sss(rng):
    finish = rng.randrange(1, 80)
    return [finish, rng.sample(range(0, 90), rng.randrange(0, 9))]


def _sex(rng):
    def expr(d):
        parts = []
        for i in range(rng.randrange(1, 4)):
            op = '' if i == 0 else rng.choice('+-')
            if i == 0 and rng.random() < 0.3: op = '-'
            if d < 3 and rng.random() < 0.35: parts.append(op + '(' + expr(d + 1) + ')')
            else: parts.append(op + rng.choice(['a', 'b', 'c', 'x', 'yz', 'abc']))
        return ''.join(parts)
    return [expr(0)]


def _slp(rng):
    half = ''.join(rng.choice('abcz') for _ in range(rng.randrange(0, 4)))
    mid = rng.choice(['', rng.choice('abcz')])
    if not half and not mid: mid = 'q'
    return [half + mid + half[::-1]]


def _smp(rng):
    n = rng.randrange(1, 7); d = rng.randrange(1, 5)
    return [[rng.randrange(0, 10) for _ in range(n)], [[rng.choice([0, 0, rng.randrange(0, 6)]) for _ in range(n)] for _ in range(d)], rng.randrange(0, 4)]


def _str(rng):
    calls = []
    names = ['A', 'B', 'AB', 'BA', 'C', 'ZZ', 'AA']
    for _ in range(rng.randrange(0, 30)):
        if rng.random() < 0.6: calls.append(('recordTrade', rng.choice(names), rng.choice([1, 2, 3, 5, 10**6])))
        else: calls.append(('getRankedStocks',))
    return _ops('StockTracker', [], calls)


def _tok(rng):
    keys = rng.sample(['a', 'ab', 'abc', 'b', 'bc', 'ca', 'cab', 'c', 'aa', 'aaa'], rng.randrange(1, 7))
    return [''.join(rng.choice('abc d') for _ in range(rng.randrange(0, 16))), [k + ':' + str(rng.randrange(0, 1000)) for k in keys]]


def _smt(rng):
    n = rng.randrange(1, 14)
    return [[rng.randrange(0, 3) for _ in range(n)], rng.randrange(n), rng.randrange(1, n + 1)]


def _smc(rng):
    n = rng.randrange(1, 12)
    return [[rng.randrange(-3, 4) for _ in range(n)], [rng.randrange(n) for _ in range(rng.randrange(0, 8))]]


def _logs(rng):
    out = []
    for _ in range(rng.randrange(0, 14)):
        content = ''.join(rng.choice('ab :x9') for _ in range(rng.randrange(0, 6)))
        out.append('%s:%s:%d:%s' % (rng.choice(['p1', 'p2', 'P1', '10', '9']), rng.choice(['t1', 't2', 'T']), rng.choice([0, 1, 5, 9, 10, 100, 10**9]), content))
    return [out]


def _tha(rng):
    n = rng.randrange(1, 12)
    return [[rng.randrange(0, 8) for _ in range(n)], rng.randrange(1, n + 3), rng.randrange(0, 6)]


def _tele(rng, last):
    froms = rng.sample(range(1, last), rng.randrange(0, last)) if last > 1 else []
    out = []
    for a in froms:
        b = rng.randrange(0, last + 1)
        if b != a: out.append('%d,%d' % (a, b))
    return out


def _tp1(rng):
    last = rng.randrange(1, 25)
    return [_tele(rng, last), rng.randrange(1, 13), rng.randrange(0, last), last]


def _tp2(rng):
    last = rng.randrange(1, 40)
    return [_tele(rng, last), rng.randrange(1, 7), last]


def _ttl(rng):
    calls, running, kind, waiting, next_id = [], set(), None, [], 0
    for _ in range(rng.randrange(0, 30)):
        if running and rng.random() < 0.45:
            job = rng.choice(sorted(running)); calls.append(('release', job)); running.discard(job)
            if not running and waiting:
                kind = waiting[0][1]
                while waiting and waiting[0][1] == kind: running.add(waiting.pop(0)[0])
        else:
            t = rng.choice(['gen', 'score']); calls.append(('acquire', next_id, t))
            if not waiting and (not running or kind == t): running.add(next_id); kind = t
            else: waiting.append((next_id, t))
            next_id += rng.choice([1, 1, 7])
    return _ops('MutexTaskLock', [], calls)


def _url(rng):
    pieces = []
    for _ in range(rng.randrange(0, 7)):
        r = rng.random()
        if r < 0.1: pieces.append('')
        elif r < 0.2: pieces.append(rng.choice(['a', 'b', 'k-1']))
        elif r < 0.25: pieces.append('=v')
        else: pieces.append(rng.choice(['a', 'b', 'k-1', 'Year']) + '=' + rng.choice(['', '1', 'x.y', 'a=b', 'q?r', '~z']))
    head = rng.choice(['http://site.com/path', 'https://a.b/c', '', '/p'])
    if rng.random() < 0.1: return [head]
    return [head + '?' + '&'.join(pieces)]


GEN = {_o.RPA: _rpa, _o.RDG: _rdg, _o.RSQ: _rsq, _o.SSS: _sss, _o.SEX: _sex, _o.SLP: _slp, _o.SMP: _smp, _o.STR: _str, _o.TOK: _tok, _o.SMT: _smt,
       _o.SMC: _smc, _o.TL1: _logs, _o.TL2: _logs, _o.THA: _tha, _o.TP1: _tp1, _o.TP2: _tp2, _o.TTL: _ttl, _o.URL: _url}

LOGS = ['p1:t1:5:start', 'p1:t1:3:boot:ok', 'p0:t9:7:', 'p1:T2:5:x', 'p1:t1:5:again', 'p10:t1:1:z']
HAND = {
    _o.RPA: [[[7], 1, []], [[1, 2, 3, 4], 2, [0, 0, 0]], [[1, 2, 3, 4], 4, [3, 2, 1]], [[5, 6, 7, 8, 9, 10], 3, [10**9, 7, 2, 1, 0]]],
    _o.RDG: [[[3, 2, 1, 4, 5], 2, 6], [[9], 1, 1], [[1, 1, 1], 3, 2], [[5, 5, 5], 2, 10], [[10, 1, 1, 1], 2, 2]],
    _o.RSQ: [_ops('RoadwaySpeedTracker', [], [('getAverageSpeed', 0), ('addReport', 0, 10, 30), ('addReport', 5, 15, 50), ('getAverageSpeed', 4), ('getAverageSpeed', 5),
                                              ('getAverageSpeed', 10), ('getAverageSpeed', 15), ('addReport', 5, 6, 1), ('getAverageSpeed', 5), ('removeReport', 0, 10, 31),
                                              ('removeReport', 0, 10, 30), ('getAverageSpeed', 5), ('removeReport', 0, 10, 30)])],
    _o.SSS: [[30, [5]], [100, []], [25, [0, 10, 20]], [12, [15, 3, 7]], [5, [5, 6]], [1, [0]]],
    _o.SEX: [['a'], ['a-(b+c)'], ['-(a-b)'], ['a-(b-(c-d))'], ['(a)+((b))'], ['x-(-y+z)'], ['-a+(-(-b))']],
    _o.SLP: [['a'], ['aba'], ['bab'], ['zaz'], ['cbaabc'], ['bacab']],
    _o.SMP: [[[1, 3, 2], [[0, 0, 0]], 0], [[0, 0], [[2, 0], [0, 3]], 1], [[5, 1, 5], [[0, 4, 0], [0, 4, 0], [0, 0, 0]], 2], [[7], [[1], [2]], 5]],
    _o.STR: [_ops('StockTracker', [], [('getRankedStocks',), ('recordTrade', 'AAPL', 5), ('recordTrade', 'MSFT', 7), ('getRankedStocks',), ('recordTrade', 'AAPL', 3),
                                       ('getRankedStocks',), ('getRankedStocks',), ('recordTrade', 'GOOG', 8), ('getRankedStocks',)])],
    _o.TOK: [['abc', ['a:1', 'ab:2', 'abc:3']], ['abcd', ['ab:7', 'bcd:9']], ['', ['a:1']], ['the cat', ['the:5', 'cat:6', 'ca:4']], ['aaa', ['aa:0']]],
    _o.SMT: [[[1, 2, 1, 1, 3, 1], 0, 3], [[4, 4, 4], 2, 1], [[5, 6, 7], 1, 3], [[0, 1, 0, 1, 1], 1, 2]],
    _o.SMC: [[[1, 3, 2, 3, 1], [0, 2, 4, 3]], [[5], [0, 0]], [[2, 2, 2], []], [[-1, -2, -2], [1, 0]]],
    _o.TL1: [[LOGS], [[]]],
    _o.TL2: [[LOGS], [[]]],
    _o.THA: [[[2, 2, 2, 2, 5, 5, 5, 8], 3, 4], [[1], 2, 0], [[0, 0, 0], 1, 0], [[3, 4, 5], 3, 4]],
    _o.TP1: [[['3,8', '5,1'], 6, 0, 20], [[], 6, 17, 20], [['2,3'], 3, 0, 4], [['1,0'], 1, 0, 2]],
    _o.TP2: [[[], 6, 20], [['1,0', '2,0', '3,0'], 3, 10], [['2,19'], 2, 20], [['1,5', '5,0'], 1, 6], [[], 1, 1]],
    _o.TTL: [_ops('MutexTaskLock', [], [('acquire', 1, 'gen'), ('acquire', 2, 'gen'), ('acquire', 3, 'score'), ('acquire', 4, 'gen'), ('acquire', 5, 'score'),
                                        ('release', 1), ('release', 2), ('release', 3), ('release', 4), ('acquire', 6, 'score'), ('release', 5), ('acquire', 7, 'gen')])],
    _o.URL: [['http://x.com/m?year=100&type=action'], ['/p'], ['/p?a=1&a=2&b&&=x&c=d=e'], ['?q?r=1'], ['http://x.com/?']],
}


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode()))
    args = list(HAND[uid]) + [GEN[uid](rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def _logline(j, n):
    return 'P%d:T%d:%d:m:%d' % (j % 4, j % 5, n - j, j)


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []
    n = 100000
    if uid == o.RPA:
        # every swap index 0: the shuffle rotates left by one
        out.append(([list(range(n)), 4, [0] * (n - 1)], [list(range(1, n // 4 + 1))] + [list(range(s * n // 4 + 1, (s + 1) * n // 4 + 1)) for s in (1, 2)]
                    + [list(range(3 * n // 4 + 1, n)) + [0]]))
        # r = i at step i keeps every element in place
        out.append(([[10**9 - i for i in range(n)], n, [n - 1 - t for t in range(n - 1)]], [[10**9 - i] for i in range(n)]))
        out.append(([[-10**9] * n, 1, [10**9] * (n - 1)], [[-10**9] * n]))
    elif uid == o.RDG:
        out.append(([[10**9] * n, 1, 10**9], 0))
        out.append(([[10**9] * n, 2, 10**9], n - 1))
        out.append(([list(range(1, n + 1)), n, 10**9], 1))
        out.append(([[1] * n, 1000, 1000], 0))
        # remaining 1..m works while m + (m - 1) <= 100001, so m = 50001
        out.append(([list(range(n, 0, -1)), 2, 100001], n - 50001))
    elif uid == o.RSQ:
        calls, want = [], [None]
        for s in range(1, 30001): calls.append(('addReport', 0, 10**6, s)); want.append(None)
        calls += [('getAverageSpeed', 0), ('getAverageSpeed', 999999), ('getAverageSpeed', 10**6)]; want += [15000.5, 15000.5, -1.0]
        for s in range(1, 30001):
            calls += [('removeReport', 0, 10**6, s), ('getAverageSpeed', 500000)]; want += [True, (s + 1 + 30000) / 2 if s < 30000 else -1.0]
        calls.append(('removeReport', 0, 10**6, 1)); want.append(False)
        out.append((_ops('RoadwaySpeedTracker', [], calls), want))
        calls, want = [], [None]
        for i in range(50000): calls.append(('addReport', 20 * i, 20 * i + 1, i + 1)); want.append(None)
        for i in range(49999, -1, -1): calls.append(('getAverageSpeed', 20 * i)); want.append(float(i + 1))
        out.append((_ops('RoadwaySpeedTracker', [], calls), want))
    elif uid == o.SSS:
        out.append(([10**9, list(range(0, 2 * 10**6, 20))], 10**9 - 10**6))
        out.append(([10**9, list(range(999990, -1, -10))], 10**9 - 10**6))
        out.append(([10**9, list(range(n))], 10**9 - (n + 9)))
        out.append(([5, list(range(5, n + 5))], 5))
        out.append(([n * 10, list(range(n * 10 - 1, -1, -10))], 9))
    elif uid == o.SEX:
        d = 24000
        out.append((['a' + '-(b' * d + ')' * d], 'a' + ''.join('-b' if t % 2 == 0 else '+b' for t in range(d))))
        out.append((['-(' + '+'.join(_code(i, 3) for i in range(24000)) + ')'], ''.join('-' + _code(i, 3) for i in range(24000))))
        out.append((['(' * 49999 + 'x' + ')' * 49999], 'x'))
        out.append((['-(-(' * 12000 + 'q' + '))' * 12000], 'q'))
    elif uid == o.SLP:
        out.append((['b' * 25000 + 'a' * 49999 + 'b' * 25000], 'a' * 24999 + 'b' * 25000 + 'a' + 'b' * 25000 + 'a' * 24999))
        x = ''.join(chr(122 - i % 26) for i in range(50000))
        half = ''.join(chr(97 + c) * (50000 // 26 + (1 if 25 - c < 50000 % 26 else 0)) for c in range(26))
        out.append(([x + x[::-1]], half + half[::-1]))
        out.append((['z' * n], 'z' * n))
    elif uid == o.SMP:
        out.append(([list(range(n)), [[5] * n, [0] * n], 1], [n - 1, n - 1]))
        out.append(([[0] * 1000, [[2 if i % 2 == 0 else 0 for i in range(1000)] for _ in range(200)], 1], [499 * (d + 1) for d in range(200)]))
        out.append(([[10**6, 0] * 1000, [[1000] * 2000 for _ in range(100)], 0], [999 * 10**6] * 100))
    elif uid == o.STR:
        m = 3000; names = [_code(i, 3, 65) for i in range(m)]
        calls, want = [], [None]
        for i in range(m): calls.append(('recordTrade', names[i], m - i)); want.append(None)
        for r in range(29):
            for i in range(m): calls.append(('recordTrade', names[i], 1)); want.append(None)
        for _ in range(150): calls.append(('getRankedStocks',)); want.append(list(names))
        out.append((_ops('StockTracker', [], calls), want))
        names = [_code(i, 4, 65) for i in range(50000)]
        calls = [('recordTrade', names[i], 5) for i in range(49999, -1, -1)] + [('getRankedStocks',)]
        out.append((_ops('StockTracker', [], calls), [None] * 50001 + [names]))
        names = [_code(i, 3, 65) for i in range(600)]
        calls, want = [], [None]
        for i in range(600): calls.append(('recordTrade', names[i], 10**6)); want.append(None)
        for i in range(599, -1, -1):  # names[i:] now hold 1e6 + 1, the rest 1e6
            calls += [('recordTrade', names[i], 1), ('getRankedStocks',)]
            want += [None, names[i:] + names[:i]]
        out.append((_ops('StockTracker', [], calls), want))
    elif uid == o.TOK:
        out.append((['a' * n, ['a' * k + ':' + str(k) for k in range(1, 21)]], ['20'] * 5000))
        out.append((['ab' * 50000, ['ab:1', 'a:2', 'abb:3']], ['1'] * 50000))
        out.append((['z' * n, ['a:1']], ['z'] * n))
        out.append(([('a' * 19 + 'b') * 5000, ['a' * 20 + ':9', 'a:1', 'b:2']], (['1'] * 19 + ['2']) * 5000))
        out.append(([' ' * n, [_code(i, 3) + ':' + str(i) for i in range(10000)]], [' '] * n))
    elif uid == o.SMT:
        out.append(([[7] * n, 5, n], 0))
        out.append(([[i % 3 for i in range(n)], 0, 3], 0))
        out.append(([[1] * (n - 1000) + [2] * 1000, n - 1, 1000], n - 1000))
        out.append(([[1] * (n - 1) + [2], n - 1, 1], n - 1))
        out.append(([[-10**9 if i % 1000 == 999 else 10**9 for i in range(n)], 999, 50000], 0))
    elif uid == o.SMC:
        out.append(([list(range(n)), list(range(n))], [1] * n))
        out.append(([[3] * n, list(range(n - 1, -1, -1))], list(range(1, n + 1))))
        out.append(([[i % 2 for i in range(n)], list(range(n))], [n // 2 - q // 2 for q in range(n)]))
    elif uid in (o.TL1, o.TL2):
        logs = [_logline(j, n) for j in range(n)]
        groups = [(p, t) for p in range(4) for t in range(5)]
        if uid == o.TL1:
            out.append(([logs], [logs[j] for p, t in groups for j in range(n - 1, -1, -1) if j % 4 == p and j % 5 == t]))
            same = ['A:B:7:%d' % j for j in range(n)]
            out.append(([same], same))
            out.append(([[_logline(j, 10**9) for j in range(n - 1, -1, -1)]], [_logline(j, 10**9) for p, t in groups for j in range(n - 1, -1, -1) if j % 4 == p and j % 5 == t]))
        else:
            res = []
            for p, t in groups:
                r = next(j for j in range(20) if j % 4 == p and j % 5 == t)
                res.append('P%d:T%d:%d:%d:%d' % (p, t, n // 20, n - (r + 20 * (n // 20 - 1)), n - r))
            out.append(([logs], res))
            out.append(([['A:B:7:%d' % j for j in range(n)]], ['A:B:%d:7:7' % n]))
            out.append(([['x%d:y:%d:' % (j, j) for j in range(n)]], ['x%d:y:1:%d:%d' % (j, j, j) for j in sorted(range(n), key=lambda j: 'x%d' % j)]))
    elif uid == o.THA:
        out.append(([[10] * n, 1000, 10], n - 999))
        out.append(([[10] * n, 1000, 11], 0))
        out.append(([[0, 20] * (n // 2), 2, 10], n - 1))
        out.append(([[0, 20] * (n // 2), 3, 10], (n - 2) // 2))
        out.append(([[10**4] * n, 10**5, 10**4], 1))
        out.append(([[10**4] * 10, 10**5, 0], 0))
    elif uid == o.TP1:
        tele = ['%d,%d' % (i, i + 50000) for i in range(1, 50000)]
        out.append(([tele, 12, 0, n], list(range(50001, 50013))))
        tele = ['%d,0' % i for i in range(1, n)]
        out.append(([tele, 12, n - 5, n], [0, n]))
        out.append(([tele, 12, 0, n], [0]))
    elif uid == o.TP2:
        out.append(([[], 6, n], (n + 5) // 6))
        out.append(([[], 12, n], (n + 11) // 12))
        out.append(([['%d,%d' % (i, n - 1) for i in range(1, 7)], 6, n], 2))
        out.append(([['%d,0' % i for i in range(1, n)], 6, n], -1))
        # every non-multiple of 12 sends the player back to 0, so only rolls of 12 make progress
        out.append(([['%d,0' % i for i in range(1, n) if i % 12], 12, n], (n + 11) // 12))
    elif uid == o.TTL:
        calls, want = [], [None]
        for j in range(30000): calls.append(('acquire', j, 'gen')); want.append(True)
        calls.append(('acquire', 10**9, 'score')); want.append(False)
        for j in range(100): calls.append(('acquire', 30000 + j, 'gen')); want.append(False)
        for j in range(30000): calls.append(('release', j)); want.append([] if j < 29999 else [10**9])
        calls.append(('release', 10**9)); want.append(list(range(30000, 30100)))
        out.append((_ops('MutexTaskLock', [], calls), want))
        calls, want = [], [None]
        for j in range(50000): calls.append(('acquire', j, 'gen' if j % 2 == 0 else 'score')); want.append(j == 0)
        for j in range(50000): calls.append(('release', j)); want.append([j + 1] if j < 49999 else [])
        out.append((_ops('MutexTaskLock', [], calls), want))
    elif uid == o.URL:
        q = '&'.join('k%d=v%d' % (i, i) for i in range(7000))
        out.append((['http://x.com/p?' + q], {'k%d' % i: 'v%d' % i for i in range(7000)}))
        out.append((['/p?' + '&'.join('a=%d' % i for i in range(13000))], {'a': [str(i) for i in range(13000)]}))
        out.append((['/' * n], {}))
        out.append((['?' + '&' * (n - 3) + 'k'], {'k': ''}))
    return out
