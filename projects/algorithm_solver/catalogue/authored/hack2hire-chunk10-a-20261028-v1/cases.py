"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h10a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _times(rng, n, step=3):
    t, out = rng.randrange(1, 5), []
    for _ in range(n):
        t += rng.randrange(0, step); out.append(t)
    return out


def _css(rng):
    letters = list('abcdef'[:rng.randrange(1, 7)]); rng.shuffle(letters); order = ''.join(letters)
    return [order, [''.join(rng.choice(order) for _ in range(rng.randrange(0, 5))) for _ in range(rng.randrange(0, 12))]]


def _tkv(rng, uid):
    calls, ts = [], _times(rng, 40)
    for i in range(rng.randrange(1, 30)):
        k = rng.choice(['a', 'b', 'c']); r = rng.random()
        if r < 0.4: calls.append(('set', k, rng.choice(['x', 'y', 'z1']), ts[i]))
        elif r < 0.8: calls.append(('get', k, rng.randrange(1, ts[i] + 4)))
        elif uid == _o.TKV1: calls.append(('remove', k))
        else: calls.append(('remove', k, ts[i]))
    return _ops('TemporalKVStore', [], calls)


def _cev(rng, uid):
    keys = ['a', 'b', 'c', 'd', 'e', 'f']; calls = []
    for _ in range(rng.randrange(1, 30)):
        r = rng.random()
        if r < 0.5: calls.append(('put', rng.choice(keys), rng.choice(['v', 'w', 'x9']), rng.choice([-1, 0, 1, 2, 10**9])))
        elif r < 0.9 or uid == _o.CEV1: calls.append(('get', rng.choice(keys)))
        else: calls.append(('getLoadCount',))
    ctor = [rng.randrange(1, 4)]
    if uid == _o.CEV2:
        src = rng.sample(keys, rng.randrange(0, 5)); ctor.append([[k, 's' + k, rng.choice([-2, 0, 3])] for k in src])
    return _ops('RankedCache', ctor, calls)


DECK = [r + s for r in _o.RANKS for s in 'SHDC']


def _cg(rng, uid):
    if uid == _o.CG3:
        n = rng.randrange(2, 6); return [n, rng.sample(DECK, 3 * n)]
    if rng.random() < 0.5:  # bias toward equal ranks, straights and flushes
        ranks = rng.sample(_o.RANKS[:6], 3) if rng.random() < 0.5 else [rng.choice(_o.RANKS)] * 2 + [rng.choice(_o.RANKS)]
        pool = [r + s for r in set(ranks) for s in 'SHDC']
        if len(pool) >= 6: return [rng.sample(pool, 6)]
    return [rng.sample(DECK, 6)]


def _cbs(rng, uid):
    calls = []; texts = ['hi', '/echo yo', '/echo ', '/reverse abc', '/count', '/count ', '/reverse ', 'x/echo a']
    chans = ['g', 'h']
    for _ in range(rng.randrange(1, 25)):
        c = [rng.choice(chans)] if uid == _o.CBS2 else []
        r = rng.random()
        if uid == _o.CBS2 and r < 0.15: calls.append(('createChannel', rng.choice(chans)))
        elif r < 0.35: calls.append(tuple(['addBot'] + c + [rng.choice(['E', 'R', 'C', 'bot_1']), rng.choice(['echo', 'reverse', 'count', 'joke'])]))
        elif r < 0.8: calls.append(tuple(['sendMessage'] + c + [rng.choice(['ann', 'Bo']), rng.choice(texts)]))
        else: calls.append(tuple(['getRecentMessages'] + c + [rng.choice([0, 1, 2, 5, 100])]))
    return _ops('ChatApp', [], calls)


def _dts(rng):
    calls, t, n = [], 0, 0
    for _ in range(rng.randrange(1, 25)):
        t += rng.choice([0, 0, 1, 3]); r = rng.random()
        if r < 0.45: n += 1; calls.append(('schedule', 't%d' % n, rng.choice([0, 1, 2, 5]), t))
        elif r < 0.75: calls.append(('runDue', t))
        else: calls.append(('cancel', 't%d' % rng.randrange(1, n + 2)))
    return _ops('DelayedTaskScheduler', [], calls)


def _sql(rng):
    calls = [('createTable', 'p', ['a', 'b'])]
    if rng.random() < 0.5: calls.append(('createTable', 'q', ['x', 'y', 'z']))
    vals = ['1', '-2', '10', '0', 'ab', 'b', '-0', '007', 'z9']
    for _ in range(rng.randrange(1, 25)):
        t = rng.choice(['p', 'q', 'r']); r = rng.random()
        if r < 0.55: calls.append(('insert', t, [rng.choice(vals) for _ in range(rng.choice([2, 2, 3, 3, 1]))]))
        else:
            conds = [[rng.choice(['a', 'b', 'x', 'y', 'w']), rng.choice(_o.OPS), rng.choice(vals)] for _ in range(rng.randrange(0, 3))]
            calls.append(('select', t, conds, rng.choice(['', 'a', 'b', 'x', 'z', 'w']), rng.random() < 0.5))
    return _ops('SQLManager', [], calls)


