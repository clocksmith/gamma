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


_o = _load('gamma_h2h14a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h14a_reference_test_cases', HERE / 'cases.py')
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

    def test_stl(self):
        self.check(_o.STL, [(['hello world', 11], 1), (['hello world', 10], 2), (['  a  bb ccc ', 4], 2), (['abcdefgh ab cd', 3], 3), (['ab cd', 1], 2), (['x', 1], 1)])

    def test_stm(self):
        a, b, c = 'AAPL,B,0100,ABC123', 'AAPL,B,0100,XYZ999', '  GE,S,0050,ID0001'
        self.check(_o.STM1, [([[a, c], [b, c, c]], [c, a, b]), ([[a, b], [b, b]], [a, b]), ([[a, a], [a]], [a]), ([[], []], [])])
        self.check(_o.STM2, [([[a, c], [b, c, c]], [c]), ([[a, b], [b, b]], []), ([[a, a], [b]], [a]), ([[a], ['AAPL,S,0100,ABC123']], ['AAPL,B,0100,ABC123', 'AAPL,S,0100,ABC123'])])

    def test_smr(self):
        self.check(_o.SMR, [([['B', 'A'], [[5, 'A', 1], [3, 'B', 2], [5, 'B', 7], [5, 'B', 8], [4, 'C', 9]]], [[3, None, 2], [5, 1, 8]]),
                            ([['A'], [[2, 'A', -1], [2, 'A', 4], [0, 'A', 3]]], [[0, 3], [2, 4]]), ([['X'], [[1, 'Y', 1]]], []), ([[], []], [])])

    def test_sst(self):
        both = [([['a', '', 'b<END>c', 'd']], ['a', '', 'b']), ([['<END>x', 'y']], []), ([['', 'q', '<END>']], ['', 'q']), ([['x<END>y<END>']], ['x']),
                ([['ab', '', 'cd']], ['ab', '', 'cd']), ([[]], [])]
        self.check(_o.SST1, both)
        self.check(_o.SST2, both + [([['ab<E', 'ND>', 'z']], ['ab']), ([['a', '<', 'E', '', 'N', 'D>']], ['a']), ([['x<', 'END>']], ['x']), ([['<EN', 'D']], ['<EN', 'D'])])

    def test_smm(self):
        self.check(_o.SMM, [([['ab', 'ba'], 'ab'], 2), ([['aaa', 'aaa', 'aaa'], 'aa'], 16), ([['a'], 'a'], 3), ([['ab', 'cb'], 'b'], 6), ([['abc'], 'abcd'], 0)])

    def test_sro(self):
        self.check(_o.SRO, [(['aab'], 'aba'), (['aaab'], ''), (['bba'], 'bab'), (['zzyy'], 'yzyz'), (['aaabb'], 'ababa'), (['a'], 'a'), (['aa'], '')])

    def test_sbs(self):
        plans = [['Basic', 1000], ['Pro', 3100], ['Max', 2900]]
        self.check(_o.SBS, [([plans, [['2024-02-10', 'START', 'Pro'], ['2024-02-20', 'SWITCH', 'Max'], ['2024-03-01', 'END', None]]], [['2024-02', 2069]]),
                            ([plans, [['2023-12-31', 'START', 'Basic']]], [['2023-12', 32]]),
                            ([plans, [['2023-03-05', 'START', 'Basic'], ['2023-03-06', 'END', None], ['2023-03-07', 'START', 'Max']]],
                             [['2023-03', 2371]] + [['2023-%02d' % m, 2900] for m in range(4, 13)]),
                            ([[['A', 14], ['B', 1], ['C', 2]], [['2023-02-28', 'START', 'A'], ['2023-03-01', 'SWITCH', 'B'], ['2023-03-02', 'END', None]]], [['2023-02', 1], ['2023-03', 0]]),
                            ([plans, []], [])])

    def test_sub(self):
        self.check(_o.SUB, [([[3, 34, 4, 12, 5, 2], 9], True), ([[3, 34, 4, 12, 5, 2], 30], False), ([[2, 2, 2], 8], False), ([[2, 2, 2], 6], True), ([[], 0], True), ([[5], 0], True), ([[], 1], False)])

    def test_tgc(self):
        g = [['a', 'b'], ['b', 'c'], ['d']]
        self.check(_o.TGC, [([g, ['b']], ['a', 'c']), ([g, []], ['a', 'b', 'c', 'd']), ([[['a', 'a', 'b']], ['a', 'b']], []), ([[['x']], ['y']], [])])

    def test_tnl(self):
        self.check(_o.TNL, [(['a\nb\nc\n', 2], 'b\nc\n'), (['a\nb\nc', 2], 'b\nc'), (['a\nb\nc', 0], ''), (['\n\n\n', 2], '\n\n'), (['one', 5], 'one'), (['', 3], ''), (['a\nb\n', 9], 'a\nb\n')])

    def test_tsf(self):
        p = '{n, plural, one{# file} other{# files}} left'
        self.check(_o.TSF, [(['Hello {name}!', ['name'], ['Ann']], 'Hello Ann!'), ([p, ['n'], ['1']], '1 file left'), ([p, ['n'], ['0']], '0 files left'),
                            (['{x} {n, plural, one{a} other{b}}', [], []], '{x} {n, plural, one{a} other{b}}'), (['{a}{a}', ['a'], ['#']], '##'),
                            (['{n, plural, one{#} other{##}}', ['n'], ['12']], '1212')])

    def test_tbf(self):
        self.check(_o.TBF1, [([['hello', 'hi', 'hey you']], ['+-------+', '|hello  |', '+-------+', '+-------+', '|hi     |', '+-------+', '+-------+', '|hey you|', '+-------+'])])
        self.check(_o.TBF2, [([['a bb ccc', 'dddd'], 5], ['+----+', '|a bb|', '|ccc |', '+----+', '+----+', '|dddd|', '+----+']),
                             ([['abcdefgh x'], 3], ['+--------+', '|abcdefgh|', '|x       |', '+--------+'])])
        self.check(_o.TBF3, [([['a bb ccc', 'dddd'], 5], ['+-----+', '|a  bb|', '|ccc  |', '+-----+', '+-----+', '|dddd |', '+-----+']),
                             ([['a b c d'], 6], ['+------+', '|a  b c|', '|d     |', '+------+'])])

    def test_ttw(self):
        self.check(_o.TTW1, [(['Hello, hello WORLD!'], [['hello', 2], ['world', 1]]), (["it's 2 o'clock; IT is"], [['it', 2], ['clock', 1], ['is', 1], ['o', 1], ['s', 1]]),
                             (['a b c d e f g h i j k l a'], [['a', 2]] + [[ch, 1] for ch in 'bcdefghij']), ([''], [])])
        t = ops('WordFrequencyTracker', [], [('getTop10',), ('addText', 'b a b'), ('getTop10',), ('addText', 'A-a'), ('getTop10',)])
        self.check(_o.TTW2, [(t, [None, [], None, [['b', 2], ['a', 1]], None, [['a', 3], ['b', 2]]])])

    def test_tkb(self):
        t = ops('BookSalesTracker', [], [('getTopK', 3), ('recordSale', 'b', 2), ('recordSale', 'a', 2), ('getTopK', 5), ('recordSale', 'b', 1), ('getTopK', 1), ('getTopK', 0)])
        self.check(_o.TKB, [(t, [None, [], None, None, ['a', 'b'], None, ['b'], []])])

    def test_tkl(self):
        self.check(_o.TKL, [([[3, 1, 2], 2], [3, 2]), ([[5, 5, 1], 2], [5, 5]), ([[-1, -2], 2], [-1, -2]), ([[4], 0], []), ([[], 0], [])])

    def test_tkp(self):
        t = ops('PinManager', [], [('getTopK', 'art', 2), ('addPin', 7, 5, 'art'), ('addPin', 3, 5, 'art'), ('addPin', 9, 8, 'food'), ('addPin', 1, -2, 'art'),
                                   ('getTopK', 'art', 2), ('getTopK', 'food', 9), ('getTopK', 'art', 0)])
        self.check(_o.TKP, [(t, [None, [], None, None, None, None, [3, 7], [9], []])])

    def test_domain(self):
        for uid, args in [(_o.STL, ['   ', 3]), (_o.STL, ['a', 0]), (_o.STL, ['a\tb', 3]),
                          (_o.STM1, [['AAPL,B,100,ABC123'], []]), (_o.STM2, [[], ['aapl,B,0100,ABC123']]), (_o.STM1, [['AAPL,X,0100,ABC123'], []]),
                          (_o.SMR, [['A', 'A'], []]), (_o.SMR, [['a'], []]), (_o.SMR, [['A'], [[-1, 'A', 1]]]), (_o.SMR, [['A'], [[1, 'A']]]),
                          (_o.SST1, [['ab<E', 'ND>']]), (_o.SST1, [['\t']]), (_o.SST2, [['a' * 200001]]),
                          (_o.SMM, [['ab', 'a'], 'a']), (_o.SMM, [['ab'], '']), (_o.SMM, [[], 'a']), (_o.SMM, [['aB'], 'a']),
                          (_o.SRO, ['']), (_o.SRO, ['aB']),
                          (_o.SBS, [[['A', 1], ['B', 1]], []]), (_o.SBS, [[['A', 1], ['A', 2], ['C', 3]], []]),
                          (_o.SBS, [[['A', 1], ['B', 1], ['C', 1]], [['2023-02-29', 'START', 'A']]]),
                          (_o.SBS, [[['A', 1], ['B', 1], ['C', 1]], [['2023-02-01', 'END', None]]]),
                          (_o.SBS, [[['A', 1], ['B', 1], ['C', 1]], [['2023-02-01', 'START', 'A'], ['2023-02-01', 'END', None]]]),
                          (_o.SBS, [[['A', 1], ['B', 1], ['C', 1]], [['2023-02-01', 'START', 'A'], ['2023-02-02', 'SWITCH', 'A']]]),
                          (_o.SBS, [[['A', 1], ['B', 1], ['C', 1]], [['2023-12-01', 'START', 'A'], ['2024-01-02', 'END', None]]]),
                          (_o.SUB, [[0], 0]), (_o.SUB, [[1], -1]), (_o.SUB, [[1] * 201, 1]),
                          (_o.TGC, [[['A']], []]), (_o.TGC, [[], ['a', 'a']]),
                          (_o.TNL, ['a\tb', 1]), (_o.TNL, ['a', -1]),
                          (_o.TSF, ['{a', [], []]), (_o.TSF, ['a}', [], []]), (_o.TSF, ['{n, plural, one{x} other{y}}', ['n'], ['x']]), (_o.TSF, ['', ['a', 'a'], ['1', '2']]),
                          (_o.TSF, ['', ['a'], ['{']]), (_o.TSF, ['{n,plural, one{x} other{y}}', [], []]),
                          (_o.TBF1, [[]]), (_o.TBF1, [['']]), (_o.TBF2, [['a  b'], 3]), (_o.TBF2, [[' a'], 3]), (_o.TBF3, [['abcd'], 3]), (_o.TBF2, [['a'], 0]),
                          (_o.TTW1, ['\t']), (_o.TTW2, [['WordFrequencyTracker', 'addText'], [[], ['a', 'b']]]), (_o.TTW2, [['WordFrequencyTracker'], [[1]]]),
                          (_o.TKB, [['BookSalesTracker', 'recordSale'], [[], ['b', 0]]]), (_o.TKB, [['BookSalesTracker', 'getTopK'], [[], [-1]]]), (_o.TKB, [['Tracker'], [[]]]),
                          (_o.TKP, [['PinManager', 'addPin', 'addPin'], [[], [1, 1, 'a'], [1, 2, 'b']]]), (_o.TKP, [['PinManager', 'getTopK'], [[], ['A', 1]]]),
                          (_o.TKL, [[1, 2], 3]), (_o.TKL, [[1.5], 1]), (_o.TKL, [[True], 1])]:
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
        module = _load(f'gamma_h2h14a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
