"""Consumed-fit correctness replay from frozen captures; not fresh inference latency."""
import json,time
from pathlib import Path
from algsolve.records import LANE_ROOT as ROOT,load_hidden_tests
from algsolve.rebuild_recognition import sha,publish
from algsolve.synth import typed_codec,development_tests,mine
from algsolve.synth.train_typed import problem_for
from algsolve.synth.typed_prediction_codec import PredictionCodec
from algsolve.synth.typed_comparison import run_route,score_fixed
from algsolve.synth.typed_literal_repair import run_literal_route

HERE=Path(__file__).parent
OUT=ROOT/'runs/typed-literal-semantic-fit-128-v1'
OLD=ROOT/'runs/typed-literal-margin-fit-128-v1'
load=lambda p:json.loads(p.read_text())
def main():
 if OUT.exists():raise ValueError('Once only; never overwrite a result')
 frozen=load(OLD/'candidate.json')
 for n,h in frozen['proposal']['assets_sha256'].items():assert sha(ROOT/n)==h,n
 captures=[load(p) for p in sorted(OLD.glob('capture-[0-9][0-9][0-9][0-9].json'))]
 seal=load(OLD/'capture-seal.json')
 for n,h in seal['captures_sha256'].items():assert sha(OLD/n)==h,n
 unique={}
 for line in (ROOT/'runs/typed-real-dev-v5/pairs.jsonl').read_text().splitlines():
  p=json.loads(line)
  if p['learning_split']=='development_fit':unique.setdefault(p['uid'],p)
 requests=list(unique.values());assert len(requests)==10 and [p['uid'] for p in requests]==[p['uid'] for p in captures]
 oldmanifest=load(ROOT/'runs/typed-composer-recovered-128-scorefix-v1/candidate.json');desc=oldmanifest['checkpoint_contract']['prediction_encoding']
 encoding=PredictionCodec(desc['slots'],desc['types']);identity=typed_codec.frozen(ROOT/'contracts/typed_codec_v1.json')
 structural=frozen['structural_config'];literal=frozen['literal_config']
 sources={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'algsolve').rglob('*.py'))}
 originals={p.name:sha(p) for p in sorted(OLD.glob('*.json'))}
 manifest=dict(name=OUT.name,scope='Semantic correctness diagnostic on consumed fit captures, shared machine; no fresh inference, no latency promotion',
  authority='Owner explicitly permits bounded semantic development alongside serving workers, separating correctness from deadline outcomes',
  source_sha256=sources,driver_sha256=sha(Path(__file__)),original_sha256=originals,
  structural_config=structural,literal_config=literal,
  local_construction_and_public_budget_seconds=2.,literal_budget_seconds=.25,
  inference_timing='Not performed or inherited. Zero shared_seconds means capture-replay stage only, not zero-cost fresh inference.',
  official_two_second_end_to_end_gate='Unchanged; this replay cannot qualify it or revise historical scores',
  decision_inputs='Public input/signature/examples and frozen raw predictions/logits only; no fit label chooses an edit',
  selection='Freeze all20 public decisions before independent source tests; no retries or bounds changes',
  acceptance='Semantic signal iff additional accepted-correct answer, no lost correct answer, no wrong acceptance, no infrastructure failure; not release qualification',
  resources=dict(cpu_threads=4,memory_max_bytes=8*1024**3,disk_max_bytes=5*1024**3,run_wall_seconds=120),
  training=False,protected_opened=False,shared_machine=True)
 OUT.mkdir();publish(OUT/'candidate.json',manifest);start=time.monotonic()
 try:
  rows=[]
  for i,(p,capture) in enumerate(zip(requests,captures)):
   problem=problem_for(p)
   control=run_route('constrained',problem,capture['codes'],capture['logits'],encoding,identity,0.,structural,2.)
   candidate=run_literal_route(control,problem,capture['logits']['bits'],encoding,identity,literal,2.)
   row=dict(uid=p['uid'],routes=dict(control=control,candidate=candidate));rows.append(row)
   publish(OUT/f'decision-{i:04d}.json',row)
   print(json.dumps(dict(uid=p['uid'],decisions={a:r['decision'] for a,r in row['routes'].items()},literal_executions=(candidate.get('literal_repair') or {}).get('executions',0))),flush=True)
  publish(OUT/'decisions-seal.json',dict(candidate_sha256=sha(OUT/'candidate.json'),decisions_sha256={p.name:sha(p) for p in sorted(OUT.glob('decision-[0-9][0-9][0-9][0-9].json'))}))
  scores=[]
  for i,(p,row) in enumerate(zip(requests,rows)):
   problem=problem_for(p);tests,_=development_tests.select(p['uid'],load_hidden_tests(problem))
   assert mine.digest(tests)==p['provenance']['independent_tests_sha256']
   scored=dict(uid=p['uid'],routes={a:score_fixed(r,problem,tests) for a,r in row['routes'].items()});scores.append(scored)
   publish(OUT/f'score-{i:04d}.json',scored)
  metrics={}
  for arm in ['control','candidate']:
   rs=[s['routes'][arm] for s in scores]
   metrics[arm]=dict(cases=10,accepted_correct=sum(r['accepted_correct'] for r in rs),wrong_acceptances=sum(r['wrong_acceptance'] for r in rs),
    independently_correct=sum(r['independently_correct'] is True for r in rs),abstentions=sum(r['decision']=='abstain' for r in rs),
    valid=sum(r['structurally_valid'] for r in rs),infrastructure_failures=sum(r['infrastructure_failure'] for r in rs),
    literal_executions=sum((r.get('literal_repair') or {}).get('executions',0) for r in rs),
    local_budget_failures=sum(r['reason'] in ['literal_budget','decision_budget'] for r in rs))
  useful=[s['uid'] for s in scores if s['routes']['candidate']['accepted_correct'] and not s['routes']['control']['accepted_correct']]
  harmful=[s['uid'] for s in scores if s['routes']['control']['accepted_correct'] and not s['routes']['candidate']['accepted_correct']]
  compact=[]
  for s in scores:
   record=dict(uid=s['uid'],routes={})
   for arm,r in s['routes'].items():
    repair=r.get('literal_repair') or {}
    record['routes'][arm]=dict(decision=r['decision'],reason=r['reason'],accepted_correct=r['accepted_correct'],wrong_acceptance=r['wrong_acceptance'],
     independently_correct=r['independently_correct'],valid=r['structurally_valid'],local_timing=r['timing'],public_reason=(r['public'] or {}).get('reason'),
     independent_reason=(r['independent'] or {}).get('reason'),edits=repair.get('edits',[]),attempts=[dict(edits=a['edits'],validation_failure=a['validation_failure'],public_passed=(a['public'] or {}).get('passed'),public_reason=(a['public'] or {}).get('reason'),execution_seconds=a['execution_seconds']) for a in repair.get('attempts',[])])
   compact.append(record)
  signal=bool(useful and not harmful and not metrics['candidate']['wrong_acceptances'] and not any(v['infrastructure_failures'] for v in metrics.values()))
  report=dict(name=OUT.name,scope=manifest['scope'],metrics=metrics,useful=useful,harmful=harmful,semantic_development_signal=signal,
   latency_qualified=False,release_qualified=False,protected_opened=False,rows=compact,actual_wall_seconds=time.monotonic()-start,
   limitation='Consumed fit replay only; captured inference excluded, current timings contended; neither generalization nor fresh end-to-end qualification')
  assert originals=={p.name:sha(p) for p in sorted(OLD.glob('*.json'))}
  assert sources=={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'algsolve').rglob('*.py'))}
  publish(OUT/'summary.json',report);print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2),flush=True)
 except BaseException as e:
  publish(OUT/'failure.json',dict(type=type(e).__name__,detail=str(e)));raise
if __name__=='__main__':main()
