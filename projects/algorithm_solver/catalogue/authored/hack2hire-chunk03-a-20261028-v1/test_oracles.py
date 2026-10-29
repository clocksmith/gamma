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


_o = _load('gamma_h2h03a_reference_test_oracles', HERE / 'oracles.py')
_c = _load('gamma_h2h03a_reference_test_cases', HERE / 'cases.py')
reference, validate_domain = _o.reference, _o.validate_domain
CONTRACTS = {row['uid']: row for row in json.loads((HERE / 'contracts.json').read_text())['problems']}


def stem(uid): return uid.split(':', 1)[1]


def exact(a, b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(map(exact, a, b))
    if type(a) is dict: return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    return a == b


def ops(name, ctor, calls): return _c._ops(name, ctor, calls)


def node(i, *kids): return {'id': i, 'children': list(kids)}


class References(unittest.TestCase):
    """Hand-worked examples for each inferred spec (worked by the author, not taken from the source)."""
    def test_itoa(self):
        self.assertEqual([reference(_o.ITOA, [v]) for v in (0, -7, 2**31 - 1, -2**31)], ['0', '-7', '2147483647', '-2147483648'])

    def test_token(self):
        self.assertEqual(reference(_o.TOKEN, ['abab', ['a', 'b', 'ab', 'abab', 'ba']]), [3])
        self.assertEqual(reference(_o.TOKEN, ['aaa', ['a', 'aa', 'aaa']]), [2])
        self.assertEqual(reference(_o.TOKEN, ['aaaa', ['a', 'aa']]), [1, 1])
        self.assertEqual(reference(_o.TOKEN, ['abc', ['a', 'b', 'c', 'bc', 'ab', 'abc']]), [5])  # bc -> [0, 3]; ab finds nothing; abc = a + bc

    def test_interleave(self):
        t = ops('InterleaveIterator', [[[1, 2, 3], [4], [5, 6]], False], [('next',)] * 7 + [('hasNext',)])
        self.assertEqual(reference(_o.ILV, t), [None, 1, 4, 5, 2, 6, 3, None, False])
        t = ops('InterleaveIterator', [[[1, 2], [], [3]], True], [('next',)] * 4 + [('hasNext',)])
        self.assertEqual(reference(_o.ILV, t), [None, 1, 3, 2, 1, True])
        self.assertEqual(reference(_o.ILV, ops('InterleaveIterator', [[[]], True], [('hasNext',), ('next',)])), [None, False, None])

    def test_jump(self):
        self.assertEqual(reference(_o.JUMP, [[1, -100, -100, 7]]), 8)
        self.assertEqual(reference(_o.JUMP, [[1, -2]]), -1)
        self.assertEqual(reference(_o.JUMP, [[0] * 14 + [3]]), 3)
        self.assertEqual(reference(_o.JUMP, [[2, -9, -9, -9, -9, 4]]), -12)  # every route to index 5 lands on two interior cells

    def test_kth(self):
        self.assertEqual(reference(_o.KTH, [[3, 1, 2], 2]), [1, 2])
        self.assertEqual(reference(_o.KTH, [[2, 5, 1, 4, 3], 1]), [2, 5, 5, 5, 5])

    def test_team(self):
        self.assertEqual(reference(_o.TEAM, [[1, 2, 2, 3, 5]]), 4)
        self.assertEqual(reference(_o.TEAM, [[1, 3, 5]]), 1)

    def test_league(self):
        self.assertEqual(reference(_o.LEAGUE, [['A', 'B', 'A'], [10, 99, 20], [1, 5, 2], 'A']), [90, '45.00'])
        self.assertEqual(reference(_o.LEAGUE, [['L', 'L', 'L'], [1, 1, 1], [1, 0, 0], 'L']), [4, '0.67'])

    def test_tree(self):
        root = node(0, node(1, node(2, node(3))), node(9))
        self.assertEqual([reference(_o.TREE1, [root, d]) for d in ([], [3], [1, 2, 3], [9], [1])], [4, 3, 2, 4, 3])
        self.assertEqual([reference(_o.TREE2, [root, h]) for h in (1, 2, 3, 4)], [4, 2, 1, 0])

    def test_lerp(self):
        self.assertEqual(reference(_o.LERP, [[[0, 5], [0, 1], [3, 9], [3, -3]], [-1, 0, 1, 2, 3, 4]]), ['1', '5', '7/3', '-1/3', '9', '9'])

    def test_fill(self):
        self.assertEqual(reference(_o.FILLPTS, [2, [[0, 0], [1, 7], [5, 0]]]), [[0, '0'], [1, '7'], [3, '7/2'], [5, '0']])

    def test_shift(self):
        self.assertEqual([reference(_o.SHIFT, [a]) for a in ([1, 3, 2], [1, 2, 3], [1, 1, 2, 1], [2, 2], [5])], [2, -1, 2, 0, 0])

    def test_tiles(self):
        self.assertEqual([reference(_o.TILES, a) for a in ([5, 1], [4, 1], [0, 0], [3, 0], [0, 1], [1, 2])], [3, 2, 0, 1, 2, 2])

    def test_leaf(self):
        self.assertEqual(reference(_o.LEAF, [[-10, 9, 20, None, None, 15, 7]]), 42)
        self.assertEqual(reference(_o.LEAF, [[1, None, 3]]), 3)
        self.assertEqual(reference(_o.LEAF, [[1, 2, None, 3, 4]]), 9)

    def test_deploy(self):
        self.assertEqual(reference(_o.DEPLOY, [[5, 1, 9]]), 12)
        self.assertEqual(reference(_o.DEPLOY, [[4, 4, 1, 1]]), 6)

    def test_calls(self):
        self.assertEqual(reference(_o.CALLS, [[[1, 'a', 0, 10], [1, 'b', 9, 20], [2, 'c', 5, 6]]]), [[1, 0, 2], [2, 0, 1]])
        self.assertEqual(reference(_o.CALLS, [[[1, 'a', 0, 10], [1, 'b', 10, 20]]]), [[1, 0, 1]])
        D = _o.DAY_MS
        self.assertEqual(reference(_o.CALLS, [[[7, 'x', D - 1, D + 1], [7, 'y', D, D + 2]]]), [[7, 0, 1], [7, 1, 2]])

    def test_stab(self):
        self.assertEqual(reference(_o.STAB, [[1, 2], [10, 1]]), 11)
        rng = random.Random(9)  # subset enumeration vs threshold scan agree on small inputs
        for _ in range(200):
            n = rng.randrange(1, 10); a = [rng.randrange(0, 9) for _ in range(n)]; r = [rng.randrange(0, 9) for _ in range(n)]
            self.assertEqual(_o.ref_stab(a, r), max(x * sum(r[i] for i in range(n) if a[i] >= x) for x in set(a)))

    def test_tree_min_deletions_vs_constructions(self):
        chain = node(1, node(2, node(3, node(4))))
        self.assertEqual(reference(_o.TREE2, [node(0, chain), 2]), 3)
        broom = node(0, node(1, node(2, node(10), node(11), node(12))))
        self.assertEqual(reference(_o.TREE2, [broom, 2]), 2)

    def test_domain(self):
        bad_tree = node(0)
        for i in range(1, _o.MAX_TREE_DEPTH + 1): bad_tree = node(i, bad_tree)
        for uid, args in [(_o.ITOA, [2**31]), (_o.TOKEN, ['ab', ['a', 'ab']]), (_o.TOKEN, ['a', ['a', 'bc', 'd']]), (_o.TOKEN, ['a', ['a', 'a']]),
                          (_o.ILV, ops('InterleaveIterator', [[[1]], 1], [])), (_o.ILV, ops('InterleaveIterator', [[[1]], True], [('peek',)])),
                          (_o.JUMP, [[]]), (_o.KTH, [[1, 3], 1]), (_o.KTH, [[1, 2], 3]), (_o.TEAM, [[0]]),
                          (_o.LEAGUE, [['A', 'B'], [1, 1], [0, 0], 'A']), (_o.TREE1, [node(0, node(1)), [0]]), (_o.TREE1, [node(0, node(1)), [2]]),
                          (_o.TREE2, [node(0, node(0)), 1]), (_o.TREE2, [bad_tree, 1]), (_o.LERP, [[], [1]]),
                          (_o.FILLPTS, [2, [[0, 0], [3, 1]]]), (_o.FILLPTS, [1, [[1, 0], [1, 1]]]), (_o.SHIFT, [[]]), (_o.TILES, [-1, 0]),
                          (_o.LEAF, [[None]]), (_o.LEAF, [[1, None, None, 2]]), (_o.DEPLOY, [[1, 2]]),
                          (_o.CALLS, [[[1, 'a', 5, 5]]]), (_o.CALLS, [[[1, 'a', 0, 1], [2, 'a', 0, 1]]]), (_o.STAB, [[1, 2], [1]])]:
            with self.assertRaises(ValueError, msg=str(args)[:80]): validate_domain(uid, args)

    def test_generated_cases_domain_valid(self):
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True): validate_domain(uid, row['args'])

    def test_generated_nesting_depth(self):
        def depth(v):
            best, stack = 0, [(v, 1)]
            while stack:
                x, d = stack.pop(); best = max(best, d)
                if type(x) is list: stack += [(y, d + 1) for y in x]
                elif type(x) is dict: stack += [(y, d + 1) for y in x.values()]
            return best
        for uid in _o.IDS:
            for row in _c.build_cases(uid, include_maximum=True): self.assertLessEqual(depth(row['args']), 200, uid)

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
        module = _load(f'gamma_h2h03a_candidate_python_{stem(uid)}', path); passed = 0; worst = 0.0
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
