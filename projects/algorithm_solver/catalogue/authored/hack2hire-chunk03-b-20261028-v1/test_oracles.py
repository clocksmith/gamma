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


_o = _load('gamma_h2h03b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h03b_reference_test_cases', HERE / 'cases.py')
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
    def test_maxt(self):
        self.assertEqual(reference(_o.MAXT, [[2, 3], [1, 10], 10]), 3)
        self.assertEqual(reference(_o.MAXT, [[2, 3], [1, 10], 12]), 6)
        self.assertEqual(reference(_o.MAXT, [[4], [5], 14]), 12)

    def test_merge(self):
        self.assertEqual(reference(_o.MERGE, [[['0, 0', '5, -3'], ['2, 4', '5, 3', '9, 1']]]), ['0, 0', '2, 4', '5, 4', '9, 5'])
        self.assertEqual(reference(_o.MERGE, [[['1, 7', '1, 2'], []]]), ['1, 9'])

    def test_zero(self):
        self.assertEqual([reference(_o.ZERO, [n]) for n in range(1, 12)], [1, 2, 3, 3, 4, 4, 5, 4, 5, 5, 6])
        for n in range(1, 400): self.assertEqual(_o.ref_zero(n), _o.bfs_zero(n))

    def test_rotf(self):
        self.assertEqual([reference(_o.ROTF, [a]) for a in ([3, 1, 2], [2, 1, 3], [1, 3, 2], [1, 2, 3], [2, 1])], [1, 2, 2, 0, 1])
        self.assertEqual(reference(_o.ROTF, [[1, 3, 2, 4]]), -1)

    def test_rotation_distance_formula_small(self):
        """The analytic maximum rows use min(s, n - s + 2) for a left rotation by s; check it by BFS for small n."""
        for n in range(3, 9):
            base = list(range(n))
            for s in range(n): self.assertEqual(_o.ref_rotf(base[s:] + base[:s]), min(n - s, s + 2) if s else 0)

    def test_layer(self):
        self.assertEqual(reference(_o.LAYER, [[1, 2, 3], [3, 1, 2]]), 1)
        self.assertEqual(reference(_o.LAYER, [[3, 2, 1], [1, 2, 3]]), 2)
        self.assertEqual(reference(_o.LAYER, [[1, 2, 3, 4], [2, 1, 3, 4]]), 3)

    def test_balls(self):
        self.assertEqual(reference(_o.BALLS, [[[0, 0], [0, 5], [0, 10], [3, 5]], 5]), 1)
        self.assertEqual(reference(_o.BALLS, [[[0, 0], [0, 5], [0, 10], [3, 5]], 4]), 3)
        self.assertEqual(reference(_o.BALLS, [[[0, 0], [1, 1]], 10]), 2)

    def test_vconv(self):
        self.assertEqual(reference(_o.VCONV, [[1, 1, 0], 2]), 2)
        self.assertEqual(reference(_o.VCONV, [[1, 1], 2]), 3)
        self.assertEqual(reference(_o.VCONV, [[1, 1, 1, 1, 1, 1], 3]), 9)

    def test_chain(self):
        self.assertEqual(reference(_o.CHAIN, [['-> a', '-> b', '<- b', '-> b', '<- b', '<- a', '-> a']]), ['a'])
        self.assertEqual(reference(_o.CHAIN, [['-> a', '-> b', '<- b', '-> b']]), ['a', 'b'])
        self.assertEqual(reference(_o.CHAIN, [[]]), [])

    def test_music(self):
        t = ops('MusicPlayer', [], [('addSong', 'A'), ('addSong', 'B'), ('playSong', 1, 5), ('playSong', 2, 5), ('playSong', 1, 6),
                                     ('getLastThreeSongs', 5), ('removeSong', 2), ('getLastThreeSongs', 5), ('getAnalytics',), ('removeSong', 2)])
        self.assertEqual(reference(_o.MUSIC3, t), [None, 1, 2, None, None, None, [2, 1], True, [1], [['A', 2]], False])
        t = ops('MusicPlayer', [], [('addSong', 'X'), ('addSong', 'Y'), ('playSong', 2, 1), ('playSong', 2, 1), ('getAnalytics',)])
        self.assertEqual(reference(_o.MUSIC1, t), [None, 1, 2, None, None, [['Y', 1], ['X', 0]]])

    def test_ngram(self):
        self.assertEqual(reference(_o.NGRAM1, ['a b c', ['a b', 'b c']]), ['a b', 'c'])
        self.assertEqual(reference(_o.NGRAM1, ['a b c', ['b c']]), ['a', 'b c'])
        self.assertEqual(reference(_o.NGRAM2, ['a b c d', ['a b', 'a b c', 'c d']]), ['a b c', 'd'])

    def test_party(self):
        win = [['a', '0', '10'], ['b', '2', '4'], ['c', '3', '12'], ['d', '10', '11']]
        self.assertEqual(reference(_o.PARTY1, [win, [['a', 'x'], ['b', 'x'], ['c', 'y'], ['d', 'x']]]), [['x', '0', '11'], ['y', '3', '12']])
        self.assertEqual(reference(_o.PARTY2, [win, [['a', 'x'], ['b', 'x'], ['c', 'x'], ['d', 'x']]]), [['x', 3]])

    def test_paint_phone(self):
        self.assertEqual(reference(_o.PAINT, [3, 3]), 12)
        self.assertEqual(reference(_o.PAINT, [1, 2]), 0)
        self.assertEqual(reference(_o.PHONE, [['cat', 'act', 'bat', 'cats'], '228']), ['cat', 'act', 'bat'])
        self.assertEqual(reference(_o.PHONE, [['ab'], '10']), [])

    def test_poker(self):
        wheel = ['A of spades', '2 of hearts', '3 of clubs', '4 of hearts', '5 of diamonds']
        self.assertTrue(reference(_o.POKER1, [wheel]))
        self.assertFalse(reference(_o.POKER1, [['Q of clubs', 'K of clubs', 'A of clubs', '2 of clubs', '3 of diamonds']]))
        two_pair = [['2 of spades', '2 of hearts', '5 of clubs', '5 of hearts', '9 of diamonds'], ['2 of clubs', '2 of diamonds', '5 of spades', '5 of diamonds', '9 of hearts']]
        self.assertEqual(reference(_o.POKER2, [two_pair]), [0, 1])
        six_high = ['2 of clubs', '3 of diamonds', '4 of spades', '5 of clubs', '6 of clubs']
        self.assertEqual(reference(_o.POKER2, [[wheel, six_high]]), [1])

    def test_prodmm_purch(self):
        self.assertEqual(reference(_o.PRODMM, [['push', 'push', 'pop', 'push'], [5, 5, 5, -1]]), [25, 25, 25, -5])
        self.assertEqual(reference(_o.PURCH, [[1, 2, 3], [1, 2, 3, 1], [6, 5, 2, 0]]), [3, 2, 0, 0])

    def test_domain(self):
        for uid, args in [(_o.MAXT, [[1, 2], [1], 5]), (_o.MERGE, [[['2, 1', '1, 1']]]), (_o.MERGE, [[['1,1']]]), (_o.ZERO, [0]),
                          (_o.ROTF, [[1, 1]]), (_o.LAYER, [[1, 2], [1, 3]]), (_o.BALLS, [[[0, 0], [0, 0]], 1]), (_o.VCONV, [[1, 0], 3]),
                          (_o.CHAIN, [['-> a', '<- b']]), (_o.MUSIC1, ops('MusicPlayer', [], [('playSong', 1, 1)])),
                          (_o.MUSIC1, ops('MusicPlayer', [], [('removeSong', 1)])), (_o.NGRAM1, ['a  b', []]), (_o.NGRAM1, ['a b', ['a b c']]),
                          (_o.PARTY1, [[['p', '3', '3']], [['p', 'x']]]), (_o.PARTY1, [[['p', '1', '3']], [['q', 'x']]]), (_o.PAINT, [0, 1]),
                          (_o.PHONE, [['Ab'], '2']), (_o.POKER1, [['A of spades'] * 5]), (_o.POKER2, [[['1 of spades', '2 of hearts', '3 of clubs', '4 of hearts', '5 of diamonds']]]),
                          (_o.PRODMM, [['push', 'pop'], [1, 1]]), (_o.PRODMM, [['pop'], [1]]), (_o.PURCH, [[2, 1], [], []]), (_o.PURCH, [[1], [2], [1]])]:
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
        module = _load(f'gamma_h2h03b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
