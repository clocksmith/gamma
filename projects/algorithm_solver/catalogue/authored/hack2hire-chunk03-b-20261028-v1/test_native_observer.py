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


observer = load('gamma_h2h03b_native_observer', ROOT / 'native_harness.py')
protocol = load('gamma_h2h03b_native_protocol', ROOT / 'native_protocol.py')
cases = load('gamma_h2h03b_native_cases', ROOT / 'cases.py')
transport = load('gamma_h2h03b_observation_transport', ROOT.parents[1] / 'public-domain-qualification-easy16-v1/harness.py')
M1 = 'hack2hire:691e23ea08ad7861624b569b'
M2 = 'hack2hire:691e30e108ad7861624b56aa'


class NativeObserverTests(unittest.TestCase):
    def test_same_receiver_and_void_normalisation(self):
        created, receivers = [], []

        class MusicPlayer:
            def __init__(self): self.titles = []; self.users = {}; created.append(self)
            def addSong(self, title): receivers.append(self); self.titles.append(title); return len(self.titles)
            def playSong(self, songId, userId): receivers.append(self); self.users.setdefault(songId, set()).add(userId)
            def getAnalytics(self): return [[t, len(self.users.get(i + 1, ()))] for i, t in enumerate(self.titles)]
        args = [['MusicPlayer', 'addSong', 'playSong', 'getAnalytics'], [[], ['A'], [1, 4], []]]
        for _ in range(2):
            record = observer.observe({'MusicPlayer': MusicPlayer, 'solve': lambda *a: 1 / 0}, M1, {'args': args}, transport)
            self.assertIsNone(protocol.check(M1, args, record, [None, 1, None, [['A', 1]]], 'python'))
        self.assertEqual(len(created), 2)
        self.assertTrue(receivers[0] is receivers[1] is created[0] and receivers[2] is receivers[3] is created[1])

    def test_return_types_checked(self):
        class MusicPlayer:
            def __init__(self): pass
            def addSong(self, title): return True  # wrong kind: boolean instead of integer
            def playSong(self, songId, userId): return None
            def getAnalytics(self): return []
        args = [['MusicPlayer', 'addSong'], [[], ['A']]]
        record = observer.observe({'MusicPlayer': MusicPlayer}, M1, {'args': args}, transport)
        self.assertEqual(protocol.check(M1, args, record, [None, 1], 'python'), 'wrong_answer')

        class Leaky(MusicPlayer):
            def addSong(self, title): return 1
            def playSong(self, songId, userId): return 0  # void method returning a value
        args = [['MusicPlayer', 'addSong', 'playSong'], [[], ['A'], [1, 1]]]
        record = observer.observe({'MusicPlayer': Leaky}, M1, {'args': args}, transport)
        self.assertEqual(protocol.check(M1, args, record, [None, 1, None], 'python'), 'native_return_type')

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
        args = [['MusicPlayer', 'getAnalytics'], [[], []]]
        with self.assertRaises(TypeError): observer.observe({'solve': lambda *a: [None, []]}, M1, {'args': args}, transport)
        raw = protocol.packet(M1, [{'args': args, 'expected': [None, []]}], maximum_bytes=10000)
        self.assertNotIn(b'expected', raw)
        with self.assertRaises(ValueError): protocol.packet(M1, [{'args': args}], maximum_bytes=1)
        with self.assertRaises(ValueError): observer.shape(M1, [['MusicPlayer', 'getLastThreeSongs'], [[], [1]]])
        observer.shape(M2, [['MusicPlayer', 'getLastThreeSongs'], [[], [1]]])


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