def _kvr(rng, uid):
    calls = []; ops = ['set', 'set', 'get', 'unset']
    if uid != _o.KVR1: ops += ['begin', 'begin', 'rollback', 'commit']
    if uid == _o.KVR3: ops += ['count', 'count']
    for _ in range(rng.randrange(1, 30)):
        op = rng.choice(ops)
        if op == 'set': calls.append(('set', rng.choice('abc'), rng.choice(['1', '2', 'x'])))
        elif op in ('get', 'unset'): calls.append((op, rng.choice('abc')))
        elif op == 'count': calls.append(('count', rng.choice(['1', '2', 'x'])))
        else: calls.append((op,))
    return _ops('KeyValueStore', [], calls)


def _nts(rng, uid):
    calls, t, n = [], 1, 0; words = ['Plan', 'plan b', 'Todo', 'x', '', 'Shop list']
    ops = ['createNote', 'createNote', 'getNote', 'updateNote', 'deleteNote']
    if uid != _o.NTS1: ops += ['searchNotes']
    if uid in (_o.NTS3, _o.NTS4): ops += ['addTag', 'removeTag', 'getNotesByTag']
    if uid == _o.NTS4: ops += ['getVersionCount', 'revertNote']
    for _ in range(rng.randrange(1, 30)):
        op = rng.choice(ops); t += rng.choice([0, 1, 2]); nid = 'note%d' % rng.randrange(1, n + 2)
        if op == 'createNote': n += 1; calls.append((op, rng.choice(words), rng.choice(words), t))
        elif op == 'updateNote': calls.append((op, nid, rng.choice(words), rng.choice(words), t))
        elif op == 'revertNote': calls.append((op, nid, rng.randrange(0, 4), t))
        elif op == 'searchNotes': calls.append((op, rng.choice(['plan', 'PLAN', 'b', 'list', 'zz'])))
        elif op in ('addTag', 'removeTag'): calls.append((op, nid, rng.choice(['work', 'home'])))
        elif op == 'getNotesByTag': calls.append((op, rng.choice(['work', 'home'])))
        else: calls.append((op, nid))
    return _ops('SecondBrainSystem', [], calls)


def _pkv(rng, uid):
    calls = []; saved = [[0, 0, 0, 0] if uid == _o.PKV1 else _o.pkv_encode(uid, [])]
    for _ in range(rng.randrange(1, 25)):
        r = rng.random(); k = rng.choice(['a', 'b', 'k9'])
        if r < 0.35: calls.append(('set', k, rng.choice(['1', ' x~', 'hello world'])))
        elif r < 0.55: calls.append(('get', k))
        elif r < 0.65: calls.append(('delete', k))
        elif r < 0.8:
            calls.append(('save',))
            pairs = sorted(rng.sample([('a', 'q'), ('b', 'zz'), ('k9', '#')], rng.randrange(0, 4)))
            saved.append(_o.pkv_encode(uid, pairs))
        else:
            b = list(rng.choice(saved))
            if uid == _o.PKV2 and rng.random() < 0.5 and b:
                i = rng.randrange(len(b)); b[i] = (b[i] + rng.choice([1, 255])) % 256
                if rng.random() < 0.3: b = b[:rng.randrange(len(b))]
            calls.append(('load', b))
    return _ops('PersistentKVStore', [], calls)


def _qpg(rng):
    recs = [[str(rng.choice([0, 5, 9, 12])), 'i%d' % i, rng.choice(['u1', 'u2']), rng.choice(['USD', 'EUR']), rng.choice(['0', '5', '5.5', '5.05', '10.00', '99.99'])]
            for i in range(rng.randrange(0, 12))]
    f = [rng.choice(['', '0', '5', '9']), rng.choice(['', '9', '12']), rng.choice(['', '5', '5.05', '5.5']), rng.choice(['', '10', '10.0', '99']),
         rng.choice(['', 'u1']), rng.choice(['', 'USD', 'GBP'])]
    return [recs, f, rng.choice([1, 2, 3, 5]), rng.choice([1, 1, 2, 3])]


def _rlm(rng, uid):
    ts = _times(rng, 30, 4)
    calls = [tuple(['allowRequest'] + ([rng.choice(['a', 'b'])] if uid == _o.RLM2 else []) + [ts[i]]) for i in range(rng.randrange(1, 30))]
    return _ops('RateLimiter', [rng.randrange(1, 4), rng.choice([1, 2, 3, 5, 10**9])], calls)


def _rft(rng):
    calls, n = [], 0
    for _ in range(rng.randrange(1, 25)):
        r = rng.random()
        if r < 0.5: n += 1; calls.append(('storeFile', rng.choice(['a', 'b.txt', 'z_1']) + str(n), rng.choice(['2024-01-02', '2024-01-10', '2023-12-31'])))
        elif r < 0.85: calls.append(('getKthRecentFiles', rng.choice([1, 2, 3, 50])))
        else: calls.append(('returnAllFiles',))
    return _ops('FileStorageSystem', [], calls)


