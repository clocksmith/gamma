"""One lab-owned matched-training comparison with finite native confirmation."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.evidence.history import materialize
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget
from .fx2_training_capture import source_members


def write(path, value): publish_immutable_artifact(path, canonical_bytes(value)+b'\n')


def run(root, output, experiment_path, closure_path, plan_path):
    experiment=json.loads(experiment_path.read_bytes()); plan=json.loads(plan_path.read_bytes())
    for row in experiment['inputs']:
        if fingerprint(root/row['path'],root)['sha256'] != row['sha256'].removeprefix('sha256:'):
            raise ValueError('bound input changed: '+row['path'])
    for path,digest in plan['build_tools']:
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest: raise ValueError('build tool changed')
    output.mkdir(parents=True,exist_ok=True); snapshot=output/'snapshot'
    materialize(root,json.loads(closure_path.read_bytes()),snapshot)
    native=output/'native'; native.mkdir()
    for name,data in source_members(snapshot/plan['native_source_zip']).items():
        path=native/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
    caps=plan['caps'];env={'PATH':'/usr/bin:/bin','PYTHONPATH':str(snapshot/'src'),'PYTHONDONTWRITEBYTECODE':'1',
        'OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','PYTHONHASHSEED':'0','LC_ALL':'C','TMPDIR':str(native)}
    context=ExecutionContext(experiment['experimentId'],snapshot,native,
        ResourceBudget(tuple(caps['cpus']),caps['memory_bytes'],caps['scratch_bytes'],caps['wall_seconds']),
        BuildProfile(tuple(plan['compile_command']),tuple(map(tuple,plan['build_tools']))),tuple(env.items()))
    records=[]
    with CgroupMemoryGuard.current(caps['memory_bytes']) as guard:
        executor=CommandExecutor(context,resident_guard=guard)
        def phase(name,argv,seconds=360):
            measured=['/usr/bin/time','-f','{"maximum_process_rss_kib":%M,"user_seconds":%U,"system_seconds":%S,"exit_status":%x}',
                      '-o',str(native/(name+'.rusage.json')),*argv]
            outcome,record=executor.run(name,measured,PhaseLimits(seconds,seconds+10,plan['address_space_bytes'],caps['scratch_bytes']))
            records.append(record)
            scratch=native/'ppm.temp'
            if scratch.exists():
                if scratch.is_symlink() or not scratch.is_file(): raise ValueError('unexpected PPM scratch')
                scratch.unlink()
            if outcome.classification!='completed': raise RuntimeError('phase failed: '+name)
            record['rusage']=json.loads((native/(name+'.rusage.json')).read_bytes())
        phase('matched-training',[plan['python'],'-m','gamma_enwiki9.adapters.fx2_matched_training','--root',str(snapshot),
               '--output',str(output/'training'),'--plan',str(snapshot/plan_path.relative_to(root))],1500)
        phase('build',plan['compile_command'])
        binary=native/'cmix'
        if fingerprint(binary,root)['sha256'] != fingerprint(snapshot/plan['parent_binary'],root)['sha256']:
            raise ValueError('native release rebuild differs')
        models={'P':snapshot/plan['parent_packed'],**{a:output/'training'/a/'weights.tfwc2' for a in ('A','J')}}
        measured={}
        def replay(population,arms):
            raw=snapshot/plan['populations'][population]['raw']; measured[population]={}
            for arm in arms:
                stem=population+'-'+arm
                archive=native/(stem+'.arc'); inverse=native/(stem+'.raw'); repeat=native/(stem+'.repeat.arc')
                for action,mode,source,destination in [('encode','-c',raw,archive),('decode','-d',archive,inverse),('repeat','-c',inverse,repeat)]:
                    phase(stem+'-'+action,[str(binary),mode,str(native/'dictionary/english.dic'),str(source),str(destination),'--transformer',str(models[arm])])
                if inverse.read_bytes()!=raw.read_bytes() or archive.read_bytes()!=repeat.read_bytes(): raise ValueError('inverse/repeat differs')
                if arm=='P' and archive.read_bytes()!=(snapshot/plan['populations'][population]['parent_archive']).read_bytes():
                    raise ValueError('parent archive differs')
                measured[population][arm]={'archive_bytes':archive.stat().st_size,'packed_bytes':models[arm].stat().st_size,
                    'archive':fingerprint(archive,root),'raw':fingerprint(inverse,root),'repeat':fingerprint(repeat,root),
                    'component_bytes':archive.stat().st_size+2*models[arm].stat().st_size,'inverse_exact':True,'repeat_exact':True}
        replay('development',('P','A','J'))
        # One predeclared ranking; confirmation cannot change the selected checkpoint.
        selected=min(('P','A','J'),key=lambda arm:(measured['development'][arm]['component_bytes'],('P','A','J').index(arm)))
        write(output/'selection.json',{'selected':selected,'rule':plan['selection'],'development':measured['development'],
              'models':{a:fingerprint(p,root) for a,p in models.items()},'confirmation_opened':False})
        replay('confirmation',('P',selected) if selected!='P' else ('P',))
        training=json.loads((output/'training/comparison.json').read_bytes())
        result={'schema':'gamma.enwiki9.fx2-matched-native-comparison.v1','candidate_id':experiment['experimentId'],
            'measurements':measured,'selected':selected,'training':training['arms'],'commands':records,
            'source_and_executable_unchanged':True,'source_zip':fingerprint(snapshot/plan['native_source_zip'],root),
            'binary':fingerprint(binary,root),'model_copies':2,'full_corpus_score_bytes':None,'objective_credit_bytes':0,
            'accounting_scope':'Finite raw-input archives plus two packed model copies; shared unchanged code, dictionary and options cancel in this comparison. No assembled delivery score.',
            'limitations':['PPMd training priors frozen from P; full native archives rerun all affected state.',
                'Development loss uses 512 causal warmup rows and128 truths at four actual piece starts.',
                'Approximate reference backward; native forward is authoritative.',
                'Confirmation is outside these training windows but historically exposed; no unseen-data claim.',
                'No prefix gain extrapolation; full-corpus score and qualification unknown.']}
        result['confirmation_component_gain']=measured['confirmation']['P']['component_bytes']-measured['confirmation'][selected]['component_bytes']
        result['confirmation_payload_gain']=measured['confirmation']['P']['archive_bytes']-measured['confirmation'][selected]['archive_bytes']
        result['paying_descendant']=selected!='P' and result['confirmation_component_gain']>0
        result['scale_ready']=result['paying_descendant'] and result['confirmation_payload_gain']>0
        write(output/'comparison.json',result)
    write(output/'artifacts.json',{'artifacts':[fingerprint(p,root) for p in sorted(output.rglob('*')) if p.is_file()]})
    return result


def main():
    parser=argparse.ArgumentParser()
    for n in ('root','output','experiment','closure','plan'):parser.add_argument('--'+n,type=Path,required=True)
    a=parser.parse_args();r=run(a.root.resolve(),a.output.resolve(),a.experiment.resolve(),a.closure.resolve(),a.plan.resolve())
    print(json.dumps({k:r[k] for k in ('selected','confirmation_component_gain','confirmation_payload_gain','scale_ready')}))

if __name__=='__main__': main()
