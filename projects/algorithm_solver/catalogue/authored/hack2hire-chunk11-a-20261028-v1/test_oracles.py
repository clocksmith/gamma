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


_o = _load('gamma_h2h11a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h11a_reference_test_cases', HERE / 'cases.py')
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
    def test_gt(self):
        self.assertEqual(reference(_o.GT, [[1, 2, 3]]), 123)
        self.assertEqual(reference(_o.GT, [[0, 0, 7]]), 7)
        self.assertEqual(reference(_o.GT, [[3, 9, 1, 9, 2, 9]]), 999)
        self.assertEqual(reference(_o.GT, [[9, 1, 8, 0, 2]]), 982)

    def test_lcm(self):
        rows = [['ceo', ['a', 'b']], ['a', ['c', 'd']], ['b', []], ['c', []], ['d', ['e']], ['e', []]]
        self.assertEqual(reference(_o.LCM, [rows, 'e', 'c']), 'a')
        self.assertEqual(reference(_o.LCM, [rows, 'e', 'b']), 'ceo')
        self.assertEqual(reference(_o.LCM, [rows, 'd', 'e']), 'd')
        self.assertEqual(reference(_o.LCM, [rows, 'c', 'c']), 'c')

    def test_fms(self):
        self.assertEqual(reference(_o.FMS, ['hello', ['he--o', 'he-lo', '-ello', 'h-l-o', 'hello', '-----', 'hexlo']]), ['he--o', 'he-lo', '-ello', 'hello'])

    def test_med(self):
        self.assertEqual(reference(_o.MED, [[3, 1, 2]]), 2)
        self.assertEqual(reference(_o.MED, [[4, 1, 3, 2]]), 2.5)
        self.assertIs(type(reference(_o.MED, [[1, 3]])), int)
        self.assertEqual(reference(_o.MED, [[-3, -4]]), -3.5)

    def test_fmo(self):
        self.assertEqual(reference(_o.FMO, ['0110']), 0)
        self.assertEqual(reference(_o.FMO, ['01']), 1)       # move 0 to the end
        self.assertEqual(reference(_o.FMO, ['0011']), 2)     # keep 1 1, move both zeros
        self.assertEqual(reference(_o.FMO, ['10110']), 1)    # reverse 01101: its prefix 0110 is a subsequence of image, so only the leading 1 moves

    def test_mst(self):
        games = [['10', 'lose'], ['20', 'win'], ['30', 'lose'], ['5', 'win']]
        # >= 30: 1/1; >= 20: 1/2; >= 10: 2/3; >= 5: 2/4
        self.assertEqual(reference(_o.MST, [games, 0.5]), 5)
        self.assertEqual(reference(_o.MST, [games, 0.6]), 10)
        self.assertEqual(reference(_o.MST, [games, 0.7]), 30)
        self.assertEqual(reference(_o.MST, [[], 0]), -1)

    def test_fom(self):
        self.assertEqual(reference(_o.FOM, [[1, 2, 3, 2, 1]]), 3)
        self.assertEqual(reference(_o.FOM, [[3, 1, 3]]), 5)
        self.assertEqual(reference(_o.FOM, [[0, 0]]), 0)

    def test_fpt(self):
        # order 3: 0 = root, 1 = left (order 1), 2 = right (order 2), 3 = right child of 2
        self.assertEqual([_o.fib_size(i) for i in range(6)], [0, 1, 2, 4, 7, 12])
        self.assertEqual(reference(_o.FPT, [3, 1, 3]), 'URR')
        self.assertEqual(reference(_o.FPT, [3, 3, 1]), 'UUL')
        self.assertEqual(reference(_o.FPT, [3, 2, 2]), '')
        # order 4: root 0, left order 2 = {1, 2 (its right child)}, right order 3 = {3, 4, 5, 6}
        self.assertEqual(reference(_o.FPT, [4, 2, 6]), 'UURRR')

    def test_mbn(self):
        edges = [[1, 2, 5], [2, 3, 1], [1, 3, 10]]
        self.assertEqual(reference(_o.MBN, [3, edges, 2]), 5)
        self.assertEqual(reference(_o.MBN, [3, edges, 1]), 10)
        self.assertEqual(reference(_o.MBN, [4, [[1, 2, 1]], 3]), -1)

    def test_pmw(self):
        self.assertEqual(reference(_o.PMW, [['cat', 'cart', 'ct', 'coat', 'cats'], 'c.t']), ['cat', 'cart', 'coat'])
        self.assertEqual(reference(_o.PMW, [['ab', 'a', 'abc'], '??']), ['ab'])
        self.assertEqual(reference(_o.PMW, [['aa', 'aaa', 'a'], '..']), ['aa', 'aaa'])

    def test_lss(self):
        self.assertEqual(reference(_o.LSS, [[16, 17, 71, 62, 12, 24, 14]]), 4)
        self.assertEqual(reference(_o.LSS, [[1, 2, 4]]), 1)

    def test_fwp(self):
        self.assertEqual(reference(_o.FWP, ['leet']), 'DDR!UURRR!!DDD!')
        self.assertEqual(reference(_o.FWP, ['zdz']), 'DDDDD!UUUUURRR!LLLDDDDD!')
        self.assertEqual(reference(_o.FWP, ['a']), '!')

    def test_f2d(self):
        t = _c._ops('Vector2D', [[[1, 2], [3], [], [4]]], [('remove',), ('next',), ('next',), ('remove',), ('remove',), ('getVector',), ('next',), ('next',),
                                                          ('remove',), ('hasNext',), ('getVector',)])
        self.assertEqual(reference(_o.F2D, t), [None, False, 1, 2, True, False, [[1], [3], [], [4]], 3, 4, True, False, [[1], [3], [], []]])

    def test_fds(self):
        ctor = [[['r1', 0, 0], ['r2', 10, 10]], [['r1', 'pizza', 12], ['r2', 'pizza', 8], ['r2', 'soup', 5]]]
        t = _c._ops('FoodDeliverySystem', ctor, [('getBestOption', 'pizza', 1, 1), ('getBestOption', 'soup', 0, 0), ('getBestOption', 'tea', 0, 0)])
        self.assertEqual(reference(_o.FDS1, t), [None, [8, 2], [5, 20], [-1, -1]])
        t = _c._ops('FoodDeliverySystem', ctor, [('getBestOrder', ['pizza', 'soup'], 0, 0), ('getBestOrder', ['pizza'], 9, 9), ('getBestOrder', ['tea', 'pizza'], 0, 0)])
        self.assertEqual(reference(_o.FDS2, t), [None, [13, 20], [8, 2], [-1, -1]])

    def test_faw(self):
        self.assertEqual(reference(_o.FAW, [['the quick brown fox', 'jumps over'], 10]), ['the quick', 'brown fox', '', 'jumps over'])
        self.assertEqual(reference(_o.FAW, [['aa bb cc', 'dd'], 5]), ['aa bb', 'cc', '', 'dd'])

    def test_mov(self):
        ids = ['u1', 'u2', 'u3', 'u4']
        self.assertEqual(reference(_o.MOV1, [ids, [['a', 'b', 'c'], ['x', 'c', 'b'], ['c', 'b'], ['b', 'b']], 2]), [['u1', 'u2', 'u3']])
        self.assertEqual(reference(_o.MOV1, [['p', 'q', 'r'], [['a', 'a', 'b'], ['b', 'a'], ['a', 'b', 'b']], 3]), [['p', 'r']])
        t = _c._ops('MovieFriends', [2], [('watch', 'a', 'x'), ('getFriends', 'a'), ('watch', 'a', 'y'), ('watch', 'b', 'y'), ('watch', 'b', 'x'), ('getFriends', 'a'),
                                          ('watch', 'c', 'x'), ('watch', 'c', 'x'), ('watch', 'a', 'x'), ('getFriends', 'b'), ('getFriends', 'z')])
        self.assertEqual(reference(_o.MOV2, t), [None, None, [], None, None, None, ['b'], None, None, None, ['a'], []])

    def test_domain(self):
        V2, F = 'Vector2D', 'FoodDeliverySystem'
        bad = [(_o.GT, [[1, 2]]), (_o.GT, [[1, 2, 10]]), (_o.LCM, [[['a', ['b']], ['b', ['a']]], 'a', 'b']), (_o.LCM, [[['a', []]], 'a', 'z']),
               (_o.LCM, [[['a', ['b']], ['b', []], ['c', []]], 'a', 'b']), (_o.FMS, ['ab', ['a']]), (_o.FMS, ['ab', ['a*']]), (_o.MED, [[]]),
               (_o.MED, [[10**9 + 1]]), (_o.FMO, ['']), (_o.FMO, ['012']), (_o.MST, [[['01', 'win']], 0.5]), (_o.MST, [[['1', 'draw']], 0.5]),
               (_o.MST, [[], 1.5]), (_o.MST, [[], True]), (_o.FOM, [[-1]]), (_o.FPT, [0, 0, 0]), (_o.FPT, [3, 0, 4]), (_o.FPT, [76, 0, 0]),
               (_o.MBN, [1, [], 1]), (_o.MBN, [3, [[1, 1, 2]], 1]), (_o.MBN, [3, [[1, 4, 2]], 1]), (_o.PMW, [['a', 'a'], 'a']), (_o.PMW, [['a'], 'a*']),
               (_o.LSS, [[0]]), (_o.FWP, ['A']), (_o.FAW, [['abc'], 2]), (_o.FAW, [['a  b'], 5]), (_o.MOV1, [['a', 'a'], [[], []], 1]),
               (_o.MOV1, [['a'], [['x']], 0]), (_o.F2D, _c._ops(V2, [[[1]]], [('next',), ('next',)])), (_o.F2D, _c._ops(V2, [[[1.5]]], [])),
               (_o.FDS1, _c._ops(F, [[['r', 0, 0], ['r', 1, 1]], []], [])), (_o.FDS1, _c._ops(F, [[['r', 0, 0]], [['s', 'a', 1]]], [])),
               (_o.FDS1, _c._ops(F, [[['r', 0, 0]], [['r', 'a', 0]]], [])), (_o.FDS2, _c._ops(F, [[['r', 0, 0]], []], [('getBestOrder', ['a', 'a'], 0, 0)])),
               (_o.FDS1, _c._ops(F, [[['r', 0, 0]], []], [('getBestOrder', ['a'], 0, 0)])), (_o.MOV2, _c._ops('MovieFriends', [0], [])),
               (_o.MOV2, _c._ops('MovieFriends', [1], [('watch', 'A', 'x')]))]
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
        module = _load(f'gamma_h2h11a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
