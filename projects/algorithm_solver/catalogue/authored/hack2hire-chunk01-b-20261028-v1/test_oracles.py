import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import time
import unittest
HERE = Path(__file__).parent
def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, file); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
_o = _load('gamma_h2h_c01b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h_c01b_reference_test_cases', HERE / 'cases.py')
reference, validate_domain, o = _o.reference, _o.validate_domain, _o
WRAPPERS = {o.ENC1: 'minEncryptOperations', o.ENC2: 'minStateOperations', o.FANCY: 'countFancyNumbers',
            o.FILT1: 'filterUnsafeMessages', o.FILT2: 'filterUnsafeMessages', o.CAM: 'findCameraAdmins',
            o.DASH: 'closestDashmartDistances', o.MODE: 'findClusterMode', o.MED: 'findClusterMedian',
            o.DEST1: 'findDestinationNode', o.DEST2: 'findDestinationNodes', o.DUP1: 'findDuplicateFiles',
            o.DUP2: 'findDuplicateFiles', o.TRADE: 'maxTradedShares', o.SHOP: 'minShoppers', o.MISS: 'findMissingWords',
            o.COM1: 'optimalCommuteMode', o.COM2: 'optimalCommuteCost', o.ROBOT: 'findRobotPositions',
            o.STOP1: 'textBeforeStopWords', o.STOP2: 'streamBeforeStopWords', o.SOCK1: 'countSockPairs', o.SOCK2: 'findSockPairs'}
