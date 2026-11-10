"""Independent hand cases and algebraic checks for host-only synthetic oracles."""
import dataclasses
import itertools
import json
import unittest
from algsolve.synth import direct_bits_oracles as o


class DirectBitsOracleTests(unittest.TestCase):
    def test_hand_computed_all_tasks(self):
        a = [2, -3, 0, 2, -2, 1]
        answers = {
            'sum': 0, 'count_positive': 3, 'sum_positive_squares': 9,
            'sum_squares': 22, 'sum_absolute': 10, 'count_nonzero': 5,
            'product': 0, 'sum_negative': -5, 'sum_incremented': 6,
            'filter_positive': [2, 2, 1], 'filter_negative': [-3, -2],
            'filter_nonzero': [2, -3, 2, -2, 1],
            'map_square': [4, 9, 0, 4, 4, 1],
            'map_negate': [-2, 3, 0, -2, 2, -1],
            'map_absolute': [2, 3, 0, 2, 2, 1],
            'map_double': [4, -6, 0, 4, -4, 2],
            'map_increment': [3, -2, 1, 3, -1, 2],
            'prefix_sum': [2, -1, -1, 1, -1, 0],
            'sort_ascending': [-3, -2, 0, 1, 2, 2],
            'sort_descending': [2, 2, 1, 0, -2, -3],
            'stable_distinct': [2, -3, 0, -2, 1],
            'sorted_distinct': [-3, -2, 0, 1, 2],
            'stable_distinct_absolute': [2, 3, 0, 1],
            'stable_distinct_squares': [4, 9, 0, 1],
            'reverse_input': [1, -2, 2, 0, -3, 2],
            'adjacent_differences': [-5, 3, 2, -4, 3],
        }
        self.assertEqual(set(answers), {t.name for t in o.tasks()})
        for name, answer in answers.items():
            with self.subTest(name=name):
                self.assertEqual(o.expected(name, a), answer)
                self.assertEqual(a, [2, -3, 0, 2, -2, 1])
        self.assertEqual(o.expected('product', []), 1)
        self.assertEqual(o.expected('product', [-2, 3, -4]), 24)

    def test_domains_splits_reproducibility_and_numeric_bounds(self):
        tasks = o.tasks()
        self.assertEqual(tasks, o.tasks())
        train_inputs = [c.inputs for c in tasks[0].train_cases]
        for task in tasks:
            with self.subTest(name=task.name):
                self.assertEqual([c.inputs for c in task.train_cases], train_inputs)
                train = {tuple(c.inputs[0]) for c in task.train_cases}
                evaluation = {tuple(c.inputs[0]) for c in task.evaluation_cases}
                self.assertFalse(train & evaluation)
                self.assertEqual(len(evaluation), len(task.evaluation_cases))
                self.assertLessEqual(len(evaluation), 1500)
                small = {a for n in range(5) for a in itertools.product(range(-2, 3), repeat=n)}
                self.assertTrue(small <= train | evaluation)
                self.assertEqual({c.category for c in task.evaluation_cases},
                                 {'exhaustive-small', 'domain-boundary', 'seeded-varied'})
                for case in task.train_cases + task.evaluation_cases:
                    self.assertEqual(len(case.inputs), 1)
                    task.domain.validate(case.inputs[0])
                    self.assertEqual(case.expected, o.expected(task.name, case.inputs[0]))
                    values = [case.expected] if type(case.expected) is int else case.expected
                    self.assertTrue(all(type(x) is int and -(2**127) <= x < 2**127 for x in values))
                self.assertTrue(all(c.split == 'train' for c in task.train_cases))
                self.assertTrue(all(c.split == 'evaluation' for c in task.evaluation_cases))

    def test_contract_binding_and_fresh_objects(self):
        task = o.tasks()[0]
        self.assertEqual(len(task.contract_hash()), 64)
        json.dumps(task.contract())
        self.assertNotEqual(task.contract_hash(), dataclasses.replace(task, budget=1).contract_hash())
        self.assertNotEqual(task.contract_hash(), dataclasses.replace(task, description='changed').contract_hash())
        before = task.contract_hash()
        task.train_cases[0].inputs[0].append(1)
        self.assertNotEqual(before, task.contract_hash())
        self.assertEqual(o.tasks()[0].train_cases[0].inputs, ([],))
        task = o.tasks()[0]
        before = task.contract_hash()
        task.evaluation_cases[0].expected.append(99)
        self.assertNotEqual(before, task.contract_hash())

    def test_fail_closed_inputs(self):
        for value in ([True], [1.0], [1_000_001], [0]*33, (1,), None):
            with self.assertRaises(ValueError):
                o.expected('sum', value)
        for value in ([9], [0]*17):
            with self.assertRaises(ValueError):
                o.expected('product', value)
        with self.assertRaises(KeyError):
            o.expected('not-a-task', [])

    def test_second_method_and_metamorphic_checks(self):
        for values in itertools.product((-2, 0, 3), repeat=4):
            a = list(values)
            prefix = o.expected('prefix_sum', a)
            self.assertEqual(prefix, [sum(a[:i]) for i in range(1, len(a)+1)])
            self.assertEqual(o.expected('sum_incremented', a), sum(a)+len(a))
            self.assertEqual(o.expected('sum_absolute', a),
                             o.expected('sum', a)-2*o.expected('sum_negative', a))
            self.assertEqual(o.expected('sum_squares', a), sum(x**2 for x in a))
            for task, transform in (('stable_distinct', lambda x: x),
                                    ('stable_distinct_absolute', abs),
                                    ('stable_distinct_squares', lambda x: x*x)):
                reference = []
                for x in a:
                    y = transform(x)
                    if y not in reference:
                        reference.append(y)
                self.assertEqual(o.expected(task, a), reference)
            sorted_a = o.expected('sort_ascending', a)
            self.assertEqual(sorted_a, list(reversed(o.expected('sort_descending', a))))
            self.assertEqual(o.expected('reverse_input', o.expected('reverse_input', a)), a)
            self.assertEqual(sum(o.expected('adjacent_differences', a)), a[-1]-a[0])


if __name__ == '__main__':
    unittest.main()
