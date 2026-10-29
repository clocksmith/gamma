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


_o = _load('gamma_h2h17a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h17a_reference_test_cases', HERE / 'cases.py')
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
    def check(self, uid, pairs):
        for args, want in pairs:
            got = reference(uid, args)
            self.assertTrue(exact(got, want), f'{uid} {args} -> {got!r}, want {want!r}')

    def test_rpa(self):
        # n = 6: swaps (5,4) (4,2) (3,2) (2,1) (1,0) give [8,5,6,10,7,9]
        self.check(_o.RPA, [([[7], 1, []], [[7]]), ([[1, 2, 3, 4], 2, [0, 0, 0]], [[2, 3], [4, 1]]), ([[1, 2, 3, 4], 4, [3, 2, 1]], [[1], [2], [3], [4]]),
                            ([[5, 6, 7, 8, 9, 10], 3, [10**9, 7, 2, 1, 0]], [[8, 5], [6, 10], [7, 9]])])

    def test_rdg(self):
        self.check(_o.RDG, [([[3, 2, 1, 4, 5], 2, 6], 2), ([[9], 1, 1], 1), ([[1, 1, 1], 3, 2], 1), ([[5, 5, 5], 2, 10], 0), ([[10, 1, 1, 1], 2, 2], 1)])

    def test_rsq(self):
        t = ops('RoadwaySpeedTracker', [], [('getAverageSpeed', 0), ('addReport', 0, 10, 30), ('addReport', 5, 15, 50), ('getAverageSpeed', 4), ('getAverageSpeed', 5),
                                            ('getAverageSpeed', 10), ('getAverageSpeed', 15), ('addReport', 5, 6, 1), ('getAverageSpeed', 5), ('removeReport', 0, 10, 31),
                                            ('removeReport', 0, 10, 30), ('getAverageSpeed', 5), ('removeReport', 0, 10, 30)])
        self.check(_o.RSQ, [(t, [None, -1.0, None, None, 30.0, 40.0, 50.0, -1.0, None, 27.0, False, True, 25.5, False])])
        t = ops('RoadwaySpeedTracker', [], [('addReport', 0, 1, 1), ('addReport', 0, 1, 1), ('addReport', 0, 1, 2), ('getAverageSpeed', 0)])
        self.check(_o.RSQ, [(t, [None, None, None, None, 4 / 3])])

    def test_sss(self):
        self.check(_o.SSS, [([30, [5]], 20), ([100, []], 100), ([25, [0, 10, 20]], 0), ([12, [15, 3, 7]], 3), ([5, [5, 6]], 5), ([1, [0]], 0)])

    def test_sex(self):
        self.check(_o.SEX, [(['a'], 'a'), (['a-(b+c)'], 'a-b-c'), (['-(a-b)'], '-a+b'), (['a-(b-(c-d))'], 'a-b+c-d'), (['(a)+((b))'], 'a+b'), (['x-(-y+z)'], 'x+y-z'),
                            (['-a+(-(-b))'], '-a+b'), (['ab-(ab)'], 'ab-ab')])

    def test_slp(self):
        self.check(_o.SLP, [(['a'], 'a'), (['aba'], 'aba'), (['bab'], 'bab'), (['abba'], 'abba'), (['bbaabb'], 'abbbba'), (['zaz'], 'zaz'), (['azza'], 'azza'), (['zaaz'], 'azza'), (['cbaabc'], 'abccba'), (['bacab'], 'abcba')])

    def test_smp(self):
        self.check(_o.SMP, [([[1, 3, 2], [[0, 0, 0]], 0], [2]), ([[0, 0], [[2, 0], [0, 3]], 1], [0, 2]), ([[5, 1, 5], [[0, 4, 0], [0, 4, 0], [0, 0, 0]], 2], [2, 0, 2]),
                            ([[7], [[1], [2]], 5], [0, 0])])

    def test_str(self):
        t = ops('StockTracker', [], [('getRankedStocks',), ('recordTrade', 'AAPL', 5), ('recordTrade', 'MSFT', 7), ('getRankedStocks',), ('recordTrade', 'AAPL', 3),
                                     ('getRankedStocks',), ('getRankedStocks',), ('recordTrade', 'GOOG', 8), ('getRankedStocks',)])
        self.check(_o.STR, [(t, [None, [], None, None, ['MSFT', 'AAPL'], None, ['AAPL', 'MSFT'], ['AAPL', 'MSFT'], None, ['AAPL', 'GOOG', 'MSFT']])])

    def test_tok(self):
        self.check(_o.TOK, [(['abc', ['a:1', 'ab:2', 'abc:3']], ['3']), (['abcd', ['ab:7', 'bcd:9']], ['7', 'c', 'd']), (['', ['a:1']], []),
                            (['the cat', ['the:5', 'cat:6', 'ca:4']], ['5', ' ', '6']), (['aaa', ['aa:0']], ['0', 'a'])])

    def test_smt(self):
        self.check(_o.SMT, [([[1, 2, 1, 1, 3, 1], 0, 3], 0), ([[4, 4, 4], 2, 1], 0), ([[5, 6, 7], 1, 3], 0), ([[0, 1, 0, 1, 1], 1, 2], 3)])

    def test_smc(self):
        self.check(_o.SMC, [([[1, 3, 2, 3, 1], [0, 2, 4, 3]], [2, 1, 1, 1]), ([[5], [0, 0]], [1, 1]), ([[2, 2, 2], []], []), ([[-1, -2, -2], [1, 0]], [2, 1])])

    def test_logs(self):
        logs = ['p1:t1:5:start', 'p1:t1:3:boot:ok', 'p0:t9:7:', 'p1:T2:5:x', 'p1:t1:5:again', 'p10:t1:1:z']
        self.check(_o.TL1, [([logs], ['p0:t9:7:', 'p1:T2:5:x', 'p1:t1:3:boot:ok', 'p1:t1:5:start', 'p1:t1:5:again', 'p10:t1:1:z']), ([[]], []),
                            ([['a:b:10:x', 'a:b:9:y']], ['a:b:9:y', 'a:b:10:x'])])
        self.check(_o.TL2, [([logs], ['p0:t9:1:7:7', 'p1:T2:1:5:5', 'p1:t1:3:3:5', 'p10:t1:1:1:1']), ([[]], []), ([['a:b:10:x', 'a:b:9:y']], ['a:b:2:9:10'])])

    def test_tha(self):
        self.check(_o.THA, [([[2, 2, 2, 2, 5, 5, 5, 8], 3, 4], 3), ([[1], 2, 0], 0), ([[0, 0, 0], 1, 0], 3), ([[3, 4, 5], 3, 4], 1)])

    def test_tp(self):
        self.check(_o.TP1, [([['3,8', '5,1'], 6, 0, 20], [1, 2, 4, 6, 8]), ([[], 6, 17, 20], [18, 19, 20]), ([['2,3'], 3, 0, 4], [1, 3]), ([['1,0'], 1, 0, 2], [0])])
        self.check(_o.TP2, [([[], 6, 20], 4), ([['1,0', '2,0', '3,0'], 3, 10], -1), ([['2,19'], 2, 20], 2), ([['1,5', '5,0'], 1, 6], 2), ([[], 1, 1], 1)])

    def test_ttl(self):
        t = ops('MutexTaskLock', [], [('acquire', 1, 'gen'), ('acquire', 2, 'gen'), ('acquire', 3, 'score'), ('acquire', 4, 'gen'), ('acquire', 5, 'score'),
                                      ('release', 1), ('release', 2), ('release', 3), ('release', 4), ('acquire', 6, 'score'), ('release', 5), ('acquire', 7, 'gen')])
        self.check(_o.TTL, [(t, [None, True, True, False, False, False, [], [3], [4], [5], True, [], False])])

    def test_url(self):
        self.check(_o.URL, [(['http://x.com/m?year=100&type=action'], {'year': '100', 'type': 'action'}), (['/p'], {}),
                            (['/p?a=1&a=2&b&&=x&c=d=e'], {'a': ['1', '2'], 'b': '', 'c': 'd=e'}), (['?q?r=1'], {'q?r': '1'}), (['http://x.com/?'], {})])

    def test_domain(self):
        bad = [(_o.RPA, [[1, 2, 3], 2, [0, 0]]), (_o.RPA, [[1, 2], 1, []]), (_o.RPA, [[], 1, []]), (_o.RDG, [[1], 2, 5]), (_o.RDG, [[0], 1, 5]),
               (_o.RSQ, ops('RoadwaySpeedTracker', [], [('addReport', 5, 5, 1)])), (_o.RSQ, ops('RoadwaySpeedTracker', [], [('getAverageSpeed', 10**6 + 1)])),
               (_o.RSQ, ops('RoadwaySpeedTracker', [], [('addReport', 0, 1, 0)])), (_o.SSS, [0, []]), (_o.SSS, [5, [1, 1]]),
               (_o.SEX, ['a+']), (_o.SEX, ['()']), (_o.SEX, ['a--b']), (_o.SEX, ['(a']), (_o.SEX, ['a)']), (_o.SEX, ['+a']), (_o.SEX, ['a b']), (_o.SEX, ['a(b)']),
               (_o.SLP, ['ab']), (_o.SLP, ['']), (_o.SLP, ['Aa']), (_o.SMP, [[1], [[1, 2]], 0]), (_o.SMP, [[1], [], 0]), (_o.SMP, [[1], [[1001]], 0]),
               (_o.STR, ops('StockTracker', [], [('recordTrade', 'aapl', 1)])), (_o.STR, ops('StockTracker', [], [('recordTrade', 'A', 0)])),
               (_o.TOK, ['a', ['a:1', 'a:2']]), (_o.TOK, ['a', []]), (_o.TOK, ['A', ['a:1']]), (_o.TOK, ['a', ['a1']]),
               (_o.SMT, [[1], 1, 1]), (_o.SMT, [[1], 0, 2]), (_o.SMC, [[1], [1]]), (_o.SMC, [[], []]),
               (_o.TL1, [['a:b:01:x']]), (_o.TL1, [['a:b:x']]), (_o.TL2, [['a_b:c:1:x']]), (_o.TL2, [['a:b:1:\n']]),
               (_o.THA, [[1], 0, 1]), (_o.THA, [[-1], 1, 1]), (_o.TP1, [[], 6, 5, 5]), (_o.TP1, [['1,1'], 6, 0, 5]), (_o.TP1, [['1,2', '1,3'], 6, 0, 5]),
               (_o.TP2, [['0,2'], 6, 5]), (_o.TP2, [['5,2'], 6, 5]), (_o.TP2, [[], 13, 5]),
               (_o.TTL, ops('MutexTaskLock', [], [('acquire', 1, 'read')])), (_o.TTL, ops('MutexTaskLock', [], [('acquire', 1, 'gen'), ('acquire', 1, 'gen')])),
               (_o.TTL, ops('MutexTaskLock', [], [('release', 1)])), (_o.TTL, ops('MutexTaskLock', [], [('acquire', 1, 'gen'), ('acquire', 2, 'score'), ('release', 2)])),
               (_o.URL, ['a b']), (_o.URL, ['x?a=%20']), (_o.URL, ['x#y'])]
        for uid, args in bad:
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
            returns = [m['return']['type'] for m in row['inferred_interface'].get('methods', [])] or [row['inferred_interface']['return']['type']]
            self.assertEqual(uid in _o.FLOATS, 'float' in returns)
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


def agrees(got, expected):
    """JavaScript has no integral-float tag: where the expected value is a float, a JavaScript number compares by value; everything else exactly."""
    if type(expected) is float: return type(got) in (int, float) and got == expected
    if type(expected) is list: return type(got) is list and len(got) == len(expected) and all(map(agrees, got, expected))
    if type(expected) is dict: return type(got) is dict and got.keys() == expected.keys() and all(agrees(got[k], expected[k]) for k in got)
    return exact(got, expected)


def js_agrees(uid, got, expected):
    return agrees(got, expected) if uid in _o.FLOATS else exact(got, expected)


class Candidates(unittest.TestCase):
    """Author-local self-check of own candidates against own generated cases; not isolated qualification."""
    def run_python(self, uid, rows):
        path = HERE / 'python' / f'{stem(uid)}.py'
        if not path.exists(): self.skipTest('candidate absent')
        module = _load(f'gamma_h2h17a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
            self.assertTrue(js_agrees(uid, got['value'], row['expected']) and js_agrees(uid, got['native'], row['expected']), f'{uid} javascript {str(row["args"])[:100]}')
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
