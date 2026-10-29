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


observer = load('gamma_h2h15a_native_observer', ROOT / 'native_harness.py')
protocol = load('gamma_h2h15a_native_protocol', ROOT / 'native_protocol.py')
cases = load('gamma_h2h15a_native_cases', ROOT / 'cases.py')
transport = load('gamma_h2h15a_observation_transport', ROOT.parents[1] / 'public-domain-qualification-easy16-v1/harness.py')
T = 'hack2hire:69334452e8ebbb1c53caf2c4'
R = 'hack2hire:692fc0f4cd79766b0b3101a0'


class Toy:
    """Source-free toy ArticleSystem (vote-log replay, full sort per ranking query)."""
    def __init__(self): self.names, self.votes, self.flips = [], {}, []

    def addArticle(self, articleName):
        self.names.append(articleName)
        return len(self.names)

    def vote(self, article, user, value):
        old = self.votes.get((user, article), 0)
        if old != value:
            self.votes[(user, article)] = value
            if old == -value: self.flips.append((user, article))

    def upvoteArticle(self, articleId, userId): self.vote(articleId, userId, 1)

    def downvoteArticle(self, articleId, userId): self.vote(articleId, userId, -1)

    def getRecentFlips(self, userId, k):
        seen = []
        for user, article in reversed(self.flips):
            if user == userId and article not in seen: seen.append(article)
        return [self.names[a - 1] for a in seen[:k]]

    def getTopArticles(self, k):
        score = {a: 0 for a in range(1, len(self.names) + 1)}
        for (_, article), value in self.votes.items(): score[article] += value
        return [self.names[a - 1] for a in sorted(score, key=lambda a: (-score[a], a))[:k]]


class NativeObserverTests(unittest.TestCase):
    def test_same_receiver_and_constructor_arguments(self):
        created, receivers = [], []

        class ArticleSystem(Toy):
            def __init__(self): super().__init__(); created.append(self)
            def addArticle(self, articleName): receivers.append(self); return super().addArticle(articleName)
            def getTopArticles(self, k): receivers.append(self); return super().getTopArticles(k)
        args = [['ArticleSystem', 'addArticle', 'getTopArticles'], [[], ['x'], [1]]]
        for _ in range(2):
            record = observer.observe({'ArticleSystem': ArticleSystem, 'solve': lambda *a: 1 / 0}, T, {'args': args}, transport)
            self.assertIsNone(protocol.check(T, args, record, [None, 1, ['x']], 'python'))
        self.assertEqual(len(created), 2)
        self.assertTrue(receivers[0] is receivers[1] is created[0] and receivers[2] is receivers[3] is created[1])

    def test_void_methods_and_return_types(self):
        args = [['ArticleSystem', 'addArticle', 'addArticle', 'downvoteArticle', 'getTopArticles'], [[], ['x'], ['y'], [1, 5], [2]]]
        want = [None, 1, 2, None, ['y', 'x']]
        record = observer.observe({'ArticleSystem': Toy}, T, {'args': args}, transport)
        self.assertIsNone(protocol.check(T, args, record, want, 'python'))

        class Wrong(Toy):
            def getTopArticles(self, k): return sorted(self.names)[:k]
        record = observer.observe({'ArticleSystem': Wrong}, T, {'args': args}, transport)
        self.assertEqual(protocol.check(T, args, record, want, 'python'), 'wrong_answer')

        class Leaky(Toy):
            def downvoteArticle(self, articleId, userId): super().downvoteArticle(articleId, userId); return len(self.votes)
        record = observer.observe({'ArticleSystem': Leaky}, T, {'args': args}, transport)
        self.assertEqual(protocol.check(T, args, record, want, 'python'), 'native_return_type')

        class BoolCount:
            def __init__(self, intervals): pass
            def count(self, x): return True
        args = [['IntervalCounter', 'count'], [[[[1, 2]]], [1]]]
        record = observer.observe({'IntervalCounter': BoolCount}, R, {'args': args}, transport)
        self.assertEqual(protocol.check(R, args, record, [None, 1], 'python'), 'wrong_answer')

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
        args = [['ArticleSystem', 'getTopArticles'], [[], [1]]]
        with self.assertRaises(TypeError): observer.observe({'solve': lambda *a: [None, []]}, T, {'args': args}, transport)
        raw = protocol.packet(T, [{'args': args, 'expected': [None, []]}], maximum_bytes=10000)
        self.assertNotIn(b'expected', raw)
        with self.assertRaises(ValueError): protocol.packet(T, [{'args': args}], maximum_bytes=1)
        with self.assertRaises(ValueError): observer.shape(T, [['ArticleSystem', 'clear'], [[], []]])


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
