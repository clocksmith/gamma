#!/usr/bin/env python3
"""One native archive test of a posterior mixture conditioned on expert disagreement."""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate, require, sha

ID='fx2_expert_mix_opening250k_v1'
PLAN='operations/provenance/'+ID+'_plan.json'
PROFILE='operations/provenance/fx2_kda_carry_toolchain_20260913.json'
PARENT='results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'
ADAPTER='operations/provenance/fx2_expert_mix_adapter_v1.json'
RAW='results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.raw'
STORED='results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.stored'
ARCHIVE='results/fx2_weight_native_transfer250k_q0_v1/opening/P/archive.bin'
TRACE='results/fx2_weight_native_transfer250k_q0_v1/work/native/opening-P-encode.trace'
CAPS=dict(cpus=[2],memory_bytes=9999998976,swap_bytes=0,scratch_bytes=24000000000,wall_seconds=1800)
N=151210
STATE_RECORD=2152

class NativeGate(BaseGate):
    def verify(self):
        self.toolchain=json.loads(self.buffers[PROFILE])
        super().verify()

def equal(a,b):
    require(a.stat().st_size==b.stat().st_size,'file lengths differ: '+str(a))
    with a.open('rb') as x,b.open('rb') as y:
        while row:=x.read(1<<20):
            require(row==y.read(len(row)),'file bytes differ: '+str(a))

def cleanup(g,label):
    g.closure()
    path=g.work/'native/ppm.temp'
    receipt=dict(child_closure=True,content_hashed=False,present=path.exists())
    if path.exists():
        require(path.resolve()==path and path.is_file(),'aliased transient')
        s=path.stat();receipt.update(logical_bytes=s.st_size,allocated_bytes=s.st_blocks*512)
        path.unlink()
    receipt['cleanup_complete']=not path.exists()
    g.write(label+'-cleanup.json',receipt)

