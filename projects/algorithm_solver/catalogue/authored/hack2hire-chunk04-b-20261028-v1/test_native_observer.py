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


observer = load('gamma_h2h04b_native_observer', ROOT / 'native_harness.py')
protocol = load('gamma_h2h04b_native_protocol', ROOT / 'native_protocol.py')
cases = load('gamma_h2h04b_native_cases', ROOT / 'cases.py')
transport = load('gamma_h2h04b_observation_transport', ROOT.parents[1] / 'public-domain-qualification-easy16-v1/harness.py')
C1 = 'hack2hire:6a579fe2665efda9311f9375'
C2 = 'hack2hire:6a579fe4665efda9311f9376'


class NativeObserverTests(unittest.TestCase):
    def test_same_receiver_and_constructor_arguments(self):
        created, receivers = [], []

        class ChatEventAggregator:
            def __init__(self, m): self.m = m; self.seen = []; created.append(self)
            def recordEvent(self, timestamp, userId, chatId): receivers.append(self); self.seen.append((timestamp, userId))
            def getUserCount(self, timestamp, userId):
                receivers.append(self); return sum(1 for t, u in self.seen if u == userId and t > timestamp - self.m)
        args = [['ChatEventAggregator', 'recordEvent', 'getUserCount'], [[5], [1, 'al', 'c'], [3, 'al']]]
        for _ in range(2):
            record = observer.observe({'ChatEventAggregator': ChatEventAggregator, 'solve': lambda *a: 1 / 0}, C1, {'args': args}, transport)
            self.assertIsNone(protocol.check(C1, args, record, [None, None, 1], 'python'))
        self.assertEqual(len(created), 2)
        self.assertTrue(receivers[0] is receivers[1] is created[0] and receivers[2] is receivers[3] is created[1])

    def test_void_methods_and_return_types(self):
        class ChatEventAggregator:
            def __init__(self, m): self.n = 0
            def recordEvent(self, timestamp, userId, chatId): self.n += 1
            def getUserCount(self, timestamp, userId): return self.n
            def getChatCount(self, timestamp, chatId): return self.n
        args = [['ChatEventAggregator', 'recordEvent', 'getChatCount'], [[3], [0, 'al', 'c1'], [0, 'c1']]]
        record = observer.observe({'ChatEventAggregator': ChatEventAggregator}, C2, {'args': args}, transport)
        self.assertIsNone(protocol.check(C2, args, record, [None, None, 1], 'python'))

        class Wrong(ChatEventAggregator):
            def getChatCount(self, timestamp, chatId): return True
        record = observer.observe({'ChatEventAggregator': Wrong}, C2, {'args': args}, transport)
        self.assertEqual(protocol.check(C2, args, record, [None, None, 1], 'python'), 'wrong_answer')

        class Leaky(ChatEventAggregator):
            def recordEvent(self, timestamp, userId, chatId): self.n += 1; return self.n
        record = observer.observe({'ChatEventAggregator': Leaky}, C2, {'args': args}, transport)
        self.assertEqual(protocol.check(C2, args, record, [None, None, 1], 'python'), 'native_return_type')

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
        args = [['ChatEventAggregator', 'getUserCount'], [[1], [0, 'al']]]
        with self.assertRaises(TypeError): observer.observe({'solve': lambda *a: [None, 0]}, C1, {'args': args}, transport)
        raw = protocol.packet(C1, [{'args': args, 'expected': [None, 0]}], maximum_bytes=10000)
        self.assertNotIn(b'expected', raw)
        with self.assertRaises(ValueError): protocol.packet(C1, [{'args': args}], maximum_bytes=1)
        with self.assertRaises(ValueError): observer.shape(C1, [['ChatEventAggregator', 'getChatCount'], [[1], [0, 'c1']]])


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
