"""Native observer controls: source-free toy classes, then an author-local pass of own class candidates (not qualification)."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


observer = load('gamma_h2h17b_native_observer', ROOT / 'native_harness.py')
protocol = load('gamma_h2h17b_native_protocol', ROOT / 'native_protocol.py')
cases = load('gamma_h2h17b_native_cases', ROOT / 'cases.py')
transport = load('gamma_h2h17b_observation_transport', ROOT.parents[1] / 'public-domain-qualification-easy16-v1/harness.py')
T = 'hack2hire:679da470996c3c60bd38b5ba'
R = 'hack2hire:67730b5ddd9437f8aa275b04'


class Toy:
    """Source-free toy AlienBaseAttack (plain list of attacks rescanned on every query)."""
    def __init__(self, n): self.n = n; self.hits = []

    def attack(self, x): self.hits.append(x)

    def isDestroyed(self): return all(i in self.hits for i in range(self.n))


class NativeObserverTests(unittest.TestCase):
    def test_same_receiver_and_constructor_arguments(self):
        created, receivers = [], []

        class AlienBaseAttack(Toy):
            def __init__(self, n): super().__init__(n); created.append(self)
            def attack(self, x): receivers.append(self); super().attack(x)
            def isDestroyed(self): receivers.append(self); return super().isDestroyed()
        args = [['AlienBaseAttack', 'attack', 'isDestroyed'], [[1], [0], []]]
        for _ in range(2):
            record = observer.observe({'AlienBaseAttack': AlienBaseAttack, 'solve': lambda *a: 1 / 0}, T, {'args': args}, transport)
            self.assertIsNone(protocol.check(T, args, record, [None, None, True], 'python'))
        self.assertEqual(len(created), 2)
        self.assertTrue(receivers[0] is receivers[1] is created[0] and receivers[2] is receivers[3] is created[1])

    def test_void_methods_and_return_types(self):
        args = [['AlienBaseAttack', 'attack', 'attack', 'isDestroyed'], [[2], [0], [1], []]]
        record = observer.observe({'AlienBaseAttack': Toy}, T, {'args': args}, transport)
        self.assertIsNone(protocol.check(T, args, record, [None, None, None, True], 'python'))

        class Wrong(Toy):
            def isDestroyed(self): return False
        record = observer.observe({'AlienBaseAttack': Wrong}, T, {'args': args}, transport)
        self.assertEqual(protocol.check(T, args, record, [None, None, None, True], 'python'), 'wrong_answer')

        class Leaky(Toy):
            def attack(self, x): super().attack(x); return len(self.hits)
        record = observer.observe({'AlienBaseAttack': Leaky}, T, {'args': args}, transport)
        self.assertEqual(protocol.check(T, args, record, [None, None, None, True], 'python'), 'native_return_type')

        class BoolBlocks:
            def __init__(self, n, maximumCycles): pass
            def write(self): return False
        args = [['DiskBlockManager', 'write'], [[1, 1], []]]
        record = observer.observe({'DiskBlockManager': BoolBlocks}, R, {'args': args}, transport)
        self.assertEqual(protocol.check(R, args, record, [None, 0], 'python'), 'wrong_answer')

    def test_layouts_bind_inferred_methods(self):
        bound = set()
        for row in json.loads((ROOT / 'contracts.json').read_text())['problems']:
            if row['uid'] in observer.LAYOUT:
                name, ctor, methods, voids = observer.LAYOUT[row['uid']]
                iface = row['inferred_interface']
                self.assertEqual(name, iface['classname'])
                self.assertEqual(ctor, len(iface['constructor']['params']))
                self.assertEqual(methods, {m['name']: len(m['params']) for m in iface['methods']})
                self.assertEqual(voids, {m['name'] for m in iface['methods'] if m['return']['type'] == 'void'})
                self.assertEqual(protocol.RETURNS[row['uid']], {m['name']: m['return']['type'] for m in iface['methods']})
                bound.add(row['uid'])
        self.assertEqual(bound, set(observer.LAYOUT))
        self.assertEqual(set(observer.LAYOUT), set(protocol.oracle.CLASSES))

    def test_no_fallback_and_packet_bound(self):
        args = [['AlienBaseAttack', 'isDestroyed'], [[1], []]]
        with self.assertRaises(TypeError): observer.observe({'solve': lambda *a: [None, False]}, T, {'args': args}, transport)
        raw = protocol.packet(T, [{'args': args, 'expected': [None, False]}], maximum_bytes=10000)
        self.assertNotIn(b'expected', raw)
        with self.assertRaises(ValueError): protocol.packet(T, [{'args': args}], maximum_bytes=1)
        with self.assertRaises(ValueError): observer.shape(T, [['AlienBaseAttack', 'clear'], [[1], []]])


class OwnCandidatesThroughObserver(unittest.TestCase):
    """Author-local: own Python class candidates observed natively against own generated cases."""
    def test_python_candidates(self):
        total = 0
        for uid in observer.LAYOUT:
            raw = (ROOT / 'python' / (uid.split(':', 1)[1] + '.py')).read_text()
            namespace = {'__name__': 'candidate'}
            exec(compile(raw, 'program.py', 'exec'), namespace)
            for row in cases.build_cases(uid, include_maximum=True):
                record = observer.observe(namespace, uid, {'args': row['args']}, transport)
                self.assertIsNone(protocol.check(uid, row['args'], record, row['expected'], 'python'), uid)
                total += 1
        print(f'native python observations passed: {total}')


JS_NATIVE = r"""
const fs=require('fs'),h=require(process.argv[1]+'/native_harness.cjs');
const transport={decode:x=>structuredClone(x),encode:x=>structuredClone(x),aliases:()=>[]};
const job=JSON.parse(fs.readFileSync(0,'utf8'));const exported=require(job.path);
process.stdout.write(JSON.stringify(job.cases.map(args=>{const before=JSON.stringify(args);const r=h.observe(exported,job.uid,{args},transport);
 return {result:r.result,types:r.native_method_return_types,unchanged:JSON.stringify(args)===before};})));"""


class OwnJavascriptCandidatesThroughObserver(unittest.TestCase):
    """Author-local: own JS class candidates observed natively (node --jitless) against own generated cases."""
    def test_javascript_candidates(self):
        import shutil
        import subprocess
        if not shutil.which('node'): self.skipTest('node absent')
        total = 0
        for uid in observer.LAYOUT:
            rows = cases.build_cases(uid, include_maximum=True)
            # small rows in one node process, each large analytic row in its own (bounds host memory)
            batches = [[r for r in rows if not r.get('isolate')]] + [[r] for r in rows if r.get('isolate')]
            for batch in batches:
                total += self.observe_batch(uid, batch, subprocess)
        print(f'native javascript observations passed: {total}')

    def observe_batch(self, uid, rows, subprocess):
        job = {'uid': uid, 'path': str(ROOT / 'javascript' / (uid.split(':', 1)[1] + '.js')), 'cases': [r['args'] for r in rows]}
        res = subprocess.run(['node', '--jitless', '-e', JS_NATIVE, str(ROOT)], input=json.dumps(job), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr[-1500:])
        done = 0
        for row, got in zip(rows, json.loads(res.stdout)):
            self.assertTrue(protocol.exact(got['result'], row['expected']) and got['unchanged'], uid)
            kinds = ['constructed'] + [protocol.KIND[protocol.RETURNS[uid][op]][1] for op in row['args'][0][1:]]
            self.assertEqual(got['types'], kinds, uid)
            done += 1
        self.assertEqual(done, len(rows))
        return done

    def test_source_free_js_controls(self):
        import shutil
        import subprocess
        if not shutil.which('node'): self.skipTest('node absent')
        res = subprocess.run(['node', str(ROOT / 'test_native_observer.cjs')], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr[-1500:])


if __name__ == '__main__': unittest.main()
