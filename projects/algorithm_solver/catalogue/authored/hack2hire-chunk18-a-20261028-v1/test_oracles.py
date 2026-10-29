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


_o = _load('gamma_h2h18a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h18a_reference_test_cases', HERE / 'cases.py')
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

    def test_hsm(self):
        # group scores with k = 2: 5 + 1 = 6, 4 + 3 = 7, 1 + 2 = 3
        self.check(_o.HSM, [([[5, 1, 4, 3, 2], [[0, 1], [2, 3, 4], [1, 4]], 2], 1), ([[5, 1, 4, 3, 2], [[2, 3, 4], [0, 1]], 1], 1), ([[0, 0], [[0], [1]], 3], 0),
                            ([[7], [[0]], 1], 0)])

    def test_hwc(self):
        recs = [['CAR1', 'A1'], ['CAR2', 'B3'], ['CAR1', 'A5'], ['CAR1', 'C2'], ['BUS', 'X10']]
        self.check(_o.HWC, [([recs], [['BUS', 0], ['CAR1', 70], ['CAR2', 0]]), ([[]], []), ([[['Z', 'A0'], ['Z', 'B0']]], [['Z', 0]])])

    def test_mab(self):
        self.check(_o.MAB, [([[1]], 0), ([[3, 3, 3]], 5), ([[1, 2, 3, 2, 1]], 0), ([[0, 5, 5, 5, 0]], 11), ([[2, 1, 4, 4, 4, 1]], 7), ([[0, 0, 7]], 6)])

    def test_mpn(self):
        self.check(_o.MPN, [([[3, 2, 1]], 2), ([[1, 2, 3]], 0), ([[5, 1, 5, 1]], 8), ([[2, 4, 1, 3]], 3), ([[7]], 0)])

    def test_mtc(self):
        self.check(_o.MTC, [([[[1, 2, 3], [4, 5, 6]], ['reverseRow 0', 'swap 0 1']], [[4, 5, 6], [3, 2, 1]]),
                            ([[[1, 2], [3, 4], [5, 6]], ['swap 0 2', 'swap 1 1', 'reverseRow 2', 'reverseRow 2']], [[5, 6], [3, 4], [1, 2]]), ([[[9]], []], [[9]])])

    def test_mns(self):
        self.check(_o.MNS, [([[1]], 0), ([[5, 2, 2]], 2), ([[1, 1, 1, 1]], 1), ([[3, 1, 1, 1, 5]], 2), ([[10, 9, 1]], 1)])

    def test_mts(self):
        # two slots, 20 20 20 30 30: shortest first gives 4 (a perfect packing would fit 5; the inferred rule is the greedy one)
        self.check(_o.MTS, [([1, 1, [30, 20, 10, 5]], 3), ([2, 1, [20, 20, 20, 30, 30]], 4), ([1, 2, [61, 70]], 0), ([3, 2, []], 0), ([1, 1, [60]], 1)])

    def test_mgj(self):
        b = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [1, 1, 100]]
        z = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        alt = [[1], [-9], [1], [-9], [1]]
        self.check(_o.MGJ1, [([b, 0], 115), ([b, 2], 118), ([[[5, -1]], 1], -1), ([[[-5], [-5], [-5]], 0], -15)])
        self.check(_o.MGJ2, [([b, 0, 0], 115), ([b, 0, 1], 115), ([alt, 0, 2], 3), ([alt, 0, 1], -6), ([[[1, 1], [1, 1]], 1, 2], 2)])
        self.check(_o.MGJ3, [([b, 0, 1], [[0, 0], [1, 1], [2, 2], [3, 2]]), ([z, 1, 1], [[0, 1], [1, 0], [2, 0]]), ([[[1], [-9], [1]], 0, 1], [[0, 0], [2, 0]]),
                             ([[[4]], 0, 0], [[0, 0]])])
        self.check(_o.MGJ4, [([z, 1, 1], 8), ([[[0], [0], [0], [0]], 0, 1], 3), ([[[1, 2], [3, 3]], 0, 0], 2), ([[[4]], 0, 0], 1)])

    def test_mbs(self):
        self.check(_o.MBS, [([[3, 1, 2, 1]], 2), ([[1, 2, 3]], 0), ([[5, 1, 1]], 1), ([[4, 3, 2, 1]], 2), ([[2, 2]], 0), ([[1, 3, 2, 5, 4]], 2)])

    def test_mvt(self):
        self.check(_o.MVT, [([1, []], 1), ([3, [[0, 1], [1, 2], [2, 0]]], 1), ([4, [[0, 1], [1, 0], [2, 3]]], 2),
                            ([5, [[0, 1], [1, 2], [2, 1], [3, 3], [4, 3]]], 2), ([2, [[0, 0], [0, 1], [0, 1]]], 1)])

    def test_domain(self):
        bad = [(_o.HSM, [[1], [[0, 0]], 1]), (_o.HSM, [[1], [[]], 1]), (_o.HSM, [[1], [[1]], 1]), (_o.HSM, [[1], [[0]], 0]), (_o.HSM, [[-1], [[0]], 1]),
               (_o.HSM, [[], [], 1]), (_o.HWC, [[['ab', 'A1']]]), (_o.HWC, [[['AB', 'A01']]]), (_o.HWC, [[['AB', '12']]]), (_o.HWC, [[['AB', 'A1', 'x']]]),
               (_o.MAB, [[0, 0]]), (_o.MAB, [[]]), (_o.MAB, [[-1, 3]]), (_o.MPN, [[0]]), (_o.MPN, [[]]), (_o.MTC, [[[1], [2, 3]], []]),
               (_o.MTC, [[[1]], ['swap 0 1']]), (_o.MTC, [[[1]], ['reverseRow  0']]), (_o.MTC, [[[1]], ['reverseCol 0']]), (_o.MTC, [[], []]),
               (_o.MNS, [[0]]), (_o.MNS, [[]]), (_o.MTS, [0, 1, [1]]), (_o.MTS, [1, 1, [0]]), (_o.MGJ1, [[[1]], 1]), (_o.MGJ1, [[[1], [1, 2]], 0]),
               (_o.MGJ2, [[[1]], 0, 2]), (_o.MGJ2, [[[1]] * 20, 0, -1]), (_o.MGJ3, [[[0] * 100] * 200, 0, 5]), (_o.MGJ4, [[[10**4 + 1]], 0, 0]),
               (_o.MBS, [[0]]), (_o.MBS, [[]]), (_o.MVT, [0, []]), (_o.MVT, [2, [[0, 2]]]), (_o.MVT, [2, [[0]]])]
        for uid, args in bad:
            with self.assertRaises(ValueError, msg=str(args)[:80]): validate_domain(uid, args)
        validate_domain(_o.MTC, [[[1], [2]], ['swap 1 0', 'reverseRow 1']])
        validate_domain(_o.MGJ2, [[[1]] * 20, 0, 20])

    def test_generated_cases_domain_valid_and_shallow(self):
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True):
                validate_domain(uid, row['args'])
                self.assertLessEqual(depth(row['args']), 200)

    def test_contract_layouts_are_functions(self):
        self.assertEqual(set(CONTRACTS), set(_o.IDS))
        self.assertEqual(_o.CLASSES, {})
        for uid, row in CONTRACTS.items():
            self.assertEqual(row['spec_basis'], 'inferred')
            self.assertNotIn('classname', row['inferred_interface'])
            self.assertEqual(row['source']['variant_count'], 4 if uid in _o.MGJ else 1)
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


def js_agrees(uid, got, expected):
    """JavaScript has no integral-float tag: FLOATS results compare by numeric value; everything else exactly."""
    if uid in _o.FLOATS: return type(got) in (int, float) and type(got) is not bool and got == expected
    return exact(got, expected)


class Candidates(unittest.TestCase):
    """Author-local self-check of own candidates against own generated cases; not isolated qualification."""
    def run_python(self, uid, rows):
        path = HERE / 'python' / f'{stem(uid)}.py'
        if not path.exists(): self.skipTest('candidate absent')
        module = _load(f'gamma_h2h18a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