def d(name, dirs=(), files=()):return {'name': name, 'directories': list(dirs), 'files': list(files)}
def ef(name, flag):return {'name': name, 'isEncrypted': flag}
def exact(a, b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(map(exact, a, b))
    return a == b
def exact_js(a, b):
    """JavaScript has one number type: int/float spelling is not observable, values must still be equal."""
    if type(a) in (int, float) and type(b) in (int, float): return a == b
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(map(exact_js, a, b))
    return a == b
class References(unittest.TestCase):
    def test_buffer(self):
        self.assertEqual(reference(o.BUF, [['BufferedFile', 'write', 'write', 'flush', 'flush'], [[3], [[1, 2]], [[3, 4, 5, 6, 7]], [], []]]), [None, [], [1, 2, 3, 4, 5, 6], [7], []])
    def test_encryption(self):
        a = d('root', [d('a', files=[ef('x', True), ef('y', True)])], [ef('p', True), ef('q', False)])
        b = d('root', [d('a', files=[ef('x', True)])], [ef('p', True), ef('q', True), ef('r', False)])
        self.assertEqual([reference(o.ENC1, [a]), reference(o.ENC2, [a])], [2, 2])
        self.assertEqual([reference(o.ENC1, [b]), reference(o.ENC2, [b])], [3, 2])
        self.assertEqual(reference(o.ENC2, [d('root', [d('e')])]), 0)
    def test_fancy(self):self.assertEqual([reference(o.FANCY, [n]) for n in (1, 2, 5, 18, 10**9)][:4], [0, 1, 2, 5])
    def test_filter(self):
        m = [['a', 'hello world'], ['b', 'helloworld'], ['c', 'hi']]
        self.assertEqual(reference(o.FILT1, [m, ['world']]), [['b', 'helloworld'], ['c', 'hi']])
        self.assertEqual(reference(o.FILT2, [m, ['world']]), [['c', 'hi']])
    def test_camera(self):
        p = [['u1', 'cameraOwner', 'c'], ['u2', 'groupMember', 'g1'], ['g1', 'subgroupMember', 'g2'], ['g2', 'groupCameraOwner', 'c'],
             ['u3', 'groupMember', 'g2'], ['u4', 'groupMember', 'g3'], ['g3', 'subgroupMember', 'g3']]
        self.assertEqual(reference(o.CAM, [p, 'c']), ['u1', 'u2', 'u3'])
    def test_dashmart(self):self.assertEqual(reference(o.DASH, [['D X', '   '], [[0, 2], [1, 2], [0, 1], [0, 0]]]), [-1, 3, 1, 0])
    def test_cluster(self):
        self.assertEqual(reference(o.MODE, [[[3, 1], [1, 3], [2, 2]]]), 1)
        self.assertEqual(reference(o.MED, [[[5, 1], [2, 4]]]), 3); self.assertIs(type(reference(o.MED, [[[5, 1], [2, 4]]])), int)
        self.assertEqual(reference(o.MED, [[[1], [2]]]), 1.5); self.assertEqual(reference(o.MED, [[[1, 2], [3]]]), 2)
    def test_destination(self):
        self.assertEqual([reference(o.DEST1, [[[1, 2], [2, 3]], 1]), reference(o.DEST1, [[[1, 2], [2, 1]], 1]), reference(o.DEST1, [[[1, 2]], 5])], [3, -1, 5])
        self.assertEqual(reference(o.DEST2, [[[1, 2], [1, 3], [3, 4], [2, 2]], 1]), [4])
    def test_duplicates(self):
        def f(n, c):return {'name': n, 'content': c}
        root = d('root', [d('d', files=[f('c', [1, 2]), f('e', [3])])], [f('a', [1, 2]), f('b', [1, 2]), f('z', [])])
        self.assertEqual(reference(o.DUP1, [root]), [['/a', '/b', '/d/c']])
        def g(n, c):return {'name': n, 'chunks': c}
        root2 = d('root', [d('d', files=[g('c', [[1], [2]])])], [g('a', [[1, 2]]), g('b', [[], [1, 2], []]), g('z', [[2, 1]])])
        self.assertEqual(reference(o.DUP2, [root2]), [['/a', '/b', '/d/c']])
    def test_trade(self):self.assertEqual(reference(o.TRADE, [[[10, 5, 'buy'], [9, 3, 'sell'], [11, 4, 'sell'], [12, 10, 'buy']]]), 7)
    def test_shoppers(self):
        self.assertEqual(reference(o.SHOP, [[[2, 0], [2, 0], [2, 0]], 3]), 2); self.assertEqual(reference(o.SHOP, [[[2, 0], [2, 0], [2, 0]], 1]), -1)
    def test_missing(self):
        self.assertEqual(reference(o.MISS, ['I like eating cheese', 'like cheese']), ['I', 'eating'])
        self.assertEqual(reference(o.MISS, ['a b a', 'a']), ['b', 'a'])
    def test_commute(self):
        args = [['S22', '11D'], ['Walk', 'Bike'], [3, 1], [0, 5]]
        self.assertEqual(reference(o.COM1, args), 'Bike'); self.assertEqual(reference(o.COM2, args), [2, 10])
        self.assertEqual(reference(o.COM2, [['S1D'], ['Walk'], [3], [4]]), [3, 4]); self.assertEqual(reference(o.COM1, [['SXD'], ['Walk'], [3], [4]]), '')
    def test_robot(self):self.assertEqual(reference(o.ROBOT, [[['O', 'E', 'X'], ['E', 'O', 'E']], [1, 1, 2, 2]]), [[0, 0]])
    def test_stop(self):
        self.assertEqual(reference(o.STOP1, ['hello world stop here', ['stop', 'world']]), 'hello ')
        self.assertEqual(reference(o.STOP2, [['hel', 'lo wo', 'rld'], ['world']]), ['hel', 'lo ', '', ''])
        self.assertEqual(reference(o.STOP2, [['ab', 'x'], ['abc', 'b']]), ['', 'a', ''])
    def test_socks(self):
        args = [[5, 3, 8, 1], ['r', 'r', 'r', 'b'], ['left', 'right', 'right', 'left']]
        self.assertEqual(reference(o.SOCK1, args), 1); self.assertEqual(reference(o.SOCK2, args), [[5, 3]])
    def test_domain(self):
        for pid, args in [(o.FANCY, [0]), (o.DEST1, [[[1, 2], [1, 3]], 1]), (o.MISS, ['a b', 'b a']), (o.SOCK1, [[1, 1], ['r', 'r'], ['left', 'right']]),
                          (o.CAM, [[['x', 'cameraOwner', 'g'], ['y', 'groupMember', 'g']], 'g']), (o.MODE, [[[1, 2, 3], [4]]]),
                          (o.COM1, [['SS'], ['A'], [1], [1]]), (o.BUF, [['BufferedFile', 'close'], [[1], []]]), (o.STOP1, ['x', ['']])]:
            with self.assertRaises(ValueError, msg=str(args)[:60]):validate_domain(pid, args)
    def test_generated_cases_domain_valid(self):
        for pid in o.IDS:
            for row in _c.build_cases(pid, include_maximum=True):validate_domain(pid, row['args'])
JS_RUNNER = r'''
const fs=require('fs');const job=JSON.parse(fs.readFileSync(0,'utf8'));const mod=require(job.path);const out=[];
for(const args of job.cases){const before=JSON.stringify(args);const t0=process.cpuUsage();let value,native=null;
 value=mod(...args);const t1=process.cpuUsage(t0);
 if(job.cls){const C=mod[job.cls];const r=new C(...args[1][0]);native=[null];for(let i=1;i<args[0].length;i++)native.push(r[args[0][i]](...args[1][i]));}
 else native=mod[job.wrapper](...args);
 out.push({value,native,unchanged:JSON.stringify(args)===before,cpu:(t1.user+t1.system)/1e6});}
process.stdout.write(JSON.stringify(out));'''
TIMES = {'python3': {}, 'node_jitless': {}}
class Candidates(unittest.TestCase):
    """Author-local self-check of own candidates against own generated cases; not isolated qualification."""
    def run_python(self, pid, rows):
        path = HERE / 'python' / f'{o.vid(pid)}.py'
        if not path.exists(): self.skipTest('candidate absent')
        module = _load(f'gamma_h2h_c01b_candidate_python_{o.vid(pid)}', path); passed = 0; worst = 0.0
        for row in rows:
            args = copy.deepcopy(row['args']); t0 = time.process_time(); value = module.solve(*args); worst = max(worst, time.process_time() - t0)
            if pid in o.CLASSES:
                receiver = getattr(module, o.CLASSES[pid])(*args[1][0]); native = [None] + [getattr(receiver, n)(*r) for n, r in zip(args[0][1:], args[1][1:])]
            else: native = getattr(module.Solution(), WRAPPERS[pid])(*args)
            self.assertTrue(exact(value, row['expected']) and exact(native, row['expected']), f'{o.vid(pid)} python {str(row["args"])[:80]}')
            self.assertEqual(args, row['args']); passed += 1
        TIMES['python3'][o.vid(pid)] = round(worst, 4)
        return passed
    def run_javascript(self, pid, rows):
        path = HERE / 'javascript' / f'{o.vid(pid)}.js'
        if not path.exists() or not shutil.which('node'): self.skipTest('candidate or node absent')
        job = {'path': str(path), 'cases': [r['args'] for r in rows], 'cls': o.CLASSES.get(pid), 'wrapper': WRAPPERS.get(pid)}
        out = json.loads(subprocess.run(['node', '--jitless', '--stack-size=65500', '-e', JS_RUNNER], input=json.dumps(job), capture_output=True, text=True, check=True).stdout)
        for row, got in zip(rows, out):
            self.assertTrue(exact_js(got['value'], row['expected']) and exact_js(got['native'], row['expected']), f'{o.vid(pid)} javascript {str(row["args"])[:80]}')
            self.assertTrue(got['unchanged'])
        self.assertEqual(len(out), len(rows))
        TIMES['node_jitless'][o.vid(pid)] = round(max(g['cpu'] for g in out), 4)
        return len(out)
    def test_candidates(self):
        for pid in o.IDS:
            rows = _c.build_cases(pid, include_maximum=True)
            for language, runner in [('python', self.run_python), ('javascript', self.run_javascript)]:
                with self.subTest(pid=pid, language=language):
                    print(f'{o.vid(pid)} {language} {runner(pid, rows)}/{len(rows)} passed', flush=True)
        print('HEAVIEST_CASE_CPU_SECONDS ' + json.dumps(TIMES, sort_keys=True), flush=True)
if __name__ == '__main__':unittest.main()
