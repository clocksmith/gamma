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


_o = _load('gamma_h2h06a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h06a_reference_test_cases', HERE / 'cases.py')
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
    def test_eod(self):
        rows = [['cust', 'co', 300], ['co', 'merch', 1000], ['bank', 'co', 700]]
        self.assertEqual(reference(_o.EOD1, [rows]), [['bank', -700], ['co', 0], ['cust', -300], ['merch', 1000]])
        # merch +1000 is the only creditor; debtors bank -700 then cust -300
        self.assertEqual(reference(_o.EOD2, [rows]), [['bank', 'merch', 700], ['cust', 'merch', 300]])
        self.assertEqual(reference(_o.EOD2, [[['a', 'b', 5], ['c', 'd', 5]]]), [['a', 'b', 5], ['c', 'd', 5]])

    def test_eval(self):
        self.assertEqual(reference(_o.EVAL, ['add(1,sub(10, 4),3)']), 10)
        self.assertEqual(reference(_o.EVAL, ['sub(sub(1,2),-5)']), 4)
        self.assertEqual(reference(_o.EVAL, ['42']), 42)

    def test_fac(self):
        costs = [[1, 5, 3], [2, 9, 4], [3, 1]]
        self.assertEqual(reference(_o.FAC1, [costs]), 1 + 2 + 1)
        self.assertEqual(reference(_o.FAC2, [costs]), 1 + 4 + 1)  # 0, 2, 1
        self.assertEqual(reference(_o.FAC3, [costs, [[0, 1], [0, 2]]]), 1 + 4 + 1)  # centre 0 (1): leaves 2 (4) and 1 (1); centre 2 gives 3 + 2 + 3
        self.assertEqual(reference(_o.FAC2, [[[1], [2]]]), -1)

    def test_fsc(self):
        t = ops('FileSystemStats', [['a.txt,10,x,y', 'b,4,y,y', 'c,1']], [('getTotalSize',), ('getCollectionSize', 'y'), ('getTopCollections', 5),
                                                                         ('setParent', 'x', 'y'), ('setParent', 'y', 'z'), ('getHierarchySize', 'z'), ('getHierarchySize', 'x')])
        self.assertEqual(reference(_o.FSC, t), [None, 15, 14, ['y', 'x'], None, None, 24, 10])
        with self.assertRaises(ValueError):
            validate_domain(_o.FSC, ops('FileSystemStats', [[]], [('setParent', 'a', 'b'), ('setParent', 'b', 'a')]))

    def test_fsd(self):
        dirs = ['/a', '/a/b']; edges = [['/a', '/a/z'], ['/a', '/a/b'], ['/a/b', '/a/b/y'], ['/a', '/a/c']]
        files = ['/a/z', '/a/b/y', '/a/c']
        self.assertEqual(reference(_o.FSD, [dirs, edges, files, '/a']), ['/a/z', '/a/b/y', '/a/b', '/a/c', '/a'])
        self.assertEqual(reference(_o.FSD, [dirs, edges, files, '/a/b']), ['/a/b/y', '/a/b'])
        self.assertEqual(reference(_o.FSD, [dirs, edges, files, '/q']), [])

    def test_fsds(self):
        root = {'name': 'root', 'children': [{'name': 'a', 'children': [{'name': 'e', 'children': [{'name': 'i', 'size': 584}]}, {'name': 'f', 'size': 29116}]},
                                          {'name': 'b', 'size': 14848514}]}
        self.assertEqual(reference(_o.FSDS, [root, 100000]), 584 + 29700)

    def test_bott(self):
        self.assertEqual(reference(_o.BOTT, [5, [[0, 1], [0, 2], [1, 3], [2, 3], [3, 4]]]), [0, 3, 4])
        self.assertEqual(reference(_o.BOTT, [3, [[0, 2], [1, 2]]]), [2])

    def test_mid(self):
        self.assertEqual(reference(_o.MID1, [[['b', 'c'], ['a', 'b'], ['d', 'e'], ['c', 'd']]]), 'c')
        # paths a-b-d (middle b), a-c-d (c), a-d (L=2: left middle a)
        self.assertEqual(reference(_o.MID2, [[['a', 'b'], ['a', 'c'], ['b', 'd'], ['c', 'd'], ['a', 'd']]]), ['a', 'b', 'c'])

    def test_exit(self):
        g = [[0, 0, 1, 0], [1, 1, 1, 0], [0, 0, 0, 1]]
        self.assertEqual(reference(_o.EXIT1, [g, [1, 2]]), 1)
        self.assertEqual(reference(_o.EXIT2, [g, [1, 2]]), [0, 2])
        self.assertEqual(reference(_o.EXIT2, [[[1, 1, 1]], [0, 1]]), [0, 0])
        self.assertEqual(reference(_o.EXIT1, [[[1]], [0, 0]]), -1)

    def test_closed_forms_match_relaxation(self):
        for r in (5, 7, 9, 11):
            for c in (5, 6, 9):
                g, start, moves, cell = _o.serpentine_exit(r, c)
                if r * c <= 400:
                    self.assertEqual((reference(_o.EXIT1, [g, start]), reference(_o.EXIT2, [g, start])), (moves, cell))
        for r in (1, 3, 5, 7, 9):
            for c in (3, 4, 5, 8):
                g, cells = _o.serpentine_path(r, c)
                if r * c <= 400: self.assertEqual(reference(_o.PATH, [g]), cells, (r, c))

    def test_offer(self):
        offers = [['o1', '0', '10', '1'], ['o2', '5', '20', '2']]
        events = [['u', '6', 'redeem', 'o2'], ['u', '3', 'redeem', 'o1'], ['u', '4', 'redeem', 'o1'], ['v', '2', 'redeem', 'o2'], ['u', '12', 'redeem', 'o2']]
        self.assertEqual(reference(_o.OFFER, [offers, events, 8]), [['u', ['o2']], ['v', ['o1', 'o2']]])

    def test_prefix(self):
        self.assertEqual(reference(_o.PREFIX, [['zebra', 'dog', 'duck', 'dove']]), ['z', 'dog', 'du', 'dov'])

    def test_hub(self):
        self.assertEqual(reference(_o.HUB, [[8, 4, 6, 4], [[], ['1:3'], ['9:9'], []], 4, '3:8']), 3)
        self.assertEqual(reference(_o.HUB, [[8, 4], [['8:9'], ['0:3']], 4, '3:8']), -1)

    def test_dna(self):
        self.assertEqual(reference(_o.DNA, [['ACG', 'CGT', 'CGT', 'AT', 'AT', 'GGA']]), 2 + 1)

    def test_login(self):
        logs = ['a signin 1', 'b signin 2', 'b signout 4', 'c signout 5', 'c signin 6', 'c signin 9', 'a signout 9', 'c signout 10']
        self.assertEqual(reference(_o.LOGIN, [logs, 2]), ['b', 'c'])

    def test_city(self):
        self.assertEqual(reference(_o.CITY, [['p1', 'p2', 'p3'], [3, 2, 1], [3, 2, 3], ['p1', 'p2', 'p3']]), ['p3', 'NONE', 'p1'])
        self.assertEqual(reference(_o.CITY, [['b', 'a', 'q'], [1, 1, 1], [1, 9, 5], ['q']]), ['a'])

    def test_path(self):
        self.assertEqual(reference(_o.PATH, [[[1, 0, 0], [1, 1, 0], [1, 1, 1]]]), 3)  # two diagonal moves
        self.assertEqual(reference(_o.PATH, [[[0, 1], [1, 1]]]), -1)

    def test_domain(self):
        for uid, args in [(_o.EOD1, [[['a', 'a', 1]]]), (_o.EOD2, [[['a', 'b', 0]]]), (_o.EVAL, ['add(1)']), (_o.EVAL, ['sub(1,2,3)']), (_o.EVAL, ['add(1,2']),
                          (_o.EVAL, ['-0']), (_o.FAC1, [[[]]]), (_o.FAC3, [[[1], [1]], [[0, 0]]]), (_o.FSD, [['/a'], [], ['/a/f'], '/a']),
                          (_o.FSDS, [{'name': 'f', 'size': 1}, 0]), (_o.BOTT, [2, [[0, 1], [1, 0]]]), (_o.MID1, [[['a', 'b'], ['c', 'd']]]),
                          (_o.MID2, [[['a', 'a']]]), (_o.EXIT1, [[[0]], [0, 0]]), (_o.OFFER, [[['o', '5', '4', '1']], [], 0]),
                          (_o.PREFIX, [['ab', 'abc']]), (_o.HUB, [[1], [['5:4']], 1, '0:0']), (_o.DNA, [['ACGU']]),
                          (_o.LOGIN, [['a signin 5', 'a signout 4'], 1]), (_o.CITY, [['a', 'b'], [1, 1], [2, 2], ['a']]), (_o.PATH, [[[1, 10]]])]:
            with self.assertRaises(ValueError, msg=str(args)[:60]): validate_domain(uid, args)

    def test_generated_cases_domain_valid_and_shallow(self):
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True):
                validate_domain(uid, row['args'])
                self.assertLessEqual(depth(row['args']), 200)

    def test_contract_layouts_match_classes(self):
        self.assertEqual(set(CONTRACTS), set(_o.IDS))
        for uid, row in CONTRACTS.items():
            self.assertEqual(row['spec_basis'], 'inferred')
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
        module = _load(f'gamma_h2h06a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
