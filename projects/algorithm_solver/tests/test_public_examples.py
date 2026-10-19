"""Synthetic parser/abstention checks; no solver or isolation qualification."""
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

    def test_multiline_nested_output_preserves_quoted_whitespace_and_labels(self):
        source = ('Input: grid = [["a"],\n\xa0 ["b"]]\nOutput: \n'
                  '[["a\xa0 b", "Input: data"],\n\xa0 ["\\\"quoted\\\"", "two  spaces"]]\n'
                  'Explanation: this is not data.\n')
        tests, dropped = importers.statement_examples(source, [('grid', 'List[List[str]]')], 'List[List[str]]')
        self.assertEqual(dropped, 0)
        self.assertEqual(tests[0]['args'], [[["a"], ["b"]]])
        self.assertEqual(tests[0]['expected'], [['a\xa0 b', 'Input: data'], ['"quoted"', 'two  spaces']])

    def test_separate_input_lines_are_not_silently_discarded(self):
        source = 'Input: ["Store", "get"]\n[[1], [2]]\nOutput: [null, 2]\n'
        tests, dropped = importers.statement_examples(source, [('ops', 'List[str]')], 'List[int]')
        self.assertEqual(tests, [])
        self.assertEqual(dropped, 1)
        # Expressions may legitimately span lines before a comma: preserve all
        # input syntax and let the restricted parser decide, not the scanner.
        source = 'Input: a = [1]\n, b = [2]\nOutput: 3\n'
        tests, dropped = importers.statement_examples(source, [('a', 'List[int]'), ('b', 'List[int]')], 'int')
        self.assertEqual(dropped, 0)
        self.assertEqual(tests[0]['args'], [[1], [2]])

    def test_multiline_incomplete_or_executable_output_is_rejected(self):
        for output in ('[1,\n2', '[1,\n__import__("os")]'):
            with self.subTest(output=output):
                source = 'Input: n = 1\nOutput: ' + output + '\nExample 2:\nInput: n = 2\nOutput: [2]\n'
                tests, dropped = importers.statement_examples(source, [('n', 'int')], 'List[int]')
                self.assertEqual(dropped, 1)
                self.assertEqual(tests, [{'args': [2], 'expected': [2], 'compare': 'return'}])

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



    def test_invalid_whitelisted_operations_are_unsupported_data(self):
        # Whitelisting float/arithmetic is not permission for malformed values
        # to escape the parser and crash one-shot recognition on the host.
        for text in ('float([1])', 'float("not-a-number")', 'float(1000000**64)',
                     '(1000000**64) * 1.0', 'float("1+1")'):
            with self.subTest(text=text), self.assertRaises(values.Unsupported):
                values.parse_value(text)
        self.assertEqual(values.parse_value('float("2.5")'), 2.5)
        self.assertEqual(values.parse_value('float("inf")'), {'__float__': 'inf'})

    def test_incomplete_example_cannot_silently_leave_a_passing_subset(self):
        source = 'Input: n = 1\nOutput: true\nInput: n = 2\n'
        tests, dropped = importers.statement_examples(source, [('n', 'int')], 'bool')
        self.assertEqual(len(tests), 1)
        self.assertEqual(dropped, 1)
        # Indented labels and literal label text preserve the same boundary.
        tests, dropped = importers.statement_examples(
            '  Input: s = "Input: text"\n  Output: "Output: text"\n', [('s', 'str')], 'str')
        self.assertEqual(dropped, 0)
        self.assertEqual(tests[0]['args'], ['Input: text'])

    def test_one_shot_answer_abstains_before_lookup_for_incomplete_or_invalid_examples(self):
        from algsolve.answer import answer
        valid = 'Input: n = 1\nOutput: true\n'
        suffixes = ('Input: n = 2\n', 'Input: n = 2\nOutput: float([1])\n',
                    'Input: n = float("bad")\nOutput: false\n')
        for suffix in suffixes:
            with self.subTest(suffix=suffix):
                problem = Problem('fixture:example', 'fixture', 'example', '', '', valid + suffix,
                                  'functional', starter_code='class Solution:\n def solve(self, n: int) -> bool:\n',
                                  entry={'method': 'solve'}, params=[['n', 'int']])
                self.assertIs(recover(problem), problem)
                # Any attempt to use a lookup, embedder or judge would fail on
                # this bare context. No candidate or untrusted code is executed.
                result = answer(object(), problem)
                self.assertEqual(result['decision'], 'abstain')
                self.assertEqual(result['reason'], 'query_has_no_public_examples')
                self.assertEqual(result['attempts'], [])
                self.assertEqual(problem.public_tests, [])


if __name__ == '__main__':
    unittest.main()
