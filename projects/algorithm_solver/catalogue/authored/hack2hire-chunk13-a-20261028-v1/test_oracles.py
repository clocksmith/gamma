import copy
from itertools import combinations
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


_o = _load('gamma_h2h13a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h13a_reference_test_cases', HERE / 'cases.py')
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
    def test_ncp(self):
        for args, want in [([1, []], 0), ([3, []], 3), ([4, [[0, 1], [2, 3]]], 4), ([5, [[0, 1], [1, 2], [3, 4]]], 6), ([3, [[0, 1], [1, 2]]], 0)]:
            self.assertEqual(reference(_o.NCP, args), want, args)

    def test_opb(self):
        self.assertEqual(reference(_o.OPB, [[]]), '')
        self.assertEqual(reference(_o.OPB, [[[1, 2], [2, 3, 1], [2, 3, 2], [2, 2, 2], [2, 5, 2], [1, 4], [2, 5, 2]]]), '0011' + '0')
        self.assertEqual(reference(_o.OPB, [[[2, 1, 1], [1, 0], [2, 1, 1], [1, 0], [2, 2, 1]]]), '101')  # x itself is never checked

    def test_oov(self):
        t = ops('VisitorTracker', [], [('getOldestOneTimeVisitor',), ('login', 'ann'), ('login', 'bo'), ('getOldestOneTimeVisitor',), ('login', 'ann'),
                                       ('getOldestOneTimeVisitor',), ('login', 'bo'), ('getOldestOneTimeVisitor',), ('login', 'cy'), ('login', 'ann'),
                                       ('getOldestOneTimeVisitor',)])
        self.assertEqual(reference(_o.OOV, t), [None, '', None, None, 'ann', None, 'bo', None, '', None, None, 'cy'])

    def test_osp(self):
        # keys price + index: [5, -1, -3, 8] -> [5, 0, -1, 11]; best 5 + 8
        for prices, want in [([5], 5), ([-3], -3), ([5, -1, -3, 8], 13), ([3, 3, 5, 6], 17), ([10, 1, 1, 1], 10), ([1, 0, 0, 0], 1), ([-2, -1], -1),
                             ([4, 3, 2], 9)]:
            self.assertEqual(reference(_o.OSP, [prices]), want, prices)

    def test_ots(self):
        for args, want in [([[0], [0]], 1), ([[1, 1, 1], [1, 1, 1]], 2), ([[0, 1, 2], [2, 1, 0]], 3), ([[0, 0, 0], [5, 5, 5]], 1),
                           ([[2, 0, 1, 0], [0, 1, 0, 3]], 2)]:
            self.assertEqual(reference(_o.OTS, args), want, args)

    def test_obs(self):
        self.assertEqual(reference(_o.OBS, [3, [1, 2, 3, 3, 2, 1]]), [0, 1, 2, 0, 1, 0])
        self.assertEqual(reference(_o.OBS, [4, [4, 1, 2, 4, 4, 4]]), [0, 0, 1, 2, 3, 1])

    def test_pci(self):
        for args, want in [([[], []], True), ([['#'], list('a#b#a')], True), ([['b'], list('ab')], True), ([[], list('ab')], False),
                           ([[], list('aA')], False), ([[' '], list('A a')], False), ([['x'], list('xxxx')], True)]:
            self.assertEqual(reference(_o.PCI, args), want, args)

    def test_pst(self):
        t = ops('PStack', [], [('push', 0, 5), ('push', 1, 7), ('peek', 2), ('pop', 2), ('peek', 1), ('push', 1, 9), ('size', 3), ('pop', 3),
                               ('push', 0, -1), ('size', 4), ('peek', 4), ('size', 2), ('pop', 1)])
        self.assertEqual(reference(_o.PST, t), [None, 1, 2, 7, 1, 5, 3, 2, 1, 4, 1, -1, 2, 0])

    def test_pbc(self):
        b = [[1, 2, 3], [3, 4], [4, 5], [6, 7]]
        self.assertEqual([reference(_o.PBC1, [b, p, q]) for p, q in [(1, 2), (1, 5), (2, 6), (1, 9)]], [True, True, False, False])
        self.assertEqual([reference(_o.PBC2, [b, p, q]) for p, q in [(1, 2), (1, 5), (2, 6), (1, 9), (5, 3)]], [1, 3, -1, -1, 2])
        self.assertEqual(reference(_o.PBC2, [[[1, 2, 3], [3, 4], [4, 5], [1, 5]], 2, 5]), 2)  # the shortcut board [1, 5]

    def test_pss(self):
        for cards, want in [(['A', '2', '3', '4', '5'], True), (['10', 'J', 'Q', 'K', 'A'], True), (['J', 'Q', 'K', 'A', '2'], False),
                            (['9', '7', '8', '6', '10'], True), (['2', '3', '4', '5', '7'], False)]:
            self.assertEqual(reference(_o.PSS, [cards]), want, cards)
        self.assertEqual(sum(reference(_o.PSS, [list(h)]) for h in combinations(_o.CARDS, 5)), 10)

    def test_peo(self):
        emps = [['2', '1', 'Bo'], ['1', '1', 'Ann'], ['3', '1', 'Cy'], ['4', '2', 'Dee Lane']]
        self.assertEqual(reference(_o.PEO, [emps]), 'Ann\n----Bo\n--------Dee Lane\n----Cy')
        self.assertEqual(reference(_o.PEO, [[['1', '1', 'Ceo']]]), 'Ceo')

    def test_rpw(self):
        races = [['Ann', 'Cy'], ['Ann', 'Cy'], ['Bo', 'Dee', 'Cy'], ['Bo', 'Dee', 'Cy'], ['Bo', 'Dee', 'Cy']]  # Ann 30, Bo 45, Cy 35, Dee 30
        self.assertEqual(reference(_o.RPW1, [races]), 'Bo')
        self.assertEqual(reference(_o.RPW2, [races]), ['Bo', 'Cy', 'Ann', 'Dee'])  # Ann and Dee tie on 30; Ann has 2 wins
        tie = [['Bo', 'Ann'], ['Ann', 'Bo']]
        self.assertEqual((reference(_o.RPW1, [tie]), reference(_o.RPW2, [tie])), ('Ann', ['Ann', 'Bo']))
        self.assertEqual(reference(_o.RPW2, [[['Zed', 'Amy', 'Bob', 'Cat', 'Dan']]]), ['Zed', 'Amy', 'Bob', 'Cat', 'Dan'])
        self.assertEqual(reference(_o.RPW2, [[['x', 'y', 'z', 'b', 'B', 'a', 'A']]]), ['x', 'y', 'z', 'A', 'B', 'a', 'b'])

    def test_rsp(self):
        self.assertEqual(reference(_o.RSP, [[[0, 1, 2], [1, 0, 2], [1, 2, 0]]]), [1, 0, 2])
        self.assertEqual(reference(_o.RSP, [[[0, 1], [1, 0]]]), [0, 1])
        self.assertEqual(reference(_o.RSP, [[[2, 1, 0], [2, 0, 1], [0, 1, 2]]]), [2, 0, 1])

    def test_rvc(self):
        ev = [['server', 'c1 c2', 'v1'], ['v1', 'c1', 'v2'], ['v2', 'c1', 'v3'], ['v1', 'c2', 'v3']]
        self.assertEqual(reference(_o.RVC, [ev]), ['v1', 'v2', 'v3'])
        self.assertEqual(reference(_o.RVC, [[['b', 'x', 'a'], ['a', 'y', 'b']]]), ['a', 'b'])
        self.assertEqual(reference(_o.RVC, [[['v1', 'c1 c1 c1', 'v2'], ['v2', 'c1', 'v1'], ['v3', 'a b', 'v1']]]), ['v1', 'v3', 'v2'])

    def test_rhn(self):
        # [[4,4,4],[4,3],[3,3]]: four 4s but three neighborhoods; [[1,1,1],[2],[2]]: the size-3 row needs 3 distinct numbers, only 2 exist
        for houses, want in [([[1, 1], [2, 2]], [[1, 2], [1, 2]]), ([[1, 1]], []), ([[3, 1, 2]], [[1, 2, 3]]), ([[5], [5], [5]], [[5], [5], [5]]),
                             ([[1, 1, 1], [2], [2]], []), ([[4, 4, 4], [4, 3], [3, 3]], []),
                             ([[2], [1, 1], [3, 3]], [[1], [1, 3], [2, 3]])]:  # counts 1:2, 3:2, 2:1; row 0 takes 1 (most copies, smaller)
            self.assertEqual(reference(_o.RHN, [houses]), want, houses)

    def test_rhn_canonical_filling_matches_exhaustive_feasibility(self):
        """ref_rhn asserts the filling succeeds exactly when backtracking finds an arrangement; exercise it widely."""
        rng = random.Random(7); seen = {True: 0, False: 0}
        for _ in range(3000):
            rows = [[rng.randrange(1, 5) for _ in range(rng.randrange(1, 4))] for _ in range(rng.randrange(1, 5))]
            out = reference(_o.RHN, [rows]); seen[out != []] += 1
        self.assertTrue(seen[True] > 100 and seen[False] > 100, seen)

    def test_rmk(self):
        for args, want in [([[5, 9, 3], 2, 1000], 9), ([[8, 8], 3, 1000], 6), ([[1, 2, 3], 10, 7], 0), ([[7], 1, 100], 3), ([[10**9], 3, 10**9 + 7], 125000000)]:
            self.assertEqual(reference(_o.RMK, args), want, args)

    def test_domain(self):
        V, S = 'VisitorTracker', 'PStack'
        for uid, args in [(_o.NCP, [0, []]), (_o.NCP, [2, [[0, 0]]]), (_o.NCP, [2, [[0, 2]]]), (_o.NCP, [2, [[0]]]),
                          (_o.OPB, [[[3, 1]]]), (_o.OPB, [[[2, 1, 2]]]), (_o.OPB, [[[2, 1, 0]]]), (_o.OPB, [[[1, -1]]]), (_o.OPB, [[[True, 1]]]),
                          (_o.OOV, ops(V, [], [('login', 'Ann')])), (_o.OOV, ops(V, [], [('logout', 'ann')])), (_o.OOV, [['Visitor'], [[]]]),
                          (_o.OSP, [[]]), (_o.OSP, [[10**9 + 1]]), (_o.OTS, [[0], [0, 0]]), (_o.OTS, [[-1], [0]]),
                          (_o.OBS, [0, []]), (_o.OBS, [2, [3]]), (_o.OBS, [2, [0]]),
                          (_o.PCI, [[], ['ab']]), (_o.PCI, [[], ['\n']]), (_o.PCI, [['a'] * 101, []]),
                          (_o.PST, ops(S, [], [('pop', 0)])), (_o.PST, ops(S, [], [('peek', 0)])), (_o.PST, ops(S, [], [('size', 1)])),
                          (_o.PST, ops(S, [], [('push', 0, 1), ('pop', 1), ('push', 3, 1)])), (_o.PST, ops(S, [], [('push', 0, 1.5)])),
                          (_o.PBC1, [[[1, 1]], 1, 2]), (_o.PBC1, [[[]], 1, 2]), (_o.PBC2, [[[1]], 1, 1]), (_o.PBC2, [[[0]], 1, 2]),
                          (_o.PSS, [['A', '2', '3', '4']]), (_o.PSS, [['A', 'A', '2', '3', '4']]), (_o.PSS, [['1', '2', '3', '4', '5']]),
                          (_o.PEO, [[]]), (_o.PEO, [[['1', '2', 'Ann'], ['2', '1', 'Bo']]]), (_o.PEO, [[['1', '1', 'Ann'], ['2', '2', 'Bo']]]),
                          (_o.PEO, [[['1', '1', 'Ann'], ['2', '3', 'Bo']]]), (_o.PEO, [[['1', '1', 'ann']]]), (_o.PEO, [[['1', '1', 'A'], ['1', '1', 'B']]]),
                          (_o.PEO, [[['1', '1', 'A'], ['2', '3', 'B'], ['3', '2', 'C']]]),
                          (_o.PEO, [[['c0', 'c0', 'A']] + [['c%d' % i, 'c%d' % (i - 1), 'A'] for i in range(1, 1500)]]),
                          (_o.RPW1, [[]]), (_o.RPW1, [[[]]]), (_o.RPW2, [[['Ann', 'Ann']]]), (_o.RPW2, [[['A1']]]),
                          (_o.RSP, [[]]), (_o.RSP, [[[0, 0]]]), (_o.RSP, [[[0, 1], [0]]]), (_o.RSP, [[[1]]]),
                          (_o.RVC, [[['server', 'a', 'server']]]), (_o.RVC, [[['v1', 'a', 'v1']]]), (_o.RVC, [[['v1', '', 'v2']]]),
                          (_o.RVC, [[['v1', 'a  b', 'v2']]]), (_o.RVC, [[['v1', 'A', 'v2']]]),
                          (_o.RHN, [[]]), (_o.RHN, [[[]]]), (_o.RHN, [[[0]]]),
                          (_o.RMK, [[], 1, 1]), (_o.RMK, [[1], -1, 1]), (_o.RMK, [[1], 1, 0]), (_o.RMK, [[-1], 1, 1]), (_o.RMK, [[1], 100001, 1])]:
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
        module = _load(f'gamma_h2h13a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
