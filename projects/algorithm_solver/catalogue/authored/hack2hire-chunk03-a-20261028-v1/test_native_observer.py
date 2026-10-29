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


observer = load('gamma_h2h03a_native_observer', ROOT / 'native_harness.py')
protocol = load('gamma_h2h03a_native_protocol', ROOT / 'native_protocol.py')
cases = load('gamma_h2h03a_native_cases', ROOT / 'cases.py')
transport = load('gamma_h2h03a_observation_transport', ROOT.parents[1] / 'public-domain-qualification-easy16-v1/harness.py')
ILV = 'hack2hire:678d6982fa7ce9616e190fb3'


class NativeObserverTests(unittest.TestCase):
    def test_same_receiver_and_constructor_arguments(self):
        created, receivers = [], []

        class InterleaveIterator:
            def __init__(self, arrays, cycle): self.values = [v for a in arrays for v in a]; created.append(self)
            def hasNext(self): receivers.append(self); return bool(self.values)
            def next(self): receivers.append(self); return self.values.pop(0) if self.values else None
        args = [['InterleaveIterator', 'next', 'hasNext', 'next'], [[[[7]], False], [], [], []]]
        for _ in range(2):
            record = observer.observe({'InterleaveIterator': InterleaveIterator, 'solve': lambda *a: 1 / 0}, ILV, {'args': args}, transport)
            self.assertIsNone(protocol.check(ILV, args, record, [None, 7, False, None], 'python'))
        self.assertEqual(len(created), 2)
        self.assertTrue(all(r is created[0] for r in receivers[:3]) and all(r is created[1] for r in receivers[3:]))

    def test_wrong_return_kind_and_answer(self):
        class InterleaveIterator:
            def __init__(self, arrays, cycle): pass
            def hasNext(self): return 0
            def next(self): return None
        args = [['InterleaveIterator', 'hasNext'], [[[], False], []]]
        record = observer.observe({'InterleaveIterator': InterleaveIterator}, ILV, {'args': args}, transport)
        self.assertEqual(protocol.check(ILV, args, record, [None, False], 'python'), 'wrong_answer')
        record['result'] = [None, False]; record['native_method_snapshots'] = [None, False]
        self.assertEqual(protocol.check(ILV, args, record, [None, False], 'python'), 'native_return_type')

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
        args = [['InterleaveIterator', 'next'], [[[], True], []]]
        with self.assertRaises(TypeError): observer.observe({'solve': lambda *a: [None, None]}, ILV, {'args': args}, transport)
        raw = protocol.packet(ILV, [{'args': args, 'expected': [None, None]}], maximum_bytes=10000)
        self.assertNotIn(b'expected', raw)
        with self.assertRaises(ValueError): protocol.packet(ILV, [{'args': args}], maximum_bytes=1)
        with self.assertRaises(ValueError): observer.shape(ILV, [['InterleaveIterator', 'peek'], [[[], True], []]])


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
                self.assertTrue(protocol.kinds_match(uid, row['args'][0], got['types'], 'javascript'), uid)
                total += 1
        print(f'native javascript observations passed: {total}')

    def test_source_free_js_controls(self):
        import shutil
        import subprocess
        if not shutil.which('node'): self.skipTest('node absent')
        res = subprocess.run(['node', str(ROOT / 'test_native_observer.cjs')], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr[-1500:])


if __name__ == '__main__': unittest.main()
