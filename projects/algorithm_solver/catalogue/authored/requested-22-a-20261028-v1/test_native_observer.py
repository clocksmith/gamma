"""Direct observer controls with local toy classes; never load numbered sources."""
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


observer = load('gamma_r22a_native_observer', ROOT / 'native_harness.py')
protocol = load('gamma_r22a_native_protocol', ROOT / 'native_protocol.py')
transport = load('gamma_r22a_observation_transport', ROOT.parents[1] / 'public-domain-qualification-easy16-v1/harness.py')


class NativeObserverTests(unittest.TestCase):
    def test_same_receiver_and_new_instance_between_traces(self):
        created, receivers = [], []
        class MyCalendarThree:
            def __init__(self): self.count = 0; created.append(self)
            def book(self, startTime, endTime): self.count += 1; receivers.append(self); return self.count
        def forbidden_solve(*args): raise AssertionError('functional fallback must never execute')
        args = [['MyCalendarThree', 'book', 'book'], [[], [1, 2], [3, 4]]]
        for _ in range(2):
            record = observer.observe({'MyCalendarThree': MyCalendarThree, 'solve': forbidden_solve}, 732, {'args': args}, transport)
            self.assertIsNone(protocol.check(732, args, record, [None, 1, 2], 'python'))
        self.assertEqual(len(created), 2)
        self.assertTrue(receivers[0] is receivers[1] is created[0] and receivers[2] is receivers[3] is created[1])

    def test_layouts_bind_exact_official_methods(self):
        for row in json.loads((ROOT / 'contracts.json').read_text())['problems']:
            if row['id'] in observer.LAYOUT:
                name, methods, _ = observer.LAYOUT[row['id']]
                self.assertEqual(name, row['official_interface']['classname'])
                self.assertEqual(methods, {m['name']: len(m['params']) for m in row['official_interface']['methods']})

    def test_no_fallback_wrong_return_type_and_packet_bound(self):
        args = [['MyCalendar', 'book'], [[], [1, 2]]]
        with self.assertRaises(TypeError): observer.observe({'solve': lambda *a: [None, True]}, 729, {'args': args}, transport)
        class MyCalendar:
            def book(self, startTime, endTime): return 1
        record = observer.observe({'MyCalendar': MyCalendar}, 729, {'args': args}, transport)
        self.assertEqual(protocol.check(729, args, record, [None, True], 'python'), 'wrong_answer')
        raw = protocol.packet(729, [{'args': args, 'expected': [None, True]}], maximum_bytes=10000)
        self.assertNotIn(b'expected', raw)
        with self.assertRaises(ValueError): protocol.packet(729, [{'args': args}], maximum_bytes=1)
        with self.assertRaises(ValueError): observer.shape(729, [['MyCalendar', 'cancel'], [[], [1]]])


if __name__ == '__main__': unittest.main()
