import copy
import importlib.util
from itertools import product
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


_o = _load('gamma_h2h07b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h07b_reference_test_cases', HERE / 'cases.py')
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


def leaf(v): return {'val': v, 'children': []}


class References(unittest.TestCase):
    """Hand-worked examples for each inferred spec (worked by the author, not taken from the source)."""
    def test_convex(self):
        self.assertEqual(reference(_o.CONVEX, [[[1, 0], [-1, 0]], -5, 5, 2]), -1)  # grid -5..5 step 2: F = 5 3 1 1 3 5
        self.assertEqual(reference(_o.CONVEX, [[[2, -3]], 0, 10, 4]), 0)
        self.assertEqual(reference(_o.CONVEX, [[[1, 0], [-1, 0]], -100, 100, 3]), -1)  # scaled copy of the first maximum row
        self.assertEqual(reference(_o.CONVEX, [[[0, 5], [1, -100], [-1, -100]], -200, 200, 10]), -100)  # scaled flat-bottom row

    def test_batt(self):
        self.assertEqual(reference(_o.BATT, [[3, 4], [4, 3], 20]), 6)  # prefix 3 7 10 14 17 21
        self.assertEqual(reference(_o.BATT, [[3, 4], [5, 3], 8]), -1)  # battery 0 idles 4 < 5 minutes
        self.assertEqual(reference(_o.BATT, [[3, 4], [5, 3], 7]), 2)
        n = 20; tight = [10 * (n - 1)] * n; tight[5] += 1  # scaled copy of the tight maximum rows
        self.assertEqual(reference(_o.BATT, [[10] * n, tight, 10 * (n + 5)]), n + 5)
        self.assertEqual(reference(_o.BATT, [[10] * n, tight, 10 * (n + 5) + 1]), -1)
        self.assertEqual(reference(_o.BATT, [[10] * n, [10 * (n - 1)] * n, 10000]), 1000)

    def test_nary(self):
        root = {'val': 1, 'children': [{'val': 2, 'children': [leaf(4), leaf(5)]}, leaf(3)]}
        self.assertEqual(reference(_o.NARY1, [root, 4, 3]), 3)
        self.assertEqual(reference(_o.NARY1, [root, 4, 5]), 2)
        self.assertEqual(reference(_o.NARY2, [root, [4], [3, 5]]), 2)
        self.assertEqual(reference(_o.NARY2, [root, [4, 1], [5, 1]]), 0)

    def test_asset(self):
        self.assertEqual(reference(_o.ASSET, [1, 1, 0, 10, 5]), '3.636364')  # (0+1+2+3+4+5*6)/11 = 40/11
        self.assertEqual(reference(_o.ASSET, [2, 1, 0, 1, 0]), '0.250000')
        self.assertEqual(reference(_o.ASSET, [3, 0, 0, 1000, 1000]), '1500.000000')
        self.assertEqual(reference(_o.ASSET, [2, 9, 2, 4, 0]), '0.000000')

    def test_menu(self):
        menu = [['x', 5, 'a,b'], ['y', 3, 'a'], ['z', 3, 'b']]
        self.assertEqual(reference(_o.MENU1, [menu, ['a', 'b']]), 5)
        self.assertEqual(reference(_o.MENU2, [[['x', 6, 'a,b']] + menu[1:], ['a', 'b']]), [6, 1])
        self.assertEqual(reference(_o.MENU1, [menu, ['c']]), -1)
        self.assertEqual(reference(_o.MENU2, [menu, ['a', 'q']]), [-1, -1])
        m3 = [['x', 2, 'a,b'], ['y', 2, 'b,c'], ['z', 2, 'a'], ['w', 1, 'c']]
        self.assertEqual(reference(_o.MENU3, [m3, ['a', 'b', 'c']]), [['w', 'x']])
        self.assertEqual(reference(_o.MENU3, [m3 + [['v', 1, 'a,c']], ['a', 'b', 'c']]), [['v', 'x']] if False else [['w', 'x']])

    def test_menu3_product_construction(self):
        names = ['item' + chr(97 + i) for i in range(6)]  # scaled copy of the 5**5 maximum row: 5**3 optimal covers
        menu = [[c + str(i), 10, names[i]] for i in range(6) for c in 'ab'] + [['p%d' % i, 20, names[2 * i] + ',' + names[2 * i + 1]] for i in range(3)]
        combos = []
        for pick in product(range(5), repeat=3):
            ids = []
            for i, c in enumerate(pick): ids += ['p%d' % i] if c == 4 else ['ab'[c // 2] + str(2 * i), 'ab'[c % 2] + str(2 * i + 1)]
            combos.append(sorted(ids))
        self.assertEqual(reference(_o.MENU3, [menu, names]), sorted(combos))

    def test_swaps(self):
        self.assertEqual(reference(_o.SWAPS, ['WRRWWR']), 2)
        self.assertEqual(reference(_o.SWAPS, ['RW' * 20]), 100)  # r * r / 4 with r = 20
        self.assertEqual(reference(_o.SWAPS, ['R' + 'W' * 30 + 'R']), 30)

    def test_battle(self):
        a, b = [{'name': 'a', 'health': 3, 'attack': 2}], [{'name': 'b', 'health': 2, 'attack': 5}]
        self.assertEqual(reference(_o.MTB1, [a, b]), ['a attacks b for 2 damage, b has 0 health left', 'b is defeated', 'Team A wins'])
        a2, b2 = [dict(a[0], defense=0)], [dict(b[0], health=3, defense=1)]
        self.assertEqual(reference(_o.MTB2, [a2, b2]), ['a attacks b for 1 damage, b has 2 health left', 'b attacks a for 5 damage, a has 0 health left',
                                                       'a is defeated', 'Team B wins'])
        self.assertEqual(reference(_o.MTB3, [[dict(a2[0], speed=1)], [dict(b2[0], speed=2)]]),
                         ['b attacks a for 5 damage, a has 0 health left', 'a is defeated', 'Team B wins'])

    def test_monsters(self):
        rows = [['r', ['a', 'b']], ['a', ['h']], ['h*', []], ['b*', []]]
        self.assertEqual(reference(_o.MB1, [rows, 'r']), ['r'])
        self.assertEqual(reference(_o.MB1, [[['r', ['a', 'b']], ['a', ['h']], ['h*', []], ['b', []]], 'r']), ['a', 'r'])
        crow = [['r', 10, ['a', 'b']], ['a', 1, ['h']], ['h*', 1, []], ['b*', 1, []]]
        self.assertEqual(reference(_o.MB2, [crow, 'r']), 10)
        self.assertEqual(reference(_o.MB2, [crow[:3] + [['b', 1, []]], 'r']), 1)
        self.assertEqual(reference(_o.MB2, [[['r*', 1, []]], 'r']), -1)

    def test_monster_spine_construction(self):
        spine = ['m%d' % i for i in range(6)]  # scaled copy of the maximum rows: hostile leaves under m2 and m4
        rows, crows = [], []
        for i, s in enumerate(spine):
            leaves = ['l%d_%d' % (i, j) for j in range(2)]
            kids = leaves + ([spine[i + 1]] if i < 5 else [])
            rows.append([s, kids]); crows.append([s, 1000 - i, kids])
            for x in leaves:
                label = x + ('*' if i in (2, 4) else ''); rows.append([label, []]); crows.append([label, 1, []])
        self.assertEqual(reference(_o.MB1, [rows, 'm0']), ['m0', 'm1', 'm2'])
        self.assertEqual(reference(_o.MB2, [crows, 'm0']), 998)

    def test_strings(self):
        self.assertEqual(reference(_o.MFS, ['banana', 2]), 'an')
        self.assertEqual(reference(_o.MFS, ['ab', 3]), '')
        self.assertEqual(reference(_o.MTS, [[3, 1, 2], 2]), [1, 2, 3])
        self.assertEqual(reference(_o.PASCAL, ['3902']), '11')  # 3902 -> 292 -> 11
        self.assertEqual(reference(_o.PASCAL, ['1' * 30]), str(pow(2, 28, 10)) * 2)

    def test_nested(self):
        self.assertTrue(reference(_o.NSE, [['a', ['b', 'c']], [['c', 'b', 'b'], 'a']]))
        self.assertFalse(reference(_o.NSE, [['a'], [['a']]]))
        self.assertFalse(reference(_o.NSE, [[['a', 'b']], [['a'], ['b']]]))

    def test_news(self):
        self.assertEqual(reference(_o.NEWS, [[['hello', 'world', 'x']], ['RIGHT'], 11]), ['*' * 13, '*hello world*', '*          x*', '*' * 13])
        self.assertEqual(reference(_o.NEWS, [[['ab'], ['c', 'd']], ['LEFT', 'RIGHT'], 3]), ['*****', '*ab *', '*c d*', '*****'])

    def test_offset(self):
        self.assertEqual(reference(_o.OFFSET, [[2, 0, 1]]), [-1, 0, 2])
        self.assertEqual(reference(_o.OFFSET, [[0, 2, 1, 5]]), [0, -1, 2, -1])

    def test_pal(self):
        self.assertEqual(reference(_o.PAL, [['a', 'b', 'a'], [0, 2], [1, 1], [2, 1, 0]]), [2, 1, 1])  # path 2-1-0 reads a, ab, aba
        n = 50; order = list(range(n))  # scaled copy of the alternating-chain maximum row
        alt = ['a' if d % 2 else 'b' for d in range(n)]
        f = lambda d: (d + 2) // 2 + (d + 1) // 4  # lengths 1..d+1: odd lengths, plus even lengths divisible by 4
        self.assertEqual(reference(_o.PAL, [alt, order[:-1], order[1:], [n - 1, n // 2, 0]]), [f(n - 1), f(n // 2), 1])

    def test_domain(self):
        bad = [(_o.CONVEX, [[], 0, 1, 1]), (_o.CONVEX, [[[1, 0]], 5, 4, 1]), (_o.CONVEX, [[[1, 0]], 0, 4, 0]), (_o.BATT, [[1], [1, 2], 3]),
               (_o.BATT, [[0], [1], 3]), (_o.NARY1, [leaf(1), 1, 2]), (_o.NARY1, [{'val': 1, 'children': [leaf(1)]}, 1, 1]),
               (_o.NARY2, [leaf(1), [], [1]]), (_o.ASSET, [0, 0, 0, 0, 0]), (_o.ASSET, [1, 0, 5, 4, 0]), (_o.MENU1, [[['x', 1, 'a,a']], ['a']]),
               (_o.MENU1, [[['x', 1, 'a'], ['x', 2, 'b']], ['a']]), (_o.MENU3, [[['x', 0, 'a']], ['a']]), (_o.SWAPS, ['RB']), (_o.SWAPS, ['']),
               (_o.MTB1, [[{'name': 'a', 'health': 1, 'attack': 1}], [{'name': 'a', 'health': 1, 'attack': 1}]]),
               (_o.MTB2, [[{'name': 'a', 'health': 1, 'attack': 1}], [{'name': 'b', 'health': 1, 'attack': 1}]]), (_o.MTB1, [[], []]),
               (_o.MB1, [[['r', ['a']]], 'r']), (_o.MB1, [[['r', ['a']], ['a', ['r']]], 'r']), (_o.MB1, [[['r', []], ['q', []]], 'r']),
               (_o.MB2, [[['r', 0, []]], 'r']), (_o.MFS, ['aB', 1]), (_o.MFS, ['a', 0]), (_o.MTS, [[1], 0]), (_o.NSE, [['A'], []]),
               (_o.NSE, [[''], []]), (_o.NEWS, [[['abc']], ['LEFT'], 2]), (_o.NEWS, [[['a']], ['CENTER'], 2]), (_o.OFFSET, [[1, 1]]),
               (_o.OFFSET, [[]]), (_o.PAL, [['a', 'b'], [0], [0], [0]]), (_o.PAL, [['A'], [], [], [0]]), (_o.PASCAL, ['1']), (_o.PASCAL, ['1a'])]
        for uid, args in bad:
            with self.assertRaises(ValueError, msg=str(args)[:80]): validate_domain(uid, args)

    def test_generated_cases_domain_valid_and_shallow(self):
        deepest = 0
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True):
                validate_domain(uid, row['args']); deepest = max(deepest, depth(row['args']))
        self.assertLessEqual(deepest, 200)

    def test_contract_layouts(self):
        self.assertEqual(set(CONTRACTS), set(_o.IDS))
        for uid, row in CONTRACTS.items():
            self.assertEqual(row['spec_basis'], 'inferred')
            self.assertNotIn('classname', row['inferred_interface'])
            self.assertEqual(row['oracle_constant'], next(k for k in dir(_o) if getattr(_o, k) == uid and k.isupper() and k != 'H'))


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
        module = _load(f'gamma_h2h07b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
