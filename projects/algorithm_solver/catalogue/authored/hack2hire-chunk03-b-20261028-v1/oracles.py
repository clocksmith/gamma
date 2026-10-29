"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-28 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (exhaustive enumeration,
breadth-first search over whole states, literal replays, quadratic scans).
"""
from collections import deque
from functools import lru_cache
from itertools import product
import re

H = 'hack2hire:'
MAXT = H + '69bef61921f6ab4226963c5a'
MERGE = H + '6907bf40e1919109b6df11ab'
ZERO = H + '698793abfedd959e9aa444b7'
ROTF = H + '6a32d62c65569fa70cc7eba3'
LAYER = H + '69fff432574d87bc4900732f'
BALLS = H + '69e939d0fbaf3da6418286b1'
VCONV = H + '6a330b986849fecc81440a21'
CHAIN = H + '68ac0aa71bf7d2097f647ee2'
MUSIC1 = H + '691e23ea08ad7861624b569b'
MUSIC2 = H + '691e30e108ad7861624b56aa'
MUSIC3 = H + '691e30e408ad7861624b56ab'
NGRAM1 = H + '67fad958ba41b3368f4e586c'
NGRAM2 = H + '67faf48fba41b3368f4e5879'
PARTY1 = H + '695743551e6311b59b803d6a'
PARTY2 = H + '69609171bb250997304ac843'
PAINT = H + '68fd382047bea664c0bba31e'
PHONE = H + '688bc3a43867670cfb89417c'
POKER1 = H + '695d6a6a68e2c0dd046c4b00'
POKER2 = H + '695ec22e9c1c1f40daea759e'
PRODMM = H + '6a973a3a0ca9cc4e1c789e48'
PURCH = H + '69e93b39fbaf3da6418286bb'

IDS = (MAXT, MERGE, ZERO, ROTF, LAYER, BALLS, VCONV, CHAIN, MUSIC1, MUSIC2, MUSIC3, NGRAM1, NGRAM2,
       PARTY1, PARTY2, PAINT, PHONE, POKER1, POKER2, PRODMM, PURCH)

_MUSIC_L1 = {'addSong': 1, 'playSong': 2, 'getAnalytics': 0}
_MUSIC_L2 = {**_MUSIC_L1, 'getLastThreeSongs': 1}
_MUSIC_L3 = {**_MUSIC_L2, 'removeSong': 1}
# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    MUSIC1: ('MusicPlayer', 0, _MUSIC_L1, ('playSong',)),
    MUSIC2: ('MusicPlayer', 0, _MUSIC_L2, ('playSong',)),
    MUSIC3: ('MusicPlayer', 0, _MUSIC_L3, ('playSong',)),
}
MOD = 1_000_000_007
WORD = r'[a-z]{1,10}'
NAME = r'[a-z_][a-z0-9_]{0,19}'
TOKEN = r'[A-Za-z0-9_-]{1,20}'
RANKS = ('2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A')
SUITS = ('hearts', 'diamonds', 'clubs', 'spades')


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def strlist(a, pattern, minimum=0, maximum=100000, width=100):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')
    for v in a: text(v, pattern, width)


def decimal(s, lo, hi):
    if type(s) is not str or re.fullmatch(r'0|-?[1-9][0-9]{0,15}', s) is None: raise ValueError('decimal string')
    v = int(s)
    if not lo <= v <= hi: raise ValueError('decimal range')
    return v


def trace(uid, args, maximum):
    name, ctor, methods, _ = CLASSES[uid]
    envelope(args, 2)
    ops, rows = args
    if type(ops) is not list or type(rows) is not list or not 1 <= len(ops) <= maximum or len(ops) != len(rows):
        raise ValueError('trace shape')
    if ops[0] != name or type(rows[0]) is not list or len(rows[0]) != ctor: raise ValueError('initial constructor')
    for op, row in zip(ops[1:], rows[1:]):
        if type(op) is not str or op not in methods or type(row) is not list or len(row) != methods[op]:
            raise ValueError('method or arity')
    return ops, rows


def parse_event(s):
    m = re.fullmatch(r'(0|[1-9][0-9]{0,9}), (0|-?[1-9][0-9]{0,6})', s) if type(s) is str else None
    if m is None: raise ValueError('event format')
    t, d = int(m.group(1)), int(m.group(2))
    if t > 10**9 or abs(d) > 10**6: raise ValueError('event range')
    return t, d


def parse_card(s):
    m = re.fullmatch(r'(10|[2-9JQKA]) of (hearts|diamonds|clubs|spades)', s) if type(s) is str else None
    if m is None: raise ValueError('card format')
    return m.group(1), m.group(2)


def party_rows(windows, geo):
    if type(windows) is not list or type(geo) is not list or not len(windows) == len(geo) <= 100000: raise ValueError('party lists')
    span, place = {}, {}
    for row in windows:
        if type(row) is not list or len(row) != 3: raise ValueError('window row')
        text(row[0], TOKEN, 20)
        s, e = decimal(row[1], 0, 10**6), decimal(row[2], 0, 10**6)
        if s >= e or row[0] in span: raise ValueError('window interval or duplicate id')
        span[row[0]] = (s, e)
    for row in geo:
        if type(row) is not list or len(row) != 2: raise ValueError('geo row')
        text(row[0], TOKEN, 20); text(row[1], TOKEN, 20)
        if row[0] in place or row[0] not in span: raise ValueError('geo id must match exactly one window')
        place[row[0]] = row[1]
    return span, place


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == MAXT:
        envelope(args, 3)
        array(args[0], 1, 10**6, 1, 20000); array(args[1], 1, 10**6, 1, 20000); integer(args[2], 0, 10**9)
        if len(args[0]) != len(args[1]): raise ValueError('parallel arrays')
    elif uid == MERGE:
        envelope(args, 1)
        if type(args[0]) is not list or len(args[0]) > 10000: raise ValueError('streams')
        total = 0
        for stream in args[0]:
            if type(stream) is not list: raise ValueError('stream')
            times = [parse_event(e)[0] for e in stream]
            if any(a > b for a, b in zip(times, times[1:])): raise ValueError('stream not sorted')
            total += len(stream)
        if total > 100000: raise ValueError('event budget')
    elif uid == ZERO:
        envelope(args, 1); integer(args[0], 1, 10**15)
    elif uid in (ROTF, LAYER):
        envelope(args, 1 if uid == ROTF else 2)
        array(args[0], -10**9, 10**9, 1, 100000)
        if len(set(args[0])) != len(args[0]): raise ValueError('distinct values')
        if uid == LAYER:
            array(args[1], -10**9, 10**9, 1, 100000)
            if sorted(args[0]) != sorted(args[1]): raise ValueError('desired must be a permutation of current')
    elif uid == BALLS:
        envelope(args, 2)
        if type(args[0]) is not list or not 1 <= len(args[0]) <= 100000: raise ValueError('balls')
        for b in args[0]: array(b, 0, 10**9, 2, 2)
        if len({tuple(b) for b in args[0]}) != len(args[0]): raise ValueError('distinct positions')
        integer(args[1], 0, 10**9)
    elif uid == VCONV:
        envelope(args, 2); array(args[0], 0, 1, 1, 100000); integer(args[1], 1, len(args[0]))
    elif uid == CHAIN:
        envelope(args, 1); strlist(args[0], r'(->|<-) ' + NAME, 0, 100000, 23)
        stack = []
        for t in args[0]:
            if t[:2] == '->': stack.append(t[3:])
            elif not stack or stack.pop() != t[3:]: raise ValueError('return must match the top of the call chain')
    elif uid in (MUSIC1, MUSIC2, MUSIC3):
        ops, rows = trace(uid, args, 20001)
        songs, removed, users = 0, set(), set()
        for op, row in zip(ops[1:], rows[1:]):
            if op == 'addSong': text(row[0], r'[A-Za-z0-9 ]{1,30}', 30); songs += 1
            elif op == 'playSong':
                integer(row[0], 1, max(songs, 1)); integer(row[1], 1, 10**9); users.add(row[1])
                if songs == 0: raise ValueError('play needs an existing song')
            elif op == 'getLastThreeSongs': integer(row[0], 1, 10**9)
            elif op == 'removeSong': integer(row[0], 1, 10**9)
        if songs > 2000: raise ValueError('song budget')
    elif uid in (NGRAM1, NGRAM2):
        envelope(args, 2)
        text(args[0], WORD + r'( ' + WORD + r')*', 1100000)
        if args[0].count(' ') >= 100000: raise ValueError('word budget')
        strlist(args[1], WORD + r'( ' + WORD + r'){1,4}' if uid == NGRAM2 else WORD + ' ' + WORD, 0, 10000, 60)
    elif uid in (PARTY1, PARTY2):
        envelope(args, 2); party_rows(*args)
    elif uid == PAINT:
        envelope(args, 2); integer(args[0], 1, 10**9); integer(args[1], 1, 10**9)
    elif uid == PHONE:
        envelope(args, 2); strlist(args[0], r'[a-z]{1,20}', 0, 10000, 20); text(args[1], r'[0-9]{1,20}', 20)
    elif uid in (POKER1, POKER2):
        envelope(args, 1)
        hands = [args[0]] if uid == POKER1 else args[0]
        if type(hands) is not list or not 1 <= len(hands) <= 10: raise ValueError('hands')
        cards = []
        for hand in hands:
            if type(hand) is not list or len(hand) != 5: raise ValueError('hand size')
            cards += [parse_card(c) for c in hand]
        if len(set(cards)) != len(cards): raise ValueError('cards come from one deck')
    elif uid == PRODMM:
        envelope(args, 2)
        strlist(args[0], r'push|pop', 1, 100000, 4); array(args[1], -10**7, 10**7, 1, 100000)
        if len(args[0]) != len(args[1]): raise ValueError('parallel arrays')
        bag = {}
        for op, v in zip(*args):
            bag[v] = bag.get(v, 0) + (1 if op == 'push' else -1)
            if bag[v] < 0: raise ValueError('pop of absent value')
            if bag[v] == 0: del bag[v]
            if not bag: raise ValueError('multiset must stay non-empty')
    elif uid == PURCH:
        envelope(args, 3)
        array(args[0], 1, 10**9, 1, 100000); array(args[1], 1, len(args[0]), 0, 100000); array(args[2], 0, 10**15, 0, 100000)
        if len(args[1]) != len(args[2]): raise ValueError('parallel queries')
        if any(a > b for a, b in zip(args[0], args[0][1:])): raise ValueError('prices non-decreasing')


# ---------------------------------------------------------------- references


def ref_maxt(tp, cost, budget):
    """Exhaustive enumeration of every upgrade-count vector within budget (small inputs only)."""
    if len(tp) > 4 or budget > 40: raise ValueError('reference budget')
    best = 0
    for xs in product(*[range(budget // c + 1) for c in cost]):
        if sum(x * c for x, c in zip(xs, cost)) <= budget: best = max(best, min(t * (1 + x) for t, x in zip(tp, xs)))
    return best


def ref_merge(streams):
    events = sorted((parse_event(e) for s in streams for e in s), key=lambda p: p[0])
    out, price, i = [], 0, 0
    while i < len(events):
        j = i
        while j < len(events) and events[j][0] == events[i][0]: price += events[j][1]; j += 1
        out.append(f'{events[i][0]}, {price}'); i = j
    return out


def ref_zero(n):
    """Memoised recurrence: halving an even number is never worse; an odd number steps to a neighbour."""
    @lru_cache(None)
    def f(m):
        if m <= 1: return m
        if m % 2 == 0: return 1 + f(m // 2)
        return 1 + min(f(m - 1), f(m + 1))
    return f(n)


def bfs_zero(n):
    """Plain BFS over integers 0..2n+2 with all three moves (cross-check for the recurrence)."""
    limit, dist, q = 2 * n + 2, {n: 0}, deque([n])
    while q:
        m = q.popleft()
        if m == 0: return dist[m]
        for nxt in (m - 1, m + 1) + ((m // 2,) if m % 2 == 0 else ()):
            if 0 <= nxt <= limit and nxt not in dist: dist[nxt] = dist[m] + 1; q.append(nxt)


def ref_rotf(arr):
    """BFS over whole array tuples (small n only)."""
    if len(arr) > 9: raise ValueError('reference budget')
    start, goal = tuple(arr), tuple(sorted(arr))
    dist, q = {start: 0}, deque([start])
    while q:
        s = q.popleft()
        if s == goal: return dist[s]
        for nxt in (s[1:] + s[:1], s[::-1]):
            if nxt not in dist: dist[nxt] = dist[s] + 1; q.append(nxt)
    return -1


def ref_layer(cur, want):
    """BFS over whole permutations with the remove-last-and-insert move (small n only)."""
    if len(cur) > 7: raise ValueError('reference budget')
    start, goal = tuple(cur), tuple(want)
    dist, q = {start: 0}, deque([start])
    while q:
        s = q.popleft()
        if s == goal: return dist[s]
        rest, last = s[:-1], s[-1]
        for i in range(len(s)):
            nxt = rest[:i] + (last,) + rest[i:]
            if nxt not in dist: dist[nxt] = dist[s] + 1; q.append(nxt)


def ref_balls(balls, d):
    """Quadratic adjacency plus DFS component count."""
    if len(balls) > 400: raise ValueError('reference budget')
    n, seen, comps = len(balls), [False] * len(balls), 0
    for s in range(n):
        if seen[s]: continue
        comps += 1; seen[s] = True; stack = [s]
        while stack:
            a = stack.pop()
            for b in range(n):
                if not seen[b]:
                    (x1, y1), (x2, y2) = balls[a], balls[b]
                    if (x1 == x2 and abs(y1 - y2) <= d) or (y1 == y2 and abs(x1 - x2) <= d): seen[b] = True; stack.append(b)
    return comps


def ref_vconv(a, k):
    """Exact minimum over every removal order and window choice (memoised over remaining-ones sets)."""
    ones = tuple(i for i, v in enumerate(a) if v)
    if len(ones) > 12: raise ValueError('reference budget')
    n = len(a)

    @lru_cache(None)
    def f(mask):
        if mask == 0: return 0
        best = None
        for b, p in enumerate(ones):
            if mask >> b & 1:
                for left in range(max(0, p - k + 1), min(p, n - k) + 1):
                    cost = sum(1 for c, q in enumerate(ones) if mask >> c & 1 and left <= q < left + k)
                    v = cost + f(mask & ~(1 << b))
                    if best is None or v < best: best = v
        return best
    return f((1 << len(ones)) - 1)


def ref_chain(traces):
    stack, count, first = [], {}, {}
    for i, t in enumerate(traces):
        if t[:2] == '->':
            stack.append(t[3:]); key = tuple(stack)
            count[key] = count.get(key, 0) + 1; first.setdefault(key, i)
        else: stack.pop()
    if not count: return []
    return list(min(count, key=lambda c: (-count[c], first[c])))


def ref_music(uid, ops, rows):
    """Literal replay: keeps the raw play log and recomputes everything per query."""
    level = (MUSIC1, MUSIC2, MUSIC3).index(uid) + 1
    titles, removed, plays, out = [], set(), [], [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'addSong': titles.append(row[0]); out.append(len(titles))
        elif op == 'playSong':
            if row[0] not in removed: plays.append((row[0], row[1]))
            out.append(None)
        elif op == 'getAnalytics':
            live = [i for i in range(1, len(titles) + 1) if i not in removed]
            users = {i: len({u for s, u in plays if s == i}) for i in live}
            out.append([[titles[i - 1], users[i]] for i in sorted(live, key=lambda i: (-users[i], i))])
        elif op == 'getLastThreeSongs':
            seen = []
            for s, u in reversed(plays):
                if u == row[0] and s not in removed and s not in seen: seen.append(s)
            out.append(seen[:3])
        else:
            ok = 1 <= row[0] <= len(titles) and row[0] not in removed
            if ok: removed.add(row[0])
            out.append(ok)
    assert level >= 1
    return out


def ref_ngram(uid, textv, entries):
    words = textv.split(' ')
    grams = [e.split(' ') for e in entries]
    out, i = [], 0
    while i < len(words):
        best = 1
        for g in grams:
            if (uid == NGRAM2 or len(g) == 2) and len(g) > best and words[i:i + len(g)] == g: best = len(g)
        out.append(' '.join(words[i:i + best])); i += best
    return out


def ref_party(uid, windows, geo):
    span, place = party_rows(windows, geo)
    if len(windows) > 3000: raise ValueError('reference budget')
    by = {}
    for pid, hood in place.items(): by.setdefault(hood, []).append(span[pid])
    out = []
    for hood in sorted(by):
        iv = by[hood]
        if uid == PARTY1:
            merged = [list(x) for x in iv]
            changed = True
            while changed:  # repeated pairwise merging until a fixpoint
                changed = False
                for a in range(len(merged)):
                    for b in range(a + 1, len(merged)):
                        if merged[a][0] <= merged[b][1] and merged[b][0] <= merged[a][1]:
                            merged[a] = [min(merged[a][0], merged[b][0]), max(merged[a][1], merged[b][1])]
                            del merged[b]; changed = True; break
                    if changed: break
            out += [[hood, str(s), str(e)] for s, e in sorted(merged)]
        else:
            out.append([hood, max(sum(1 for s, e in iv if s <= t < e) for t, _ in iv)])
    return out


def ref_paint(k, n):
    if n <= 6 and k ** n <= 50000:
        return sum(1 for seq in product(range(k), repeat=n) if all(a != b for a, b in zip(seq, seq[1:]))) % MOD
    if n > 200000: raise ValueError('reference budget')
    ways = k % MOD
    for _ in range(n - 1): ways = ways * (k - 1) % MOD  # DP: each next slot avoids the previous process
    return ways


KEYPAD = ['', '', 'abc', 'def', 'ghi', 'jkl', 'mno', 'pqrs', 'tuv', 'wxyz']


def ref_phone(words, number):
    def ok(w):
        if len(w) != len(number): return False
        for ch, dg in zip(w, number):
            if dg == '0':
                if ch != ' ': return False
            elif ch not in KEYPAD[int(dg)]: return False
        return True
    return [w for w in words if ok(w)]


def poker_key(hand):
    """Reference hand strength via explicit pattern predicates, then kickers."""
    cards = [parse_card(c) for c in hand]
    vals = sorted((RANKS.index(r) + 2 for r, _ in cards), reverse=True)
    flush = len({s for _, s in cards}) == 1
    distinct = sorted(set(vals), reverse=True)
    straight_high = 0
    if len(distinct) == 5 and distinct[0] - distinct[4] == 4: straight_high = distinct[0]
    if distinct == [14, 5, 4, 3, 2]: straight_high = 5
    groups = {}
    for v in vals: groups[v] = groups.get(v, 0) + 1
    by_size = lambda size: sorted((v for v, c in groups.items() if c == size), reverse=True)
    if straight_high and flush: return (8, straight_high)
    if by_size(4): return (7, by_size(4)[0], by_size(1)[0])
    if by_size(3) and by_size(2): return (6, by_size(3)[0], by_size(2)[0])
    if flush: return (5, *vals)
    if straight_high: return (4, straight_high)
    if by_size(3): return (3, by_size(3)[0], *by_size(1))
    if len(by_size(2)) == 2: return (2, *by_size(2), by_size(1)[0])
    if by_size(2): return (1, by_size(2)[0], *by_size(1))
    return (0, *vals)


def ref_poker(uid, arg):
    if uid == POKER1: return poker_key(arg)[0] > 0
    keys = [poker_key(h) for h in arg]
    return [i for i, k in enumerate(keys) if all(k >= other for other in keys)]


def ref_prodmm(ops, xs):
    if len(ops) > 5000: raise ValueError('reference budget')
    bag, out = {}, []
    for op, v in zip(ops, xs):
        bag[v] = bag.get(v, 0) + (1 if op == 'push' else -1)
        if bag[v] == 0: del bag[v]
        out.append(max(bag) * min(bag))
    return out


def ref_purch(prices, pos, amount):
    if len(prices) * len(pos) > 2000000: raise ValueError('reference budget')
    out = []
    for p, budget in zip(pos, amount):
        spent = count = 0
        for price in prices[p - 1:]:
            if spent + price > budget: break
            spent += price; count += 1
        out.append(count)
    return out


def reference(uid, args):
    validate_domain(uid, args)
    if uid == MAXT: return ref_maxt(*args)
    if uid == MERGE: return ref_merge(args[0])
    if uid == ZERO: return ref_zero(args[0])
    if uid == ROTF: return ref_rotf(args[0])
    if uid == LAYER: return ref_layer(*args)
    if uid == BALLS: return ref_balls(*args)
    if uid == VCONV: return ref_vconv(*args)
    if uid == CHAIN: return ref_chain(args[0])
    if uid in (MUSIC1, MUSIC2, MUSIC3): return ref_music(uid, *args)
    if uid in (NGRAM1, NGRAM2):
        if len(args[0]) * (len(args[1]) + 1) > 4000000: raise ValueError('reference budget')
        return ref_ngram(uid, *args)
    if uid in (PARTY1, PARTY2): return ref_party(uid, *args)
    if uid == PAINT: return ref_paint(*args)
    if uid == PHONE: return ref_phone(*args)
    if uid in (POKER1, POKER2): return ref_poker(uid, args[0])
    if uid == PRODMM: return ref_prodmm(*args)
    return ref_purch(*args)