def _rms(rng, uid):
    calls, n = [], 0
    ops = ['addRecipe', 'addRecipe', 'getRecipe', 'updateRecipe', 'deleteRecipe']
    if uid != _o.RMS1: ops += ['searchByIngredient']
    if uid in (_o.RMS3, _o.RMS4): ops += ['rateRecipe', 'rateRecipe', 'getTopRated']
    if uid == _o.RMS4: ops += ['listByNamePrefix']
    names = ['Soup', 'soup', 'Pie', 'pie 2', 'Pasta']; ings = ['Salt', 'salt', 'egg', 'Flour']
    for _ in range(rng.randrange(1, 30)):
        op = rng.choice(ops); rid = 'recipe%d' % rng.randrange(1, n + 2)
        body = [rng.choice(names), rng.sample(ings, rng.randrange(0, 3)), rng.sample(['Mix.', 'Bake 20m', 'Serve'], rng.randrange(0, 3))]
        if op == 'addRecipe': n += 1; calls.append(tuple([op] + body))
        elif op == 'updateRecipe': calls.append(tuple([op, rid] + body))
        elif op == 'searchByIngredient': calls.append((op, rng.choice(ings + ['EGG', 'milk'])))
        elif op == 'rateRecipe': calls.append((op, rid, rng.randrange(1, 6)))
        elif op == 'getTopRated': calls.append((op, rng.choice([1, 2, 10])))
        elif op == 'listByNamePrefix': calls.append((op, rng.choice(['', 'p', 'PI', 'soup', 'x'])))
        else: calls.append((op, rid))
    return _ops('RecipeManager', [], calls)


def _rbf(rng):
    calls = []
    for _ in range(rng.randrange(1, 20)):
        if rng.random() < 0.5: calls.append(('write', ''.join(rng.choice('abcXYZ ~') for _ in range(rng.randrange(0, 9)))))
        else: calls.append(('read', rng.randrange(0, 9)))
    return _ops('RingBuffer', [rng.randrange(1, 7)], calls)


