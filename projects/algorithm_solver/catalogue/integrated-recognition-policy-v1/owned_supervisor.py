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
   rows[int(p.name)]={'pid':int(p.name),'state':f[0],'ppid':int(f[1]),'pgid':int(f[2]),'starttime':int(f[19]),'rss_bytes':max(0,int(f[21]))*os.sysconf('SC_PAGE_SIZE')}
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

def supervise(argv,log_path,deadline,state,grace=3,rss_limit_bytes=None,env=None,cwd=None):
 if not math.isfinite(deadline):raise ValueError('finite deadline required')
 if type(rss_limit_bytes)is not int or rss_limit_bytes<=0:raise ValueError('positive integer RSS cap required')
 # Must be the dedicated supervisor process, with exclusive child ownership.
 initial,bad=snapshot()
 if bad or any(r['ppid']==os.getpid() for r in initial.values()):raise RuntimeError('exclusive observable child ownership required')
 libc=ctypes.CDLL(None,use_errno=True)
 if libc.prctl(36,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'child subreaper unavailable')
 peak_rss=0;samples=0;rss_exceeded=False
 child=None;owned={};unreadable=set();timed_out=False;error=None;signals=[];adopted_reaped=[]
 def observe():
  nonlocal peak_rss,samples,rss_exceeded
  rows,bad=snapshot();unreadable.update(bad)
  for pid,prior in owned.items():
   if pid in rows and rows[pid]['starttime']!=prior['starttime']:unreadable.add(pid)
  if child is not None:discover(child.pid,owned,rows)
  if os.getpid() not in rows:unreadable.add(os.getpid())
  total=rows.get(os.getpid(),{}).get('rss_bytes',0)+sum(r['rss_bytes'] for r in live_owned(owned,rows));peak_rss=max(peak_rss,total);samples+=1
  if total>rss_limit_bytes:rss_exceeded=True
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
   child=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env,cwd=cwd)
   while True:
    observe()
    if unreadable:raise RuntimeError('owned process inspection uncertain')
    if rss_exceeded:break
    if state['signals']:break
    if time.monotonic()>=deadline:timed_out=True;break
    if child.poll() is not None:break
    time.sleep(.05)
 except BaseException as e:error=type(e).__name__
 finally:
  if child is not None:
   observe()
   # Trusted inference has no state requiring graceful shutdown. Kill every
   # live owned identity immediately; never leave an allocation grace window.
   until=time.monotonic()+2
   while True:
    signal_owned(signal.SIGKILL);reap_adopted()
    if not live_owned(owned,observe()) or time.monotonic()>=until:break
    time.sleep(.02)
   child.poll()
   if child.returncode is None:error='UnreapedLeader'
  remaining=live_owned(owned,observe());reap_adopted()
 evidence={'rss_limit_bytes':rss_limit_bytes,'rss_limit_exceeded':rss_exceeded,'peak_summed_owned_rss_bytes':peak_rss,'rss_samples':samples,'rss_accounting':'Conservative sum of supervisor plus all owned live-process RSS; shared resident pages may be counted repeatedly. Not unique physical usage; sampled every 50ms with possible between-sample overshoot, not a kernel allocation cap.','exit_code':None if child is None else child.returncode,'wall_timeout':timed_out,'error_type':error,'termination_signals':state['signals'],'cleanup_signals':signals,'child_subreaper':True,'adopted_children_reaped':adopted_reaped,'owned_processes':list(owned.values()),'remaining_live_owned':remaining,'inspection_unreadable_pids':sorted(unreadable),'no_executing_owned_processes_observed':not remaining and not unreadable,'termination_grace_seconds':0,'cleanup_poll_budget_seconds':2}
 return evidence
