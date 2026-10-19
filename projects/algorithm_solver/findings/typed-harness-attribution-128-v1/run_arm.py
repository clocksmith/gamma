"""One predeclared timing arm. No independent tests, solver decisions or scoring."""
import argparse,hashlib,json,os,time
from pathlib import Path
import numpy as np
import torch
from algsolve.embed import Embedder,EMBEDDING_DIR
from algsolve.records import LANE_ROOT as ROOT
from algsolve.rebuild_recognition import Monitor,publish,sha
from algsolve.synth import typed_codec
from algsolve.synth.train_typed import query_text,INSTRUCTION
from algsolve.synth.typed_prediction_codec import PredictionCodec
from algsolve.synth.typed_predictor import TypedPredictor,decisions

HERE=Path(__file__).parent
ARMS=['embedding_only','full_monitored','full_unmonitored']
def load(p):return json.loads(p.read_text())
def read_rows(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def counters():
 cgroup=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
 cpu={k:int(v) for k,v in (s.split() for s in (cgroup/'cpu.stat').read_text().splitlines())}
 sched={}
 for p in Path('/proc/self/task').iterdir():
  try:sched[p.name]=list(map(int,(p/'schedstat').read_text().split()))
  except FileNotFoundError:pass
 return dict(cpu=cpu,sched=sched,process_cpu_seconds=time.process_time())
def delta(before,after):
 common=set(before['sched'])&set(after['sched'])
 return dict(cpu_stat={k:after['cpu'][k]-v for k,v in before['cpu'].items()},
  process_cpu_seconds=after['process_cpu_seconds']-before['process_cpu_seconds'],
  sched_runtime_ns=sum(after['sched'][k][0]-before['sched'][k][0] for k in common),
  sched_runnable_delay_ns=sum(after['sched'][k][1]-before['sched'][k][1] for k in common),
  sched_timeslices=sum(after['sched'][k][2]-before['sched'][k][2] for k in common),
  common_threads=len(common),new_threads=len(set(after['sched'])-set(before['sched'])))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--arm',choices=ARMS,required=True);args=ap.parse_args()
 protocol=load(HERE/'protocol.json');old=ROOT/'runs/typed-literal-margin-fit-128-v1'
 # This runner cannot interrupt another project. Require owner-quiesced workers.
 for worker in load(HERE/'preflight.json')['samples'][0]['workers']:
  path=Path('/proc')/str(worker['pid'])
  if path.exists():
   status=dict(s.split(':',1) for s in (path/'status').read_text().splitlines() if ':' in s)
   if (path/'stat').read_text().split()[21]==worker['starttime']:
    assert status['State'].strip().startswith(('T','t','Z')), 'Separate Reploid worker remains active; uncontended precondition unsatisfied'
 frozen=load(old/'candidate.json');out=ROOT/'runs/typed-harness-attribution-128-v1'/args.arm
 if out.exists():raise ValueError('Never overwrite or retry a timing arm')
 for name,h in frozen['proposal']['assets_sha256'].items():assert sha(ROOT/name)==h,name
 assert sha(EMBEDDING_DIR/'model.safetensors')==protocol['unchanged']['encoder_sha256']
 assert sha(EMBEDDING_DIR/'tokenizer.json')==protocol['unchanged']['tokenizer_sha256']
 fit=[p for p in read_rows(ROOT/'runs/typed-real-dev-v5/pairs.jsonl') if p['learning_split']=='development_fit']
 unique={}
 for p in fit:unique.setdefault(p['uid'],p)
 requests=list(unique.values());original=[load(p) for p in sorted(old.glob('capture-[0-9][0-9][0-9][0-9].json'))]
 assert [p['uid'] for p in requests]==[p['uid'] for p in original] and len(requests)==10
 out.mkdir(parents=True)
 publish(out/'manifest.json',dict(arm=args.arm,protocol_sha256=sha(HERE/'protocol.json'),driver_sha256=sha(Path(__file__)),
  frozen_candidate_sha256=sha(old/'candidate.json'),query_sha256={p['uid']:hashlib.sha256(query_text(p).encode()).hexdigest() for p in requests},
  source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'algsolve').rglob('*.py'))},
  no_independent_tests=True,no_solver_decisions=True,initial_affinity=sorted(os.sched_getaffinity(0))))
 monitor=None;monitor_measurement={};run_start=time.monotonic()
 try:
  os.sched_setaffinity(0,protocol['unchanged']['cpu_affinity'])
  if args.arm=='full_monitored':
   monitor=Monitor([out,EMBEDDING_DIR,ROOT/'runs/typed-student-v2',ROOT/'runs/typed-real-dev-v5'],seconds=120)
   watch=monitor.watch
   def observed_watch():
    started=time.thread_time()
    try:watch()
    finally:monitor_measurement['thread_cpu_seconds']=time.thread_time()-started
   monitor.watch=observed_watch;monitor.start()
  torch.set_num_threads(4);torch.set_num_interop_threads(1)
  assert torch.equal(torch.ones((2,2))@torch.ones((2,2)),torch.full((2,2),2.))
  setup={}
  if args.arm!='embedding_only':
   tick=time.monotonic();checkpoint=torch.load(ROOT/'runs/typed-student-v2/model.pt',map_location='cpu',weights_only=True)
   training=checkpoint['contract'];desc=training['prediction_encoding'];encoding=PredictionCodec(desc['slots'],desc['types'])
   model=TypedPredictor(checkpoint['state_dict']['project.weight'].shape[1],encoding.slots,len(encoding.types),width=training['width'])
   model.load_state_dict(checkpoint['state_dict'],strict=True);model.eval();setup['checkpoint_seconds']=time.monotonic()-tick
  tick=time.monotonic();encoder=Embedder(device='cpu');setup['encoder_seconds']=time.monotonic()-tick
  if args.arm!='embedding_only':
   descriptions=[typed_codec.digest(p['target'])+' '+json.dumps(p['target']['program'],sort_keys=True) for p in fit]
   tick=time.monotonic();memory=encoder.encode(descriptions,batch_size=4);setup['fit_memory_seconds']=time.monotonic()-tick
  tick=time.monotonic();warm=encoder.encode(['Return an integer input unchanged.'],query=True,instruction=INSTRUCTION)[0]
  if args.arm!='embedding_only':
   with torch.inference_mode():model(torch.from_numpy(warm[None]),torch.from_numpy(memory[:4][None]))
  setup['warmup_seconds']=time.monotonic()-tick;publish(out/'setup.json',setup)
  metadata=[]
  for i,(pair,prior) in enumerate(zip(requests,original)):
   start=counters();tick=time.monotonic();vector=encoder.encode([query_text(pair)],query=True,instruction=INSTRUCTION)[0]
   embedding=time.monotonic()-tick;end=counters()
   row=dict(uid=pair['uid'],embedding_seconds=embedding,embedding_telemetry=delta(start,end),
    vector_sha256=hashlib.sha256(vector.tobytes()).hexdigest(),affinity=sorted(os.sched_getaffinity(0)),
    query_fresh=True,prior_embedding_seconds=prior['embedding_seconds'])
   capture={**row}
   if args.arm!='embedding_only':
    tick=time.monotonic();similarities=memory@vector;neighbors=np.argsort(-similarities,kind='stable')[:4];row['retrieval_seconds']=time.monotonic()-tick
    tick=time.monotonic()
    with torch.inference_mode():
     logits=model(torch.from_numpy(vector[None]),torch.from_numpy(memory[neighbors][None]));raw=decisions(logits);scores={k:v[0].tolist() for k,v in logits.items()}
    row['prediction_capture_seconds']=time.monotonic()-tick;row['raw_parity']=raw==prior['codes']
    capture.update(codes=raw,logits=scores,similarities=similarities.tolist())
   tick=time.monotonic();publish(out/f'capture-{i:04d}.json',capture);row['publication_seconds']=time.monotonic()-tick
   metadata.append(row);print(json.dumps(row),flush=True)
  if monitor:
   monitor.stop.set();monitor.thread.join(2);assert not monitor.thread.is_alive()
  summary=dict(arm=args.arm,setup=setup,rows=metadata,run_wall_seconds=time.monotonic()-run_start,
   monitor=monitor_measurement,resources=monitor.counters() if monitor else {},quality_scored=False)
  publish(out/'summary.json',summary)
 except BaseException as error:
  publish(out/'failure.json',dict(type=type(error).__name__,detail=str(error),wall_seconds=time.monotonic()-run_start));raise
 finally:
  if monitor:monitor.stop.set();monitor.thread.join(2)
if __name__=='__main__':main()
