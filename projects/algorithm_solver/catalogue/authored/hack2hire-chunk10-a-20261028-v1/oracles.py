"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (explicit comparator
insertion sorts, event-list rescans, linear minimum scans instead of heaps, full snapshot stacks for
transactions, sort-everything-per-query, explicit byte encoders, per-level nut simulation, index
arithmetic over the whole written stream) and refuse inputs above a small budget.
"""
import re

H = 'hack2hire:'
CSS = H + '67ce7ab08f73eb6319edd207'
TKV1 = H + '69d3f7fd79bf03c0074bce16'
TKV2 = H + '69dd59d595e80ae213e5b7fc'
CEV1 = H + '688d0850b6c09ad9a4fcc2db'
CEV2 = H + '68aba144fc2e86fe2162e8a1'
CG1 = H + '6ab30396e74ebb7457a3ef46'
CG2 = H + '6ab3042be74ebb7457a3ef4a'
CG3 = H + '6ab3047ce74ebb7457a3ef51'
CBS1 = H + '69190b156723130c5456345c'
CBS2 = H + '691b8695419c66014d71411a'
DTS = H + '677ed3ec052a260e0165706f'
SQL = H + '691cfb5cba2fba0a9e173e8c'
KVR1 = H + '6920d01494b324049c3251bd'
KVR2 = H + '6920d07794b324049c3251be'
KVR3 = H + '6920d4a994b324049c3251c1'
NTS1 = H + '69b35205a4e93c007df404fe'
NTS2 = H + '69b38216a4e93c007df405de'
NTS3 = H + '69b38409a4e93c007df405e6'
NTS4 = H + '69b385d3a4e93c007df405f1'
PKV1 = H + '691523d03f8671d8f7a56571'
PKV2 = H + '691523d43f8671d8f7a56572'
QPG = H + '6792d9906828628f54397d99'
RLM1 = H + '67ce4e968f73eb6319edd1f0'
RLM2 = H + '67e0bdefa59c3d249d3625fe'
RFT = H + '67d44fdf488516fd8ad5a0ba'
RMS1 = H + '69f2665342791c82ab992694'
RMS2 = H + '69f266df42791c82ab992697'
RMS3 = H + '69f2674342791c82ab99269a'
RMS4 = H + '69f2676842791c82ab99269b'
RBF = H + '69d16c6917b72775cc49bf96'
SQN = H + '696bebd76b040fa4d120bb7a'

IDS = (CSS, TKV1, TKV2, CEV1, CEV2, CG1, CG2, CG3, CBS1, CBS2, DTS, SQL, KVR1, KVR2, KVR3, NTS1, NTS2, NTS3, NTS4,
       PKV1, PKV2, QPG, RLM1, RLM2, RFT, RMS1, RMS2, RMS3, RMS4, RBF, SQN)
KVR = (KVR1, KVR2, KVR3)
NTS = (NTS1, NTS2, NTS3, NTS4)
RMS = (RMS1, RMS2, RMS3, RMS4)

_KV1 = {'set': 2, 'get': 1, 'unset': 1}
_KV2 = dict(_KV1, begin=0, rollback=0, commit=0)
_NT1 = {'createNote': 3, 'getNote': 1, 'updateNote': 4, 'deleteNote': 1}
_NT2 = dict(_NT1, searchNotes=1)
_NT3 = dict(_NT2, addTag=2, removeTag=2, getNotesByTag=1)
_RM1 = {'addRecipe': 3, 'getRecipe': 1, 'updateRecipe': 4, 'deleteRecipe': 1}
_RM2 = dict(_RM1, searchByIngredient=1)
_RM3 = dict(_RM2, rateRecipe=2, getTopRated=1)
# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    TKV1: ('TemporalKVStore', 0, {'set': 3, 'get': 2, 'remove': 1}, ('set',)),
    TKV2: ('TemporalKVStore', 0, {'set': 3, 'get': 2, 'remove': 2}, ('set',)),
    CEV1: ('RankedCache', 1, {'put': 3, 'get': 1}, ('put',)),
    CEV2: ('RankedCache', 2, {'put': 3, 'get': 1, 'getLoadCount': 0}, ('put',)),
    CBS1: ('ChatApp', 0, {'addBot': 2, 'sendMessage': 2, 'getRecentMessages': 1}, ('sendMessage',)),
    CBS2: ('ChatApp', 0, {'createChannel': 1, 'addBot': 3, 'sendMessage': 3, 'getRecentMessages': 2}, ()),
    DTS: ('DelayedTaskScheduler', 0, {'schedule': 3, 'runDue': 1, 'cancel': 1}, ()),
    SQL: ('SQLManager', 0, {'createTable': 2, 'insert': 2, 'select': 4}, ('createTable',)),
    KVR1: ('KeyValueStore', 0, _KV1, ('set', 'unset')),
    KVR2: ('KeyValueStore', 0, _KV2, ('set', 'unset', 'begin')),
    KVR3: ('KeyValueStore', 0, dict(_KV2, count=1), ('set', 'unset', 'begin')),
    NTS1: ('SecondBrainSystem', 0, _NT1, ()),
    NTS2: ('SecondBrainSystem', 0, _NT2, ()),
    NTS3: ('SecondBrainSystem', 0, _NT3, ()),
    NTS4: ('SecondBrainSystem', 0, dict(_NT3, getVersionCount=1, revertNote=3), ()),
    PKV1: ('PersistentKVStore', 0, {'set': 2, 'get': 1, 'delete': 1, 'save': 0, 'load': 1}, ('set', 'load')),
    PKV2: ('PersistentKVStore', 0, {'set': 2, 'get': 1, 'delete': 1, 'save': 0, 'load': 1}, ('set',)),
    RLM1: ('RateLimiter', 2, {'allowRequest': 1}, ()),
    RLM2: ('RateLimiter', 2, {'allowRequest': 2}, ()),
    RFT: ('FileStorageSystem', 0, {'storeFile': 2, 'getKthRecentFiles': 1, 'returnAllFiles': 0}, ('storeFile',)),
    RMS1: ('RecipeManager', 0, _RM1, ()),
    RMS2: ('RecipeManager', 0, _RM2, ()),
    RMS3: ('RecipeManager', 0, _RM3, ()),
    RMS4: ('RecipeManager', 0, dict(_RM3, listByNamePrefix=1), ()),
    RBF: ('RingBuffer', 1, {'write': 1, 'read': 1}, ('write',)),
    SQN: ('SquirrelResearch', 0, {'hideNuts': 2, 'retrieveNuts': 2, 'getHighestLevel': 1}, ()),
}
MAX_OPS = 100001

# ---------------------------------------------------------------- domain helpers
WORD = r'[a-z0-9]{1,10}'
NAME = r'[A-Za-z0-9_]{1,15}'
PRINT = r'[ -~]*'
DATE = r'[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])'
DIGITS = r'0|[1-9][0-9]{0,8}'


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def boolean(v):
    if type(v) is not bool: raise ValueError('boolean domain')


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def strlist(a, pattern, minimum=0, maximum=100000, width=100):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')
    for v in a: text(v, pattern, width)


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
    return list(zip(ops[1:], rows[1:]))


def nondecreasing(times):
    for a, b in zip(times, times[1:]):
        if b < a: raise ValueError('time order')


RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
CARD = r'(?:[2-9]|10|[JQKA])[SHDC]'


def cards(deck, n):
    strlist(deck, CARD, n, n, 3)
    if len(set(deck)) != len(deck): raise ValueError('duplicate card')


# ---------------------------------------------------------------- per-variant domains
def css_domain(order, words):
    text(order, r'[a-z]{1,26}', 26)
    if len(set(order)) != len(order): raise ValueError('repeated order letter')
    strlist(words, '[' + order + ']{0,50}', 0, 20000, 50)
    if sum(map(len, words)) > 200000: raise ValueError('total characters')


def tkv_domain(uid, args):
    calls = trace(uid, args); times = []
    for op, row in calls:
        text(row[0], WORD, 10)
        if op == 'set': text(row[1], WORD, 10); integer(row[2], 1, 10**9); times.append(row[2])
        elif op == 'get': integer(row[1], 1, 10**9)
        elif uid == TKV2: integer(row[1], 1, 10**9); times.append(row[1])
    nondecreasing(times)


def cev_domain(uid, args):
    calls = trace(uid, args); ctor = args[1][0]
    integer(ctor[0], 1, 100000)
    if uid == CEV2:
        if type(ctor[1]) is not list or len(ctor[1]) > 100000: raise ValueError('source size')
        for r in ctor[1]:
            if type(r) is not list or len(r) != 3: raise ValueError('source row')
            text(r[0], WORD, 10); text(r[1], WORD, 10); integer(r[2], -10**9, 10**9)
        if len({r[0] for r in ctor[1]}) != len(ctor[1]): raise ValueError('duplicate source key')
    for op, row in calls:
        if op == 'getLoadCount': continue
        text(row[0], WORD, 10)
        if op == 'put': text(row[1], WORD, 10); integer(row[2], -10**9, 10**9)


BOTS = ('echo', 'reverse', 'count')


def cbs_domain(uid, args):
    calls = trace(uid, args)
    for op, row in calls:
        if uid == CBS2: text(row[0], WORD, 10)
        rest = row[1:] if uid == CBS2 else row
        if op == 'addBot': text(rest[0], NAME, 15); text(rest[1], r'[a-z]{1,10}', 10)
        elif op == 'sendMessage': text(rest[0], NAME, 15); text(rest[1], PRINT, 60)
        elif op == 'getRecentMessages': integer(rest[0], 0, 100000)


def dts_domain(args):
    calls = trace(DTS, args); times, ids = [], set()
    for op, row in calls:
        text(row[0] if op != 'runDue' else 't', WORD, 10)
        if op == 'schedule':
            integer(row[1], 0, 10**9); integer(row[2], 0, 10**9); times.append(row[2])
            if row[0] in ids: raise ValueError('duplicate task id')
            ids.add(row[0])
        elif op == 'runDue': integer(row[0], 0, 10**9); times.append(row[0])
    nondecreasing(times)


SQL_VALUE = r'-?[a-z0-9]{1,10}'
OPS = ('=', '!=', '<', '<=', '>', '>=')


def sql_domain(args):
    calls = trace(SQL, args); tables = set()
    for op, row in calls:
        text(row[0], r'[a-z]{1,10}', 10)
        if op == 'createTable':
            strlist(row[1], r'[a-z]{1,10}', 1, 5, 10)
            if len(set(row[1])) != len(row[1]) or row[0] in tables: raise ValueError('table or column duplicate')
            tables.add(row[0])
        elif op == 'insert': strlist(row[1], SQL_VALUE, 0, 6, 11)
        else:
            if type(row[1]) is not list or len(row[1]) > 3: raise ValueError('conditions')
            for c in row[1]:
                if type(c) is not list or len(c) != 3 or c[1] not in OPS: raise ValueError('condition')
                text(c[0], r'[a-z]{1,10}', 10); text(c[2], SQL_VALUE, 11)
            text(row[2], r'[a-z]{0,10}', 10); boolean(row[3])


def kvr_domain(uid, args):
    for op, row in trace(uid, args):
        if op in ('set', 'get', 'unset', 'count'): text(row[0], WORD, 10)
        if op == 'set': text(row[1], WORD, 10)


TEXT = r'[A-Za-z0-9 ]{0,30}'
NOTE_ID = r'note[0-9]{1,6}'


def nts_domain(uid, args):
    times = []
    for op, row in trace(uid, args):
        if op == 'createNote': text(row[0], TEXT, 30); text(row[1], TEXT, 30); integer(row[2], 1, 10**9); times.append(row[2])
        elif op == 'updateNote': text(row[0], NOTE_ID, 10); text(row[1], TEXT, 30); text(row[2], TEXT, 30); integer(row[3], 1, 10**9); times.append(row[3])
        elif op == 'revertNote': text(row[0], NOTE_ID, 10); integer(row[1], 0, 100000); integer(row[2], 1, 10**9); times.append(row[2])
        elif op == 'searchNotes': text(row[0], r'[A-Za-z0-9]{1,10}', 10)
        elif op in ('addTag', 'removeTag'): text(row[0], NOTE_ID, 10); text(row[1], WORD, 10)
        elif op == 'getNotesByTag': text(row[0], WORD, 10)
        else: text(row[0], NOTE_ID, 10)
    nondecreasing(times)


PKV_VALUE = r'[ -~]{1,20}'
MAGIC = [80, 75, 86, 50]


def u32(blob, i):
    if i + 4 > len(blob): raise ValueError('truncated')
    return ((blob[i] * 256 + blob[i + 1]) * 256 + blob[i + 2]) * 256 + blob[i + 3], i + 4


def be32(n): return [n >> 24 & 255, n >> 16 & 255, n >> 8 & 255, n & 255]


def pkv_encode(uid, pairs):
    """Reference encoder: explicit big-endian layout, entries sorted by key."""
    body = be32(len(pairs))
    for k, v in sorted(pairs):
        body += be32(len(k)) + [ord(c) for c in k] + be32(len(v)) + [ord(c) for c in v]
    if uid == PKV1: return body
    return MAGIC + body + be32(sum(body) % 2**32)


def pkv_decode(uid, blob):
    """Reference decoder; raises ValueError on any malformed blob."""
    if uid == PKV2:
        if blob[:4] != MAGIC or len(blob) < 12: raise ValueError('magic')
        body = blob[4:-4]
        if u32(blob, len(blob) - 4)[0] != sum(body) % 2**32: raise ValueError('checksum')
    else:
        body = blob
    count, i = u32(body, 0); out = []
    for _ in range(count):
        n, i = u32(body, i); k = ''.join(map(chr, body[i:i + n])); i += n
        if len(k) != n or re.fullmatch(WORD, k) is None: raise ValueError('key')
        n, i = u32(body, i); v = ''.join(map(chr, body[i:i + n])); i += n
        if len(v) != n or re.fullmatch(PKV_VALUE, v) is None: raise ValueError('value')
        if out and out[-1][0] >= k: raise ValueError('key order')
        out.append((k, v))
    if i != len(body): raise ValueError('trailing bytes')
    return out


def pkv_domain(uid, args):
    for op, row in trace(uid, args):
        if op in ('set', 'get', 'delete'): text(row[0], WORD, 10)
        if op == 'set': text(row[1], PKV_VALUE, 20)
        if op == 'load':
            b = row[0]
            if type(b) is not list or len(b) > 2000000: raise ValueError('blob size')
            for x in b: integer(x, 0, 255)
            if uid == PKV1: pkv_decode(uid, b)  # level 1 only loads well-formed blobs


AMOUNT = r'(?:0|[1-9][0-9]{0,8})(?:\.[0-9]{1,2})?'


def qpg_domain(records, filters, size, page):
    if type(records) is not list or len(records) > 100000: raise ValueError('records')
    for r in records:
        if type(r) is not list or len(r) != 5: raise ValueError('record shape')
        text(r[0], DIGITS, 9); text(r[1], WORD, 10); text(r[2], WORD, 10); text(r[3], r'[A-Z]{3}', 3); text(r[4], AMOUNT, 12)
    if len({r[1] for r in records}) != len(records): raise ValueError('duplicate id')
    if type(filters) is not list or len(filters) != 6: raise ValueError('filters')
    for f, p in zip(filters, ['|' + DIGITS] * 2 + ['|' + AMOUNT] * 2 + ['|' + WORD, r'|[A-Z]{3}']):
        text(f, p, 12)
    integer(size, 1, 100000); integer(page, 1, 100000)


def rlm_domain(uid, args):
    calls = trace(uid, args); integer(args[1][0][0], 1, 100000); integer(args[1][0][1], 1, 10**9); times = []
    for _, row in calls:
        if uid == RLM2: text(row[0], WORD, 10)
        integer(row[-1], 0, 10**9); times.append(row[-1])
    nondecreasing(times)


def rft_domain(args):
    files = set()
    for op, row in trace(RFT, args):
        if op == 'storeFile':
            text(row[0], r'[a-z0-9_.]{1,20}', 20); text(row[1], DATE, 10)
            if row[0] in files: raise ValueError('duplicate file')
            files.add(row[0])
        elif op == 'getKthRecentFiles': integer(row[0], 1, 100000)


RNAME = r'[A-Za-z0-9 ]{1,20}'
ING = r'[A-Za-z ]{1,15}'
RID = r'recipe[0-9]{1,6}'


def rms_domain(uid, args):
    for op, row in trace(uid, args):
        if op in ('addRecipe', 'updateRecipe'):
            r = row[1:] if op == 'updateRecipe' else row
            if op == 'updateRecipe': text(row[0], RID, 12)
            text(r[0], RNAME, 20); strlist(r[1], ING, 0, 10, 15); strlist(r[2], r'[ -~]{1,40}', 0, 10, 40)
        elif op == 'searchByIngredient': text(row[0], ING, 15)
        elif op == 'rateRecipe': text(row[0], RID, 12); integer(row[1], 1, 5)
        elif op == 'getTopRated': integer(row[0], 1, 100000)
        elif op == 'listByNamePrefix': text(row[0], r'[A-Za-z0-9 ]{0,20}', 20)
        else: text(row[0], RID, 12)


def rbf_domain(args):
    calls = trace(RBF, args); integer(args[1][0][0], 1, 100000)
    for op, row in calls:
        if op == 'write': text(row[0], PRINT, 100000)
        else: integer(row[0], 0, 100000)


def sqn_domain(args):
    total = 0
    for op, row in trace(SQN, args):
        text(row[0], WORD, 10)
        if op != 'getHighestLevel': integer(row[1], 0, 10**9)
        if op == 'hideNuts': total += row[1]
    if total > 10**14: raise ValueError('nut total')


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == CSS:
        envelope(args, 2); css_domain(*args)
    elif uid in (TKV1, TKV2): tkv_domain(uid, args)
    elif uid in (CEV1, CEV2): cev_domain(uid, args)
    elif uid in (CG1, CG2):
        envelope(args, 1); cards(args[0], 6)
    elif uid == CG3:
        envelope(args, 2); integer(args[0], 2, 17); cards(args[1], 3 * args[0])
    elif uid in (CBS1, CBS2): cbs_domain(uid, args)
    elif uid == DTS: dts_domain(args)
    elif uid == SQL: sql_domain(args)
    elif uid in KVR: kvr_domain(uid, args)
    elif uid in NTS: nts_domain(uid, args)
    elif uid in (PKV1, PKV2): pkv_domain(uid, args)
    elif uid == QPG:
        envelope(args, 4); qpg_domain(*args)
    elif uid in (RLM1, RLM2): rlm_domain(uid, args)
    elif uid == RFT: rft_domain(args)
    elif uid in RMS: rms_domain(uid, args)
    elif uid == RBF: rbf_domain(args)
    elif uid == SQN: sqn_domain(args)


# ---------------------------------------------------------------- references
def ref_css(order, words):
    def less(x, y):  # explicit comparator from the inferred definition
        for a, b in zip(x, y):
            if a != b: return order.index(a) < order.index(b)
        return len(x) < len(y)
    out = []
    for w in words:  # insertion sort, stable
        i = len(out)
        while i > 0 and less(w, out[i - 1]): i -= 1
        out.insert(i, w)
    return out


def ref_tkv(uid, calls):
    events, out = [], [None]
    def look(key, t):
        best = ''
        for k, s, v in events:
            if k == key and s <= t: best = '' if v is None else v
        return best
    for op, row in calls:
        if op == 'set': events.append((row[0], row[2], row[1])); out.append(None)
        elif op == 'get': out.append(look(row[0], row[1]))
        elif uid == TKV1:
            had = any(k == row[0] for k, _, _ in events)
            events = [e for e in events if e[0] != row[0]]; out.append(had)
        else:
            had = look(row[0], row[1]) != ''
            events.append((row[0], row[1], None)); out.append(had)
    return out


def ref_cev(uid, args, calls):
    cap = args[1][0][0]; source = {r[0]: (r[1], r[2]) for r in args[1][0][1]} if uid == CEV2 else {}
    cache, seq, loads, out = {}, 0, 0, [None]
    def write(k, v, r):
        nonlocal seq
        seq += 1
        if k not in cache and len(cache) == cap:
            victim = None
            for key, (_, rank, s) in cache.items():
                if victim is None or (rank, s) < (cache[victim][1], cache[victim][2]): victim = key
            del cache[victim]
        cache[k] = (v, r, seq)
    for op, row in calls:
        if op == 'put':
            write(*row); source[row[0]] = (row[1], row[2]); out.append(None)
        elif op == 'getLoadCount': out.append(loads)
        elif row[0] in cache: out.append(cache[row[0]][0])
        elif uid == CEV2 and row[0] in source:
            loads += 1; v, r = source[row[0]]; write(row[0], v, r); out.append(v)
        else: out.append('')
    return out


def strength(hand, extended):
    ranks = sorted((RANKS.index(c[:-1]) for c in hand), reverse=True)
    suits = {c[-1] for c in hand}
    same = [r for r in ranks if ranks.count(r) >= 2]
    straight = ranks[0] - ranks[1] == 1 and ranks[1] - ranks[2] == 1
    if extended and straight and len(suits) == 1: return (6, ranks)
    if len(set(ranks)) == 1: return (5 if extended else 3, ranks[:1])
    if extended and straight: return (4, ranks)
    if extended and len(suits) == 1: return (3, ranks)
    if same: return (2, [same[0], [r for r in ranks if r != same[0]][0]])
    return (1, ranks)


def ref_cg(uid, args):
    if uid == CG3:
        n, deck = args
        hands = [[deck[i] for i in range(p, len(deck), n)] for p in range(n)]
        s = [strength(h, False) for h in hands]
        return [hands, [i + 1 for i in range(n) if s[i] == max(s)]]
    deck = args[0]; h1, h2 = deck[0::2], deck[1::2]
    a, b = strength(h1, uid == CG2), strength(h2, uid == CG2)
    return [h1, h2, 1 if a > b else 2 if b > a else 0]


def bot_reply(kind, text, users):
    if kind == 'echo' and text.startswith('/echo '): return text[6:]
    if kind == 'reverse' and text.startswith('/reverse '): return text[9:][::-1]
    if kind == 'count' and text == '/count': return str(users)
    return None


def ref_cbs(uid, calls):
    chans, out = ({'': ([], [], [0])} if uid == CBS1 else {}), [None]
    for op, row in calls:
        if uid == CBS1: row = [''] + row
        if op == 'createChannel':
            ok = row[0] not in chans
            if ok: chans[row[0]] = ([], [], [0])
            out.append(ok); continue
        if row[0] not in chans:
            out.append([] if op == 'getRecentMessages' else False); continue
        log, bots, users = chans[row[0]]
        if op == 'addBot':
            ok = row[2] in BOTS and all(b[0] != row[1] for b in bots)
            if ok: bots.append((row[1], row[2]))
            out.append(ok)
        elif op == 'sendMessage':
            users[0] += 1; log.append(row[1] + ': ' + row[2])
            for name, kind in bots:
                r = bot_reply(kind, row[2], users[0])
                if r is not None: log.append(name + ': ' + r)
            out.append(None if uid == CBS1 else True)
        else:
            k = row[1]; out.append(log[max(0, len(log) - k):] if k else [])
    return out


def ref_dts(calls):
    pending, seq, out = [], 0, [None]
    for op, row in calls:
        if op == 'schedule':
            seq += 1; pending.append((row[2] + row[1], seq, row[0])); out.append(row[2] + row[1])
        elif op == 'cancel':
            hit = [p for p in pending if p[2] == row[0]]
            pending = [p for p in pending if p[2] != row[0]]; out.append(bool(hit))
        else:
            due = sorted(p for p in pending if p[0] <= row[0])
            pending = [p for p in pending if p[0] > row[0]]; out.append([p[2] for p in due])
    return out


INT_RE = r'0|-?[1-9][0-9]{0,8}'


def is_int(s): return re.fullmatch(INT_RE, s) is not None


def ref_sql(calls):
    tables, out = {}, [None]
    for op, row in calls:
        if op == 'createTable':
            tables[row[0]] = {'cols': list(row[1]), 'types': None, 'rows': []}; out.append(None)
        elif op == 'insert':
            t = tables.get(row[0])
            if t is None or len(row[1]) != len(t['cols']): out.append(False); continue
            kinds = [is_int(v) for v in row[1]]
            if t['types'] is not None and kinds != t['types']: out.append(False); continue
            t['types'] = kinds; t['rows'].append(list(row[1])); out.append(True)
        else:
            t = tables.get(row[0]); conds, order, asc = row[1], row[2], row[3]
            names = [c[0] for c in conds] + ([order] if order else [])
            if t is None or any(n not in t['cols'] for n in names) or not t['rows']:
                out.append([]); continue
            def val(r, col):
                i = t['cols'].index(col)
                return int(r[i]) if t['types'][i] else r[i]
            def ok(r):
                for col, o, lit in conds:
                    if t['types'][t['cols'].index(col)]:
                        if not is_int(lit): return False
                        lit = int(lit)
                    a = val(r, col)
                    if not {'=': a == lit, '!=': a != lit, '<': a < lit, '<=': a <= lit, '>': a > lit, '>=': a >= lit}[o]: return False
                return True
            hits = [r for r in t['rows'] if ok(r)]
            res = []
            for r in hits:  # stable insertion sort
                i = len(res)
                if order:
                    while i > 0 and (val(r, order) < val(res[i - 1], order) if asc else val(r, order) > val(res[i - 1], order)): i -= 1
                res.insert(i, list(r))
            out.append(res)
    return out


def ref_kvr(uid, calls):
    data, stack, out = {}, [], [None]
    for op, row in calls:
        if op == 'set': data[row[0]] = row[1]; out.append(None)
        elif op == 'get': out.append(data.get(row[0], ''))
        elif op == 'unset': data.pop(row[0], None); out.append(None)
        elif op == 'begin': stack.append(dict(data)); out.append(None)
        elif op == 'rollback':
            out.append(bool(stack))
            if stack: data = stack.pop()
        elif op == 'commit': out.append(bool(stack)); stack = []
        else: out.append(sum(1 for v in data.values() if v == row[0]))
    return out


def ref_nts(uid, calls):
    notes, n, out = {}, 0, [None]
    def num(i): return int(i[4:])
    for op, row in calls:
        if op == 'createNote':
            n += 1; notes['note%d' % n] = {'h': [(row[0], row[1])], 'c': row[2], 'u': row[2], 'tags': []}; out.append('note%d' % n)
        elif op == 'getNote':
            x = notes.get(row[0]); out.append([] if x is None else [x['h'][-1][0], x['h'][-1][1], x['c'], x['u']])
        elif op in ('updateNote', 'revertNote'):
            x = notes.get(row[0])
            if x is None or op == 'revertNote' and not 1 <= row[1] <= len(x['h']): out.append(False); continue
            x['h'].append((row[1], row[2]) if op == 'updateNote' else x['h'][row[1] - 1]); x['u'] = row[-1]; out.append(True)
        elif op == 'deleteNote': out.append(notes.pop(row[0], None) is not None)
        elif op == 'searchNotes':
            k = row[0].lower()
            hits = [i for i, x in notes.items() if k in x['h'][-1][0].lower() or k in x['h'][-1][1].lower()]
            out.append(sorted(hits, key=lambda i: (-notes[i]['u'], num(i))))
        elif op == 'addTag':
            x = notes.get(row[0]); ok = x is not None and row[1] not in x['tags']
            if ok: x['tags'].append(row[1])
            out.append(ok)
        elif op == 'removeTag':
            x = notes.get(row[0]); ok = x is not None and row[1] in x['tags']
            if ok: x['tags'].remove(row[1])
            out.append(ok)
        elif op == 'getNotesByTag': out.append(sorted((i for i, x in notes.items() if row[0] in x['tags']), key=num))
        else:
            x = notes.get(row[0]); out.append(0 if x is None else len(x['h']))
    return out


def ref_pkv(uid, calls):
    data, out = {}, [None]
    for op, row in calls:
        if op == 'set': data[row[0]] = row[1]; out.append(None)
        elif op == 'get': out.append(data.get(row[0], ''))
        elif op == 'delete': out.append(data.pop(row[0], None) is not None)
        elif op == 'save': out.append(pkv_encode(uid, list(data.items())))
        else:
            try: pairs = pkv_decode(uid, row[0])
            except ValueError: out.append(False); continue
            data = dict(pairs); out.append(None if uid == PKV1 else True)
    return out


def cents(a):
    whole, _, frac = a.partition('.')
    return int(whole) * 100 + int((frac + '00')[:2])


def ref_qpg(records, filters, size, page):
    lo_t, hi_t, lo_a, hi_a, user, cur = filters
    keep = []
    for r in records:
        if lo_t and int(r[0]) < int(lo_t) or hi_t and int(r[0]) > int(hi_t): continue
        if lo_a and cents(r[4]) < cents(lo_a) or hi_a and cents(r[4]) > cents(hi_a): continue
        if user and r[2] != user or cur and r[3] != cur: continue
        i = len(keep)
        while i > 0 and int(keep[i - 1][0]) > int(r[0]): i -= 1
        keep.insert(i, list(r))
    return keep[(page - 1) * size: page * size]


def ref_rlm(uid, args, calls):
    limit, ttl = args[1][0]; accepted, out = [], [None]
    for _, row in calls:
        key = row[0] if uid == RLM2 else ''; t = row[-1]
        n = sum(1 for k, s in accepted if k == key and s > t - ttl)
        out.append(n < limit)
        if n < limit: accepted.append((key, t))
    return out


def ref_rft(calls):
    files, out = [], [None]
    for op, row in calls:
        if op == 'storeFile': files.append((row[0], row[1])); out.append(None)
        elif op == 'returnAllFiles': out.append([f for f, _ in files])
        else:
            order = sorted(files, key=lambda x: x[0])
            order = sorted(order, key=lambda x: x[1], reverse=True)
            out.append([f for f, _ in order[:row[0]]])
    return out


def ref_rms(uid, calls):
    recipes, n, out = {}, 0, [None]
    def num(i): return int(i[6:])
    def clash(name, me):
        return any(x['name'].lower() == name.lower() for i, x in recipes.items() if i != me)
    for op, row in calls:
        if op == 'addRecipe':
            if clash(row[0], None): out.append(''); continue
            n += 1; recipes['recipe%d' % n] = {'name': row[0], 'ing': list(row[1]), 'steps': list(row[2]), 'ratings': []}
            out.append('recipe%d' % n)
        elif op == 'getRecipe':
            x = recipes.get(row[0]); out.append([] if x is None else [x['name'], list(x['ing']), list(x['steps'])])
        elif op == 'updateRecipe':
            x = recipes.get(row[0])
            if x is None or clash(row[1], row[0]): out.append(False); continue
            x.update(name=row[1], ing=list(row[2]), steps=list(row[3])); out.append(True)
        elif op == 'deleteRecipe': out.append(recipes.pop(row[0], None) is not None)
        elif op == 'searchByIngredient':
            out.append(sorted((i for i, x in recipes.items() if any(g.lower() == row[0].lower() for g in x['ing'])), key=num))
        elif op == 'rateRecipe':
            x = recipes.get(row[0])
            if x is not None: x['ratings'].append(row[1])
            out.append(x is not None)
        elif op == 'getTopRated':
            from fractions import Fraction
            rated = [i for i, x in recipes.items() if x['ratings']]
            rated.sort(key=lambda i: (-Fraction(sum(recipes[i]['ratings']), len(recipes[i]['ratings'])), num(i)))
            out.append(rated[:row[0]])
        else:
            p = row[0].lower()
            hits = [i for i, x in recipes.items() if x['name'].lower().startswith(p)]
            out.append(sorted(hits, key=lambda i: recipes[i]['name'].lower()))
    return out


def ref_rbf(args, calls):
    cap = args[1][0][0]; stream, read, unread, out = '', 0, 0, [None]
    for op, row in calls:
        if op == 'write':
            stream += row[0]; unread = min(cap, unread + len(row[0])); out.append(None)
        else:
            m = min(row[0], unread); got = []
            for j in range(m):
                cell = (read + j) % cap
                i = len(stream) - 1 - ((len(stream) - 1 - cell) % cap)  # last stream index stored in this cell
                got.append(stream[i])
            read += m; unread -= m; out.append(''.join(got))
    return out


def ref_sqn(calls):
    levels, out = {}, [None]
    def top(lv):
        return max((i for i, c in enumerate(lv) if c), default=-1)
    for op, row in calls:
        lv = levels.setdefault(row[0], [])
        if op == 'hideNuts':
            left, i = row[1], 0
            while left:
                if i == len(lv): lv.append(0)
                cap = 1 if i == 0 else 2 if i == 1 else None
                if cap is None:  # Fibonacci capacities 1, 2, 3, 5, 8, ...
                    a, b = 1, 2
                    for _ in range(i - 1): a, b = b, a + b
                    cap = b
                take = min(left, cap - lv[i]); lv[i] += take; left -= take; i += 1
            out.append(top(lv))
        elif op == 'retrieveNuts':
            left, got = row[1], 0
            for i in range(len(lv) - 1, -1, -1):
                take = min(left, lv[i]); lv[i] -= take; left -= take; got += take
            out.append(got)
        else: out.append(top(lv))
    return out


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid == CSS:
        budget(len(args[1]) <= 300); return ref_css(*args)
    if uid in (CG1, CG2, CG3): return ref_cg(uid, args)
    if uid == QPG:
        budget(len(args[0]) <= 400); return ref_qpg(*args)
    calls = trace(uid, args)
    budget(len(calls) <= 600)
    if uid in (TKV1, TKV2): return ref_tkv(uid, calls)
    if uid in (CEV1, CEV2): return ref_cev(uid, args, calls)
    if uid in (CBS1, CBS2): return ref_cbs(uid, calls)
    if uid == DTS: return ref_dts(calls)
    if uid == SQL: return ref_sql(calls)
    if uid in KVR: return ref_kvr(uid, calls)
    if uid in NTS: return ref_nts(uid, calls)
    if uid in (PKV1, PKV2): return ref_pkv(uid, calls)
    if uid in (RLM1, RLM2): return ref_rlm(uid, args, calls)
    if uid == RFT: return ref_rft(calls)
    if uid in RMS: return ref_rms(uid, calls)
    if uid == RBF:
        budget(sum(len(r[0]) for o, r in calls if o == 'write') <= 20000); return ref_rbf(args, calls)
    budget(sum(r[1] for o, r in calls if o == 'hideNuts') <= 10**6)
    return ref_sqn(calls)
