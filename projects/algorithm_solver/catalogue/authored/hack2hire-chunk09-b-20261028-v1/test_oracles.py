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


_o = _load('gamma_h2h09b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h09b_reference_test_cases', HERE / 'cases.py')
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
    def test_cbs(self):
        self.assertEqual(reference(_o.CBS, [[['A1', 'A2'], ['B3', 'A0']]]), 12)
        self.assertEqual(reference(_o.CBS, [[['A1', 'B1', 'A1'], ['A1', 'A1', 'A1']]]), 26)
        self.assertEqual(reference(_o.CBS, [[['C1'], ['C1'], ['D9']]]), 13)

    def test_cps(self):
        self.assertEqual(reference(_o.CPS, [[3, 1, 2]]), [2, 0, 0])
        self.assertEqual(reference(_o.CPS, [[5, 1, 9, 0, 7]]), [3, 2, 2, 0, 0])
        self.assertEqual(reference(_o.CPS, [[]]), [])

    def test_cdg(self):
        self.assertEqual(reference(_o.CDG, [[[13, 4], [11, 7], [19, 2], [15, 9]]]), [[10, 9, 2, 7, 2]])
        self.assertEqual(reference(_o.CDG, [[[25, 3], [2, 8], [21, 1], [8, 6]]]), [[0, 8, 6, 8, 6], [20, 3, 1, 1, 3]])

    def test_cll(self):
        self.assertEqual(reference(_o.CLL, [[[1, 2], [3], [], [4, 5, 6]], 2]), [[1, 2], [3, 4], [5, 6]])
        self.assertEqual(reference(_o.CLL, [[[7], [8]], 5]), [[7, 8]])
        self.assertEqual(reference(_o.CLL, [[[]], 3]), [])

    def test_cra(self):
        self.assertEqual(reference(_o.CRA, [[], [['c', 'p', 'R'], ['c', 'p', 'R'], ['c', 'q', 'R'], ['c', 'q', 'S']]]), ['VALID', 'ALREADY_EXISTS', 'ROLE_TAKEN', 'VALID'])
        self.assertEqual(reference(_o.CRA, [[['c', 'p', 'R'], ['c', 'q', 'R']], [['c', 'q', 'R'], ['d', 'q', 'R'], ['c', 'r', 'R']]]), ['ALREADY_EXISTS', 'VALID', 'ROLE_TAKEN'])

    def test_cnt(self):
        tree = [[1, [2, 3]], [2, [4, 5]], [4, []], [5, []], [3, []]]
        self.assertEqual(reference(_o.CNT, [tree, [2]]), [[1, [4, 5, 3]], [4, []], [5, []], [3, []]])
        self.assertEqual(reference(_o.CNT, [tree, [2, 4, 99, 1]]), [[1, [5, 3]], [5, []], [3, []]])
        self.assertEqual(reference(_o.CNT, [[[0, [1]], [1, [2]], [2, [3]], [3, []]], [1, 2]]), [[0, [3]], [3, []]])

    def test_cpm(self):
        t = ops('PointMatrix', [], [('addPoint', 0, 0), ('addPoint', 0, 5), ('addPoint', 3, 5), ('addPoint', 7, 7), ('isConnected', [0, 0], [3, 5]),
                                    ('getMinSteps', [0, 0], [3, 5]), ('isConnected', [0, 0], [7, 7]), ('getMinSteps', [0, 0], [7, 7]), ('getMinSteps', [3, 5], [3, 5]),
                                    ('addPoint', 3, 7), ('getMinSteps', [0, 0], [7, 7]), ('isConnected', [0, 0], [1, 1]), ('addPoint', 0, 0), ('getMinSteps', [0, 5], [0, 0])])
        self.assertEqual(reference(_o.CPM, t), [None, None, None, None, None, True, 2, False, -1, 0, None, 4, False, None, 1])

    def test_cat(self):
        self.assertEqual(reference(_o.CAT, [[1, 9, 9, 1, 9], 5, 3, 60]), 3)
        self.assertEqual(reference(_o.CAT, [[1, 9, 9, 1, 9], 5, 3, 67]), 0)
        self.assertEqual(reference(_o.CAT, [[1, 2], 0, 3, 0]), 0)
        self.assertEqual(reference(_o.CAT, [[0, 0], 0, 2, 0]), 1)

    def test_cde(self):
        self.assertEqual(reference(_o.CDE, [[1, 2, 1, 3, 4, 2, 3], 4]), [3, 4, 4, 3])

    def test_cdr(self):
        self.assertEqual(reference(_o.CDR, [[1, 1, 1, 1, 1]]), 2)
        self.assertEqual(reference(_o.CDR, [[1, 1, 1, 2, 2, 2, 2]]), 1)
        self.assertEqual(reference(_o.CDR, [[1 + i // 3 for i in range(21)]]), 1)
        self.assertEqual(reference(_o.CDR, [[1 + i // 2 for i in range(62)]]), 2)

    def test_cip(self):
        self.assertEqual(reference(_o.CIP, [['a', 'b'], [2, 3.5], ['a', 'b', 'b', 'a'], [2.0, 3.5, 3, 2]]), 1)

    def test_cbd(self):
        self.assertEqual(reference(_o.CBD, [[0, 9], [9, 0]]), 2)
        self.assertEqual(reference(_o.CBD, [[100, 0, 6], [5, 6, 100]]), 3)  # smallest-payback-first would stop at 2
        self.assertEqual(reference(_o.CBD, [[0, 5, 6], [10, 1, 2]]), 2)
        self.assertEqual(reference(_o.CBD, [[10, 1, 0], [1, 1, 10]]), 3)
        self.assertEqual(reference(_o.CBD, [[], []]), 0)

    def test_cop(self):
        self.assertEqual(reference(_o.COP, [['**', '**'], [[1, 1], [1, 2]]]), 2)
        self.assertEqual(reference(_o.COP, [['*_*', '***'], [[1, 0, 1], [1, 1, 1]]]), 1)
        self.assertEqual(reference(_o.COP, [['**', '**'], [[1, 2], [2, 1]]]), 4)

    def test_crc(self):
        self.assertEqual(reference(_o.CRC, [[['s', 'A', '2000'], ['s', 'B', '2001']], 1]), [['A', 'B', '1'], ['B', 'A', '1']])
        self.assertEqual(reference(_o.CRC, [[['s', 'A', '2000'], ['s', 'B', '2002']], 1]), [])
        perf = [['s', 'A', '2000'], ['t', 'B', '2000'], ['t', 'A', '2000'], ['s', 'B', '2000'], ['s', 'B', '1990']]
        self.assertEqual(reference(_o.CRC, [perf, 0]), [['A', 'B', '2'], ['B', 'A', '2']])

    def test_cwt(self):
        self.assertEqual(reference(_o.CWT, ['The cat the CAT dog', 1]), [['cat', 2], ['the', 2]])
        self.assertEqual(reference(_o.CWT, ['b a c b a d', 2]), [['a', 2], ['b', 2], ['c', 1], ['d', 1]])
        self.assertEqual(reference(_o.CWT, ['x  y Y', 5]), [['y', 2], ['x', 1]])
        self.assertEqual(reference(_o.CWT, ['   ', 2]), [])

    def test_ccf(self):
        base = ['5,a,100,4111,shop', '3,b,5,4222,cafe', '5,c,1000,4111,cafe', '1,d,0,5555000011112222,shop']
        self.assertEqual(reference(_o.CCF1, [base]), [['d', 'APPROVE'], ['b', 'APPROVE'], ['a', 'APPROVE'], ['c', 'APPROVE']])
        self.assertEqual(reference(_o.CCF2, [base, ['merchant,cafe', 'max_amount,999']]), [['d', 'APPROVE'], ['b', 'DECLINE'], ['a', 'APPROVE'], ['c', 'DECLINE']])
        reqs = ['1,x,5,4111,shop', '2,y,5,4111,shop', '2,z,5,4222,shop', '9,w,5,4111,shop']
        self.assertEqual(reference(_o.CCF3, [reqs, [], ['1,x']]), [['x', 'APPROVE'], ['y', 'DECLINE'], ['z', 'APPROVE'], ['w', 'DECLINE']])
        self.assertEqual(reference(_o.CCF3, [reqs, ['card_number,4222'], ['2,y']]), [['x', 'APPROVE'], ['y', 'APPROVE'], ['z', 'DECLINE'], ['w', 'DECLINE']])

    def test_domain(self):
        for uid, args in [(_o.CBS, [[]]), (_o.CBS, [[['A1', 'a1']]]), (_o.CBS, [[['A1'], ['A1', 'B1']]]), (_o.CPS, [[True]]),
                          (_o.CDG, [[[1, 2], [1, 3]]]), (_o.CDG, [[[1, 0]]]), (_o.CLL, [[[1]], 0]), (_o.CRA, [[['c', 'p', 'r']], []]),
                          (_o.CNT, [[[1, [2]], [2, [1]]], []]), (_o.CNT, [[[1, [2, 3]], [3, []], [2, []]], []]), (_o.CNT, [[], []]),
                          (_o.CPM, ops('PointMatrix', [], [('isConnected', [0], [0, 0])])), (_o.CPM, ops('PointMatrix', [0], [])),
                          (_o.CAT, [[1], 0, 0, 50]), (_o.CAT, [[1], 0, 1, 101]), (_o.CDE, [[1, 2], 3]), (_o.CDE, [[], 1]), (_o.CDR, [[2, 1]]),
                          (_o.CIP, [['a', 'a'], [1, 1], [], []]), (_o.CIP, [['a'], [1], ['b'], [1]]), (_o.CIP, [['a'], [float('nan')], [], []]),
                          (_o.CBD, [[1] * 17, [1] * 17]), (_o.CBD, [[1], []]), (_o.COP, [['*'], [[0]]]), (_o.COP, [['_'], [[3]]]), (_o.COP, [['*x'], [[1, 1]]]),
                          (_o.CRC, [[['s', 'A', '20x0']], 0]), (_o.CRC, [[['s', 'r%d' % i, '1'] for i in range(201)], 0]), (_o.CWT, ['a1', 1]), (_o.CWT, ['a', 0]),
                          (_o.CCF1, [['1,a,1,4111']]), (_o.CCF1, [['1,a,1,4111,shop', '2,a,1,4111,shop']]), (_o.CCF2, [['1,a,1,4111,shop'], ['color,red']]),
                          (_o.CCF3, [['5,a,1,4111,shop'], [], ['4,a']]), (_o.CCF3, [['5,a,1,4111,shop'], [], ['6,b']])]:
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
        module = _load(f'gamma_h2h09b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
