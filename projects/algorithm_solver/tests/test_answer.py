"""Exercise the editor-facing gate with the real Linux sandbox, no model calls."""
import unittest
from unittest.mock import patch
import numpy as np
from algsolve.answer import answer
from algsolve.lookup import LookupIndex
from algsolve.model import Generation
from algsolve.records import Problem
from algsolve.routes import Budget, Context
from algsolve.splits import IndexEntry

MAX = 'class Solution:\n def solve(self, nums):\n  return max(nums)\n'
SUM = 'class Solution:\n def solve(self, nums):\n  return sum(nums)\n'

class Embedding:
    def encode(self, *args, **kwargs):
        return np.array([[1., 0.]])

class Generator:
    torch = None
    def __init__(self, code=SUM):
        self.messages = []
        self.code = code
    def generate(self, messages, **kwargs):
        self.messages.append(messages)
        return Generation('```python\n' + self.code + '```', 1, 1, 0, 'eos')


def context(generator=None):
    entries = [IndexEntry('lc:max', 'max', 'Maximum', 'Return the maximum.',
                         'class Solution:\n def solve(self, nums): pass', {'class': 'Solution', 'method': 'solve'},
                         [['nums', 'List[int]']], [], 'Easy', ['source:max'],
                         [{'code': MAX, 'validated': True}], license=['test'], attribution=['fixture'])]
    return Context(generator=generator, embedder=Embedding(), lookup=LookupIndex(entries, np.array([[1., 0.]])),
                   thresholds={'min_score': 0, 'min_margin': 0}, classifier=None, entries=entries,
                   budget=Budget(100, 100, 1, 20, 5, 2, 2, 1))


def query(expected=5):
    return Problem('user:1', 'user', '1', 'Sum', '', 'Return the sum.', 'functional',
                   starter_code='class Solution:\n def solve(self, nums): pass',
                   entry={'class': 'Solution', 'method': 'solve'},
                   public_tests=[{'args': [[2, 3]], 'expected': expected}],
                   hidden_tests_path='must-never-be-opened.json', reference_solutions=['hidden sentinel'])

class AnswerTests(unittest.TestCase):
    def test_original_validation_does_not_approve_different_query(self):
        result = answer(context(), query())
        self.assertIsNone(result['code'])
        self.assertFalse(result['example_passed'])
        self.assertTrue(result['source']['stored_reference_validated'])
        self.assertIsNone(result['independent_tests_passed'])

    def test_stored_pass_preserves_attribution_without_generation(self):
        generator = Generator()
        result = answer(context(generator), query(3), allow_generation=True)
        self.assertEqual(result['code'], MAX)
        self.assertEqual(result['source']['attribution'], ['fixture'])
        self.assertEqual(generator.messages, [])

    def test_fallback_uses_retrieved_code_and_only_public_query(self):
        generator = Generator()
        result = answer(context(generator), query(), allow_generation=True)
        self.assertTrue(result['example_passed'])
        self.assertEqual(result['route'], 'adapted')
        prompt = generator.messages[0][1]['content']
        self.assertIn(MAX.strip(), prompt)
        self.assertNotIn('hidden sentinel', prompt)
        self.assertNotIn('must-never-be-opened', prompt)

    def test_failed_generator_is_not_returned(self):
        result = answer(context(Generator(MAX)), query(), allow_generation=True)
        self.assertIsNone(result['code'])
        self.assertEqual(result['reason'], 'generation_not_verified')

    def test_no_examples_does_not_generate(self):
        q = query(); q.public_tests = []
        generator = Generator()
        self.assertEqual(answer(context(generator), q, allow_generation=True)['reason'], 'query_has_no_public_examples')
        self.assertEqual(generator.messages, [])

    def test_reranker_requires_calibration_and_finite_scores(self):
        with self.assertRaises(ValueError):
            answer(context(), query(), reranker=lambda *_: [1])
        with self.assertRaises(ValueError):
            answer(context(), query(), reranker=lambda *_: [float('nan')],
                   rerank_thresholds={'min_score': 0, 'min_margin': 0})

    def test_sandbox_failure_is_not_sent_to_generator(self):
        from algsolve.judge.judge import Verdict, SANDBOX_ERROR
        generator = Generator()
        with patch('algsolve.answer.validate.judge_problem', return_value=Verdict(False, SANDBOX_ERROR, 1, 0, 0)):
            self.assertEqual(answer(context(generator), query(), allow_generation=True)['reason'], 'sandbox_unavailable')
        self.assertEqual(generator.messages, [])

if __name__ == '__main__':
    unittest.main()
