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


_o = _load('gamma_h2h14b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h14b_reference_test_cases', HERE / 'cases.py')
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

    def test_tlg(self):
        self.check(_o.TLG1, [([[], 'int'], '() -> int'), ([['int', ['char', 'T1']], ['T1', 'float']], '(int, [char, T1]) -> [T1, float]')])
        self.check(_o.TLG2, [([['T1', 'int'], ['T1', 'T1'], [['char', 'float'], 'int']], '[[char, float], [char, float]]'), ([['T1', 'T1'], 'T1', ['int', 'char']], None),
                             ([['T1'], 'T2', ['int']], 'T2'), ([[['T1', 'char']], 'T1', [['int', 'char']]], 'int'), ([[['T1', 'char']], 'T1', [['int', 'char', 'int']]], None),
                             ([['int'], 'int', ['char']], None), ([['int'], 'int', []], None), ([[], ['T1'], []], '[T1]')])

    def test_vla(self):
        logs = [['p1', 'spam', '2024-01-01'], ['p2', 'spam', '2024-01-01'], ['p1', 'spam', '2024-01-02'], ['p1', 'hate', '2024-01-03'], ['p1', 'hate', '2024-01-03']]
        t = ops('ViolationLogAnalyzer', [logs], [('countPolicies', 'p1', '2024-01-01', '2024-01-03'), ('countPolicies', 'p1', '2024-01-01', '2024-01-02'),
                                                 ('countPosts', 'spam', '2024-01-01', '2024-01-05'), ('countViolations', '2024-01-01', '2024-01-03'),
                                                 ('countViolations', '2024-01-03', '2024-01-01'), ('countPolicies', 'p9', '2024-01-01', '2024-01-09')])
        self.check(_o.VLA, [(t, [None, 2, 1, 2, 3, 0, 0])])

    def test_vss(self):
        self.check(_o.VSS, [([''], 0), (['aeiou'], 1), (['aaeiouu'], 4), (['aeioxaeiou'], 1), (['uoiea'], 1), (['aeio'], 0), (['aeiouaeiou'], 21)])

    def test_wpa(self):
        self.check(_o.WPA, [([[1], []], 0), ([[2, 1], ['PACKAGE'] * 4], 0), ([[1, 1, 1], ['PACKAGE', 'CLOSURE 1', 'PACKAGE', 'PACKAGE']], 0),
                            ([[3, 2], ['PACKAGE', 'CLOSURE 0', 'PACKAGE']], 1)])

    def test_wca(self):
        a = ops('WeightedCache', [10], [('put', 'a', 1, 5), ('put', 'b', 2, 8), ('get', 'a'), ('get', 'b'), ('put', 'c', 3, 5), ('get', 'a'), ('get', 'c')])
        b = ops('WeightedCache', [5], [('put', 'a', 1, 6), ('get', 'a'), ('put', 'b', 2, 3), ('put', 'b', 7, 2), ('get', 'b')])
        self.check(_o.WCA, [(a, [None, None, None, 1, -1, None, 1, 3]), (b, [None, None, -1, None, None, 7])])

    def test_wse(self):
        self.check(_o.WSE, [(['', ''], 0), (['', 'abc'], 0), (['*', ''], 0), (['a*c', 'xxabzcx'], 2), (['b*', 'aab'], 2), (['abc', 'ab'], -1), (['a*a', 'a'], -1),
                            (['*b', 'aab'], 0), (['ba*ab', 'abab'], -1)])

    def test_wdg(self):
        box = [[0, 0, 0, 1], [0, 0, 1, 0], [1, 0, 1, 1], [0, 1, 1, 1]]
        self.check(_o.WDG, [([[]], 0), ([box], 2), ([box[:3] + [[5, 5, 5, 6]] + box[3:]], 1), ([[[0, 1, 0, 0]]], 0)])

    def test_wsl(self):
        g = [['a', 'b'], ['c', 'd']]
        self.check(_o.WSL, [([[['a']], 'a'], True), ([[['a']], 'b'], False), ([g, 'ad'], True), ([g, 'abd'], False), ([[['a', 'b', 'c']], 'cba'], True), ([[['a', 'B']], 'ab'], False)])

    def test_wtm(self):
        t = [[1, 5], [2, 3], [3, 1], [4, 2], [5, 4]]
        self.check(_o.WTM1, [([['bob', 'alice'], []], [[], []]), ([['bob', 'alice'], t], [[2, 3, 4], [1, 5]]), ([['c', 'b', 'a'], t], [[3, 4], [2, 5], [1]])])
        self.check(_o.WTM2, [([['bob', 'alice'], [['x'], ['x', 'y']], t, ['x', 'y', 'x', 'z', 'x']], [[3, 5], [1, 2], [4]]), ([['a'], [[]], t[:1], ['x']], [[], [1]])])
        self.check(_o.WTM3, [([['bob', 'alice'], [['x'], ['x', 'y']], [2, 1], t, ['x', 'y', 'x', 'x', 'x']], [[3, 4], [1], [2, 5]]), ([['a'], [['x']], [0], t[:1], ['x']], [[], [1]])])

    def test_aba(self):
        self.check(_o.ABA, [([[0], []], [0]), ([[1, 0, 1, 0], ['1', '1', '1']], [1, 1, 1, 1]), ([[1, 1], ['2 1', '2 0', '1']], [1, 0]), ([[0, 0], ['2 0', '1']], [1, 0])])

    def test_aeg(self):
        self.check(_o.AEG, [([[], [], 'Sam'], 'Dear Sam,\nNo violations found.'),
                            ([['scam', 'cheat', 'bot', 'cheat'], [['scam', 'Fraud'], ['cheat', 'Gameplay'], ['bot', 'Gameplay']], 'Kim'], 'Dear Kim,\nFraud: scam (1)\nGameplay: cheat (2), bot (1)'),
                            ([['zzz'], [['scam', 'Fraud']], 'a1'], 'Dear a1,\nNo violations found.')])

    def test_bsm(self):
        self.check(_o.BSM, [([0, []], 0), ([1, [-2]], 0), ([1, [-1, 5, -3, -4, 2]], 3), ([0, [3, -2, -2, 4, -4, -1]], 2), ([10, [-3, -3, -3, -3]], 3)])

    def test_bca(self):
        self.check(_o.BCA, [(['5/2'], 2), (['-7/3'], -2), (['2*(-3)'], -6), (['-4/2'], -2), (['-(3+2)'], -5), (['1+2*3-4/2'], 5), (['2*-3'], -6), (['--5'], 5),
                            (['(1+(4+5+2)-3)+(6+8)'], 23), (['7-3-2'], 2), (['0'], 0), (['8/3/2'], 1)])
        for s, want in [('5/2', 2), ('-7/3', -2), ('(1+(4+5+2)-3)+(6+8)', 23), ('8/3/2', 1), ('2*-3', -6)]:
            self.assertEqual(_o.bca_value(s), want)

    def test_bsd(self):
        sc = [[1, 3, 3], [5, 2, 0], [0, 0, 0]]
        self.check(_o.BSD1, [([sc], [1, 0, 0]), ([[[7]]], [0]), ([[[-1, -2], [-5, -5]]], [0, 0])])
        self.check(_o.BSD2, [([sc, 1], [[1, 0, 0]]), ([sc, 4], [[1, 0, 0], [1, 0, 1], [1, 0, 2], [2, 0, 0]]), ([[[7]], 3], [[0]]), ([[[1, 2], [3, 3]], 2], [[1, 0], [1, 1]])])

    def test_bcb(self):
        self.check(_o.BCB, [([2, 2, []], [[], [], [], []]), ([3, 3, [[0, 0]]], [[[0, 0]], [], [], []]), ([3, 3, [[0, 0], [1, 1], [0, 2]]], [[[1, 0], [1, 1]], [[0, 0], [0, 1]], [], []]),
                            ([2, 3, [[0, 0], [0, 1], [1, 0], [1, 1], [1, 2], [0, 2]]], [[], [], [], [[0, 0], [0, 1]]])])

    def test_bsa(self):
        self.check(_o.BSA, [([[], ''], True), ([[], 'a'], False), ([[['a', 'b'], ['b']], 'ab'], True), ([[['a', 'b'], ['a']], 'ba'], True), ([[['a'], ['a']], 'aa'], True),
                            ([[['a', 'b']], 'ab'], False), ([[['a', 'b'], ['b', 'c'], ['a']], 'abc'], True)])

    def test_domain(self):
        deep = 'int'
        for _ in range(21): deep = [deep]
        for uid, args in [(_o.TLG1, [[], 'T10']), (_o.TLG1, [[[]], 'int']), (_o.TLG1, [[], deep]), (_o.TLG1, [['bool'], 'int']), (_o.TLG2, [['T1'], 'int', ['T1']]),
                          (_o.VLA, ops('ViolationLogAnalyzer', [[['p', 'spam', '2024-01-02'], ['p', 'spam', '2024-01-01']]], [])),
                          (_o.VLA, ops('ViolationLogAnalyzer', [[['p', 'spam', '2024-02-30']]], [])), (_o.VLA, ops('ViolationLogAnalyzer', [[]], [('countPosts', 'P', '2024-01-01', '2024-01-01')])),
                          (_o.VSS, ['aeIou']), (_o.WPA, [[], []]), (_o.WPA, [[1], ['CLOSURE 0']]), (_o.WPA, [[1, 1], ['CLOSURE 0', 'CLOSURE 0']]), (_o.WPA, [[1, 1], ['CLOSURE 01']]),
                          (_o.WPA, [[0], []]), (_o.WCA, ops('WeightedCache', [0], [])), (_o.WCA, ops('WeightedCache', [5], [('put', 'a', 1, 0)])),
                          (_o.WCA, ops('WeightedCache', [5], [('put', 'a', -1, 1)])), (_o.WSE, ['A', 'a']), (_o.WSE, ['a', 'a*']),
                          (_o.WDG, [[[0, 0, 1, 1]]]), (_o.WDG, [[[0, 0, 0, 1], [0, 1, 0, 0]]]), (_o.WDG, [[[8, 8, 8, 9]]]),
                          (_o.WSL, [[['a', 'b'], ['c']], 'a']), (_o.WSL, [[['ab']], 'a']), (_o.WSL, [[['a']], '']),
                          (_o.WTM1, [['a', 'a'], []]), (_o.WTM1, [['a'], [[1, 0]]]), (_o.WTM1, [['a'], [[1, 1], [1, 2]]]), (_o.WTM2, [['a'], [['x', 'x']], [], []]),
                          (_o.WTM2, [['a'], [], [], []]), (_o.WTM3, [['a'], [[]], [-1], [], []]),
                          (_o.ABA, [[], []]), (_o.ABA, [[2], []]), (_o.ABA, [[0], ['2 1']]), (_o.ABA, [[0], ['3']]),
                          (_o.AEG, [['a'], [['a', 'X'], ['a', 'Y']], 'u']), (_o.AEG, [['A'], [], 'u']), (_o.AEG, [[], [], '']),
                          (_o.BSM, [-1, []]), (_o.BSM, [0, [0]]),
                          (_o.BCA, ['']), (_o.BCA, ['1/0']), (_o.BCA, ['1+']), (_o.BCA, ['(1']), (_o.BCA, ['1 + 2']), (_o.BCA, ['01']), (_o.BCA, ['1-+2']), (_o.BCA, ['()']),
                          (_o.BCA, ['1000000000*1000000000']),
                          (_o.BSD1, [[]]), (_o.BSD1, [[[1, 2], [3]]]), (_o.BSD2, [[[1]], 0]), (_o.BSD2, [[[1]] * 201, 1]),
                          (_o.BCB, [1, 5, []]), (_o.BCB, [2, 2, [[2, 0]]]), (_o.BCB, [2, 2, [[0, 0], [0, 0]]]),
                          (_o.BSA, [[[]], '']), (_o.BSA, [[['ab']], 'a']), (_o.BSA, [[], 'A'])]:
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
        module = _load(f'gamma_h2h14b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
