#!/usr/bin/env python3
"""Bounded repeated conditional attribution of retained native KDA trajectories."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
CID='fx2_kda_conditional_cost250k_v1'

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    out=ROOT/'results'/CID;e=json.loads((ROOT/'operations/adaptive/experiments'/(CID+'.json')).read_text())
    for r in e['inputs']:
        if digest(ROOT/r['path'])!=r['sha256'].removeprefix('sha256:'):raise ValueError('bound input differs')
    snapshot=Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
    if (snapshot/'program.py').read_bytes()!=(ROOT/'tools/fx2_kda_conditional_cost_v1.py').read_bytes():raise ValueError('sealed source differs')
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
            r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=120)
        row=dict(phase=label,command=cmd,returncode=r.returncode,elapsed_seconds=time.monotonic()-started)
        (out/(label+'.execution.json')).write_text(json.dumps(row,indent=2)+'\n');phases.append(row)
        with marker.open('a') as f:f.write(json.dumps(dict(phase=label,event='end'))+'\n')
        if r.returncode:raise ValueError('attribution subprocess failed')
    if (out/'first.json').read_bytes()!=(out/'repeat.json').read_bytes():raise ValueError('numeric receipt bytes differ')
    result=json.loads((out/'first.json').read_text());result.update(candidate_id=CID,numerical_receipt_byte_repeat=True,phases=phases,
        verdict='Fixed-trajectory opportunity only; no implemented selector or new archive. The native carry regression remains unchanged.')
    (out/'decision.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ['ideal_bits_saved','positive_D_pieces','PD_certificate','PDS_certificate','fixed_trajectory_selector_headroom_pass']}))

if __name__=='__main__':main()
