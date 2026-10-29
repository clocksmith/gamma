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


_o = _load('gamma_h2h11b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h11b_reference_test_cases', HERE / 'cases.py')
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
    def test_fbt(self):
        reqs = [['1', 'v1/REGISTER/ann/100'], ['2', 'v1/REGISTER/bo/5'], ['3', 'v1/TRANSFER/ann/bo/10'], ['4', 'v1/FRIEND_REQUEST/ann/bo'], ['5', 'v1/ACCEPT_FRIEND_REQUEST/4'],
                ['6', 'v1/ACCEPT_FRIEND_REQUEST/4'], ['7', 'v1/TRANSFER/ann/bo/100'], ['8', 'v1/TRANSFER/ann/bo/1'], ['9', 'v1/BALANCE/bo'], ['10', 'v1/BALANCE/cy'],
                ['11', 'v1/REGISTER/bo/1'], ['12', 'v1/FRIEND_REQUEST/bo/ann'], ['13', 'v1/FRIEND_REQUEST/bo/bo'], ['14', 'v1/TRANSFER/bo/bo/1']]
        self.assertEqual(reference(_o.FBT, [reqs]), ['OK', 'OK', 'ERROR', 'OK', 'OK', 'ERROR', 'OK', 'ERROR', '105', 'ERROR', 'ERROR', 'ERROR', 'ERROR', 'ERROR'])
        reqs = [['7', 'v1/REGISTER/a/0'], ['3', 'v1/REGISTER/b/0'], ['1', 'v1/FRIEND_REQUEST/a/b'], ['2', 'v1/FRIEND_REQUEST/b/a'], ['9', 'v1/ACCEPT_FRIEND_REQUEST/2'],
                ['8', 'v1/ACCEPT_FRIEND_REQUEST/1'], ['5', 'v1/ACCEPT_FRIEND_REQUEST/7']]
        self.assertEqual(reference(_o.FBT, [reqs]), ['OK', 'OK', 'OK', 'OK', 'OK', 'OK', 'ERROR'])  # second pending request still accepts

    def test_fsq(self):
        self.assertEqual(reference(_o.FSQ, [[2, 8, 4, 3, 2], 7, 11, 3]), 8)
        self.assertEqual(reference(_o.FSQ, [[5], 4, 4, 4]), -1)
        self.assertEqual(reference(_o.FSQ, [[1, 1, 1, 1], 1, 1, 1]), -1)
        self.assertEqual(reference(_o.FSQ, [[3, 3, 3], 10, 0, 0]), 6)
        self.assertEqual(reference(_o.FSQ, [[], 0, 0, 0]), 0)

    def test_guu(self):
        self.assertEqual(reference(_o.GUU, [['John Smith', 'Jane Smith', 'John Q Smith', 'Alexander Montgomery', 'Al Montgomeryx', 'ann lee']]),
                         ['jsmith', 'jsmith1', 'jsmith2', 'amontgom', 'amontgo1', 'alee'])
        # truncation collision: 'abcdefgh' + 1 and 'abcdefg' + 1 both give 'abcdefg1'
        self.assertEqual(reference(_o.GUU, [['A Bcdefgh', 'A Bcdefgh', 'A Bcdefg', 'A Bcdefg']]), ['abcdefgh', 'abcdefg1', 'abcdefg', 'abcdefg2'])

    def test_gds(self):
        self.assertEqual(reference(_o.GDS, [[[9, 10], [9, 10], [9, 11]], 1]), 2)
        self.assertEqual(reference(_o.GDS, [[[9, 17]] * 5, 2]), 5)
        self.assertEqual(reference(_o.GDS, [[[16, 17], [15, 17], [9, 17]], 1]), 3)
        self.assertEqual(reference(_o.GDS, [[[9, 11], [9, 10], [10, 11]], 1]), 2)

    def test_hop(self):
        self.assertEqual(reference(_o.HOP, [['R'], 0]), 0)
        self.assertEqual(reference(_o.HOP, [['X'], 0]), -1)
        self.assertEqual(reference(_o.HOP, [['R2', 'X', 'L1R1', 'R'], 0]), 2)
        self.assertEqual(reference(_o.HOP, [['R', 'L', 'R'], 0]), -1)
        self.assertEqual(reference(_o.HOP, [['L3R2', 'R', 'R', 'L2', 'R10', 'L'], 2]), -1)
        self.assertEqual(reference(_o.HOP, [['R3', 'L', 'X', 'L2R', 'R1'], 0]), 2)  # 0 -> 3 -> 4

    def test_ipr(self):
        routes = [['192.168.1.0/24', 'a'], ['192.168.0.0/16', 'b'], ['0.0.0.0/0', 'c'], ['192.168.1.123/32', 'd'], ['192.168.1.0/24', 'e']]
        self.assertEqual(reference(_o.IPR, [routes, ['192.168.1.123', '192.168.1.7', '192.168.2.1', '10.0.0.1', '192.168.1.124']]), ['d', 'e', 'b', 'c', 'e'])
        self.assertEqual(reference(_o.IPR, [[['10.255.0.0/8', 'x']], ['10.0.0.0', '11.0.0.0']]), ['x', ''])

    def test_dsj(self):
        c = ['id,name', '1,ann', '2,bob', '3,cy', '2,dee']; p = ['pid,id,amt', 'p1,2,5', 'p2,4,7', 'p3,2,9']
        inner = ['id,name,pid,id,amt', '2,bob,p1,2,5', '2,bob,p3,2,9', '2,dee,p1,2,5', '2,dee,p3,2,9']
        self.assertEqual(reference(_o.DSJ1, [c, p, 'id']), inner)
        left = ['id,name,pid,id,amt', '1,ann,,,', '2,bob,p1,2,5', '2,bob,p3,2,9', '3,cy,,,', '2,dee,p1,2,5', '2,dee,p3,2,9']
        self.assertEqual(reference(_o.DSJ2, [c, p, 'id']), left)
        self.assertEqual(reference(_o.DSJ3, [c, p, 'id']), left + [',,p2,4,7'])
        self.assertEqual(reference(_o.DSJ4, [c, p, ['id']]), inner)
        self.assertEqual(reference(_o.DSJ3, [['id'], ['id', ''], 'id']), ['id,id', ','])
        self.assertEqual(reference(_o.DSJ1, [['id', ''], ['id', ''], 'id']), ['id,id', ','])  # empty keys match
        self.assertEqual(reference(_o.DSJ3, [['id,name'], ['amt,id', '1,1'], 'id']), ['id,name,amt,id', ',,1,1'])
        self.assertEqual(reference(_o.DSJ4, [['a,b,c', '1,x,q', '1,y,r', '2,x,s'], ['b,z,a', 'x,1,1', 'y,2,1', 'x,3,2'], ['a', 'b']]),
                         ['a,b,c,b,z,a', '1,x,q,x,1,1', '1,y,r,y,2,1', '2,x,s,x,3,2'])

    def test_its(self):
        t = ops('TaskScheduler', [], [('getExecutionOrder',), ('addTask', 'c', ['a', 'b']), ('addTask', 'a', []), ('getExecutionOrder',), ('addTask', 'b', ['a']),
                                      ('getExecutionOrder',), ('addTask', 'b', []), ('addTask', 'd', ['d']), ('addTask', 'e', ['f']), ('addTask', 'f', ['c', 'e']),
                                      ('addTask', 'f', ['c']), ('getExecutionOrder',)])
        self.assertEqual(reference(_o.ITS, t), [None, [], True, True, ['a'], True, ['a', 'b', 'c'], False, False, True, False, True, ['a', 'b', 'c', 'f', 'e']])
        t = ops('TaskScheduler', [], [('addTask', 'z', []), ('addTask', 'b', []), ('addTask', 'a', ['z']), ('getExecutionOrder',)])
        self.assertEqual(reference(_o.ITS, t), [None, True, True, True, ['b', 'z', 'a']])  # smallest ready id first

    def test_iwf(self):
        t = ops('FilterIterator', [[3, -2, 0, 7, 8, -5], 'odd'], [('hasNext',), ('next',), ('next',), ('hasNext',), ('hasNext',), ('next',), ('hasNext',)])
        self.assertEqual(reference(_o.IWF, t), [None, True, 3, 7, True, True, -5, False])
        t = ops('FilterIterator', [[3, -2, 0, 7, 8, -5], 'nonzero'], [('next',)] * 5 + [('hasNext',)])
        self.assertEqual(reference(_o.IWF, t), [None, 3, -2, 7, 8, -5, False])
        self.assertEqual(reference(_o.IWF, ops('FilterIterator', [[-4, 0, 6], 'even'], [('next',)] * 3)), [None, -4, 0, 6])

    def test_jbh(self):
        self.assertEqual(reference(_o.JBH, [[0], 0]), -1)
        self.assertEqual(reference(_o.JBH, [[1], 0]), 0)
        self.assertEqual(reference(_o.JBH, [[1, 1, 1], 1]), -1)
        self.assertEqual(reference(_o.JBH, [[1, 3, 2, 9, 9], 2]), 2)  # 2 -left 2-> 0 -right 1-> 1 -left 3-> out

    def test_kvp(self):
        t = ops('KVStore', [], [('set', 'apple', 3), ('set', 'app', 1), ('set', 'b', 2), ('get', 'apple'), ('get', 'ap'), ('prefixSearch', 'ap'), ('update', 'app', 9),
                                ('prefixSearch', ''), ('deleteKey', 'apple'), ('deleteKey', 'zz'), ('prefixSearch', 'app'), ('get', 'apple'), ('prefixSearch', 'c')])
        self.assertEqual(reference(_o.KVP, t), [None, None, None, None, 3, -1, [1, 3], None, [9, 3, 2], None, None, [9], -1, []])

    def test_klc(self):
        for digits, want in [('', []), ('2', ['D']), ('22', ['DD', 'E']), ('111', ['AAA', 'AB', 'BA', 'C']), ('7777', ['SSSS', 'SST', 'STS', 'TSS', 'TT']),
                             ('0000', ['ZZZZ']), ('12', ['AD']), ('9919', ['XXAX', 'YAX'])]:
            self.assertEqual(reference(_o.KLC, [digits]), want)

    def test_lcb(self):
        self.assertEqual(reference(_o.LCB, [[5, 3, 8, 1, 4, None, 9], [7, 4, 9, None, None, 8]]), 9)
        self.assertEqual(reference(_o.LCB, [[1], [2]]), -1)
        self.assertEqual(reference(_o.LCB, [[2, 1, 3], [3, 2, None, 1]]), 3)

    def test_lgs(self):
        for args, want in [([1, []], 1), ([3, [[0, 1], [1, 2]]], 2), ([5, [[0, 1], [0, 2], [0, 3], [0, 4]]], 4), ([4, []], 4),
                           ([7, [[0, 1], [1, 2], [2, 3], [4, 5]]], 4), ([6, [[0, 1], [1, 2], [1, 3], [3, 4], [3, 5]]], 4)]:
            self.assertEqual(reference(_o.LGS, args), want)

    def test_lkw(self):
        self.assertEqual(reference(_o.LKW, [[1, 3, -1, -3, 5, 3, 6, 7], 2, 3]), [[3, 1], [3, -1], [5, -1], [5, 3], [6, 5], [7, 6]])
        self.assertEqual(reference(_o.LKW, [[4, 4, 4], 2, 2]), [[4, 4], [4, 4]])
        self.assertEqual(reference(_o.LKW, [[5, 1, 9], 3, 3]), [[9, 5, 1]])

    def test_lra(self):
        sq = [[1, 1], [1, 3], [3, 1], [3, 3], [2, 2]]; six = [[1, 1], [1, 3], [3, 1], [3, 3], [4, 1], [4, 3]]; diamond = [[0, 1], [1, 0], [2, 1], [1, 2], [5, 5]]
        self.assertEqual([reference(_o.LRA1, [p]) for p in ([], sq, six, diamond)], [0, 4, 6, 0])
        self.assertEqual([reference(_o.LRA2, [p]) for p in ([], sq, six, diamond)], [0, 4, 6, 2])
        self.assertEqual(reference(_o.LRA2, [[[0, 0], [2, 1], [1, 3], [-1 + 2, 2 - 2]]]), 0)  # not a rectangle

    def test_domain(self):
        K, T, F = 'KVStore', 'TaskScheduler', 'FilterIterator'
        for uid, args in [(_o.FBT, [[['1', 'v1/REGISTER/a/1'], ['1', 'v1/BALANCE/a']]]), (_o.FBT, [[['1', 'v1/DEPOSIT/a/1']]]), (_o.FBT, [[['1', 'v1/TRANSFER/a/b/0']]]),
                          (_o.FBT, [[['1', 'v1/REGISTER/a/1000000001']]]), (_o.FSQ, [[0], 1, 1, 1]), (_o.FSQ, [[1], -1, 1, 1]),
                          (_o.GUU, [['Solo']]), (_o.GUU, [['Ann  Lee']]), (_o.GUU, [['Ann O\'Neil']]), (_o.GDS, [[[9, 9]], 1]), (_o.GDS, [[[8, 10]], 1]), (_o.GDS, [[[9, 18]], 1]),
                          (_o.GDS, [[], 0]), (_o.HOP, [[], 0]), (_o.HOP, [['R0'], 0]), (_o.HOP, [['R01'], 0]), (_o.HOP, [['U'], 0]), (_o.HOP, [['R'], 1]), (_o.HOP, [['R200000'], 0]),
                          (_o.IPR, [[['1.2.3.4/33', 'a']], []]), (_o.IPR, [[], ['1.2.3']]), (_o.IPR, [[], ['01.2.3.4']]), (_o.IPR, [[['1.2.3.4/8', '']], []]),
                          (_o.DSJ1, [['id,id', '1,1'], ['id'], 'id']), (_o.DSJ1, [['id', '1,2'], ['id'], 'id']), (_o.DSJ1, [['id'], ['x'], 'id']), (_o.DSJ1, [['id', 'a"b'], ['id'], 'id']),
                          (_o.DSJ4, [['id'], ['id'], 'id']), (_o.DSJ4, [['id'], ['id'], ['id', 'id']]), (_o.DSJ1, [['id'] + ['k'] * 400, ['id'] + ['k'] * 400, 'id']),
                          (_o.ITS, ops(T, [], [('addTask', 'A', [])])), (_o.ITS, ops(T, [], [('addTask', 'a', ['b', 'b'])])), (_o.ITS, ops(T, [], [('addTask', 'a', ['b'] * 11)])),
                          (_o.IWF, ops(F, [[1], 'prime'], [])), (_o.IWF, ops(F, [[2], 'odd'], [('next',)])), (_o.IWF, ops(F, [[1.5], 'odd'], [])),
                          (_o.JBH, [[], 0]), (_o.JBH, [[-1], 0]), (_o.JBH, [[1], 1]),
                          (_o.KVP, ops(K, [], [('set', 'a', 1), ('set', 'a', 2)])), (_o.KVP, ops(K, [], [('update', 'a', 1)])), (_o.KVP, ops(K, [], [('set', 'A', 1)])),
                          (_o.KVP, ops(K, [], [('set', 'a', 10**10)])), (_o.KLC, ['12a']), (_o.KLC, ['1' * 30]),
                          (_o.LCB, [[], [1]]), (_o.LCB, [[2, 3], [1]]), (_o.LCB, [[2, 1, 2], [1]]), (_o.LCB, [[2, None], [1]]), (_o.LCB, [[5, 3, 8, None, 9], [1]]),
                          (_o.LGS, [0, []]), (_o.LGS, [3, [[0, 1], [1, 2], [2, 0]]]), (_o.LGS, [2, [[0, 0]]]), (_o.LGS, [2, [[0, 1], [1, 0]]]),
                          (_o.LKW, [[1, 2], 3, 2]), (_o.LKW, [[1, 2], 1, 3]), (_o.LKW, [[], 1, 1]), (_o.LKW, [[0] * 20000, 20, 1]),
                          (_o.LRA1, [[[1, 1], [1, 1]]]), (_o.LRA1, [[[-1, 0]]]), (_o.LRA2, [[[0, i] for i in range(301)]])]:
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
        module = _load(f'gamma_h2h11b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
