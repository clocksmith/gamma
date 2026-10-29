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


_o = _load('gamma_h2h17b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h17b_reference_test_cases', HERE / 'cases.py')
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

    def test_urd(self):
        t = ops('Router', [], [('addRoute', '/users/*', 'anyUser'), ('addRoute', '/users/me', 'me'), ('addRoute', '/*/*', 'pair'), ('callRoute', '/users/me'),
                               ('callRoute', '/users/42'), ('callRoute', '/posts/7'), ('callRoute', '/users'), ('addRoute', '/', 'root'), ('callRoute', '/'),
                               ('addRoute', '/*/me', 'anyMe'), ('addRoute', '/users/me', 'me2'), ('callRoute', '/users/me'), ('callRoute', '/x/me')])
        # equal wildcard counts: the literal at the leftmost differing segment wins
        u = ops('Router', [], [('addRoute', '/*/b/*', 'x'), ('addRoute', '/a/*/*', 'y'), ('callRoute', '/a/b/c'), ('callRoute', '/q/b/c')])
        self.check(_o.URD, [(t, [None, None, None, None, 'me', 'anyUser', 'pair', '', None, 'root', None, None, 'me2', 'anyMe']), (u, [None, None, None, 'y', 'x'])])

    def test_une(self):
        self.check(_o.UNE, [([[1, 2, 1, 1, 3], 2], 4), ([[1, 2, 3, 4, 5, 1], 0], 2), ([[7], 0], 1), ([[1, 2, 1, 2, 1], 1], 3), ([[5, 5, 5], 3], 3)])

    def test_wcm(self):
        self.check(_o.WCM, [(['', ''], True), (['', '*'], True), (['a', ''], False), (['aa', 'a'], False), (['aa', '*'], True), (['abcd', 'a*d'], True),
                            (['abcd', 'a*c'], False), (['abab', '*ab'], True), (['aab', '*a*b*'], True), (['ab', 'ab*b'], False)])

    def test_wpm(self):
        self.check(_o.WPM, [(['abba', ['dogg', 'xyyx', 'xyzx', 'xxxx', 'xyy']], [False, True, False, False, False]), (['a', ['', 'z', 'zz']], [False, True, False]),
                            (['abc', ['xyz', 'xyx', 'cab']], [True, False, True])])

    def test_wdb(self):
        self.check(_o.WDB, [(ops('DiskBlockManager', [3, 2], [('write',)] * 8), [None, 0, 0, 1, 1, 2, 2, -1, -1]),
                            (ops('DiskBlockManager', [1, 1], [('write',)] * 2), [None, 0, -1])])

    def test_aba(self):
        t = ops('AlienBaseAttack', [3], [('isDestroyed',), ('attack', 0), ('attack', 2), ('isDestroyed',), ('attack', 3), ('attack', -1), ('isDestroyed',),
                                         ('attack', 1), ('isDestroyed',), ('attack', 1), ('isDestroyed',)])
        self.check(_o.ABA, [(t, [None, False, None, None, False, None, None, False, None, True, None, True])])

    def test_ags(self):
        self.check(_o.AGS, [([[5, 1, 9, 2], '1000', 4], [5, 5, 9, 9]), ([[5, 1, 9, 2], '0010', 3], [9, 9, 9]), ([[3, 8], '01', 2], [8, 8]), ([[4], '1', 1], [4])])

    def test_bsd(self):
        # [3,1],[2,2],k=1: both need 2 hits; heavier server first: 3*2 + 1*4 = 10
        self.check(_o.BSD, [([[3, 1], [2, 2], 1], 10), ([[1], [5], 2], 3), ([[1, 2, 3], [3, 3, 3], 3], 10), ([[2, 5], [4, 1], 2], 11)])

    def test_crt(self):
        self.check(_o.CRT, [([[]], 0), ([[3, 2, 1]], 1), ([[5, 4, 4, 3]], 2), ([[1, 2, 3]], 0), ([[4, 3, 2, 1]], 4)])

    def test_cdt(self):
        t = ops('PurchaseAnalyzer', [[['2024-03-01', 'ann', 'buy', '10'], ['2024-03-01', 'bob', 'buy', '5'], ['2024-03-01', 'cy', 'buy', '1']],
                                     [['2024-03-02', 'bob', 'sell', '7.5'], ['2024-03-02', 'ann', 'buy', '3'], ['2024-03-02', 'dee', 'gift', '2']]],
                [('crossDayDiverseUsers',), ('crossDayDiverseUsers',)])
        self.check(_o.CDT, [(t, [None, ['bob'], ['bob']])])

    def test_ese(self):
        self.check(_o.ESE, [(['7'], 7), (['-12'], -12), (['(add 1 2)'], 3), (['(mul 2 (add 1 2) 4)'], 24), (['( add  (mul -3 4)(add 1 1) )'], -10), (['(mul 0 -5)'], 0)])

    def test_ffe(self):
        logs = [['u1', 0, 'login'], ['u1', 86399, 'login'], ['u2', 5, 'pay'], ['u3', 6, 'pay'], ['u1', 86400, 'pay'], ['u1', 1, 'pay']]
        self.check(_o.FFE, [([logs, 2], ['login', 'pay']), ([logs, 3], []), ([[], 1], []), ([[['a', 0, 'x'], ['a', 86400, 'x']], 2], [])])

    def test_lpd(self):
        self.check(_o.LPD, [([[]], []), ([[['A', 'B'], ['B', 'C'], ['A', 'C']]], ['A', 'B', 'C']), ([[['X', 'Y'], ['A', 'B']]], ['A', 'B']),
                            ([[['B', 'C'], ['A', 'C'], ['C', 'D']]], ['A', 'C', 'D'])])

    def test_fpe(self):
        self.check(_o.FPE, [([[[1, 4], [2, 5], [4, 6]]], 2), ([[[0, 1], [1, 2]]], 0), ([[[5, 9], [0, 3], [6, 7], [2, 4]]], 2)])

    def test_frs(self):
        self.check(_o.FRS, [(['abc', 1, 1], 6), (['ab', 2, 0], 1), (['aeb', 2, 0], 1), (['zz', 0, 1], 3)])

    def test_got(self):
        self.check(_o.GOT, [([5, [[0, 2], [1, 1], [4, 4]]], [1, 2, 1, 0, 1]), ([3, []], [0, 0, 0]), ([1, [[0, 0], [0, 0]]], [2])])

    def test_domain(self):
        bad = [(_o.URD, ops('Router', [], [('addRoute', 'users', 'h')])), (_o.URD, ops('Router', [], [('addRoute', '/a/', 'h')])),
               (_o.URD, ops('Router', [], [('callRoute', '/a/*')])), (_o.URD, ops('Router', [], [('addRoute', '/a', '1h')])),
               (_o.URD, ops('Router', [], [('callRoute', '/a/b/c/d/e/f/g/h/i')])), (_o.UNE, [[], 0]), (_o.UNE, [[1, 2], 3]), (_o.UNE, [[0], 0]),
               (_o.WCM, ['a?', 'a']), (_o.WCM, ['A', '*']), (_o.WCM, ['a' * 2001, '*']), (_o.WPM, ['', []]), (_o.WPM, ['ab', ['Ab']]),
               (_o.WDB, ops('DiskBlockManager', [0, 1], [])), (_o.WDB, ops('DiskBlockManager', [1, 0], [])), (_o.WDB, ops('DiskBlockManager', [1, 1], [('read',)])),
               (_o.ABA, ops('AlienBaseAttack', [0], [])), (_o.ABA, ops('AlienBaseAttack', [3], [('attack', 1.5)])), (_o.AGS, [[1, 2], '00', 1]),
               (_o.AGS, [[1, 2], '1', 1]), (_o.AGS, [[1], '1', 0]), (_o.AGS, [[0], '1', 1]), (_o.BSD, [[1], [1, 2], 1]), (_o.BSD, [[101], [1], 1]),
               (_o.BSD, [[1], [1], 0]), (_o.CRT, [[10**9 + 1]]), (_o.CDT, ops('PurchaseAnalyzer', [[['2024-01-01', 'A', 'buy', '1']], []], [])),
               (_o.CDT, ops('PurchaseAnalyzer', [[['2024-01-01', 'a', 'buy']], []], [])), (_o.ESE, ['(add 1)']), (_o.ESE, ['(sub 1 2)']), (_o.ESE, ['(add 1 2']),
               (_o.ESE, ['(add 12)']), (_o.ESE, ['(add1 2)']), (_o.ESE, ['(add 01 2)']), (_o.ESE, ['(add -0 2)']), (_o.ESE, ['1 2']), (_o.ESE, ['(1 add 2)']),
               (_o.ESE, ['(mul' + ' 2' * 53 + ')']), (_o.ESE, ['']), (_o.FFE, [[['u', -1, 'a']], 1]), (_o.FFE, [[['u', 1, 'a']], 0]),
               (_o.LPD, [[['A', 'B'], ['B', 'A']]]), (_o.LPD, [[['A', 'A']]]), (_o.LPD, [[['A', 'B'], ['A', 'B']]]), (_o.LPD, [[['a', 'B']]]),
               (_o.FPE, [[]]), (_o.FPE, [[[3, 3]]]), (_o.FRS, ['', 1, 1]), (_o.FRS, ['aB', 1, 1]), (_o.GOT, [3, [[2, 1]]]), (_o.GOT, [3, [[0, 3]]]), (_o.GOT, [0, []])]
        for uid, args in bad:
            with self.assertRaises(ValueError, msg=str(args)[:80]): validate_domain(uid, args)
        validate_domain(_o.ESE, ['(add 1 2) '])
        validate_domain(_o.ESE, [' (add (mul 1 2)3) '])

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
        module = _load(f'gamma_h2h17b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
