#!/usr/bin/env python3
"""Native complete-cost comparison for one fixed final-MLP weight ablation."""
import io
import json
from pathlib import Path
import struct
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate, require, sha
from tools.fx2_expert_release250k_v3 import source_zip, equal, cleanup
ID='fx2_final_mlp_zero250k_v1'
PLAN='operations/provenance/'+ID+'_plan.json'
PROFILE='operations/provenance/fx2_kda_carry_toolchain_20260913.json'
RELEASE='results/fx2_expert_release250k_v3/'
ZIP=RELEASE+'P-source.zip'
FIXTURE='results/fx2_weight_native_transfer250k_q0_v1/'
RAW=FIXTURE+'work/native/opening.raw'; STORED=FIXTURE+'work/native/opening.stored'
ARCHIVE=FIXTURE+'opening/P/archive.bin'
MODEL='models/6m-q4-fp32.tfwc2'
CAPS=dict(cpus=[2],memory_bytes=9999998976,swap_bytes=0,scratch_bytes=16000000000,wall_seconds=3600)
N=151210

class NativeGate(BaseGate):
    def verify(self):
        self.toolchain=json.loads(self.buffers[PROFILE]);super().verify()

def execute(g):
    plan=json.loads(g.buffers[PLAN]);require(plan['caps']==CAPS,'caps differ')
    require(len(g.buffers[RAW])==250000 and len(g.buffers[STORED])==N+10,'population differs')
    native=g.work/'native';native.mkdir()
    with zipfile.ZipFile(io.BytesIO(g.buffers[ZIP])) as z:
        names=z.namelist();require(len(names)==len(set(names))==127,'source population differs')
        members={}
        for name in names:
            p=Path(name);require(not p.is_absolute() and '..' not in p.parts and not name.endswith('/'),'unsafe source member')
            members[name]=z.read(name)
    for name,data in members.items():
        p=native/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    require(members[MODEL]==g.buffers[RELEASE+'work/native/'+MODEL],'model binding differs')
    package=json.loads(g.buffers[RELEASE+'package.json'])
    g.retain_sources()
    src=g.work/'source'
    probe=g.work/'prepare';compare=g.work/'native-compare'
    g.run('prepare-compile',['/usr/bin/g++','-std=c++17','-O2','-Wall','-Wextra',str(src/'tools/fx2_final_mlp_zero_v1.cpp'),'-o',str(probe)],60)
    g.binaries[str(probe)]=sha(probe)
    g.run('prepare-self-test',[str(probe),'--self-test'],60)
    include=native/'cpp_infer/src'
    g.run('native-compare-compile',['/usr/bin/g++','-std=c++17','-O2','-fno-fast-math','-I'+str(include),str(src/'tools/fx2_final_mlp_native_compare_v1.cpp'),str(include/'weights_io.cpp'),str(include/'weights_io_compressed.cpp'),'-o',str(compare)],60)
    g.binaries[str(compare)]=sha(compare)
    g.run('model-prepare',[str(probe),str(native/MODEL),str(g.work/'K-model'),str(g.work/'D-model')],60)
    g.run('model-prepare-repeat',[str(probe),str(native/MODEL),str(g.work/'K-repeat'),str(g.work/'D-repeat')],60)
    equal(g.work/'K-model',native/MODEL);equal(g.work/'K-repeat',native/MODEL);equal(g.work/'D-model',g.work/'D-repeat')
    g.run('native-tensor-compare',[str(compare),str(native/MODEL),str(g.work/'D-model')],60)
    child=dict(members);child[MODEL]=(g.work/'D-model').read_bytes()
    require({n for n in members if members[n]!=child[n]}=={MODEL},'undeclared source member change')
    g.copy(RAW,native/'population.raw')
    arms={};deliveries={};models={}
    for arm,source in [('P',members),('D',child)]:
        (native/MODEL).write_bytes(source[MODEL])
        model=g.work/(arm+'-paid-model');model.write_bytes(source[MODEL]);models[arm]=g.artifact(model)
        source_zip(g.result/(arm+'-source.zip'),source)
        if arm=='P':equal(g.result/'P-source.zip',ROOT/ZIP)
        else:g.run('D-clean',['/usr/bin/make','clean'],30,work=native)
        command=plan['compile_command']
        g.run(arm+'-compile',command,360,work=native);built=(native/'cmix').read_bytes()
        g.run(arm+'-clean-repeat',['/usr/bin/make','clean'],30,work=native)
        g.run(arm+'-compile-repeat',command,360,work=native)
        require((native/'cmix').read_bytes()==built,'clean build repeat differs')
        binary=native/('cmix-'+arm);binary.write_bytes(built);binary.chmod(0o755);g.binaries[str(binary)]=sha(binary)
        require(sha(binary)==package['deliveries']['P']['binary']['sha256'].removeprefix('sha256:'),'unchanged binary differs')
        if arm=='P':
            try:
                g.run('preprocess',[str(binary),'-s','dictionary/english.dic','population.raw','population.stored'],180,work=native)
                equal(native/'population.stored',ROOT/STORED)
            finally:cleanup(g,'preprocess')
        for phase in ('encode','decode','repeat','untraced'):
            label=arm+'-'+phase
            if phase=='decode':args=['-d','dictionary/english.dic',arm+'-encode.arc',label+'.raw']
            else:args=['-c','dictionary/english.dic',arm+'-decode.raw' if phase=='repeat' else 'population.raw',label+'.arc']
            args+=['--transformer',MODEL]
            if phase in ('encode','repeat'):args+=['--save-transformer-probs',label+'.probs']
            try:g.run(label,[str(binary),*args],180,work=native)
            finally:cleanup(g,label)
            require((native/MODEL).read_bytes()==source[MODEL],'runtime model changed')
            if phase=='decode':equal(native/(label+'.raw'),native/'population.raw')
            if phase in ('repeat','untraced'):equal(native/(label+'.arc'),native/(arm+'-encode.arc'))
            if phase=='repeat':equal(native/(label+'.probs'),native/(arm+'-encode.probs'))
        if arm=='P':equal(native/'P-encode.arc',ROOT/ARCHIVE)
        arc=native/(arm+'-encode.arc')
        arms[arm]=dict(archive=g.artifact(arc),archive_bytes=arc.stat().st_size,restored=g.artifact(native/(arm+'-decode.raw')),repeat=g.artifact(native/(arm+'-repeat.arc')),probabilities=g.artifact(native/(arm+'-encode.probs')),probability_repeat=g.artifact(native/(arm+'-repeat.probs')),exact_inverse=True,archive_repeat_byte_equal=True,neural_probability_repeat_byte_equal=True,traced_untraced_archive_identity=True)
        deliveries[arm]=dict(binary=g.artifact(binary),source_zip=g.artifact(g.result/(arm+'-source.zip')),model=models[arm],source_members=len(source),uncompressed_source_bytes=sum(map(len,source.values())),clean_build_repeat_byte_equal=True,compile_command=command)
        g.write('completed-arms.json',dict(arms=arms,deliveries=deliveries,complete=False))
    changed=0;first=None
    with (native/'P-encode.probs').open('rb') as p,(native/'D-encode.probs').open('rb') as d:
        for i in range(N):
            a=p.read(410);b=d.read(410);require(len(a)==len(b)==410,'neural population incomplete')
            for row in (a,b):require(all((v&0x7c00)!=0x7c00 for (v,) in struct.iter_unpack('<H',row)),'nonfinite neural probability')
            if a!=b:
                changed+=1
                if first is None:first=i
        require(not p.read(1) and not d.read(1),'extra neural rows')
    g.write('neural-comparison.json',dict(rows=N,changed_rows=changed,first_changed_row=first,final_row_predicts_outside_sample=True,encoder_decoder_neural_comparison_available=False))
    zp=deliveries['D']['source_zip']['bytes']-deliveries['P']['source_zip']['bytes']
    mp=models['D']['bytes']-models['P']['bytes'];gain=arms['P']['archive_bytes']-arms['D']['archive_bytes']
    pricing=dict(deliveries=deliveries,source_zip_increment_bytes=zp,model_increment_bytes=mp,binary_increment_bytes=0,additional_required_option_bytes=0,source_component_net_bytes=gain-zp,runtime_one_model_component_net_bytes=gain-mp,runtime_two_model_component_net_bytes=gain-2*mp,complete_submission_package=False,complete_package_bytes=None,unresolved=package['unresolved'],boundary='Source ZIP already includes the model: never add its raw model price again. Binary is byte-identical. One/two model copies are component sensitivities, not an accepted packaging form. Preparation tools are not runtime dependencies; unchanged loader consumes stored paid model.')
    g.write('package.json',pricing)
    confirm=gain>=0 and gain-zp>0 and mp<0 and changed>0
    return dict(arms=arms,g_P=gain,source_zip_increment_bytes=zp,model_increment_bytes=mp,binary_increment_bytes=0,source_component_net_bytes=gain-zp,runtime_one_model_component_net_bytes=gain-mp,runtime_two_model_component_net_bytes=gain-2*mp,confirmation_authorized=confirm,identity_model_exact=True,native_changed_tensor_count=2,changed_neural_rows=changed,state_boundary='Only final MLP tensors change; original loader verifies every other tensor including generated RoPE. Native neural streams repeat within arm; full recurrent state and decoder neural stream are not serialized. Same decoded bytes feed unchanged update rules; downstream mixer state may change.',scientific_verdict='Fixed ablation saves paid model/source bytes without archive regression; authorize unchanged independent confirmation.' if confirm else 'Fixed ablation fails the predeclared no-archive-regression and paid-component gate; record actual component totals without extrapolation.')

