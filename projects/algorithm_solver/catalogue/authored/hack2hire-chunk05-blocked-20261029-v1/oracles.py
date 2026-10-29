"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). hack2hire-chunk05-v1 had blocked all nine
variants because the previews stop before the deciding rules; most rules below are invented and carry
"very high" uncertainty. None is the official specification.
References deliberately use different, simpler algorithms than the candidates (all-pairs running sums,
minute-by-minute pay simulation, full rescans of stored readings, round replay from scratch, breaker
history replay and per-word token comparison) and refuse inputs above a small budget.
"""
import re

H = 'hack2hire:'
CSS = H + '68f82cd8d7ff180d0ab950c7'
DP1 = H + '678472f60e1dbb6a09385781'
DP2 = H + '678478d50e1dbb6a09385782'
DP3 = H + '6784b4640e1dbb6a09385784'
ALS = H + '6a14a84c7b0582b352787d44'
CG1 = H + '67842117d0faf7ec64cc3add'
CG2 = H + '6784211bd0faf7ec64cc3ade'
DCB = H + '694609632c048134ada83559'
DAW = H + '688bd5423867670cfb894188'

IDS = (CSS, DP1, DP2, DP3, ALS, CG1, CG2, DCB, DAW)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    ALS: ('ALSWrapper', 0, {'record': 3, 'getLatestLux': 0, 'getAverageLux': 2}, ('record',)),
    CG1: ('CardGame', 1, {'playRound': 0, 'getScore': 1, 'getWinner': 0}, ()),
    CG2: ('CardGame', 1, {'playRound': 0, 'getScore': 1, 'getWinner': 0}, ()),
    DCB: ('DualCircuitBreaker', 2, {'request': 3}, ()),
}
DASHER = {DP1: 1, DP2: 2, DP3: 3}
SYMBOLS = '0123456789@$!|+#%&*?'
PEAKS = ((660, 840), (1020, 1200))  # inferred peak windows [11:00, 14:00) and [17:00, 20:00)


# ---------------------------------------------------------------- domain helpers
def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def sized(a, minimum, maximum):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')


def intlist(a, lo, hi, minimum=0, maximum=100000):
    sized(a, minimum, maximum)
    for v in a: integer(v, lo, hi)


def trace(uid, args, maximum=100001):
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


def minute(hhmm):
    return int(hhmm[:2]) * 60 + int(hhmm[3:])


def dasher_domain(uid, activities):
    events = ('accepted', 'delivered', 'cancelled') if DASHER[uid] == 3 else ('accepted', 'delivered')
    sized(activities, 0, 20000)
    state, last = {}, ''
    for row in activities:
        if type(row) is not list or len(row) != 3: raise ValueError('activity row')
        t, order, event = row
        text(t, r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', 5); text(order, r'[A-Za-z0-9]{1,10}', 10)
        if type(event) is not str or event not in events: raise ValueError('event')
        if t < last: raise ValueError('activities out of time order')
        last = t
        if event == 'accepted':
            if order in state: raise ValueError('order accepted twice')
            state[order] = 'open'
        else:
            if state.get(order) != 'open': raise ValueError('finish without open order')
            state[order] = 'done'
    if 'open' in state.values(): raise ValueError('unfinished order')


def daw_domain(words, substitutions, comment):
    sized(words, 1, 500)
    for w in words: text(w, r'[a-z]{1,20}', 20)
    if sum(len(w) for w in words) > 2000: raise ValueError('total word length')
    sized(substitutions, 0, 60)
    letters = {}
    for pair in substitutions:
        if type(pair) is not list or len(pair) != 2: raise ValueError('substitution pair')
        text(pair[0], '[' + re.escape(SYMBOLS) + ']', 1); text(pair[1], '[a-z]', 1)
        letters.setdefault(pair[0], set()).add(pair[1])
    if any(len(v) > 3 for v in letters.values()): raise ValueError('more than three letters per symbol')
    token = '[a-z' + re.escape(SYMBOLS) + ']{1,20}'
    text(comment, token + '(?: ' + token + ')*', 10000)


def validate_domain(uid, args):
    if type(uid) is not str or uid not in IDS: raise ValueError('unknown uid')
    if uid == CSS:
        envelope(args, 1); intlist(args[0], 1, 10**9, 1, 100000); return
    if uid in DASHER:
        envelope(args, 1); return dasher_domain(uid, args[0])
    if uid == DAW:
        envelope(args, 3); return daw_domain(*args)
    if uid == ALS:
        calls = trace(ALS, args, 20001)
        for op, row in calls:
            if op == 'record':
                integer(row[0], 0, 1); integer(row[1], 0, 100000); integer(row[2], 0, 10**6)
            elif op == 'getAverageLux':
                integer(row[0], 0, 10**6); integer(row[1], row[0], 10**6)
        return calls
    if uid in (CG1, CG2):
        calls = trace(uid, args, 10001)
        deck = args[1][0][0]
        intlist(deck, 0, 51, 52, 52)
        if sorted(deck) != list(range(52)): raise ValueError('deck must be a permutation of 0..51')
        for op, row in calls:
            if op == 'getScore' and (type(row[0]) is not str or row[0] not in ('A', 'B')): raise ValueError('player')
        return calls
    calls = trace(DCB, args, 100001)
    integer(args[1][0][0], 1, 100); integer(args[1][0][1], 1, 10**9)
    last = 0
    for _, row in calls:
        integer(row[0], last, 10**9); last = row[0]
        if type(row[1]) is not bool or type(row[2]) is not bool: raise ValueError('outcome flags')
    return calls


# ---------------------------------------------------------------- references
def ref_css(cap):
    total = 0
    for l in range(len(cap)):
        middle = 0
        for r in range(l + 2, len(cap)):
            middle += cap[r - 1]
            if cap[l] == cap[r] == middle: total += 1
    return total


def ref_dasher(activities, variant):
    start, end, cancelled = {}, {}, set()
    for t, order, event in activities:
        if event == 'accepted': start[order] = minute(t)
        else: end[order] = minute(t)
        if event == 'cancelled': cancelled.add(order)
    total = 0
    for m in range(1440):
        weight = 2 if variant >= 2 and any(a <= m < b for a, b in PEAKS) else 1
        active = sum(1 for o in start if o not in cancelled and start[o] <= m < end[o])
        total += 30 * weight * active
    return total


def ref_als(calls):
    readings, out = [], [None]
    for op, row in calls:
        if op == 'record':
            if row[0] == 1: readings.append((row[2], row[1]))
            out.append(None)
        elif op == 'getLatestLux':
            best = None
            for ts, lux in readings:
                if best is None or ts >= best[0]: best = (ts, lux)
            out.append(-1 if best is None else best[1])
        else:
            inside = [lux for ts, lux in readings if row[0] <= ts <= row[1]]
            out.append(sum(inside) // len(inside) if inside else -1)
    return out


def cg_scores(deck, rounds, variant):
    """Replay the first `rounds` rounds from scratch; returns (scores, last round result)."""
    score, last = {'A': 0, 'B': 0}, ''
    for i in range(rounds):
        a, b = deck[2 * i], deck[2 * i + 1]
        if variant == 1:
            last = 'A' if a > b else 'B'; score[last] += 1
        else:
            ra, rb = a % 13, b % 13
            if ra == rb: last = 'TIE'
            else: last = 'A' if ra > rb else 'B'; score[last] += ra + rb + 2
    return score, last


def ref_cg(deck, calls, variant):
    rounds, out = 0, [None]
    for op, row in calls:
        if op == 'playRound':
            if 2 * rounds + 2 > len(deck): out.append(''); continue
            rounds += 1; out.append(cg_scores(deck, rounds, variant)[1])
        elif op == 'getScore':
            out.append(cg_scores(deck, rounds, variant)[0][row[0]])
        else:
            if 2 * rounds < len(deck): out.append(''); continue
            s = cg_scores(deck, rounds, variant)[0]
            out.append('TIE' if s['A'] == s['B'] else ('A' if s['A'] > s['B'] else 'B'))
    return out


def breaker_allows(history, t, threshold, cooldown):
    """Replay one breaker's full attempt history; return whether an attempt at time t is allowed."""
    is_open, opened, run = False, 0, 0
    for at, ok in history:
        trial = is_open
        if ok: is_open, run = False, 0
        elif trial: opened = at
        else:
            run += 1
            if run >= threshold: is_open, opened, run = True, at, 0
    return not is_open or t - opened >= cooldown


