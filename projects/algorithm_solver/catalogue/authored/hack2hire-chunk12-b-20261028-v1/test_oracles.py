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


_o = _load('gamma_h2h12b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h12b_reference_test_cases', HERE / 'cases.py')
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

    def test_mda(self):
        self.check(_o.MDA, [([[1, 2, 11, 15], [4, 12, 19, 23, 127, 235]], [11, 12]), ([[1, 5], [3]], [1, 3]), ([[-5, -5, 0], [-5, 7]], [-5, -5]), ([[1, 3], [23]], [3, 23])])

    def test_mvs(self):
        self.check(_o.MVS, [([[0, -3], 0], 1), ([[5], 0], -1), ([[5], 1], 5), ([[5, 5, 5], 3], 5), ([[7, 3], 4], 3), ([[10, 1, 1], 6], 3)])

    def test_mcv(self):
        self.check(_o.MCV, [([[10, 6], 0], 16), ([[10, 6], 1], 11), ([[10, 6], 3], 5), ([[1, 1, 1], 100], 0), ([[9], 2], 2), ([[], 3], 0)])

    def test_msd(self):
        self.check(_o.MSD, [([[['milk', 'Dairy'], ['cheese', 'Dairy'], ['apple', 'Produce']], ['milk', 'apple', 'cheese', 'milk', 'tent']], 2), ([[], ['x']], 0)])

    def test_mcc(self):
        self.check(_o.MCC, [([[1], 0], [0]), ([[2], 3], []), ([[1, 2, 5], 11], [1, 0, 2]), ([[1, 3, 4], 6], [0, 2, 0]), ([[5, 3], 7], []), ([[2, 4], 9], []),
                            ([[1, 5, 6], 11], [0, 1, 1])])

    def test_mdp(self):
        self.check(_o.MDP, [([[5]], [5, 0]), ([[1, 2]], [1, 1]), ([[2, 1]], [1, 1]), ([[1, 2, 3, 100]], [2, 100]), ([[-1, -1, 5]], [-1, 6]), ([[3, 3, 1, 1]], [1, 4])])

    def test_mfg(self):
        self.check(_o.MFG, [([['B']], 0), ([['BW']], 1), ([['BW', 'WB']], 2), ([['BBW', 'WBW', 'BWB']], 2)])

    def test_mik(self):
        self.check(_o.MIK, [(['a', 0], 1), (['aab', 0], 2), (['aaaa', 1], 2), (['aaaaa', 1], 2), (['abab', 0], 1), (['aaabbb', 2], 1), (['aaaa', 2], 1)])

    def test_mmt(self):
        self.check(_o.MMT, [([[]], 0), ([[[0, 30], [5, 10], [15, 20]]], 2), ([[[1, 2], [2, 3]]], 1), ([[[1, 5], [1, 5], [1, 5]]], 3)])

    def test_mrl(self):
        self.check(_o.MRL, [([[]], []), ([[1]], [1]), ([[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1]], [5, 8, 4, 1]), ([[1, 2, 2]], [1, 2]),
                            ([[-1, None, -2, None, -3]], [-1, -2, -3]), ([[1, 2, 3, 4]], [1, 3])])

    def test_msb(self):
        self.check(_o.MSB, [([[1]], 2), ([[3, -2, 4]], 6), ([[-5, 1]], 1), ([[0, 0]], 1), ([[2, 2, -10, 1]], 5)])

    def test_msk(self):
        self.check(_o.MSK, [([[1], 1], 1), ([[1], 2], -1), ([[1, 2, 1, 3, 4], 3], 3), ([[5, 5, 5], 1], 1), ([[1, 2, 2, 2, 3, 1], 3], 3)])

    def test_mse(self):
        self.check(_o.MSE, [([[]], 0), ([[2, 4, 1]], 0), ([[1, 2]], 1), ([[1, 3, 2, 4]], 2), ([[-3, -2, 7, 8, 0]], 2)])

    def test_ntl(self):
        self.check(_o.NTL, [([[]], []), ([[1]], [[1]]), ([[1, None, 3, 2, 4, None, 5, 6]], [[2, 4, 5, 6], [3], [1]]),
                            ([[1, None, 2, None, 3, None, 4]], [[4], [3], [2], [1]]), ([[7, None, 7, 7, None, 7]], [[7, 7], [7], [7]])])

    def test_nsb(self):
        self.check(_o.NSB1, [([''], True), (['()'], True), ([')('], False), (['(a,(b,c))'], True), (['((a)'], False), (['abc,d'], True), (['(()'], False), (['())'], False)])
        self.check(_o.NSB2, [(['()'], []), (['(a)'], ['a']), (['(a,(b,c),d)'], ['a', ['b', 'c'], 'd']), (['((),(()),xyz)'], [[], [[]], 'xyz']), (['(((deep)))'], [[['deep']]])])

    def test_ngp(self):
        self.check(_o.NGP, [(['1'], '2'), (['9'], '11'), (['11'], '22'), (['99'], '101'), (['123'], '131'), (['808'], '818'), (['1299'], '1331'), (['9999'], '10001'),
                            (['12921'], '13031'), (['10'], '11')])

    def test_domain(self):
        for uid, args in [(_o.MDA, [[], [1]]), (_o.MDA, [[2, 1], [1]]), (_o.MDA, [[1], [10**9 + 1]]), (_o.MDA, [[1.0], [1]]),
                          (_o.MVS, [[], 1]), (_o.MVS, [[1], -1]), (_o.MVS, [[True], 1]),
                          (_o.MCV, [[-1], 1]), (_o.MCV, [[1], 100001]),
                          (_o.MSD, [[['a', 'D'], ['a', 'E']], []]), (_o.MSD, [[['a', 'D', 'x']], []]), (_o.MSD, [[], ['']]), (_o.MSD, [[['a-b', 'D']], []]),
                          (_o.MCC, [[], 1]), (_o.MCC, [[1, 1], 1]), (_o.MCC, [[0], 1]), (_o.MCC, [[1], 10001]), (_o.MCC, [list(range(1, 52)), 1]),
                          (_o.MDP, [[]]), (_o.MFG, [[]]), (_o.MFG, [['']]), (_o.MFG, [['BW', 'B']]), (_o.MFG, [['BX']]), (_o.MFG, [['B' * 501] * 500]),
                          (_o.MIK, ['', 0]), (_o.MIK, ['abc', 0]), (_o.MIK, ['ab', 3]),
                          (_o.MMT, [[[1, 1]]]), (_o.MMT, [[[-1, 1]]]), (_o.MMT, [[[1, 2, 3]]]),
                          (_o.MRL, [[None]]), (_o.MRL, [[1, None]]), (_o.MRL, [[1, None, None, 2]]), (_o.MRL, [[1, 2.5]]),
                          (_o.MSB, [[]]), (_o.MSK, [[0], 1]), (_o.MSK, [[1], 0]), (_o.MSE, [[1.5]]),
                          (_o.NTL, [[None]]), (_o.NTL, [[1, 2]]), (_o.NTL, [[1, None]]), (_o.NTL, [[1, None, 2, None, None, None, 3]]), (_o.NTL, [[1, None, None, 2]]),
                          (_o.NSB1, ['a[b]']), (_o.NSB1, ['A']),
                          (_o.NSB2, ['']), (_o.NSB2, ['a']), (_o.NSB2, ['(a,)']), (_o.NSB2, ['(,a)']), (_o.NSB2, ['(a)(b)']), (_o.NSB2, ['(a(b))']), (_o.NSB2, ['((a)b)']),
                          (_o.NSB2, ['(a']), (_o.NSB2, ['(' * 101 + ')' * 101]),
                          (_o.NGP, ['0']), (_o.NGP, ['012']), (_o.NGP, ['']), (_o.NGP, ['1' * 100001])]:
            with self.assertRaises(ValueError, msg=str(args)[:80]): validate_domain(uid, args)

    def test_generated_cases_domain_valid_and_shallow(self):
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True):
                validate_domain(uid, row['args'])
                self.assertLessEqual(depth(row['args']), 200)

    def test_contract_layouts_match_classes(self):
        self.assertEqual(set(CONTRACTS), set(_o.IDS))
        self.assertEqual(_o.CLASSES, {})
        for uid, row in CONTRACTS.items():
            self.assertEqual(row['spec_basis'], 'inferred')
            self.assertNotIn('classname', row['inferred_interface'])

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
        module = _load(f'gamma_h2h12b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