def main():
    validate=sys.argv[1:]==['--validate'];require(validate or not sys.argv[1:],'unsupported arguments')
    g=NativeGate(ROOT,ID,CAPS,validate_only=validate)
    if validate:print(json.dumps(dict(status='preflight_passed',inputs=len(g.inputs))));return 0
    result=dict(schema='gamma.enwiki9.final-mlp-zero-terminal.v1',candidate_id=ID,experiment=g.reference,raw_population='[0,250000)',raw_bytes=250000,complete_package_bytes=None,full_corpus_score_bytes=None,objective_credit_bytes=0,larger_gate_authorized=False)
    try:result.update(execute(g),status='passed');g.verify()
    except Exception as e:result.update(status='execution_failed',failure_class=getattr(e,'category','correctness_or_evidence_failure'),error=str(e),scientific_verdict='Incomplete ablation comparison; preserve completed evidence.')
    try:cleanup(g,'terminal');g.verify();result['child_closure_ok']=True
    except Exception as e:result.update(status='execution_failed',cleanup_error=str(e),child_closure_ok=False)
    result['commands']=g.commands
    g.write('artifacts.json',dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*')) if p.is_file() and p.name!='ppm.temp'],errors=[]))
    result['artifacts']=g.artifact(g.result/'artifacts.json');g.write('decision.json',result)
    print(json.dumps({k:result[k] for k in ('status','scientific_verdict','g_P','source_component_net_bytes','error') if k in result}))
    return 0 if result['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
