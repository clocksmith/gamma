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


_o = _load('gamma_h2h08a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h08a_reference_test_cases', HERE / 'cases.py')
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
    def test_pay(self):
        tx = [['a', 'PAYMENT', 'PAYPAL', '', '1', '5'], ['b', 'PAYMENT', 'CREDIT', '', '0', '5'], ['c', 'PAYMENT', 'CREDIT_CARD', '', '9', '5'], ['r', 'REFUND', '', 'b', '2', '5']]
        self.assertEqual(reference(_o.PAY, [tx, 7]), [['c', 5], ['a', 2]])  # b is fully refunded already
        tx = [['x', 'PAYMENT', 'ZED', '', '1', '3'], ['y', 'PAYMENT', 'BANK', '', '1', '3'], ['w', 'PAYMENT', 'BANK', '', '1', '3']]
        self.assertEqual(reference(_o.PAY, [tx, 8]), [['w', 3], ['y', 3], ['x', 2]])
        tx = [['o', 'PAYMENT', 'CREDIT', '', '1', '4'], ['n', 'PAYMENT', 'CREDIT', '', '7', '4']]
        self.assertEqual(reference(_o.PAY, [tx, 100]), [['n', 4], ['o', 4]])

    def test_pfp(self):
        self.assertEqual(reference(_o.PFP, ['ABBA']), [2, 4])
        self.assertEqual(reference(_o.PFP, ['AABBAB']), [6])
        self.assertEqual(reference(_o.PFP, ['ZZZZ']), [1, 2, 4])

    def test_prefix_search(self):
        names = ['Ab cd', 'cd Ab', 'ab', 'AB x', 'b ab']
        self.assertEqual(reference(_o.PS1, [names, 'ab', 10]), ['AB x', 'Ab cd', 'ab', 'b ab', 'cd Ab'])
        self.assertEqual(reference(_o.PS1, [names, 'aB', 2]), ['AB x', 'Ab cd'])
        self.assertEqual(reference(_o.PS2, [['abc abd', 'xab'], 'abcz']), [['abc abd'], ['abc abd'], ['abc abd'], []])
        self.assertEqual(reference(_o.PS2, [['x ab', 'ab'], 'A']), [['ab', 'x ab']])

    def test_pel(self):
        t = ops('PriorityExpiryLRUCache', [2], [('set', 'a', 1, 5, 100, 0), ('set', 'b', 2, 1, 100, 0), ('set', 'c', 3, 9, 100, 1), ('get', 'a', 1), ('get', 'b', 1), ('get', 'c', 2)])
        self.assertEqual(reference(_o.PEL, t), [None, None, None, None, 1, -1, 3])
        t = ops('PriorityExpiryLRUCache', [2], [('set', 'a', 1, 5, 3, 0), ('set', 'b', 2, 1, 100, 0), ('get', 'a', 3), ('set', 'c', 3, 0, 4, 3), ('set', 'd', 4, 0, 9, 4), ('get', 'b', 4), ('get', 'd', 5)])
        self.assertEqual(reference(_o.PEL, t), [None, None, None, -1, None, None, 2, 4])
        t = ops('PriorityExpiryLRUCache', [2], [('set', 'a', 1, 1, 9, 0), ('set', 'b', 2, 1, 9, 0), ('get', 'a', 1), ('set', 'c', 3, 1, 9, 1), ('get', 'a', 1), ('get', 'b', 1)])
        self.assertEqual(reference(_o.PEL, t), [None, None, None, 1, None, 1, -1])

    def test_pq(self):
        self.assertEqual(reference(_o.PQ, [[2, 2, 3, 1]]), [4, 2, 1, 0])
        self.assertEqual(reference(_o.PQ, [[3, 2, 1]]), [3, 1, 0])
        self.assertEqual(reference(_o.PQ, [[]]), [0])

    def test_pbs(self):
        t = ops('BookingSystem', [[['p1', 'a', '3'], ['p2', 'a', '5'], ['p3', 'a', '2'], ['p4', 'b', '9']]], [('book', 'a', 4), ('book', 'a', 4), ('book', 'a', 1), ('book', 'b', 10)])
        self.assertEqual(reference(_o.PBS, t), [None, ['p2'], ['p1', 'p3'], [], []])
        t = ops('BookingSystem', [[['z', 'n', '4'], ['y', 'n', '4'], ['x', 'n', '8']]], [('book', 'n', 8), ('book', 'n', 8), ('book', 'n', 1)])
        self.assertEqual(reference(_o.PBS, t), [None, ['x'], ['y', 'z'], []])

    def test_pairing(self):
        self.assertEqual(reference(_o.RUP1, [['a', 'b', 'c'], [5, 7]]), [['c', 'b'], ['a']])
        self.assertEqual(reference(_o.RUP1, [['a', 'b', 'c', 'd'], [10**9, 3, 2, 0]]), [['a', 'd'], ['c', 'b']])
        self.assertEqual(reference(_o.RUP2, [[['a', 'B'], ['b', 'A'], ['c', 'A'], ['d', 'C'], ['e', 'B']]]), [['b', 'a'], ['c', 'e']])
        for n in (10, 11):  # the closed forms used by the maximum rows, checked against the literal reference at small n
            u = ['u%d' % i for i in range(n)]; m = n
            if n % 2 == 0:
                self.assertEqual(reference(_o.RUP1, [u, [0] * n]), [[u[0], u[n - 1]]] + [[u[n - 2 * k], u[n - 2 * k - 1]] for k in range(1, n // 2)])
            else:
                self.assertEqual(reference(_o.RUP1, [u, [m - k - 1 for k in range(m - 1)]]), [[u[m - 1 - 2 * j], u[m - 2 - 2 * j]] for j in range(m // 2)] + [[u[0]]])

    def test_ri(self):
        self.assertEqual(reference(_o.RI, ops('RangeIterator', [5, -1, -2], [('next',), ('next',), ('next',), ('hasNext',)])), [None, 5, 3, 1, False])
        self.assertEqual(reference(_o.RI, ops('RangeIterator', [0, 10, -1], [('hasNext',)])), [None, False])

    def test_tele(self):
        self.assertEqual(reference(_o.TELE, [[[0, 0, 0], [0, 0, 0]], [[0, 2, 1, 0]]]), 4)
        self.assertEqual(reference(_o.TELE, [[[0, 0, 0], [0, 0, 0]], [[0, 1, 0, 0]]]), -1)
        self.assertEqual(reference(_o.TELE, [[[0, 0, 0, 0], [0, 1, 0, 0]], [[0, 2, 1, 2]]]), 3)
        self.assertEqual(reference(_o.TELE, [[[0, 1, 0]], []]), -1)
        self.assertEqual(reference(_o.TELE, [[[0]], []]), 0)

    def test_bot(self):
        self.assertEqual(reference(_o.BOT, ops('DetectionSystem', [1, 1], [('isBot', '1', 0), ('isBot', '1', 0), ('isBot', '1', 1)])), [None, False, True, False])
        t = ops('DetectionSystem', [2, 3], [('isBot', '1.1', 1), ('isBot', '2', 2), ('isBot', '1.1', 3), ('isBot', '1.1', 3), ('isBot', '1.1', 4), ('isBot', '1.1', 6)])
        self.assertEqual(reference(_o.BOT, t), [None, False, False, False, True, True, False])

    def test_rfi(self):
        self.assertEqual(reference(_o.RFI, [['toast', 'tea', 'oats'], 'toast']), 2)
        self.assertEqual(reference(_o.RFI, [['aa', 'a', 'b'], 'ab']), 2)

    def test_rbs(self):
        base = [['t2', 'u1', '100', '', '5'], ['t1', 'u1', '', '30', '5'], ['t3', 'u2', '0', '50', '1'], ['t4', 'u1', '', '', '0'], ['t5', 'u2', '60', '', '2']]
        self.assertEqual(reference(_o.RBS1, [base]), [['u1', 70], ['u2', 10]])
        self.assertEqual(reference(_o.RBS2, [base, 1]), [['u1', 0], ['u2', -50]])
        self.assertEqual(reference(_o.RBS2, [base, 4]), [['u1', 0], ['u2', 10]])
        self.assertEqual(reference(_o.RBS3, [base]), [['u1', 70, 70], ['u2', 10, 10]])
        drop = [['b', 'u', '', '9', '3'], ['a', 'u', '5', '', '3'], ['c', 'u', '1', '', '1']]
        self.assertEqual(reference(_o.RBS3, [drop]), [['u', -3, 6]])  # c (+1), then a (+5) before b (-9) at the same time

    def test_boot(self):
        self.assertEqual(reference(_o.BOOT1, [['plus 3', 'jump -1']]), [0, 3])
        self.assertEqual(reference(_o.BOOT1, [['next 0', 'plus 2']]), [-1, 2])
        self.assertEqual(reference(_o.BOOT1, [['plus -4', 'jump +5']]), [-1, -4])
        self.assertEqual(reference(_o.BOOT2, [['plus 3', 'jump -1']]), [1, 3])
        self.assertEqual(reference(_o.BOOT2, [['jump 0']]), [0, 0])
        self.assertEqual(reference(_o.BOOT2, [['jump 2', 'plus 5', 'jump -1']]), [2, 0])
        self.assertEqual(reference(_o.BOOT2, [['plus -4', 'jump +5']]), [1, -4])

    def test_rsd(self):
        self.assertEqual(reference(_o.RSD, ['?', 5, 4]), '')
        self.assertEqual(reference(_o.RSD, ['?1?', 3, 1]), '111')
        self.assertEqual(reference(_o.RSD, ['?1?', 4, 1]), '')
        self.assertEqual(reference(_o.RSD, ['??', 10, 9]), '19')
        self.assertEqual(reference(_o.RSD, ['0?0', 0, 9]), '000')

    def test_tbl(self):
        t = ops('Table', [2, 3], [('selectRow', 1), ('setColor', 'red'), ('selectCell', 1, 0), ('setColor', 'blue'), ('selectTable',), ('getColor', 1, 0), ('setColor', 'z'),
                                  ('getColor', 1, 1), ('selectRow', 0), ('setColor', 'red'), ('getColor', 0, 2), ('getColor', 1, 2)])
        self.assertEqual(reference(_o.TBL, t), [None, None, None, None, None, None, 'blue', None, 'z', None, None, 'red', 'z'])
        self.assertEqual(reference(_o.TBL, ops('Table', [1, 2], [('setColor', 'red'), ('getColor', 0, 1)])), [None, None, ''])

    def test_domain(self):
        for uid, args in [(_o.PAY, [[['r', 'REFUND', '', 'p', '1', '1']], 1]), (_o.PAY, [[['p', 'PAYMENT', 'X', '', '1', '2'], ['r', 'REFUND', '', 'p', '1', '3']], 1]),
                          (_o.PAY, [[['p', 'PAYMENT', 'X', '', '1', '0']], 1]), (_o.PFP, ['abc']), (_o.PFP, ['']), (_o.PS1, [['a  b'], 'a', 1]), (_o.PS1, [['a'], 'a', 0]),
                          (_o.PS2, [['a'], '']), (_o.PEL, ops('PriorityExpiryLRUCache', [1], [('get', 'a', 5), ('get', 'a', 4)])), (_o.PEL, ops('PriorityExpiryLRUCache', [0], [])),
                          (_o.PQ, [[0]]), (_o.PBS, ops('BookingSystem', [[['a', 'n', '1'], ['a', 'n', '2']]], [])),
                          (_o.PBS, ops('BookingSystem', [[['p%d' % i, 'n', '1'] for i in range(13)]], [])), (_o.RUP1, [['a', 'b'], [1]]), (_o.RUP2, [[['a', 'b', 'c']]]),
                          (_o.RI, ops('RangeIterator', [0, 5, 0], [])), (_o.RI, ops('RangeIterator', [0, 1, 1], [('next',), ('next',)])), (_o.TELE, [[[1]], []]),
                          (_o.TELE, [[[0, 0, 0]], [[0, 1, 0, 2], [0, 2, 0, 1]]]), (_o.TELE, [[[0, 1, 0]], [[0, 0, 0, 2]]]),
                          (_o.BOT, ops('DetectionSystem', [1, 1], [('isBot', 'a', 1)])), (_o.BOT, ops('DetectionSystem', [1, 1], [('isBot', '1', 2), ('isBot', '1', 1)])),
                          (_o.RFI, [['A'], 'a']), (_o.RBS1, [[['t', 'u', 'x', '', '1']]]), (_o.RBS1, [[['t', 'u', '', '', '1'], ['t', 'v', '', '', '1']]]), (_o.RBS2, [[], -1]),
                          (_o.BOOT1, [['add 1']]), (_o.BOOT1, [[]]), (_o.BOOT2, [['plus 1']]), (_o.RSD, ['?', 1, 10]), (_o.RSD, ['a', 1, 1]),
                          (_o.TBL, ops('Table', [2, 2], [('getColor', 2, 0)])), (_o.TBL, ops('Table', [2, 2], [('setColor', '')]))]:
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
        module = _load(f'gamma_h2h08a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
