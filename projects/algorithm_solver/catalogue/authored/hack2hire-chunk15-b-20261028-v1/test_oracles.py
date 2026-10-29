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


_o = _load('gamma_h2h15b_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h15b_reference_test_cases', HERE / 'cases.py')
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

    def test_fst(self):
        files = [['a.txt', ['Foo bar', 'nothing', 'foo-FOO xfoo foo1']], ['b.txt', ['bar']], ['c', []]]
        self.check(_o.FST, [([files, 'foo'], [['a.txt', '3', 'Foo bar', 'foo-FOO xfoo foo1']]), ([files, 'BAR'], [['a.txt', '1', 'Foo bar'], ['b.txt', '1', 'bar']]),
                            ([[], 'x'], []), ([[['a', ['foofoo foo']]], 'FOO'], [['a', '1', 'foofoo foo']])])

    def test_imd(self):
        t1 = ops('InMemoryDB', [], [('setData', 'a', 'f', 'x'), ('getData', 'a', 'f'), ('getData', 'a', 'g'), ('setData', 'a', 'f', 'y'), ('getData', 'a', 'f'),
                                    ('deleteData', 'a', 'f'), ('deleteData', 'a', 'f'), ('deleteData', 'z', 'f'), ('getData', 'a', 'f')])
        self.check(_o.IMD1, [(t1, [None, None, 'x', '', None, 'y', True, False, False, ''])])
        t2 = ops('InMemoryDB', [], [('setData', 'a', 'fb', '2'), ('setData', 'a', 'f', '1'), ('setData', 'a', 'g', ''), ('scanData', 'a'), ('scanDataByPrefix', 'a', 'f'),
                                    ('scanDataByPrefix', 'a', 'z'), ('scanData', 'b')])
        self.check(_o.IMD2, [(t2, [None, None, None, None, ['f(1)', 'fb(2)', 'g()'], ['f(1)', 'fb(2)'], [], []])])
        t3 = ops('InMemoryDB', [], [('setDataAtWithTtl', 'a', 'f', 'x', 1, 5), ('getDataAt', 'a', 'f', 5), ('getDataAt', 'a', 'f', 6), ('setDataAt', 'a', 'g', 'y', 7),
                                    ('setDataAtWithTtl', 'a', 'h', 'z', 8, 2), ('scanDataAt', 'a', 9), ('scanDataByPrefixAt', 'a', 'h', 10), ('deleteDataAt', 'a', 'h', 11), ('deleteDataAt', 'a', 'g', 12)])
        self.check(_o.IMD3, [(t3, [None, None, 'x', '', None, None, ['g(y)', 'h(z)'], [], False, True])])
        t4 = ops('InMemoryDB', [], [('setDataAtWithTtl', 'a', 'f', 'x', 1, 10), ('setDataAt', 'b', 'g', 'y', 2), ('backup', 3), ('setDataAt', 'a', 'h', 'z', 4), ('deleteDataAt', 'b', 'g', 5),
                                    ('backup', 6), ('restore', 20, 5), ('scanDataAt', 'a', 21), ('getDataAt', 'b', 'g', 22), ('getDataAt', 'a', 'f', 27), ('getDataAt', 'a', 'f', 28),
                                    ('restore', 30, 6), ('getDataAt', 'b', 'g', 31), ('scanDataAt', 'a', 32), ('backup', 33)])
        # backup at 3 keeps f with 8 left (expiry 11) and g; restore at 20 re-anchors f to expire at 28; backup at 6 has f (5 left) and h, no g
        self.check(_o.IMD4, [(t4, [None, None, None, 2, None, True, 1, None, ['f(x)'], 'y', 'x', '', None, '', ['f(x)', 'h(z)'], 1])])

    def test_iqr(self):
        t = ops('InfiniteQueue', [], [('poll',), ('getRandom', 3), ('add', 5), ('add', 7), ('add', 9), ('getRandom', 0), ('getRandom', 4), ('poll',), ('getRandom', 10**15), ('poll',), ('poll',), ('poll',)])
        self.check(_o.IQR, [(t, [None, -1, -1, None, None, None, 5, 7, 5, 7, 7, 9, -1])])

    def test_lza(self):
        t = ops('LazyArray', [[1, 2, 3, 2]], [('indexOf', 2), ('map', 'multiply', 2), ('indexOf', 2), ('indexOf', 4), ('map', 'add', -1), ('indexOf', 5), ('indexOf', 4),
                                             ('map', 'multiply', 0), ('indexOf', 0), ('indexOf', 1)])
        self.check(_o.LZA, [(t, [None, 1, None, 0, 1, None, 2, -1, None, 0, -1]), (ops('LazyArray', [[]], [('indexOf', 0), ('map', 'multiply', 0), ('indexOf', 0)]), [None, -1, None, -1])])

    def test_dwc(self):
        self.check(_o.DWC, [([0, [], []], 0), ([5, [1, -1], [3, 3]], 1), ([9, [1, -1], [3, 3]], 2), ([10, [2, 5, -1, -4], [1, 4, 2, 2]], 3), ([0, [3], [1]], 0), ([1, [3], [1]], 1),
                            ([8, [1, 2, -1], [1, 1, 4]], 3), ([7, [1, 2, -1], [1, 1, 4]], 2)])

    def test_esc(self):
        t = ops('EscapeRoom', [3, 4], [('topPlayers', 10), ('advance', 2), ('advance', 1), ('advance', 2), ('advance', 2), ('countInRoom', 2), ('countInRoom', 0), ('topPlayers', 3),
                                      ('advance', 1), ('topPlayers', 4)])
        self.check(_o.ESC, [(t, [None, [0, 1, 2, 3], None, None, None, None, 1, 2, [2, 1, 0], None, [2, 1, 0, 3]])])

    def test_elr(self):
        t = ops('EventLogger', [10], [('logEvent', 'a', 0), ('logEvent', 'a', 5), ('logEvent', 'b', 5), ('logEvent', 'a', 10), ('logEvent', 'a', 19), ('logEvent', 'a', 20)])
        self.check(_o.ELR, [(t, [None, True, False, True, True, False, True])])

    def test_fvs(self):
        self.check(_o.FVS, [([[]], []), ([[['a:1', 'b:2'], ['a:3', 'c:null']]], ['a:3', 'b:2', 'c:null']), ([[['a:1', 'a:2'], ['b:x:y', 'b:']]], ['a:2', 'b:']),
                            ([[['a10:1', 'a1:2']]], ['a1:2', 'a10:1'])])

    def test_fmi(self):
        self.check(_o.FMI, [(['Mon 10:00 AM', 'Mon 10:12 AM'], ['Mon 10:00 AM', 'Mon 10:05 AM', 'Mon 10:10 AM']),
                            (['Fri 11:58 AM', 'Fri 12:07 PM'], ['Fri 12:00 PM', 'Fri 12:05 PM']),
                            (['Sun 11:50 PM', 'Mon 12:05 AM'], ['Sun 11:50 PM', 'Sun 11:55 PM', 'Mon 12:00 AM', 'Mon 12:05 AM']),
                            (['Tue 3:03 PM', 'Tue 3:04 PM'], []), (['Wed 9:05 AM', 'Wed 9:05 AM'], ['Wed 9:05 AM'])])
        self.assertEqual(len(reference(_o.FMI, ['Mon 12:00 AM', 'Sun 11:59 PM'])), 2016)

    def test_fas(self):
        self.check(_o.FAS, [([['abc'], 'xbca'], 'abc'), ([['ab', 'ba'], 'xba'], 'ab'), ([['zz', 'q'], 'abc'], ''), ([['abc'], ''], ''), ([['aab', 'b'], 'abab'], 'aab'), ([['bb', 'b'], 'abab'], 'b')])

    def test_fkd(self):
        self.check(_o.FKD, [([[1], 1], 1), ([[1, 2, 1, 3], 3], 3), ([[1, 1, 1], 2], -1), ([[1, 2, 2, 2, 3, 1], 3], 3), ([[5, 5, 6, 6], 2], 2)])

    def test_fpt(self):
        t = [1, None, 3, 2, 4, None, 5, 6, None, None, 3]
        self.check(_o.FPT1, [([t, [1, 3, 5]], True), ([t, [1, 4, 3]], True), ([t, [3, 5]], False), ([t, [1, 3, 7]], False), ([[7], [7, 7]], False)])
        self.check(_o.FPT2, [([t, [3, 5]], True), ([t, [4, 3]], True), ([t, [3]], True), ([t, [2, 3]], False), ([t, [5, 6]], False)])

    def test_fri(self):
        self.check(_o.FRI, [([0, 10, 2, [], 1], [[0, 10]]), ([0, 10, 2, [[2, 5, 2]], 1], [[0, 2], [5, 10]]),
                            ([0, 10, 3, [[0, 4, 1], [2, 6, 1], [6, 10, 3]], 2], [[0, 2], [4, 6]]), ([5, 8, 1, [[5, 6, 1], [7, 8, 1]], 1], [[6, 7]])])

    def test_khd(self):
        loans = [['amy', 'bob', '10'], ['cat', 'bob', '5'], ['amy', 'cat', '5']]
        self.check(_o.KHD, [([[], 1], ''), ([loans, 1], 'amy'), ([loans, 2], ''), ([[['amy', 'bob', '10'], ['cat', 'bob', '10']], 2], 'cat'), ([[['amy', 'bob', '0']], 1], '')])

    def test_fir(self):
        self.check(_o.FIR, [([[['']], [0, 0], 'a'], False), ([[['a', 'a', 'a', '']], [0, 3], 'a'], True), ([[['a', 'a', 'a', '']], [0, 3], 'b'], False),
                            ([[['a'], ['a'], [''], ['a']], [2, 0], 'a'], True), ([[['a', '', '', ''], ['', 'a', '', ''], ['', '', '', ''], ['', '', '', 'a']], [2, 2], 'a'], True),
                            ([[['', '', '', 'b'], ['', '', 'b', ''], ['', '', '', ''], ['b', '', '', '']], [2, 1], 'b'], True), ([[['a', 'a', '', 'a', 'b']], [0, 2], 'a'], True)])

    def test_gtr(self):
        self.check(_o.GTR, [([[3, 3, 5], [3, 5, 9], [5, 7, 1]], [15, 21, 21]), ([[1], [], []], []), ([[2, 2], [2], [2]], [4])])

    def test_domain(self):
        bad = [(_o.FST, [[['a', ['x']], ['a', []]], 'x']), (_o.FST, [[['a', ['tab\there']]], 'x']), (_o.FST, [[], '']), (_o.FST, [[], 'a-b']),
               (_o.IMD1, ops('InMemoryDB', [], [('setData', 'A', 'f', 'x')])), (_o.IMD1, ops('InMemoryDB', [], [('scanData', 'a')])),
               (_o.IMD2, ops('InMemoryDB', [1], [])), (_o.IMD3, ops('InMemoryDB', [], [('getDataAt', 'a', 'f', 2), ('getDataAt', 'a', 'f', 2)])),
               (_o.IMD3, ops('InMemoryDB', [], [('setDataAtWithTtl', 'a', 'f', 'x', 1, 0)])), (_o.IMD4, ops('InMemoryDB', [], [('restore', 5, 1)])),
               (_o.IMD4, ops('InMemoryDB', [], [('backup', 3), ('restore', 5, 2)])), (_o.IMD4, ops('InMemoryDB', [], [('backup', 3), ('restore', 5, 5)])),
               (_o.IQR, ops('InfiniteQueue', [], [('add', -1)])), (_o.IQR, ops('InfiniteQueue', [], [('getRandom', -1)])),
               (_o.LZA, ops('LazyArray', [[1]], [('map', 'divide', 2)])), (_o.LZA, ops('LazyArray', [[10**6]], [('map', 'multiply', 1000)] * 4)),
               (_o.LZA, ops('LazyArray', [[1]], [('map', 'add', 10**7)])), (_o.DWC, [1, [0], [1]]), (_o.DWC, [1, [1, 1], [1, 1]]), (_o.DWC, [1, [1], [0]]), (_o.DWC, [1, [1], []]),
               (_o.ESC, ops('EscapeRoom', [1, 1], [('advance', 1)])), (_o.ESC, ops('EscapeRoom', [0, 1], [])), (_o.ESC, ops('EscapeRoom', [1, 1], [('topPlayers', 0)])),
               (_o.ELR, ops('EventLogger', [0], [])), (_o.ELR, ops('EventLogger', [1], [('logEvent', 'a', 5), ('logEvent', 'a', 4)])),
               (_o.FVS, [[['a:1'], []]]), (_o.FVS, [[['a1']]]), (_o.FVS, [[[':v']]]), (_o.FMI, ['Mon 10:00', 'Mon 10:05 AM']), (_o.FMI, ['Mon 00:00 AM', 'Mon 10:05 AM']),
               (_o.FMI, ['Mon 09:00 AM', 'Mon 10:05 AM']), (_o.FAS, [['a', 'a'], 'a']), (_o.FAS, [[], 'a']), (_o.FAS, [['A'], 'a']), (_o.FKD, [[], 1]), (_o.FKD, [[1], 2]),
               (_o.FPT1, [[None], [1]]), (_o.FPT1, [[1, 2], [1]]), (_o.FPT1, [[1, None], [1]]), (_o.FPT1, [[1, None, 2, None, None, None, 3], [1]]), (_o.FPT2, [[1], []]),
               (_o.FRI, [0, 10, 1, [[0, 5, 1], [2, 6, 1]], 1]), (_o.FRI, [0, 10, 2, [[3, 5, 1], [2, 6, 1]], 1]), (_o.FRI, [0, 10, 2, [[3, 3, 1]], 1]), (_o.FRI, [0, 10, 2, [], 3]),
               (_o.KHD, [[['a', 'a', '1']], 1]), (_o.KHD, [[['a', 'b', '01']], 1]), (_o.KHD, [[['a', 'b', '-1']], 1]), (_o.KHD, [[], 0]),
               (_o.FIR, [[['a']], [0, 0], 'a']), (_o.FIR, [[['', ''], ['']], [0, 0], 'a']), (_o.FIR, [[['c']], [0, 0], 'a']), (_o.FIR, [[['']], [0, 0], 'c']),
               (_o.GTR, [[], [], []]), (_o.GTR, [[1], [1], []]), (_o.GTR, [[0], [], []])]
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
        module = _load(f'gamma_h2h15b_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
