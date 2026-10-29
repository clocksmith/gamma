import copy
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import time
import unittest
HERE = Path(__file__).parent


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, file); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


_o = _load('gamma_h2h10a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h10a_reference_test_cases', HERE / 'cases.py')
reference, validate_domain = _o.reference, _o.validate_domain
CONTRACTS = {row['uid']: row for row in json.loads((HERE / 'contracts.json').read_text())['problems']}


def stem(uid): return uid.split(':', 1)[1]


def exact(a, b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(map(exact, a, b))
    if type(a) is dict: return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    return a == b


def ops(name, ctor, calls): return _c._ops(name, ctor, calls)


def depth(v):
    """Nesting depth of a JSON value (a scalar is 0)."""
    best, stack = 0, [(v, 1)]
    while stack:
        x, d = stack.pop()
        if isinstance(x, (list, dict)):
            best = max(best, d)
            stack.extend((y, d + 1) for y in (x.values() if isinstance(x, dict) else x))
    return best




class References(unittest.TestCase):
    """Hand-worked examples for each inferred spec (worked by the author, not taken from the source)."""
    def test_css(self):
        self.assertEqual(reference(_o.CSS, ['hlabcdefgijkmnopqrstuvwxyz', ['leetcode', 'hello']]), ['hello', 'leetcode'])
        self.assertEqual(reference(_o.CSS, ['ba', ['a', 'ab', '', 'b', 'ba', 'a']]), ['', 'b', 'ba', 'a', 'a', 'ab'])
        self.assertEqual(reference(_o.CSS, ['zyx', ['zz', 'z', 'zx', 'xz']]), ['z', 'zz', 'zx', 'xz'])

    def test_tkv(self):
        base = [('set', 'a', 'x', 1), ('set', 'a', 'y', 4), ('get', 'a', 3), ('get', 'a', 4), ('set', 'a', 'z', 4), ('get', 'a', 4)]
        self.assertEqual(reference(_o.TKV1, ops('TemporalKVStore', [], base + [('remove', 'a'), ('get', 'a', 5), ('remove', 'a')])),
                         [None, None, None, 'x', 'y', None, 'z', True, '', False])
        self.assertEqual(reference(_o.TKV2, ops('TemporalKVStore', [], base + [('remove', 'a', 6), ('get', 'a', 5), ('get', 'a', 6), ('remove', 'a', 7), ('set', 'a', 'w', 8), ('get', 'a', 9)])),
                         [None, None, None, 'x', 'y', None, 'z', True, 'z', '', False, None, 'w'])

    def test_cev(self):
        calls = [('put', 'a', '1', 3), ('put', 'b', '2', 1), ('put', 'c', '3', 2), ('get', 'b'), ('get', 'a'), ('put', 'a', '4', 0), ('put', 'd', '5', 9), ('get', 'a'), ('get', 'c')]
        self.assertEqual(reference(_o.CEV1, ops('RankedCache', [2], calls)), [None, None, None, None, '', '1', None, None, '', '3'])
        self.assertEqual(reference(_o.CEV1, ops('RankedCache', [2], [('put', 'a', '1', 0), ('put', 'b', '2', 0), ('put', 'a', '3', 0), ('put', 'c', '4', 0), ('get', 'a'), ('get', 'b')])),
                         [None, None, None, None, None, '3', ''])  # equal ranks: the oldest write (b) goes
        t = ops('RankedCache', [1, [['a', 'sa', 5], ['z', 'sz', -1]]], [('get', 'z'), ('get', 'a'), ('get', 'z'), ('getLoadCount',), ('put', 'q', 'w', -5), ('get', 'q'), ('get', 'zz')])
        self.assertEqual(reference(_o.CEV2, t), [None, 'sz', 'sa', 'sz', 3, None, 'w', ''])

    def test_cg(self):
        self.assertEqual(reference(_o.CG1, [['KS', 'KH', 'KD', 'AS', '2S', 'AH']]), [['KS', 'KD', '2S'], ['KH', 'AS', 'AH'], 2])
        self.assertEqual(reference(_o.CG1, [['10S', '10H', 'JS', 'JH', '9D', '9C']]), [['10S', 'JS', '9D'], ['10H', 'JH', '9C'], 0])
        self.assertEqual(reference(_o.CG1, [['4S', '4H', '5S', '5H', '6S', '7C']]), [['4S', '5S', '6S'], ['4H', '5H', '7C'], 2])
        self.assertEqual(reference(_o.CG2, [['4S', '4H', '5S', '5H', '6S', '7C']]), [['4S', '5S', '6S'], ['4H', '5H', '7C'], 1])  # straight flush
        self.assertEqual(reference(_o.CG2, [['AS', 'AH', '2S', '2H', '3S', '3H']]), [['AS', '2S', '3S'], ['AH', '2H', '3H'], 0])  # A-2-3 is not a straight; both flushes
        self.assertEqual(reference(_o.CG2, [['QS', '2D', 'KH', '2C', 'AS', '2H']]), [['QS', 'KH', 'AS'], ['2D', '2C', '2H'], 2])  # trips beat a straight
        self.assertEqual(reference(_o.CG3, [3, ['5S', '5H', '9C', '5D', '5C', '9S', '7H', '7D', '9D']]), [[['5S', '5D', '7H'], ['5H', '5C', '7D'], ['9C', '9S', '9D']], [3]])
        self.assertEqual(reference(_o.CG3, [2, ['2S', '2H', '3S', '3H', '4S', '4H']]), [[['2S', '3S', '4S'], ['2H', '3H', '4H']], [1, 2]])

    def test_cbs(self):
        t = ops('ChatApp', [], [('addBot', 'E', 'echo'), ('addBot', 'C', 'count'), ('addBot', 'E', 'reverse'), ('addBot', 'X', 'joke'), ('sendMessage', 'ann', '/echo hi'),
                                ('sendMessage', 'bo', '/count'), ('getRecentMessages', 10), ('getRecentMessages', 1), ('getRecentMessages', 0)])
        self.assertEqual(reference(_o.CBS1, t), [None, True, True, False, False, None, None, ['ann: /echo hi', 'E: hi', 'bo: /count', 'C: 2'], ['C: 2'], []])
        t = ops('ChatApp', [], [('sendMessage', 'g', 'a', 'x'), ('createChannel', 'g'), ('createChannel', 'g'), ('addBot', 'g', 'R', 'reverse'), ('addBot', 'h', 'R', 'reverse'),
                                ('sendMessage', 'g', 'a', '/reverse abc'), ('getRecentMessages', 'g', 5), ('getRecentMessages', 'h', 5)])
        self.assertEqual(reference(_o.CBS2, t), [None, False, True, False, True, False, True, ['a: /reverse abc', 'R: cba'], []])

    def test_dts(self):
        t = ops('DelayedTaskScheduler', [], [('schedule', 'a', 5, 0), ('schedule', 'b', 2, 1), ('schedule', 'c', 4, 1), ('runDue', 3), ('cancel', 'c'), ('cancel', 'b'),
                                             ('runDue', 5), ('schedule', 'd', 0, 5), ('schedule', 'e', 0, 5), ('runDue', 5)])
        self.assertEqual(reference(_o.DTS, t), [None, 5, 3, 5, ['b'], True, False, ['a'], 5, 5, ['d', 'e']])

    def test_sql(self):
        t = ops('SQLManager', [], [('createTable', 'emp', ['name', 'age']), ('insert', 'emp', ['bob', '30']), ('insert', 'emp', ['al', '7']), ('insert', 'emp', ['cy', 'old']),
                                   ('insert', 'emp', ['dee', '30']), ('insert', 'emp', ['x']), ('select', 'emp', [['age', '>=', '10']], 'name', False), ('select', 'emp', [], 'age', True),
                                   ('select', 'emp', [['age', '=', 'x']], '', True), ('select', 'emp', [['name', '<', 'c']], '', True), ('select', 'emp', [], 'zzz', True)])
        self.assertEqual(reference(_o.SQL, t), [None, None, True, True, False, True, False, [['dee', '30'], ['bob', '30']], [['al', '7'], ['bob', '30'], ['dee', '30']], [],
                                                [['bob', '30'], ['al', '7']], []])
        t = ops('SQLManager', [], [('createTable', 't', ['v']), ('insert', 't', ['9']), ('insert', 't', ['10']), ('insert', 't', ['-0']), ('select', 't', [['v', '<', '10']], 'v', False)])
        self.assertEqual(reference(_o.SQL, t), [None, None, True, True, False, [['9']]])  # numeric, not string, comparison; -0 is a string

    def test_kvr(self):
        t = [('set', 'a', '1'), ('get', 'a'), ('unset', 'a'), ('get', 'a'), ('unset', 'zz')]
        self.assertEqual(reference(_o.KVR1, ops('KeyValueStore', [], t)), [None, None, '1', None, '', None])
        t2 = t + [('rollback',), ('set', 'a', '1'), ('begin',), ('set', 'a', '2'), ('begin',), ('unset', 'a'), ('get', 'a'), ('rollback',), ('get', 'a'), ('commit',), ('get', 'a'), ('commit',)]
        self.assertEqual(reference(_o.KVR2, ops('KeyValueStore', [], t2)), [None, None, '1', None, '', None, False, None, None, None, None, None, '', True, '2', True, '2', False])
        t3 = [('set', 'a', 'x'), ('set', 'b', 'x'), ('count', 'x'), ('begin',), ('set', 'a', 'y'), ('count', 'x'), ('begin',), ('unset', 'b'), ('count', 'x'), ('rollback',), ('count', 'x'), ('rollback',), ('count', 'x')]
        self.assertEqual(reference(_o.KVR3, ops('KeyValueStore', [], t3)), [None, None, None, 2, None, None, 1, None, None, 0, True, 1, True, 2])

    def test_nts(self):
        base = [('createNote', 'Plan', 'buy milk', 1), ('createNote', 'Todo', 'plan trip', 2), ('getNote', 'note1'), ('updateNote', 'note1', 'Plan A', 'milk', 3),
                ('getNote', 'note1'), ('deleteNote', 'note2'), ('deleteNote', 'note2'), ('createNote', 'z', 'Z', 4)]
        exp = [None, 'note1', 'note2', ['Plan', 'buy milk', 1, 1], True, ['Plan A', 'milk', 1, 3], True, False, 'note3']
        self.assertEqual(reference(_o.NTS1, ops('SecondBrainSystem', [], base)), exp)
        s = [('createNote', 'zz', 'PLANS', 4), ('searchNotes', 'plan')]
        self.assertEqual(reference(_o.NTS2, ops('SecondBrainSystem', [], base + s)), exp + ['note4', ['note4', 'note1']])
        tg = [('addTag', 'note3', 'w'), ('addTag', 'note3', 'w'), ('addTag', 'note2', 'w'), ('addTag', 'note1', 'w'), ('getNotesByTag', 'w'), ('deleteNote', 'note1'), ('getNotesByTag', 'w')]
        self.assertEqual(reference(_o.NTS3, ops('SecondBrainSystem', [], base + tg)), exp + [True, False, False, True, ['note1', 'note3'], True, ['note3']])
        v = [('getVersionCount', 'note1'), ('revertNote', 'note1', 1, 9), ('getNote', 'note1'), ('getVersionCount', 'note1'), ('revertNote', 'note1', 4, 9), ('revertNote', 'note1', 0, 9)]
        self.assertEqual(reference(_o.NTS4, ops('SecondBrainSystem', [], base + v)), exp + [2, True, ['Plan', 'buy milk', 1, 9], 3, False, False])

    def test_pkv(self):
        blob = [0, 0, 0, 2, 0, 0, 0, 1, 97, 0, 0, 0, 3, 111, 110, 101, 0, 0, 0, 1, 98, 0, 0, 0, 3, 116, 119, 111]  # {a: one, b: two}
        self.assertEqual(reference(_o.PKV1, ops('PersistentKVStore', [], [('set', 'b', 'two'), ('set', 'a', 'one'), ('save',), ('delete', 'a'), ('load', blob), ('get', 'a')])),
                         [None, None, None, blob, True, None, 'one'])
        b2 = [80, 75, 86, 50] + blob + [0, 0, 3, 105]  # body byte sum 873 = 3 * 256 + 105
        self.assertEqual(sum(blob), 873)
        t = ops('PersistentKVStore', [], [('set', 'b', 'two'), ('set', 'a', 'one'), ('save',), ('set', 'c', 'q'), ('load', b2[:-1] + [106]), ('get', 'c'), ('load', b2), ('get', 'c'), ('load', [])])
        self.assertEqual(reference(_o.PKV2, t), [None, None, None, b2, None, False, 'q', True, '', False])

    def test_qpg(self):
        recs = [['5', 'a', 'u1', 'USD', '10.5'], ['3', 'b', 'u2', 'EUR', '3'], ['5', 'c', 'u1', 'USD', '7.25'], ['1', 'd', 'u1', 'USD', '100']]
        none = ['', '', '', '', '', '']
        self.assertEqual(reference(_o.QPG, [recs, none, 2, 2]), [recs[0], recs[2]])
        self.assertEqual(reference(_o.QPG, [recs, ['2', '', '7.25', '10.50', 'u1', 'USD'], 10, 1]), [recs[0], recs[2]])
        self.assertEqual(reference(_o.QPG, [recs, none, 3, 3]), [])

    def test_rlm(self):
        t = ops('RateLimiter', [2, 10], [('allowRequest', x) for x in (0, 1, 2, 9, 10, 11, 11, 20)])
        self.assertEqual(reference(_o.RLM1, t), [None, True, True, False, False, True, True, False, True])
        t = ops('RateLimiter', [1, 5], [('allowRequest', 'a', 0), ('allowRequest', 'b', 0), ('allowRequest', 'a', 4), ('allowRequest', 'a', 5)])
        self.assertEqual(reference(_o.RLM2, t), [None, True, True, False, True])

    def test_rft(self):
        t = ops('FileStorageSystem', [], [('getKthRecentFiles', 3), ('storeFile', 'b.txt', '2024-03-01'), ('storeFile', 'a.txt', '2024-03-01'), ('storeFile', 'c.txt', '2025-01-01'),
                                          ('storeFile', 'd.txt', '2023-01-01'), ('getKthRecentFiles', 2), ('getKthRecentFiles', 9), ('returnAllFiles',)])
        self.assertEqual(reference(_o.RFT, t), [None, [], None, None, None, None, ['c.txt', 'a.txt'], ['c.txt', 'a.txt', 'b.txt', 'd.txt'], ['b.txt', 'a.txt', 'c.txt', 'd.txt']])

    def test_rms(self):
        base = [('addRecipe', 'Pancakes', ['Flour', 'Egg'], ['Mix', 'Fry']), ('addRecipe', 'PANCAKES', [], []), ('addRecipe', 'Omelet', ['egg'], ['Beat']),
                ('updateRecipe', 'recipe2', 'pancakes', [], []), ('updateRecipe', 'recipe2', 'OMELET', ['EGG'], []), ('getRecipe', 'recipe2'), ('deleteRecipe', 'recipe1'), ('addRecipe', 'pancakes', [], [])]
        exp = [None, 'recipe1', '', 'recipe2', False, True, ['OMELET', ['EGG'], []], True, 'recipe3']
        self.assertEqual(reference(_o.RMS1, ops('RecipeManager', [], base)), exp)
        self.assertEqual(reference(_o.RMS2, ops('RecipeManager', [], base + [('searchByIngredient', 'egg'), ('searchByIngredient', 'flour')])), exp + [['recipe2'], []])
        r = [('rateRecipe', 'recipe2', 4), ('rateRecipe', 'recipe3', 5), ('rateRecipe', 'recipe3', 2), ('rateRecipe', 'recipe1', 5), ('getTopRated', 5), ('rateRecipe', 'recipe3', 5), ('getTopRated', 1)]
        self.assertEqual(reference(_o.RMS3, ops('RecipeManager', [], base + r)), exp + [True, True, True, False, ['recipe2', 'recipe3'], True, ['recipe2']])  # 4 = 4 ties: lower id
        self.assertEqual(reference(_o.RMS4, ops('RecipeManager', [], base + [('listByNamePrefix', ''), ('listByNamePrefix', 'O')])), exp + [['recipe2', 'recipe3'], ['recipe2']])

    def test_rbf(self):
        t = ops('RingBuffer', [4], [('read', 3), ('write', 'abc'), ('read', 2), ('write', 'defg'), ('read', 10), ('write', 'hi'), ('read', 1), ('read', 5)])
        # after 'defg' the cells are [e f g d], unread 4, read pointer 2 -> 'gdef' (pointer back at 2);
        # 'hi' lands in cells 3 and 0 while the read pointer stays at 2, so the next byte read is the stale 'g'
        self.assertEqual(reference(_o.RBF, t), [None, '', None, 'ab', None, 'gdef', None, 'g', 'h'])
        self.assertEqual(reference(_o.RBF, ops('RingBuffer', [3], [('write', 'abcdefgh'), ('read', 2), ('read', 9)])), [None, None, 'gh', 'f'])

    def test_sqn(self):
        t = ops('SquirrelResearch', [], [('getHighestLevel', 'oak'), ('hideNuts', 'oak', 1), ('hideNuts', 'oak', 2), ('hideNuts', 'oak', 3), ('hideNuts', 'oak', 1),
                                         ('retrieveNuts', 'oak', 4), ('getHighestLevel', 'oak'), ('retrieveNuts', 'oak', 10), ('getHighestLevel', 'oak'), ('hideNuts', 'elm', 0)])
        self.assertEqual(reference(_o.SQN, t), [None, -1, 0, 1, 2, 3, 4, 1, 3, -1, -1])
        for total in (1, 2, 3, 4, 6, 7, 11, 12, 19, 20, 1000):  # closed form used by the maximum rows
            self.assertEqual(reference(_o.SQN, ops('SquirrelResearch', [], [('hideNuts', 'a', total)]))[1], _c._fib_top(total))

    def test_domain(self):
        K = 'KeyValueStore'
        for uid, args in [(_o.CSS, ['aa', []]), (_o.CSS, ['ab', ['c']]), (_o.CSS, ['A', []]),
                          (_o.TKV1, ops('TemporalKVStore', [], [('set', 'a', 'x', 5), ('set', 'a', 'x', 4)])), (_o.TKV2, ops('TemporalKVStore', [], [('remove', 'a', 5), ('set', 'a', 'x', 4)])),
                          (_o.TKV1, ops('TemporalKVStore', [], [('get', 'a', 0)])), (_o.CEV1, ops('RankedCache', [0], [])), (_o.CEV2, ops('RankedCache', [1, [['a', 'b', 1], ['a', 'c', 2]]], [])),
                          (_o.CG1, [['2S', '2S', '3S', '4S', '5S', '6S']]), (_o.CG1, [['1S', '2S', '3S', '4S', '5S', '6S']]), (_o.CG3, [2, ['2S', '3S', '4S']]), (_o.CG3, [18, []]),
                          (_o.CBS1, ops('ChatApp', [], [('sendMessage', 'a b', 'x')])), (_o.CBS2, ops('ChatApp', [], [('addBot', 'g', 'B', 'Echo')])),
                          (_o.DTS, ops('DelayedTaskScheduler', [], [('schedule', 'a', 1, 5), ('runDue', 4)])), (_o.DTS, ops('DelayedTaskScheduler', [], [('schedule', 'a', 1, 5), ('schedule', 'a', 1, 5)])),
                          (_o.SQL, ops('SQLManager', [], [('createTable', 't', ['a', 'a'])])), (_o.SQL, ops('SQLManager', [], [('select', 't', [['a', '==', '1']], '', True)])),
                          (_o.SQL, ops('SQLManager', [], [('select', 't', [], '', 1)])), (_o.KVR1, ops(K, [], [('begin',)])), (_o.KVR2, ops(K, [], [('set', 'a', '')])),
                          (_o.NTS1, ops('SecondBrainSystem', [], [('createNote', 'a', 'b', 5), ('createNote', 'a', 'b', 4)])), (_o.NTS2, ops('SecondBrainSystem', [], [('searchNotes', '')])),
                          (_o.PKV1, ops('PersistentKVStore', [], [('load', [0, 0, 0, 1])])), (_o.PKV2, ops('PersistentKVStore', [], [('load', [256])])),
                          (_o.PKV1, ops('PersistentKVStore', [], [('set', 'a', '')])), (_o.QPG, [[['1', 'a', 'u', 'USD', '1.234']], ['', '', '', '', '', ''], 1, 1]),
                          (_o.QPG, [[['1', 'a', 'u', 'USD', '1'], ['2', 'a', 'u', 'USD', '1']], ['', '', '', '', '', ''], 1, 1]), (_o.QPG, [[], ['', '', '', '', '', ''], 0, 1]),
                          (_o.RLM1, ops('RateLimiter', [1, 1], [('allowRequest', 5), ('allowRequest', 4)])), (_o.RLM2, ops('RateLimiter', [0, 1], [])),
                          (_o.RFT, ops('FileStorageSystem', [], [('storeFile', 'a', '2024-02-30x')])), (_o.RFT, ops('FileStorageSystem', [], [('storeFile', 'a', '2024-01-01'), ('storeFile', 'a', '2024-01-02')])),
                          (_o.RMS1, ops('RecipeManager', [], [('addRecipe', 'x', ['a1'], [])])), (_o.RMS3, ops('RecipeManager', [], [('rateRecipe', 'recipe1', 6)])),
                          (_o.RBF, ops('RingBuffer', [0], [])), (_o.RBF, ops('RingBuffer', [1], [('write', '\n')])), (_o.SQN, ops('SquirrelResearch', [], [('hideNuts', 'a', -1)])),
                          (_o.SQN, ops('SquirrelResearch', [], [('hideNuts', 'a', 10**9)] * 100001))]:
            with self.assertRaises(ValueError, msg=str(args)[:80]): validate_domain(uid, args)

    def test_generated_cases_domain_valid_and_shallow(self):
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True):
                validate_domain(uid, row['args'])
                self.assertLessEqual(depth(row['args']), 200)

    def test_contract_layouts_match_classes(self):
        self.assertEqual(set(CONTRACTS), set(_o.IDS))
        for uid, row in CONTRACTS.items():
            self.assertEqual(row['spec_basis'], 'inferred')
            self.assertEqual(uid in _o.CLASSES, 'classname' in row['inferred_interface'])
            if uid in _o.CLASSES:
                name, ctor, methods, voids = _o.CLASSES[uid]
                iface = row['inferred_interface']
                self.assertEqual(iface['classname'], name)
                self.assertEqual(len(iface['constructor']['params']), ctor)
                self.assertEqual({m['name']: len(m['params']) for m in iface['methods']}, methods)
                self.assertEqual({m['name'] for m in iface['methods'] if m['return']['type'] == 'void'}, set(voids))

