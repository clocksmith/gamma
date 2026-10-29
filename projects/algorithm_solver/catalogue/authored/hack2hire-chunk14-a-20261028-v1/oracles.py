"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (prefix dynamic
programming, nested list scans, per-cell timestamp scans, position-by-position token comparison,
cell-by-cell path comparison, lexicographic permutation enumeration, day-by-day calendar walks with
exact fractions, subset enumeration, linear membership checks, split-and-slice, regular-expression
substitution, explicit character loops, space-by-space justification, full sorts and full recounts)
and refuse inputs above a small budget.
"""
import calendar
import datetime
from fractions import Fraction
from itertools import permutations
import re

H = 'hack2hire:'
STL = H + '68757267ab23078e4e46aa3c'
STM1 = H + '67eb34914c9bb801bfd0ef7d'
STM2 = H + '67eb3ff94c9bb801bfd0ef7e'
SMR = H + '69cd7029ff3ebde766cee760'
SST1 = H + '6a5019e9665efda9311f5903'
SST2 = H + '6a501a01665efda9311f5906'
SMM = H + '6a14eb4e7b0582b35278812d'
SRO = H + '6887e0fc6509c24ee64e4b21'
SBS = H + '68c331ec1f64f4312b0a3e2d'
SUB = H + '68e870c780f69c7a0170688c'
TGC = H + '696a84b7cc483345efb1b23c'
TNL = H + '677c6cdc5cbaff553b53b06c'
TSF = H + '69d18cb017b72775cc49c0c4'
TBF1 = H + '68d56825569e57bd10bbd432'
TBF2 = H + '68d5a07e569e57bd10bbd44d'
TBF3 = H + '68d5a07f569e57bd10bbd44e'
TTW1 = H + '68bad7afb5314dcd938cb9fe'
TTW2 = H + '68bad975b5314dcd938cb9ff'
TKB = H + '686751b9a2d59460201f2cdb'
TKL = H + '6a4813cd3588ba8acc69302a'
TKP = H + '681d10c6cc14e2629f006012'

IDS = (STL, STM1, STM2, SMR, SST1, SST2, SMM, SRO, SBS, SUB, TGC, TNL, TSF, TBF1, TBF2, TBF3, TTW1, TTW2, TKB, TKL, TKP)
STM = (STM1, STM2)
SST = (SST1, SST2)
TBF = (TBF1, TBF2, TBF3)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    TTW2: ('WordFrequencyTracker', 0, {'addText': 1, 'getTop10': 0}, ('addText',)),
    TKB: ('BookSalesTracker', 0, {'recordSale': 2, 'getTopK': 1}, ('recordSale',)),
    TKP: ('PinManager', 0, {'addPin': 3, 'getTopK': 2}, ('addPin',)),
}


# ---------------------------------------------------------------- domain helpers
def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def sized(a, minimum, maximum):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')


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
    return list(zip(ops[1:], rows[1:]))


PRINTABLE = r'[ -~]*'
TRADE = r' {0,3}[A-Z]{1,4},[BS],[0-9]{4},[A-Z0-9]{6}'


def trade_list(a):
    sized(a, 0, 50000)
    for t in a:
        if type(t) is not str or len(t) != 18: raise ValueError('trade width')
        text(t, TRADE, 18)


def stl_domain(s, width):
    text(s, PRINTABLE, 200000)
    if not s.strip(' '): raise ValueError('no word')
    integer(width, 1, 200000)


def smr_domain(codes, records):
    sized(codes, 0, 20)
    for c in codes: text(c, r'[A-Z]{1,5}', 5)
    if len(set(codes)) != len(codes): raise ValueError('duplicate code')
    sized(records, 0, 50000)
    for r in records:
        sized(r, 3, 3); integer(r[0], 0, 10**9); text(r[1], r'[A-Z]{1,5}', 5); integer(r[2], -10**9, 10**9)


def sst_domain(uid, stream):
    sized(stream, 0, 50000); total = 0
    for c in stream:
        text(c, PRINTABLE, 200000); total += len(c)
    if total > 200000: raise ValueError('total length')
    if uid == SST1:
        joined = ''.join(stream); p = joined.find('<END>')
        if p >= 0:
            start = 0
            for c in stream:
                if start <= p < start + len(c):
                    if p + 5 > start + len(c): raise ValueError('token spans chunks')
                    break
                start += len(c)


def smm_domain(matrix, s):
    sized(matrix, 1, 100000)
    width = None
    for row in matrix:
        text(row, r'[a-z]+', 100000)
        if width is None: width = len(row)
        elif len(row) != width: raise ValueError('ragged matrix')
    if len(matrix) * width > 100000: raise ValueError('matrix size')
    text(s, r'[a-z]{1,100}', 100)


def sbs_domain(plans, events):
    sized(plans, 3, 3); names = set()
    for p in plans:
        sized(p, 2, 2); text(p[0], r'[A-Za-z]{1,10}', 10); integer(p[1], 1, 10**6); names.add(p[0])
    if len(names) != 3: raise ValueError('plan names')
    sized(events, 0, 366); active = None; last = None; year = None
    for e in events:
        sized(e, 3, 3); text(e[0], r'(19[0-9]{2}|20[0-9]{2}|2100)-[0-9]{2}-[0-9]{2}', 10)
        try: d = datetime.date(int(e[0][:4]), int(e[0][5:7]), int(e[0][8:]))
        except ValueError: raise ValueError('calendar date') from None
        if year is None: year = d.year
        if d.year != year or (last is not None and d <= last): raise ValueError('chronology')
        last = d
        if e[1] == 'START':
            if active is not None or e[2] not in names: raise ValueError('start')
            active = e[2]
        elif e[1] == 'SWITCH':
            if active is None or e[2] not in names or e[2] == active: raise ValueError('switch')
            active = e[2]
        elif e[1] == 'END':
            if active is None or e[2] is not None: raise ValueError('end')
            active = None
        else: raise ValueError('event type')


def sub_domain(nums, target):
    sized(nums, 0, 200)
    for v in nums: integer(v, 1, 10000)
    integer(target, 0, 100000)


TAG = r'[a-z0-9_-]{1,20}'


def tgc_domain(groups, flt):
    sized(groups, 0, 10000); total = 0
    for g in groups:
        sized(g, 0, 100000); total += len(g)
        if total > 100000: raise ValueError('tag budget')
        for t in g: text(t, TAG, 20)
    sized(flt, 0, 50)
    for t in flt: text(t, TAG, 20)
    if len(set(flt)) != len(flt): raise ValueError('duplicate filter tag')


def tnl_domain(s, n):
    text(s, r'[ -~\n]*', 200000); integer(n, 0, 100000)


NAME = r'[A-Za-z_][A-Za-z0-9_]*'
EXPR = re.compile(r'\{(' + NAME + r')\}|\{(' + NAME + r'), plural, one\{([^{}]*)\} other\{([^{}]*)\}\}')


def tsf_domain(s, keys, values):
    text(s, PRINTABLE, 100000)
    sized(keys, 0, 1000); sized(values, len(keys), len(keys))
    for k in keys: text(k, NAME, 20)
    for v in values: text(v, r'[ -z|~]*', 20)
    if len(set(keys)) != len(keys): raise ValueError('duplicate key')
    if re.sub(r'[{}]', '', EXPR.sub('', s)) != EXPR.sub('', s): raise ValueError('stray brace')
    lookup = dict(zip(keys, values))
    for m in EXPR.finditer(s):
        if m.group(2) is not None and m.group(2) in lookup and re.fullmatch(r'0|[1-9][0-9]{0,6}', lookup[m.group(2)]) is None:
            raise ValueError('plural value')
        if m.group(2) is not None and m.group(2) in lookup and int(lookup[m.group(2)]) > 10**6: raise ValueError('plural value')


def tbf_domain(uid, sentences, width=None):
    sized(sentences, 1, 1000)
    for s in sentences:
        if uid == TBF1: text(s, r'[ -~]{1,100}', 100)
        else: text(s, r'[!-~]+( [!-~]+)*', 100)
    if uid != TBF1:
        integer(width, 1, 100)
        if uid == TBF3 and any(len(w) > width for s in sentences for w in s.split(' ')): raise ValueError('word wider than box')


def ttw_text(s): text(s, r'[ -~\n]*', 200000)


def ttw2_domain(args):
    calls = trace(TTW2, args, 20001); total = 0
    for op, row in calls:
        if op == 'addText': ttw_text(row[0]); total += len(row[0])
    if total > 200000: raise ValueError('text budget')
    return calls


def tkb_domain(args):
    calls = trace(TKB, args, 20001)
    for op, row in calls:
        if op == 'recordSale': text(row[0], r'[A-Za-z0-9]{1,10}', 10); integer(row[1], 1, 10000)
        else: integer(row[0], 0, 10000)
    return calls


def tkp_domain(args):
    calls = trace(TKP, args, 20001); ids = set()
    for op, row in calls:
        if op == 'addPin':
            integer(row[0], 0, 10**9); integer(row[1], -10**9, 10**9); text(row[2], r'[a-z]{1,10}', 10)
            if row[0] in ids: raise ValueError('duplicate pin id')
            ids.add(row[0])
        else: text(row[0], r'[a-z]{1,10}', 10); integer(row[1], 0, 10000)
    return calls


def validate_domain(uid, args):
    if uid == STL: envelope(args, 2); stl_domain(*args)
    elif uid in STM: envelope(args, 2); trade_list(args[0]); trade_list(args[1])
    elif uid == SMR: envelope(args, 2); smr_domain(*args)
    elif uid in SST: envelope(args, 1); sst_domain(uid, args[0])
    elif uid == SMM: envelope(args, 2); smm_domain(*args)
    elif uid == SRO: envelope(args, 1); text(args[0], r'[a-z]{1,100000}', 100000)
    elif uid == SBS: envelope(args, 2); sbs_domain(*args)
    elif uid == SUB: envelope(args, 2); sub_domain(*args)
    elif uid == TGC: envelope(args, 2); tgc_domain(*args)
    elif uid == TNL: envelope(args, 2); tnl_domain(*args)
    elif uid == TSF: envelope(args, 3); tsf_domain(*args)
    elif uid == TBF1: envelope(args, 1); tbf_domain(uid, args[0])
    elif uid in TBF: envelope(args, 2); tbf_domain(uid, *args)
    elif uid == TTW1: envelope(args, 1); ttw_text(args[0])
    elif uid == TTW2: ttw2_domain(args)
    elif uid == TKB: tkb_domain(args)
    elif uid == TKL:
        envelope(args, 2); sized(args[0], 0, 100000)
        for v in args[0]: integer(v, -10**9, 10**9)
        integer(args[1], 0, len(args[0]))
    elif uid == TKP: tkp_domain(args)
    else: raise ValueError('unknown uid')


# ---------------------------------------------------------------- references
def ref_stl(s, width):
    words = s.split()
    best = [0] + [None] * len(words)
    for i in range(1, len(words) + 1):
        for j in range(i):
            seg = words[j:i]
            length = sum(map(len, seg)) + len(seg) - 1
            if len(seg) == 1 or length <= width:
                if best[j] is not None and (best[i] is None or best[j] + 1 < best[i]): best[i] = best[j] + 1
    return best[len(words)]


def first_unused(pool, used, pred):
    for i, x in enumerate(pool):
        if not used[i] and pred(x): return i
    return -1


def ref_stm(uid, house, street):
    hu, su = [False] * len(house), [False] * len(street)
    for i, t in enumerate(house):
        j = first_unused(street, su, lambda x, t=t: x == t)
        if j >= 0: hu[i] = su[j] = True
    if uid == STM2:
        order_h = sorted(range(len(house)), key=lambda i: house[i])
        for i in order_h:
            if hu[i]: continue
            key = house[i][:12]
            cands = sorted((street[j], j) for j in range(len(street)) if not su[j] and street[j][:12] == key)
            if cands: hu[i] = su[cands[0][1]] = True
    return sorted([house[i] for i in range(len(house)) if not hu[i]] + [street[j] for j in range(len(street)) if not su[j]])


def ref_smr(codes, records):
    cols = sorted(codes)
    times = sorted({r[0] for r in records if r[1] in cols})
    out = []
    for t in times:
        row = [t]
        for c in cols:
            best = None
            for idx, r in enumerate(records):
                if r[1] == c and r[0] <= t and (best is None or (r[0], idx) > best[0]): best = ((r[0], idx), r[2])
            row.append(None if best is None else best[1])
        out.append(row)
    return out


def ref_sst(stream):
    joined = ''
    for c in stream: joined += c
    pos = -1
    for p in range(len(joined) - 4):
        if joined[p] == '<' and joined[p + 1] == 'E' and joined[p + 2] == 'N' and joined[p + 3] == 'D' and joined[p + 4] == '>':
            pos = p; break
    if pos < 0: return list(stream)
    # chunk k is the one with start_k <= pos < start_k + len_k (empty chunks never hold a position)
    out, start = [], 0
    for c in stream:
        if start <= pos < start + len(c):
            if pos > start: out.append(c[:pos - start])
            return out
        out.append(c); start += len(c)
    raise AssertionError('token position not found')


def ref_smm(matrix, s):
    m, n, count = len(matrix), len(matrix[0]), 0
    for r in range(m):
        for c in range(n):
            for dr, dc in ((0, 1), (1, 0), (1, 1)):
                ok = True
                for i, ch in enumerate(s):
                    rr, cc = r + i * dr, c + i * dc
                    if not (0 <= rr < m and 0 <= cc < n) or matrix[rr][cc] != ch: ok = False; break
                if ok: count += 1
    return count


def ref_sro(s):
    for p in permutations(sorted(s)):
        if all(p[i] != p[i + 1] for i in range(len(p) - 1)): return ''.join(p)
    return ''


def ref_sbs(plans, events):
    if not events: return []
    price = dict(map(tuple, plans))
    year = int(events[0][0][:4])
    changes = {datetime.date.fromisoformat(e[0]): e for e in events}
    totals = {}
    active = None
    day = datetime.date(year, 1, 1)
    while day.year == year:
        if day in changes:
            e = changes[day]; active = e[2] if e[1] != 'END' else None
        if active is not None:
            key = (day.month,)
            totals[key] = totals.get(key, Fraction(0)) + Fraction(price[active], calendar.monthrange(year, day.month)[1])
        day += datetime.timedelta(days=1)
    out = []
    for (month,), amount in sorted(totals.items()):
        floor = amount.numerator // amount.denominator
        cents = floor + (1 if amount - floor >= Fraction(1, 2) else 0)
        out.append(['%04d-%02d' % (year, month), cents])
    return out


def ref_sub(nums, target):
    n = len(nums)
    for mask in range(1 << n):
        if sum(nums[i] for i in range(n) if mask >> i & 1) == target: return True
    return False


def ref_tgc(groups, flt):
    out = []
    for g in groups:
        if all(any(t == x for x in g) for t in flt):
            for t in g:
                if not any(t == f for f in flt) and not any(t == o for o in out): out.append(t)
    return sorted(out)


def ref_tnl(s, n):
    lines = s.splitlines(keepends=True)
    return ''.join(lines[max(0, len(lines) - n):]) if n else ''


def ref_tsf(s, keys, values):
    lookup = dict(zip(keys, values))

    def sub(m):
        if m.group(1) is not None:
            return lookup[m.group(1)] if m.group(1) in lookup else m.group(0)
        if m.group(2) not in lookup: return m.group(0)
        v = lookup[m.group(2)]
        return (m.group(3) if v == '1' else m.group(4)).replace('#', v)
    return EXPR.sub(sub, s)


def wrap_ref(sentence, width):
    words, lines = sentence.split(' '), []
    while words:
        take = 1
        for t in range(1, len(words) + 1):
            if len(' '.join(words[:t])) <= width: take = t
        lines.append(words[:take]); words = words[take:]
    return lines


def pad_ref(line, width):
    out = line
    while len(out) < width: out = out + ' '
    return out


def boxes_ref(blocks, width):
    border = '+'
    for _ in range(width): border += '-'
    border += '+'
    out = []
    for block in blocks:
        out.append(border)
        for line in block: out.append('|' + pad_ref(line, width) + '|')
        out.append(border)
    return out


def justify_ref(words, width):
    if len(words) == 1: return pad_ref(words[0], width)
    gaps = [1] * (len(words) - 1)
    while sum(map(len, words)) + sum(gaps) < width:
        smallest = min(gaps); gaps[gaps.index(smallest)] += 1
    out = words[0]
    for g, w in zip(gaps, words[1:]): out += ' ' * g + w
    return out


def ref_tbf(uid, sentences, width=None):
    if uid == TBF1:
        w = 0
        for s in sentences:
            if all(len(s) >= len(t) for t in sentences): w = len(s)
        return boxes_ref([[s] for s in sentences], w)
    wrapped = [wrap_ref(s, width) for s in sentences]
    if uid == TBF2:
        blocks = [[' '.join(line) for line in lines] for lines in wrapped]
        return boxes_ref(blocks, max(len(line) for b in blocks for line in b))
    blocks = [[justify_ref(line, width) if i < len(lines) - 1 else ' '.join(line) for i, line in enumerate(lines)] for lines in wrapped]
    return boxes_ref(blocks, width)


def words_ref(s): return [w.lower() for w in re.findall(r'[A-Za-z]+', s)]


def top10_ref(words):
    counts = {}
    for w in words: counts[w] = counts.get(w, 0) + 1
    return [[w, c] for w, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]]


def ref_ttw2(calls):
    texts, out = [], [None]
    for op, row in calls:
        if op == 'addText': texts.append(row[0]); out.append(None)
        else: out.append(top10_ref([w for t in texts for w in words_ref(t)]))
    return out


def ref_tkb(calls):
    totals, out = {}, [None]
    for op, row in calls:
        if op == 'recordSale': totals[row[0]] = totals.get(row[0], 0) + row[1]; out.append(None)
        else: out.append([b for b, _ in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))][:row[0]])
    return out


def ref_tkp(calls):
    pins, out = [], [None]
    for op, row in calls:
        if op == 'addPin': pins.append(tuple(row)); out.append(None)
        else: out.append([p[0] for p in sorted((p for p in pins if p[2] == row[0]), key=lambda p: (-p[1], p[0]))][:row[1]])
    return out


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid == STL:
        budget(len(args[0].split()) <= 60); return ref_stl(*args)
    if uid in STM:
        budget(len(args[0]) * len(args[1]) <= 4000); return ref_stm(uid, *args)
    if uid == SMR:
        budget(len(args[1]) ** 2 * max(1, len(args[0])) <= 200000); return ref_smr(*args)
    if uid in SST:
        budget(sum(map(len, args[0])) <= 3000); return ref_sst(args[0])
    if uid == SMM:
        budget(len(args[0]) * len(args[0][0]) * len(args[1]) <= 20000); return ref_smm(*args)
    if uid == SRO:
        budget(len(args[0]) <= 8); return ref_sro(args[0])
    if uid == SBS: return ref_sbs(*args)
    if uid == SUB:
        budget(len(args[0]) <= 14); return ref_sub(*args)
    if uid == TGC:
        budget(sum(map(len, args[0])) <= 400); return ref_tgc(*args)
    if uid == TNL:
        budget(len(args[0]) <= 5000); return ref_tnl(*args)
    if uid == TSF:
        budget(len(args[0]) <= 5000); return ref_tsf(*args)
    if uid in TBF:
        budget(sum(map(len, args[0])) <= 3000); return ref_tbf(uid, *args)
    if uid == TTW1:
        budget(len(args[0]) <= 5000); return top10_ref(words_ref(args[0]))
    if uid == TKL:
        budget(len(args[0]) <= 2000); return sorted(args[0], reverse=True)[:args[1]]
    calls = trace(uid, args, 20001)
    budget(len(calls) <= 400)
    if uid == TTW2: return ref_ttw2(calls)
    if uid == TKB: return ref_tkb(calls)
    return ref_tkp(calls)
