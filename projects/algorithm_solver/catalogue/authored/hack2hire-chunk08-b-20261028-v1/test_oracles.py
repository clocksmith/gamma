import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import unittest
HERE = Path(__file__).parent


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, file); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


_o = _load('gamma_h2h08b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h08b_reference_test_cases', HERE / 'cases.py')
reference, validate_domain = _o.reference, _o.validate_domain
CONTRACTS = {row['uid']: row for row in json.loads((HERE / 'contracts.json').read_text())['problems']}


def stem(uid): return uid.split(':', 1)[1]


def exact(a, b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(map(exact, a, b))
    if type(a) is dict: return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    return a == b


def depth(v):
    """Nesting depth of a JSON value (a scalar is 0)."""
    best, stack = 0, [(v, 1)]
    while stack:
        x, d = stack.pop()
        if isinstance(x, (list, dict)):
            best = max(best, d)
            stack.extend((y, d + 1) for y in (x.values() if isinstance(x, dict) else x))
    return best


def snake(rc, moves): return [['SnakeGame'] + ['move'] * len(moves), [rc] + [[d] for d in moves]]


def ttt(nmk, moves): return [['TicTacToe'] + ['move'] * len(moves), [nmk] + [list(m) for m in moves]]


class References(unittest.TestCase):
    """Hand-worked examples for each inferred spec (worked by the author, not taken from the source)."""
    def test_parity(self):
        self.assertEqual(reference(_o.PARITY, [0b10101010]), 0b10101010)   # low seven bits hold three 1s: MSB set
        self.assertEqual(reference(_o.PARITY, [0b00000001]), 0b10000001)
        self.assertEqual(reference(_o.PARITY, [0b10000000]), 0)
        self.assertEqual(reference(_o.PARITY, [255]), 255)

    def test_hike(self):
        self.assertEqual(reference(_o.HIKE, [[0, 3, 4, 10], 0]), 10)
        self.assertEqual(reference(_o.HIKE, [[0, 3, 4, 10], 1]), 6)       # rest at 4: days 4 and 6
        self.assertEqual(reference(_o.HIKE, [[0, 3, 4, 10], 2]), 6)       # the last day 4 -> 10 cannot be split
        self.assertEqual(reference(_o.HIKE, [[0], 3]), 0)

    def test_spath(self):
        self.assertEqual(reference(_o.SPATH, [4, [[0, 1], [1, 2], [2, 3], [0, 3]], 0, 2]), 2)
        self.assertEqual(reference(_o.SPATH, [2, [], 0, 1]), -1)
        self.assertEqual(reference(_o.SPATH, [1, [], 0, 0]), 0)

    def test_snake(self):
        self.assertEqual(reference(_o.SNAKE, snake([2, 2], 'RDLURDLURDLU')), [None] + [True] * 12)   # length 3 after move 10, still circling
        self.assertEqual(reference(_o.SNAKE, snake([1, 2], 'RLRLRLRLRLR')), [None] + [True] * 9 + [False] * 2)   # move 10 grows into its tail
        self.assertEqual(reference(_o.SNAKE, snake([3, 3], 'UR')), [None, False, False])

    def test_spam(self):
        self.assertEqual(reference(_o.SPAM, [[['a', 'r', '1999-12-31T23:59:59']], [['r', '2000-01-01T00:00:00']], 1]), [['a', 1]])
        self.assertEqual(reference(_o.SPAM, [[['a', 'r', '2000-02-28T23:59:59'], ['b', 'r', '2000-03-01T00:00:00']], [['r', '2000-02-29T12:00:00']], 43201]),
                         [['a', 1], ['b', 1]])                            # leap day: both calls are 43200 / 43201 s away
        self.assertEqual(reference(_o.SPAM, [[['a', 'r', '2024-01-01T00:00:00']], [['r', '2024-01-01T00:00:06']], 5]), [])

    def test_bee(self):
        self.assertEqual(reference(_o.BEE, ['e', ['b', 'n'], ['been', 'bee', 'nene', 'bean', 'eebn']]), ['been', 'nene', 'eebn'])
        self.assertEqual(reference(_o.BEE, ['x', ['x'], ['xxxx', 'xxxx']]), ['xxxx', 'xxxx'])

    def test_repl(self):
        self.assertEqual(reference(_o.REPL, ['aaa', 'aa', 'b']), 'ba')
        self.assertEqual(reference(_o.REPL, ['aaaa', 'aa', '']), '')
        self.assertEqual(reference(_o.REPL, ['abcabc', 'bc', 'XYZ']), 'aXYZaXYZ')

    def test_read(self):
        self.assertEqual(reference(_o.READ, [[3, 6, 7, 11], 8]), 4)       # x = 4: 1 + 2 + 2 + 3 days
        self.assertEqual(reference(_o.READ, [[3, 6, 7, 11], 3]), -1)
        self.assertEqual(reference(_o.READ, [[5], 6]), 1)

    def test_subsets(self):
        t = [[3, 34, 4, 12, 5, 2], 9]
        self.assertIs(reference(_o.SUB1, t), True)
        self.assertEqual(reference(_o.SUB2, t), 2)                        # {4, 5} and {3, 4, 2}
        self.assertEqual(reference(_o.SUB3, t), [[2, 3, 4], [4, 5]])
        t = [[5, 3, 5, 2, 3], 8]
        self.assertEqual(reference(_o.SUB2, t), 5)                        # four (5, 3) position pairs and 3 + 3 + 2
        self.assertEqual(reference(_o.SUB3, t), [[2, 3, 3], [3, 5]])
        self.assertIs(reference(_o.SUB1, [[2, 2], 3]), False)

    def test_wrap(self):
        self.assertEqual(reference(_o.WRAP, ['abcd bcd', ['cd', 'bc', 'b']]), 'a[bc]d [bc]d')
        self.assertEqual(reference(_o.WRAP, ['hello world', ['o', 'l']]), 'he[l]lo w[o]rld')
        self.assertEqual(reference(_o.WRAP, ['xyz', ['a']]), 'xyz')

    def test_tpl(self):
        self.assertEqual(reference(_o.TPL1, ['Hi {name}, {name}!', ['name'], ['Ann']]), 'Hi Ann, Ann!')
        self.assertEqual(reference(_o.TPL2, ['{a}', ['a', 'b'], ['<{b}>', 'B']]), '<B>')
        self.assertEqual(reference(_o.TPL2, ['{a}{a}', ['a', 'b', 'c'], ['{b}{c}', '{c}', 'z']]), 'zzzz')

    def test_tet(self):
        t = [[[0, 0, 0], [0, 0, 0], [1, 0, 1]], [[0, 1, 0], [1, 1, 1]], 0]
        self.assertEqual(reference(_o.TET1, t), [[0, 1, 0], [1, 1, 1], [1, 0, 1]])
        self.assertEqual(reference(_o.TET2, t), [[0, 0, 0], [0, 1, 0], [1, 0, 1]])
        t = [[[0, 0, 0], [1, 0, 0], [1, 0, 1]], [[1, 1], [0, 1]], 1]    # column 2 stops on row 2, so the block rests on rows 0-1
        self.assertEqual(reference(_o.TET1, t), [[0, 1, 1], [1, 0, 1], [1, 0, 1]])

    def test_color(self):
        self.assertIs(reference(_o.COLOR, [['a', 'b', 'c'], [['a', 'b'], ['b', 'c'], ['c', 'a']]]), True)
        self.assertIs(reference(_o.COLOR, [['a', 'b', 'c', 'd'], [['a', 'b'], ['a', 'c'], ['a', 'd'], ['b', 'c'], ['b', 'd'], ['c', 'd']]]), False)

    def test_ttt(self):
        self.assertEqual(reference(_o.TTT, ttt([3, 3, 3], [(0, 0, 1), (1, 0, 2), (1, 1, 1), (2, 0, 2), (2, 2, 1)])), [None, 0, 0, 0, 0, 1])
        self.assertEqual(reference(_o.TTT, ttt([2, 4, 2], [(0, 3, 1), (1, 0, 2), (1, 2, 1)])), [None, 0, 0, 1])   # anti-diagonal of length 2
        self.assertEqual(reference(_o.TTT, ttt([1, 1, 1], [(0, 0, 2)])), [None, 2])

    def test_tri(self):
        self.assertEqual(reference(_o.TRI, [0, 0, 1, 1, 2, 2, 0, 0, 5, 5]), 0)
        self.assertEqual(reference(_o.TRI, [0, 0, 4, 0, 0, 4, 2, 2, 4, 0]), 3)    # p on the hypotenuse, q a vertex
        self.assertEqual(reference(_o.TRI, [0, 0, 4, 0, 0, 4, 1, 1, 5, 5]), 1)
        self.assertEqual(reference(_o.TRI, [0, 0, 4, 0, 0, 4, 9, 9, 2, 2]), 2)
        self.assertEqual(reference(_o.TRI, [0, 0, 4, 0, 0, 4, -1, 0, 5, 0]), 4)

    def test_flight(self):
        f = [['SFO', '2024-01-02T08:00', 'LAX', '2024-01-02T09:30', 'u'], ['JFK', '2024-01-01T10:00', 'SFO', '2024-01-02T08:00', 'u']]
        self.assertEqual(reference(_o.FLIGHT, [f, 'u', '2024-01-01T09:00']), 'JFK')
        self.assertEqual(reference(_o.FLIGHT, [f, 'u', '2024-01-01T12:00']), '')
        self.assertEqual(reference(_o.FLIGHT, [f, 'u', '2024-01-02T08:00']), 'SFO')
        self.assertEqual(reference(_o.FLIGHT, [f, 'u', '2024-01-02T09:30']), 'LAX')
        self.assertEqual(reference(_o.FLIGHT, [f, 'v', '2024-01-02T09:30']), '')

    def test_domain(self):
        for uid, args in [(_o.PARITY, [256]), (_o.PARITY, [True]), (_o.HIKE, [[1, 2], 0]), (_o.HIKE, [[0, 2, 1], 0]),
                          (_o.SPATH, [2, [[0, 2]], 0, 1]), (_o.SNAKE, snake([2, 2], 'X')), (_o.SNAKE, [['SnakeGame'], [[0, 1]]]),
                          (_o.SPAM, [[['a', 'r', '2023-02-29T00:00:00']], [], 0]), (_o.SPAM, [[['a', 'r', '2024-01-01 00:00:00']], [], 0]),
                          (_o.BEE, ['ab', [], []]), (_o.BEE, ['a', [], ['Abcd']]), (_o.REPL, ['abc', '', 'x']), (_o.READ, [[0], 1]),
                          (_o.SUB1, [[0], 1]), (_o.SUB1, [[10**6] * 1000, 5 * 10**8]), (_o.SUB2, [[3] * 1000, 1500]),
                          (_o.SUB3, [[1] * 100, 10001]), (_o.SUB3, [list(range(1, 101)), 70]), (_o.WRAP, ['a  b', ['a']]), (_o.WRAP, ['a', []]),
                          (_o.TPL1, ['{a', ['a'], ['x']]), (_o.TPL1, ['{b}', ['a'], ['x']]), (_o.TPL1, ['{a}', ['a'], ['{a}']]),
                          (_o.TPL2, ['{a}', ['a', 'b'], ['{b}', '{a}']]), (_o.TPL2, ['x}', ['a'], ['']]),
                          (_o.TET1, [[[1, 1]], [[1]], 0]), (_o.TET2, [[[0, 0]], [[0]], 0]), (_o.TET1, [[[0, 0]], [[1, 1]], 1]),
                          (_o.COLOR, [['a'], [['a', 'a']]]), (_o.COLOR, [['a', 'a'], []]), (_o.TTT, ttt([2, 2, 2], [(0, 0, 1), (0, 0, 2)])),
                          (_o.TTT, ttt([1, 2, 1], [(0, 0, 1), (0, 1, 2)])), (_o.TTT, ttt([2, 2, 3], [])), (_o.TRI, [0] * 9 + [10**7 + 1]),
                          (_o.FLIGHT, [[['JFK', '2024-01-01T10:00', 'SFO', '2024-01-01T10:00', 'u']], 'u', '2024-01-01T10:00']),
                          (_o.FLIGHT, [[['JFK', '2024-01-01T10:00', 'SFO', '2024-01-01T12:00', 'u'], ['SFO', '2024-01-01T11:00', 'LAX', '2024-01-01T13:00', 'u']], 'u', '2024-01-01T10:00'])]:
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
            self.assertEqual(row['oracle_constant'], next(k for k in dir(_o) if getattr(_o, k) == uid and k.isupper() and k != 'H'))
            if uid in _o.CLASSES:
                name, ctor, methods, voids = _o.CLASSES[uid]
                iface = row['inferred_interface']
                self.assertEqual(iface['classname'], name)
                self.assertEqual(len(iface['constructor']['params']), ctor)
                self.assertEqual({m['name']: len(m['params']) for m in iface['methods']}, methods)
                self.assertEqual({m['name'] for m in iface['methods'] if m['return']['type'] == 'void'}, set(voids))
            else:
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
        module = _load(f'gamma_h2h08b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
