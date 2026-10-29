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


_o = _load('gamma_h2h10b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h10b_reference_test_cases', HERE / 'cases.py')
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
    def test_tkl(self):
        t = ops('TokenLimiter', [], [('setPolicy', 'a', 5, 2, 3, 0), ('consume', 'a', 4, 1), ('consume', 'a', 2, 2), ('consume', 'a', 2, 3),
                                     ('getTokens', 'a', 8), ('getTokens', 'a', 9), ('setPolicy', 'a', 1, 1, 1, 9), ('getTokens', 'a', 9)])
        self.assertEqual(reference(_o.TKL, t), [None, None, True, False, True, 3, 5, None, 1])
        self.assertEqual(reference(_o.TKL, ops('TokenLimiter', [], [('consume', 'a', 1, 0), ('getTokens', 'a', 0)])), [None, False, -1])

    def test_wms(self):
        t = ops('WorkerManagementSystem', [], [('addWorker', 'Ann', 'Dev', 10), ('addWorker', 'Ann', 'QA', 1), ('registerWorker', 'Ann', 5), ('get', 'Ann'),
                                               ('registerWorker', 'Ann', 9), ('registerWorker', 'Bob', 10), ('registerWorker', 'Ann', 12), ('get', 'Ann'), ('get', 'Bob')])
        for uid in _o.WMS: self.assertEqual(reference(uid, t), [None, True, False, 'registered', 0, 'registered', 'invalid_request', 'registered', 4, -1])
        t = ops('WorkerManagementSystem', [], [('addWorker', 'B', 'Dev', 1), ('addWorker', 'A', 'Dev', 1), ('addWorker', 'C', 'QA', 1), ('registerWorker', 'A', 1), ('registerWorker', 'A', 4),
                                               ('registerWorker', 'B', 5), ('registerWorker', 'B', 8), ('topNWorkers', 5, 'Dev'), ('topNWorkers', 1, 'Dev'), ('topNWorkers', 1, 'Ops')])
        self.assertEqual(reference(_o.WMS2, t)[-3:], ['A(3), B(3)', 'A(3)', ''])
        t = ops('WorkerManagementSystem', [], [('addWorker', 'A', 'Dev', 10), ('registerWorker', 'A', 0), ('registerWorker', 'A', 10), ('promote', 'A', 'Lead', 20, 15),
                                               ('promote', 'A', 'X', 1, 0), ('registerWorker', 'A', 12), ('registerWorker', 'A', 16), ('registerWorker', 'A', 20), ('registerWorker', 'A', 25),
                                               ('get', 'A'), ('calcSalary', 'A', 5, 22), ('topNWorkers', 5, 'Lead'), ('topNWorkers', 5, 'Dev'), ('calcSalary', 'Z', 0, 1)])
        self.assertEqual(reference(_o.WMS3, t)[4:], ['success', 'invalid_request', 'registered', 'registered', 'registered', 'registered', 19, 130, 'A(5)', '', -1])
        t = ops('WorkerManagementSystem', [], [('addWorker', 'A', 'Dev', 3), ('setDoublePaid', 2, 6), ('setDoublePaid', 4, 8), ('registerWorker', 'A', 0), ('registerWorker', 'A', 10),
                                               ('calcSalary', 'A', 0, 10), ('calcSalary', 'A', 7, 20)])
        self.assertEqual(reference(_o.WMS4, t)[-2:], [48, 12])

    def test_tas(self):
        t = ops('TaskManager', [], [('addTask', 1, 'a', 3), ('addTask', 2, 'a', 3), ('updateTask', 3, 'taskId2', 'b', -1), ('updateTask', 4, 'taskId3', 'c', 0),
                                    ('getTask', 5, 'taskId2'), ('getTask', 6, 'taskId1'), ('getTask', 7, 'taskId9')])
        for uid in _o.TAS: self.assertEqual(reference(uid, t), [None, 'taskId1', 'taskId2', True, False, 'b(-1)', 'a(3)', ''])
        t = ops('TaskManager', [], [('addTask', 1, 'fix bug', 1), ('addTask', 2, 'Bug', 5), ('addTask', 3, 'bugfix', 1), ('addTask', 4, 'docs', 9),
                                    ('searchTasks', 5, 'bug', 10), ('searchTasks', 6, 'bug', 1), ('listTasksSorted', 7, 2), ('listTasksSorted', 8, 10)])
        self.assertEqual(reference(_o.TAS2, t)[5:], [['taskId1', 'taskId3'], ['taskId1'], ['taskId4', 'taskId2'], ['taskId4', 'taskId2', 'taskId1', 'taskId3']])
        t = ops('TaskManager', [], [('addTask', 1, 'x', 0), ('addTask', 2, 'y', 0), ('addUser', 3, 'u', 1), ('addUser', 4, 'u', 5), ('assignTask', 5, 'taskId1', 'u', 10),
                                    ('assignTask', 6, 'taskId2', 'u', 8), ('assignTask', 7, 'taskId1', 'v', 20), ('getUserTasks', 8, 'u'), ('assignTask', 10, 'taskId2', 'u', 15),
                                    ('getUserTasks', 11, 'u'), ('assignTask', 12, 'taskId9', 'u', 20), ('addUser', 13, 'w', 2), ('assignTask', 14, 'taskId1', 'w', 30),
                                    ('assignTask', 15, 'taskId1', 'w', 40), ('assignTask', 16, 'taskId2', 'w', 20), ('getUserTasks', 17, 'w')])
        self.assertEqual(reference(_o.TAS3, t)[3:], [True, False, True, False, False, ['taskId1'], True, ['taskId2'], False, True, True, False, True, ['taskId2', 'taskId1']])
        t = ops('TaskManager', [], [('addTask', 1, 'x', 0), ('addTask', 2, 'y', 0), ('addUser', 3, 'u', 2), ('assignTask', 4, 'taskId1', 'u', 10), ('assignTask', 5, 'taskId2', 'u', 6),
                                    ('completeTask', 6, 'taskId2', 'u'), ('completeTask', 7, 'taskId1', 'u'), ('getOverdueAssignments', 8, 'u'), ('completeTask', 9, 'taskId1', 'u'),
                                    ('getOverdueAssignments', 20, 'u'), ('getOverdueAssignments', 21, 'z')])
        self.assertEqual(reference(_o.TAS4, t), [None, 'taskId1', 'taskId2', True, True, True, False, True, ['taskId2'], False, ['taskId2'], []])

    def test_pag(self):
        t = ops('Paginator', [10, 5, 5], [('next',), ('goTo', 10), ('prev',), ('goTo', 1), ('goTo', 99)])
        self.assertEqual(reference(_o.PAG, t), [None, '< ... 4 5 [6] 7 8 ... >', '< ... 6 7 8 9 [10]', '< ... 6 7 8 [9] 10 >', '[1] 2 3 4 5 ... >', '< ... 6 7 8 9 [10]'])
        self.assertEqual(reference(_o.PAG, ops('Paginator', [3, 7, 2], [('prev',)])), [None, '[1] 2 3 >'])
        self.assertEqual(reference(_o.PAG, ops('Paginator', [10, 4, 1], [('goTo', 5)])), [None, '< ... 4 [5] 6 7 ... >'])

    def test_enc(self):
        t = ops('Codec', [], [('encode', [1, 1, 2, 2, 2]), ('encode', list(range(5, 14))), ('encode', [0]), ('decode', ['RLE[5, 2]', 'BP[3, 1, 2]'])])
        self.assertEqual(reference(_o.ENC, t), [None, ['BP[1, 1, 1]', 'RLE[2, 3]'], ['BP[4, 5, 6, 7, 8, 9, 10, 11, 12]', 'BP[4, 13]'], ['BP[1, 0]'], [5, 5, 1, 2]])

    def test_eqf(self):
        for s, want in [('aabb', True), ('abac', True), ('aabbccc', True), ('aabbcd', False), ('abcc', True), ('aaaabb', False), ('a', True), ('aaabbbcc', False)]:
            self.assertEqual(reference(_o.EQF, [s]), want, s)

    def test_esl(self):
        self.assertEqual(reference(_o.ESL, [3, [1, 2, 3]]), 1)
        self.assertEqual(reference(_o.ESL, [7, [1, 1, 1, 1, 2, 3, 4]]), 4)
        self.assertEqual(reference(_o.ESL, [7, [1, 5, 1, 1, 1, 2, 9]]), 11)
        self.assertEqual(reference(_o.ESL, [1, [5]]), 0)

    def test_ejt(self):
        c = lambda v: {'operation': 'CONSTANT_NUMBER', 'value': v}
        d = lambda op, a, b: {'operation': op, 'inputs': [a, b]}
        self.assertEqual(reference(_o.EJT, [d('DIVIDE', c(-7), c(2))]), -3)
        self.assertEqual(reference(_o.EJT, [d('DIVIDE', c(7), c(-2))]), -3)
        self.assertEqual(reference(_o.EJT, [d('DIVIDE', c(1), c(3))]), 0)
        self.assertEqual(reference(_o.EJT, [d('SUBTRACT', c(3), d('MULTIPLY', c(4), c(5)))]), -17)

    def test_f1(self):
        a = [['Lewis', 'Max'], [[90, 92, 85], [91, 91, 86]]]; b = [['b', 'a'], [[10, 10, 10], [12, 8, 10]]]
        self.assertEqual((reference(_o.F1A, a), reference(_o.F1A, b)), ('Lewis', 'a'))
        self.assertEqual((reference(_o.F1B, a), reference(_o.F1B, b)), (['Lewis', 'Max'], ['a', 'b']))

    def test_flx(self):
        for args, want in [([[1, 2, 5], 11], 3), ([[2], 3], -1), ([[3, 7], 5], -1), ([[5, 5, 2], 9], 3), ([[1], 0], 0)]:
            self.assertEqual(reference(_o.FLX, args), want)

    def test_fal(self):
        c = ['INIT a 5', 'FUND 1 a 10 2', 'BALANCE 2 a', 'BALANCE 3 a', 'FUND 3 a 4 0', 'FUND 3 zz 1 0', 'BALANCE 3 a', 'BALANCE 3 zz']
        for uid in _o.FAL: self.assertEqual(reference(uid, [c]), [5, 15, 19, -1])
        self.assertEqual(reference(_o.FAL2, [['INIT a 5', 'FUND 0 a 10 3', 'WITHDRAW 1 a 6', 'BALANCE 1 a', 'WITHDRAW 3 a 6', 'BALANCE 3 a']]), [5, 9])
        c = ['INIT a 5', 'INIT b 0', 'TRANSFER 0 a b 5', 'TRANSFER 0 a b 1', 'TRANSFER 0 b b 1', 'TRANSFER 0 b zz 1', 'BALANCE 0 a', 'BALANCE 0 b']
        self.assertEqual(reference(_o.FAL3, [c]), [0, 5])
        c = ['INIT a 0', 'FUND 0 a 5 10', 'FUND 1 a 7 1', 'PENDING 1 a', 'CANCEL 2 a', 'PENDING 2 a', 'BALANCE 2 a', 'CANCEL 3 a', 'PENDING 3 a', 'BALANCE 20 a', 'PENDING 20 zz']
        self.assertEqual(reference(_o.FAL4, [c]), [12, 0, 7, 0, 7, -1])

    def test_gpu(self):
        self.assertEqual(reference(_o.GPU, [8, [3]]), [[3], 7])
        self.assertEqual(reference(_o.GPU, [5, [4, 0]]), [[0, 4], 9])
        self.assertEqual(reference(_o.GPU, [1, [0]]), [[0], 1])
        self.assertEqual(reference(_o.GPU, [1, []]), [[], 1])

    def test_bpp(self):
        self.assertEqual(reference(_o.BPP, [[2, 1, 3]]), '111')
        self.assertEqual(reference(_o.BPP, [[1, 3, 2]]), '101')
        self.assertEqual(reference(_o.BPP, [[4, 1, 3, 2, 5]]), '10111')

    def test_cfd(self):
        b = [[1, 2, 2], [2, 4, 6], [1, 5, 5]]
        self.assertEqual(reference(_o.CFD1, [[[1, 1, 3]], 5]), [4, 5])
        self.assertEqual(reference(_o.CFD1, [b, 8]), [1, 3, 7, 8])
        self.assertEqual(reference(_o.CFD2, [b, 8]), [[1, 1], [3, 3], [7, 8]])
        b = [[1, 1, 4], [1, 3, 6], [2, 2, 2]]
        self.assertEqual(reference(_o.CFD3, [b, 9, 1]), [[1, 1], [3, 9]])
        self.assertEqual(reference(_o.CFD3, [b, 9, 2]), [[7, 9]])

    def test_fcp(self):
        self.assertEqual(reference(_o.FCP, [[['JFK', 'ATL'], ['ATL', 'JFK'], ['JFK', 'SFO']]]), ['JFK', 'ATL', 'JFK', 'SFO'])
        self.assertEqual(reference(_o.FCP, [[['MUC', 'LHR'], ['JFK', 'MUC'], ['SFO', 'SJC'], ['LHR', 'SFO']]]), ['JFK', 'MUC', 'LHR', 'SFO', 'SJC'])
        self.assertEqual(reference(_o.FCP, [[['AAA', 'BBB'], ['AAA', 'CCC'], ['CCC', 'AAA']]]), ['AAA', 'CCC', 'AAA', 'BBB'])

    def test_eos(self):
        self.assertEqual(reference(_o.EOS, [[3, 1, 2]]), [2, 3, 1])
        self.assertEqual(reference(_o.EOS, [[1, 5, 2, 4, 3]]), [4, 3, 5, 2, 1])
        self.assertEqual(reference(_o.EOS, [[]]), [])

    def test_domain(self):
        c0 = {'operation': 'CONSTANT_NUMBER', 'value': 0}
        bad = [(_o.TKL, ops('TokenLimiter', [], [('consume', 'a', 1, 5), ('consume', 'a', 1, 4)])), (_o.TKL, ops('TokenLimiter', [], [('setPolicy', 'a', 1, 0, 1, 0)])),
               (_o.TKL, ops('TokenLimiter', [1], [])), (_o.WMS1, ops('WorkerManagementSystem', [], [('topNWorkers', 1, 'Dev')])),
               (_o.WMS1, ops('WorkerManagementSystem', [], [('registerWorker', 'A', 5), ('registerWorker', 'A', 5)])), (_o.WMS1, ops('WorkerManagementSystem', [], [('addWorker', 'A1', 'Dev', 1)])),
               (_o.WMS4, ops('WorkerManagementSystem', [], [('setDoublePaid', 5, 5)])), (_o.WMS3, ops('WorkerManagementSystem', [], [('calcSalary', 'A', 5, 4)])),
               (_o.TAS1, ops('TaskManager', [], [('addTask', 2, 'a', 1), ('addTask', 2, 'b', 1)])), (_o.TAS2, ops('TaskManager', [], [('addUser', 1, 'u', 1)])),
               (_o.TAS3, ops('TaskManager', [], [('assignTask', 5, 'taskId1', 'u', 5)])), (_o.TAS4, ops('TaskManager', [], [('getTask', 1, 'task-1')])),
               (_o.PAG, ops('Paginator', [5, 3, 6], [])), (_o.PAG, ops('Paginator', [5, 101, 1], [])), (_o.ENC, ops('Codec', [], [('decode', ['BP[1, 2]'])])),
               (_o.ENC, ops('Codec', [], [('decode', ['RLE[1, 0]'])])), (_o.ENC, ops('Codec', [], [('encode', [-1])])), (_o.EQF, ['']), (_o.EQF, ['aB']),
               (_o.ESL, [2, [1, 1]]), (_o.ESL, [3, [1, 0, 1]]), (_o.EJT, [{'operation': 'DIVIDE', 'inputs': [c0, c0]}]), (_o.EJT, [{'operation': 'ADD', 'inputs': [c0]}]),
               (_o.EJT, [{'operation': 'CONSTANT_NUMBER', 'value': 1.5}]), (_o.F1A, [['A', 'B'], [[1, 2], [1, 2, 3]]]), (_o.F1B, [['A', 'A'], [[1, 2], [1, 2]]]),
               (_o.F1A, [['A'], [[1]]]), (_o.FLX, [[0], 3]), (_o.FLX, [[], 3]), (_o.FAL1, [['BALANCE 1 a', 'INIT a 5']]), (_o.FAL1, [['INIT a 5', 'WITHDRAW 1 a 1']]),
               (_o.FAL2, [['INIT a 5', 'BALANCE 3 a', 'BALANCE 2 a']]), (_o.FAL4, [['INIT a 05']]), (_o.FAL3, [['INIT a 1', 'INIT a 2']]), (_o.GPU, [3, [1, 1]]),
               (_o.GPU, [0, []]), (_o.BPP, [[1, 3]]), (_o.BPP, [[]]), (_o.CFD1, [[[1, 3, 2]], 5]), (_o.CFD1, [[], 10**5 + 1]), (_o.CFD3, [[[1, 1, 1]], 5, 2]),
               (_o.FCP, [[]]), (_o.FCP, [[['AAA', 'BBB'], ['CCC', 'DDD']]]), (_o.FCP, [[['AAA', 'BBB'], ['AAA', 'CCC']]]), (_o.FCP, [[['aaa', 'BBB']]]), (_o.EOS, [[1, 1]])]
        for uid, args in bad:
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
        module = _load(f'gamma_h2h10b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
