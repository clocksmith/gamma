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


observer = load('direct_native_observer', ROOT / 'native_harness.py')
protocol = load('direct_native_protocol', ROOT / 'native_protocol.py')
transport = load('existing_observation_transport', ROOT.parents[1] / 'public-domain-qualification-easy16-v1/harness.py')


class NativeObserverTests(unittest.TestCase):
    def test_same_receiver_native_methods_and_new_instance_between_traces(self):
        created, receivers = [], []
        class ExamTracker:
            def __init__(self): self.count = 0; created.append(self)
            def record(self, time, score): self.count += 1; receivers.append(self)
            def totalScore(self, startTime, endTime): receivers.append(self); return self.count
        def forbidden_solve(*args): raise AssertionError('functional fallback must never execute')
        args = [['ExamTracker', 'record', 'record', 'totalScore'], [[], [1, 1], [2, 1], [1, 2]]]
        for _ in range(2):
            record = observer.observe({'ExamTracker': ExamTracker, 'solve': forbidden_solve}, 3709, {'args': args}, transport)
            self.assertEqual(record['result'], [None, None, None, 2])
            self.assertIsNone(protocol.check(3709, args, record, [None, None, None, 2], 'python'))
        self.assertEqual(len(created), 2)
        self.assertTrue(all(x is created[0] for x in receivers[:3]))
        self.assertTrue(all(x is created[1] for x in receivers[3:]))

    def test_all_three_layouts_bind_exact_official_methods(self):
        contract = json.loads((ROOT / 'contracts.json').read_text())
        for row in contract['problems']:
            name, methods, _ = observer.LAYOUT[row['id']]
            self.assertEqual(name, row['native_interface']['classname'])
            self.assertEqual(methods, {m['name']: len(m['params']) for m in row['native_interface']['methods']})

    def test_auction_and_rider_routes_dispatch_on_their_native_receivers(self):
        class AuctionSystem:
            def __init__(self): self.events = 0
            def addBid(self, *args): self.events += 1
            def updateBid(self, *args): self.events += 1
            def removeBid(self, *args): self.events += 1
            def getHighestBidder(self, *args): return self.events
        args = [['AuctionSystem', 'addBid', 'updateBid', 'removeBid', 'getHighestBidder'],
                [[], [1, 1, 1], [1, 1, 2], [1, 1], [1]]]
        row = observer.observe({'AuctionSystem': AuctionSystem}, 3815, {'args': args}, transport)
        self.assertEqual(row['result'], [None, None, None, None, 3])
        class RideSharingSystem:
            def __init__(self): self.events = 0
            def addRider(self, *args): self.events += 1
            def addDriver(self, *args): self.events += 1
            def cancelRider(self, *args): self.events += 1
            def matchDriverWithRider(self, *args): return [self.events, self.events]
        args = [['RideSharingSystem', 'addRider', 'addDriver', 'matchDriverWithRider'], [[], [2], [2], []]]
        row = observer.observe({'RideSharingSystem': RideSharingSystem}, 3829, {'args': args}, transport)
        self.assertEqual(row['result'], [None, None, None, [2, 2]])

    def test_expected_outputs_never_enter_packet_or_call_shape(self):
        args = [['ExamTracker', 'record', 'totalScore'], [[], [1, 9], [1, 1]]]
        raw = protocol.packet(3709, [{'args': args, 'expected': 7654321}], maximum_bytes=4096)
        self.assertNotIn(b'expected', raw); self.assertNotIn(b'7654321', raw)
        with self.assertRaises(ValueError): protocol.packet(3709, [{'args': args}], maximum_bytes=1)
        with self.assertRaises(ValueError): protocol.packet(3709, [{'args': args}], maximum_bytes=True)
        with self.assertRaises(ValueError): observer.observe({}, 3709, {'args': args, 'expected': 9}, transport)

    def test_no_fallback_or_constructor_injection(self):
        call = {'args': [['ExamTracker'], [[]]]}
        for namespace in ({}, {'solve': lambda: []}, {'ExamTracker': lambda: object()}):
            with self.assertRaises(TypeError): observer.observe(namespace, 3709, call, transport)

    def test_bad_arity_unknown_method_and_wrong_id_fail_before_constructing(self):
        class ExamTracker:
            def __init__(self): raise AssertionError('constructor should not run')
        for pid, args in [(3709, [['ExamTracker', 'record'], [[], [1]]]),
                          (3709, [['ExamTracker', '__init__'], [[], []]]),
                          (3815, [['ExamTracker'], [[]]]), (True, [['ExamTracker'], [[]]])]:
            with self.assertRaises(ValueError): observer.observe({'ExamTracker': ExamTracker}, pid, {'args': args}, transport)

    def test_constructor_factory_return_cannot_replace_native_instance(self):
        class ExamTracker:
            def __new__(cls): return object()
        with self.assertRaises(TypeError):
            observer.observe({'ExamTracker': ExamTracker}, 3709, {'args': [['ExamTracker'], [[]]]}, transport)

    def test_receiver_proof_snapshots_query_type_and_input_effect_mutants_rejected(self):
        args = [['AuctionSystem', 'getHighestBidder'], [[], [1]]]
        expected = [None, -1]
        record = dict(result=expected, result_type='list', args_before=args, args_after=args, alias_edges=[],
                      native_route='direct-class-v1', native_class='AuctionSystem', native_receiver_count=1,
                      native_method_return_types=['constructed', 'int'], native_method_snapshots=expected)
        self.assertIsNone(protocol.check(3815, args, record, expected, 'python'))
        for changes in ({'native_route': 'solve-trace-v1'}, {'native_class': 'ExamTracker'},
                        {'native_receiver_count': True}, {'native_receiver_count': 2},
                        {'native_method_return_types': ['constructed', 'float']},
                        {'native_method_snapshots': [None, True]}, {'args_after': [[], []]},
                        {'alias_edges': [['result.1', 'args.1.1']]}):
            self.assertIsNotNone(protocol.check(3815, args, record | changes, expected, 'python'))


if __name__ == '__main__': unittest.main()
