"""Paired synthetic checks of process wait only; no solver candidate execution."""
import hashlib,json,statistics,time
from pathlib import Path
from algsolve.judge import sandbox,judge

fixed=sandbox._wait_for_exit
rows=[]
try:
 for i in range(8):
  for mode in (['poll','pidfd'] if i%2==0 else ['pidfd','poll']):
   sandbox._wait_for_exit=fixed if mode=='pidfd' else lambda proc,timeout:proc.wait(timeout=timeout)
   started=time.monotonic()
   r=judge.judge_functional('class Solution:\n def identity(self,x): return x\n',{'class':'Solution','method':'identity'},[judge.FunctionalTest(args=[7],expected=7)],wall_seconds=1)
   elapsed=time.monotonic()-started
   assert r.passed,r
   rows.append(dict(index=i,mode=mode,total_seconds=elapsed,sandbox_seconds=r.wall_seconds,passed=r.passed))
finally:sandbox._wait_for_exit=fixed
metrics={m:dict(median_seconds=statistics.median(r['total_seconds'] for r in rows if r['mode']==m),minimum_seconds=min(r['total_seconds'] for r in rows if r['mode']==m),maximum_seconds=max(r['total_seconds'] for r in rows if r['mode']==m)) for m in ['poll','pidfd']}
report=dict(scope='16 alternating synthetic functional checks, fixed sandbox policy and 1-second limit; not solver results',rows=rows,metrics=metrics,sandbox_sha256=hashlib.sha256(Path(sandbox.__file__).read_bytes()).hexdigest())
with Path(__file__).with_name('wait-comparison.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(metrics,indent=2))
