#!/usr/bin/env python3
"""Guarded fixed-cache build and exact conditional K/D/S comparison."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CID = 'fx2_hidden_cache250k_v1'
PROFILE = 'operations/provenance/fx2_kda_carry_toolchain_20260913.json'


def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    out = ROOT/'results'/CID
    experiment = json.loads((ROOT/'operations/adaptive/experiments'/(CID+'.json')).read_text())
    toolchain = json.loads((ROOT/PROFILE).read_text())['toolchain']
    phases = []
    env = {**os.environ, 'PYTHONPATH':str(ROOT)+os.pathsep+str(ROOT/'tools'),
           'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
           'TMPDIR':str(out/'tmp'),'LC_ALL':'C'}
    def verify():
        for r in experiment['inputs']:
            if sha(ROOT/r['path']) != r['sha256'].removeprefix('sha256:'):
                raise ValueError('input differs: '+r['path'])
        for r in toolchain:
            if sha(Path(r['path'])) != r['sha256']: raise ValueError('toolchain differs: '+r['name'])
    def run(label, command, stop):
        marker = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
        with marker.open('a') as f: f.write(json.dumps(dict(phase=label,event='start'))+'\n')
        start = time.monotonic()
        with (out/(label+'.stdout')).open('xb') as stdout, (out/(label+'.stderr')).open('xb') as stderr:
            p = subprocess.run(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=stop)
        row = dict(phase=label,command=command,returncode=p.returncode,elapsed_seconds=time.monotonic()-start)
        phases.append(row); (out/(label+'.execution.json')).write_text(json.dumps(row,indent=2)+'\n')
        with marker.open('a') as f: f.write(json.dumps(dict(phase=label,event='end'))+'\n')
        if p.returncode: raise ValueError('subprocess failed: '+label)
    result = dict(candidate_id=CID,status='execution_failed',objective_credit_bytes=0,
                  full_corpus_score_bytes=None,complete_package_bytes=None,standalone_decoder=False,
                  larger_gate_authorized=False)
    try:
        verify()
        if os.sched_getaffinity(0) != {3}: raise ValueError('CPU3 required')
        snapshot = Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
        if (snapshot/'program.py').read_bytes() != (ROOT/'tools/fx2_hidden_cache250k_v1.py').read_bytes():
            raise ValueError('sealed program differs')
        (out/'tmp').mkdir()
        native = ROOT/'results/fx2_residual_features250k_v3/work/native'
        for suffix in ('features','coder'):
            for phase in ('decode','repeat'):
                if sha(native/('encode.'+suffix)) != sha(native/(phase+'.'+suffix)):
                    raise ValueError('retained native observation differs')
        for phase in ('repeat','untraced'):
            if sha(native/'encode.arc') != sha(native/(phase+'.arc')):
                raise ValueError('retained native archive differs')
        compiler = next(r['path'] for r in toolchain if r['name']=='g++')
        for label in ('cache','cache-repeat'):
            command = [compiler,'-std=c++17','-O2','-shared','-fPIC','-fno-exceptions','-fno-rtti',
                       str(ROOT/'tools/fx2_hidden_cache_bridge_v1.cpp'),'-o',str(out/(label+'.so'))]
            run(label+'-compile',command,60)
        if sha(out/'cache.so') != sha(out/'cache-repeat.so'): raise ValueError('build repeat differs')
        if (out/'cache.so').stat().st_size > 65536: raise ValueError('experimental library ceiling')
        source_bytes = sum((ROOT/p).stat().st_size for p in
                           ('lib/fx2_hidden_cache_v1.hpp','tools/fx2_hidden_cache_bridge_v1.cpp'))
        if source_bytes > 16384: raise ValueError('authored kernel source ceiling')
        command = [sys.executable,str(snapshot/'program.py'),str(ROOT),str(out)]
        run('project',command+['project'],90)
        rows = {}
        for arm in ('K','D','S'):
            for phase in ('encode','decode','repeat'):
                library = out/('cache-repeat.so' if phase=='repeat' else 'cache.so')
                run(arm+'-'+phase,command+[phase,arm,str(library)],240)
                rows[arm+'-'+phase] = json.loads((out/(arm+'-'+phase+'.json')).read_text())
            reference = rows[arm+'-encode']
            for phase in ('decode','repeat'):
                other = rows[arm+'-'+phase]
                for k in reference:
                    if k != 'operation' and reference[k] != other[k]:
                        raise ValueError('independent inverse/repeat differs: '+arm+' '+k)
            if sha(out/(arm+'-encode.arc')) != sha(out/(arm+'-repeat.arc')):
                raise ValueError('archive repeat differs')
        if (out/'K-encode.arc').read_bytes() != (native/'encode.arc').read_bytes():
            raise ValueError('P/K archive differs')
        projection = json.loads((out/'projection.json').read_text())
        if rows['K-encode']['probability_sha256'] != projection['parent_count_sha256']:
            raise ValueError('P/K count sequence differs')
        for field in ('controller_state_sha256','final_state_sha256','queries','queries_with_neighbors',
                      'neighbors_selected','active_expert_events','hypothetical_changed_events','insertions'):
            if rows['K-encode'][field] != rows['D-encode'][field]: raise ValueError('K/D state differs: '+field)
        verify()
        gain = projection['parent_archive_bytes']-rows['D-encode']['archive_bytes']
        control = rows['S-encode']['archive_bytes']-rows['D-encode']['archive_bytes']
        result.update(status='passed',projection=projection,arms={a:rows[a+'-encode'] for a in 'KDS'},
            exact_inverses=True,archive_repeats=True,probability_and_state_repeats=True,
            parent_bookkeeping_identity=True,bookkeeping_treatment_state_identity=True,
            experimental_library_bytes=(out/'cache.so').stat().st_size,library_sha256=sha(out/'cache.so'),
            library_build_repeat=True,kernel_source_bytes=source_bytes,
            gain_parent_bytes=gain,gain_control_bytes=control,conditional_prediction_pass=gain>0 and control>0,
            inputs_reverified=len(experiment['inputs']),
            verdict='Conditional cache gain warrants separately priced native integration.' if gain>0 and control>0
                    else 'This fixed hidden-cache configuration does not pass the conditional archive/control comparison.')
    except Exception as exc:
        result.update(error=str(exc),failure_class='implementation-resource-or-evidence',
                      verdict='No valid terminal compression inference; preserve completed phases.')
    result['phases'] = phases
    artifacts = [dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p))
                 for p in sorted(out.rglob('*')) if p.is_file()]
    (out/'artifacts.json').write_text(json.dumps(dict(files=artifacts),indent=2)+'\n')
    (out/'decision.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result.get(k) for k in ('status','gain_parent_bytes','gain_control_bytes','error','verdict')}))
    return 0 if result['status']=='passed' else 1


if __name__ == '__main__': raise SystemExit(main())
