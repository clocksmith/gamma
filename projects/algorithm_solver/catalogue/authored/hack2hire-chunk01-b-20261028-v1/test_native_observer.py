"""Direct observer controls with local toy classes, plus an author-local run of the authored BufferedFile candidates."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parent
UID = 'hack2hire:695aed975242f618a4d2fa2f'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


observer = load('gamma_h2h_c01b_native_observer', ROOT / 'native_harness.py')
protocol = load('gamma_h2h_c01b_native_protocol', ROOT / 'native_protocol.py')
cases = load('gamma_h2h_c01b_native_cases', ROOT / 'cases.py')
transport = load('gamma_h2h_c01b_observation_transport', ROOT.parents[1] / 'public-domain-qualification-easy16-v1/harness.py')


class NativeObserverTests(unittest.TestCase):
    def test_same_receiver_and_new_instance_between_traces(self):
        created, receivers = [], []
        class BufferedFile:
            def __init__(self, capacity): self.capacity, self.held = capacity, []; created.append(self)
            def write(self, data):
                receivers.append(self); self.held += data; out = []
                while len(self.held) >= self.capacity: out += self.held[:self.capacity]; self.held = self.held[self.capacity:]
                return out
            def flush(self): receivers.append(self); out, self.held = self.held, []; return out
        def forbidden_solve(*args): raise AssertionError('functional fallback must never execute')
        args = [['BufferedFile', 'write', 'flush'], [[2], [[1, 2, 3]], []]]
        for _ in range(2):
            record = observer.observe({'BufferedFile': BufferedFile, 'solve': forbidden_solve}, UID, {'args': args}, transport)
            self.assertIsNone(protocol.check(UID, args, record, [None, [1, 2], [3]], 'python'))
        self.assertEqual(len(created), 2)
        self.assertTrue(receivers[0] is receivers[1] is created[0] and receivers[2] is receivers[3] is created[1])

    def test_layout_binds_inferred_methods(self):
        for row in json.loads((ROOT / 'contracts.json').read_text())['problems']:
            if row['uid'] in observer.LAYOUT:
                name, methods, _, ctor = observer.LAYOUT[row['uid']]
                iface = row['inferred_interface']
                self.assertEqual(name, iface['classname'])
                self.assertEqual(methods, {m['name']: len(m['params']) for m in iface['methods']})
                self.assertEqual(ctor, len(iface['constructor']['params']))

    def test_no_fallback_aliasing_and_packet_bound(self):
        args = [['BufferedFile', 'write'], [[1], [[5]]]]
        with self.assertRaises(TypeError): observer.observe({'solve': lambda *a: [None, [5]]}, UID, {'args': args}, transport)
        class BufferedFile:
            def __init__(self, capacity): pass
            def write(self, data): return data  # aliases the caller's argument
            def flush(self): return []
        record = observer.observe({'BufferedFile': BufferedFile}, UID, {'args': args}, transport)
        self.assertEqual(protocol.check(UID, args, record, [None, [5]], 'python'), 'effects')
        raw = protocol.packet(UID, [{'args': args, 'expected': [None, [5]]}], maximum_bytes=10000)
        self.assertNotIn(b'expected', raw)
        with self.assertRaises(ValueError): protocol.packet(UID, [{'args': args}], maximum_bytes=1)
        with self.assertRaises(ValueError): observer.shape(UID, [['BufferedFile', 'close'], [[1], []]])
        with self.assertRaises(ValueError): observer.shape(UID, [['BufferedFile'], [[]]])

    def test_authored_candidate_through_observer(self):
        """Author-local, not isolated qualification: the authored Python class through observe() on all generated rows."""
        namespace = {'__name__': 'candidate'}
        source = (ROOT / 'python' / '695aed975242f618a4d2fa2f.py').read_text()
        exec(compile(source, 'program.py', 'exec'), namespace)
        rows = cases.build_cases(UID, include_maximum=True)
        for row in rows:
            record = observer.observe(namespace, UID, {'args': row['args']}, transport)
            self.assertIsNone(protocol.check(UID, row['args'], record, row['expected'], 'python'))
        print(f'BufferedFile python native observer {len(rows)}/{len(rows)} passed')


if __name__ == '__main__': unittest.main()
