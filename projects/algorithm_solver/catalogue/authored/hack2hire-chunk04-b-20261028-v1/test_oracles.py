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


_o = _load('gamma_h2h04b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h04b_reference_test_cases', HERE / 'cases.py')
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
    def test_bsv(self):
        self.assertEqual(reference(_o.BSV, [[1, 2, 2, 2, 5], 2]), 1)
        self.assertEqual(reference(_o.BSV, [[1, 2, 2, 2, 5], 4]), 3)
        self.assertEqual(reference(_o.BSV, [[1, 2, 2, 2, 5], 0]), -1)
        self.assertEqual(reference(_o.BSV, [[1, 2, 2, 2, 5], 9]), 4)

    def test_btc(self):
        t = reference(_o.BTC, ['aabbbc'])
        self.assertEqual(t['count'], 6)
        self.assertEqual(t['left']['ch'], 'b')  # c(1)+a(2) -> #3 (id 3); then b(3, id 1) before #3 (id 3)
        self.assertEqual((t['right']['left']['ch'], t['right']['right']['ch']), ('c', 'a'))
        self.assertEqual(reference(_o.BTC, ['zz']), {'ch': 'z', 'count': 2, 'left': None, 'right': None})
        self.assertIsNone(reference(_o.BTC, ['']))
        for row in _c.build_cases(_o.BTC): self.assertTrue(_o.huffman_valid(row['args'][0], row['expected']))

    def test_trans(self):
        logs = [['3', 'u1', '/c'], ['1', 'u1', '/a'], ['2', 'u2', '/a'], ['2', 'u1', '/b']]
        self.assertEqual(reference(_o.TRANS, [logs]), [['/a', '/b', 1], ['/a', 'END', 1], ['/b', '/c', 1], ['/c', 'END', 1], ['START', '/a', 2]])
        self.assertEqual(reference(_o.TRANS, [[['10', 'u', 'x'], ['9', 'u', 'y']]]), [['START', 'y', 1], ['x', 'END', 1], ['y', 'x', 1]])

    def test_cake(self):
        self.assertEqual(reference(_o.CAKE, [[3, 2, 1], [[1, 1, 1], [2, 0, 1], [2, 1, 0], [0, 1, 0]]]), [True, False, True, False])

    def test_eq(self):
        arr = ['x', 'x = y + 3 + y', 'y = 4']
        self.assertEqual(reference(_o.EQ1, [arr]), 11)
        self.assertEqual(reference(_o.EQ2, [['x', 'x = y - 10 + 1', 'y = 4']]), -5)
        self.assertIsNone(reference(_o.EQ3, [['x', 'x = y', 'y = x + 1']]))
        self.assertIsNone(reference(_o.EQ3, [['x', 'x = y']]))
        self.assertEqual(reference(_o.EQ3, [['x', 'x = 2', 'y = y']]), 2)

    def test_wait(self):
        # [3,1,2]: t1 A, t2 B done(2), t3 C, t4 A, t5 C done(5), t6 A done(6); waits 6-3 + 2-1 + 5-2 = 7
        self.assertEqual(reference(_o.WAIT, [[3, 1, 2]]), 7)
        self.assertEqual(reference(_o.WAIT, [[]]), 0)

    def test_elev(self):
        ev = [['9', 'down'], ['2', 'up'], ['6', 'idle'], ['5', 'up']]
        self.assertEqual(reference(_o.ELEV, [ev, ['4', 'up']]), 1)  # 2 up (dist 2) ties idle 6 (dist 2): lower index
        self.assertEqual(reference(_o.ELEV, [ev, ['8', 'down']]), 0)
        self.assertEqual(reference(_o.ELEV, [[['1', 'down']], ['4', 'down']]), -1)

    def test_chat(self):
        t = ops('ChatEventAggregator', [10], [('recordEvent', 1, 'al', 'c1'), ('recordEvent', 5, 'bo', 'c1'), ('recordEvent', 5, 'al', 'c1'),
                                              ('getUserCount', 10, 'al'), ('getUserCount', 11, 'al'), ('getChatCount', 14, 'c1'),
                                              ('getChatUserCount', 14, 'c1'), ('getChatUserCount', 15, 'c1')])
        self.assertEqual(reference(_o.CHAT3, t), [None, None, None, None, 2, 1, 2, 2, 0])
        with self.assertRaises(ValueError):
            validate_domain(_o.CHAT1, ops('ChatEventAggregator', [3], [('recordEvent', 2, 'al', 'c'), ('recordEvent', 2, 'al', 'd')]))

    def test_pwd(self):
        self.assertEqual(reference(_o.PWD, [['abc', 'zab', 'aaa'], ['bd', 'ac', 'abc']]), ['YES', 'YES', 'NO'])

    def test_cprime(self):
        self.assertEqual([reference(_o.CPRIME, [n]) for n in (2, 11, 19, 197, 101, 1, 23)],
                         [True, True, False, True, False, False, False])
        circular = [n for n in range(1, 1000) if reference(_o.CPRIME, [n])]
        self.assertEqual(circular, [2, 3, 5, 7, 11, 13, 17, 31, 37, 71, 73, 79, 97, 113, 131, 197, 199, 311, 337, 373, 719, 733, 919, 971, 991])

    def test_alloc(self):
        reqs = [['store', '3', '3'], ['store', '0', '2'], ['store', '4', '1'], ['free', '4', '3'], ['store', '4', '2']]
        # 5 slots: store at 3 wraps 3,4,0 -> 3; store 2 from 0: 1,2 -> 1; full -> -1; free 4,0,1 -> 3 freed; store 2 from 4: 4,0 -> 4
        self.assertEqual(reference(_o.ALLOC, [5, reqs]), [3, 1, -1, 3, 4])

    def test_coins(self):
        self.assertEqual(reference(_o.COINS, [0, [1, 0, 0], [5, 2, 3]]), 5)
        self.assertEqual(reference(_o.COINS, [0, [2, 0, 0], [1, 2, 3]]), 5)
        self.assertEqual(reference(_o.COINS, [1, [0, 1, 0], [1, 1, 9]]), 10)

    def test_collatz(self):
        self.assertEqual([reference(_o.COLLATZ, [n]) for n in (1, 2, 3, 6, 7, 27, 8400511)], [0, 1, 7, 8, 16, 111, 685])

    def test_houses(self):
        for n in range(1, 7):
            for k in range(1, 5):
                for a in range(k):
                    for b in range(k):
                        self.assertEqual(reference(_o.HOUSES, [n, k, a, b]), _o.brute_houses(n, k, a, b), (n, k, a, b))

    def test_load(self):
        reqs = [[0, 's1', 'LIGHT'], [60, 's1', 'HEAVY'], [121, 's1', 'STANDARD'], [7, 's2', 'LIGHT'], [7, 's2', 'LIGHT'], [1, 'zz', 'HEAVY']]
        self.assertEqual(reference(_o.LOAD, [[['s1', 10], ['s2', 0], ['s3', 4]], reqs]), [['s1', 10 + 1 + 6 + 3 + 3], ['s2', 8], ['s3', 4]])

    def test_bed(self):
        d = ['Sunny STUDIO', 'Large 1-Bedroom', 'studio or one bedroom', 'two bedroom', '1br', 'studios', 'one,bedroom']
        self.assertEqual(reference(_o.BED, [d, [1, 0, 1, 0, 0, 1, 0]]), [0, 1, 1, 0, 1, 1, 1])

    def test_domain(self):
        for uid, args in [(_o.BSV, [[2, 1], 0]), (_o.BTC, ['a1']), (_o.TRANS, [[['1', 'u', 'START']]]), (_o.TRANS, [[['1', 'u', 'a'], ['1', 'u', 'b']]]),
                          (_o.CAKE, [[1, 1], []]), (_o.EQ1, [['x', 'x = 1 - 1']]), (_o.EQ2, [['x', 'x = y']]), (_o.EQ2, [['x', 'x = x']]),
                          (_o.EQ1, [['x', 'x = 1', 'x = 2']]), (_o.WAIT, [[0]]), (_o.ELEV, [[['1', 'up']], ['1', 'idle']]),
                          (_o.CHAT2, ops('ChatEventAggregator', [3], [('getChatCount', 5, 'c'), ('getUserCount', 4, 'a')])),
                          (_o.PWD, [['a'], []]), (_o.CPRIME, [0]), (_o.ALLOC, [3, [['store', '3', '1']]]), (_o.COINS, [0, [], []]),
                          (_o.COLLATZ, [0]), (_o.HOUSES, [3, 2, 2, 0]), (_o.LOAD, [[['a', 1], ['a', 2]], []]), (_o.BED, [['x'], [2]])]:
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
        module = _load(f'gamma_h2h04b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
