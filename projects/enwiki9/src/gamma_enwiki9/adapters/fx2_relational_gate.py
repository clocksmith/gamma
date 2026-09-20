"""Lab-owned fixed P/K/I/S/W relational comparison, with original native replay."""
from __future__ import annotations
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import zipfile
from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.evidence.history import materialize
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget
from .fx2_relational_native import adapt
from .fx2_training_capture import source_members


def write(path,value):publish_immutable_artifact(path,canonical_bytes(value)+b'\n')

def source_zip(path,members):
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(members.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,data,compresslevel=9)

def equal(a,b):
    if a.stat().st_size!=b.stat().st_size:raise ValueError('size mismatch: '+str(a)+' '+str(b))
    with a.open('rb') as x,b.open('rb') as y:
        while block:=x.read(1<<20):
            if block!=y.read(len(block)):raise ValueError('byte mismatch: '+str(a)+' '+str(b))

def run(root,output,experiment_path,closure_path,plan_path):
    experiment=json.loads(experiment_path.read_bytes());plan=json.loads(plan_path.read_bytes())
    for row in experiment['inputs']:
        if fingerprint(root/row['path'],root)['sha256']!=row['sha256'].removeprefix('sha256:'):raise ValueError('bound input changed: '+row['path'])
    for path,digest in plan['build_tools']:
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('build tool changed: '+path)
    output.mkdir(parents=True,exist_ok=True);snapshot=output/'snapshot';materialize(root,json.loads(closure_path.read_bytes()),snapshot)
    native=output/'native';native.mkdir()
    members,adapter=adapt(snapshot/plan['native_source_zip'],snapshot/'lib');write(output/'adapter.json',adapter)
    for name,data in members.items():
        p=native/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    original=source_members(snapshot/plan['native_source_zip'])
    source_zip(output/'P-source.zip',original);source_zip(output/'S-source.zip',members)
    caps=plan['caps'];env={'PATH':'/usr/bin:/bin','PYTHONPATH':str(snapshot/'src'),'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','LC_ALL':'C','TMPDIR':str(native)}
    context=ExecutionContext(experiment['experimentId'],snapshot,native,ResourceBudget(tuple(caps['cpus']),caps['memory_bytes'],caps['scratch_bytes'],caps['wall_seconds']),BuildProfile(tuple(plan['compile_command']),tuple(map(tuple,plan['build_tools']))),tuple(env.items()))
    records=[];measurements={}
    with CgroupMemoryGuard.current(caps['memory_bytes']) as guard:
        def phase(name,argv,seconds=360,extra=None):
            current=replace(context,environment=tuple({**env,**(extra or {})}.items()))
            executor=CommandExecutor(current,resident_guard=guard)
            measured=['/usr/bin/time','-f','{"maximum_process_rss_kib":%M,"user_seconds":%U,"system_seconds":%S,"exit_status":%x}','-o',str(native/(name+'.rusage.json')),*argv]
            outcome,record=executor.run(name,measured,PhaseLimits(seconds,seconds+20,plan['address_space_bytes'],caps['scratch_bytes']));records.append(record)
            scratch=native/'ppm.temp'
            if scratch.exists():
                if scratch.is_symlink() or not scratch.is_file():raise ValueError('scratch ownership')
                scratch.unlink()
            write(output/(name+'.command.json'),record)
            if outcome.classification!='completed':raise RuntimeError('phase failed: '+name)
            print(json.dumps({'phase':name,'elapsed_seconds':record['elapsed_seconds']}),flush=True)
        phase('build',plan['compile_command']);binary=native/'cmix'
        first=fingerprint(binary,root);phase('clean',['/usr/bin/make','clean'],30);phase('build-repeat',plan['compile_command'])
        if first!=fingerprint(binary,root):raise ValueError('build repeat differs')
        parent=snapshot/plan['parent_binary'];weights=snapshot/plan['parent_packed'];dictionary=native/'dictionary/english.dic'
        delta=binary.stat().st_size-parent.stat().st_size
        zip_delta=(output/'S-source.zip').stat().st_size-(output/'P-source.zip').stat().st_size
        options=len('GAMMA_RELATIONAL_ARM=S')
        package={'binary_increment_per_copy':delta,'source_zip_increment':zip_delta,'required_option_bytes':options,
                 'executable_form_increment':2*delta+options,'source_form_increment':zip_delta+delta+options,
                 'counted_increment':min(2*delta+options,zip_delta+delta+options),'complete_package_bytes':None,
                 'scope':'Incremental same-model, dictionary and frontend comparison; diagnostic observer is conservatively included. Alternative forms are never added.',
                 'source':fingerprint(output/'S-source.zip',root),'binary':fingerprint(binary,root)}
        write(output/'package.json',package)
        if max(0,package['counted_increment'])>65536:raise ValueError('declared source/package budget exceeded')
        # Zero tuning budget: source and parameters fixed before either retained confirmation population is opened.
        write(output/'selection.json',{'selected':'S','tuning_trials':0,'arms':['P','K','I','S','W'],'package':package,'confirmation_opened':False})
        for population,pop in plan['populations'].items():
            raw=snapshot/pop['raw'];measurements[population]={}
            # Uninstrumented P is a fresh direct control, including on previously
            # unmeasured validation. Its native arithmetic payload is authority.
            baseline=native/(population+'-original.arc')
            phase(population+'-original',[str(parent),'-c',str(dictionary),str(raw),str(baseline),'--transformer',str(weights)])
            for arm in 'PKISW':
                stem=population+'-'+arm;archive=native/(stem+'.arc');restored=native/(stem+'.decoded');repeat=native/(stem+'.repeat.arc')
                for action,mode,source,dest in [('encode','-c',raw,archive),('decode','-d',archive,restored),('repeat','-c',restored,repeat)]:
                    capture=native/(stem+'-'+action)
                    phase(stem+'-'+action,[str(binary),mode,str(dictionary),str(source),str(dest),'--transformer',str(weights)],extra={'GAMMA_RELATIONAL_ARM':arm,'GAMMA_RELATIONAL_CAPTURE':str(capture)})
                    equal(raw,Path(str(capture)+'.raw'))
                    if action!='encode':
                        for suffix in ['.state','.parent','.json']:equal(Path(str(capture)+suffix),native/(stem+'-encode'+suffix))
                    # Every prediction of the original parent and its truth is
                    # checked across arms; this witnesses observations, not all parent state.
                    equal(Path(str(capture)+'.parent'),native/(population+'-P-encode.parent'))
                equal(raw,restored);equal(archive,repeat)
                if arm in 'PK':equal(archive,baseline)
                if arm=='K':equal(native/(stem+'-encode.state'),native/(population+'-P-encode.state'))
                if arm=='S':equal(native/(stem+'-encode.state'),native/(population+'-K-encode.state'))
                measurements[population][arm]={'archive_bytes':archive.stat().st_size,'archive':fingerprint(archive,root),'inverse':fingerprint(restored,root),'repeat':fingerprint(repeat,root),'diagnostics':json.loads((native/(stem+'-encode.json')).read_bytes()),'exact_inverse':True,'repeat_exact':True,'parent_predictions_exact':True,'introduced_state_exact':True}
            cells=measurements[population];gain=cells['P']['archive_bytes']-cells['S']['archive_bytes']
            result={'population':population,'measurements':cells,'shared_payload_gain':gain,'shared_net_gain':gain-package['counted_increment'],'shared_over_independent':cells['I']['archive_bytes']-cells['S']['archive_bytes'],'shared_over_wrong':cells['W']['archive_bytes']-cells['S']['archive_bytes']}
            write(output/(population+'.json'),result)
        supported=all(c['S']['archive_bytes']+package['counted_increment']<c['P']['archive_bytes'] and c['S']['archive_bytes']<min(c['I']['archive_bytes'],c['W']['archive_bytes']) for c in measurements.values())
        result={'schema':'gamma.enwiki9.relational-binding-comparison.v1','candidate_id':experiment['experimentId'],'measurements':measurements,'package':package,'mechanism_supported':supported,'commands':records,'objective_credit_bytes':0,'full_corpus_score_bytes':None,
            'witness_scope':'Complete introduced relational/parser state at retained epoch boundaries and termination; every parent binary probability/truth, complete inverse emissions. Not a hash of complete parent predictor state.',
            'numerics':'Q48 floored largest-remainder posterior; 16-bit rounded output. Exact rational synthetic tests bound one update error; no corpus one-bit or complete-package guarantee.',
            'limits':['Depth-one word bindings; no edited copies or recursive templates.','Fixed4096-modeled-byte donor epochs and4slots per role; FIFO64 completed word records per role.','Validation and confirmation historically exposed; no unseen-data claim.','Shared-host timing only; no prize qualification.']}
        write(output/'comparison.json',result)
    write(output/'artifacts.json',{'artifacts':[fingerprint(p,root) for p in sorted(output.rglob('*')) if p.is_file()]})
    return result

def main():
    parser=argparse.ArgumentParser()
    for key in ['root','output','experiment','closure','plan']:parser.add_argument('--'+key,type=Path,required=True)
    a=parser.parse_args();result=run(a.root.resolve(),a.output.resolve(),a.experiment.resolve(),a.closure.resolve(),a.plan.resolve());print(json.dumps({'mechanism_supported':result['mechanism_supported']}))
if __name__=='__main__':main()
