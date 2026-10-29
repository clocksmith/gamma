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


_o = _load('gamma_h2h02c_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h02c_reference_test_cases', HERE / 'cases.py')
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
    def test_windowed_store(self):
        t = ops('WindowedKeyValueStore', [2, 10], [('put', 1, 1, 0), ('put', 2, 2, 0), ('get', 1, 5), ('put', 3, 3, 6), ('get', 2, 6), ('get', 1, 9), ('get', 1, 10)])
        self.assertEqual(reference(_o.WKV, t), [None, None, None, 1, None, -1, 1, -1])

    def test_accept_language(self):
        self.assertEqual(reference(_o.ALH1, ['en-US, fr-CA, fr-FR', ['fr-FR', 'en-US']]), ['en-US', 'fr-FR'])
        self.assertEqual(reference(_o.ALH2, ['fr, en-US', ['en-US', 'fr-CA', 'fr-FR', 'de-DE']]), ['fr-CA', 'fr-FR', 'en-US'])
        self.assertEqual(reference(_o.ALH3, ['fr-FR, *', ['en-US', 'fr-FR', 'de-DE']]), ['fr-FR', 'en-US', 'de-DE'])
        self.assertEqual(reference(_o.ALH4, ['fr-FR;q=1, fr;q=0.5, *;q=0', ['en-US', 'fr-CA', 'fr-FR']]), ['fr-FR', 'fr-CA'])
        self.assertEqual(reference(_o.ALH4, ['*;q=0.1, en;q=0, en-US', ['en-GB', 'en-US', 'de-DE']]), ['en-US', 'de-DE'])

    def test_transfers(self):
        t = ops('TransactionSystem', [[['a', 100], ['b', 0]], [['a', 'b', 50], ['b', 'a', 33]]],
                [('getBalances',), ('getBalance', 'b'), ('getBalanceAfter', 'b', 1), ('getBalanceAfter', 'q', 2)])
        self.assertEqual(reference(_o.ABT2, t), [None, [['a', 66], ['b', 34]], 34, 50, -1])

    def test_sort_and_columns(self):
        self.assertEqual(reference(_o.AFS, [[2, 3, 1, 3, 2]]), [1, 2, 2, 3, 3])
        self.assertEqual(reference(_o.BAC1, [[5, 1, 1, 1, 1, 1]]), [[0], [1, 2, 3, 4, 5]])
        self.assertEqual(reference(_o.BAC2, [[5, 1, 1, 1, 1, 1], 3]), [[0], [1, 3, 5], [2, 4]])

    def test_csv(self):
        data = ['h', 'a1,Acme Corp,the acme corp,retail,10.50,2024-02-29', 'a1,Acme,widgets,retail,1,2024-01-01', 'a2,x,y,bad,1,2024-01-01',
                'a3,x,y,ok,01,2024-01-01', 'a4,x,y,ok,1,2023-02-29', 'a5,x,y,ok,1.50,2023-02-28']
        self.assertEqual(reference(_o.CSV, [data, ['bad'], ['the']]), [2, 6])

    def test_dasher(self):
        recs = [['o1', '10:00', 'ACCEPTED'], ['o2', '10:05', 'ACCEPTED'], ['o1', '10:10', 'DELIVERED'], ['o2', '10:06', 'CANCELED'], ['o3', '11:00', 'ACCEPTED']]
        self.assertEqual(reference(_o.DASH, [recs]), 300)

    def test_camera(self):
        t = ops('CameraLogServer', [], [('pollLog',), ('requestLog', 1, 5), ('requestLog', 2, 6), ('requestLog', 1, 7), ('pollCommand', 1), ('pollCommand', 3),
                                        ('sendLog', 1, 5, 'x'), ('pollLog',), ('pollCommand', 1), ('pollCommand', 1)])
        self.assertEqual(reference(_o.CAM, t), [None, None, None, None, None, 5, -1, None, [1, 5, 'x'], 7, -1])

    def test_chat(self):
        m = [[1, 'a'], [5, 'b'], [9, 'c'], [12, 'd']]
        self.assertEqual(reference(_o.CHAT1, [m, [[1, 0, 0], [9, 0, 0], [5, 0, 0]]]), [[1, 9]])
        self.assertEqual(reference(_o.CHAT1, [m, [[1, 0, 0], [12, 1, 0]]]), [[1, 1], [9, 12]])
        self.assertEqual(reference(_o.CHAT2, [[[[1, 'a'], [3, 'c']], [[2, 'b'], [3, 'c']], []]]), [[1, 'a'], [2, 'b'], [3, 'c']])

    def test_cost(self):
        report = {'region': 'r', 'services': [{'service': 's', 'hours': 7}, {'service': 's', 'hours': 5}, {'service': 't', 'hours': 1}, {'service': 'u', 'hours': 9}]}
        self.assertEqual(reference(_o.COST1, [report, {'r': {'s': '0.005', 't': '1'}}]), '1.06')
        tiers = {'r': {'s': [[10, '1'], [None, '0.5']], 't': '1'}}
        self.assertEqual(reference(_o.COST2, [report, tiers]), '12.00')
        self.assertEqual(reference(_o.COST3, [report, tiers]), {'total': '12.00', 'services': [['s', '11.00'], ['t', '1.00']]})

    def test_storage(self):
        t = ops('CloudStorage', [], [('addFile', 'a/b.txt', 10), ('addFile', 'a/b.txt', 3), ('copyFile', 'a', 'x'), ('copyFile', 'a/b.txt', 'c.txt'),
                                     ('findFile', '', '.txt'), ('addUser', 'u1', 15), ('addFileBy', 'u1', 'u.txt', 10), ('copyFile', 'u.txt', 'v.txt'),
                                     ('addUser', 'u2', 4), ('addFileBy', 'u2', 'w', 4), ('mergeUser', 'u1', 'u2'), ('backupUser', 'u1'),
                                     ('addFileBy', 'u1', 'z', 1), ('restoreUser', 'u1'), ('getFilesize', 'z'), ('getFilesize', 'w')])
        self.assertEqual(reference(_o.CSS4, t), [None, True, False, False, True, ['a/b.txt(10)', 'c.txt(10)'], True, 5, False, True, 0, 5, 2, 4, 2, -1, 4])

    def test_snake(self):
        self.assertEqual(reference(_o.SNAKE, ['__the_variable = my_counter+a__b+_x_+X_y+var_1+q_']), '__theVariable = myCounter+a__b+_x_+X_y+var1+q_')

    def test_mining(self):
        txs = [['a', 3, 4], ['b', 1, 2], ['c', 2, 2]]
        self.assertEqual(reference(_o.MINE1, [txs, 3]), 4)
        self.assertEqual(reference(_o.MINE2, [txs, 3]), ['a'])  # fee 4 and size 3 either way; index list [0] < [1, 2]
        self.assertEqual(reference(_o.MINE2, [[['a', 2, 3], ['b', 1, 3], ['c', 1, 0]], 2]), ['b'])
        self.assertEqual(reference(_o.MINE3, [[['b', 1, 10, 'a'], ['a', 5, 1, None]], 5]), 1)
        self.assertEqual(reference(_o.MINE3, [[['b', 1, 10, 'a'], ['a', 5, 1, None]], 6]), 11)

    def test_fx(self):
        self.assertEqual(reference(_o.FX, [[['BGP', 'USD', '109.0'], ['USD', 'EUR', '0.9']], 'BGP', 'EUR']), '98.1')
        self.assertEqual(reference(_o.FX, [[['AAA', 'BBB', '2'], ['BBB', 'CCC', '0.5'], ['AAA', 'CCC', '1.5']], 'AAA', 'CCC']), '1.5')
        self.assertEqual(reference(_o.FX, [[], 'USD', 'EUR']), '-1')
        self.assertEqual(reference(_o.FX, [[], 'USD', 'USD']), '1')

    def test_revenue(self):
        t = ops('CustomerRevenueSystem', [], [('insert', 10), ('insertWithReferrer', 5, 0), ('insertWithReferrer', 7, 1), ('getLowestK', 3, 0), ('getLowestK', 5, 13),
                                              ('getNestedRevenue', 0, 0), ('getNestedRevenue', 0, 1), ('getNestedRevenue', 0, 2)])
        self.assertEqual(reference(_o.CRS2, t), [None, 0, 1, 2, [2, 1, 0], [0], 10, 15, 22])

    def test_connect_four(self):
        t = ops('ConnectFour', [], [('play', c) for c in [0, 1, 0, 1, 0, 1, 0, 1]])
        self.assertEqual(reference(_o.C4, t), [None] + ['ONGOING'] * 6 + ['A_WINS', 'INVALID'])
        t = ops('ConnectFour', [], [('play', c) for c in [0, 1, 1, 2, 2, 3, 2, 3, 3, 6, 3]])
        self.assertEqual(reference(_o.C4, t)[-1], 'A_WINS')

    def test_kvdb(self):
        t = ops('InMemoryKVDB', [], [('rollback',), ('set', 'a', '1'), ('begin',), ('set', 'a', '2'), ('begin',), ('delete', 'a'), ('count', '2'),
                                     ('rollback',), ('get', 'a'), ('count', '2'), ('commit',), ('get', 'a'), ('rollback',)])
        self.assertEqual(reference(_o.KVDB, t), [None, False, None, None, None, None, None, 0, True, '2', 1, True, '2', False])

    def test_index(self):
        t = ops('DocumentLibrary', [[['d1', 'The quick brown fox'], ['d2', 'quick, BROWN!'], ['d3', 'brown quick']]], [('search', 'Quick brown'), ('search', '!!'), ('search', 'fox')])
        self.assertEqual(reference(_o.INV, t), [None, ['d1', 'd2'], [], ['d1']])

    def test_domain(self):
        for uid, args in [(_o.ALH1, ['en', []]), (_o.ALH2, ['*', []]), (_o.ALH4, ['en;q=1.5', []]), (_o.AFS, [[10**10]]),
                          (_o.WKV, ops('WindowedKeyValueStore', [1, 1], [('put', 1, 1, 5), ('get', 1, 4)])),
                          (_o.ABT1, ops('TransactionSystem', [[['a', 1]], [['a', 'a', 5]]], [])),
                          (_o.DASH, [[['o', '10:00', 'DELIVERED']]]), (_o.CHAT2, [[[[1, 'a']], [[1, 'b']]]]),
                          (_o.COST1, [{'region': 'r', 'services': []}, {'r': {'s': [[None, '1']]}}]),
                          (_o.MINE3, [[['a', 1, 1, 'b'], ['b', 1, 1, 'a']], 5]), (_o.FX, [[['AAA', 'BBB', '2'], ['BBB', 'AAA', '0.6']], 'AAA', 'BBB']),
                          (_o.CRS1, ops('CustomerRevenueSystem', [], [('insertWithReferrer', 1, 0)])), (_o.SNAKE, ['é'])]:
            with self.assertRaises(ValueError, msg=str(args)[:60]): validate_domain(uid, args)

    def test_generated_cases_domain_valid(self):
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True): validate_domain(uid, row['args'])

    def test_contract_layouts_match_classes(self):
        for uid, row in CONTRACTS.items():
            iface = row['inferred_interface']
            if uid in _o.CLASSES:
                name, ctor, methods, voids = _o.CLASSES[uid]
                self.assertEqual(iface['classname'], name)
                self.assertEqual(len(iface['constructor']['params']), ctor)
                self.assertEqual({m['name']: len(m['params']) for m in iface['methods']}, methods)
                self.assertEqual({m['name'] for m in iface['methods'] if m['return']['type'] == 'void'}, set(voids))
            else: self.assertIn('name', iface)
        self.assertEqual(set(CONTRACTS), set(_o.IDS))


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
        module = _load(f'gamma_h2h02c_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
