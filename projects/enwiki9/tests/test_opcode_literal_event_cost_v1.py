from fractions import Fraction
import hashlib
import lzma
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.opcode_literal_event_cost_v1 import literal_event_costs


class EventCostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        packed = (ROOT / 'programs/opcode_field_compact_v1/p').read_bytes()
        assert hashlib.sha256(packed).hexdigest() == '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8'
        ns = {'__name__': 'authenticated_event_cost_parent'}
        exec(compile(lzma.decompress(packed), '<compact-parent>', 'exec'), ns)
        cls.CM = ns['CM']

    def compare_sequential(self, models, keys):
        before = {k: (tuple(v.c), v.t) for k, v in models.items()}
        expected, sequential = [], {}
        for key in keys:
            if key not in sequential:
                sequential[key] = self.CM(3)
                if key in models:
                    sequential[key].c = list(models[key].c)
                    sequential[key].t = models[key].t
            model = sequential[key]
            _, frequency, total = model.cf(0)
            expected.append((frequency, total))
            model.up(0)
        costs, actual = literal_event_costs(models, keys)
        self.assertEqual(actual, expected)
        self.assertEqual({k: (tuple(v.c), v.t) for k, v in models.items()}, before)
        self.assertEqual(len(costs), len(keys) + 1)
        return costs, actual

    def test_exact_repeated_context_counterexample(self):
        _, probabilities = self.compare_sequential({}, ['same'] * 10)
        actual = Fraction(1)
        for frequency, total in probabilities:
            actual *= Fraction(frequency, total)
        static = Fraction(1, 3) ** 10
        self.assertEqual(actual, Fraction(1, 66))
        self.assertEqual(static, Fraction(1, 59049))
        self.assertGreater(actual, static)

    def test_interleaved_contexts_and_existing_counts(self):
        model = self.CM(3)
        for symbol in (0, 2, 1, 0, 0):
            model.up(symbol)
        self.compare_sequential({'a': model}, ['a', 'b', 'a', 'c', 'b', 'a'])

    def test_rescaling_uses_original_count_law(self):
        model = self.CM(3)
        model.c = [4090, 3, 3]
        model.t = 4096
        _, probabilities = self.compare_sequential({'a': model}, ['a'] * 258)
        self.assertEqual(probabilities[1], (2046, 2050))

    def test_bounds_and_invalid_count_state(self):
        self.assertEqual(literal_event_costs({}, []), ([0.0], []))
        with self.assertRaises(ValueError):
            literal_event_costs({}, ['a'] * 259)
        model = self.CM(3)
        model.t = 4
        with self.assertRaises(ValueError):
            literal_event_costs({'a': model}, ['a'])


if __name__ == '__main__':
    unittest.main()
