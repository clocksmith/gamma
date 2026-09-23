"""Lab-owned coverage/preservation training and deployed measurement, one frozen plan."""
from __future__ import annotations
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from gamma_enwiki9.evidence.artifacts import canonical_bytes,fingerprint,publish_immutable_artifact
from gamma_enwiki9.evidence.history import materialize
from gamma_enwiki9.execution.commands import CommandExecutor,PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile,ExecutionContext,ResourceBudget
from .fx2_training_capture import source_members
from .fx2_trajectory_native_v1 import adapt
from .fx2_coverage_costs_v1 import costs,deltas
from .fx2_coverage_preservation_v1 import ARMS,target_sets,partition_name


def write(path,value):publish_immutable_artifact(path,canonical_bytes(value)+b'\n')
def same(a,b):return fingerprint(a,a.parent)['sha256']==fingerprint(b,b.parent)['sha256']


def select(development):
    eligible=[a for a in ARMS if development[a]['archive_bytes']<development['P']['archive_bytes'] and development[a]['component_bytes']<development['P']['component_bytes']]
    selected=min(eligible,key=lambda a:(development[a]['component_bytes'],list(ARMS).index(a))) if eligible else 'P'
    return selected,eligible


def run(root,output,experiment_path,closure_path,plan_path):
    experiment=json.loads(experiment_path.read_bytes());plan=json.loads(plan_path.read_bytes())
    for row in experiment['inputs']:
        if fingerprint(root/row['path'],root)['sha256']!=row['sha256'].removeprefix('sha256:'):raise ValueError('bound input changed: '+row['path'])
    for path,digest in plan['build_tools']+plan['runtime_files']:
        if fingerprint(Path(path),Path(path).parent)['sha256']!=digest:raise ValueError('host tool/runtime changed: '+path)
    output.mkdir(parents=True,exist_ok=True);snapshot=output/'snapshot';materialize(root,json.loads(closure_path.read_bytes()),snapshot)
    native=output/'native';plain=output/'plain';native.mkdir();plain.mkdir()
    members,receipt=adapt(snapshot/plan['native_source_zip'],snapshot/plan['observer']);write(output/'adapter.json',{'changes':receipt})
    for directory,files in [(native,members),(plain,source_members(snapshot/plan['native_source_zip']))]:
        for name,data in files.items():
            path=directory/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    tokens=(snapshot/plan['tokens']).read_bytes();masks=target_sets(plan);counts={}
    for row in range(len(tokens)//2):
        key=partition_name(row,row>0 and tokens[2*(row-1)+1]!=2,masks);counts[key]=counts.get(key,0)+1
    write(output/'mask.json',{'tokens':fingerprint(snapshot/plan['tokens'],root),'sets':{k:sorted(v) for k,v in masks.items()},
        'partition_order':['narrow','broad','preservation'],'disjoint_target_counts':counts,'coordinate':'zero-based modeled target rows; corresponding neural prediction is row-1; no partition resets'})
    caps=plan['caps'];env={'PATH':'/usr/bin:/bin','PYTHONPATH':str(snapshot/'src'),'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','PYTHONHASHSEED':'0','LC_ALL':'C','TMPDIR':str(native)}
    context=ExecutionContext(experiment['experimentId'],snapshot,native,ResourceBudget(tuple(caps['cpus']),caps['memory_bytes'],caps['scratch_bytes'],caps['wall_seconds']),BuildProfile(tuple(plan['compile_command']),tuple(map(tuple,plan['build_tools']))),tuple(env.items()))
    records=[];measured={};models={}
    with CgroupMemoryGuard.current(caps['memory_bytes']) as guard:
        def phase(name,argv,seconds=360,capture=None):
            ctx=replace(context,environment=tuple({**env,**({'GAMMA_ATTRIBUTION_CAPTURE':str(capture)} if capture else {})}.items()))
            measured_argv=['/usr/bin/time','-f','{"maximum_process_rss_kib":%M,"user_seconds":%U,"system_seconds":%S,"exit_status":%x}','-o',str(native/(name+'.rusage.json')),*argv]
            outcome,record=CommandExecutor(ctx,resident_guard=guard).run(name,measured_argv,PhaseLimits(seconds,seconds+10,plan['address_space_bytes'],caps['scratch_bytes']))
            scratch=native/'ppm.temp'
            if scratch.exists():
                if scratch.is_symlink() or not scratch.is_file():raise ValueError('unexpected scratch ownership')
                scratch.unlink()
            record['rusage']=json.loads((native/(name+'.rusage.json')).read_bytes());records.append(record);write(output/(name+'.command.json'),record)
            if outcome.classification!='completed':raise RuntimeError('phase failed: '+name)
            print(json.dumps({'phase':name,'elapsed_seconds':record['elapsed_seconds']}),flush=True)
        phase('training',[plan['python'],'-m','gamma_enwiki9.adapters.fx2_coverage_preservation_v1','--root',str(snapshot),'--output',str(output/'training'),'--plan',str(snapshot/plan_path.relative_to(root))],1800)
        phase('observer-build',plan['compile_command']);phase('plain-build',plan['compile_command']+['-C',str(plain)])
        if not same(plain/'cmix',snapshot/plan['parent_binary']):raise ValueError('unobserved native rebuild changed')
        models={'P':snapshot/plan['parent_packed'],**{a:output/'training'/a/'weights.tfwc2' for a in ARMS}}
        def replay(population,arms,observe):
            spec=plan['populations'][population];raw=snapshot/spec['raw'];measured[population]={}
            for arm in arms:
                stem=population+'-'+arm;archive=native/(stem+'.arc');inverse=native/(stem+'.raw');repeat=native/(stem+'.repeat.arc')
                for action,mode,source,destination in [('encode','-c',raw,archive),('decode','-d',archive,inverse),('repeat','-c',inverse,repeat)]:
                    cap=native/(stem+'-'+action) if observe else None
                    phase(stem+'-'+action,[str((native if observe else plain)/'cmix'),mode,str(native/'dictionary/english.dic'),str(source),str(destination),'--transformer',str(models[arm])],capture=cap)
                    if observe and action!='encode':
                        for suffix in ('.bits','.neural','.tokens','.priors'):
                            if not same(Path(str(cap)+suffix),native/(stem+'-encode'+suffix)):raise ValueError('trajectory repeat differs')
                if not same(inverse,raw) or not same(archive,repeat):raise ValueError('inverse or archive repeat differs')
                if arm=='P' and not same(archive,snapshot/spec['parent_archive']):raise ValueError('parent archive differs')
                row={'archive_bytes':archive.stat().st_size,'packed_bytes':models[arm].stat().st_size,'component_bytes':archive.stat().st_size+2*models[arm].stat().st_size,
                    'archive':fingerprint(archive,root),'raw':fingerprint(inverse,root),'repeat':fingerprint(repeat,root),'inverse_exact':True,'repeat_exact':True}
                if observe:
                    control=native/(stem+'.unobserved.arc')
                    phase(stem+'-unobserved',[str(plain/'cmix'),'-c',str(native/'dictionary/english.dic'),str(raw),str(control),'--transformer',str(models[arm])])
                    if not same(archive,control):raise ValueError('observer changed child archive')
                    row.update(costs=costs(native/(stem+'-encode'),tokens,plan),observer_archive_exact=True,
                        priors_equal_training_capture=same(native/(stem+'-encode.priors'),snapshot/plan['priors']))
                measured[population][arm]=row
        replay('development250k',('P',*ARMS),True)
        development=measured['development250k'];selected,eligible=select(development)
        write(output/'selection.json',{'selected':selected,'rule':plan['selection'],'eligible_children':eligible,'models':{a:fingerprint(p,root) for a,p in models.items()},'development':development,'exposed1m_replay_started':False})
        if selected!='P':replay('exposed1m',('P',selected),False)
        training=json.loads((output/'training/comparison.json').read_bytes())
        result={'schema':'gamma.enwiki9.coverage-preservation-native.v1','candidate_id':experiment['experimentId'],'measurements':measured,
            'development_deltas':deltas(development),'selected':selected,'training':training,'commands':records,
            'models':{a:fingerprint(p,root) for a,p in models.items()},'narrow_reproduces_old_A_packed':same(models['N'],snapshot/plan['old_A_packed']),
            'exposed1m_replay_performed':selected!='P','all_children_regress_payload':all(development[a]['archive_bytes']>=development['P']['archive_bytes'] for a in ARMS),
            'joint_development_gain':bool(eligible),'source_and_executable_unchanged':True,'model_copies':2,'full_corpus_score_bytes':None,'objective_credit_bytes':0,
            'accounting_scope':'Actual archive plus two actual packed model copies; original unobserved code/dictionary/options unchanged. No assembled package or full-corpus score.',
            'limits':plan['limits']}
        result['exposed1m_joint_gain']=selected!='P' and all(measured['exposed1m'][selected][k]<measured['exposed1m']['P'][k] for k in ['archive_bytes','component_bytes'])
        write(output/'comparison.json',result)
    write(output/'artifacts.json',{'artifacts':[fingerprint(p,root) for p in sorted(output.rglob('*')) if p.is_file()]})
    return result


def main():
    p=argparse.ArgumentParser()
    for name in ('root','output','experiment','closure','plan'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(*(getattr(a,k).resolve() for k in ('root','output','experiment','closure','plan')))
if __name__=='__main__':main()