JS_RUNNER = r'''
const fs=require('fs');const job=JSON.parse(fs.readFileSync(0,'utf8'));const mod=require(job.path);const out=[];
for(const args of job.cases){const before=JSON.stringify(args);let value,native=null;const t0=process.cpuUsage();
 value=mod(...args);
 if(job.cls){const C=mod[job.cls];const r=new C(...args[1][0]);native=[null];
  for(let i=1;i<args[0].length;i++){let v=r[args[0][i]](...args[1][i]);if(job.voids.includes(args[0][i])){if(v!==undefined)throw Error('void returned value');v=null;}native.push(v);}}
 else native=mod[job.wrapper](...args);
 const t=process.cpuUsage(t0);
 out.push({value,native,unchanged:JSON.stringify(args)===before,cpu:(t.user+t.system)/1e6});}
process.stdout.write(JSON.stringify(out));'''
TIMES = {'python3': {}, 'node_jitless': {}}


class Candidates(unittest.TestCase):
    """Author-local self-check of own candidates against own generated cases; not isolated qualification."""
    def run_python(self, uid, rows):
        path = HERE / 'python' / f'{stem(uid)}.py'
        if not path.exists(): self.skipTest('candidate absent')
        module = _load(f'gamma_h2h10a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
        iface = CONTRACTS[uid]['inferred_interface']
        for row in rows:
            args = copy.deepcopy(row['args']); t0 = time.process_time(); value = module.solve(*args)
            if uid in _o.CLASSES:
                name, _, _, voids = _o.CLASSES[uid]
                receiver = getattr(module, name)(*args[1][0]); native = [None]
                for op, r in zip(args[0][1:], args[1][1:]):
                    v = getattr(receiver, op)(*r)
                    if op in voids: self.assertIsNone(v); v = None
                    native.append(v)
            else: native = getattr(module.Solution(), iface['name'])(*args)
            worst = max(worst, (time.process_time() - t0) / 2)
            self.assertTrue(exact(value, row['expected']) and exact(native, row['expected']), f'{uid} python {str(row["args"])[:100]}')
            self.assertEqual(args, row['args']); passed += 1
        TIMES['python3'][uid] = round(worst, 4)
        return passed

    def run_javascript(self, uid, rows):
        path = HERE / 'javascript' / f'{stem(uid)}.js'
        if not path.exists() or not shutil.which('node'): self.skipTest('candidate or node absent')
        cls = _o.CLASSES.get(uid)
        job = {'path': str(path), 'cases': [r['args'] for r in rows], 'cls': cls and cls[0], 'voids': list(cls[3]) if cls else [],
               'wrapper': None if cls else CONTRACTS[uid]['inferred_interface']['name']}
        flags = ['--jitless'] if os.environ.get('GAMMA_JITLESS', '1') == '1' else []
        res = subprocess.run(['node', *flags, '--stack-size=65500', '-e', JS_RUNNER], input=json.dumps(job), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr[-2000:])
        out = json.loads(res.stdout)
        for row, got in zip(rows, out):
            self.assertTrue(exact(got['value'], row['expected']) and exact(got['native'], row['expected']), f'{uid} javascript {str(row["args"])[:100]}')
            self.assertTrue(got['unchanged'])
        TIMES['node_jitless'][uid] = round(max(g['cpu'] for g in out) / 2, 4)
        self.assertEqual(len(out), len(rows)); return len(out)

    def test_candidates(self):
        only = os.environ.get('GAMMA_ONLY')
        for uid in _o.IDS:
            if only and only not in uid: continue
            rows = _c.build_cases(uid, include_maximum=True)
            for language, runner in [('python', self.run_python), ('javascript', self.run_javascript)]:
                with self.subTest(uid=uid, language=language):
                    print(f'{uid} {language} {runner(uid, rows)}/{len(rows)} passed', flush=True)
        print('HEAVIEST_CPU_SECONDS_PER_ENTRYPOINT ' + json.dumps(TIMES), flush=True)


if __name__ == '__main__': unittest.main()