def ref_dcb(threshold, cooldown, calls):
    hist, out = {'P': [], 'S': []}, [None]
    for _, (t, p_ok, s_ok) in calls:
        attempted = False
        if breaker_allows(hist['P'], t, threshold, cooldown):
            attempted = True; hist['P'].append((t, p_ok))
            if p_ok: out.append('PRIMARY'); continue
        if breaker_allows(hist['S'], t, threshold, cooldown):
            hist['S'].append((t, s_ok)); out.append('SECONDARY' if s_ok else 'FAILED'); continue
        out.append('FAILED' if attempted else 'BLOCKED')
    return out


def ref_daw(words, substitutions, comment):
    pairs = {(s, c) for s, c in substitutions}
    found = []
    for i, token in enumerate(comment.split(' ')):
        for w in words:
            if len(w) == len(token) and all(t == c if 'a' <= t <= 'z' else (t, c) in pairs for t, c in zip(token, w)):
                found.append(i); break
    return found


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid in CLASSES:
        calls = trace(uid, args)
        budget(len(calls) <= 400)
        if uid == ALS: return ref_als(calls)
        if uid == DCB: return ref_dcb(*args[1][0], calls)
        return ref_cg(args[1][0][0], calls, 1 if uid == CG1 else 2)
    if uid == CSS:
        budget(len(args[0]) <= 300); return ref_css(args[0])
    if uid in DASHER:
        budget(len(args[0]) <= 120); return ref_dasher(args[0], DASHER[uid])
    budget(len(args[2]) <= 400 and len(args[0]) <= 60); return ref_daw(*args)
