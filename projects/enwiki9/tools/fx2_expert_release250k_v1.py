#!/usr/bin/env python3
"""Production equivalence and component pricing for the frozen expert mixture."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate,require,sha
ID='fx2_expert_release250k_v1'
PLAN='operations/provenance/'+ID+'_plan.json'
PROFILE='operations/provenance/fx2_kda_carry_toolchain_20260913.json'
PARENT='results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'
ADAPTER='operations/provenance/fx2_expert_release_adapter_v1.json'
RAW='results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.raw'
STORED='results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.stored'
REFERENCES={a:'results/fx2_expert_mix_opening250k_v1/work/native/'+a+'-encode.arc' for a in 'PD'}
CAPS=dict(cpus=[2],memory_bytes=9999998976,swap_bytes=0,scratch_bytes=24000000000,wall_seconds=1800)

class NativeGate(BaseGate):
    def verify(self):
        self.toolchain=json.loads(self.buffers[PROFILE]);super().verify()

def equal(a,b):
    require(a.stat().st_size==b.stat().st_size,'length mismatch:'+str(a))
    with a.open('rb') as x,b.open('rb') as y:
        while data:=x.read(1<<20):require(data==y.read(len(data)),'byte mismatch:'+str(a))

def cleanup(g,label):
    g.closure();p=g.work/'native/ppm.temp'
    r=dict(child_closure=True,present=p.exists(),content_hashed=False)
    if p.exists():
        require(p.is_file() and p.resolve()==p,'aliased temporary');s=p.stat()
        r.update(logical_bytes=s.st_size,allocated_bytes=s.st_blocks*512);p.unlink()
    r['cleanup_complete']=not p.exists();g.write(label+'-cleanup.json',r)

def source_zip(path,members):
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(members.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16;z.writestr(info,data,compresslevel=9)

def execute(g):
    plan=json.loads(g.buffers[PLAN]);require(plan['caps']==CAPS,'caps differ')
    native=g.work/'native';native.mkdir()
    package=json.loads(g.buffers[PARENT+'package.json']);adapter=json.loads(g.buffers[ADAPTER])
    omitted=set(adapter['omitted_source_members'])
    for row in package['source_members']+package['runtime_members']:
        name=row['path'].removeprefix(PARENT+'work/')
        if name=='cmix' or name in omitted:continue
        target=native/name
        if not target.exists():g.copy(row['path'],target)
    g.adapter(ADAPTER,native)
    for row in adapter['added_files']:g.copy(row['source']['path'],native/row['target'])
    g.copy(RAW,native/'population.raw')
    base_sources={r['path'].removeprefix(PARENT+'work/'):g.buffers[r['path']] for r in package['source_members']}
    release_sources={name:(native/name).read_bytes() for name in base_sources if name not in omitted}
    source_zip(g.result/'original-source.zip',base_sources)
    arms={};deliveries={}
    for arm in 'PD':
        members=dict(release_sources)
        if arm=='D':members['src/gamma-expert-release.h']=(native/'src/gamma-expert-release.h').read_bytes()
        source_zip(g.result/(arm+'-source.zip'),members)
        command=list(plan['compile_command'])
        if arm=='D':command=[arg+' -DGAMMA_EXPERT_RELEASE' if arg.startswith('CPPFLAGS_') else arg for arg in command]
        g.run(arm+'-compile',command,360,work=native)
        first=(native/'cmix').read_bytes()
        g.run(arm+'-compile-repeat',command,360,work=native)
        require((native/'cmix').read_bytes()==first,'build repeat differs')
        binary=native/('cmix-'+arm);binary.write_bytes(first);binary.chmod(0o755)
        g.binaries[str(binary)]=sha(binary)
        deliveries[arm]=dict(binary=g.artifact(binary),source_zip=g.artifact(g.result/(arm+'-source.zip')),
            uncompressed_source_bytes=sum(map(len,members.values())),source_members=len(members),
            compile_command=command,build_repeat_byte_equal=True)
        if arm=='P':
            try:g.run('preprocess',[str(binary),'-s','dictionary/english.dic','population.raw','population.stored'],180,work=native);equal(native/'population.stored',ROOT/STORED)
            finally:cleanup(g,'preprocess')
        for phase in ('encode','decode','repeat'):
            name=arm+'-'+phase
            if phase=='decode':args=['-d','dictionary/english.dic',arm+'-encode.arc',name+'.raw']
            else:args=['-c','dictionary/english.dic','population.raw' if phase=='encode' else arm+'-decode.raw',name+'.arc']
            try:g.run(name,[str(binary),*args,'--transformer','models/6m-q4-fp32.tfwc2'],180,work=native)
            finally:cleanup(g,name)
            if phase=='decode':equal(native/(name+'.raw'),native/'population.raw')
            if phase=='repeat':equal(native/(name+'.arc'),native/(arm+'-encode.arc'))
        archive=native/(arm+'-encode.arc');equal(archive,ROOT/REFERENCES[arm])
        arms[arm]=dict(archive=g.artifact(archive),archive_bytes=archive.stat().st_size,
            restored=g.artifact(native/(arm+'-decode.raw')),repeat=g.artifact(native/(arm+'-repeat.arc')),
            exact_inverse=True,archive_repeat_byte_equal=True,frozen_archive_byte_identity=True)
        g.write('completed-arms.json',dict(arms=arms,complete=False))
    dp=deliveries['D']['binary']['bytes']-deliveries['P']['binary']['bytes']
    zp=deliveries['D']['source_zip']['bytes']-deliveries['P']['source_zip']['bytes']
    # Component forms are alternatives, never a sum of source and binary prices.
    pricing=dict(deliveries=deliveries,original_source_zip=g.artifact(g.result/'original-source.zip'),
        model=g.artifact(native/'models/6m-q4-fp32.tfwc2'),dictionary=g.artifact(native/'dictionary/english.dic'),
        source_zip_increment_bytes=zp,binary_increment_bytes=dp,
        compile_option_union_increment_text='-DGAMMA_EXPERT_RELEASE',compile_option_increment_bytes=21,
        complete_submission_package=False,complete_package_bytes=None,unresolved=package['unresolved'],
        diagnostic_forms='Source ZIP and executable deltas are separate alternatives; model/dictionary/runtime/options/multiplicities remain explicitly unresolved.')
    g.write('package.json',pricing)
    gp=arms['P']['archive_bytes']-arms['D']['archive_bytes']
    return dict(arms=arms,g_P=gp,source_zip_increment_bytes=zp,binary_increment_bytes=dp,
        source_component_net_bytes=gp-zp-21,binary_component_net_bytes=gp-dp,
        frozen_archive_byte_identity=True,no_runtime_arm_or_trace_options=True,
        state_evidence='Synthetic differential verifies every aligned mixture weight and count; native full model state is not serialized. Native archives and independent inverses must match frozen counterparts.',
        scientific_verdict='Production equivalence established; unchanged measured mixture gain. Component costs measured, complete submission qualification unresolved.')

def main():
    validate=sys.argv[1:]==['--validate'];require(validate or not sys.argv[1:],'unsupported arguments')
    g=NativeGate(ROOT,ID,CAPS,validate_only=validate)
    if validate:print(json.dumps(dict(status='preflight_passed',inputs=len(g.inputs))));return 0
    result=dict(schema='gamma.enwiki9.expert-release-native-terminal.v1',candidate_id=ID,experiment=g.reference,
        raw_population='[0,250000)',raw_bytes=250000,complete_package_bytes=None,full_corpus_score_bytes=None,
        objective_credit_bytes=0,larger_gate_authorized=False)
    try:result.update(execute(g),status='passed');g.verify()
    except Exception as e:result.update(status='execution_failed',failure_class=getattr(e,'category','correctness_or_evidence_failure'),error=str(e),scientific_verdict='Incomplete release proof; preserve completed measurements.')
    try:cleanup(g,'terminal');g.verify();result['child_closure_ok']=True
    except Exception as e:result.update(status='execution_failed',cleanup_error=str(e),child_closure_ok=False)
    result['commands']=g.commands
    g.write('artifacts.json',dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*')) if p.is_file() and p.name!='ppm.temp'],errors=[]))
    result['artifacts']=g.artifact(g.result/'artifacts.json');g.write('decision.json',result)
    print(json.dumps({k:result[k] for k in ('status','scientific_verdict','g_P','source_component_net_bytes','error') if k in result}))
    return 0 if result['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
