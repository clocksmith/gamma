"""Public synthetic receipt composition controls. No real admission or payloads."""
import copy,unittest
import admission as a
class AdmissionTests(unittest.TestCase):
 def fixture(self):
  cases=[117,66,106,103,91,83,110,126];src=[];rows=[];parsed=[]
  for pid,n in zip(a.IDS,cases):
   common=dict(source_sha256='0'*64,cases_sha256='1'*64,effects_sha256='2'*64,runtime_sha256='3'*64)
   src.append(dict(problem_id=pid,**common,case_count=n,finite_primitive_number_arguments_reasoned=True,numeric_bounds_reasoned=True,no_reflection_or_callable_escape_in_source=True,source_contains_intrinsic_or_input_mutation=False))
   rows.append(dict(problem_id=pid,**common,cases=n,all_args_numeric_JSON_arrays_scalars=True));parsed.append(dict(key=str(pid)+':original',source_sha256='0'*64,syntactic_candidate=True,admitted=False))
  review=dict(schema='gamma.extrema8.composite-transform-review.v1',independent_review=True,reviewer='synthetic-only',root_parser_transform_authorized=True,source_pool_admission=False,guard_sha256=a.GUARD,runtime_freeze_sha256=a.RUNTIME_FREEZE,anchors={k:{'sha256':h}for k,h in a.FIXED.items()});review['anchors'].update({k:{'sha256':'4'*64}for k in('runtime_verified','runtime_supervisor')})
  evidence={'source_review':dict(alignment_sha256=a.GUARD,guard_review={'controls_executed_by_reviewer':False},rows=src),'parser_verified':dict(verified=True,sources=8,syntactic_candidates=8,qualified=0,candidate_execution=False,cleanup_passed=True,controls=[dict(expected=True,observed=True)for _ in range(38)],source_results=parsed),'case_audit':dict(ids=a.IDS,blocked=[],case_files_opened=8,rows=rows),'historical123_binding':dict(bindings={'runtime':{'manifest':{'synthetic':'runtime'}}},implementation=dict(source_sha256='0'*64,tests_sha256='1'*64,runtime_sha256='3'*64)),'runtime_verified':dict(schema='gamma.extrema-public-runtime-control.verified.v2',verified=True,freeze_sha256=a.RUNTIME_FREEZE,checks=6,public_isolated_executions=2,corpus_executions=0,algorithm_admission=False,runtime={'synthetic':'runtime'}),'runtime_supervisor':dict(exit_code=0,no_executing_owned_processes_observed=True,remaining_live_owned=[],inspection_unreadable_pids=[],wall_timeout=False)}
  return review,evidence
 def test_composition_shape(self):
  review,evidence=self.fixture();self.assertEqual(len(a.validate(review,evidence)),8)
 def test_root_missing(self):
  r,e=self.fixture();r['root_parser_transform_authorized']=False
  with self.assertRaises(ValueError):a.validate(r,e)
 def test_arbitrary_static_receipt(self):
  r,e=self.fixture();r['anchors']['source_review']['sha256']='f'*64
  with self.assertRaises(ValueError):a.validate(r,e)
 def test_missing_runtime_control(self):
  r,e=self.fixture();e['runtime_verified']['checks']=0
  with self.assertRaises(ValueError):a.validate(r,e)
 def test_changed_runtime(self):
  r,e=self.fixture();e['runtime_verified']['runtime']={'synthetic':'other'}
  with self.assertRaises(ValueError):a.validate(r,e)
 def test_source_mutation(self):
  r,e=self.fixture();e['source_review']['rows'][0]['source_contains_intrinsic_or_input_mutation']=True
  with self.assertRaises(ValueError):a.validate(r,e)
 def test_mismatched_cases(self):
  r,e=self.fixture();e['case_audit']['rows'][0]['cases_sha256']='f'*64
  with self.assertRaises(ValueError):a.validate(r,e)
 def test_duplicate_owner(self):
  r,e=self.fixture();e['source_review']['rows'][-1]=e['source_review']['rows'][0]
  with self.assertRaises(ValueError):a.validate(r,e)
 def test_surviving_process(self):
  r,e=self.fixture();e['runtime_supervisor']['remaining_live_owned']=[{'pid':123}]
  with self.assertRaises(ValueError):a.validate(r,e)
if __name__=='__main__':unittest.main()
