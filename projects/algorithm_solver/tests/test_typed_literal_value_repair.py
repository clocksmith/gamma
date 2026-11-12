import time
import unittest

from algsolve.synth import typed_program
from algsolve.synth.typed_literal_value_repair import POLICY, literal_value_search
from algsolve.synth.typed_prediction_codec import OPS, PredictionCodec
from test_typed_comparison import pair, graph, capture


class LiteralValueRepairTests(unittest.TestCase):
    def setUp(self):
        self.encoding = PredictionCodec.fit([pair(), pair(7)])
        self.codes, _ = capture(self.encoding, graph(0))
        self.slot = next(i for i, v in enumerate(self.codes['op']) if OPS[v] == 'int')
        self.logits = [[10. if bit else -10. for bit in row] for row in self.codes['bits']]
        self.logits[self.slot][1] = -.1
        self.logits[self.slot][2] = -.2
        self.config = dict(pool_size=8, max_edits=2, max_executions=4, wall_seconds=.25)

    def search(self, evaluate):
        return literal_value_search(self.encoding, self.codes, self.logits, ['x'], self.config,
                                    evaluate, deadline=time.perf_counter() + 1)

    def test_reaches_a_small_value_and_reports_field_and_bit_edits(self):
        seen = []
        def evaluate(program, seconds):
            value = typed_program.execute(program, {'x': 0}); seen.append(value)
            return dict(passed=value == 2, reason=None if value == 2 else 'wrong_answer')
        result = self.search(evaluate)
        self.assertEqual(result['policy'], POLICY)
        self.assertEqual(result['reason'], 'literal_public_passed')
        self.assertEqual(seen[-1], 2)
        final = result['attempts'][-1]
        self.assertEqual(final['field_edits'], 1)
        self.assertEqual(final['bit_changes'], 1)
        self.assertEqual(final['edits'][0]['after'], 2)
        # Ordered by captured-margin cost before any execution.
        costs = [p['cost'] for p in result['proposal_order']]
        self.assertEqual(costs, sorted(costs))

    def test_exhausted_pool_and_mismatched_capture_fail_closed(self):
        # One literal slot holding 0: the distinct values are -1, 1 and 2 (the
        # low-margin flips give 1 and 2 again), and one slot cannot combine.
        result = self.search(lambda program, seconds: dict(passed=False, reason='wrong_answer'))
        self.assertEqual(result['executions'], 3)
        self.assertEqual(result['reason'], 'no_public_passing_literal')
        self.logits[self.slot][0] = -self.logits[self.slot][0]
        result = self.search(lambda program, seconds: self.fail('must not execute'))
        self.assertEqual(result['reason'], 'invalid_literal_capture')


if __name__ == '__main__':
    unittest.main()
