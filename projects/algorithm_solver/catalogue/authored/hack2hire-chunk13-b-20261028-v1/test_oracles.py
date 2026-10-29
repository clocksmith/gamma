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


_o = _load('gamma_h2h13b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h13b_reference_test_cases', HERE / 'cases.py')
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

    def test_rcf(self):
        star = [[['F0', 'F1'], ['F1'], ['F0'], []], [['C0', 'C2'], ['C0', 'C1']]]
        chain = [[['F0'], ['F0', 'F1'], ['F1'], []], [['C0', 'C1'], ['C1', 'C2']]]
        self.check(_o.RCF1, [(star + [0], ['C1', 'C2']), (star + [1], ['C0']), (star + [3], []), (star + [4], []), (star + [-1], []), (chain + [0], ['C1'])])
        self.check(_o.RCF2, [(star + [1], ['C0', 'C2']), (chain + [0], ['C1', 'C2']), (chain + [3], []), ([[], [], 0], [])])

    def test_rcp(self):
        self.check(_o.RCP, [([[[10, 13]], 1], [[10, 11], [12, 13]]), ([[[5, 7], [-3, -1]], 2], [[5, 7], [-2, -1]]), ([[[1, 2]], 1], [[1, 2]]), ([[[1, 2]], 0], []),
                            ([[[4, 6], [0, 2]], 3], [[4, 6], [0, 1]]), ([[], 0], [])])

    def test_rmv(self):
        self.check(_o.RMV, [([['apple', 'Area', 'a', 'sky', 'OboE', 'io']], ['alppe', 'Aera', 'a', 'sky', 'OobE', 'io']), ([[]], [])])

    def test_rps(self):
        self.check(_o.RPS, [([['admin', 'editor', 'viewer', 'guest'], [['editor'], ['viewer'], [], ['viewer']], [['delete'], ['write'], ['read', 'list'], []], [[], [], [], ['list']]],
                             [['delete', 'list', 'read', 'write'], ['list', 'read', 'write'], ['list', 'read'], ['read']]),
                            ([['a', 'b', 'c'], [['b'], ['c'], []], [[], ['x'], ['y']], [['x'], ['y'], []]], [[], ['x'], ['y']]),
                            ([['solo'], [[]], [['k', 'k_b']], [['k']]], [['k_b']])])

    def test_rnc(self):
        self.check(_o.RNC, [([[[0, 0], [3, 4], [3, 0]], [0, 2, 3, 5, 7, 8, 9, 100]], [0, 0, 1, 1, 1, 2, 2, 2]), ([[[0, 0]], [0, 7]], [0, 0]),
                            ([[[0, 0], [6, 0], [0, 0]], [3, 6, 9, 12]], [0, 1, 0, 0]), ([[[0, 0], [2, 0]], [1]], [0])])

    def test_swh(self):
        self.check(_o.SWH, [([[['abc', []]], [['', [1, 2]], ['ab', []], ['c', []]]], True), ([[['', [2, 1]], ['c', []], ['ab', []]], [['abc', []]]], True),
                            ([[['', [1]], ['', [2]], ['x', []]], [['y', []]]], False), ([[['ab', []]], [['', [1, 2]], ['a', []], ['bb', []]]], False)])

    def test_sop(self):
        self.check(_o.SOP, [([[[4, 3], [2, 5], [9, 4]], [[1, [3, 3, 2]], [1, [5, 1]], [3, [4]], [0, [4, 9]]]], [[2, 4, 2], [], [9], []]),
                            ([[[10, 5]], [[3, [2, 2]], [3, [2]], [10, [1]]]], [[10, 10], [], []]), ([[[5, 0], [6, 2]], [[4, [1, 1, 1]], [4, [2]]]], [[], [6]])])

    def test_shs(self):
        t = ops('SearchHistory', [2], [('getTopK', 3), ('add', 'cat'), ('add', 'dog'), ('add', 'cat'), ('getTopK', 5), ('add', 'emu'), ('getTopK', 2), ('getTopK', 0)])
        self.check(_o.SHS, [(t, [None, [], None, None, None, ['cat', 'dog'], None, ['emu', 'cat'], []])])

    def test_ssr(self):
        hello = [[['b', 'c', 'lo'], ['a', 'b', 'hel'], ['c', 'd', '']]]
        self.check(_o.SSR1, [(hello, 'hello'), ([[['x', 'y', 'abc']]], 'abc')])
        self.check(_o.SSR2, [(hello, 'hello'), ([[['a', 'b', 'x'], ['b', 'a', 'y']]], ''), ([[['a', 'a', 'x']]], ''), ([[['a', 'b', 'x'], ['c', 'd', 'y']]], ''),
                             ([[['a', 'b', 'x'], ['c', 'd', 'y'], ['d', 'c', 'z']]], '')])
        self.check(_o.SSR3, [(hello, ['hello']), ([[]], []), ([[['m', 'n', 'x'], ['c', 'd', 'y'], ['d', 'e', 'z'], ['b', 'q', '']]], ['', 'yz', 'x'])])

    def test_sva(self):
        self.check(_o.SVA, [([['ab'], ['ba ba']], [['ab ab', 'ab ba', 'ba ab', 'ba ba']]), ([['act', 'cat'], ['tac', 'dog']], [['act', 'cat', 'tac'], ['dog']]), ([[], []], [])])

    def test_shr(self):
        self.check(_o.SHR, [([1, ['a:0:10', 'b:5:15', 'c:20:30']], ['a:0:10', 'b:11:15', 'c:16:30']), ([2, ['a:0:10', 'b:5:15', 'c:3:8', 'd:12:12']], ['a:0:10', 'c:3:8', 'b:9:15', 'd:12:12']),
                            ([1, ['z:0:5', 'a:0:5']], ['a:0:5']), ([1, ['a:0:10', 'b:2:5', 'c:3:20', 'd:4:30']], ['a:0:10', 'c:11:20', 'd:21:30']), ([1, []], [])])

    def test_sup(self):
        self.check(_o.SUP, [([[5], '1'], 5), ([[5], '0'], 0), ([[10, 5, 8, 1], '0101'], 18), ([[3, 9, 4], '011'], 13), ([[7, 2, 6, 4], '1011'], 17), ([[0, 0, 9], '001'], 9)])

    def test_src(self):
        routes = ['US:UK:UPS:5', 'US:UK:DHL:3', 'US:CA:FedEx:3', 'CA:UK:DHL:7', 'CA:UK:UPS:1', 'UK:FR:DHL:2', 'US:FR:UPS:20']
        self.check(_o.SRC1, [([routes, 'US', 'UK'], [['DHL', 3], ['UPS', 5]]), ([routes, 'UK', 'US'], [])])
        self.check(_o.SRC2, [([routes, 'US', 'UK'], [['US:DHL:UK', 3], ['US:FedEx:CA:UPS:UK', 4], ['US:UPS:UK', 5], ['US:FedEx:CA:DHL:UK', 10]]),
                             ([routes, 'US', 'FR'], [['US:DHL:UK:DHL:FR', 5], ['US:UPS:UK:DHL:FR', 7], ['US:UPS:FR', 20]])])
        self.check(_o.SRC3, [([routes, 'US', 'FR'], 5), ([routes, 'US', 'US'], 0), ([routes, 'UK', 'US'], -1), ([routes, 'CA', 'FR'], 3)])

    def test_spg(self):
        self.check(_o.SPG, [([['SD'], 0], -1), ([['SD'], 1], 1), ([['S.D'], 1], -1), ([['S.G.D'], 2], 4), ([['S..', '##.', 'D..'], 6], 6), ([['S#D'], 9], -1)])

    def test_smo(self):
        t = ops('SparseMatrix', [[[1, 0, 0], [-1, 0, 3]]], [('get', 1, 2), ('multiply', [[7, 0, 0], [0, 0, 0], [0, 0, 1]]), ('add', [[-1, 0, 0], [0, 2, 0]]),
                                                            ('set', 1, 2, 0), ('get', 1, 2), ('multiply', [[1], [1], [1]])])
        self.check(_o.SMO, [(t, [None, 3, [[0, 0, 7], [1, 0, -7], [1, 2, 3]], [[1, 0, -1], [1, 1, 2], [1, 2, 3]], None, 0, [[0, 0, 1], [1, 0, -1]]])])

    def test_sae(self):
        self.check(_o.SAE, [([[1]], -1), ([[2, 2]], 0), ([[1, 2, 3, 3, 2, 1]], 2), ([[1, 1, 1]], -1), ([[10, 3, 7]], 0)])

    def test_domain(self):
        for uid, args in [(_o.RCF1, [[['F0']], [[]], 0]), (_o.RCF1, [[['F1']], [['C0']], 0]), (_o.RCF2, [[['F0', 'F0']], [['C0']], 0]), (_o.RCF1, [[['F01']], [['C0']], 0]),
                          (_o.RCP, [[[1, 1]], 0]), (_o.RCP, [[[0, 5], [4, 6]], 0]), (_o.RCP, [[[0, 1]], -1]),
                          (_o.RMV, [['']]), (_o.RMV, [['a1']]),
                          (_o.RPS, [['a', 'b'], [['b'], ['a']], [[], []], [[], []]]), (_o.RPS, [['a'], [['a']], [[]], [[]]]), (_o.RPS, [['a', 'a'], [[], []], [[], []], [[], []]]),
                          (_o.RPS, [['a'], [['z']], [[]], [[]]]),
                          (_o.RNC, [[[0, 0], [1, 1]], [0]]), (_o.RNC, [[[0, 0], [0, 0]], [0]]), (_o.RNC, [[], [0]]), (_o.RNC, [[[0, 0]], [-1]]),
                          (_o.SWH, [[['', []]], [['a', []]]]), (_o.SWH, [[['a', [1]], ['b', []]], [['a', []]]]), (_o.SWH, [[['', [1, 1]], ['b', []]], [['a', []]]]),
                          (_o.SWH, [[['', [1]], ['', [2]], ['', [1]]], [['a', []]]]),
                          (_o.SOP, [[[1, 1], [1, 2]], []]), (_o.SOP, [[], [[0, []]]]), (_o.SOP, [[], [[0, [0]]]]),
                          (_o.SHS, [['SearchHistory'], [[0]]]), (_o.SHS, [['SearchHistory', 'add'], [[1], ['A']]]), (_o.SHS, [['SearchHistory', 'getTopK'], [[1], [101]]]),
                          (_o.SHS, [['SearchHistory', 'remove'], [[1], ['a']]]),
                          (_o.SSR1, [[]]), (_o.SSR1, [[['a', 'b', 'x'], ['c', 'd', 'y']]]), (_o.SSR1, [[['a', 'a', 'x']]]), (_o.SSR2, [[['a', 'b', 'x'], ['a', 'c', 'y']]]),
                          (_o.SSR3, [[['a', 'b', 'x'], ['b', 'a', 'y']]]), (_o.SSR3, [[['a', 'b', 'X']]]),
                          (_o.SVA, [['ab', 'ab'], []]), (_o.SVA, [[], ['a  b']]), (_o.SVA, [['abc', 'acb', 'bac', 'bca', 'cab', 'cba'], [' '.join(['abc'] * 4)]]),
                          (_o.SHR, [0, []]), (_o.SHR, [1, ['a:5:4']]), (_o.SHR, [1, ['a:0:1', 'a:2:3']]), (_o.SHR, [1, ['a:01:3']]),
                          (_o.SUP, [[1, 2], '1']), (_o.SUP, [[1], '2']), (_o.SUP, [[-1], '1']),
                          (_o.SRC1, [['US:UK:a:1'], 'US', 'US']), (_o.SRC2, [['US:US:a:1'], 'US', 'UK']), (_o.SRC3, [['US:UK:a:1', 'US:UK:a:2'], 'US', 'UK']),
                          (_o.SRC1, [['US:UK:a:0'], 'US', 'UK']), (_o.SRC3, [[], 'US', 'UK']),
                          (_o.SPG, [['S'], 1]), (_o.SPG, [['SDD'], 1]), (_o.SPG, [['SD', 'D'], 1]), (_o.SPG, [['SD'], 101]),
                          (_o.SMO, [['SparseMatrix', 'get'], [[[[1]]], [1, 0]]]), (_o.SMO, [['SparseMatrix', 'add'], [[[[1]]], [[[1, 2]]]]]),
                          (_o.SMO, [['SparseMatrix', 'multiply'], [[[[1, 2]]], [[[1, 2]]]]]), (_o.SMO, [['SparseMatrix'], [[[[1], [2, 3]]]]]),
                          (_o.SAE, [[]]), (_o.SAE, [[0, 1]])]:
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
        module = _load(f'gamma_h2h13b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
