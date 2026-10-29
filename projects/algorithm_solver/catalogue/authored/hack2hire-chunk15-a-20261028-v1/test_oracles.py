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


_o = _load('gamma_h2h15a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h15a_reference_test_cases', HERE / 'cases.py')
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
            self.assertTrue(exact(got, want), f'{uid} {args} -> {got!r}, want {want!r}')

    def test_blp(self):
        self.check(_o.BLP, [([['ab', 'ba']], 4), ([['ab', 'ab']], 0), ([['aa', 'aa', 'aa']], 6), ([['abc', 'cba', 'bab', 'xyx']], 9), ([['lc', 'cl', 'gg']], 6)])

    def test_bfo(self):
        P = [['apple', 10], ['pear', 7]]
        self.check(_o.BFO, [([[], P, []], 0), ([[['apple', '3', '0'], ['apple', '2', '600000']], P, [[5, 20]]], 40),
                            ([[['apple', '3', '0'], ['apple', '2', '600001']], P, [[5, 20]]], 50),
                            ([[['apple', '1', '0'], ['pear', '9', '1'], ['apple', '1', '1200000'], ['apple', '1', '600000']], P, [[2, 10], [3, 50]]], 78),
                            ([[['pear', '7', '5']], P, [[2, 100]]], 49), ([[['pear', '1', '5'], ['pear', '2', '5']], P, [[2, 33]]], 14)])

    def test_ccp(self):
        roads = [['A', 'B', 5], ['B', 'C', 5], ['X', 'C', 3], ['C', 'Campground', 4]]
        self.check(_o.CCP, [([roads, [['amy', 'B'], ['bo', 'C'], ['cy', 'X'], ['di', 'A']], 'A', 'X'], [['di', 'amy'], ['cy', 'bo']]),
                            ([roads, [['amy', 'C'], ['zed', 'C']], 'X', 'B'], [['amy', 'zed'], []]), ([[['P', 'Campground', 1], ['Q', 'P', 1]], [['f', 'P']], 'P', 'Q'], [['f'], []])])

    def test_cfs(self):
        a = [[0, 30], [5, 10], [10, 20], [15, 25]]
        self.check(_o.CFS1, [([a], [1, 2, 2, 3]), ([[]], []), ([[[1, 2], [1, 2], [2, 3]]], [1, 2, 1]), ([[[5, 6], [0, 10], [0, 5]]], [2, 1, 2])])
        self.check(_o.CFS2, [([a, 1], [1, -1, -1, -1]), ([a, 2], [1, 2, 2, -1]), ([[[5, 6], [0, 10], [0, 5]], 1], [-1, 1, -1])])

    def test_cpp(self):
        self.check(_o.CPP, [([[1]], [True]), ([[1, 3, 2]], [True, False, True]), ([[4, 1, 3, 2]], [True, False, True, True]), ([[2, 4, 1, 3, 5]], [True, False, False, True, True])])

    def test_cpd(self):
        self.check(_o.CPD, [([[[0, 0], [3, 4]]], 5.0), ([[[0, 0], [1, 1], [5, 5], [-1, 2]]], 2 ** 0.5), ([[[1, 1], [1, 2], [1, 3]]], 1.0)])

    def test_cns(self):
        self.check(_o.CNS, [([[[1, 2, 3], [4]]], [10, 2, 3]), ([[[1, None, 2], []]], [3, None, 2]), ([[[]]], []), ([[[5, 1], [1, 2], [0, None, 3]]], [9, 3, 3]),
                            ([[[1, 2, 3, 4], [10]]], [16, 6, 3, 4])])

    def test_cds(self):
        self.check(_o.CDS, [([[1], 1], 1), ([[1], 5], 5), ([[2, 3], 5], 5), ([[2], 3], 5), ([[5, 5], 4], 6), ([[3, 1, 2], 10], 5)])

    def test_cic(self):
        t = ops('IntervalCounter', [[[1, 4], [2, 6], [8, 9], [2, 2]]], [('count', x) for x in (0, 1, 2, 3, 6, 7, 8, 10)])
        self.check(_o.CIC, [(t, [None, 0, 1, 3, 2, 1, 0, 1, 0])])

    def test_cvb(self):
        self.check(_o.CVB, [([[1, 1, 3], '???0111'], 1), ([[], '0?0'], 1), ([[], '1'], 0), ([[2], '??'], 1), ([[1, 1], '?????'], 6), ([[3, 2, 1], '?111????????'], 10)])

    def test_com(self):
        self.check(_o.COM, [([[5], [10], [['buy', 10], ['sell', 4], ['buy', 9]]], [10, 5, -1]),
                            ([[3, 8], [9, 12], [['sell', 2], ['buy', 15], ['buy', 15], ['buy', 15]]], [8, 9, 12, -1]), ([[], [7, 7], [['buy', 7], ['buy', 6], ['sell', 6]]], [7, -1, 6])])

    def test_dws(self):
        d = [{'tags': ['web'], 'timestamp': 1, 'value': 5}, {'tags': ['db'], 'timestamp': 2, 'value': 7}, {'tags': ['web', 'db'], 'timestamp': 4, 'value': -2},
             {'tags': ['web'], 'timestamp': 6, 'value': 10}]
        self.check(_o.DWS1, [([d, 'web', 3], [5, -2, 8]), ([d, 'db', 1], [7, -2]), ([d, 'web', 100], [5, 3, 13]), ([d, 'x', 2], [])])
        self.check(_o.DWS2, [([d, 'web', 3], [5, 3, 13]), ([d, 'web', 2], [5, 3, 8]), ([d, 'db', 1], [7, -2])])

    def test_dkb(self):
        self.check(_o.DKB, [([[2, 1, 6, 4], 1], 1), ([[1, 1, 1], 1], 0), ([[1, 2, 3], 3], 0), ([[1, 2], 1], -1), ([[3, 1, 2, 2, 1], 2], -1)])

    def test_dvc(self):
        v = ['1.0.0', '1.2.0', '1.10.0', '2.0.1', '10.0.0']
        self.check(_o.DVC1, [([[], []], None), ([v, [False, False, True, True, True]], '1.10.0'), ([v, [False] * 5], None), ([v, [True] * 5], '1.0.0')])
        self.check(_o.DVC2, [([v[::-1], [True, True, True, False, False]], '1.10.0'), ([['9.0.0', '10.0.0', '1.0.0'], [True, True, False]], '9.0.0')])

    def test_das(self):
        t = ops('ArticleSystem', [], [('addArticle', 'alpha'), ('addArticle', 'beta'), ('upvoteArticle', 1, 7), ('downvoteArticle', 2, 7), ('getTopArticles', 2),
                                      ('downvoteArticle', 1, 7), ('upvoteArticle', 2, 7), ('getRecentFlips', 7, 5), ('getTopArticles', 5), ('upvoteArticle', 2, 7),
                                      ('upvoteArticle', 1, 7), ('getRecentFlips', 7, 1), ('getRecentFlips', 8, 3)])
        self.check(_o.DAS, [(t, [None, 1, 2, None, None, ['alpha', 'beta'], None, None, ['beta', 'alpha'], ['beta', 'alpha'], None, None, ['alpha'], []])])

    def test_dcf(self):
        t = ops('ConnectFourBoard', [2, 2], [('drop', 'R', 0), ('drop', 'Y', 0), ('drop', 'R', 0), ('drop', 'B', 1)])
        self.check(_o.DCF1, [(t, [None, [['0', '0'], ['R', '0']], [['Y', '0'], ['R', '0']], [['Y', '0'], ['R', '0']], [['Y', '0'], ['R', 'B']]])])
        row = ops('ConnectFourBoard', [1, 5], [('drop', 'Y', 4), ('getWinner',)] + [('drop', 'R', c) for c in range(4)] + [('getWinner',)])
        self.check(_o.DCF2, [(row, [None, [['0', '0', '0', '0', 'Y']], '0', [['R', '0', '0', '0', 'Y']], [['R', 'R', '0', '0', 'Y']], [['R', 'R', 'R', '0', 'Y']],
                                    [['R', 'R', 'R', 'R', 'Y']], 'R'])])
        diag = ops('ConnectFourBoard', [4, 4], [('drop', 'Y', 1), ('drop', 'Y', 2), ('drop', 'Y', 2), ('drop', 'Y', 3), ('drop', 'Y', 3), ('drop', 'Y', 3)]
                   + [('drop', 'R', c) for c in range(4)] + [('getWinner',)])
        self.assertEqual(reference(_o.DCF2, diag)[-1], 'R')
        vert = ops('ConnectFourBoard', [4, 1], [('drop', 'B', 0)] * 4 + [('getWinner',), ('drop', 'R', 0), ('getWinner',)])
        self.assertEqual(reference(_o.DCF2, vert)[-3:], ['B', [['B'], ['B'], ['B'], ['B']], 'B'])

    def test_domain(self):
        for uid, args in [(_o.BLP, [['ab', 'a']]), (_o.BLP, [[]]), (_o.BLP, [['Ab']]),
                          (_o.BFO, [[['apple', '1', '0']], [], []]), (_o.BFO, [[['apple', '01', '0']], [['apple', 1]], []]), (_o.BFO, [[], [], [[5, 1], [5, 2]]]),
                          (_o.BFO, [[], [['a', 1], ['a', 2]], []]), (_o.BFO, [[['a', '1', '10000000000001']], [['a', 1]], []]),
                          (_o.CCP, [[['A', 'B', 1]], [], 'A', 'B']), (_o.CCP, [[['A', 'B', 1], ['B', 'A', 1]], [], 'A', 'B']),
                          (_o.CCP, [[['A', 'Campground', 1], ['B', 'Campground', 1]], [], 'A', 'A']), (_o.CCP, [[['A', 'Campground', 1], ['B', 'Campground', 1], ['C', 'Campground', 1]], [['f', 'C']], 'A', 'B']),
                          (_o.CCP, [[['A', 'Campground', 1], ['B', 'Campground', 1]], [['f', 'A'], ['f', 'B']], 'A', 'B']),
                          (_o.CFS1, [[[3, 3]]]), (_o.CFS2, [[[1, 2]], 0]), (_o.CPP, [[1, 3]]), (_o.CPP, [[]]), (_o.CPD, [[[0, 0]]]), (_o.CPD, [[[0, 0], [0, 0]]]),
                          (_o.CPD, [[[0, 0], [10**7 + 1, 0]]]), (_o.CNS, [[]]), (_o.CNS, [[[None]]]), (_o.CNS, [[[1, None]]]), (_o.CNS, [[[1, None, None, 2]]]),
                          (_o.CDS, [[0], 1]), (_o.CDS, [[], 1]), (_o.CDS, [[1], 0]), (_o.CVB, [[0], '1']), (_o.CVB, [[], '']), (_o.CVB, [[], '2']),
                          (_o.COM, [[], [], [['hold', 1]]]), (_o.COM, [[0], [], []]), (_o.DWS1, [[{'tags': [], 'timestamp': 2, 'value': 1}, {'tags': [], 'timestamp': 2, 'value': 1}], 'a', 1]),
                          (_o.DWS1, [[{'tags': ['a', 'a'], 'timestamp': 2, 'value': 1}], 'a', 1]), (_o.DWS2, [[], 'a', 0]), (_o.DWS2, [[{'tags': [], 'timestamp': 2}], 'a', 1]),
                          (_o.DKB, [[1], 2]), (_o.DKB, [[], 1]), (_o.DVC1, [['1.0.0', '0.9.0'], [False, True]]), (_o.DVC1, [['1.0.0'], [1]]), (_o.DVC1, [['01.0.0'], [True]]),
                          (_o.DVC2, [['2.0.0', '1.0.0'], [False, True]]), (_o.DVC2, [['1.0.0', '1.0.0'], [True, True]]),
                          (_o.DAS, ops('ArticleSystem', [], [('upvoteArticle', 1, 1)])), (_o.DAS, ops('ArticleSystem', [], [('getTopArticles', 0)])),
                          (_o.CIC, ops('IntervalCounter', [[[2, 1]]], [])), (_o.CIC, ops('IntervalCounter', [[]], [('add', 1)])),
                          (_o.DCF1, ops('ConnectFourBoard', [0, 3], [])), (_o.DCF1, ops('ConnectFourBoard', [2, 2], [('drop', 'R', 2)])), (_o.DCF1, ops('ConnectFourBoard', [2, 2], [('getWinner',)])),
                          (_o.DCF2, ops('ConnectFourBoard', [2, 2], [('drop', 'red', 0)])), (_o.DCF2, ops('ConnectFourBoard', [50, 50], [('drop', 'R', 0)] * 401))]:
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


def js_agrees(uid, got, expected):
    """JavaScript has no integral-float tag: FLOATS results compare by numeric value; everything else exactly."""
    if uid in _o.FLOATS: return type(got) in (int, float) and type(got) is not bool and got == expected
    return exact(got, expected)


class Candidates(unittest.TestCase):
    """Author-local self-check of own candidates against own generated cases; not isolated qualification."""
    def run_python(self, uid, rows):
        path = HERE / 'python' / f'{stem(uid)}.py'
        if not path.exists(): self.skipTest('candidate absent')
        module = _load(f'gamma_h2h15a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
            self.assertTrue(js_agrees(uid, got['value'], row['expected']) and js_agrees(uid, got['native'], row['expected']), f'{uid} javascript {str(row["args"])[:100]}')
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
