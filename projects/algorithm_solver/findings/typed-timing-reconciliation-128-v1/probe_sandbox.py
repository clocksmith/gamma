"""Harmless timing probe; observe payload exit without changing sandbox behavior."""
import hashlib,json,os,select,subprocess,threading,time
from pathlib import Path
from algsolve.judge import sandbox,judge

Original=subprocess.Popen
observations=[]
class ObservedPopen(Original):
 def __init__(self,*a,**kw):
  start=time.monotonic();super().__init__(*a,**kw)
  self.observation=dict(spawn_started=start,spawn_returned=time.monotonic())
  observations.append(self.observation)
  fd=os.pidfd_open(self.pid)
  def observe():
   try:
    if select.select([fd],[],[],2)[0]:self.observation['exit_observed']=time.monotonic()
   finally:os.close(fd)
  self.observer=threading.Thread(target=observe);self.observer.start()
 def wait(self,timeout=None):
  start=time.monotonic()
  try:return super().wait(timeout=timeout)
  finally:
   if timeout is not None:self.observation.update(timed_wait_started=start,timed_wait_returned=time.monotonic(),timeout=timeout)

subprocess.Popen=ObservedPopen
rows=[]
try:
 for kind in ['payload','functional']:
  for i in range(6):
   start=time.monotonic()
   if kind=='payload':
    r=sandbox.run_python('probe.py',files={'probe.py':'import time,json\nprint(json.dumps({"entered":time.monotonic()}))\n'},limits=sandbox.Limits(wall_seconds=1))
    assert r.ok
    entered=json.loads(r.stdout)['entered'];verdict='ok'
   else:
    r=judge.judge_functional('class Solution:\n def identity(self,x): return x\n',{'class':'Solution','method':'identity'},[judge.FunctionalTest(args=[7],expected=7)],wall_seconds=1)
    assert r.passed,r
    entered=None;verdict=r.reason
   end=time.monotonic();o=observations[-1]
   for t in threading.enumerate():
    if t is not threading.current_thread() and t.name.startswith('Thread-') and 'observe' in t.name:t.join(2)
   rows.append(dict(kind=kind,index=i,total_seconds=end-start,sandbox_seconds=r.wall_seconds,
      spawn_seconds=o['spawn_returned']-o['spawn_started'],
      enter_after_spawn_seconds=entered-o['spawn_started'] if entered else None,
      exit_after_spawn_seconds=o.get('exit_observed',end)-o['spawn_started'],
      exit_observation_to_wait_return_seconds=o['timed_wait_returned']-o.get('exit_observed',end),
      verdict=verdict))
finally:subprocess.Popen=Original
out=dict(scope='12 harmless synthetic probes; unchanged sandbox policy and wait implementation; observer scheduling makes exit-delay estimates approximate',
 sandbox_sha256=hashlib.sha256(Path(sandbox.__file__).read_bytes()).hexdigest(),rows=rows)
p=Path(__file__).with_name('sandbox-probe.json')
with p.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(out,indent=2))
