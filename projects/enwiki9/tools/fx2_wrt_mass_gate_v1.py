#!/usr/bin/env python3
"""Guarded expert legal-mass correction on fixed native parent trajectories."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
CID='fx2_wrt_mass250k_v1'


def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    out=ROOT/'results'/CID
    ep=ROOT/'operations/adaptive/experiments'/(CID+'.json')
    experiment=json.loads(ep.read_text()); phases=[]
    env={**os.environ,'PYTHONPATH':str(ROOT)+os.pathsep+str(ROOT/'tools'),
         'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
         'TMPDIR':str(out/'tmp'),'LC_ALL':'C'}
    def verify():
        for r in experiment['inputs']:
            if sha(ROOT/r['path'])!=r['sha256'].removeprefix('sha256:'):
                raise ValueError('input differs: '+r['path'])
    def run(label, command):
        marker=Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
        with marker.open('a') as f:f.write(json.dumps(dict(phase=label,event='start'))+'\n')
        start=time.monotonic()
        with (out/(label+'.stdout')).open('xb') as stdout,(out/(label+'.stderr')).open('xb') as stderr:
            p=subprocess.run(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=150)
        row=dict(phase=label,command=command,returncode=p.returncode,elapsed_seconds=time.monotonic()-start)
        phases.append(row);(out/(label+'.execution.json')).write_text(json.dumps(row,indent=2)+'\n')
        with marker.open('a') as f:f.write(json.dumps(dict(phase=label,event='end'))+'\n')
        if p.returncode:raise ValueError('phase failed: '+label)
    result=dict(candidate_id=CID,status='execution_failed',objective_credit_bytes=0,
                full_corpus_score_bytes=None,complete_package_bytes=None,standalone_decoder=False,
                larger_gate_authorized=False)
    try:
        verify()
        if os.sched_getaffinity(0)!={3}:raise ValueError('CPU3 required')
        if json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON'])!={'path':str(ep.relative_to(ROOT)),'sha256':'sha256:'+sha(ep)}:
            raise ValueError('execution experiment differs')
        snapshot=Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
        if (snapshot/'program.py').read_bytes()!=(ROOT/'tools/fx2_wrt_mass250k_v1.py').read_bytes():
            raise ValueError('sealed program differs')
        (out/'tmp').mkdir()
        import io,zipfile
        old=ROOT/'results/fx2_attention_window250k_v2/work/native'
        if sha(old/'P-encode.probs')!=sha(old/'P-repeat.probs'):raise ValueError('retained neural repeat differs')
        for phase in ('repeat','untraced'):
            if sha(old/'P-encode.arc')!=sha(old/('P-'+phase+'.arc')):raise ValueError('retained parent archive differs')
        if sha(old/'P-encode.arc')!=sha(ROOT/'results/fx2_wrt_elision250k_v2/K-encode.arc'):
            raise ValueError('native parent and conditional population differ')
        package=json.loads((ROOT/'results/fx2_expert_release250k_v3/package.json').read_text())
        if sha(old/'cmix-P')!=package['deliveries']['P']['binary']['sha256'].removeprefix('sha256:'):
            raise ValueError('native neural-export parent binary differs')
        with zipfile.ZipFile(ROOT/'results/fx2_expert_release250k_v3/P-source.zip') as z:
            if z.read('src/predictor.cpp')!=(old/'src/predictor.cpp').read_bytes():raise ValueError('neural row source differs')
        command=[sys.executable,str(snapshot/'program.py'),str(ROOT),str(out)]
        run('project',command+['project']);rows={}
        for arm in ('K','M','S'):
            for phase in ('encode','decode','repeat'):
                run(arm+'-'+phase,command+[phase,arm])
                rows[arm+'-'+phase]=json.loads((out/(arm+'-'+phase+'.json')).read_text())
            reference=rows[arm+'-encode']
            for phase in ('decode','repeat'):
                other=rows[arm+'-'+phase]
                for k in reference:
                    if k!='operation' and reference[k]!=other[k]:raise ValueError('inverse/repeat differs: '+arm+' '+k)
            if sha(out/(arm+'-encode.arc'))!=sha(out/(arm+'-repeat.arc')):raise ValueError('archive repeat differs')
        if (out/'K-encode.arc').read_bytes()!=(ROOT/'results/fx2_wrt_elision250k_v2/D-encode.arc').read_bytes():
            raise ValueError('elision baseline bookkeeping differs')
        for a in ('M','S'):
            for k in ('grammar_state_sha256','final_state_sha256','causal_feature_sha256','elided_events'):
                if rows['K-encode'][k]!=rows[a+'-encode'][k]:raise ValueError('common causal state differs')
        if rows['K-encode']['changed_counts']!=0:raise ValueError('bookkeeping changes counts')
        verify();projection=json.loads((out/'projection.json').read_text())
        gain=projection['parent_archive_bytes']-rows['M-encode']['archive_bytes']
        increment=rows['K-encode']['archive_bytes']-rows['M-encode']['archive_bytes']
        control=rows['S-encode']['archive_bytes']-rows['M-encode']['archive_bytes']
        pays=gain>=3000 and increment>0 and control>0
        result.update(status='passed',projection=projection,arms={a:rows[a+'-encode'] for a in ('K','M','S')},
            exact_inverses=True,archive_repeats=True,state_and_action_repeats=True,
            elision_bookkeeping_identity=True,common_grammar_state_identity=True,
            native_neural_source_and_repeat_identity=True,
            kernel_source_bytes=(ROOT/'lib/fx2_wrt_mass_v1.py').stat().st_size,
            gain_parent_bytes=gain,gain_elision_bytes=increment,gain_rotated_control_bytes=control,
            native_pricing_authorized=pays,inputs_reverified=len(experiment['inputs']),
            screening_floor_bytes=3000,
            verdict='Expert legal-mass correction passes the frozen conditional headroom and controls; native pricing only.' if pays
                    else 'This fixed expert legal-mass correction fails conditional headroom or a matched control; no native or larger run.')
    except Exception as exc:
        result.update(error=str(exc),failure_class='implementation-resource-or-evidence',
                      verdict='Incomplete comparison; no scientific compression decision.')
    result['phases']=phases
    files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()]
    (out/'artifacts.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
    (out/'decision.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result.get(k) for k in ('status','gain_parent_bytes','gain_elision_bytes','gain_rotated_control_bytes','error','verdict')}))
    return 0 if result['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
