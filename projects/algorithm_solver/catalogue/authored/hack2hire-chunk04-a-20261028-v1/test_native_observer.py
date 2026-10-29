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


observer = load('gamma_h2h04a_native_observer', ROOT / 'native_harness.py')
protocol = load('gamma_h2h04a_native_protocol', ROOT / 'native_protocol.py')
cases = load('gamma_h2h04a_native_cases', ROOT / 'cases.py')
transport = load('gamma_h2h04a_observation_transport', ROOT.parents[1] / 'public-domain-qualification-easy16-v1/harness.py')
ITER = 'hack2hire:677bf4df5cbaff553b53b068'
SNAP1 = 'hack2hire:69b191c3a4e93c007df4004d'


class NativeObserverTests(unittest.TestCase):
    def test_same_receiver_and_constructor_arguments(self):
        created, receivers = [], []

        class SubarrayFirstIterator:
            def __init__(self, a, b): self.items = list(b) + list(a); created.append(self)
            def hasNext(self): receivers.append(self); return bool(self.items)
            def next(self): receivers.append(self); return self.items.pop(0)
        args = [['SubarrayFirstIterator', 'next', 'hasNext'], [[[], [7]], [], []]]
        for _ in range(2):
            record = observer.observe({'SubarrayFirstIterator': SubarrayFirstIterator, 'solve': lambda *a: 1 / 0}, ITER, {'args': args}, transport)
            self.assertIsNone(protocol.check(ITER, args, record, [None, 7, False], 'python'))
        self.assertEqual(len(created), 2)
        self.assertTrue(receivers[0] is receivers[1] is created[0] and receivers[2] is receivers[3] is created[1])

    def test_void_methods_and_return_types(self):
        class SocialNetwork:
            def __init__(self): self.edges, self.snaps = set(), []
            def follow(self, f, e): self.edges.add((f, e))
            def unfollow(self, f, e): self.edges.discard((f, e))
            def snapshot(self): self.snaps.append(set(self.edges)); return len(self.snaps) - 1
            def isFollowing(self, f, e, s): return (f, e) in self.snaps[s]
        args = [['SocialNetwork', 'follow', 'snapshot', 'isFollowing'], [[], [1, 2], [], [1, 2, 0]]]
        record = observer.observe({'SocialNetwork': SocialNetwork}, SNAP1, {'args': args}, transport)
        self.assertIsNone(protocol.check(SNAP1, args, record, [None, None, 0, True], 'python'))

        class Wrong(SocialNetwork):
            def isFollowing(self, f, e, s): return 1
        record = observer.observe({'SocialNetwork': Wrong}, SNAP1, {'args': args}, transport)
        self.assertEqual(protocol.check(SNAP1, args, record, [None, None, 0, True], 'python'), 'wrong_answer')

        class Chatty(SocialNetwork):
            def follow(self, f, e): self.edges.add((f, e)); return True
        record = observer.observe({'SocialNetwork': Chatty}, SNAP1, {'args': args}, transport)
        self.assertEqual(protocol.check(SNAP1, args, record, [None, None, 0, True], 'python'), 'native_return_type')

    def test_layouts_bind_inferred_methods(self):
        for row in json.loads((ROOT / 'contracts.json').read_text())['problems']:
            if row['uid'] in observer.LAYOUT:
                name, ctor, methods, voids = observer.LAYOUT[row['uid']]
                iface = row['inferred_interface']
                self.assertEqual(name, iface['classname'])
                self.assertEqual(ctor, len(iface['constructor']['params']))
                self.assertEqual(methods, {m['name']: len(m['params']) for m in iface['methods']})
                self.assertEqual(voids, {m['name'] for m in iface['methods'] if m['return']['type'] == 'void'})

    def test_no_fallback_and_packet_bound(self):
        args = [['SubarrayFirstIterator', 'hasNext'], [[[], []], []]]
        with self.assertRaises(TypeError): observer.observe({'solve': lambda *a: [None, False]}, ITER, {'args': args}, transport)
        raw = protocol.packet(ITER, [{'args': args, 'expected': [None, False]}], maximum_bytes=10000)
        self.assertNotIn(b'expected', raw)
        with self.assertRaises(ValueError): protocol.packet(ITER, [{'args': args}], maximum_bytes=1)
        with self.assertRaises(ValueError): observer.shape(ITER, [['SubarrayFirstIterator', 'peek'], [[[], []], []]])


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
JS_KIND = {'bool': 'boolean', 'int': 'number', 'list': 'object', 'NoneType': 'undefined'}


class OwnJavascriptCandidatesThroughObserver(unittest.TestCase):
    """Author-local: own JS class candidates observed natively (node --jitless) against own generated cases."""
    def test_javascript_candidates(self):
        import shutil
        import subprocess
        if not shutil.which('node'): self.skipTest('node absent')
        total = 0
        for uid in observer.LAYOUT:
            rows = cases.build_cases(uid, include_maximum=True)
            job = {'uid': uid, 'path': str(ROOT / 'javascript' / (uid.split(':', 1)[1] + '.js')), 'cases': [r['args'] for r in rows]}
            res = subprocess.run(['node', '--jitless', '-e', JS_NATIVE, str(ROOT)], input=json.dumps(job), capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, res.stderr[-1500:])
            for row, got in zip(rows, json.loads(res.stdout)):
                self.assertTrue(protocol.exact(got['result'], row['expected']) and got['unchanged'], uid)
                kinds = ['constructed'] + [protocol.KIND[protocol.RETURNS[uid][op]][1] for op in row['args'][0][1:]]
                self.assertEqual(got['types'], kinds, uid)
                total += 1
        print(f'native javascript observations passed: {total}')

    def test_source_free_js_controls(self):
        import shutil
        import subprocess
        if not shutil.which('node'): self.skipTest('node absent')
        res = subprocess.run(['node', str(ROOT / 'test_native_observer.cjs')], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr[-1500:])


if __name__ == '__main__': unittest.main()