def states(path):
    raw=path.read_bytes()
    require(len(raw)==(N*8//2048+1)*STATE_RECORD,'state population differs')
    for i in range(len(raw)//STATE_RECORD):
        row=raw[i*STATE_RECORD:(i+1)*STATE_RECORD]
        pos=struct.unpack_from('<Q',row)[0]
        require(pos==min((i+1)*2048,N*8),'state clock differs')
        for context in range(64):
            weights=struct.unpack_from('<4Q',row,8+32*context)
            require(sum(weights)==1<<32 and min(weights)>0,'posterior weight invariant differs')
    return len(raw)//STATE_RECORD

def parent_trajectory(a,b):
    with a.open('rb') as x,b.open('rb') as y:
        while left:=x.read(28*8192):
            right=y.read(len(left));require(len(left)==len(right),'trajectory lengths differ')
            for u,v in zip(struct.iter_unpack('<7I',left),struct.iter_unpack('<7I',right)):
                require(u[0]==v[0] and u[6]==v[6],'parent probability or truth changed')
        require(not y.read(1),'extra trajectory bytes')

def execute(g):
    plan=json.loads(g.buffers[PLAN]);require(plan['caps']==CAPS,'caps differ')
    require(len(g.buffers[RAW])==250000 and len(g.buffers[STORED])==N+10,'population differs')
    native=g.work/'native';native.mkdir()
    package=json.loads(g.buffers[PARENT+'package.json'])
    for row in package['source_members']+package['runtime_members']:
        if row['path']==PARENT+'work/cmix':continue
        target=native/row['path'].removeprefix(PARENT+'work/')
        if not target.exists():g.copy(row['path'],target)
    adapter=json.loads(g.buffers[ADAPTER]);g.adapter(ADAPTER,native)
    for row in adapter['added_files']:g.copy(row['source']['path'],native/row['target'])
    g.copy(RAW,native/'population.raw')
    compile_command=plan['compile_command']
    g.run('compile',compile_command,360,work=native)
    first=sha(native/'cmix');(g.work/'cmix.first').write_bytes((native/'cmix').read_bytes())
    g.run('compile-repeat',compile_command,360,work=native)
    require(sha(native/'cmix')==first,'same-path clean build binary differs')
    g.binaries[str(native/'cmix')]=first
    sources=[native/r['path'].removeprefix(PARENT+'work/') for r in package['source_members']]
    sources += [native/r['target'] for r in adapter['added_files']]
    source_delta=sum(p.stat().st_size for p in sources)-package['source_member_bytes']
    binary_delta=(native/'cmix').stat().st_size-next(r['bytes'] for r in package['runtime_members'] if r['path'].endswith('/cmix'))
    options=package['option_text']+'\nGAMMA_FX2_EXPERT_ARM=D\n'
    local_delta=source_delta+binary_delta+len(options.encode())-package['option_bytes']
    g.write('package.json',dict(source_files=[g.artifact(p) for p in sources],
        binary=g.artifact(native/'cmix'),model=g.artifact(native/'models/6m-q4-fp32.tfwc2'),
        dictionary=g.artifact(native/'dictionary/english.dic'),option_text=options,
        source_delta_bytes=source_delta,binary_delta_bytes=binary_delta,
        added_local_component_bytes=local_delta,same_path_build_repeat_byte_equal=True,
        complete_submission_package=False,complete_package_bytes=None,unresolved=package['unresolved']))
    require(local_delta<=65536,'local component budget exceeded')
    try:
        g.run('preprocess',[str(native/'cmix'),'-s','dictionary/english.dic','population.raw','population.stored'],180,env=dict(GAMMA_FX2_EXPERT_ARM='P'),work=native)
        equal(native/'population.stored',ROOT/STORED)
    finally:cleanup(g,'preprocess')
    arms={}
    for arm in 'PKDS':
        for phase in ('encode','decode','repeat'):
            name=arm+'-'+phase
            trace=native/(name+'.coder');state=native/(name+'.state')
            require(not trace.exists() and not state.exists(),'audit output already exists')
            if phase=='decode':
                args=['-d','dictionary/english.dic',arm+'-encode.arc',arm+'-decode.raw']
            else:
                source='population.raw' if phase=='encode' else arm+'-decode.raw'
                args=['-c','dictionary/english.dic',source,name+'.arc']
            try:
                g.run(name,[str(native/'cmix'),*args,'--transformer','models/6m-q4-fp32.tfwc2'],180,
                      env=dict(GAMMA_FX2_EXPERT_ARM=arm,GAMMA_FX2_EXPERT_TRACE=str(state),GAMMA_FX2_CODER_TRACE=str(trace)),work=native)
            finally:cleanup(g,name)
            require(trace.stat().st_size==N*8*28,'coder coordinate differs')
            count=states(state)
            if phase!='encode':
                equal(native/(arm+'-encode.coder'),trace)
                equal(native/(arm+'-encode.state'),state)
            if phase=='decode':equal(native/(arm+'-decode.raw'),native/'population.raw')
            if phase=='repeat':equal(native/(arm+'-encode.arc'),native/(arm+'-repeat.arc'))
        archive=native/(arm+'-encode.arc')
        arms[arm]=dict(archive=g.artifact(archive),archive_bytes=archive.stat().st_size,
            restored=g.artifact(native/(arm+'-decode.raw')),repeat=g.artifact(native/(arm+'-repeat.arc')),
            state_boundaries=count,exact_inverse=True,archive_repeat_byte_equal=True,
            boundary_state_byte_equal=True,coder_trace_byte_equal=True)
        g.write('completed-arms.json',dict(arms=arms,complete=False))
    try:
        g.run('D-untraced',[str(native/'cmix'),'-c','dictionary/english.dic','population.raw',
              'D-untraced.arc','--transformer','models/6m-q4-fp32.tfwc2'],180,
              env=dict(GAMMA_FX2_EXPERT_ARM='D'),work=native)
        equal(native/'D-encode.arc',native/'D-untraced.arc')
    finally:cleanup(g,'D-untraced')
    for suffix in ('arc','coder'):equal(native/('P-encode.'+suffix),native/('K-encode.'+suffix))
    equal(native/'P-encode.arc',ROOT/ARCHIVE);equal(native/'P-encode.coder',ROOT/TRACE)
    equal(native/'K-encode.state',native/'D-encode.state')
    for arm in 'KDS':parent_trajectory(native/'P-encode.coder',native/(arm+'-encode.coder'))
    require((native/'D-encode.state').read_bytes()!=(native/'P-encode.state').read_bytes(),'D inactive')
    require((native/'D-encode.state').read_bytes()!=(native/'S-encode.state').read_bytes(),'control inactive')
    gp=arms['P']['archive_bytes']-arms['D']['archive_bytes'];gs=arms['S']['archive_bytes']-arms['D']['archive_bytes']
    verdict='Archive regression.' if gp<0 else 'No archive improvement.' if gp==0 else 'Parent improvement observed, but advantage over the delayed-expert control is unconfirmed.' if gs<=0 else 'Positive native development comparison; confirmation and final packaging unmeasured.'
    return dict(arms=arms,g_P=gp,g_S=gs,n_1=None,n_2=None,
        historical_source_cost_sensitivities='Prior cold1MB n1/n2 do not belong to this experiment.',
        PK_archive_byte_identity=True,KD_adapter_state_byte_identity=True,all_parent_probability_and_truth_identity=True,released_parent_archive_and_coder_parity=True,trace_on_off_archive_identity=True,
        changed_state_audit='Every mixture weight, delayed expert history and clock at each2048bit boundary and termination; parent raw probabilities and truths at every bit. Parent model transitions are untouched; full native model state is not serialized.',
        full_native_state_serialized=False,added_local_component_bytes=local_delta,
        diagnostic_local_net_bytes=gp-local_delta,scientific_verdict=verdict)

def main():
    validate=sys.argv[1:]==['--validate'];require(not sys.argv[1:] or validate,'unsupported arguments')
    g=NativeGate(ROOT,ID,CAPS,validate_only=validate)
    if validate:print(json.dumps(dict(status='preflight_passed',inputs=len(g.inputs))));return 0
    result=dict(schema='gamma.enwiki9.expert-mixture-native-terminal.v1',candidate_id=ID,experiment=g.reference,
                raw_population='[0,250000)',raw_bytes=250000,complete_package_bytes=None,
                full_corpus_score_bytes=None,objective_credit_bytes=0,larger_gate_authorized=False)
    try:
        result.update(execute(g),status='passed');g.verify()
    except Exception as error:
        category=getattr(error,'category','correctness_or_evidence_failure')
        result.update(status='execution_failed',failure_class=category,error=str(error),
                      scientific_verdict='No complete confirmation verdict; preserve completed measurements.')
    try:cleanup(g,'terminal');g.verify();result['child_closure_ok']=True
    except Exception as error:result.update(status='execution_failed',cleanup_error=str(error),child_closure_ok=False)
    result['commands']=g.commands
    files=[g.artifact(p) for p in sorted(g.result.rglob('*')) if p.is_file() and p.name!='ppm.temp']
    g.write('artifacts.json',dict(files=files,errors=[]));result['artifacts']=g.artifact(g.result/'artifacts.json')
    g.write('decision.json',result)
    print(json.dumps({k:result[k] for k in ('status','scientific_verdict','g_P','g_S','error') if k in result}))
    return 0 if result['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
