"""One fixed exposed input, two CPU placement policies; no solver or scoring."""
import hashlib,json,os,statistics,time
from pathlib import Path
import numpy as np
import torch
from algsolve.embed import Embedder
from algsolve.records import LANE_ROOT as ROOT
from algsolve.synth.train_typed import query_text,INSTRUCTION

out=Path(__file__).with_name('affinity-probe.json')
assert not out.exists()
initial=sorted(os.sched_getaffinity(0));fixed=initial[:4]
def affinity(cpus):
 for p in Path('/proc/self/task').iterdir():
  try:os.sched_setaffinity(int(p.name),cpus)
  except ProcessLookupError:pass

def counters():
 path=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
 return {k:int(v) for k,v in (s.split() for s in (path/'cpu.stat').read_text().splitlines())}

torch.set_num_threads(4);torch.set_num_interop_threads(1)
assert torch.equal(torch.ones((2,2))@torch.ones((2,2)),torch.full((2,2),2.))
start=time.monotonic();encoder=Embedder(device='cpu');setup=time.monotonic()-start
pair=next(json.loads(s) for s in (ROOT/'runs/typed-real-dev-v5/pairs.jsonl').read_text().splitlines() if json.loads(s)['uid']=='lcd:1051')
text=query_text(pair);encoder.encode(['Return an integer input unchanged.'],query=True,instruction=INSTRUCTION)
rows=[];reference=None
try:
 for i in range(4):
  for mode in (['first_four','scheduler'] if i%2==0 else ['scheduler','first_four']):
   affinity(fixed if mode=='first_four' else initial)
   before=counters();cpu=time.process_time();tick=time.monotonic()
   vector=encoder.encode([text],query=True,instruction=INSTRUCTION)[0]
   wall=time.monotonic()-tick;cpu=time.process_time()-cpu;after=counters()
   if reference is None:reference=vector.copy()
   rows.append(dict(pair=i,mode=mode,wall_seconds=wall,process_cpu_seconds=cpu,
    cpu_stat_delta={k:after[k]-v for k,v in before.items()},exact_vector_equal=bool(np.array_equal(reference,vector)),
    maximum_vector_difference=float(np.max(np.abs(reference-vector))),vector_sha256=hashlib.sha256(vector.tobytes()).hexdigest()))
finally:affinity(initial)
result=dict(scope='Eight fixed-query embedding calls; placement diagnostic, no solver decisions or new candidate',
 uid='lcd:1051',query_sha256=hashlib.sha256(text.encode()).hexdigest(),threads=4,
 first_four=fixed,scheduler_allowed=initial,encoder_setup_seconds=setup,rows=rows,
 metrics={m:dict(median_seconds=statistics.median(r['wall_seconds'] for r in rows if r['mode']==m),
 median_process_cpu_seconds=statistics.median(r['process_cpu_seconds'] for r in rows if r['mode']==m)) for m in ['first_four','scheduler']},
 limitations=['Current paired placement effect cannot attribute past slowdown fully','Both conditions retain four threads and the same four-CPU cgroup cap; other host workloads remain active'])
with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,indent=2))
