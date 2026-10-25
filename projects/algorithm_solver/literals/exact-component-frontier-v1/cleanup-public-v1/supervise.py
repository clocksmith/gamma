"""Narrow owned-process supervisor, pattern linked to persistent timing launch.py.
No sandbox changes: detached native groups discovered by procfs PID/starttime.
"""
import argparse,json,os,signal,subprocess,time,ctypes,math
from pathlib import Path
HERE=Path(__file__).resolve().parent

def snapshot():
 rows={};unreadable=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   text=(p/'stat').read_text();f=text[text.rfind(')')+2:].split()
   rows[int(p.name)]={'pid':int(p.name),'state':f[0],'ppid':int(f[1]),'pgid':int(f[2]),'starttime':int(f[19])}
  except (FileNotFoundError,ProcessLookupError):pass
  except (OSError,ValueError,IndexError):unreadable.append(int(p.name))
 return rows,unreadable

def discover(root,owned,rows):
 # A dedicated child-subreaper owns newly reparented descendants even if the
 # intermediate leader died before the first polling snapshot.
 for pid,row in rows.items():
  if row["ppid"]==os.getpid():owned[pid]=row
 # Never adopt a reused tracked PID. Newly descended children are identity-bound.
 seeds={pid for pid,r in owned.items() if pid in rows and rows[pid]['starttime']==r['starttime']}
 if not owned and root in rows:owned[root]=rows[root];seeds.add(root)
 changed=True
 while changed:
  changed=False
  for pid,row in rows.items():
   if pid not in seeds and row['ppid'] in seeds:
    owned[pid]=row;seeds.add(pid);changed=True
 return owned

def live_owned(owned,rows):
 return [r for pid,r in rows.items() if pid in owned and r['starttime']==owned[pid]['starttime'] and r['state'] not in ('Z','X')]

def supervise(argv,log_path,deadline,state,grace=10):
 if not math.isfinite(deadline):raise ValueError('finite deadline required')
 # Must be the dedicated supervisor process, with exclusive child ownership.
 initial,bad=snapshot()
 if bad or any(r['ppid']==os.getpid() for r in initial.values()):raise RuntimeError('exclusive observable child ownership required')
 libc=ctypes.CDLL(None,use_errno=True)
 if libc.prctl(36,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'child subreaper unavailable')
 child=None;owned={};unreadable=set();timed_out=False;error=None;signals=[];adopted_reaped=[]
 def observe():
  rows,bad=snapshot();unreadable.update(bad)
  if child is not None:discover(child.pid,owned,rows)
  return rows
 def signal_owned(sig):
  rows=observe()
  for r in live_owned(owned,rows):
   # pidfds bind the actual process: never broadcast to potentially reused PGID.
   try:
    fd=os.pidfd_open(r['pid'],0)
    try:
     current,bad=snapshot();unreadable.update(bad)
     if r['pid'] in current and current[r['pid']]['starttime']==r['starttime']:
      signal.pidfd_send_signal(fd,sig);signals.append({'pid':r['pid'],'starttime':r['starttime'],'signal':sig})
    finally:os.close(fd)
   except ProcessLookupError:pass
 def reap_adopted():
  for pid in tuple(owned):
   if child is not None and pid==child.pid:continue
   try:
    got,status=os.waitpid(pid,os.WNOHANG)
    if got:adopted_reaped.append(got)
   except ChildProcessError:pass

 try:
  with log_path.open('xb') as log:
   if state['signals'] or time.monotonic()>=deadline:raise RuntimeError('stopped before launch')
   child=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   while True:
    observe()
    if state['signals']:break
    if time.monotonic()>=deadline:timed_out=True;break
    if child.poll() is not None:break
    time.sleep(.05)
 except BaseException as e:error=type(e).__name__
 finally:
  if child is not None:
   observe()
   # Flag-only worker handler lets currently bounded native call clean itself.
   if child.poll() is None:
    try:child.send_signal(signal.SIGTERM)
    except ProcessLookupError:pass
    until=time.monotonic()+grace
    while child.poll() is None and time.monotonic()<until:observe();time.sleep(.05)
   signal_owned(signal.SIGTERM)
   until=time.monotonic()+1
   while live_owned(owned,observe()) and time.monotonic()<until:signal_owned(signal.SIGTERM);reap_adopted();time.sleep(.02)
   signal_owned(signal.SIGKILL)
   until=time.monotonic()+1
   while live_owned(owned,observe()) and time.monotonic()<until:signal_owned(signal.SIGKILL);reap_adopted();time.sleep(.02)
   try:child.wait(timeout=.2)
   except subprocess.TimeoutExpired:error='UnreapedLeader'
  remaining=live_owned(owned,observe());reap_adopted()
 evidence={'exit_code':None if child is None else child.returncode,'wall_timeout':timed_out,'error_type':error,'termination_signals':state['signals'],'cleanup_signals':signals,'child_subreaper':True,'adopted_children_reaped':adopted_reaped,'owned_processes':list(owned.values()),'remaining_live_owned':remaining,'inspection_unreadable_pids':sorted(unreadable),'no_executing_owned_processes_observed':not remaining and not unreadable,'termination_grace_seconds':grace+2}
 return evidence

def main(a,state,start):
 a.output.mkdir(mode=0o700,parents=True,exist_ok=False)
 deadline=start+900
 argv=['/usr/bin/python3',str(HERE/'run.py'),'--node-path',str(a.node_path),'--review',str(a.review),'--output',str(a.output/'results'),'--contract-sha256',a.contract_sha256,'--absolute-deadline',str(deadline)]
 result=supervise(argv,a.output/'worker.log',deadline,state)
 result.update(absolute_deadline_monotonic=deadline,wall_seconds=time.monotonic()-start,successor_freeze_sha256=a.contract_sha256)
 passed=result['exit_code']==0 and not result['wall_timeout'] and not result['error_type'] and not result['termination_signals'] and result['no_executing_owned_processes_observed']
 try:
  report=json.loads((a.output/'results/report.json').read_bytes())
  passed=passed and report['status']=='completed' and report['passed_source_language_pairs']==16
 except (OSError,ValueError,KeyError):passed=False
 result['status']='completed' if passed else 'failed';(a.output/'supervisor.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 return 0 if passed else 1
if __name__=='__main__':
 start=time.monotonic();os.umask(0o077);state={'signals':[]}
 def handler(signum,frame):state['signals'].append(signum)
 for signum in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):signal.signal(signum,handler)
 p=argparse.ArgumentParser()
 for n in ('node-path','review','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--contract-sha256',required=True);raise SystemExit(main(p.parse_args(),state,start))
