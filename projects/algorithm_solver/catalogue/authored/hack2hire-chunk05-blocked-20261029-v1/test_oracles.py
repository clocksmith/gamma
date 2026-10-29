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


_o = _load('gamma_h2h05x_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h05x_reference_test_cases', HERE / 'cases.py')
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
    def check(self, uid, pairs):
        for args, want in pairs:
            got = reference(uid, args)
            self.assertTrue(exact(got, want), f'{uid} {str(args)[:200]} -> {got!r}, want {want!r}')

    def test_css(self):
        # [3,1,2,3,3]: only (0, 3), whose middle 1 + 2 equals both ends
        self.check(_o.CSS, [([[1, 1, 1]], 1), ([[2, 1, 1, 2]], 1), ([[3, 1, 2, 3, 3]], 1), ([[1, 2]], 0), ([[5]], 0), ([[1, 1, 1, 1]], 2)])

    def test_dasher(self):
        two = [['09:00', 'a', 'accepted'], ['09:10', 'b', 'accepted'], ['09:30', 'a', 'delivered'], ['09:40', 'b', 'delivered']]
        self.check(_o.DP1, [([two], 1800), ([[]], 0), ([[['10:00', 'x', 'accepted'], ['10:00', 'x', 'delivered']]], 0)])
        # 10 normal + 10 peak minutes = 30 weighted minutes; 1 peak + 180 normal + 1 peak = 184
        self.check(_o.DP2, [([[['10:50', 'a', 'accepted'], ['11:10', 'a', 'delivered']]], 900), ([[['13:59', 'a', 'accepted'], ['17:01', 'a', 'delivered']]], 5520),
                            ([two], 1800)])
        cancel = [['11:00', 'a', 'accepted'], ['11:05', 'b', 'accepted'], ['11:20', 'a', 'cancelled'], ['11:30', 'b', 'delivered']]
        self.check(_o.DP3, [([cancel], 1500), ([[['08:00', 'a', 'accepted'], ['08:30', 'a', 'delivered']]], 900)])

    def test_als(self):
        t = ops('ALSWrapper', [], [('record', 1, 50, 10), ('record', 0, 999, 20), ('getLatestLux',), ('record', 1, 30, 5), ('getLatestLux',),
                                   ('getAverageLux', 0, 10), ('getAverageLux', 11, 100), ('record', 1, 7, 10), ('getLatestLux',), ('getAverageLux', 10, 10)])
        self.check(_o.ALS, [(t, [None, None, None, 50, None, 50, 40, -1, None, 7, 28]), (ops('ALSWrapper', [], [('getLatestLux',), ('getAverageLux', 0, 0)]), [None, -1, -1])])

    def test_card_games(self):
        deck = [51, 0] + list(range(1, 51))
        t = ops('CardGame', [deck], [('playRound',), ('getScore', 'A'), ('getWinner',)] + [('playRound',)] * 26 + [('getScore', 'B'), ('getWinner',)])
        self.check(_o.CG1, [(t, [None, 'A', 1, ''] + ['B'] * 25 + ['', 25, 'B'])])
        deck = [12, 0, 13, 26] + [c for c in range(52) if c not in (0, 12, 13, 26)]
        t = ops('CardGame', [deck], [('playRound',), ('getScore', 'A'), ('getScore', 'B'), ('playRound',), ('getWinner',)])
        self.check(_o.CG2, [(t, [None, 'A', 14, 0, 'TIE', ''])])

    def test_dcb(self):
        t = ops('DualCircuitBreaker', [2, 5], [('request', 0, False, True), ('request', 1, False, True), ('request', 2, True, False), ('request', 3, True, False),
                                               ('request', 4, True, True), ('request', 6, False, True), ('request', 8, True, True), ('request', 11, True, True),
                                               ('request', 11, False, False)])
        self.check(_o.DCB, [(t, [None, 'SECONDARY', 'SECONDARY', 'FAILED', 'FAILED', 'BLOCKED', 'FAILED', 'SECONDARY', 'PRIMARY', 'FAILED'])])

    def test_daw(self):
        subs = [['@', 'a'], ['$', 's'], ['3', 'e'], ['1', 'l'], ['1', 'i']]
        self.check(_o.DAW, [([['ass', 'hell'], subs, '@$$ is h3ll and he11o sh1t a$s'], [0, 2, 6]), ([['ab'], [], 'a@ ab ab'], [1, 2]), ([['ab'], [], '?b'], []),
                            ([['shit'], subs, 'sh1t'], [0])])

    def test_domain(self):
        deck = list(range(52))
        bad = [(_o.CSS, [[]]), (_o.CSS, [[0]]), (_o.CSS, [[10**9 + 1]]), (_o.CSS, [[True]]),
               (_o.DP1, [[['9:00', 'a', 'accepted']]]), (_o.DP1, [[['09:00', 'a', 'accepted']]]), (_o.DP1, [[['09:00', 'a', 'delivered']]]),
               (_o.DP1, [[['09:00', 'a', 'accepted'], ['08:00', 'a', 'delivered']]]), (_o.DP1, [[['09:00', 'a', 'accepted'], ['09:01', 'a', 'cancelled']]]),
               (_o.DP2, [[['24:00', 'a', 'accepted'], ['24:00', 'a', 'delivered']]]), (_o.DP3, [[['09:00', 'a', 'accepted'], ['09:00', 'a', 'accepted']]]),
               (_o.DP3, [[['09:00', 'a-b', 'accepted'], ['09:01', 'a-b', 'delivered']]]),
               (_o.ALS, ops('ALSWrapper', [], [('record', 2, 1, 1)])), (_o.ALS, ops('ALSWrapper', [], [('getAverageLux', 5, 4)])),
               (_o.ALS, ops('ALSWrapper', [], [('record', 1, 1, 10**6 + 1)])), (_o.ALS, ops('ALSWrapper', [1], [])),
               (_o.CG1, ops('CardGame', [deck[:-1]], [])), (_o.CG1, ops('CardGame', [deck[:-1] + [0]], [])), (_o.CG2, ops('CardGame', [deck], [('getScore', 'C')])),
               (_o.CG2, ops('CardGame', [deck], [('draw',)])), (_o.DCB, ops('DualCircuitBreaker', [0, 1], [])), (_o.DCB, ops('DualCircuitBreaker', [1, 0], [])),
               (_o.DCB, ops('DualCircuitBreaker', [1, 1], [('request', 5, True, True), ('request', 4, True, True)])),
               (_o.DCB, ops('DualCircuitBreaker', [1, 1], [('request', 5, 1, True)])),
               (_o.DAW, [[], [], 'a']), (_o.DAW, [['A'], [], 'a']), (_o.DAW, [['a'], [['a', 'b']], 'a']), (_o.DAW, [['a'], [['1', 'a'], ['1', 'b'], ['1', 'c'], ['1', 'd']], 'a']),
               (_o.DAW, [['a'], [], 'a  b']), (_o.DAW, [['a'], [], ' a']), (_o.DAW, [['a'], [], '']), (_o.DAW, [['a'], [], 'aB']), (_o.DAW, [['a' * 21], [], 'a'])]
        for uid, args in bad:
            with self.assertRaises(ValueError, msg=str(args)[:80]): validate_domain(uid, args)
        validate_domain(_o.DP1, [[]])
        validate_domain(_o.DAW, [['a'], [['1', 'a'], ['1', 'a']], 'a 1'])

    def test_generated_cases_domain_valid_and_shallow(self):
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True):
                validate_domain(uid, row['args'])
                self.assertLessEqual(depth(row['args']), 200)

    def test_contract_layouts_match_classes(self):
        self.assertEqual(set(CONTRACTS), set(_o.IDS))
        for uid, row in CONTRACTS.items():
            self.assertEqual(row['spec_basis'], 'inferred')
            self.assertEqual(row['prior_blocker']['cohort'], 'hack2hire-chunk05-v1')
            self.assertEqual(uid in _o.CLASSES, 'classname' in row['inferred_interface'])
            if uid in _o.CLASSES:
                name, ctor, methods, voids = _o.CLASSES[uid]
                iface = row['inferred_interface']
                self.assertEqual(iface['classname'], name)
                self.assertEqual(len(iface['constructor']['params']), ctor)
                self.assertEqual({m['name']: len(m['params']) for m in iface['methods']}, methods)
                self.assertEqual({m['name'] for m in iface['methods'] if m['return']['type'] == 'void'}, set(voids))

    def test_prior_blockers_cover_exactly_these_variants(self):
        blocked = json.loads((HERE.parent / 'hack2hire-chunk05-v1' / 'blockers.json').read_text())['variants']
        self.assertEqual({b['id'] for b in blocked}, set(_o.IDS))
        for b in blocked: self.assertEqual(CONTRACTS[b['id']]['prior_blocker']['reason'], b['reason'])
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
        module = _load(f'gamma_h2h05x_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
