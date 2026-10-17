import unittest

from algsolve import importers, values
from algsolve.public_examples import recover
from algsolve.records import Problem


class PublicExampleTests(unittest.TestCase):
    def test_json_literals_are_names_not_substitutions_inside_strings(self):
        self.assertEqual(values.parse_value('[true, false, null, "true false null"]'),
                         [True, False, None, 'true false null'])
        for source in ['__import__("os")', 'true()', '[v for v in [1]]']:
            with self.assertRaises(values.Unsupported):
                values.parse_value(source)
        for source in ['**data', 'n=1, n=2']:
            with self.assertRaises(values.Unsupported):
                values.parse_call_arguments(source)

    def test_transport_suffix_and_string_whitespace_survive_parsing(self):
        source = 'Input: s = "a  b", root = [1,null,2]\\r\nOutput: true\\r\nExplanation: text\n'
        tests, dropped = importers.statement_examples(source, [('s','str'), ('root','Optional[TreeNode]')], 'bool')
        self.assertEqual(dropped, 0)
        self.assertEqual(tests, [{'args':['a  b', {'__tree_node__':[1,None,2]}], 'expected':True, 'compare':'return'}])
        tests, dropped = importers.statement_examples('Input: s = "a\\rb"\nOutput: "a\\rb"\n', [('s','str')], 'str')
        self.assertEqual(tests[0]['args'], ['a\rb'])
        self.assertEqual(tests[0]['expected'], 'a\rb')

    def test_recovery_uses_only_explicit_examples_and_refuses_partial_parse(self):
        problem = Problem(uid='user:1', source='user', source_id='1', title='P', slug='',
                          statement='Input: n = 1\nOutput: true\n', io_mode='functional',
                          starter_code='class Solution:\n def solve(self, n: int) -> bool:\n',
                          entry={'method':'solve'}, params=[['n','int']])
        recovered = recover(problem)
        self.assertEqual(recovered.public_tests, [{'args':[1], 'expected':True, 'compare':'return'}])
        self.assertEqual(problem.public_tests, [])
        problem.statement += 'Input: n = unknown()\nOutput: false\n'
        self.assertIs(recover(problem), problem)
        problem.statement = 'No examples supplied.'
        self.assertIs(recover(problem), problem)
        problem.public_tests = [{'args':[2], 'expected':False}]
        self.assertIs(recover(problem), problem)


if __name__ == '__main__':
    unittest.main()
