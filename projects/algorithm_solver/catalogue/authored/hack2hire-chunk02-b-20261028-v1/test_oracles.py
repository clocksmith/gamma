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


_o = _load('gamma_h2h02b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h02b_reference_test_cases', HERE / 'cases.py')
reference, validate_domain, o = _o.reference, _o.validate_domain, _o
CONTRACTS = {row['uid']: row for row in json.loads((HERE / 'contracts.json').read_text())['problems']}


def stem(uid): return uid.split(':', 1)[1]


def exact(a, b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(map(exact, a, b))
    if type(a) is dict: return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    return a == b


def ops(name, ctor, calls): return _c._ops(name, ctor, calls)


ORG = [['B', 'D'], ['A', 'B', 'C']]
CART = ['s1|apple|2|150', 's1|apple|-1|5', '|x|1|1', 's2|pear|007|010', 's3|fig|1|2|3']


class References(unittest.TestCase):
    """Hand-derived expectations for the INFERRED specifications."""
    def test_org(self):
        self.assertEqual(reference(o.ORG1, [ORG]), ['A', '  B', '    D', '  C'])
        self.assertEqual(reference(o.ORG2, [ORG]), ['A (3)', '  B (1)', '    D (0)', '  C (0)'])
        self.assertEqual(reference(o.ORG3, [ORG, 'D']), ['A', 'B', 'D'])
        self.assertEqual([reference(o.ORG4, [ORG, 'D', 'C']), reference(o.ORG4, [ORG, 'D', 'B']), reference(o.ORG4, [ORG, 'C', 'C'])], ['A', 'B', 'C'])

    def test_pivot(self):
        rows = [['order_id', 'cost', 'sell_price', 'product', 'date'], ['1', '1.50', '2', 'milk', '2024-01-05'],
                ['2', '3', '1.25', 'milk', '2024-02-01'], ['3', '0', '0.1', 'eggs', '2024-01-31']]
        self.assertEqual(reference(o.PIVOT, [rows]), [['product', '2024-01', '2024-02'], ['eggs', '0.10', '0.00'], ['milk', '0.50', '-1.75']])

    def test_percentile(self):
        self.assertEqual([reference(o.PCT, [['5,2', '3,2'], 50]), reference(o.PCT, [['5,2', '3,2'], 51]), reference(o.PCT, [['7,1'], 1])], [3, 5, 7])

    def test_pythagorean(self):
        self.assertEqual(reference(o.PYTH, [5, [0, 1, 2, 3], [1, 2, 3, 4], 0, 0, 4]), 1)
        self.assertEqual(reference(o.PYTH, [1, [], [], 0, 0, 0]), 1)

    def test_qlog(self):
        self.assertEqual(reference(o.QLOG, [['Q: a b', 'L: b a c', 'Q: c', 'L: c', 'L: z']]), ['ACK: a b; ID=1', 'M: b a c; Q=1', 'ACK: c; ID=2', 'M: c; Q=2'])

    def test_negate_prefix(self):
        self.assertEqual(reference(o.NEGATE, [[1, 2, 3], [[1, 2], [2, 3]]]), [-1, 2, -3])
        self.assertEqual(reference(o.PREFIX, [['abc', 'ab', 'b']]), ['abc', 'b'])

    def test_count_and_say(self):
        self.assertIn('3322251', reference(o.RCS, ['23321511']))
        self.assertEqual([reference(o.RCS, ['1211']), reference(o.RCS, ['10']), reference(o.RCS, ['111']), reference(o.RCS, ['1111']), reference(o.RCS, ['01'])],
                         [['21'], ['0'], ['11111111111'], [], []])

    def test_reversi(self):
        b = [['.', 'W', 'B'], ['.', '.', '.'], ['.', '.', '.']]
        self.assertEqual(reference(o.REVERSI, [b, 0, 0, 'B']), [['B', 'B', 'B'], ['.', '.', '.'], ['.', '.', '.']])
        self.assertEqual(reference(o.REVERSI, [b, 1, 1, 'B']), b)

    def test_cart(self):
        self.assertEqual(reference(o.CART1, [CART]), [9, 370])
        self.assertEqual(reference(o.CART2, [CART]), ['s1|apple|2|300', 's2|pear|7|70'])
        self.assertEqual(reference(o.CART3, [CART, 1]), ['s1|apple|2|300'])

    def test_dfa_drain(self):
        self.assertTrue(reference(o.DFA, ['aab', [[1, 0], [0, 1]], 0, [0]]))
        self.assertFalse(reference(o.DFA, ['ab', [[1, 0], [0, 1]], 0, [0]]))
        self.assertEqual(reference(o.DRAIN, [[-1, 0, 0, 1], [1, 2, 3, 4]]), 2)

    def test_nary(self):
        self.assertEqual(reference(o.NARY1, [[['r', 1, 1, 2], ['a', 2], ['b', 3, 3], ['c', 4]]]), [['r', 1], ['a', 2], ['b', 3], ['c', 4]])
        self.assertEqual(reference(o.NARY2, [[['r', 1, 1], ['a', 2]], [['r', 10, 1, 2], ['b', 5], ['a', 7]]]), [['r', 11, 1, 2], ['a', 9], ['b', 5]])

    def test_maze(self):
        m = {'/': {'message': 'ok', 'next': ['/a', '/b']}, '/a': {'message': 'ok', 'next': ['/c']},
             '/b': {'message': 'Congrats', 'next': []}, '/c': {'message': 'Congrats', 'next': []}}
        self.assertEqual(reference(o.MAZE1, [m]), '/b')
        h = {'/': {'message': 'ok', 'next': ['/a'], 'headers': {'Token': 'x'}}, '/a': {'message': 'Congrats', 'next': [], 'requiredHeaders': {'Token': 'x'}}}
        self.assertEqual(reference(o.MAZE2, [h]), '/a')
        del h['/']['headers']
        self.assertEqual(reference(o.MAZE2, [h]), '')

    def test_journey(self):
        logs = [['u1', '10', 'buy'], ['u1', '9', 'view'], ['u2', '1', 'view'], ['u2', '2', 'cart']]
        self.assertEqual(reference(o.JOURNEY, [logs]), ['view (2)', '  buy (1)', '  cart (1)'])

    def test_classes(self):
        t = ops('SnapshotSet', [], [('add', 1), ('add', 2), ('getIterator',), ('remove', 1), ('add', 1), ('contains', 1), ('next', 0), ('next', 0),
                                    ('hasNext', 0), ('getIterator',), ('next', 1), ('next', 1)])
        self.assertEqual(reference(o.SNAP, t), [None, True, True, 0, True, True, True, 1, 2, False, 1, 2, 1])
        t = ops('ToDoList', [], [('add', 'a', 'x', 'TODO'), ('add', 'b', 'y', 'TODO'), ('addDependency', 'a', 'b'), ('addDependency', 'b', 'a'),
                                 ('getExecutionOrder',), ('get', 'a'), ('add', 'a', 'z', 'DONE'), ('updateStatus', 'a', 'DONE'), ('get', 'a'), ('get', 'q')])
        self.assertEqual(reference(o.TODO2, t), [None, None, None, True, False, ['b', 'a'], ['a', 'x', 'TODO'], None, True, ['a', 'x', 'DONE'], []])
        t1 = [t[0][:5], t[1][:5]]
        self.assertEqual(reference(o.TODO1, t1), [None, None, None, True, True])
        t = ops('FunctionLibrary', [], [('register', 'f', ['int'], True), ('register', 'g', ['int', 'int'], False),
                                        ('findMatches', ['int', 'int']), ('findMatches', []), ('findMatches', ['int'])])
        self.assertEqual(reference(o.VARIADIC, t), [None, None, None, ['f', 'g'], [], ['f']])

    def test_domain(self):
        for uid, args in [(o.ORG1, [[['A', 'B'], ['B', 'A']]]), (o.ORG1, [[['A', 'B'], ['C', 'D']]]), (o.ORG3, [ORG, 'Z']),
                          (o.PCT, [['1,0'], 5]), (o.PCT, [['1,1'], 0]), (o.PYTH, [3, [0, 1], [1, 0], 0, 0, 0]),
                          (o.NEGATE, [[1], [[1, 2]]]), (o.PREFIX, [['a', 'a']]), (o.RCS, ['']), (o.REVERSI, [[['.', 'X'], ['.', '.']], 0, 0, 'B']),
                          (o.DFA, ['c', [[0, 0]], 0, []]), (o.DRAIN, [[-1, 2, 1], [0, 0, 0]]), (o.NARY2, [[['a', 1]], [['b', 1]]]),
                          (o.NARY2, [[['a', 1, 1, 2], ['b', 1], ['b', 2]], [['a', 1]]]),
                          (o.SNAP, ops('SnapshotSet', [], [('getIterator',), ('next', 0)])),
                          (o.VARIADIC, ops('FunctionLibrary', [], [('register', 'f', [], True)])),
                          (o.JOURNEY, [[['u', '1', 'a'], ['u', '1', 'b']]])]:
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
            else: self.assertEqual(len(row['inferred_interface']['params']), _o.ARITY[uid])


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
        module = _load(f'gamma_h2h02b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
            worst = max(worst, time.process_time() - t0)
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
        TIMES['node_jitless'][uid] = round(max(g['cpu'] for g in out), 4)
        self.assertEqual(len(out), len(rows)); return len(out)

    def test_candidates(self):
        only = os.environ.get('GAMMA_ONLY')
        for uid in _o.IDS:
            if only and only not in uid: continue
            rows = _c.build_cases(uid, include_maximum=True)
            for language, runner in [('python', self.run_python), ('javascript', self.run_javascript)]:
                with self.subTest(uid=uid, language=language):
                    print(f'{uid} {language} {runner(uid, rows)}/{len(rows)} passed', flush=True)
        print('HEAVIEST_CPU_SECONDS ' + json.dumps(TIMES), flush=True)


if __name__ == '__main__': unittest.main()
