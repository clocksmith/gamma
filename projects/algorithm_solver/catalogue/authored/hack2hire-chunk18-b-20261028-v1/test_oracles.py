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


_o = _load('gamma_h2h18b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h18b_reference_test_cases', HERE / 'cases.py')
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

    def test_nct(self):
        self.check(_o.NCT, [(['hello'], 'jemmo'), (['xyz'], 'yzb'), (['b'], 'c'), (['aeiou'], 'aeiou'), (['abcdefghijklmnopqrstuvwxyz'], 'acdfeghjiklmnpoqrstvuwxyzb')])

    def test_ohe(self):
        self.check(_o.OHE, [([[2, 1, 2]], [[0, 1], [1, 0], [0, 1]]), ([[5, -5, 0, 5]], [[0, 0, 1], [1, 0, 0], [0, 1, 0], [0, 0, 1]]), ([[3]], [[1]])])

    def test_ptp(self):
        self.check(_o.PTP, [(['*+AB-CD'], 'AB+CD-*'), (['-a*bc'], 'abc*-'), (['^2^34'], '234^^'), (['A'], 'A'), (['/+ab+cd'], 'ab+cd+/')])

    def test_rpm(self):
        self.check(_o.RPM, [(['', 'a*'], True), (['', 'a'], False), (['aab', 'a*b'], True), (['ababc', '(ab)*c'], True), (['abac', '(ab)*c'], False),
                            (['xyz', '(x.)*z'], True), (['b', 'a*(ab)*b'], True), (['aaa', 'a*a'], True), (['abab', '(a.)(b)*a.'], True), (['ab', '(.)*'], True)])

    def test_sim(self):
        self.check(_o.SIM, [([[[1, 2, 0], [0, 3, 0], [4, 0, 9]]], 9), ([[[1, 0, 1], [0, 1, 0], [1, 0, 1]]], 1), ([[[0]]], 0), ([[[2, 2], [2, 2]]], 8)])

    def test_dls(self):
        self.check(_o.DLS, [([2, 3, 3, 2], [['t1', 'm1', 'h1'], ['t1', 'm2', 'h2'], ['t2', 'm3', 'h3'], ['t2', 'm1', 'h1']]), ([2, 1, 5, 2], []),
                            ([3, 2, 4, 2], [['t1', 'm1', 'h1'], ['t1', 'm2', 'h2'], ['t2', 'm1', 'h3'], ['t2', 'm2', 'h4'], ['t3', 'm1', 'h1'], ['t3', 'm2', 'h2']])])

    def test_dlv(self):
        self.check(_o.DLV, [(_c.HAND[_o.DLV][0], True), (_c.HAND[_o.DLV][1], False), (_c.HAND[_o.DLV][2], False), (_c.HAND[_o.DLV][3], False),
                            (_c.HAND[_o.DLV][4], False), (_c.HAND[_o.DLV][5], False), (_c.HAND[_o.DLV][6], True)])

    def test_fcc(self):
        # capacity 2: 1, True and "1" are different keys; keyword and object key order do not matter
        self.check(_o.FCC, [(_c.HAND[_o.FCC][0], [None, False, False, True, False, False, False, True, False, True, False])])

    def test_fcs(self):
        # f(1), f(a=1), f(1, 0) and f(b=0, a=1) bind identically; f(1, b=False) differs from f(1, 0)
        self.check(_o.FCS, [(_c.HAND[_o.FCS][0], [None, False, True, True, True, False, False, False, True, True])])

    def test_cellular(self):
        g1, g2 = _c.G1, _c.G2
        self.check(_o.CID, [([g1, 1], [[0, 1, 2], [1, 1, 2], [2, 2, 2]]), ([g1, 2], [[0, -1, -1], [-1, -1, -1], [-1, -1, -1]]),
                            ([g2, 2], [[0, 1, 0], [1, 1, 1], [0, 1, 0]]), ([g2, 4], [[0, -1, 0], [-1, 1, -1], [0, -1, 0]]), ([[[1, 1, 0, 0, 0]], 1], [[0, 0, 1, 2, 3]])])
        self.check(_o.CSD, [([g1, 1], 2), ([g1, 2], 0), ([g2, 4], 1), ([[[1, 1, 0, 0, 0]], 1], 3), ([[[0]], 1], 0)])
        self.check(_o.CIA, [([g1, 1], 2), ([g1, 2], -1), ([g2, 2], 1), ([g2, 4], -1), ([[[1]], 8], 0), ([[[0]], 1], -1)])
        self.check(_o.CFG, [([g2, 4], [[1, 0, 1], [0, 1, 0], [1, 0, 1]]), ([g1, 1], [[1] * 3] * 3)])
        self.check(_o.CGD, [([g1, 1, 1], [[1, 1, 0], [1, 1, 0], [0, 0, 0]]), ([g1, 1, 0], g1), ([g1, 1, 10**9], [[1] * 3] * 3)])

    def test_cell_constructions_match_reference(self):
        for n in (4, 5, 8, 9):
            for grid, threshold, day in _c.cell_rows(n):
                self.assertEqual(_o.ref_cells(grid, threshold), day, (n, threshold))

    def test_ote(self):
        # (5, 1, 10, 3, 100): only k >= 4 is feasible; k = 4 costs 40 + 25, k = 5 costs 50
        self.check(_o.OTE, [([5, 1, 10, 3, 100], 50), ([3, 2, 5, 1, 7], 12), ([1, 1, 1, 1, 1], 1), ([2, 5, 1, 9, 9], 2), ([3, 1, 1, 1, 10], 3)])

    def test_pae(self):
        self.check(_o.PAE, [([[1, 2, 3, 4], [[1, 3]]], [[1, 3], [2], [4]]), ([[5, 5, 6], []], [[5, 5], [6]]), ([[1, 9], [[1, 5], [5, 9]]], [[1, 9]]),
                            ([[4, 2, 4, 3, 2], [[2, 3], [3, 3]]], [[4, 4], [2, 3, 2]])])

    def test_domain(self):
        F = 'FunctionCallCache'
        sig = {'f': [['a'], ['b', 0]]}
        bad = [(_o.NCT, ['']), (_o.NCT, ['aB']), (_o.OHE, [[]]), (_o.OHE, [[1.5]]), (_o.OHE, [list(range(1001))]), (_o.PTP, ['+A']), (_o.PTP, ['AB']),
               (_o.PTP, ['+A B']), (_o.PTP, ['']), (_o.PTP, ['%AB']), (_o.RPM, ['a', '*a']), (_o.RPM, ['a', '(a*)']), (_o.RPM, ['a', '((a))']),
               (_o.RPM, ['a', 'a**']), (_o.RPM, ['A', 'a']), (_o.RPM, ['a', '()']), (_o.RPM, ['a', '']), (_o.RPM, ['a', '(*)']), (_o.SIM, [[[]]]),
               (_o.SIM, [[[1], [1, 2]]]), (_o.SIM, [[[-1]]]), (_o.SIM, [[[1] * 201]]), (_o.DLS, [1, 1, 1, 0]), (_o.DLS, [10**5, 1, 1, 2]),
               (_o.DLS, [1, 10**4 + 1, 1, 1]), (_o.DLV, [1, 1, 1, 1, [['t1', 'm1']]]), (_o.DLV, [1, 1, 1, 1, [['T1', 'm1', 'h1']]]),
               (_o.FCC, ops(F, [0], [])), (_o.FCC, ops(F, [1], [('call', 'f', [1.5], {})])), (_o.FCC, ops(F, [1], [('call', 'f', [[[[[1]]]]], {})])),
               (_o.FCC, ops(F, [1], [('call', 'f', [], {'A': 1})])), (_o.FCC, ops(F, [1], [('call', 'F', [], {})])), (_o.FCC, ops(F, [1], [('call', 'f', [1])])),
               (_o.FCS, ops(F, [1, sig], [('call', 'g', [1], {})])), (_o.FCS, ops(F, [1, sig], [('call', 'f', [1, 2, 3], {})])),
               (_o.FCS, ops(F, [1, sig], [('call', 'f', [], {'b': 1})])), (_o.FCS, ops(F, [1, sig], [('call', 'f', [1], {'a': 1})])),
               (_o.FCS, ops(F, [1, sig], [('call', 'f', [1], {'c': 1})])), (_o.FCS, ops(F, [1, {'f': [['a', 0], ['b']]}], [])),
               (_o.FCS, ops(F, [1, {'f': [['a'], ['a']]}], [])), (_o.CSD, [[[2]], 1]), (_o.CIA, [[[1]], 0]), (_o.CFG, [[[1]], 9]), (_o.CGD, [[[1]], 1, -1]),
               (_o.CID, [[[1], [0, 0]], 1]), (_o.OTE, [0, 1, 1, 1, 1]), (_o.OTE, [1, 1, 1, 1, 0]), (_o.OTE, [1001, 1, 1, 1, 1]), (_o.PAE, [[], []]),
               (_o.PAE, [[1], [[1, 2, 3]]])]
        for uid, args in bad:
            with self.assertRaises(ValueError, msg=str(args)[:80]): validate_domain(uid, args)
        validate_domain(_o.RPM, ['', '(a.)*.b*'])
        validate_domain(_o.FCS, ops(F, [1, sig], [('call', 'f', [], {'a': [1, {'k': None}]})]))

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
        module = _load(f'gamma_h2h18b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
