"""Read-only service monitor; writes only experiment-owned admission evidence.

Never changes the provider. A model driver must honor allowed=false or stale data.
Run on the same host as the experiment and the named systemd user service.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def observe(unit, baseline, minimum_memory):
    now=dt.datetime.now(dt.timezone.utc)
    status=subprocess.run(['systemctl','--user','is-active',unit],capture_output=True,text=True,timeout=5)
    journal=subprocess.run(['journalctl','--user','-u',unit,'-n','10','--no-pager','-o','cat'],capture_output=True,text=True,timeout=5)
    latest=None
    for line in reversed(journal.stdout.splitlines()):
        try: row=json.loads(line)
        except (ValueError,TypeError): continue
        if isinstance(row,dict) and isinstance(row.get('owner'),dict) and row['owner'].get('measurements'):
            latest=row;break
    memory={}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key,value=line.split(':',1);memory[key]=int(value.split()[0])*1024
    count=latest['owner']['measurements'].get('stageAdmitted') if latest else None
    source_at=latest.get('at') if latest else None
    age=(now-dt.datetime.fromisoformat(source_at.replace('Z','+00:00'))).total_seconds() if source_at else None
    reasons=[]
    if status.returncode or status.stdout.strip()!='active':reasons.append('provider_not_active')
    if journal.returncode or age is None or not 0<=age<=15:reasons.append('provider_observation_stale_or_missing')
    if count!=baseline:reasons.append('provider_admitted_work_since_idle_baseline')
    if memory.get('MemAvailable',0)<minimum_memory:reasons.append('memory_headroom_below_floor')
    return {'schema':'gamma.channel-gain-service-guard/v1','checkedAt':now.isoformat(),'allowed':not reasons,'reasons':reasons,'unit':unit,'stageAdmitted':count,'baselineStageAdmitted':baseline,'sourceObservedAt':source_at,'sourceAgeSeconds':age,'availableMemoryBytes':memory.get('MemAvailable'),'minimumAvailableMemoryBytes':minimum_memory,'providerModified':False}


def main():
    p=argparse.ArgumentParser();p.add_argument('--unit',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--baseline-stage-admitted',type=int,required=True);p.add_argument('--minimum-memory-bytes',type=int,required=True);p.add_argument('--duration-seconds',type=float,required=True);a=p.parse_args()
    stop=False
    def terminate(*_):
        nonlocal stop
        stop=True
    signal.signal(signal.SIGTERM,terminate);signal.signal(signal.SIGINT,terminate)
    deadline=time.monotonic()+a.duration_seconds
    log=a.output.with_suffix('.jsonl')
    def save(row):
        temporary=a.output.with_name(a.output.name+f'.{os.getpid()}.tmp')
        temporary.write_text(json.dumps(row)+'\n');os.replace(temporary,a.output)
        with log.open('a') as f:f.write(json.dumps(row)+'\n')
    try:
        while not stop and time.monotonic()<deadline:
            try:row=observe(a.unit,a.baseline_stage_admitted,a.minimum_memory_bytes)
            except Exception as e:row={'checkedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'allowed':False,'reasons':['monitor_error'],'error':str(e),'providerModified':False}
            save(row)
            if not row['allowed']:print(json.dumps(row),flush=True)
            time.sleep(5)
    finally:save({'checkedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'allowed':False,'reasons':['monitor_stopped'],'providerModified':False})

if __name__=='__main__':main()
