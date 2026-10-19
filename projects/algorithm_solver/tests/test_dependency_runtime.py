"""Pinned dependency, sandbox fidelity, and private-global adapter checks."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from algsolve import dependency_bundle,dependency_judge,validate,answer as answer_module
from algsolve.dependency_lookup import make_answer,profile_record,check_profile
from algsolve.judge import judge,sandbox
from algsolve.records import Problem


def problem():
    return Problem('fixture:dep','fixture','dep','Sorted fixture','fixture','Sort values.','functional',
        entry={'class':'Solution','method':'solve'},params=[['nums','List[int]']],
        public_tests=[{'args':[[4,1,3]],'expected':[1,3,4]}])


class DependencyRuntimeTests(unittest.TestCase):
    def test_wrong_wheel_fails_before_execution_and_does_not_import_on_host(self):
        import sys
        before=sys.modules.get('sortedcontainers')
        with patch.object(sandbox,'run_python') as execute:
            for data in [b'',b'wrong',dependency_bundle.read_bundle()[:-1]+b'!']:
                with self.subTest(size=len(data)),self.assertRaises(ValueError):dependency_judge.make_judge_problem(data)
            execute.assert_not_called()
        self.assertIs(sys.modules.get('sortedcontainers'),before)

    def test_clones_preserve_code_defaults_closure_and_original_globals(self):
        originals=[judge.judge_functional,validate.judge_problem,answer_module.check_stored,answer_module.answer]
        snapshots=[dict(f.__globals__) for f in originals]
        functions=[dependency_judge.make_judge_problem(),dependency_judge.make_public_checker(),
            make_answer({'lc:fixture':'0'*64})]
        for clone,original in zip(functions,[validate.judge_problem,answer_module.check_stored,answer_module.answer]):
            self.assertIs(clone.__code__,original.__code__)
            self.assertIs(clone.__defaults__,original.__defaults__)
            self.assertIs(clone.__closure__,original.__closure__)
            self.assertEqual(clone.__kwdefaults__,original.__kwdefaults__)
            self.assertIsNot(clone.__globals__,original.__globals__)
        for original,before in zip(originals,snapshots):
            self.assertEqual(set(original.__globals__),set(before))
            for name,value in before.items():self.assertIs(original.__globals__[name],value,name)
        with self.assertRaises(ValueError):
            dependency_judge.isolated_function(judge.judge_functional,{'sandbox':object()},allowed={'unapproved'})

    def test_backend_preserves_candidate_calls_limits_and_flat_files(self):
        backend=dependency_judge.BundleBackend();source='class Solution: pass'
        files={'harness.py':judge.HARNESS_PATH.read_text(),'candidate.py':source,
               'calls.json':json.dumps({'entry':{'class':'Solution','method':'solve'},'calls':[{'args':[[4,1,3]],'kwargs':{}}]})}
        original=dict(files);limits=sandbox.Limits(memory_bytes=123456789)
        with patch.object(sandbox,'run_python',return_value=object()) as run:
            backend.run_python('harness.py',files=files,limits=limits)
        self.assertEqual(files,original)
        sent=run.call_args.kwargs
        self.assertIs(sent['limits'],limits)
        self.assertEqual(sent['files']['candidate.py'],source)
        self.assertEqual(sent['files']['calls.json'],files['calls.json'])
        self.assertEqual(sent['files']['base_harness.py'],files['harness.py'])
        self.assertTrue(all('/' not in name for name in sent['files']))
        self.assertEqual(hashlib.sha256(sent['files'][dependency_bundle.TASK_NAME]).hexdigest(),dependency_bundle.SHA256)
        self.assertNotIn('expected',json.loads(sent['files']['calls.json']))
        self.assertNotIn('expected',json.loads(sent['files']['calls.json'])['calls'][0])

    def test_sortedlist_implicit_and_explicit_import_work_only_in_opt_in_judge(self):
        p=problem();dependency=dependency_judge.make_judge_problem()
        source='class Solution:\n def solve(self, nums):\n  return list(SortedList(nums))\n'
        self.assertFalse(validate.judge_problem(p,source,p.public_tests,wall_seconds=3).passed)
        for code in [source,'from sortedcontainers import SortedList\n'+source]:
            with self.subTest(explicit=code.startswith('from')):
                verdict=dependency(p,code,p.public_tests,wall_seconds=3)
                self.assertTrue(verdict.passed,verdict)
        self.assertFalse(validate.judge_problem(p,source,p.public_tests,wall_seconds=3).passed)
        wrong=source.replace('list(SortedList(nums))','list(reversed(SortedList(nums)))')
        verdict=dependency(p,wrong,p.public_tests,wall_seconds=3)
        self.assertEqual(verdict.reason,judge.WRONG_ANSWER)

    def test_isolated_startup_and_readonly_task_remain_enforced(self):
        p=problem();p.public_tests=[{'args':[[]],'expected':True}]
        source='''class Solution:
 def solve(self, nums):
  import sys, pathlib, sortedcontainers
  try:
   pathlib.Path('/task/unapproved-write').write_text('x')
   return False
  except OSError:
   pass
  return bool(sys.flags.isolated and sys.flags.no_site and '/task' not in sys.path and
   not any('vendor-sortedcontainers' in p for p in sys.path) and
   sortedcontainers.__file__.startswith('/task/vendor-sortedcontainers-2.4.0.whl/'))
'''
        verdict=dependency_judge.make_judge_problem()(p,source,p.public_tests,wall_seconds=3)
        self.assertTrue(verdict.passed,verdict)

    def test_dependency_profile_cannot_select_arbitrary_files(self):
        for sources in [{},{'lc:fixture':'not-a-hash'},{'/tmp/file':'0'*64}]:
            with self.subTest(sources=sources),self.assertRaises(ValueError):profile_record(sources)

    def test_profile_rejects_runtime_or_wheel_identity_drift(self):
        sources={'lc:fixture':'0'*64}
        for field in ['wheel_sha256','task_file','id']:
            record=profile_record(sources);record[field]='changed'
            with self.subTest(field=field),self.assertRaises(ValueError):
                check_profile(SimpleNamespace(manifest={'runtime_dependency':record}))
        record=profile_record(sources);record['modules_sha256']['dependency_judge.py']='0'*64
        with self.assertRaises(ValueError):check_profile(SimpleNamespace(manifest={'runtime_dependency':record}))

    def test_source_scope_preserves_other_checker_and_rejects_changed_reference(self):
        cloned=make_answer({'lc:fixture':'0'*64})
        checker=cloned.__globals__['check_stored']
        entry=SimpleNamespace(key='lc:other')
        with patch.object(answer_module,'check_stored',return_value='original') as original:
            self.assertEqual(checker(problem(),entry,3),'original')
            original.assert_called_once()
        entry=SimpleNamespace(key='lc:fixture',references=[{'code':'changed stored code'}])
        with self.assertRaisesRegex(ValueError,'selected-source identity mismatch'):
            checker(problem(),entry,3)
