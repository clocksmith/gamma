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


_o = _load('gamma_h2h02a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h02a_reference_test_cases', HERE / 'cases.py')
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
    def test_ads(self):
        imps = [['1', 'b'], ['2', 'a'], ['3', 'b'], ['9', 'c'], ['9', 'a'], ['10', 'c']]
        self.assertEqual(reference(_o.ADS1, [imps, 2]), ['a', 'b'])
        self.assertEqual(reference(_o.ADS2, [imps, 5, 3, 9]), ['a', 'b', 'c'])
        self.assertEqual(reference(_o.ADS2, [imps, 1, 9, 10]), ['c'])

    def test_rect(self):
        self.assertEqual(reference(_o.RECT, [[[1, 1, 1], [0, 2, 5], [1, 5, 2], [1, 2, 4], [0, 3, 3], [1, 5, 3]]]), [True, True, False, True])

    def test_gpu(self):
        t = ops('CreditSystem', [], [('addCredit', 'a', 5, 0, 10), ('getBalance', 3), ('revokeCredit', 'a', 4), ('getBalance', 3), ('getBalance', 4),
                                     ('revokeCredit', 'a', 1), ('revokeCredit', 'b', 1), ('addCredit', 'b', 2, 2, 2), ('getBalance', 2)])
        self.assertEqual(reference(_o.GPU1, t), [None, None, 5, True, 5, 0, False, False, None, 7])
        t = ops('CreditSystem', [], [('addCredit', 'a', 5, 0, 10), ('addCredit', 'b', 5, 0, 5), ('consumeCredit', 3, 2), ('getBalance', 6),
                                     ('getBalance', 3), ('consumeCredit', 8, 1), ('getBalance', 3), ('consumeCredit', 1, 11)])
        self.assertEqual(reference(_o.GPU2, t), [None, None, None, True, 5, 7, True, 2, False])

    def test_nft(self):
        traits = [['eyes', ['x', 'y', 'z']], ['nose', ['p', 'q']]]
        self.assertEqual(reference(_o.NFT1, [traits, 2, [4, 1, 3, 2]]), [['y', 'q'], ['x', 'p']])
        self.assertEqual(reference(_o.NFT2, [[['e', [['x', 1], ['y', 3]]]], 3, [0, 1, 7]]), [['x'], ['y'], ['y']])
        self.assertEqual(reference(_o.NFT3, [traits, 3, [5, 0, 0]]), [['z', 'q'], ['x', 'q'], ['y', 'p']])
        self.assertEqual(reference(_o.NFT3, [traits, 7, [0] * 7]), [])

    def test_loans(self):
        parents = [['b', 'a'], ['c', 'b'], ['e', 'd']]
        self.assertEqual(reference(_o.LOAN1, [parents, [['L2', 'c'], ['L1', 'a'], ['L3', 'e'], ['L4', 'z']]]), [['a', ['L1', 'L2']], ['d', ['L3']], ['z', ['L4']]])
        self.assertEqual(reference(_o.LOAN2, [parents, [['L2', 'c', 5], ['L1', 'a', 5], ['L3', 'e', 10], ['L4', 'z', 1]]]), [['a', 10], ['d', 10], ['z', 1]])

    def test_seller(self):
        self.assertEqual(reference(_o.SELLER, [[['a', 'b'], ['b', 'c'], ['a', 'b', 'c'], ['d']]]),
                         [['a', ['b']], ['b', ['a', 'c']], ['c', ['b']], ['d', []]])

    def test_avg(self):
        self.assertEqual(reference(_o.AVG, [[['a', '-1'], ['a', '0'], ['b', '-3']]]), -1)
        self.assertEqual(reference(_o.AVG, [[['a', '5'], ['a', '6'], ['b', '4']]]), 5)
        self.assertEqual(reference(_o.AVG, [[]]), 0)

    def test_firewall(self):
        t = ops('IpFirewall', [[['DENY', '10.0.0.5'], ['ALLOW', '10.1.2.3/8'], ['ALLOW', '0.0.0.0/0']]],
                [('isAllowed', '10.0.0.5'), ('isAllowed', '10.200.0.1'), ('isAllowed', '8.8.8.8')])
        self.assertEqual(reference(_o.FIREWALL, t), [None, False, True, True])
        self.assertEqual(reference(_o.FIREWALL, ops('IpFirewall', [[['ALLOW', '1.1.1.1/32']]], [('isAllowed', '1.1.1.2')])), [None, False])

    def test_ipo(self):
        bids = [[1, 5, 5, 0], [2, 7, 8, 1], [3, 3, 5, 2], [4, 2, 5, 3], [5, 1, 4, 0]]
        self.assertEqual(reference(_o.IPO, [bids, 9]), [4, 5])
        self.assertEqual(reference(_o.IPO, [bids, 18]), [])

    def test_tree(self):
        self.assertEqual(reference(_o.TREE, [[[2, 1], [3, 1], [5, 4], [6, 4], [7, 6]]]), 4)
        self.assertEqual(reference(_o.TREE, [[[2, 9], [3, 1]]]), 1)

    def test_fraud(self):
        t = ops('DistinctPIIValuesCounter', [], [('processEvent', ['A', 'x', '1', '', 's']), ('getDistinctPIICount',), ('processEvent', ['B', 'x', '2', 'x', 's']),
                                                 ('getDistinctPIICount',), ('getSharedPIICount',)])
        self.assertEqual(reference(_o.FRAUD2, t), [None, None, 3, None, 5, 2])

    def test_pay(self):
        pays = ['p1,100,paying off:i2', 'p2,100,', 'p3,50,note, paying off:i9', 'p4,100,paying off:i2']
        invs = ['i1,100,2026-02-01', 'i2,100,2026-01-01', 'i3,100,2026-01-15']
        self.assertEqual(reference(_o.PAY1, [pays, invs]), [['p1', 'i2'], ['p2', None], ['p3', None], ['p4', 'i2']])
        self.assertEqual(reference(_o.PAY2, [pays, invs]), [['p1', 'i2'], ['p2', 'i3'], ['p3', None], ['p4', 'i1']])

    def test_simple(self):
        self.assertEqual(reference(_o.TRANSPOSE, [[[1, 2], [3, 4]], 3]), [[1, 3], [2, 4]])
        self.assertEqual(reference(_o.PRISON, [6, 6, [4], [2, 3]]), 6)
        self.assertEqual(reference(_o.ISLAND, [[['1', '1', '0'], ['0', '0', '1']]]), 6)
        self.assertEqual([reference(_o.INCR, [a]) for a in ([1, 2], [3, 1, 4], [3, 1, 0], [4, 1, 2], [5, 2, 6, 3, 9])], [0, 2, -1, -1, 3])
        self.assertEqual(reference(_o.MULTI, ops('MultiStreamReader', [['012', '34', '']], [('read', 2), ('read', 4), ('read', 2)])), [None, '01', '234', ''])

    def test_domain_and_contracts(self):
        for uid, args in [(_o.TREE, [[[1, 2], [2, 1]]]), (_o.LOAN1, [[['a', 'a']], []]), (_o.NFT1, [[['t', ['a']]], 2, [1]]),
                          (_o.FIREWALL, ops('IpFirewall', [[['ALLOW', '1.2.3.4/33']]], [])), (_o.FIREWALL, ops('IpFirewall', [[]], [('isAllowed', '256.0.0.1')])),
                          (_o.GPU1, ops('CreditSystem', [], [('addCredit', 'a', 1, 5, 4)])), (_o.AVG, [[['a', '01']]]),
                          (_o.PRISON, [3, 3, [1, 1], []]), (_o.TRANSPOSE, [[[1, 2]], 1]), (_o.PAY2, [[], ['i,1,2026-01-01', 'i,2,2026-01-02']])]:
            with self.assertRaises(ValueError, msg=str(args)[:60]): validate_domain(uid, args)
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True): validate_domain(uid, row['args'])
        self.assertEqual(set(CONTRACTS), set(_o.IDS))
        for uid, row in CONTRACTS.items():
            self.assertEqual(row['spec_basis'], 'inferred')
            iface = row['inferred_interface']
            if uid in _o.CLASSES:
                name, ctor, methods, _ = _o.CLASSES[uid]
                self.assertEqual(iface['classname'], name)
                self.assertEqual(len(iface['constructor']['params']), ctor)
                self.assertEqual({m['name']: len(m['params']) for m in iface['methods']}, methods)
            else: self.assertEqual(iface['kind'], 'function')


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
        module = _load(f'gamma_h2h02a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
