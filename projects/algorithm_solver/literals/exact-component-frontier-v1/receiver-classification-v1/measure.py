"""Trusted native-launch child resource meter; source strings never evaluated here."""
import json,os,subprocess,sys,time
from pathlib import Path
start=time.monotonic();child=subprocess.Popen(sys.argv[2:]);pid,status,usage=os.wait4(child.pid,0);child.returncode=os.waitstatus_to_exitcode(status)
Path(sys.argv[1]).write_text(json.dumps({'exit_code':child.returncode,'wall_seconds':time.monotonic()-start,'user_cpu_seconds':usage.ru_utime,'system_cpu_seconds':usage.ru_stime,'peak_rss_KiB':usage.ru_maxrss,'measurement':'Linux wait4 reaped single parser child maximum RSS, not process-tree RSS; expected512MiB not hard RAM limit'},sort_keys=True)+'\n')
raise SystemExit(child.returncode if child.returncode>=0 else 128-child.returncode)
