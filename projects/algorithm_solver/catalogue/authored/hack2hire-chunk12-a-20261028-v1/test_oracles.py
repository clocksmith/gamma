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


_o = _load('gamma_h2h12a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h12a_reference_test_cases', HERE / 'cases.py')
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
    def test_nary_format(self):
        vals, kids = _o.nary_parse([1, None, 3, 2, 4, None, 5, 6])
        self.assertEqual((vals, kids), ([1, 3, 2, 4, 5, 6], [[1, 2, 3], [4, 5], [], [], [], []]))
        self.assertEqual(_o.nary_serialize(vals, kids), [1, None, 3, 2, 4, None, 5, 6])
        self.assertEqual(_o.nary_parse([]), ([], []))
        self.assertEqual(_o.nary_parse([1, None, 2, 3, None, None, 4])[1], [[1, 2], [], [3], []])

    def test_lmn(self):
        for tree, want in [([], 0), ([7], 1), ([1, None, 3, 2, 4, None, 5, 6], 2), ([1, None, 2, None, 3, 4, 5], 3), ([1, None, 2, 3, None, 4, None, 5], 2)]:
            self.assertEqual(reference(_o.LMN, [tree]), want)

    def test_lur(self):
        recs = [['id', 'name', 'email', 'company'], ['1', 'Ann', 'a@x.io', 'Acme'], ['2', 'Ann', 'a@x.io', 'Bolt'], ['3', 'Bo', 'b@x.io', 'Acme'],
                ['4', 'Bo', 'a@x.io', ''], ['5', 'Cy', '', '']]
        w = ['name:0.5', 'email:0.3', 'company:0.2']
        self.assertEqual(reference(_o.LUR1, [recs, w, 0.5]), [['1', '2'], ['3', '4']])
        self.assertEqual(reference(_o.LUR1, [recs, w, 0.3]), [['1', '2'], ['1', '4'], ['2', '4'], ['3', '4']])
        self.assertEqual(reference(_o.LUR2, [recs, w, 0.3]), [['1', '2', '3', '4']])
        self.assertEqual(reference(_o.LUR2, [recs, w, 0.5]), [['1', '2'], ['3', '4']])
        self.assertEqual(reference(_o.LUR3, [recs, w, 0.3]), ['2', '1', '4', '3', ''])  # 4 ties with 1 and 2 (0.3) but scores 0.5 with 3
        self.assertEqual(reference(_o.LUR3, [recs, w, 0.2]), ['2', '1', '4', '3', ''])
        self.assertEqual(reference(_o.LUR3, [recs, ['company:1'], 0]), ['3', '1', '1', '1', '1'])  # threshold 0 links everyone; empty never matches
        # 0.1 + 0.2 must reach 0.3 exactly
        r = [['id', 'a', 'b', 'c'], ['x', 'p', 'q', 'r'], ['y', 'p', 'q', 's']]
        self.assertEqual(reference(_o.LUR1, [r, ['a:0.1', 'b:0.2', 'c:0.7'], 0.3]), [['x', 'y']])

    def test_lfc(self):
        deps = [['api', 'auth'], ['api', 'db'], ['auth', 'db'], ['db', 'disk'], ['cache', 'db']]
        self.assertEqual(reference(_o.LFC, [deps, 'api']), [['api', 1], ['auth', 1], ['cache', 0], ['db', 2], ['disk', 2]])
        self.assertEqual(reference(_o.LFC, [[], 'solo']), [['solo', 1]])
        diamond = [['e', 'a'], ['e', 'b'], ['a', 'c'], ['b', 'c'], ['c', 'd'], ['e', 'd']]
        self.assertEqual(reference(_o.LFC, [diamond, 'e']), [['a', 1], ['b', 1], ['c', 2], ['d', 3], ['e', 1]])

    def test_lvp(self):
        for s, want in [('', 0), ('()', 2), ('(())', 4), ('([])', 2), ('[()]', 4), ('{[()]}', 6), ('[{}]', 2), (')()())', 4), ('(]', 0),
                        ('{}[]()', 6), ('([)]', 0), ('(()[]', 4), ('[[]]{{}}', 8), ('{(})', 0)]:
            self.assertEqual(reference(_o.LVP, [s]), want, s)

    def test_mes(self):
        self.assertEqual(reference(_o.MES, [['U']]), 0)
        self.assertEqual(reference(_o.MES, [['XXX', 'XUX', 'XXX']]), -1)
        self.assertEqual(reference(_o.MES, [['XXXX', 'XU.X', 'XX.X']]), 2)
        self.assertEqual(reference(_o.MES, [['XXXX', 'XU.X', 'XXPX']]), -1)  # threat reaches the exit at the same minute
        self.assertEqual(reference(_o.MES, [['XXXXX', 'XU..X', 'XXX.X', 'XXXPX']]), -1)
        self.assertEqual(reference(_o.MES, [['XXXXXX', 'XU...X', 'XXX..X', 'XXX..P']]), -1)
        self.assertEqual(reference(_o.MES, [['XXXXXXX', 'XP.U..X', 'XXXXX..']]), 3)  # the threat chases one step behind
        self.assertEqual(reference(_o.MES, [['XXXXX', '.U..P', 'XXXXX']]), 1)
        self.assertEqual(reference(_o.MES, [['XXXXXXX', 'X.....X', 'XU....X', 'X.....X', 'XXXXX.X', 'XXXXXPX']]), -1)

    def test_mco_matches_flip_search(self):
        """The window rule (at most k zero blocks) against a search over real segment flips."""
        from itertools import product
        for n in range(1, 8):
            for bits in product('01', repeat=n):
                s = ''.join(bits)
                reach, frontier = {s}, {s}
                for k in range(3):
                    best = max(max((len(r) for r in t.split('0')), default=0) for t in reach)
                    self.assertEqual(reference(_o.MCO, [s, k]), best, (s, k))
                    nxt = set()
                    for t in frontier:
                        for i in range(n):
                            for j in range(i + 1, n + 1):
                                nxt.add(t[:i] + ''.join('1' if c == '0' else '0' for c in t[i:j]) + t[j:])
                    frontier = nxt - reach; reach |= nxt

    def test_mfd(self):
        self.assertEqual(reference(_o.MFD, [[5], 0]), 0)
        self.assertEqual(reference(_o.MFD, [[3, 1, 4, 1, 5], 1]), 12)
        self.assertEqual(reference(_o.MFD, [[3, 1, 4, 1, 5], 2]), 12)  # at most (5 + 2) // 2 = 3 flights
        self.assertEqual(reference(_o.MFD, [[1, 9, 1, 9], 1]), 18)
        self.assertEqual(reference(_o.MFD, [[2, 2, 2], 5]), 6)

    def test_mle(self):
        self.assertEqual(reference(_o.MLE, [[2, 1, 3, 1], [1, 0, 2, 0], 6]), [2, 3, 2, 1])
        self.assertEqual(reference(_o.MLE, [[0, 0], [5, 0], 4]), [0, 1])
        self.assertEqual(reference(_o.MLE, [[5], [0], 4]), [0])

    def test_mbt(self):
        for args, want in [([1, []], 0), ([3, [1, 1, 1]], 3), ([2, [1, 1, 2, 2, 3]], 4), ([2, [5, 5, 5, 6]], 2), ([3, [1, 2, 3, 1, 2, 3, 4]], 6),
                           ([4, [1, 2, 3]], 0), ([1, [4, 4, 4]], 1)]:
            self.assertEqual(reference(_o.MBT, args), want, args)

    def test_mbh(self):
        for g, want in [(['P'], 0), (['-'], -1), (['P--'], 2), (['P-X-'], -1), (['---', '-P-', '---'], 2), (['P----', 'XXXX-', '-----'], 10), (['X'], 0), (['XX', 'XP'], 0)]:
            self.assertEqual(reference(_o.MBH, [g]), want, g)

    def test_mio(self):
        for iv, want in [([], 0), ([[1, 3], [3, 5]], 2), ([[1, 2], [3, 4]], 1), ([[1, 10], [2, 3], [4, 5], [2, 4]], 3), ([[0, 0], [0, 0], [-1, 0]], 3)]:
            self.assertEqual(reference(_o.MIO, [iv]), want)

    def test_mmp(self):
        self.assertEqual(reference(_o.MMP, [1, [], 0, 0]), 1)
        self.assertEqual(reference(_o.MMP, [2, [[1, 0, 3]], 0, 1]), -1)
        self.assertEqual(reference(_o.MMP, [3, [[0, 1, 2], [1, 2, 3], [0, 2, 5]], 0, 2]), 6)
        self.assertEqual(reference(_o.MMP, [4, [[0, 1, 0], [1, 3, 10], [0, 2, 1], [2, 3, 1]], 0, 3]), 1)
        self.assertEqual(reference(_o.MMP, [3, [[0, 1, 5], [1, 0, 5], [1, 2, 0]], 0, 2]), 0)
        self.assertEqual(reference(_o.MMP, [4, [[0, 1, 2], [1, 2, 2], [2, 1, 9], [2, 3, 2], [1, 3, 1]], 0, 3]), 8)  # simple paths only

    def test_mvf(self):
        for d, want in [([[0]], [0, 0]), ([[1, 1], [2, 2]], [4, 1]), ([[7, 0, 7], [0, 7, 0]], [21, 2]), ([[3, 3], [3, 3]], [6, 0]),
                        ([[0, 5], [5, 0], [5, 5]], [10, 1])]:
            self.assertEqual(reference(_o.MVF, [d]), want, d)

    def test_mnt(self):
        self.assertEqual(reference(_o.MNT, [[], []]), [])
        self.assertEqual(reference(_o.MNT, [[1, None, 2, 3], [10, None, 20, None, 30]]), [11, None, 22, 3, None, 30])
        self.assertEqual(reference(_o.MNT, [[1, None, 2, None, 3], [1, None, 5, 6, None, None, 7]]), [2, None, 7, 6, None, 3, None, 7])
        self.assertEqual(reference(_o.MNT, [[], [2, None, 3]]), [2, None, 3])

    def test_mrp(self):
        for tree, want in [([], 0), ([7], 7), ([1, None, 3, 2, 4, None, 5, 6], 3), ([-5, None, 2, -9, None, None, 1], -13), ([1, None, -1, 5, None, -10], -10)]:
            self.assertEqual(reference(_o.MRP, [tree]), want, tree)

    def test_mmq(self):
        t = ops('MinMaxQueue', [], [('enqueue', 3), ('enqueue', 1), ('enqueue', 2), ('getMin',), ('getMax',), ('dequeue',), ('getMax',), ('dequeue',),
                                    ('getMin',), ('enqueue', 2), ('getMax',), ('dequeue',), ('getMin',)])
        self.assertEqual(reference(_o.MMQ, t), [None, None, None, None, 1, 3, 3, 2, 1, 2, None, 2, 2, 2])

    def test_domain(self):
        Q = 'MinMaxQueue'
        recs = [['id', 'name'], ['1', 'a']]
        for uid, args in [(_o.LMN, [[None]]), (_o.LMN, [[1, None]]), (_o.LMN, [[1, 2]]), (_o.LMN, [[1, None, 2, None, None, 3]]), (_o.LMN, [[True]]),
                          (_o.LMN, [[1, None, None, 2]]), (_o.MRP, [[10**9 + 1]]),
                          (_o.LUR1, [recs, ['name:0.5'], 0.5]), (_o.LUR1, [recs, ['id:1'], 0.5]), (_o.LUR1, [recs, ['name:1'], 0.12345]),
                          (_o.LUR1, [recs, ['name:1'], True]), (_o.LUR1, [recs, ['name:1'], 1.5]), (_o.LUR1, [recs, ['name:1'], '0.5']),
                          (_o.LUR2, [[['id', 'name'], ['1', 'a'], ['1', 'b']], ['name:1'], 1]), (_o.LUR3, [[['name']], ['name:1'], 1]),
                          (_o.LUR3, [[['id', 'name', 'name']], ['name:1'], 1]), (_o.LUR1, [recs, ['name:1', 'name:0'], 1]), (_o.LUR1, [recs, ['name:0.30000'], 1]),
                          (_o.LFC, [[['a', 'a']], 'a']), (_o.LFC, [[['a', 'b'], ['b', 'a']], 'a']), (_o.LFC, [[['a', 'b'], ['a', 'b']], 'a']), (_o.LFC, [[], 'A']),
                          (_o.LFC, [[['a%d' % i, x] for i in range(54) for x in ('b%d' % i, 'c%d' % i)] + [['b%d' % i, 'a%d' % (i + 1)] for i in range(53)]
                                    + [['c%d' % i, 'a%d' % (i + 1)] for i in range(53)], 'a0']),
                          (_o.LVP, ['(a)']), (_o.LVP, ['(' * 100001]),
                          (_o.MES, [['..']]), (_o.MES, [['UU']]), (_o.MES, [['U', '..']]), (_o.MES, [[]]), (_o.MES, [['U-']]),
                          (_o.MCO, ['', 0]), (_o.MCO, ['012', 0]), (_o.MCO, ['1', -1]),
                          (_o.MFD, [[], 1]), (_o.MFD, [[-1], 1]), (_o.MFD, [[1] * 1001, 1000]),
                          (_o.MLE, [[1], [1, 2], 3]), (_o.MLE, [[], [], 3]), (_o.MLE, [[1], [1], 10**14 + 1]),
                          (_o.MBT, [0, [1]]), (_o.MBT, [1, [0]]),
                          (_o.MBH, [['P-', 'P']]), (_o.MBH, [['P.']]),
                          (_o.MIO, [[[2, 1]]]), (_o.MIO, [[[1]]]),
                          (_o.MMP, [13, [], 0, 0]), (_o.MMP, [2, [[0, 0, 1]], 0, 1]), (_o.MMP, [2, [[0, 1, 1], [0, 1, 2]], 0, 1]), (_o.MMP, [2, [[0, 1, 11]], 0, 1]),
                          (_o.MMP, [2, [], 0, 2]),
                          (_o.MVF, [[]]), (_o.MVF, [[[1, 2], [1]]]), (_o.MVF, [[[8]]]),
                          (_o.MNT, [[1], [None]]),
                          (_o.MMQ, ops(Q, [], [('dequeue',)])), (_o.MMQ, ops(Q, [], [('enqueue', 1), ('dequeue',), ('getMin',)])),
                          (_o.MMQ, ops(Q, [], [('enqueue', 1.5)])), (_o.MMQ, ops(Q, [], [('size',)])), (_o.MMQ, [['MinQueue'], [[]]])]:
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
        module = _load(f'gamma_h2h12a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
