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


observer = load('gamma_h2h13a_native_observer', ROOT / 'native_harness.py')
protocol = load('gamma_h2h13a_native_protocol', ROOT / 'native_protocol.py')
cases = load('gamma_h2h13a_native_cases', ROOT / 'cases.py')
transport = load('gamma_h2h13a_observation_transport', ROOT.parents[1] / 'public-domain-qualification-easy16-v1/harness.py')
OOV = 'hack2hire:688aefae3867670cfb894129'
PST = 'hack2hire:677f4db36fee41e51af73dd6'


class ToyTracker:
    """Source-free toy VisitorTracker (the whole log rescanned on every query)."""
    def __init__(self): self.log = []

    def login(self, username): self.log.append(username)

    def getOldestOneTimeVisitor(self): return next((u for u in self.log if self.log.count(u) == 1), '')


class ToyStack:
    """Source-free toy PStack (a full list copy per version)."""
    def __init__(self): self.versions, self.base = [[]], [None]

    def push(self, version, val): self.versions.append(self.versions[version] + [val]); self.base.append(version); return len(self.versions) - 1

    def pop(self, version): return self.base[version]

    def peek(self, version): return self.versions[version][-1]

    def size(self, version): return len(self.versions[version])


class NativeObserverTests(unittest.TestCase):
    def test_same_receiver_and_constructor_arguments(self):
        created, receivers = [], []

        class VisitorTracker(ToyTracker):
            def __init__(self): super().__init__(); created.append(self)
            def login(self, username): receivers.append(self); super().login(username)
            def getOldestOneTimeVisitor(self): receivers.append(self); return super().getOldestOneTimeVisitor()
        args = [['VisitorTracker', 'login', 'getOldestOneTimeVisitor'], [[], ['ann'], []]]
        for _ in range(2):
            record = observer.observe({'VisitorTracker': VisitorTracker, 'solve': lambda *a: 1 / 0}, OOV, {'args': args}, transport)
            self.assertIsNone(protocol.check(OOV, args, record, [None, None, 'ann'], 'python'))
        self.assertEqual(len(created), 2)
        self.assertTrue(receivers[0] is receivers[1] is created[0] and receivers[2] is receivers[3] is created[1])

    def test_void_methods_and_return_types(self):
        args = [['VisitorTracker', 'login', 'login', 'login', 'getOldestOneTimeVisitor'], [[], ['ann'], ['bo'], ['ann'], []]]
        record = observer.observe({'VisitorTracker': ToyTracker}, OOV, {'args': args}, transport)
        self.assertIsNone(protocol.check(OOV, args, record, [None, None, None, None, 'bo'], 'python'))

        class Wrong(ToyTracker):
            def getOldestOneTimeVisitor(self): return self.log[0]
        record = observer.observe({'VisitorTracker': Wrong}, OOV, {'args': args}, transport)
        self.assertEqual(protocol.check(OOV, args, record, [None, None, None, None, 'bo'], 'python'), 'wrong_answer')

        class Leaky(ToyTracker):
            def login(self, username): super().login(username); return len(self.log)
        record = observer.observe({'VisitorTracker': Leaky}, OOV, {'args': args}, transport)
        self.assertEqual(protocol.check(OOV, args, record, [None, None, None, None, 'bo'], 'python'), 'native_return_type')

        sargs = [['PStack', 'push', 'push', 'peek', 'pop', 'size'], [[], [0, 4], [1, 2], [2], [2], [1]]]
        record = observer.observe({'PStack': ToyStack}, PST, {'args': sargs}, transport)
        self.assertIsNone(protocol.check(PST, sargs, record, [None, 1, 2, 2, 1, 1], 'python'))

        class FloatSize(ToyStack):
            def size(self, version): return float(super().size(version))
        record = observer.observe({'PStack': FloatSize}, PST, {'args': sargs}, transport)
        self.assertEqual(protocol.check(PST, sargs, record, [None, 1, 2, 2, 1, 1], 'python'), 'wrong_answer')

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
        args = [['PStack', 'push', 'peek'], [[], [0, 3], [1]]]
        with self.assertRaises(TypeError): observer.observe({'solve': lambda *a: [None, 1, 3]}, PST, {'args': args}, transport)
        raw = protocol.packet(PST, [{'args': args, 'expected': [None, 1, 3]}], maximum_bytes=10000)
        self.assertNotIn(b'expected', raw)
        with self.assertRaises(ValueError): protocol.packet(PST, [{'args': args}], maximum_bytes=1)
        with self.assertRaises(ValueError): observer.shape(PST, [['PStack', 'clear'], [[], []]])


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
