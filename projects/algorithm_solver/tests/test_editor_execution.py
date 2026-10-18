import unittest
from unittest.mock import patch
from algsolve.editor_execution import execute, query_problem
from algsolve.judge import sandbox

PROBLEM = {'title':'Sum', 'statement':'Return the sum.', 'entry':{'class':'Solution','method':'solve'},
           'params':[['nums','List[int]']], 'public_tests':[{'args':[[2,3]],'expected':5}]}

class EditorContracts(unittest.TestCase):
    def test_client_cannot_supply_checker_or_hidden_path(self):
        problem = query_problem(dict(PROBLEM, checker='raise Exception()', hidden_tests_path='/secret', memory_bytes=10**12))
        self.assertIsNone(problem.checker)
        self.assertEqual(problem.hidden_tests_path, '')
        self.assertEqual(problem.memory_bytes, 512*1024*1024)

    def test_missing_examples_fail_closed(self):
        result = execute('javascript', 'function solve(){return 5}', dict(PROBLEM, public_tests=[]))
        self.assertFalse(result['example_passed'])

    def test_expected_values_never_enter_javascript_sandbox(self):
        with patch('algsolve.editor_execution.sandbox.run', return_value=sandbox.SandboxResult(0,None,b'{"i":0,"result":5,"args_after":[[2,3]]}\n{"done":1}\n',b'',0.1)) as run:
            self.assertTrue(execute('javascript','function solve(nums){return nums.reduce((a,b)=>a+b,0)}',PROBLEM)['example_passed'])
            self.assertNotIn('expected', run.call_args.kwargs['files']['calls.json'])

    def test_challenge_export_keeps_solution_and_hidden_records_out(self):
        import json
        from types import SimpleNamespace
        from algsolve.editor_task import details
        from algsolve.records import Problem
        entry=SimpleNamespace(slug='sum',title='Sum',members=['known'],statement='Return the sum.',
              entry={'class':'Solution','method':'solve'},params=[['nums','List[int]']],
              starter_code='class Solution:\n def solve(self, nums): return SECRET_SOLUTION',
              attribution=['author'],license=['source license'])
        original=Problem(uid='known',source='test',source_id='sum',title='Sum',slug='sum',
                         statement='Sum',io_mode='functional',public_tests=PROBLEM['public_tests'],
                         hidden_tests_path='SECRET_HIDDEN',reference_solutions=['SECRET_SOLUTION'])
        with patch('algsolve.corpus.read_entries',return_value=[entry]), patch('algsolve.splits.load_all',return_value={'known':original}):
            exported=details('sum')
        serialized=json.dumps(exported)
        self.assertNotIn('SECRET',serialized)
        self.assertIn('pass',exported['starters']['python'])
        self.assertEqual(exported['source']['license'],['source license'])
        self.assertEqual(exported['problem']['public_tests'],PROBLEM['public_tests'])


@unittest.skipUnless(__import__('sys').platform.startswith('linux'), 'Requires the real Linux sandbox')
class PhysicalEditorExecution(unittest.TestCase):
    def test_both_languages_and_wrong_result(self):
        self.assertTrue(execute('python', 'class Solution:\n def solve(self, nums): return sum(nums)', PROBLEM)['example_passed'])
        self.assertTrue(execute('javascript', 'function solve(nums){return nums.reduce((a,b)=>a+b,0)}', PROBLEM)['example_passed'])
        self.assertFalse(execute('javascript', 'function solve(){return 6}', PROBLEM)['example_passed'])

    def test_timeout_output_and_network_isolation(self):
        for language, source in [('python','while True: pass'), ('javascript','while(true){}')]:
            self.assertFalse(execute(language,source)['execution_ok'])
        self.assertTrue(execute('javascript', 'console.log("x".repeat(70000))')['output_limit_exceeded'])
        for language, source in [('python','open("/home/x/.ssh/id_ed25519").read()'),
                                 ('javascript','require("node:fs").readFileSync("/home/x/.ssh/id_ed25519")')]:
            self.assertFalse(execute(language, source)['execution_ok'])
        result=execute('javascript', 'require("node:net").connect(443,"1.1.1.1").on("connect",()=>console.log("connected"))')
        self.assertNotIn('connected', result['stdout'])
        self.assertFalse(result['execution_ok'])

    def test_nodes_and_mutation(self):
        problem=dict(PROBLEM, params=[['head','ListNode']],public_tests=[{'args':[{'__list_node__':[1,2]}], 'expected':{'__list_node__':[2,1]}}])
        self.assertTrue(execute('javascript','function solve(head){return new ListNode(2,new ListNode(1))}',problem)['example_passed'])
        problem=dict(PROBLEM,public_tests=[{'args':[[2,3]], 'expected':[3,2], 'compare':'arg:0'}])
        self.assertTrue(execute('javascript','function solve(nums){nums.reverse()}',problem)['example_passed'])

    def test_unsupported_results_fail_closed_instead_of_becoming_json_null_or_object(self):
        for expression, expected in [('NaN', None), ('new Set([1])', {}), ('Infinity', None)]:
            problem=dict(PROBLEM, public_tests=[{'args':[[2,3]], 'expected':expected}])
            self.assertFalse(execute('javascript',f'function solve(){{return {expression}}}',problem)['example_passed'])
