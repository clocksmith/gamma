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


_o = _load('gamma_h2h16a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h16a_reference_test_cases', HERE / 'cases.py')
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

    def test_gwc(self):
        doc = ['alpha', 'Alexandra', 'beta', 'gamma', 'alex', 'delta', 'ALEX', 'Alex']
        self.check(_o.GWC1, [([doc, 'Alex', 0], ['Alexandra', 'Alex']), ([doc, 'Alex', 1], ['alpha', 'Alexandra', 'beta', 'ALEX', 'Alex']), ([doc, 'zeta', 3], []),
                             ([['a', 'a', 'b'], 'a', 0], ['a', 'a']), ([[], 'x', 2], [])])
        doc = ['m1', 'a', 'b', 'c', 'd', 'm2', 'e', 'f', 'g', 'h', 'i', 'm3']
        self.check(_o.GWC2, [([doc, 'm', 0, 0], [['m1'], ['m2'], ['m3']]), ([doc, 'm', 1, 1], [['m1', 'a'], ['d', 'm2', 'e'], ['i', 'm3']]),
                             ([doc, 'm', 0, 4], [['m1', 'a', 'b', 'c', 'd', 'm2', 'e', 'f', 'g', 'h'], ['m3']]), ([['m', 'x', 'm'], 'm', 0, 0], [['m'], ['m']])])

    def test_ges(self):
        self.check(_o.GES, [([[]], []), ([[[3, 'a', 'x', 'y'], [1, 'b', 'x', 'z'], [2, 'c', 'w', 'z'], [9, 'd', 'e', 'f']]], [[1, 2, 3], [9]]),
                            ([[[5, 'a', 'b', 'c'], [4, 'b', 'c', 'a']]], [[4], [5]])])

    def test_hee(self):
        self.check(_o.HEE, [([['Q'], [''], [0]], ['']), ([['U', 'U', 'Q', 'U', 'Q', 'U', 'Q'], ['b', 'a', '', 'b', '', 'a', ''], [5, 5, 0, -1, 0, -10, 0]], ['a', 'a', 'b']),
                            ([['U', 'Q', 'U', 'Q'], ['x', '', 'x', 'zz'], [-3, 7, 3, -1]], ['x', 'x'])])

    def test_jbs(self):
        self.check(_o.JBS, [(['', ''], 1.0), (['a', ''], 0.0), (['Joe Pizza Co', 'Pizza Co Inc'], 0.5), (['a b c', 'A B C'], 0.0), (['a a a', 'a'], 1.0),
                            (['a b c d e f g h', 'a'], 0.13), (['a b c', 'a d e f g h i j'], 0.1), (['a b', 'a c'], 0.33), (['a b c', 'a b d'], 0.5)])

    def test_lot(self):
        self.check(_o.LOT, [([[], []], []), ([['b', 'a', 'c'], [['a', 'c'], ['b', 'c']]], [['a', 'b'], ['c']]), ([['x', 'y'], [['x', 'y'], ['y', 'x']]], []),
                            ([['d', 'c', 'b', 'a'], [['a', 'b'], ['b', 'c'], ['a', 'c'], ['a', 'd']]], [['a'], ['b', 'd'], ['c']])])

    def test_lps(self):
        self.check(_o.LPS, [(['a'], 0), (['aa'], 1), (['aaaa'], 3), (['abcab'], 2), (['aabcdaabc'], 4), (['abcd'], 0)])

    def test_mes(self):
        self.check(_o.MES, [([1, []], 0), ([2, [[0, 1]]], 3), ([3, [[0, 1], [1, 2]]], 3 * 2 + 1 + 2), ([4, [[0, 1], [0, 2], [0, 3]]], 4 * 3 + 1 + 2 + 3)])

    def test_mnk(self):
        self.check(_o.MNK, [(['1', 0], '1'), (['1234', 2], '5534'), (['6142', 1], '6542'), (['555', 2], '555'), (['105', 5], '555'), (['99', 2], '99')])

    def test_mst(self):
        self.check(_o.MST, [([[]], 0), ([[4, 2]], 0), ([[1, 2, 3]], 2), ([[1, 2, 3, 4, 5, 6]], 5 + 3), ([[9, 1, 8, 2, 7, 3, 6, 4, 5]], 8 + 6 + 4)])

    def test_mpq(self):
        self.check(_o.MPQ, [([[5], [3], 4], [0, -1]), ([[5], [3], 5], [3, 0]), ([[2, 3], [3, 4], 6], [9, 0]), ([[2, 3], [4, 6], 6], [12, 0]), ([[1, 2], [1, 3], 7], [9, 1])])

    def test_mss(self):
        self.check(_o.MSS, [([[], []], 0), ([[['lodge', 2, 'a'], ['a', 1, 'b'], ['lodge', 0, 'b']], [['a', 4], ['b', 3]]], 4),
                            ([[['lodge', 9, 'a']], [['a', 1]]], -8), ([[['lodge', 0, 'a'], ['lodge', 5, 'a'], ['x', 0, 'lodge']], [['a', 2], ['x', 100]]], 2),
                            ([[['lodge', 1, 'a'], ['a', 1, 'b'], ['a', 1, 'c'], ['c', 1, 'd']], [['a', 1], ['b', 1], ['c', 2], ['d', 0]]], 0)])

    def test_msp(self):
        self.check(_o.MSP, [([[1], 1], 1), ([[3], 2], 5), ([[1, 3, 1], 2], 5), ([[2, 3, 1], 3], 6), ([[3, 3, 3], 5], 2 + 3 + 1 + 2 + 3), ([[4, 1], 5], 1 + 2 + 3 + 4 + 1)])

    def test_mcs(self):
        self.check(_o.MCS, [(['abc', 'cde'], 'abcde'), (['abc', 'def'], 'abcdef'), (['abab', 'abab'], 'abab'), (['abcab', 'ab'], 'abcab'), (['xab', 'abab'], 'xabab'),
                            (['aaa', 'aaaa'], 'aaaa')])

    def test_mje(self):
        logs = {'b': [{'time': 2, 'type': 'idle'}], 'a': [{'time': 2, 'type': 'send', 'target': 'b'}, {'time': 2, 'type': 'idle'}]}
        self.check(_o.MJE, [([logs], [{'serverId': 'a', 'time': 2, 'type': 'send', 'target': 'b'}, {'serverId': 'a', 'time': 2, 'type': 'idle'}, {'serverId': 'b', 'time': 2, 'type': 'idle'}]),
                            ([{'a': []}], [])])

    def test_mti(self):
        self.check(_o.MTI, [([[], []], []), ([[[1, 3], [6, 9]], [[2, 5]]], [[1, 5], [6, 9]]), ([[[1, 3]], [[3, 5]]], [[1, 5]]), ([[[1, 2]], [[3, 4]]], [[1, 2], [3, 4]]),
                            ([[[0, 10]], [[2, 3], [5, 6], [11, 12]]], [[0, 10], [11, 12]]), ([[[1, 1], [3, 3]], [[2, 2]]], [[1, 1], [2, 2], [3, 3]])])

    def test_mua(self):
        self.check(_o.MUA, [([[], []], []), ([[1, 1, 2], []], [1, 2]), ([[1, 3, 5], [2, 3, 4]], [1, 2, 3, 4, 5]), ([[1, 2, 2, 3], [2, 2, 2]], [1, 2, 3])])

    def test_domain(self):
        bad = [(_o.GWC1, [['a'], '', 0]), (_o.GWC1, [['a'], 'a', -1]), (_o.GWC1, [['tab\t'], 'a', 0]), (_o.GWC2, [['a'], 'a', 0]), (_o.GWC2, [['a'], 'a', 0, 100001]),
               (_o.GES, [[[1, 'a', 'b', 'c'], [1, 'd', 'e', 'f']]]), (_o.GES, [[[1, 'a', 'b']]]), (_o.GES, [[['1', 'a', 'b', 'c']]]), (_o.GES, [[[1, 'A', 'b', 'c']]]),
               (_o.HEE, [[], [], []]), (_o.HEE, [['X'], ['a'], [0]]), (_o.HEE, [['U'], [''], [1]]), (_o.HEE, [['U', 'Q'], ['a'], [1, 0]]), (_o.HEE, [['U'], ['a'], [10**9 + 1]]),
               (_o.JBS, [' a', 'b']), (_o.JBS, ['a  b', 'b']), (_o.JBS, ['a ', '']), (_o.LOT, [['a', 'a'], []]), (_o.LOT, [['a'], [['a', 'a']]]), (_o.LOT, [['a', 'b'], [['a', 'c']]]),
               (_o.LOT, [['a', 'b'], [['a', 'b'], ['a', 'b']]]), (_o.LOT, [['A'], []]), (_o.LPS, ['']), (_o.LPS, ['aB']), (_o.MES, [0, []]), (_o.MES, [2, [[0, 0]]]),
               (_o.MES, [2, [[0, 1], [1, 0]]]), (_o.MES, [2, [[0, 2]]]), (_o.MNK, ['0', 1]), (_o.MNK, ['012', 1]), (_o.MNK, ['12', -1]), (_o.MST, [[0]]), (_o.MST, [[1.5]]),
               (_o.MPQ, [[], [], 1]), (_o.MPQ, [[1], [1, 2], 1]), (_o.MPQ, [[0], [1], 1]), (_o.MPQ, [[1], [0], 1]), (_o.MSS, [[['lodge', 1, 'a'], ['a', 1, 'lodge']], []]),
               (_o.MSS, [[['lodge', -1, 'a']], []]), (_o.MSS, [[], [['a', 1], ['a', 2]]]), (_o.MSS, [[['a', 1, 'a']], []]), (_o.MSP, [[], 1]), (_o.MSP, [[2], 3]), (_o.MSP, [[0], 1]),
               (_o.MSP, [[2], 0]), (_o.MCS, ['', 'a']), (_o.MCS, ['A', 'a']), (_o.MJE, [{}]), (_o.MJE, [{'1a': []}]), (_o.MJE, [{'a': [{'time': 2, 'type': 'x'}, {'time': 1, 'type': 'x'}]}]),
               (_o.MJE, [{'a': [{'time': 1, 'type': 'x', 'extra': 1}]}]), (_o.MJE, [{'a': [{'time': 1}]}]), (_o.MTI, [[[2, 1]], []]), (_o.MTI, [[[1, 2], [2, 3]], []]),
               (_o.MTI, [[[3, 4], [1, 2]], []]), (_o.MUA, [[2, 1], []]), (_o.MUA, [[10**9 + 1], []])]
        for uid, args in bad:
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
            self.assertEqual(uid in _o.FLOATS, row['inferred_interface']['return']['type'] == 'float')

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
        module = _load(f'gamma_h2h16a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
