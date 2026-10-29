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


_o = _load('gamma_h2h09a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h09a_reference_test_cases', HERE / 'cases.py')
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
    def test_zbp(self):
        self.assertEqual(reference(_o.ZBP, [[2, 0, 1]]), True)
        self.assertEqual(reference(_o.ZBP, [[1, 2, 0, 2]]), False)
        self.assertEqual(reference(_o.ZBP, [[3, 0, 1]]), False)
        self.assertEqual(reference(_o.ZBP, [[]]), True)

    def test_vps(self):
        self.assertEqual(reference(_o.VPS, [3, [2, 3, 1, 2, 3, 1, 2]]), True)
        self.assertEqual(reference(_o.VPS, [3, [1, 2, 3, 1, 3]]), True)   # cut after the first three plays
        self.assertEqual(reference(_o.VPS, [3, [1, 2, 1, 3]]), True)      # offset 1: [1], [2, 1, 3]
        self.assertEqual(reference(_o.VPS, [2, [1, 1, 1]]), False)
        self.assertEqual(reference(_o.VPS, [1, []]), True)

    def test_wak(self):
        self.assertEqual(reference(_o.WAK, [[1, 2, 3, 4], 2, 1]), [1, 2, 3])
        self.assertEqual(reference(_o.WAK, [[-3, -2], 2, 1]), [-3])
        self.assertEqual(reference(_o.WAK, [[4, 4, 1], 3, 2]), [1])
        self.assertEqual(reference(_o.WAK, [[-1, -2], 2, 0]), [-2])  # floor of -1.5
        self.assertEqual(reference(_o.WAK, [[7, 7, 7, 1], 4, 3]), [1])

    def test_tok(self):
        s = ['u,100,200,basic', 'u,0,50,pro', 'a,1,1,basic', 'u,30,0,basic']
        self.assertEqual(reference(_o.TOK1, [s, ['basic,1,2', 'pro,3,4']]), [['a', 3], ['u', 730]])
        self.assertEqual(reference(_o.TOK2, [s, ['basic,1,2,10,150', 'pro,3,4,0,0']]), [['a', 10], ['u', 540]])
        self.assertEqual(reference(_o.TOK3, [s, ['basic,1,2,10,150,250', 'pro,3,4,0,0,1000000']]), [['a', 10], ['u', 460]])
        self.assertEqual(reference(_o.TOK1, [[], ['p,1,1']]), [])

    def test_api(self):
        t = ops('APIMatchingSystem', [], [('registerPath', '/a', 'A'), ('registerPath', '/a/b/c', 'C'), ('matchPath', '/a/b'), ('matchPath', '/a/b/c/d'), ('matchPath', '/ab'),
                                          ('registerPath', '/', 'R'), ('matchPath', '/ab'), ('registerPath', '/a', 'A2'), ('matchPath', '/a/x')])
        self.assertEqual(reference(_o.API, t), [None, None, None, 'A', 'C', '', None, 'R', None, 'A2'])

    def test_ard(self):
        self.assertEqual(reference(_o.ARD1, [['A', 'B', 'C'], ['a@x.com', 'b@x.com', 'a@x.com'], ['1', '1', '2']]), [1, 2])
        self.assertEqual(reference(_o.ARD1, [['A', 'B', 'C'], ['a@x.com', 'b@x.com', 'b@x.com'], ['1', '1', '2']]), [1])  # B failed, so b@x.com stays free
        self.assertEqual(reference(_o.ARD1, [['A', 'B'], ['a@x.com', 'A@x.com'], ['1', '2']]), [])
        self.assertEqual(reference(_o.ARD2, [['A', 'B', 'C', 'D'], ['A.b+1@x.com', 'ab@X.com', 'c@x.com', 'c@y.com'], ['(555) 1', '7', '5551', '8']]), [1, 2])

    def test_drl(self):
        self.assertEqual(reference(_o.DRL, ops('DomainRateLimiter', [1, 1], [('allowRequest', 'a')] * 3)), [None, True, True, True])
        t = ops('DomainRateLimiter', [2, 3], [('allowRequest', 'a'), ('allowRequest', 'a'), ('allowRequest', 'a'), ('allowRequest', 'b'), ('allowRequest', 'a'), ('allowRequest', 'a')])
        self.assertEqual(reference(_o.DRL, t), [None, True, True, False, True, True, True])

    def test_ast(self):
        self.assertEqual(reference(_o.AST, [[2, 3], [3, -2]]), [])
        self.assertEqual(reference(_o.AST, [[4, 1, 5], [1, 2, -1]]), [[5, -1]])
        self.assertEqual(reference(_o.AST, [[1, 1, 10], [5, 5, -1]]), [[10, -1]])
        self.assertEqual(reference(_o.AST, [[1, 1], [-1, 1]]), [[1, -1], [1, 1]])

    def test_acp(self):
        w = ['eat', 'tea', 'tan', 'ate', 'nat', 'bat']
        self.assertEqual(reference(_o.ACP, [w, ['ate', 'nat', 'cab']]), [['eat', 'tea', 'ate'], ['tan', 'nat'], []])
        self.assertEqual(reference(_o.ACP, [['aa', 'a', 'aa'], ['aa']]), [['aa', 'aa']])

    def test_bpg(self):
        self.assertEqual(reference(_o.BPG, [[3, -10, 4]]), -6)
        self.assertEqual(reference(_o.BPG, [[10, -1, -1, 10]]), 9)
        self.assertEqual(reference(_o.BPG, [[1, 2]]), 3)
        self.assertEqual(reference(_o.BPG, [[-5]]), -5)
        self.assertEqual(reference(_o.BPG, [[]]), 0)
        for v, n in ((1, 7), (-1, 6), (3, 5)):  # the equal-value closed recurrence used by the maximum rows
            self.assertEqual(reference(_o.BPG, [[v] * n]), _c._game_line(v, n))

    def test_bmd(self):
        p = [['Ann', 'US', ['2026-01-02', '2026-01-01']], ['Bob', 'US', ['2026-01-02']], ['Cy', 'Peru', ['2026-03-01', '2026-02-01']], ['Di', 'US', ['2026-01-01']]]
        self.assertEqual(reference(_o.BMD, [p]), [['Peru', '2026-02-01', ['Cy']], ['US', '2026-01-01', ['Ann', 'Di']]])
        self.assertEqual(reference(_o.BMD, [[['Ann', 'US', []]]]), [])

    def test_bub(self):
        self.assertEqual(reference(_o.BUB, [[[1, 1, 1]]]), [[0, 0, 0]])
        self.assertEqual(reference(_o.BUB, [[[1, 1], [1, 2]]]), [[0, 0], [0, 2]])
        self.assertEqual(reference(_o.BUB, [[[2, 1, 2], [1, 1, 1], [2, 1, 2]]]), [[0, 0, 0], [2, 0, 2], [2, 0, 2]])
        self.assertEqual(reference(_o.BUB, [[[3, 1], [2, 1], [2, 1], [2, 3]]]), [[0, 0], [0, 0], [0, 0], [3, 3]])

    def test_bsn(self):
        self.assertEqual(reference(_o.BSN1, [[3, 0, 1]]), '103')
        self.assertEqual(reference(_o.BSN1, [[0, 0, 2, 1]]), '1002')
        self.assertEqual(reference(_o.BSN1, [[0, 0]]), '0')
        self.assertEqual(reference(_o.BSN2, [[0, 2, 21]]), '2021')  # the comparator-smallest non-zero (21) is not the best first element
        self.assertEqual(reference(_o.BSN2, [[0, 10, 2]]), '1002')
        self.assertEqual(reference(_o.BSN2, [[3, 30, 34, 5, 9]]), '3033459')
        self.assertEqual(reference(_o.BSN2, [[10, 2]]), '102')

    def test_spk(self):
        self.assertEqual(reference(_o.SPK, [[4, 5, 7, 6, 3, 2]]), 6)
        self.assertEqual(reference(_o.SPK, [[1, 1, 5, 4, 3]]), 5)
        self.assertEqual(reference(_o.SPK, [[2, 2, 2, 1, 1, 1]]), 3)
        self.assertEqual(reference(_o.SPK, [[1, 1]]), 1)

    def test_cpu(self):
        self.assertEqual(reference(_o.CPU, [[['a', 'enter', '0'], ['b', 'enter', '2'], ['b', 'exit', '5'], ['a', 'exit', '6']]]), [['a', 3], ['b', 3]])
        logs = [['a', 'enter', '1'], ['a', 'enter', '3'], ['a', 'exit', '4'], ['a', 'exit', '4'], ['b', 'enter', '7'], ['b', 'exit', '7']]
        self.assertEqual(reference(_o.CPU, [logs]), [['a', 3], ['b', 0]])

    def test_cae(self):
        self.assertEqual(reference(_o.CAE, ['Hello, World!', 13]), 'Uryyb, Jbeyq!')
        self.assertEqual(reference(_o.CAE, ['Zebra-123', -1]), 'Ydaqz-123')
        self.assertEqual(reference(_o.CAE, ['xyz', 3]), 'abc')
        self.assertEqual(reference(_o.CAE, ['aA', -27]), 'zZ')

    def test_domain(self):
        for uid, args in [(_o.ZBP, [[True]]), (_o.ZBP, [[10**9 + 1]]), (_o.VPS, [2, [3]]), (_o.VPS, [0, []]), (_o.WAK, [[1, 2], 3, 0]), (_o.WAK, [[1, 2], 2, 2]), (_o.WAK, [[], 1, 0]),
                          (_o.TOK1, [['u,1,1,zz'], ['p,1,1']]), (_o.TOK1, [['u,01,1,p'], ['p,1,1']]), (_o.TOK2, [[], ['p,1,1']]), (_o.TOK3, [[], ['p,1,1,1,1,1', 'p,1,1,1,1,1']]),
                          (_o.TOK1, [['U,1,1,p'], ['p,1,1']]), (_o.API, ops('APIMatchingSystem', [], [('matchPath', '/a/')])), (_o.API, ops('APIMatchingSystem', [], [('registerPath', 'a', 'h')])),
                          (_o.API, ops('APIMatchingSystem', [1], [])), (_o.ARD1, [['a'], ['a@x.com'], []]), (_o.ARD1, [['a'], ['a@X.com'], ['1']]), (_o.ARD2, [['a'], ['a@x.com'], ['()']]),
                          (_o.DRL, ops('DomainRateLimiter', [0, 1], [])), (_o.DRL, ops('DomainRateLimiter', [1, 1], [('allowRequest', 'A')])), (_o.AST, [[1], [0]]), (_o.AST, [[0], [1]]),
                          (_o.AST, [[1, 2], [1]]), (_o.ACP, [['A'], []]), (_o.BPG, [[0] * 501]), (_o.BMD, [[['a', 'US', ['2026-13-01']]]]), (_o.BMD, [[['a', 'US']]]),
                          (_o.BUB, [[[1, 0]]]), (_o.BUB, [[[1], [1, 1]]]), (_o.BUB, [[]]), (_o.BSN1, [[]]), (_o.BSN1, [[10]]), (_o.BSN2, [[-1]]),
                          (_o.SPK, [[1.5]]), (_o.CPU, [[['a', 'enter', '1']]]), (_o.CPU, [[['a', 'enter', '2'], ['a', 'exit', '1']]]), (_o.CPU, [[['a', 'enter', '0'], ['b', 'exit', '1']]]),
                          (_o.CAE, ['\n', 1]), (_o.CAE, ['a', 10**9 + 1])]:
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
        module = _load(f'gamma_h2h09a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
