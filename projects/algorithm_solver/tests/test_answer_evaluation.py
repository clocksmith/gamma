from types import SimpleNamespace
import unittest

from algsolve.answer_evaluation import make_query
from algsolve.records import Problem


class AnswerEvaluationTests(unittest.TestCase):
    def test_query_inputs_exclude_oracles_and_reference_solutions(self):
        problem = Problem(uid='p', source='fixture', source_id='p', title='P', slug='p',
                          statement='Original', io_mode='functional', entry={'method':'solve'},
                          params=[['n','int']], public_tests=[{'args':[1], 'expected':1}],
                          hidden_tests_path='secret.json', reference_solutions=['SECRET'], import_notes={'private':1})
        entry = SimpleNamespace(key='key', judge_uid='p', entry=problem.entry, params=problem.params,
                                statement='Indexed', starter_code='class Solution: ...')
        for spec, expected in [({'kind':'exact','target':'key'}, 'Indexed'),
                               ({'kind':'paraphrase','target':'key'}, 'Reworded'),
                               ({'kind':'absent_exact','problem_uid':'p'}, 'Original')]:
            original, query = make_query(spec, {'key':entry}, {'p':problem}, {'key':{'paraphrase':'Reworded'}})
            self.assertIs(original, problem)
            self.assertEqual(query.statement, expected)
            self.assertEqual(query.hidden_tests_path, '')
            self.assertEqual(query.reference_solutions, [])
            self.assertEqual(query.import_notes, {})
            self.assertEqual(query.public_tests, problem.public_tests)
        self.assertEqual(problem.hidden_tests_path, 'secret.json')
        entry.entry = {'method':'different'}
        with self.assertRaisesRegex(ValueError, 'signatures'):
            make_query({'kind':'exact','target':'key'}, {'key':entry}, {'p':problem}, {})


if __name__ == '__main__':
    unittest.main()
