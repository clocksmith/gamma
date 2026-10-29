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


_o = _load('gamma_h2h16b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h16b_reference_test_cases', HERE / 'cases.py')
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

    def test_mvb(self):
        self.check(_o.MVB, [([[1]], 0), ([[1, 2, 1, 3, 3]], 1), ([[1, 1, 2, 2]], 0), ([[1, 2, 1, 2]], 1), ([[5, 6, 7, 5]], 2), ([[3, 1, 3, 2, 4, 2]], 2)])

    def test_mcg(self):
        self.check(_o.MCG, [([[['1', 'buy', '10', '5'], ['2', 'sell', '4', '9']]], '1.6'),
                            # highest lot (20) first: profit 5 -> 0.5; then lot 10: profit 15 -> 1.5
                            ([[['1', 'buy', '1', '10'], ['1', 'buy', '1', '20'], ['3', 'sell', '1', '25'], ['4', 'sell', '1', '25']]], '2.0'),
                            ([[['0', 'buy', '3', '9'], ['0', 'sell', '3', '1']]], '0.0'),
                            # sells the 100 lot then one 1 lot: profit -40 + 59 = 19 -> 1.9
                            ([[['5', 'buy', '2', '1'], ['6', 'buy', '1', '100'], ['7', 'sell', '2', '60']]], '1.9')])

    def test_mad(self):
        self.check(_o.MAD, [([[4, 2, 1, 3]], [[1, 2], [2, 3], [3, 4]]), ([[1, 3, 6, 10, 15]], [[1, 3]]),
                            ([[3, 8, -10, 23, 19, -4, -14, 27]], [[-14, -10], [19, 23], [23, 27]]), ([[0, 1000000]], [[0, 1000000]])])

    def test_mcf(self):
        self.check(_o.MCF, [([[1], 1], 1), ([[2], 5], -1), ([[1, 2, 5], 10], 4), ([[1, 3], 7], 4), ([[1, 10**9], 300], 300), ([[4, 1, 4, 2], 100], 27),
                            ([[1, 2, 5], 1], 1), ([[30, 1], 30], 30)])

    def test_mdp(self):
        self.check(_o.MDP, [([0, 0, 1, 1, 1], 0), ([3, 5, 2, 3, 4], 18), ([3, 5, 2, 3, 6], 21), ([3, 5, 1, 1, 100], 8), ([4, 4, 5, 5, 1], 4)])

    def test_mrc(self):
        # [1,2,3] avg 2: prefix -1,-1,0; clockwise sum - n min = -2 + 3 = 1; counterclockwise n max - sum = 0 + 2 = 2
        self.check(_o.MRC, [([[0]], 0), ([[1, 2, 3]], 1), ([[3, 2, 1]], 1), ([[2, 0, 1]], 1), ([[4, 0, 0, 0]], 6), ([[0, 0, 0, 4]], 6), ([[0, 4, 0, 0]], 6), ([[2, 0, 1, 1]], 1)])

    def test_mre(self):
        self.check(_o.MRE, [([1, [], []], 0), ([2, [1], [2]], 0), ([3, [2, 3], [1, 1]], 1), ([4, [1, 3, 3], [2, 2, 4]], 1), ([3, [1, 3], [2, 2]], 1)])

    def test_nid(self):
        self.check(_o.NID, [([[0], [0]], 0), ([[0, 1, -1, 0, 0], [0, 0, 0, 1, -1]], 1), ([[0, 5, -5, 0, 0], [0, 0, 0, 7, -1]], 1), ([[0, 1, 0, 1], [0, 0, 1, 1]], 0)])

    def test_ofm(self):
        t = ops('ObjectLayout', [['foo', 'bar', 'baz'], [3, 6, 2]], [('getOffset', 'bar'), ('getOffset', 'baz'), ('getOffset', 'qux'), ('fieldAt', 0), ('fieldAt', 3),
                                                                     ('fieldAt', 10), ('fieldAt', 11), ('totalSize',), ('removeField', 'bar'), ('getOffset', 'baz'),
                                                                     ('addField', 'baz', 1), ('addField', 'bar', 4), ('getOffset', 'bar'), ('totalSize',), ('fieldAt', 5)])
        self.check(_o.OFM, [(t, [None, 3, 9, -1, 'foo', 'bar', 'baz', '', 11, True, 3, False, True, 5, 9, 'bar'])])

    def test_pst(self):
        t = ops('PalindromeStream', [], [('isPalindrome',), ('track', 'a'), ('isPalindrome',), ('track', 'b'), ('isPalindrome',), ('track', 'a'), ('isPalindrome',),
                                         ('track', 'A'), ('isPalindrome',)])
        self.check(_o.PST, [(t, [None, True, None, True, None, False, None, True, None, False])])

    def test_pds(self):
        # 124 + 659 = 783 and 125 + 739 = 864 style sums; fixed full assignment 123+456 != 789
        self.check(_o.PDS, [(['123456789'], 0), (['124659783'], 1), (['12465978?'], 1), (['?24659783'], 1)])
        self.assertEqual(sum(reference(_o.PDS, [d + '????????']) for d in '123456789'), 336)

    def test_pig(self):
        self.check(_o.PIG, [(['apple'], 'appleway'), (['Hello World'], 'elloHay orldWay'), ([''], ''), (['I am a Pig'], 'Iway amway away igPay'), (['b c d'], 'bay cay day')])

    def test_pvo(self):
        # ratio 2 first: 3 shares of AA cost 30 -> 60; 10 left buys 2 BB -> 12
        self.check(_o.PVO, [([[['AA', 10, 20, 3], ['BB', 5, 6, 10]], 40], '72.00'), ([[['A', 3, 1, 5]], 1], '0.33'), ([[['A', 8, 1, 1]], 4], '0.50'),
                            ([[['A', 8, 1, 1]], 1], '0.13'), ([[['A', 400, 1, 1]], 2], '0.01'), ([[['A', 400, 1, 1]], 1], '0.00'),
                            ([[['A', 1, 0, 5], ['B', 2, 1, 5]], 3], '1.50'), ([[['A', 5, 5, 0]], 100], '0.00')])

    def test_pfp(self):
        self.check(_o.PFP, [([[1, 2, 3, 4], [[2, 3], [4], [], []], ['root', 'a', 'b', 'c'], 4], 'root/a/c'), ([[1, 2, 3, 4], [[2, 3], [4], [], []], ['root', 'a', 'b', 'c'], 9], ''),
                            ([[7, 8], [[], []], ['x', 'y'], 8], 'y'), ([[3, 1, 2], [[], [3], [1]], ['c', 'b', 'a'], 3], 'a/b/c')])

    def test_ppq(self):
        log = ['milk, 2023-01-05, 300', 'milk, 2023-01-02, 250', 'Big Box, 2023-01-03, 999']
        self.check(_o.PPQ, [([log, [['milk', '2023-01-04'], ['milk', '2023-01-01'], ['milk', '2023-01-05'], ['Big Box', '2024-01-01'], ['tea', '2023-01-05']]], [250, -1, 300, 999, -1]),
                            ([[], [['a', '2000-01-01']]], [-1])])

    def test_ppt(self):
        t = ops('ProductPrice', [], [('current',), ('update', 5, 10), ('update', 3, 20), ('current',), ('maximum',), ('minimum',), ('update', 3, 5), ('maximum',),
                                     ('minimum',), ('update', 5, 7), ('current',), ('maximum',)])
        self.check(_o.PPT, [(t, [None, -1, None, None, 10, 20, 10, None, 10, 5, None, 7, 7])])

    def test_domain(self):
        bad = [(_o.MVB, [[]]), (_o.MVB, [[0]]), (_o.MCG, [[['1', 'sell', '1', '5']]]), (_o.MCG, [[['2', 'buy', '1', '5'], ['1', 'buy', '1', '5']]]),
               (_o.MCG, [[['1', 'buy', '01', '5']]]), (_o.MCG, [[['1', 'hold', '1', '5']]]), (_o.MAD, [[1, 1]]), (_o.MAD, [[1]]), (_o.MCF, [[], 5]), (_o.MCF, [[1], 0]),
               (_o.MDP, [-1, 0, 1, 1, 1]), (_o.MDP, [0, 0, 0, 1, 1]), (_o.MRC, [[1, 2]]), (_o.MRC, [[]]), (_o.MRE, [3, [1, 2], [2, 1]]), (_o.MRE, [2, [1], [3]]),
               (_o.NID, [[0, 0], [1, 1]]), (_o.NID, [[0], []]), (_o.OFM, ops('ObjectLayout', [['a', 'a'], [1, 1]], [])), (_o.OFM, ops('ObjectLayout', [['a'], [0]], [])),
               (_o.OFM, ops('ObjectLayout', [[], []], [('fieldAt', -1)])), (_o.OFM, ops('ObjectLayout', [[], []], [('addField', 'A', 1)])),
               (_o.PST, ops('PalindromeStream', [], [('track', 'ab')])), (_o.PST, ops('PalindromeStream', [1], [])), (_o.PDS, ['11???????']), (_o.PDS, ['0????????']),
               (_o.PDS, ['????????']), (_o.PIG, [' a']), (_o.PIG, ['a  b']), (_o.PIG, ['a1']), (_o.PVO, [[['A', 0, 1, 1]], 1]), (_o.PVO, [[], 1]), (_o.PVO, [[['a', 1, 1, 1]], 1]),
               (_o.PFP, [[1, 2], [[2], [1]], ['a', 'b'], 1]), (_o.PFP, [[1, 2], [[2], [2]], ['a', 'b'], 1]), (_o.PFP, [[1, 1], [[], []], ['a', 'b'], 1]),
               (_o.PFP, [[1], [[3]], ['a'], 1]), (_o.PPQ, [['a, 2023-02-30, 5'], [['a', '2023-01-01']]]), (_o.PPQ, [['a, 2023-01-01, 5', 'a, 2023-01-01, 6'], [['a', '2023-01-01']]]),
               (_o.PPQ, [['a,b, 2023-01-01, 5'], [['a', '2023-01-01']]]), (_o.PPQ, [[], []]), (_o.PPT, ops('ProductPrice', [], [('update', 0, 1)])),
               (_o.PPT, ops('ProductPrice', [], [('latest',)]))]
        for uid, args in bad:
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
        module = _load(f'gamma_h2h16b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
