"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (per-item rescans, full
sorts, literal list and grid simulation, bitmask subset enumeration, materialised ranges, plain
backtracking, brute-force retries of every repair) and refuse inputs above a small budget.
"""
import re

H = 'hack2hire:'
PAY = H + '68b996c98c4a0a9996afdd81'
PFP = H + '6a330e686849fecc81440a3c'
PS1 = H + '67f5703f83ba2e5f057e6dfb'
PS2 = H + '67f8222b1d70a71460925c53'
PEL = H + '699f70796e73e4abccc9b539'
PQ = H + '67a2d68216a8465483dca727'
PBS = H + '68b975348c4a0a9996afdd79'
RUP1 = H + '67fa9534ba41b3368f4e5851'
RUP2 = H + '67fa954aba41b3368f4e5852'
RI = H + '678d7c57fa7ce9616e190fb5'
TELE = H + '69a3a0426e73e4abccc9c0e9'
BOT = H + '68ad7692cdaebe9459ce9a78'
RFI = H + '67a43f105141b0ac3b8be4df'
RBS1 = H + '69499ed489ec36a1b1e2c13f'
RBS2 = H + '6949a92289ec36a1b1e2c15c'
RBS3 = H + '6949b64a89ec36a1b1e2c16d'
BOOT1 = H + '6a373b356849fecc81442862'
BOOT2 = H + '6a373b366849fecc81442863'
RSD = H + '69ff8062574d87bc49006e92'
TBL = H + '69d17a8817b72775cc49bfe0'

IDS = (PAY, PFP, PS1, PS2, PEL, PQ, PBS, RUP1, RUP2, RI, TELE, BOT, RFI, RBS1, RBS2, RBS3, BOOT1, BOOT2, RSD, TBL)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    PEL: ('PriorityExpiryLRUCache', 1, {'get': 2, 'set': 5}, ('set',)),
    PBS: ('BookingSystem', 1, {'book': 2}, ()),
    RI: ('RangeIterator', 3, {'hasNext': 0, 'next': 0}, ()),
    BOT: ('DetectionSystem', 2, {'isBot': 2}, ()),
    TBL: ('Table', 2, {'selectTable': 0, 'selectRow': 1, 'selectCell': 2, 'setColor': 1, 'getColor': 2},
          ('selectTable', 'selectRow', 'selectCell', 'setColor')),
}
DIGITS = r'0|[1-9][0-9]{0,9}'
NAME20 = r'[A-Za-z0-9_]{1,20}'
NAME10 = r'[A-Za-z0-9_]{1,10}'
MAX_OPS = 100001


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def decimal(v, lo, hi):
    text(v, DIGITS, 10)
    if not lo <= int(v) <= hi: raise ValueError('decimal range')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def strlist(a, pattern, minimum=0, maximum=100000, width=100):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')
    for v in a: text(v, pattern, width)


def rows_of(a, width, maximum, minimum=0):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('row list size')
    for r in a:
        if type(r) is not list or len(r) != width: raise ValueError('row width')


def trace(uid, args, maximum=MAX_OPS):
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


def pay_domain(tx, amount):
    rows_of(tx, 6, 100000)
    integer(amount, 0, 10**14)
    ids, payments, refunds = set(), {}, []
    for r in tx:
        for v in r:
            if type(v) is not str: raise ValueError('string fields')
        text(r[0], NAME20, 20)
        if r[0] in ids: raise ValueError('unique ids')
        ids.add(r[0])
        decimal(r[4], 0, 10**9); decimal(r[5], 1, 10**9)
        if r[1] == 'PAYMENT':
            text(r[2], r'[A-Z_]{1,20}', 20)
            if r[3] != '': raise ValueError('payment has no link')
            payments[r[0]] = int(r[5])
        elif r[1] == 'REFUND':
            if r[2] != '': raise ValueError('refund has no type')
            refunds.append((r[3], int(r[5])))
        else: raise ValueError('kind')
    used = {}
    for link, x in refunds:
        if link not in payments: raise ValueError('refund links a payment')
        used[link] = used.get(link, 0) + x
        if used[link] > payments[link]: raise ValueError('over-refunded payment')


NAME_WORDS = r'[A-Za-z0-9]{1,15}(?: [A-Za-z0-9]{1,15}){0,9}'
NAME_WORDS2 = r'[A-Za-z0-9]{1,12}(?: [A-Za-z0-9]{1,12}){0,4}'


def pel_domain(args):
    ops, rows = trace(PEL, args)
    integer(rows[0][0], 1, 100000)
    last = 0
    for op, row in zip(ops[1:], rows[1:]):
        text(row[0], r'[a-z0-9]{1,10}', 10)
        if op == 'set':
            integer(row[1], 0, 10**9); integer(row[2], 0, 10**9); integer(row[3], 0, 2 * 10**9)
        integer(row[-1], 0, 2 * 10**9)
        if row[-1] < last: raise ValueError('time decreases')
        last = row[-1]


def pbs_domain(args):
    ops, rows = trace(PBS, args, 301)
    props = rows[0][0]
    rows_of(props, 3, 300)
    ids, per = set(), {}
    for pid, nb, cap in props:
        text(pid, NAME10, 10); text(nb, NAME10, 10); decimal(cap, 1, 1000)
        if pid in ids: raise ValueError('unique ids')
        ids.add(pid); per[nb] = per.get(nb, 0) + 1
        if per[nb] > 12: raise ValueError('neighborhood size')
    for row in rows[1:]:
        text(row[0], NAME10, 10); integer(row[1], 1, 20000)


def range_length(start, end, step):
    if step > 0: return max(0, (end - start + step - 1) // step)
    return max(0, (start - end - step - 1) // -step)


def ri_domain(args):
    ops, rows = trace(RI, args)
    start, end, step = rows[0]
    integer(start, -10**9, 10**9); integer(end, -10**9, 10**9); integer(step, -10**9, 10**9)
    if step == 0: raise ValueError('step 0')
    if ops.count('next') > range_length(start, end, step): raise ValueError('next on exhausted iterator')


def tele_domain(grid, teleports):
    if type(grid) is not list or not grid: raise ValueError('grid rows')
    width = None
    for row in grid:
        if type(row) is not list or not row: raise ValueError('grid row')
        if width is None: width = len(row)
        if len(row) != width: raise ValueError('rectangular grid')
        for v in row:
            if type(v) is not int or v not in (0, 1): raise ValueError('grid cell')
    n, m = len(grid), width
    if n * m > 100000: raise ValueError('grid size')
    rows_of(teleports, 4, 10000)
    entrances = set()
    for r1, c1, r2, c2 in teleports:
        for v, hi in ((r1, n - 1), (c1, m - 1), (r2, n - 1), (c2, m - 1)): integer(v, 0, hi)
        if (r1, c1) in entrances or grid[r1][c1] or grid[r2][c2] or (r1, c1) == (r2, c2): raise ValueError('teleport cells')
        entrances.add((r1, c1))
    for r1, c1, r2, c2 in teleports:
        if (r2, c2) in entrances: raise ValueError('exit is an entrance')
    if grid[0][0] or grid[n - 1][m - 1] or (0, 0) in entrances or (n - 1, m - 1) in entrances: raise ValueError('start/destination')


def bot_domain(args):
    ops, rows = trace(BOT, args)
    integer(rows[0][0], 1, 100000); integer(rows[0][1], 1, 10**9)
    last = 0
    for row in rows[1:]:
        text(row[0], r'[0-9.]{1,15}', 15); integer(row[1], 0, 10**9)
        if row[1] < last: raise ValueError('time decreases')
        last = row[1]


def rbs_domain(tx):
    rows_of(tx, 5, 100000)
    ids = set()
    for r in tx:
        for v in r:
            if type(v) is not str: raise ValueError('string fields')
        text(r[0], NAME20, 20); text(r[1], NAME20, 20)
        if r[0] in ids: raise ValueError('unique ids')
        ids.add(r[0])
        for x in (r[2], r[3]):
            if x != '': decimal(x, 0, 10**9)
        decimal(r[4], 0, 10**9)


BOOT_LINE = r'(?:plus|next|jump) [+-]?(?:0|[1-9][0-9]{0,6})'


def parse_boot(lines):
    return [(s.split(' ')[0], int(s.split(' ')[1])) for s in lines]


def boot_domain(lines):
    strlist(lines, BOOT_LINE, 1, 100000, 13)
    for s in lines:
        if abs(int(s.split(' ')[1])) > 10**6: raise ValueError('value range')


def tbl_domain(args):
    ops, rows = trace(TBL, args)
    nr, nc = rows[0]
    integer(nr, 1, 100000); integer(nc, 1, 100000)
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'selectRow': integer(row[0], 0, nr - 1)
        elif op in ('selectCell', 'getColor'): integer(row[0], 0, nr - 1); integer(row[1], 0, nc - 1)
        elif op == 'setColor': text(row[0], r'[a-z0-9#]{1,10}', 10)


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == PAY:
        envelope(args, 2); pay_domain(*args)
    elif uid == PFP:
        envelope(args, 1); text(args[0], r'[A-Z]{1,100000}', 100000)
    elif uid == PS1:
        envelope(args, 3)
        strlist(args[0], NAME_WORDS, 0, 100000, 159)
        if sum(map(len, args[0])) > 3000000: raise ValueError('total characters')
        text(args[1], r'[A-Za-z0-9]{1,15}', 15); integer(args[2], 1, 100000)
    elif uid == PS2:
        envelope(args, 2)
        strlist(args[0], NAME_WORDS2, 0, 3000, 64); text(args[1], r'[A-Za-z0-9]{1,20}', 20)
    elif uid == PEL: pel_domain(args)
    elif uid == PQ:
        envelope(args, 1); array(args[0], 1, 10**9)
    elif uid == PBS: pbs_domain(args)
    elif uid == RUP1:
        envelope(args, 2)
        strlist(args[0], NAME20, 0, 100000, 20)
        array(args[1], 0, 10**9)
        if len(args[1]) != 2 * (len(args[0]) // 2): raise ValueError('draw count')
    elif uid == RUP2:
        envelope(args, 1); rows_of(args[0], 2, 100000)
        for name, group in args[0]: text(name, NAME20, 20); text(group, NAME20, 20)
    elif uid == RI: ri_domain(args)
    elif uid == TELE:
        envelope(args, 2); tele_domain(*args)
    elif uid == BOT: bot_domain(args)
    elif uid == RFI:
        envelope(args, 2)
        strlist(args[0], r'[a-z]{1,100}', 0, 100000, 100)
        if sum(map(len, args[0])) > 1000000: raise ValueError('total characters')
        text(args[1], r'[a-z]{0,100000}', 100000)
    elif uid in (RBS1, RBS2, RBS3):
        envelope(args, 2 if uid == RBS2 else 1); rbs_domain(args[0])
        if uid == RBS2: integer(args[1], 0, 10**9)
    elif uid in (BOOT1, BOOT2):
        envelope(args, 1); boot_domain(args[0])
        if uid == BOOT2 and run_boot(parse_boot(args[0]))[0] == 'end': raise ValueError('program already terminates')
    elif uid == RSD:
        envelope(args, 3)
        text(args[0], r'[0-9?]{1,100000}', 100000); integer(args[1], 0, 10**6); integer(args[2], 0, 9)
    elif uid == TBL: tbl_domain(args)


# ---------------------------------------------------------------- references
TYPE_RANK = {'CREDIT': 0, 'CREDIT_CARD': 1, 'PAYPAL': 2}


def ref_pay(tx, amount):
    payments = [r for r in tx if r[1] == 'PAYMENT']
    left = []
    for p in payments:  # rescan every refund row for each payment
        refunded = 0
        for r in tx:
            if r[1] == 'REFUND' and r[3] == p[0]: refunded += int(r[5])
        left.append((TYPE_RANK.get(p[2], 3), '' if p[2] in TYPE_RANK else p[2], -int(p[4]), p[0], int(p[5]) - refunded))
    left.sort()
    out = []
    for *_, pid, avail in left:
        give = min(avail, amount)
        if give > 0: out.append([pid, give]); amount -= give
    return out


def ref_pfp(s):
    n, out = len(s), []
    for size in range(1, n + 1):
        if n % size: continue
        want = sorted(s[:size])
        if all(sorted(s[i:i + size]) == want for i in range(0, n, size)): out.append(size)
    return out


def first_word(name, prefix):
    for i, w in enumerate(name.split(' ')):
        if w.lower().startswith(prefix.lower()): return i
    return None


def ref_ps1(names, prefix, k):
    keyed = sorted((first_word(nm, prefix), nm) for nm in names if first_word(nm, prefix) is not None)
    return [nm for _, nm in keyed[:k]]


def ref_ps2(names, word):
    return [[nm for _, nm in sorted((first_word(nm, word[:i]), nm) for nm in names if first_word(nm, word[:i]) is not None)]
            for i in range(1, len(word) + 1)]


def ref_pel(ops, rows):
    cap = rows[0][0]; items = {}; clock = 0; out = [None]
    for op, row in zip(ops[1:], rows[1:]):
        clock += 1
        if op == 'get':
            key, now = row
            if key not in items: out.append(-1); continue
            if items[key]['expiry'] <= now: del items[key]; out.append(-1); continue
            items[key]['seen'] = clock; out.append(items[key]['value'])
        else:
            key, value, priority, expiry, now = row
            if key not in items and len(items) == cap:
                expired = [k for k in items if items[k]['expiry'] <= now]
                if expired: victim = min(expired, key=lambda k: (items[k]['expiry'], items[k]['seen']))
                else: victim = min(items, key=lambda k: (items[k]['priority'], items[k]['seen']))
                del items[victim]
            items[key] = {'value': value, 'priority': priority, 'expiry': expiry, 'seen': clock}
            out.append(None)
    return out


def ref_pq(wait):
    queue = list(wait); sizes = [len(queue)]; t = 0
    while queue:
        t += 1
        queue = [w for w in queue[1:] if w > t]
        sizes.append(len(queue))
    return sizes


def ref_pbs(ops, rows):
    free = [[p[0], p[1], int(p[2])] for p in rows[0][0]]; out = [None]
    for nb, size in rows[1:]:
        here = [p for p in free if p[1] == nb]
        best = None
        for mask in range(1, 1 << len(here)):
            pick = [here[i] for i in range(len(here)) if mask >> i & 1]
            total = sum(p[2] for p in pick)
            if total < size: continue
            key = (len(pick), total, sorted(p[0] for p in pick))
            if best is None or key < best: best = key
        if best is None: out.append([]); continue
        free = [p for p in free if p[0] not in best[2]]
        out.append(best[2])
    return out


def ref_rup1(users, draws):
    pool = list(users); pairs = []; k = 0
    while len(pool) >= 2:
        pair = []
        for _ in range(2):
            i = draws[k] % len(pool); k += 1
            pair.append(pool[i])
            pool = pool[:i] + [pool[-1]] + pool[i + 1:-1] if i != len(pool) - 1 else pool[:-1]
        pairs.append(pair)
    if pool: pairs.append([pool[0]])
    return pairs


def ref_rup2(users):
    groups = {}
    for name, group in users: groups.setdefault(group, []).append(name)
    pairs = []
    while sum(1 for g in groups if groups[g]) >= 2:
        order = sorted((g for g in groups if groups[g]), key=lambda g: (-len(groups[g]), g))
        a, b = order[0], order[1]
        pairs.append([groups[a].pop(0), groups[b].pop(0)])
    return pairs


def ref_ri(ops, rows):
    values = list(range(*rows[0])); i = 0; out = [None]
    for op in ops[1:]:
        if op == 'hasNext': out.append(i < len(values))
        else: out.append(values[i]); i += 1
    return out


def ref_tele(grid, teleports):
    n, m = len(grid), len(grid[0]); r = c = moves = 0
    for _ in range(n * m + 1):  # a walk longer than n*m positions must repeat one
        if (r, c) == (n - 1, m - 1): return moves
        if c == m - 1 or grid[r][c + 1] == 1: return -1
        c += 1; moves += 1
        for t in teleports:
            if (t[0], t[1]) == (r, c): r, c = t[2], t[3]; break
    return -1


def ref_bot(ops, rows):
    limit, window = rows[0]; seen = {}; out = [None]
    for ip, ts in rows[1:]:
        seen.setdefault(ip, []).append(ts)
        out.append(sum(1 for x in seen[ip] if ts - window + 1 <= x <= ts) > limit)
    return out


def ref_rfi(recipes, ingredients):
    return sum(1 for r in recipes if all(r.count(ch) <= ingredients.count(ch) for ch in set(r)))


def amount(x): return int(x) if x else 0


def ref_rbs(uid, tx, at=None):
    users = sorted({r[1] for r in tx if at is None or int(r[4]) <= at})
    out = []
    for u in users:
        mine = [r for r in tx if r[1] == u and (at is None or int(r[4]) <= at)]
        if uid != RBS3:
            out.append([u, sum(amount(r[2]) - amount(r[3]) for r in mine)])
            continue
        balance = peak = 0
        for r in sorted(mine, key=lambda r: (int(r[4]), r[0])):
            balance += amount(r[2]) - amount(r[3]); peak = max(peak, balance)
        out.append([u, balance, peak])
    return out


def run_boot(prog):
    """Literal run; returns ('end' | 'out' | 'loop', index, accumulator) with a set of executed indices."""
    executed, i, acc = set(), 0, 0
    while True:
        if i == len(prog): return 'end', i, acc
        if not 0 <= i < len(prog): return 'out', i, acc
        if i in executed: return 'loop', i, acc
        executed.add(i)
        op, x = prog[i]
        if op == 'plus': acc += x; i += 1
        elif op == 'next': i += 1
        else: i += x


def ref_boot1(lines):
    kind, i, acc = run_boot(parse_boot(lines))
    return [i, acc] if kind == 'loop' else [-1, acc]


def ref_boot2(lines):
    prog = parse_boot(lines)
    for j, (op, x) in enumerate(prog):
        if op == 'plus': continue
        changed = list(prog); changed[j] = ('next' if op == 'jump' else 'jump', x)
        kind, _, acc = run_boot(changed)
        if kind == 'end': return [j, acc]
    return [-1, 0]


def ref_rsd(pattern, target, cap):
    slots = [i for i, ch in enumerate(pattern) if ch == '?']
    fixed = sum(int(ch) for ch in pattern if ch != '?')
    chosen = []

    def dfs(k, total):
        if k == len(slots): return total == target
        for d in range(cap + 1):
            chosen.append(d)
            if dfs(k + 1, total + d): return True
            chosen.pop()
        return False
    if not dfs(0, fixed): return ''
    out = list(pattern)
    for i, d in zip(slots, chosen): out[i] = str(d)
    return ''.join(out)


def ref_tbl(ops, rows):
    nr, nc = rows[0]; grid = [[''] * nc for _ in range(nr)]; sel = []; out = [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'selectTable': sel = [(r, c) for r in range(nr) for c in range(nc)]
        elif op == 'selectRow': sel = [(row[0], c) for c in range(nc)]
        elif op == 'selectCell': sel = [(row[0], row[1])]
        elif op == 'setColor':
            for r, c in sel: grid[r][c] = row[0]
        if op == 'getColor': out.append(grid[row[0]][row[1]])
        else: out.append(None)
    return out


def reference(uid, args):
    validate_domain(uid, args)
    if uid == PAY:
        if len(args[0]) > 400: raise ValueError('reference budget')
        return ref_pay(*args)
    if uid == PFP:
        if len(args[0]) > 3000: raise ValueError('reference budget')
        return ref_pfp(args[0])
    if uid == PS1:
        if len(args[0]) > 2000: raise ValueError('reference budget')
        return ref_ps1(*args)
    if uid == PS2:
        if len(args[0]) > 300: raise ValueError('reference budget')
        return ref_ps2(*args)
    if uid == PEL:
        if len(args[0]) > 3000: raise ValueError('reference budget')
        return ref_pel(*args)
    if uid == PQ:
        if len(args[0]) > 2000: raise ValueError('reference budget')
        return ref_pq(args[0])
    if uid == PBS:
        if len(args[0]) > 80: raise ValueError('reference budget')
        return ref_pbs(*args)
    if uid == RUP1:
        if len(args[0]) > 2000: raise ValueError('reference budget')
        return ref_rup1(*args)
    if uid == RUP2:
        if len(args[0]) > 400: raise ValueError('reference budget')
        return ref_rup2(args[0])
    if uid == RI:
        if len(range(*args[1][0])) > 200000: raise ValueError('reference budget')
        return ref_ri(*args)
    if uid == TELE:
        if len(args[0]) * len(args[0][0]) > 400: raise ValueError('reference budget')
        return ref_tele(*args)
    if uid == BOT:
        if len(args[0]) > 3000: raise ValueError('reference budget')
        return ref_bot(*args)
    if uid == RFI:
        if sum(map(len, args[0])) + len(args[1]) > 20000: raise ValueError('reference budget')
        return ref_rfi(*args)
    if uid in (RBS1, RBS2, RBS3):
        if len(args[0]) > 400: raise ValueError('reference budget')
        return ref_rbs(uid, *args)
    if uid == BOOT1:
        if len(args[0]) > 2000: raise ValueError('reference budget')
        return ref_boot1(args[0])
    if uid == BOOT2:
        if len(args[0]) > 300: raise ValueError('reference budget')
        return ref_boot2(args[0])
    if uid == RSD:
        if (args[2] + 1) ** args[0].count('?') > 20000: raise ValueError('reference budget')
        return ref_rsd(*args)
    if args[1][0][0] * args[1][0][1] > 400 or len(args[0]) > 400: raise ValueError('reference budget')
    return ref_tbl(*args)
