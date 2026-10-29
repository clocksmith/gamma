"""Direct native observer: toy controls plus author-local self-check of own native classes; not qualification."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).parent
TRANSPORT = ROOT.parents[1] / 'public-domain-qualification-easy16-v1'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


observer = load('gamma_h2h02c_native_observer', ROOT / 'native_harness.py')
protocol = load('gamma_h2h02c_native_protocol', ROOT / 'native_protocol.py')
cases = load('gamma_h2h02c_native_cases', ROOT / 'cases.py')
transport = load('gamma_h2h02c_observation_transport', TRANSPORT / 'harness.py')
C4 = protocol.oracle.C4
JS_OBSERVE = r'''
const fs=require('fs');const job=JSON.parse(fs.readFileSync(0,'utf8'));
const h=require(job.harness),t=require(job.transport),m=require(job.program);const out=[];
for(const args of job.cases){let r;try{r=h.observe(m,job.uid,{args},t);}catch(e){r={error:String(e)};}out.push(r);}
process.stdout.write(JSON.stringify(out));'''


class NativeObserverTests(unittest.TestCase):
    def test_layouts_bind_inferred_methods(self):
        for uid, row in protocol.CONTRACTS.items():
            if uid in observer.LAYOUT:
                name, ctor, methods, voids = observer.LAYOUT[uid]
                iface = row['inferred_interface']
                self.assertEqual(name, iface['classname'])
                self.assertEqual(ctor, len(iface['constructor']['params']))
                self.assertEqual(methods, {m['name']: len(m['params']) for m in iface['methods']})
                self.assertEqual(voids, {m['name'] for m in iface['methods'] if m['return']['type'] == 'void'})

    def test_no_fallback_wrong_return_type_and_packet_bound(self):
        args = [['ConnectFour', 'play', 'play'], [[], [0], [7]]]
        with self.assertRaises(TypeError): observer.observe({'solve': lambda *a: [None, 'ONGOING', 'INVALID']}, C4, {'args': args}, transport)
        class ConnectFour:
            def play(self, column): return 1
        record = observer.observe({'ConnectFour': ConnectFour}, C4, {'args': args}, transport)
        self.assertEqual(protocol.check(C4, args, record, [None, 1, 1], 'python'), 'native_return_type')
        raw = protocol.packet(C4, [{'args': args, 'expected': [None, 'ONGOING', 'INVALID']}], maximum_bytes=10000)
        self.assertNotIn(b'expected', raw)
        with self.assertRaises(ValueError): protocol.packet(C4, [{'args': args}], maximum_bytes=1)
        with self.assertRaises(ValueError): observer.shape(C4, [['ConnectFour', 'reset'], [[], []]])

    def test_own_native_classes_python(self):
        for uid in observer.LAYOUT:
            namespace = {'__name__': 'candidate'}
            exec(compile((ROOT / 'python' / (uid.split(':')[1] + '.py')).read_text(), 'program.py', 'exec'), namespace)
            rows = cases.build_cases(uid, include_maximum=True)
            for row in rows:
                record = observer.observe(namespace, uid, {'args': row['args']}, transport)
                self.assertIsNone(protocol.check(uid, row['args'], record, row['expected'], 'python'), uid)
            print(f'{uid} python native observer {len(rows)}/{len(rows)}', flush=True)

    def test_own_native_classes_javascript(self):
        if not shutil.which('node'): self.skipTest('node absent')
        for uid in observer.LAYOUT:
            rows = cases.build_cases(uid, include_maximum=True)
            job = {'harness': str(ROOT / 'native_harness.cjs'), 'transport': str(TRANSPORT / 'harness.cjs'),
                   'program': str(ROOT / 'javascript' / (uid.split(':')[1] + '.js')), 'uid': uid, 'cases': [r['args'] for r in rows]}
            res = subprocess.run(['node', '-e', JS_OBSERVE], input=json.dumps(job), capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, res.stderr[-1500:])
            for row, record in zip(rows, json.loads(res.stdout)):
                self.assertIsNone(protocol.check(uid, row['args'], record, row['expected'], 'javascript'), uid)
            print(f'{uid} javascript native observer {len(rows)}/{len(rows)}', flush=True)


if __name__ == '__main__': unittest.main()
