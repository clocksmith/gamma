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


_o = _load('gamma_h2h04a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h04a_reference_test_cases', HERE / 'cases.py')
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
    def test_credit(self):
        t = ops('AccountCreditTracker', [], [('addAccount', 10), ('addAccountWithReferral', 5, 0), ('addAccountWithReferral', 7, 0),
                                             ('addAccountWithReferral', 1, 1), ('getTotalCredit', 0), ('getTotalCredit', 1), ('getTotalCredit', 3),
                                             ('getTopAccounts', 2), ('getTopAccounts', 20)])
        self.assertEqual(reference(_o.CREDIT2, t), [None, 0, 1, 2, 3, 22, 6, 1, [0, 2], [0, 2, 1, 3]])

    def test_router(self):
        cmds = ['REGISTER a 0 0 2', 'REGISTER b 0 1 1', 'REGISTER a 1 1 1', 'REGISTER c 91 0 1', 'REGISTER c 0 0 0', 'ROUTE 0 0', 'ROUTE 0 0',
                'ROUTE 0 0', 'ROUTE 0 0', 'RELEASE a', 'ROUTE 0 1', 'DOWN a', 'ROUTE 0 0', 'UP zz']
        t = ops('RequestRouter', [], [('processCommand', c) for c in cmds])
        self.assertEqual(reference(_o.ROUTE3, t), [None, 'OK', 'OK', 'ERROR', 'ERROR', 'ERROR', 'a', 'a', 'b', 'ERROR', 'OK', 'a', 'OK', 'ERROR', 'ERROR'])
        self.assertEqual(reference(_o.ROUTE1, t)[10:], ['ERROR', 'ERROR', 'ERROR', 'ERROR', 'ERROR'])

    def test_snap(self):
        t = ops('SocialNetwork', [], [('follow', 1, 2), ('snapshot',), ('unfollow', 1, 2), ('follow', 1, 3), ('snapshot',), ('follow', 2, 3),
                                      ('follow', 3, 4), ('snapshot',), ('isFollowing', 1, 2, 0), ('isFollowing', 1, 2, 1), ('getFollowees', 1, 1),
                                      ('recommend', 1, 2, 5), ('recommend', 2, 2, 5), ('recommend', 4, 2, 5)])
        self.assertEqual(reference(_o.SNAP3, t), [None, None, 0, None, None, 1, None, None, 2, True, False, [3], [4], [4], []])

    def test_stay(self):
        self.assertEqual(reference(_o.STAY, [[[5, 5, 6], [6, 7], [7, 5]], 5, 7]), [[0, 1], [0, 2], [2, 1]])
        self.assertEqual(reference(_o.STAY, [[[1, 2, 3], [1, 2, 3]], 1, 3]), [[0], [1], [0, 1], [1, 0]])
        self.assertEqual(reference(_o.STAY, [[[4], [4]], 4, 4]), [[0], [1]])

    def test_iter(self):
        t = ops('SubarrayFirstIterator', [[1, 2, 2, 3], [2]], [('next',), ('next',), ('next',), ('hasNext',)])
        self.assertEqual(reference(_o.ITER, t), [None, 2, 1, 3, False])

    def test_stock(self):
        self.assertEqual(reference(_o.STOCK, [0, 0, 2]), 2)
        self.assertEqual(reference(_o.STOCK, [2, 0, 4]), 4)
        self.assertEqual(reference(_o.STOCK, [3, 5, 1]), 0)

    def test_stock_closed_form_matches_enumeration(self):
        from itertools import product
        for i in range(4):
            for t in range(4):
                for m in range(7):
                    count = 0
                    for length in range(m + 1):
                        for seq in product((1, -1), repeat=length):
                            h, ok = i, True
                            for s in seq:
                                h += s; ok = ok and h >= 0
                            count += ok and h == t
                    self.assertEqual(reference(_o.STOCK, [i, t, m]), count)

    def test_love(self):
        self.assertEqual(reference(_o.LOVE, [[['a', 'b', 'hi'], ['a', 'b', 'love'], ['c', 'b', 'x'], ['b', 'a', '']], 5]), ['b', 'a'])

    def test_incident(self):
        logs = ['3,m,500,2', '1,m,500,2', '2,m,200,5', '9,m,500,4']
        self.assertEqual(reference(_o.INC1, [logs, 3, 4]), ['3,m,500'])
        self.assertEqual(reference(_o.INC2, [logs + ['9,m,200,1'], 3, 2, 50]), ['1,m,500'])
        self.assertEqual(reference(_o.INC3, [logs + ['9,m,200,1'], 3, 2, 50]), ['1,m,500', '9,m,500'])

    def test_tree(self):
        self.assertEqual(reference(_o.TREE, [[[1, 2], [3]], '1']), [[2, 3]])
        self.assertEqual(reference(_o.TREE, [[[0], [1], [2]], '2']), [[0, 2], [1, 2]])

    def test_tree_rank_is_a_bijection_onto_valid_trees(self):
        for groups in ([[0, 1], [2], [3, 4, 5]], [[0], [1], [2], [3]], [[9, 8], [7, 6], [5], [4]]):
            seen = set()
            for r in range(_o.tree_count(groups)):
                edges = reference(_o.TREE, [groups, str(r)])
                self.assertTrue(_o.tree_is_valid(groups, edges))
                seen.add(frozenset(frozenset(e) for e in edges))
            self.assertEqual(len(seen), _o.tree_count(groups))

    def test_time(self):
        self.assertEqual(reference(_o.TIME, [2, 3, 5, 9]), 1)
        self.assertEqual(reference(_o.TIME, [0, 0, 0, 0]), 1)
        self.assertEqual(reference(_o.TIME, [9, 9, 9, 9]), 0)

    def test_sched(self):
        self.assertEqual(reference(_o.SCHED, ['??00000', 3, 2]), ['1200000', '2100000'])
        self.assertEqual(reference(_o.SCHED, ['8000000', 7, 8]), [])

    def test_atm(self):
        self.assertEqual(reference(_o.ATM, [[2, 5, 1], 2]), [1, 3, 2])

    def test_balance(self):
        logs = ['t1,a,5,3', 't2,a,-7,1', 't1,b,2,0', 't3,b,-2,0']
        self.assertEqual(reference(_o.BAL1, [logs]), [['a', -2], ['b', 0]])
        self.assertEqual(reference(_o.BAL2, [logs]), [['a', -2], ['b', -2]])
        self.assertEqual(reference(_o.BAL3, [logs]), [[['a', 5], ['b', 0]], ['t3', 't2']])

    def test_add(self):
        self.assertEqual(reference(_o.ADD, [['-', '5'], ['1', '0']]), 5)
        self.assertEqual(reference(_o.ADD, [['-', '1', '0', '0'], ['0', '0', '7']]), -93)

    def test_agg(self):
        now = 10**9
        txs = [['1.5', 'm', 'COMPLETED', 'u', str(now)], ['2.05', 'm', 'COMPLETED', 'u', str(now - 86399)], ['3', 'm', 'COMPLETED', 'u', str(now - 86400)],
               ['4', 'n', 'PENDING', 'u', str(now)], ['9', 'n', 'COMPLETED', 'u', str(now + 1)]]
        self.assertEqual(reference(_o.AGG, [txs, str(now)]), [['m', '3.55', 2]])

    def test_mine(self):
        self.assertEqual(reference(_o.MINE, [[['1', '10'], ['2', '0']], [['t', '1', '2', '10'], ['u', '1', '2', '1'], ['v', '2', '1', '11']]]), [['2', '10'], ['1', '0']])

    def test_domain(self):
        for uid, args in [(_o.CREDIT1, ops('AccountCreditTracker', [], [('addAccountWithReferral', 1, 0)])),
                          (_o.CREDIT1, ops('AccountCreditTracker', [], [('getTopAccounts', 1)])),
                          (_o.ROUTE1, ops('RequestRouter', [], [('processCommand', 'ROUTE  0 0')])),
                          (_o.SNAP1, ops('SocialNetwork', [], [('isFollowing', 1, 2, 0)])), (_o.SNAP1, ops('SocialNetwork', [], [('follow', 1, 1)])),
                          (_o.STAY, [[[1]], 3, 2]), (_o.ITER, ops('SubarrayFirstIterator', [[], []], [('next',)])), (_o.STOCK, [0, 0, 501]),
                          (_o.LOVE, [[['a', 'b']], 1]), (_o.INC1, [['1,m,302,1'], 1, 1]), (_o.INC2, [['1,m,500,1'], 1, 1]),
                          (_o.TREE, [[[1], [1]], '0']), (_o.TREE, [[[1], [2]], '1']), (_o.TIME, [10, 0, 0, 0]), (_o.SCHED, ['???????', 28, 8]),
                          (_o.ATM, [[0], 1]), (_o.BAL1, [['t,a,01,1']]), (_o.ADD, [['1', '-'], ['1']]), (_o.ADD, [['2', '0', '0'], ['1']]),
                          (_o.AGG, [[['1.234', 'm', 'COMPLETED', 'u', '0']], '0']), (_o.MINE, [[['1', '1'], ['1', '2']], []])]:
            with self.assertRaises(ValueError, msg=str(args)[:60]): validate_domain(uid, args)

    def test_generated_cases_domain_valid(self):
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True): validate_domain(uid, row['args'])

    def test_tree_maximum_rows_are_valid_trees(self):
        for args, expected in _c.maximum_rows(_o.TREE): self.assertTrue(_o.tree_is_valid(args[0], expected))

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
        module = _load(f'gamma_h2h04a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
