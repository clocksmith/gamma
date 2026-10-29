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


_o = _load('gamma_h2h02d_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h02d_reference_test_cases', HERE / 'cases.py')
reference, validate_domain = _o.reference, _o.validate_domain
CONTRACTS = {row['uid']: row for row in json.loads((HERE / 'contracts.json').read_text())['problems']}


def stem(uid): return uid.split(':', 1)[1]


def exact(a, b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(map(exact, a, b))
    if type(a) is dict: return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    return a == b


def ops(name, ctor, calls): return _c._ops(name, ctor, calls)


class References(unittest.TestCase):
    """Hand-worked examples for each inferred spec (worked by the author, not taken from the source)."""
    def test_rate(self):
        self.assertEqual(reference(_o.RATE, [[1, 1, 2, 3, 10], 3, 2]), [True, True, False, False, True])

    def test_mod(self):
        logs = [[1, 'al', 'ADD'], [2, 'bo', 'ADD'], [3, 'al', 'REMOVE'], [4, 'al', 'ADD'], [5, 'cy', 'ADD'], [5, 'bo', 'ADD']]
        t = ops('ModSystem', [logs], [('canRemove', 'bo', 'al'), ('canRemove', 'al', 'bo'), ('canRemove', 'al', 'al'), ('canRemove', 'al', 'zz'),
                                      ('getModerators',), ('getModeratorsAt', 3), ('canRemoveAt', 2, 'al', 'bo'), ('getModeratorsAt', 0)])
        self.assertEqual(reference(_o.MOD3, t), [None, True, False, False, False, ['bo', 'al', 'cy'], ['bo'], True, []])

    def test_rect(self):
        t = ops('RectangleBoard', [5, 5], [('addRectangle', 0, 0, 4, 4), ('addRectangle', 1, 1, 2, 2), ('getTopRectangle', 1, 1), ('bringToFront', 1),
                                           ('getTopRectangle', 1, 1), ('removeRectangle', 1), ('getTopRectangle', 1, 1), ('getTopRectangle', 0, 0),
                                           ('undo',), ('getTopRectangle', 1, 1), ('undo',), ('getTopRectangle', 1, 1), ('undo',), ('getTopRectangle', 1, 1),
                                           ('undo',), ('getTopRectangle', 1, 1), ('undo',), ('removeRectangle', 1), ('addRectangle', 0, 0, 0, 0)])
        self.assertEqual(reference(_o.RECT4, t), [None, 1, 2, 2, True, 1, True, 2, -1, True, 1, True, 2, True, 1, True, -1, False, False, 3])

    def test_sheet(self):
        t = ops('Spreadsheet', [], [('setCell', 'A1', '5'), ('setCell', 'B1', '=A1+A1+2'), ('getCell', 'B1'), ('setCell', 'A1', '=B1'),
                                    ('getCell', 'A1'), ('resetCell', 'A1'), ('getCell', 'B1'), ('setCell', 'C1', '=C1')])
        self.assertEqual(reference(_o.SHEET2, t), [None, True, True, 12, False, 5, None, 2, False])
        with self.assertRaises(ValueError): validate_domain(_o.SHEET1, ops('Spreadsheet', [], [('setCell', 'A1', '=A1')]))

    def test_diag(self):
        self.assertEqual(reference(_o.DIAG, [[[0, 0], [2, 2], [1, 1], [3, -1], [5, 5]], [1, 1, 2, 4]]), [1, 1])

    def test_expense(self):
        rules = [['expense', 'R1', 'amount', '<=', '75', 'expense_type', 'meals'], ['trip', 'R2', 'amount', '<', '100', '', ''],
                 ['expense', 'R3', 'vendor_type', '!=', 'airline', '', '']]
        exps = [['E1', 'T1', '80', 'meals', 'restaurant', 'a'], ['E2', 'T1', '30', 'travel', 'airline', 'b'], ['E3', 'T2', '10.5', 'meals', 'restaurant', 'a']]
        self.assertEqual(reference(_o.EXP2, [rules, exps]), [['R1', 'E1'], ['R2', 'T1'], ['R3', 'E2']])
        self.assertEqual(reference(_o.EXP1, [rules[:1], exps]), [['R1', 'E1']])

    def test_queue(self):
        t = ops('WorkQueue', [[1, 2], 10, 2], [('reserve', 0), ('reserve', 1), ('complete', 5, 2), ('reserve', 10), ('fail', 12, 1),
                                               ('getDeadLetters', 12), ('complete', 13, 2)])
        self.assertEqual(reference(_o.WQ1, t), [None, 1, 2, True, 1, True, [1], False])
        t = ops('WorkQueue', [[1, 2, 3, 4], [[1, 2], [2, 3], [1, 4]], 5, 1], [('reserve', 0), ('reserve', 0), ('complete', 1, 1), ('reserve', 2),
                                                                         ('reserve', 2), ('fail', 3, 2), ('getDeadLetters', 3), ('reserve', 4)])
        self.assertEqual(reference(_o.WQ2, t), [None, 1, -1, True, 2, 4, True, [2, 3], -1])

    def test_perm(self):
        tree = {'uuid': 't1', 'type': 'TEAM', 'userIds': ['u1'], 'children': [
            {'uuid': 'f1', 'type': 'FOLDER', 'userIds': ['u2'], 'children': [{'uuid': 'x1', 'type': 'FILE', 'userIds': [], 'children': []}]}]}
        q = [['u1', 'x1'], ['u2', 'x1'], ['u2', 't1'], ['u3', 'x1'], ['u1', 'zz']]
        self.assertEqual(reference(_o.PERM, [[tree], q]), [True, True, False, False, False])

    def test_fill(self):
        self.assertEqual(reference(_o.FILL, ['2 3 4 = 14']), ['2*(3+4)', '2+3*4'])
        self.assertEqual(reference(_o.FILL, ['2 3 4 = 20']), ['(2+3)*4'])
        self.assertEqual(reference(_o.FILL, ['1 1 1 = 1']), ['1*1*1'])

    def test_meet(self):
        self.assertEqual(reference(_o.MEET, [['al busy 09:00 09:59', 'bo lunch 00:00 08:59'], 60]), '10:00')
        self.assertEqual(reference(_o.MEET, [['al busy 00:00 23:58'], 2]), '-1')

    def test_free(self):
        rows = [['a', '10', '19'], ['b', '0', '4']]
        self.assertEqual(reference(_o.FREE1, [rows]), [['5', '9'], ['20', '999']])
        self.assertEqual(reference(_o.FREE2, [rows, 6]), [['20', '999']])

    def test_ipv4(self):
        root = {'name': 'r', 'isFile': False, 'lines': [], 'children': [
            {'name': 'a', 'isFile': True, 'lines': ['a 1.2.3.4, 01.2.3.4 256.0.0.1 9.9.9.9.', '0.0.0.0'], 'children': []}]}
        self.assertEqual(reference(_o.IPV4, [root]), ['0.0.0.0', '1.2.3.4'])

    def test_tile(self):
        self.assertTrue(reference(_o.TILE, [list('RB_'), list('_BR')]))
        self.assertTrue(reference(_o.TILE, [list('R_'), list('R_')]))
        self.assertFalse(reference(_o.TILE, [list('_R'), list('R_')]))
        rng = random.Random(5)  # forward BFS cross-check of the reverse-BFS reference
        for _ in range(400):
            s = [rng.choice('RB__') for _ in range(rng.randrange(1, 8))]; t = [rng.choice('RB__') for _ in range(len(s))]
            seen, stack = {tuple(s)}, [s]
            while stack:
                for b in _c._forward(stack.pop()):
                    if tuple(b) not in seen: seen.add(tuple(b)); stack.append(b)
            self.assertEqual(reference(_o.TILE, [s, t]), tuple(t) in seen)

    def test_frac(self):
        orders = [['AAPL', 'B', '0.5', '15000'], ['AAPL', 'S', '0.75', '15000'], ['GOOG', 'B', '$15', '1000']]
        self.assertEqual(reference(_o.FRAC, [orders, [['AAPL', '20']]]), [['AAPL', '45'], ['GOOG', '50']])

    def test_friend(self):
        self.assertEqual(reference(_o.FRIEND, [5, [[0, 1], [0, 2], [1, 3], [2, 3], [3, 4]]]), [3, 2, 1, 0, 1])

    def test_prof(self):
        s = ['1:main', '2:main->f', '4:main->f->f', '6:main', '9:']
        self.assertEqual(reference(_o.PROF1, [s]), [['start', 'main', 1], ['start', 'f', 2], ['start', 'f', 4], ['end', 'f', 6], ['end', 'f', 6], ['end', 'main', 9]])
        self.assertEqual(reference(_o.PROF2, [s, 2]), [['start', 'main', 1], ['start', 'f', 2], ['end', 'f', 6], ['end', 'main', 9]])
        self.assertEqual(reference(_o.PROF3, [s]), [['f', 4], ['main', 4]])

    def test_hotel(self):
        res = [{'guest_name': 'Ann', 'room_type': 'suite', 'check_in_day': 10, 'stay_length': 3}]
        tps = {'welcome': {'anchor': 'check_in', 'offset': -2}, 'survey': {'anchor': 'check_out', 'offset': 1}}
        self.assertEqual(reference(_o.HOTEL2, [res, tps]), [[8, 'Ann', 'welcome'], [14, 'Ann', 'survey']])
        tps['survey']['room_types'] = ['king']
        self.assertEqual(reference(_o.HOTEL3, [res, tps]), [[8, 'Ann', 'welcome']])
        self.assertEqual(reference(_o.HOTEL1, [res, {'a': 0, 'b': -1}]), [[9, 'Ann', 'b'], [10, 'Ann', 'a']])

    def test_diff(self):
        a, b = ['a', 'b', 'c', 'b'], ['c', 'a', 'b']
        self.assertEqual(reference(_o.DIFF1, [a, b]), [0, 1])
        self.assertEqual(reference(_o.DIFF2, [a, b]), [[0, 1]])
        self.assertEqual(reference(_o.DIFF3, [a, b]), ['+ c', '  a', '- b', '- c', '  b'])
        self.assertEqual(reference(_o.DIFF2, [['x', 'p', 'q', 'y'], ['p', 'x', 'y', 'q']]), [[0, 1], [2, 3]])

    def test_diff_reconstructs(self):
        for row in _c.build_cases(_o.DIFF3): self.assertTrue(_o.diff_reconstructs(*row['args'], row['expected']))

    def test_domain(self):
        for uid, args in [(_o.RATE, [[2, 1], 1, 1]), (_o.MOD1, ops('ModSystem', [[[2, 'a', 'ADD'], [1, 'b', 'ADD']]], [])),
                          (_o.RECT1, ops('RectangleBoard', [2, 2], [('addRectangle', 1, 0, 0, 0)])), (_o.DIAG, [[[0, 0], [0, 0]], []]),
                          (_o.EXP1, [[['trip', 'R1', 'amount', '<', '1', '', '']], []]), (_o.FILL, ['1 2 3 4 5 6 7 8 = 1']),
                          (_o.WQ2, ops('WorkQueue', [[1, 2], [[1, 2], [2, 1]], 1, 1], [])), (_o.FREE1, [[['a', '0', '5'], ['b', '5', '6']]]),
                          (_o.MEET, [['al busy 10:00 09:00'], 5]), (_o.FRIEND, [2, [[0, 1], [1, 0]]]), (_o.PROF1, [['2:a', '2:b']]),
                          (_o.TILE, [['R'], ['R', '_']]), (_o.FRAC, [[['B', 'B', '1', '1'], ['A', 'B', '1', '1']], []])]:
            with self.assertRaises(ValueError, msg=str(args)[:60]): validate_domain(uid, args)

    def test_generated_cases_domain_valid(self):
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True): validate_domain(uid, row['args'])

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
        module = _load(f'gamma_h2h02d_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
