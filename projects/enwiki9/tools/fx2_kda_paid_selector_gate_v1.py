#!/usr/bin/env python3
"""Bounded exact paid selection of retained native KDA trajectories."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
CID='fx2_kda_paid_selector250k_v1'

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    out=ROOT/'results'/CID;e=json.loads((ROOT/'operations/adaptive/experiments'/(CID+'.json')).read_text())
    for r in e['inputs']:
        if digest(ROOT/r['path'])!=r['sha256'].removeprefix('sha256:'):raise ValueError('bound input differs')
    snapshot=Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
    if (snapshot/'program.py').read_bytes()!=(ROOT/'tools/fx2_kda_paid_selector250k_v1.py').read_bytes():raise ValueError('sealed source differs')
    native=ROOT/'results/fx2_kda_carry_opening250k_v1/work/native'
    for a in 'PKDS':
        for suffix in ('coder','state','arc'):
            if digest(native/(a+'-encode.'+suffix))!=digest(native/(a+'-repeat.'+suffix)):raise ValueError('retained repeated input differs')
    for suffix in ('coder','state','arc'):
        if digest(native/('P-encode.'+suffix))!=digest(native/('K-encode.'+suffix)):raise ValueError('P/K identity differs')
    env={**os.environ,'PYTHONPATH':str(ROOT),'PYTHONDONTWRITEBYTECODE':'1'};phases=[]
    marker=Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
    for label in ['first','repeat']:
        with marker.open('a') as f:f.write(json.dumps(dict(phase=label,event='start'))+'\n')
        cmd=[sys.executable,str(snapshot/'program.py'),str(ROOT),str(out/(label+'.json'))]
        started=time.monotonic()
        with (out/(label+'.stdout')).open('xb') as stdout,(out/(label+'.stderr')).open('xb') as stderr:
            r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=600)
        row=dict(phase=label,command=cmd,returncode=r.returncode,elapsed_seconds=time.monotonic()-started)
        (out/(label+'.execution.json')).write_text(json.dumps(row,indent=2)+'\n');phases.append(row)
        with marker.open('a') as f:f.write(json.dumps(dict(phase=label,event='end'))+'\n')
        if r.returncode:raise ValueError('attribution subprocess failed')
    for suffix in ('.json','.D.policy','.S.policy'):
        if (out/('first'+suffix)).read_bytes()!=(out/('repeat'+suffix)).read_bytes():raise ValueError('numeric receipt or policy differs')
    result=json.loads((out/'first.json').read_text());result.update(candidate_id=CID,numerical_receipt_byte_repeat=True,phases=phases,
        policy_byte_repeat=True,verdict='Paid ideal diagnostic only; no native decoder or archive credit. Fixed family closes if paid upper bound is nonpositive; positive bound needs finite replay and state-cost proof.')
    (out/'decision.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ['conditional_table_headroom_pass','fixed_family_paid_ideal_reject','control_separation']}))

if __name__=='__main__':main()
