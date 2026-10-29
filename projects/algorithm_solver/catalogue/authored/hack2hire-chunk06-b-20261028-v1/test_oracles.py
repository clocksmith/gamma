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


_o = _load('gamma_h2h06b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h06b_reference_test_cases', HERE / 'cases.py')
reference, validate_domain = _o.reference, _o.validate_domain
CONTRACTS = {row['uid']: row for row in json.loads((HERE / 'contracts.json').read_text())['problems']}


def stem(uid): return uid.split(':', 1)[1]


def exact(a, b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(map(exact, a, b))
    if type(a) is dict: return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    return a == b


class References(unittest.TestCase):
    """Hand-worked examples for each inferred spec (worked by the author, not taken from the source)."""
    def test_flat(self):
        t = {'tag': 'a', 'children': [{'tag': 'b', 'children': []}, {'tag': 'c', 'children': [{'tag': 'd', 'children': []}]}]}
        self.assertEqual(reference(_o.FLAT, [t]), ['<a>', '<b>', '</b>', '<c>', '<d>', '</d>', '</c>', '</a>'])

    def test_tasks(self):
        recs = ['9,subtask,a,b,Child', '1,task,a,Root', '3,subtask,b,c,Leaf', '2,task,z,Other', '4,subtask,a,d,Second']
        self.assertEqual(reference(_o.TASK1, [recs]), ['Root', '  Child', '    Leaf', '  Second', 'Other'])
        dirty = recs + ['5,task,a,Dup', '6,subtask,q,r,Orphan', '7,subtask,r,q,Cycle', 'x', '8,task,,Empty', '9,complete,c']
        self.assertEqual(reference(_o.TASK2, [dirty]), ['Root', '  Child', '    Leaf', '  Second', 'Other'])
        self.assertEqual(reference(_o.TASK3, [dirty]), ['1 Root', '  1.1 Child', '    1.1.1 Leaf', '  1.2 Second', '2 Other'])
        self.assertEqual(reference(_o.TASK4, [dirty]), ['1 [ ] Root', '  1.1 [x] Child', '    1.1.1 [x] Leaf', '  1.2 [ ] Second', '2 [ ] Other'])
        self.assertEqual(reference(_o.TASK4, [dirty + ['1,complete,d']])[:4:3], ['1 [x] Root', '  1.2 [x] Second'])

    def test_game(self):
        self.assertEqual(reference(_o.GAME, [[2, 2, 2], [1, -5, 9], 4]), 9)   # start 2 passes only the last layer
        self.assertEqual(reference(_o.GAME, [[3, 1], [-4, 2], 3]), 2)
        self.assertEqual(reference(_o.GAME, [[5], [7], 4]), 0)
        self.assertEqual(reference(_o.GAME, [[0, 0], [-1, -1], 0]), -1)

    def test_grid(self):
        self.assertEqual(reference(_o.GRID, [[[9, 9], [9, 0]]]), [[0, 1], [1, 0]])
        self.assertEqual(reference(_o.GRID, [[[9, -1, 9], [-1, 9, 9]]]), [[1, -1, 1], [-1, 1, 0]])
        self.assertEqual(reference(_o.GRID, [[[1, 9, 1]]]), [[1, 0, 1]])
        self.assertEqual(reference(_o.GRID, [[[1, 1]]]), [])
        self.assertEqual(reference(_o.GRID, [[[1, -1, 1]]]), [[1, -1, 1]])

    def test_mention(self):
        msgs = ['@id1,id2 hi @id1', 'appro@ch @id3', 'x@id1', '@all', 'hello']
        self.assertEqual(reference(_o.MENTION, [['id1', 'id2', 'id4'], msgs]), [2, 2, 1])

    def test_guess(self):
        self.assertEqual(reference(_o.GUESS, ['0123']), ['0000', '1111', '2222', '3333', '0444', '4144', '4424', '0123'])
        self.assertEqual(reference(_o.GUESS, ['3333']), ['0000', '1111', '2222', '3333'])
        self.assertEqual(reference(_o.GUESS, ['9999'])[-1], '9999')

    def test_guess_transcripts_identify_every_secret(self):
        for k in range(0, 10000, 37):
            s = '%04d' % k; log = reference(_o.GUESS, [s])
            self.assertEqual(log[-1], s); self.assertLessEqual(len(log), 19)
            answers = [sum(a == b for a, b in zip(g, s)) for g in log[:-1]]
            consistent = [c for c in ('%04d' % x for x in range(10000)) if all(sum(a == b for a, b in zip(g, c)) == r for g, r in zip(log[:-1], answers))]
            self.assertIn(s, consistent)

    def test_guess2(self):
        self.assertEqual(reference(_o.GUESS2, [0]), [0])
        self.assertEqual(reference(_o.GUESS2, [999]), [0, 999])
        self.assertEqual(reference(_o.GUESS2, [500]), [0, 999, 500])   # First; 999 is Hotter than 0, so C = 500..998 and min(C) = 500
        log = reference(_o.GUESS2, [700])
        self.assertEqual(log[:3], [0, 999, 500]); self.assertEqual(log[-1], 700)

    def test_delay(self):
        self.assertEqual(reference(_o.DELAY1, [1, 1]), [1, 2])
        self.assertEqual(reference(_o.DELAY1, [10, 3]), [3, 6])     # mids 5 (TOO_HIGH), 2 (TOO_LOW), 3
        self.assertEqual(reference(_o.DELAY2, [10, 3, 3]), [3, 12])
        self.assertEqual(reference(_o.DELAY2, [1, 20, 1]), [1, 21])

    def test_highlight(self):
        m = [['san francisco', 'city'], ['san', 'saint'], ['SAN', 'dup'], ['bay', 'water']]
        self.assertEqual(reference(_o.HIGHLIGHT, ['San Francisco bay, sandbox san? Bayou', m]),
                         '[city]{San Francisco} [water]{bay}, sandbox [saint]{san}? Bayou')

    def test_words(self):
        self.assertEqual(reference(_o.INT1, [0]), 'Zero')
        self.assertEqual(reference(_o.INT2, [115]), 'One Hundred Fifteen')
        self.assertEqual(reference(_o.INT2, [990]), 'Nine Hundred Ninety')
        self.assertEqual(reference(_o.INT3, [1000010]), 'One Million Ten')
        self.assertEqual(reference(_o.INT3, [2147483647]), 'Two Billion One Hundred Forty Seven Million Four Hundred Eighty Three Thousand Six Hundred Forty Seven')

    def test_job(self):
        jobs = [['J1', '0000', '10'], ['J2', '0005', '5'], ['J3', '0010', '1'], ['J4', '0010', '3'], ['J5', '0011', '1']]
        self.assertEqual(reference(_o.JOB, [jobs]), [['J1', 'M1'], ['J2', 'M2'], ['J3', 'M1'], ['J4', 'M2'], ['J5', 'M1']])

    def test_keys(self):
        kb = [['a', 'b', 'c'], ['d', 'e', 'a']]
        self.assertTrue(reference(_o.KEYS, [kb, 1, 'abe']))
        self.assertTrue(reference(_o.KEYS, [kb, 1, 'ad']))      # a at (0,0) is adjacent to d at (1,0)
        self.assertFalse(reference(_o.KEYS, [kb, 1, 'cd']))
        self.assertFalse(reference(_o.KEYS, [kb, 3, 'az']))

    def test_knight(self):
        self.assertEqual(reference(_o.KNIGHT, [1, 1]), ['1'])
        self.assertEqual(reference(_o.KNIGHT, [1, 6]), ['16'])
        self.assertEqual(reference(_o.KNIGHT, [1, 0]), ['160'])
        self.assertEqual(reference(_o.KNIGHT, [1, 3]), ['183'])
        self.assertEqual(reference(_o.KNIGHT, [5, 1]), [])
        self.assertEqual(reference(_o.KNIGHT, [1, 9]), ['16049', '16729', '18349'])

    def test_parity(self):
        self.assertEqual(reference(_o.PARITY, ['1234']), '1234')
        self.assertEqual(reference(_o.PARITY, ['65875']), '65875')
        self.assertEqual(reference(_o.PARITY, ['2468135']), '8642531')
        self.assertEqual(reference(_o.PARITY, ['247']), '427')
        self.assertEqual(reference(_o.PARITY, ['13579']), '97531')

    def test_latency(self):
        self.assertEqual(reference(_o.LATENCY, [[5, 10, 10, 19, 20, 100], 10, 3]), [1, 3, 2])

    def test_circ(self):
        self.assertEqual(reference(_o.CIRC, [[1, 1, 0, 1, 1], 0]), 4)
        self.assertEqual(reference(_o.CIRC, [[1, 0, 0, 1, 0], 1]), 3)
        self.assertEqual(reference(_o.CIRC, [[0, 0, 0], 2]), 2)

    def test_domain(self):
        for uid, args in [(_o.FLAT, [{'tag': 'A', 'children': []}]), (_o.FLAT, [{'tag': 'a'}]),
                          (_o.TASK1, [['1,subtask,x,y,Y']]), (_o.TASK1, [['1,task,a,A', '2,task,a,B']]), (_o.TASK2, [['1;task']]),
                          (_o.GAME, [[1], [1, 2], 0]), (_o.GAME, [[], [], 0]), (_o.GRID, [[[2]]]), (_o.GRID, [[[1], [1, 1]]]),
                          (_o.MENTION, [['id0'], []]), (_o.MENTION, [['id1'], ['@id01']]), (_o.MENTION, [['id1', 'id1'], []]),
                          (_o.GUESS, ['123']), (_o.GUESS2, [1000]), (_o.DELAY1, [5, 6]), (_o.DELAY2, [5, 0, 1]),
                          (_o.HIGHLIGHT, ['x', [['a  b', 'c']]]), (_o.HIGHLIGHT, ['x', [['a', '']]]), (_o.INT1, [10]), (_o.INT3, [2**31]),
                          (_o.JOB, [[['J1', '2400', '1']]]), (_o.JOB, [[['J1', '0001', '1'], ['J2', '0000', '1']]]), (_o.JOB, [[['J1', '0000', '0']]]),
                          (_o.KEYS, [[['ab']], 1, 'a']), (_o.KEYS, [[['a']], 1, '']), (_o.KNIGHT, [10, 1]), (_o.PARITY, ['']),
                          (_o.LATENCY, [[2, 1], 1, 1]), (_o.LATENCY, [[0], 1, 1]), (_o.CIRC, [[1, 2], 0]), (_o.CIRC, [[1], 2])]:
            with self.assertRaises(ValueError, msg=str(args)[:60]): validate_domain(uid, args)

    def test_generated_cases_domain_valid(self):
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True): validate_domain(uid, row['args'])

    def test_contract_layouts(self):
        self.assertEqual(set(CONTRACTS), set(_o.IDS))
        for uid, row in CONTRACTS.items():
            self.assertEqual(row['spec_basis'], 'inferred')
            self.assertNotIn('classname', row['inferred_interface'])
            self.assertEqual(row['oracle_constant'], next(k for k in dir(_o) if getattr(_o, k) == uid and k.isupper() and k != 'H'))


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
        module = _load(f'gamma_h2h06b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
