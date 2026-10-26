"""Failure-oriented checks for the independent import execution boundary."""
import json
import unittest

from . import imported_qualification as q


class VerificationTests(unittest.TestCase):
    def record(self, result=7, kind='int'):
        return {'i': 0, 'result': result, 'result_type': kind,
                'args_before': [3, 4], 'args_after': [3, 4], 'alias_edges': []}

    def test_numeric_bool_and_container_types(self):
        case = {'args': [3, 4], 'expected': 7}
        self.assertIsNone(q.compare(case, self.record(), 'python'))
        self.assertEqual(q.compare(case, self.record(True, 'bool'), 'python'), 'result_type')
        self.assertEqual(q.compare(case, self.record(7.0), 'python'), 'result_value')
        self.assertEqual(q.expected_type([], 'javascript'), 'object')

    def test_input_mutation_and_return_alias_are_failures(self):
        case = {'args': [3, 4], 'expected': 7}
        record = self.record(); record['args_after'] = [4, 3]
        self.assertEqual(q.compare(case, record, 'python'), 'input_effects')
        record = self.record(); record['alias_edges'] = [['result', 'args.0']]
        self.assertEqual(q.compare(case, record, 'python'), 'return_aliases')

    def test_complete_ordered_observation_protocol(self):
        cases = [{'args': [3, 4], 'expected': 7}]
        good = q.encoded(self.record()) + q.encoded({'done': 1})
        self.assertEqual(q.check_output(good, cases, 'python'), [])
        for bad in [q.encoded(self.record()), good + good, q.encoded({'done': 1}),
                    q.encoded(dict(self.record(), i=True)) + q.encoded({'done': 1})]:
            with self.assertRaises(ValueError):
                q.check_output(bad, cases, 'python')

    def test_duplicate_fields_and_nonfinite_are_rejected(self):
        for raw in [b'{"i":0,"i":1}', b'{"result":NaN}']:
            with self.assertRaises(ValueError):
                q.decode(raw)

    def test_packet_never_contains_expected_answers(self):
        cases = [{'args': [1], 'expected': 987654321, 'compare': 'return'}]
        value = q.packet(cases)
        self.assertEqual(value['calls'], [{'args': [1]}])
        self.assertNotIn('987654321', json.dumps(value))

    def test_oversize_case_is_not_silently_dropped(self):
        with self.assertRaisesRegex(ValueError, 'cap'):
            list(q.batches([{'args': ['x' * q.MAX_PACKET]}]))
        cases = [{'args': [i]} for i in range(65)]
        groups = list(q.batches(cases))
        self.assertEqual([o for o, _ in groups], [0, 32, 64])
        self.assertEqual([c for _, group in groups for c in group], cases)


if __name__ == '__main__':
    unittest.main()