def _sqn(rng):
    calls = []
    for _ in range(rng.randrange(1, 20)):
        loc = rng.choice(['oak', 'elm']); r = rng.random()
        if r < 0.45: calls.append(('hideNuts', loc, rng.choice([0, 1, 2, 3, 5, 7, 20, 100])))
        elif r < 0.8: calls.append(('retrieveNuts', loc, rng.choice([0, 1, 2, 4, 50])))
        else: calls.append(('getHighestLevel', loc))
    return _ops('SquirrelResearch', [], calls)


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); o = _o; args = []
    if uid == o.CSS:
        args = [['abc', []], ['cba', ['a', 'b', 'c']], ['ba', ['a', 'ab', '', 'b', 'ba', 'a']], ['hlabcdefgijkmnopqrstuvwxyz', ['hello', 'leetcode']], ['zyx', ['zz', 'z', 'zx', 'xz']]]
        args += [_css(rng) for _ in range(250)]
    elif uid in (o.TKV1, o.TKV2):
        rm = ('remove', 'a') if uid == o.TKV1 else ('remove', 'a', 6)
        args = [_ops('TemporalKVStore', [], [('get', 'a', 5)]),
                _ops('TemporalKVStore', [], [('set', 'a', 'x', 1), ('set', 'a', 'y', 4), ('get', 'a', 3), ('get', 'a', 4), ('get', 'a', 1000), ('set', 'a', 'z', 4), ('get', 'a', 4), rm, ('get', 'a', 5), ('get', 'a', 6)])]
        args += [_tkv(rng, uid) for _ in range(250)]
    elif uid in (o.CEV1, o.CEV2):
        ctor = [2] if uid == o.CEV1 else [2, [['a', 'sa', 5], ['z', 'sz', -1]]]
        args = [_ops('RankedCache', ctor, [('put', 'a', '1', 3), ('put', 'b', '2', 1), ('put', 'c', '3', 2), ('get', 'b'), ('get', 'a'), ('put', 'a', '4', 0), ('put', 'd', '5', 9), ('get', 'a'), ('get', 'c')])]
        if uid == o.CEV2:
            args.append(_ops('RankedCache', ctor, [('get', 'z'), ('get', 'a'), ('get', 'z'), ('getLoadCount',), ('put', 'q', 'w', -5), ('get', 'z'), ('get', 'a'), ('getLoadCount',)]))
        args += [_cev(rng, uid) for _ in range(250)]
    elif uid in (o.CG1, o.CG2):
        args = [[['2S', '3S', '2H', '3H', '2D', 'AS']], [['KS', 'KH', 'KD', 'AS', '2S', 'AH']], [['10S', '10H', 'JS', 'JH', '9D', '9C']],
                [['4S', '4H', '5S', '5H', '6S', '7C']], [['QS', 'QH', 'KS', 'KD', 'AS', 'AD']], [['AS', 'AH', '2S', '2H', '3S', '3H']]]
        args += [_cg(rng, uid) for _ in range(250)]
    elif uid == o.CG3:
        args = [[2, ['2S', '3S', '2H', '3H', '2D', 'AS']], [3, ['AS', 'AH', 'AD', 'KS', 'KH', 'KD', 'QS', 'QH', 'QD']],
                [3, ['5S', '5H', '9C', '5D', '5C', '9S', '7H', '7D', '9D']], [17, DECK[:51]]]
        args += [_cg(rng, uid) for _ in range(250)]
    elif uid in (o.CBS1, o.CBS2):
        c = [] if uid == o.CBS1 else ['g']
        pre = [] if uid == o.CBS1 else [('createChannel', 'g'), ('createChannel', 'g')]
        args = [_ops('ChatApp', [], pre + [tuple(['addBot'] + c + ['E', 'echo']), tuple(['addBot'] + c + ['C', 'count']), tuple(['addBot'] + c + ['E', 'reverse']),
                                           tuple(['addBot'] + c + ['R', 'reverse']), tuple(['sendMessage'] + c + ['ann', '/echo hi there']),
                                           tuple(['sendMessage'] + c + ['bo', '/count']), tuple(['sendMessage'] + c + ['ann', '/reverse abc']),
                                           tuple(['getRecentMessages'] + c + [10]), tuple(['getRecentMessages'] + c + [2])])]
        if uid == o.CBS2: args.append(_ops('ChatApp', [], [('sendMessage', 'g', 'a', 'x'), ('getRecentMessages', 'g', 3), ('addBot', 'g', 'E', 'echo')]))
        args += [_cbs(rng, uid) for _ in range(250)]
    elif uid == o.DTS:
        args = [_ops('DelayedTaskScheduler', [], [('schedule', 'a', 5, 0), ('schedule', 'b', 2, 1), ('schedule', 'c', 4, 1), ('runDue', 3), ('cancel', 'c'), ('cancel', 'b'),
                                                  ('runDue', 5), ('schedule', 'd', 0, 5), ('runDue', 5), ('cancel', 'zz')])]
        args += [_dts(rng) for _ in range(250)]
    elif uid == o.SQL:
        args = [_ops('SQLManager', [], [('createTable', 'emp', ['name', 'age']), ('insert', 'emp', ['bob', '30']), ('insert', 'emp', ['al', '7']), ('insert', 'emp', ['cy', 'old']),
                                        ('insert', 'emp', ['dee', '30']), ('select', 'emp', [['age', '>=', '10']], 'name', False), ('select', 'emp', [], 'age', True),
                                        ('select', 'emp', [['age', '=', 'x']], '', True), ('select', 'emp', [['name', '<', 'c']], '', True), ('select', 'nope', [], '', True)])]
        args += [_sql(rng) for _ in range(250)]
    elif uid in o.KVR:
        base = [('set', 'a', '1'), ('get', 'a'), ('unset', 'a'), ('get', 'a'), ('unset', 'zz')]
        if uid != o.KVR1:
            base += [('rollback',), ('set', 'a', '1'), ('begin',), ('set', 'a', '2'), ('begin',), ('unset', 'a'), ('get', 'a'), ('rollback',), ('get', 'a'), ('commit',), ('get', 'a'), ('commit',)]
        if uid == o.KVR3: base += [('set', 'b', '2'), ('count', '2'), ('begin',), ('set', 'b', '1'), ('count', '2'), ('rollback',), ('count', '2')]
        args = [_ops('KeyValueStore', [], base)]
        args += [_kvr(rng, uid) for _ in range(250)]
    elif uid in o.NTS:
        base = [('createNote', 'Plan', 'buy milk', 1), ('createNote', 'Todo', 'plan trip', 2), ('getNote', 'note1'), ('updateNote', 'note1', 'Plan A', 'milk', 3),
                ('getNote', 'note1'), ('deleteNote', 'note2'), ('deleteNote', 'note2'), ('updateNote', 'note2', 'x', 'y', 4), ('getNote', 'note9'), ('createNote', 'z', 'Z', 4)]
        if uid != o.NTS1: base += [('searchNotes', 'PLAN'), ('searchNotes', 'z')]
        if uid in (o.NTS3, o.NTS4): base += [('addTag', 'note3', 'w'), ('addTag', 'note3', 'w'), ('addTag', 'note1', 'w'), ('getNotesByTag', 'w'), ('removeTag', 'note3', 'w'), ('getNotesByTag', 'w')]
        if uid == o.NTS4: base += [('getVersionCount', 'note1'), ('revertNote', 'note1', 1, 9), ('getNote', 'note1'), ('getVersionCount', 'note1'), ('revertNote', 'note1', 4, 9)]
        args = [_ops('SecondBrainSystem', [], base)]
        args += [_nts(rng, uid) for _ in range(250)]
    elif uid in (o.PKV1, o.PKV2):
        blob = o.pkv_encode(uid, [('k', 'v')])
        base = [('set', 'b', 'two'), ('set', 'a', 'one'), ('save',), ('delete', 'a'), ('delete', 'a'), ('load', blob), ('get', 'k'), ('get', 'b')]
        if uid == o.PKV2: base += [('load', blob[:-1] + [(blob[-1] + 1) % 256]), ('get', 'k'), ('load', [1, 2, 3])]
        args = [_ops('PersistentKVStore', [], base)]
        args += [_pkv(rng, uid) for _ in range(250)]
    elif uid == o.QPG:
        recs = [['5', 'a', 'u1', 'USD', '10.5'], ['3', 'b', 'u2', 'EUR', '3'], ['5', 'c', 'u1', 'USD', '7.25'], ['1', 'd', 'u1', 'USD', '100']]
        args = [[[], ['', '', '', '', '', ''], 1, 1], [recs, ['', '', '', '', '', ''], 2, 1], [recs, ['', '', '', '', '', ''], 2, 2], [recs, ['2', '', '7.25', '', 'u1', 'USD'], 10, 1],
                [recs, ['', '', '', '', '', ''], 3, 3]]
        args += [_qpg(rng) for _ in range(250)]
    elif uid in (o.RLM1, o.RLM2):
        k = [] if uid == o.RLM1 else ['a']
        args = [_ops('RateLimiter', [2, 10], [tuple(['allowRequest'] + k + [t]) for t in (0, 1, 2, 9, 10, 11, 11, 20)])]
        if uid == o.RLM2: args.append(_ops('RateLimiter', [1, 5], [('allowRequest', 'a', 0), ('allowRequest', 'b', 0), ('allowRequest', 'a', 4), ('allowRequest', 'a', 5)]))
        args += [_rlm(rng, uid) for _ in range(250)]
    elif uid == o.RFT:
        args = [_ops('FileStorageSystem', [], [('getKthRecentFiles', 3), ('returnAllFiles',), ('storeFile', 'b.txt', '2024-03-01'), ('storeFile', 'a.txt', '2024-03-01'),
                                               ('storeFile', 'c.txt', '2025-01-01'), ('storeFile', 'd.txt', '2023-01-01'), ('getKthRecentFiles', 2), ('getKthRecentFiles', 9), ('returnAllFiles',)])]
        args += [_rft(rng) for _ in range(250)]
    elif uid in o.RMS:
        base = [('addRecipe', 'Pancakes', ['Flour', 'Egg'], ['Mix', 'Fry']), ('addRecipe', 'PANCAKES', [], []), ('addRecipe', 'Omelet', ['egg'], ['Beat']),
                ('getRecipe', 'recipe1'), ('updateRecipe', 'recipe2', 'pancakes', [], []), ('updateRecipe', 'recipe2', 'Omelette', ['EGG', 'salt'], ['Beat', 'Cook']),
                ('getRecipe', 'recipe2'), ('deleteRecipe', 'recipe1'), ('getRecipe', 'recipe1'), ('addRecipe', 'Pancakes', ['egg'], ['x']), ('deleteRecipe', 'recipe9')]
        if uid != o.RMS1: base += [('searchByIngredient', 'Egg'), ('searchByIngredient', 'flour')]
        if uid in (o.RMS3, o.RMS4): base += [('rateRecipe', 'recipe2', 4), ('rateRecipe', 'recipe3', 5), ('rateRecipe', 'recipe3', 2), ('rateRecipe', 'recipe1', 5), ('getTopRated', 5), ('getTopRated', 1)]
        if uid == o.RMS4: base += [('listByNamePrefix', 'o'), ('listByNamePrefix', ''), ('listByNamePrefix', 'PAN')]
        args = [_ops('RecipeManager', [], base)]
        args += [_rms(rng, uid) for _ in range(250)]
    elif uid == o.RBF:
        args = [_ops('RingBuffer', [4], [('read', 3), ('write', 'abc'), ('read', 2), ('write', 'defg'), ('read', 10), ('write', 'hi'), ('read', 1), ('read', 5)]),
                _ops('RingBuffer', [3], [('write', 'abcdefgh'), ('read', 2), ('write', ''), ('read', 0), ('read', 9)])]
        args += [_rbf(rng) for _ in range(250)]
    elif uid == o.SQN:
        args = [_ops('SquirrelResearch', [], [('getHighestLevel', 'oak'), ('hideNuts', 'oak', 1), ('hideNuts', 'oak', 2), ('hideNuts', 'oak', 3), ('hideNuts', 'oak', 1),
                                              ('retrieveNuts', 'oak', 4), ('getHighestLevel', 'oak'), ('retrieveNuts', 'oak', 10), ('getHighestLevel', 'oak'), ('hideNuts', 'elm', 0)])]
        args += [_sqn(rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def _fib_top(total):
    """Highest occupied level for `total` nuts: smallest L with F(L+4) - 2 >= total (closed form of the Fibonacci prefix sums)."""
    if total == 0: return -1
    f = [0, 1]
    while len(f) < 200: f.append(f[-1] + f[-2])
    return next(L for L in range(190) if f[L + 4] - 2 >= total)


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []; n = 100000
    if uid == o.CSS:
        order = 'qwertyuiopasdfghjklzxcvbnm'
        def code(i): return ''.join(order[i // 26 ** p % 26] for p in range(3, -1, -1)) + order[0] * 6
        perm = list(range(20000)); random.Random(7).shuffle(perm)
        out.append(([order, [code(i) for i in perm]], [code(i) for i in range(20000)]))
        out.append(([order, [order[1] * (50 - i % 51) for i in range(4000)]], sorted([order[1] * (50 - i % 51) for i in range(4000)], key=len)))
    elif uid in (o.TKV1, o.TKV2):
        m = 50000
        calls = [('set', 'k%d' % (i % 100), 'v%d' % i, i + 1) for i in range(m)]
        if uid == o.TKV2: calls += [('remove', 'k%d' % x, m + 1) for x in range(100)]
        calls += [('get', 'k%d' % (j % 100), j + 1) for j in range(m - 200)]
        if uid == o.TKV1: calls += [('remove', 'k%d' % x) for x in range(100)] + [('get', 'k0', 10**9)]
        else: calls += [('get', 'k%d' % x, 10**9) for x in range(100)]
        exp = [None] * (m + 1) + ([True] * 100 if uid == o.TKV2 else []) + ['v%d' % j for j in range(m - 200)]
        exp += [True] * 100 + [''] if uid == o.TKV1 else [''] * 100
        out.append((_ops('TemporalKVStore', [], calls), exp))
    elif uid in (o.CEV1, o.CEV2):
        m = 49999
        if uid == o.CEV1:
            for rank in (lambda i: i, lambda i: 0):
                calls = [('put', 'k%d' % i, 'v%d' % i, rank(i)) for i in range(m)] + [('get', 'k%d' % j) for j in range(m)]
                out.append((_ops('RankedCache', [1000], calls), [None] * (m + 1) + ['v%d' % j if j >= m - 1000 else '' for j in range(m)]))
        else:
            src = [['k%d' % i, 'v%d' % i, i] for i in range(m)]
            calls = [('get', 'k%d' % i) for i in range(m)] + [('getLoadCount',), ('get', 'k%d' % (m - 1)), ('get', 'k0'), ('getLoadCount',)]
            out.append((_ops('RankedCache', [1000, src], calls), [None] + ['v%d' % i for i in range(m)] + [m, 'v%d' % (m - 1), 'v0', m + 1]))
    elif uid in (o.CBS1, o.CBS2):
        if uid == o.CBS1:
            calls = [('addBot', 'E', 'echo'), ('addBot', 'C', 'count')]; log = []
            for i in range(n - 4):
                t = '/echo m%d' % i if i % 2 == 0 else '/count'
                calls.append(('sendMessage', 'u', t)); log.append('u: ' + t); log.append('E: m%d' % i if i % 2 == 0 else 'C: %d' % (i + 1))
            calls += [('getRecentMessages', n), ('getRecentMessages', 3)]
            out.append((_ops('ChatApp', [], calls), [None, True, True] + [None] * (n - 4) + [log[-n:], log[-3:]]))
        else:
            calls = [('createChannel', 'c%d' % i) for i in range(1000)] + [('addBot', 'c%d' % i, 'R', 'reverse') for i in range(1000)]
            calls += [('sendMessage', 'c%d' % (i % 1000), 'u', '/reverse ab%d' % i) for i in range(97000)]
            calls += [('getRecentMessages', 'c%d' % i, 2) for i in range(1000)]
            last = {i % 1000: i for i in range(97000)}
            exp = [None] + [True] * 99000 + [['u: /reverse ab%d' % last[i], 'R: ' + ('ab%d' % last[i])[::-1]] for i in range(1000)]
            out.append((_ops('ChatApp', [], calls), exp))
    elif uid == o.DTS:
        m = 50000
        calls = [('schedule', 't%d' % i, m - i, i) for i in range(m)] + [('cancel', 't%d' % i) for i in range(10000)] + [('runDue', m - 1), ('runDue', m), ('cancel', 't20000')]
        out.append((_ops('DelayedTaskScheduler', [], calls), [None] + [m] * m + [True] * 10000 + [[], ['t%d' % i for i in range(10000, m)], False]))
        calls = []; exp = [None]
        for i in range(m // 2): calls += [('schedule', 'x%d' % i, 0, 7 * i), ('runDue', 7 * i)]; exp += [7 * i, ['x%d' % i]]
        out.append((_ops('DelayedTaskScheduler', [], calls), exp))
    elif uid == o.SQL:
        rows = 3000
        calls = [('createTable', 't', ['a', 'b', 'c'])] + [('insert', 't', [str(i), 'n%d' % (i % 7), str(-i)]) for i in range(rows)]
        calls += [('insert', 't', ['x', 'n1', '5']), ('insert', 't', ['1', '2', '3', '4'])]
        calls += [('select', 't', [['a', '>=', str(rows - 10)]], 'c', True) for _ in range(150)]
        calls += [('select', 't', [['b', '=', 'n3'], ['a', '<', '50']], 'a', False)]
        exp = [None, None] + [True] * rows + [False, False] + [[[str(i), 'n%d' % (i % 7), str(-i)] for i in range(rows - 1, rows - 11, -1)]] * 150
        exp += [[[str(i), 'n3', str(-i)] for i in range(49, -1, -1) if i % 7 == 3]]
        out.append((_ops('SQLManager', [], calls), exp))
    elif uid in o.KVR:
        if uid == o.KVR1:
            calls = [('set', 'k%d' % (i % 5000), 'v%d' % i) for i in range(50000)] + [('unset', 'k%d' % i) for i in range(0, 5000, 2)] + [('get', 'k%d' % (i % 5000)) for i in range(40000)]
            out.append((_ops('KeyValueStore', [], calls), [None] * 52501 + ['' if i % 2 == 0 else 'v%d' % (45000 + i % 5000) for i in range(40000)]))
        elif uid == o.KVR2:
            m = 30000
            calls = []
            for i in range(m): calls += [('begin',), ('set', 'k', 'v%d' % i)]
            calls += [('get', 'k')] + [('rollback',)] * m + [('get', 'k'), ('rollback',), ('commit',)]
            out.append((_ops('KeyValueStore', [], calls), [None] * (2 * m + 1) + ['v%d' % (m - 1)] + [True] * m + ['', False, False]))
        else:
            m = 30000
            calls = [('set', 'k%d' % i, 'x') for i in range(m)] + [('count', 'x'), ('begin',)] + [('set', 'k%d' % i, 'y') for i in range(10000)]
            calls += [('count', 'x'), ('count', 'y'), ('begin',), ('unset', 'k0'), ('count', 'y'), ('commit',), ('count', 'y'), ('rollback',), ('count', 'x')]
            out.append((_ops('KeyValueStore', [], calls), [None] * (m + 1) + [m, None] + [None] * 10000 + [m - 10000, 10000, None, None, 9999, True, 9999, False, m - 10000]))
    elif uid in o.NTS:
        m = 30000
        calls = [('createNote', 'A%05d' % i, 'body', i + 1) for i in range(m)] + [('getNote', 'note%d' % (i + 1)) for i in range(0, m, 3)]
        exp = [None] + ['note%d' % (i + 1) for i in range(m)] + [['A%05d' % i, 'body', i + 1, i + 1] for i in range(0, m, 3)]
        calls += [('updateNote', 'note1', 'A00000', 'u%d' % j, m + 1) for j in range(1000)] + [('deleteNote', 'note%d' % m), ('getNote', 'note1')]
        exp += [True] * 1000 + [True, ['A00000', 'u999', 1, m + 1]]
        if uid != o.NTS1:
            calls += [('searchNotes', 'BODY')] * 10 + [('searchNotes', 'a1234')]
            exp += [['note%d' % i for i in range(m - 1, 1, -1)]] * 10 + [['note%d' % (i + 1) for i in range(12349, 12339, -1)]]
        if uid in (o.NTS3, o.NTS4):
            calls += [('addTag', 'note%d' % (i + 1), 'even') for i in range(0, m, 2)] + [('getNotesByTag', 'even')] * 10
            exp += [True] * (m // 2) + [['note%d' % (i + 1) for i in range(0, m, 2)]] * 10
        if uid == o.NTS4:
            calls += [('getVersionCount', 'note1'), ('revertNote', 'note1', 1, m + 2), ('getNote', 'note1'), ('getVersionCount', 'note1'), ('getVersionCount', 'note%d' % m)]
            exp += [1001, True, ['A00000', 'body', 1, m + 2], 1002, 0]
        out.append((_ops('SecondBrainSystem', [], calls), exp))
    elif uid in (o.PKV1, o.PKV2):
        m = 20000
        pairs = [('k%05d' % i, 'value %d~' % i) for i in range(m)]
        calls = [('set', k, v) for k, v in reversed(pairs)] + [('save',), ('delete', 'k00000'), ('get', 'k00001')]
        blob = o.pkv_encode(uid, pairs)
        exp = [None] * (m + 1) + [blob, True, 'value 1~']
        small = o.pkv_encode(uid, [('z', 'last')])
        calls += [('load', small), ('get', 'k00001'), ('get', 'z'), ('load', blob), ('get', 'k00000')]
        exp += [None if uid == o.PKV1 else True, '', 'last', None if uid == o.PKV1 else True, 'value 0~']
        if uid == o.PKV2:
            bad = blob[:-1] + [(blob[-1] + 1) % 256]
            calls += [('load', bad), ('load', blob[:-5]), ('get', 'k19999')]; exp += [False, False, 'value 19999~']
        out.append((_ops('PersistentKVStore', [], calls), exp))
    elif uid == o.QPG:
        recs = [[str(i), 'id%d' % i, 'u%d' % (i % 10), 'USD' if i % 3 else 'EUR', '%d.%02d' % (i, i % 100)] for i in range(n)]
        hits = [r for r in recs if r[2] == 'u3' and r[3] == 'USD' and 1000 <= int(r[0]) <= 90000]
        out.append(([recs, ['1000', '90000', '', '', 'u3', 'USD'], 100, 5], hits[400:500]))
        rev = list(reversed(recs))
        out.append(([rev, ['', '', '500', '600.5', '', ''], 1000, 1], [r for r in recs if 500 <= int(r[0]) <= 600]))
        out.append(([rev, ['', '', '', '', '', ''], 100000, 1], recs))
    elif uid in (o.RLM1, o.RLM2):
        if uid == o.RLM1:
            out.append((_ops('RateLimiter', [3, 10], [('allowRequest', t) for t in range(n)]), [None] + [t % 10 < 3 for t in range(n)]))
            out.append((_ops('RateLimiter', [100000, 10**9], [('allowRequest', 5)] * n), [None] + [True] * n))
        else:
            out.append((_ops('RateLimiter', [3, 10], [('allowRequest', 'c%d' % (i % 100), i // 100) for i in range(n)]), [None] + [(i // 100) % 10 < 3 for i in range(n)]))
            out.append((_ops('RateLimiter', [1, 10**9], [('allowRequest', 'd%d' % (i % 50000), 7) for i in range(n)]), [None] + [i < 50000 for i in range(n)]))
    elif uid == o.RFT:
        m = 50000
        calls = [('storeFile', 'f%05d' % i, '2026-02-%02d' % (i % 28 + 1)) for i in range(m)] + [('getKthRecentFiles', 10)] * (m - 2) + [('returnAllFiles',)]
        out.append((_ops('FileStorageSystem', [], calls), [None] * (m + 1) + [['f%05d' % (27 + 28 * j) for j in range(10)]] * (m - 2) + [['f%05d' % i for i in range(m)]]))
        calls = [('storeFile', 'g%05d' % i, '1999-12-31' if i % 2 else '2000-01-01') for i in range(m)] + [('getKthRecentFiles', 100000)]
        out.append((_ops('FileStorageSystem', [], calls), [None] * (m + 1) + [['g%05d' % i for i in range(0, m, 2)] + ['g%05d' % i for i in range(1, m, 2)]]))
    elif uid in o.RMS:
        m = 20000
        calls = [('addRecipe', 'R%d' % i, ['salt', 'ing' + chr(97 + i % 10)], ['step']) for i in range(m)] + [('addRecipe', 'r5', [], [])]
        exp = [None] + ['recipe%d' % (i + 1) for i in range(m)] + ['']
        calls += [('getRecipe', 'recipe%d' % (i + 1)) for i in range(0, m, 2)]
        exp += [['R%d' % i, ['salt', 'ing' + chr(97 + i % 10)], ['step']] for i in range(0, m, 2)]
        if uid != o.RMS1:
            calls += [('searchByIngredient', 'SALT')] * 5 + [('searchByIngredient', 'INGH')]
            exp += [['recipe%d' % (i + 1) for i in range(m)]] * 5 + [['recipe%d' % (i + 1) for i in range(7, m, 10)]]
        if uid in (o.RMS3, o.RMS4):
            calls += [('rateRecipe', 'recipe%d' % (i + 1), i % 5 + 1) for i in range(m)] + [('getTopRated', 5)] * 20
            exp += [True] * m + [['recipe%d' % (i + 1) for i in (4, 9, 14, 19, 24)]] * 20
        if uid == o.RMS4:
            calls += [('listByNamePrefix', 'r1')] * 5
            exp += [sorted(('recipe%d' % (i + 1) for i in range(m) if str(i).startswith('1')), key=lambda r: str(int(r[6:]) - 1))] * 5
        out.append((_ops('RecipeManager', [], calls), exp))
    elif uid == o.RBF:
        chunk = ''.join(chr(32 + i % 95) for i in range(1000))
        calls = [('write', chunk)] * 100 + [('read', 1000)] * 100 + [('read', 5)]
        out.append((_ops('RingBuffer', [100000], calls), [None] * 101 + [chunk] * 100 + ['']))
        pat = 'abcdefg' * 14286
        calls = [('write', pat[:n]), ('read', 3), ('write', 'XYZ' * 30000), ('read', 100000)]
        # capacity 7: after the first write the cells hold the period 'abcdefg'; then 90000 more chars land at write offsets 100000 mod 7 = 5 onward
        stream = pat[:n] + 'XYZ' * 30000
        cells = [stream[len(stream) - 1 - ((len(stream) - 1 - c) % 7)] for c in range(7)]
        out.append((_ops('RingBuffer', [7], calls), [None, None, 'abc', None, ''.join(cells[(3 + j) % 7] for j in range(7))]))
    elif uid == o.SQN:
        total = (n - 4) * 10**9
        calls = [('hideNuts', 'a', 10**9)] * (n - 4) + [('getHighestLevel', 'a'), ('retrieveNuts', 'a', 10**9 - 1), ('getHighestLevel', 'a')]
        out.append((_ops('SquirrelResearch', [], calls), [None] + [_fib_top((i + 1) * 10**9) for i in range(n - 4)] + [_fib_top(total), 10**9 - 1, _fib_top(total - 10**9 + 1)]))
        calls = [('hideNuts', 'l%d' % i, i) for i in range(50000)] + [('retrieveNuts', 'l%d' % i, 10**9) for i in range(49999)]
        out.append((_ops('SquirrelResearch', [], calls), [None] + [_fib_top(i) for i in range(50000)] + list(range(49999))))
    return out
