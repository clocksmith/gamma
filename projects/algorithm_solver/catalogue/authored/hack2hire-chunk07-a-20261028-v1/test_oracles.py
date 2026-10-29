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


_o = _load('gamma_h2h07a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h07a_reference_test_cases', HERE / 'cases.py')
reference, validate_domain = _o.reference, _o.validate_domain
CONTRACTS = {row['uid']: row for row in json.loads((HERE / 'contracts.json').read_text())['problems']}


def stem(uid): return uid.split(':', 1)[1]


def exact(a, b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(map(exact, a, b))
    if type(a) is dict: return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    return a == b


class References(unittest.TestCase):
    """Hand-worked examples for each inferred spec (worked by the author, not taken from the source)."""
    def test_lcss(self):
        self.assertEqual(reference(_o.LCSS, ['axbxc', 'zabcz']), 3)
        self.assertEqual(reference(_o.LCSS, ['ab', 'ba']), 1)
        self.assertEqual(reference(_o.LCSS, ['abc', 'xyz']), 0)
        self.assertEqual(reference(_o.LCSS, ['', 'abc']), 0)

    def test_houses(self):
        self.assertEqual(reference(_o.HOUSES, [[0, 2, 1]]), [1, 1, 1])      # 1 has both neighbours occupied: skipped
        self.assertEqual(reference(_o.HOUSES, [[3, 1, 2, 5, 4]]), [1, 1, 1, 1, 1])   # 2 and 4 would join two runs: never allowed, so runs never merge
        self.assertEqual(reference(_o.HOUSES, [[1, 1, 2]]), [1, 1, 2])

    def test_semi(self):
        self.assertEqual(reference(_o.SEMI, ['aabba']), 5)
        self.assertEqual(reference(_o.SEMI, ['aaabb']), 4)
        self.assertEqual(reference(_o.SEMI, ['baaabaaab']), 5)
        self.assertEqual(reference(_o.SEMI, ['']), 0)

    def test_under(self):
        self.assertEqual(reference(_o.UNDER, [[3, 1, 1, 1, 3], 3]), 3)
        self.assertEqual(reference(_o.UNDER, [[5, 5, 5], 4]), 0)
        self.assertEqual(reference(_o.UNDER, [[2, 1, 2, 1], 4]), 3)

    def test_case(self):
        self.assertEqual(reference(_o.CASE, ['aA']), 1)
        self.assertEqual(reference(_o.CASE, ['aAa']), 0)
        self.assertEqual(reference(_o.CASE, ['aBbA']), 1)    # a: lowercase before uppercase; b: uppercase B precedes b
        self.assertEqual(reference(_o.CASE, ['xyzZ']), 3)

    def test_margin(self):
        t = [['1', 'A', 'B', '5', '100'], ['2', 'A', 'S', '9', '120']]
        for uid in _o.MARGINS: self.assertEqual(reference(uid, [t]), [['CASH', '1100']])   # sell clamped to 5 shares
        t = [['1', 'A', 'B', '2', '400'], ['1', 'B', 'B', '2', '400'], ['2', 'C', 'B', '1', '300']]
        self.assertEqual(reference(_o.MARGIN1, [t]), [['CASH', '-900'], ['A', '2'], ['B', '2'], ['C', '1']])
        # level 2: deficit 900; A and B both at 400, A first: two A shares (cash -100), then one B share (cash 300)
        self.assertEqual(reference(_o.MARGIN2, [t]), [['CASH', '300'], ['B', '1'], ['C', '1']])
        t = [['1', 'A', 'B', '100', '10'], ['2', 'AO', 'B', '100', '5']]
        self.assertEqual(reference(_o.MARGIN2, [t]), [['CASH', '0'], ['A', '50'], ['AO', '100']])
        # level 3: A is locked by AO; each AO sale (5) unlocks one A share (10): 34 AO and 33 A shares cover 500
        self.assertEqual(reference(_o.MARGIN3, [t]), [['CASH', '0'], ['A', '67'], ['AO', '66']])
        t = [['1', 'A', 'B', '1', '10'], ['2', 'AO', 'B', '3', '400']]
        self.assertEqual(reference(_o.MARGIN3, [t]), [['CASH', '190'], ['A', '1'], ['AO', '2']])   # A stays locked (1 share, 2 options left)

    def test_frame(self):
        self.assertEqual(reference(_o.FRAME, [[[1, 2, 3], [4, 9, 6], [7, 8, 9]], 3]), 40)   # border {1,2,3,6,9,8,7,4}; the centre 9 is ignored
        self.assertEqual(reference(_o.FRAME, [[[1, 1], [1, 1]], 2]), 1)
        self.assertEqual(reference(_o.FRAME, [[[-1, -2], [-3, -4]], 1]), -1)

    def test_nonover(self):
        self.assertEqual(reference(_o.NONOVER, [[[1, 2], [2, 3]]]), 2)
        self.assertEqual(reference(_o.NONOVER, [[[1, 10], [2, 3], [3, 4], [4, 5]]]), 3)
        self.assertEqual(reference(_o.NONOVER, [[]]), 0)

    def test_floor(self):
        self.assertEqual(reference(_o.FLOOR, [[1, 5], [2, 1], 7]), 4)
        self.assertEqual(reference(_o.FLOOR, [[3, 3, 3], [1, 2, 3], 5]), 3)
        self.assertEqual(reference(_o.FLOOR, [[3, 3, 3], [1, 2, 3], 6]), 4)

    def test_bxor(self):
        self.assertEqual(reference(_o.BXOR, [1, 7, 7]), 7)
        self.assertEqual(reference(_o.BXOR, [1, 7, 3]), 3)
        self.assertEqual(reference(_o.BXOR, [8, 15, 6]), 6)
        self.assertEqual(reference(_o.BXOR, [5, 6, 3]), 3)

    def test_health(self):
        self.assertEqual(reference(_o.HEALTH, [[1, 2, 3], ['a', 'b', 'a'], 1]), 4)
        self.assertEqual(reference(_o.HEALTH, [[1, 2, 3], ['a', 'b', 'c'], 2]), 5)

    def test_split(self):
        self.assertEqual(reference(_o.SPLIT, [[1, 2, 1]]), 3)
        self.assertEqual(reference(_o.SPLIT, [[1, 1, 2, 2]]), 3)
        self.assertEqual(reference(_o.SPLIT, [[1, 2, 2, 1]]), 4)

    def test_reward(self):
        self.assertEqual(reference(_o.REWARD, [[['a', '2', '5'], ['b', '1', '7'], ['c', '2', '1']]]), 12)
        self.assertEqual(reference(_o.REWARD, [[['a', '0', '5']]]), 0)

    def test_testeff(self):
        self.assertEqual(reference(_o.TESTEFF, [[1, 1, 3, 3]]), 2)
        self.assertEqual(reference(_o.TESTEFF, [[5, 1, 5, 2, 2, 2]]), 3)   # [1, 2]: 4 tests - 1, or [2, 2]: 3 tests
        self.assertEqual(reference(_o.TESTEFF, [[1, 2]]), 1)

    def test_expr(self):
        self.assertEqual(reference(_o.EXPR, [[['1', '+'], ['+', '2']]]), 3)
        self.assertEqual(reference(_o.EXPR, [[['9', '-'], ['-', '9']]]), 9)
        self.assertEqual(reference(_o.EXPR, [[['+', '3'], ['4', '5']]]), 5)   # 3 and 5 / 4 and 5 are adjacent digits: no longer path
        self.assertEqual(reference(_o.EXPR, [[['0', '-', '9']]]), 9)

    def test_board(self):
        self.assertEqual(reference(_o.BOARD, [[0, 10, 11, 21]]), 10)
        self.assertEqual(reference(_o.BOARD, [[5]]), 1)
        self.assertEqual(reference(_o.BOARD, [[1, 2, 3]]), 1)
        self.assertEqual(reference(_o.BOARD, [[-5, 5, 6]]), 1)

    def test_domain(self):
        for uid, args in [(_o.LCSS, ['A', 'b']), (_o.LCSS, ['a' * 1001, '']), (_o.HOUSES, [[]]), (_o.SEMI, ['\n']),
                          (_o.UNDER, [[0], 1]), (_o.UNDER, [[1], 0]), (_o.CASE, ['ab1']), (_o.CASE, ['']),
                          (_o.MARGIN1, [[]]), (_o.MARGIN1, [[['2', 'A', 'B', '1', '1'], ['1', 'A', 'B', '1', '1']]]),
                          (_o.MARGIN2, [[['1', 'A', 'X', '1', '1']]]), (_o.MARGIN2, [[['1', 'A', 'B', '0', '1']]]),
                          (_o.MARGIN3, [[['1', 'AOO', 'B', '1', '1']]]), (_o.MARGIN3, [[['1', 'O', 'B', '1', '1']]]),
                          (_o.FRAME, [[[1, 2], [3]], 1]), (_o.FRAME, [[[1]], 2]), (_o.NONOVER, [[[2, 2]]]),
                          (_o.FLOOR, [[1], [1, 1], 0]), (_o.FLOOR, [[1], [0], 0]), (_o.BXOR, [3, 3, 5]), (_o.BXOR, [5, 6, 2]),
                          (_o.HEALTH, [[1], ['A'], 1]), (_o.HEALTH, [[0], ['a'], 1]), (_o.SPLIT, [[1]]),
                          (_o.REWARD, [[['a', '01', '1']]]), (_o.REWARD, [[['a', '1']]]), (_o.TESTEFF, [[]]),
                          (_o.EXPR, [[['+']]]), (_o.EXPR, [[['*']]]), (_o.BOARD, [[]])]:
            with self.assertRaises(ValueError, msg=str(args)[:60]): validate_domain(uid, args)

    def test_generated_cases_domain_valid(self):
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True): validate_domain(uid, row['args'])

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
        module = _load(f'gamma_h2h07a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
