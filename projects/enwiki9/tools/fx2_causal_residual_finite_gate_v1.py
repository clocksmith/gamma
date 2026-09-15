#!/usr/bin/env python3
"""Guarded finite-coder verification of the unchanged causal residual family."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
CID='fx2_causal_residual_finite250k_v1'

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    out=ROOT/'results'/CID
    e=json.loads((ROOT/'operations/adaptive/experiments'/(CID+'.json')).read_text())
    def verify():
        for r in e['inputs']:
            if digest(ROOT/r['path'])!=r['sha256'].removeprefix('sha256:'):raise ValueError('bound input differs: '+r['path'])
    verify()
    if os.sched_getaffinity(0)!={3}:raise ValueError('CPU3 affinity required')
    snapshot=Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
    if (snapshot/'program.py').read_bytes()!=(ROOT/'tools'/('fx2_causal_residual_finite250k_v1.py')).read_bytes():raise ValueError('sealed source differs')
    native=ROOT/'results/fx2_residual_features250k_v3/work/native'
    for suffix in ('features','coder'):
        expected=digest(native/('encode.'+suffix))
        for phase in ('decode','repeat'):
            if digest(native/(phase+'.'+suffix))!=expected:raise ValueError('retained observation repeat differs')
    for name in ('repeat.arc','untraced.arc'):
        if digest(native/name)!=digest(native/'encode.arc'):raise ValueError('retained archive repeat differs')
    if (native/'decode.raw').read_bytes()!=(native/'population.raw').read_bytes():raise ValueError('retained native inverse differs')
    marker=Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS']);phases=[]
    env={**os.environ,'PYTHONPATH':str(ROOT)+os.pathsep+str(ROOT/'tools'),'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}
    for label in ('first','repeat'):
        with marker.open('a') as f:f.write(json.dumps(dict(phase=label,event='start'))+'\n')
        cmd=[sys.executable,str(snapshot/'program.py'),str(ROOT),str(out/label)]
        start=time.monotonic()
        with (out/(label+'.stdout')).open('xb') as stdout,(out/(label+'.stderr')).open('xb') as stderr:
            p=subprocess.run(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=420)
        row=dict(phase=label,command=cmd,returncode=p.returncode,elapsed_seconds=time.monotonic()-start)
        (out/(label+'.execution.json')).write_text(json.dumps(row,indent=2)+'\n');phases.append(row)
        with marker.open('a') as f:f.write(json.dumps(dict(phase=label,event='end'))+'\n')
        if p.returncode:raise ValueError('bound subprocess failed')
    first={str(p.relative_to(out/'first')):digest(p) for p in (out/'first').rglob('*') if p.is_file()}
    repeat={str(p.relative_to(out/'repeat')):digest(p) for p in (out/'repeat').rglob('*') if p.is_file()}
    if first!=repeat:raise ValueError('complete conditional artifact repeat differs')
    verify();result=json.loads((out/'first/report.json').read_text())
    result.update(candidate_id=CID,status='passed',phases=phases,certificate_repeat_identical=True,all_conditional_artifacts_repeat_identical=True,
        retained_native_archive_and_observation_identities=True,inputs_reverified=len(e['inputs']),
        native_run=False,new_standalone_archive_bytes=None,new_standalone_compression_savings_bytes=0,larger_gate_authorized=False)
    (out/'decision.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('status','verdict','finite_replay')}))

if __name__=='__main__':main()
