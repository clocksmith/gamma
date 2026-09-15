#!/usr/bin/env python3
"""Native 1024/2048 attention-window comparison with unchanged paid weights."""
import io
import json
from pathlib import Path
import struct
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate, require, sha
from tools.fx2_attention_window_adapter_v1 import mutate, CHANGES
from tools.fx2_expert_release250k_v3 import source_zip, equal, cleanup

ID='fx2_attention_window250k_v1'
PLAN='operations/provenance/'+ID+'_plan.json'
PROFILE='operations/provenance/fx2_kda_carry_toolchain_20260913.json'
RELEASE='results/fx2_expert_release250k_v3/'
ZIP=RELEASE+'P-source.zip'
FIXTURE='results/fx2_weight_native_transfer250k_q0_v1/'
RAW=FIXTURE+'work/native/opening.raw'
STORED=FIXTURE+'work/native/opening.stored'
ARCHIVE=FIXTURE+'opening/P/archive.bin'
VALIDITY='results/fx2_residual_features250k_v3/closure/feature_validity.json'
CAPS=dict(cpus=[2],memory_bytes=9999998976,swap_bytes=0,scratch_bytes=12000000000,wall_seconds=1800)
N=151210


class NativeGate(BaseGate):
    def verify(self):
        self.toolchain=json.loads(self.buffers[PROFILE]);super().verify()


def neural_compare(parent, child, starts):
    size=205*2
    require(parent.stat().st_size==child.stat().st_size==N*size,'neural row population differs')
    index=0; piece=0; first=None; changed=0; prefix_rows=0
    with parent.open('rb') as p,child.open('rb') as d:
        for i in range(N):
            a=p.read(size);b=d.read(size);j=i+1
            if piece+1<len(starts) and j>=starts[piece+1]:piece+=1
            distance=j-starts[piece]
            for row in (a,b):
                require(all((v&0x7c00)!=0x7c00 for (v,) in struct.iter_unpack('<H',row)), 'nonfinite neural probability')
            if j<N and distance<1024:
                require(a==b,'neural prefix changed before the declared window boundary')
                prefix_rows+=1
            if a!=b:
                changed+=1
                if first is None:first=dict(row=i,predicted_modeled_byte=j,piece=piece,preceding_piece_inputs=distance)
            index+=1
    return dict(rows=index,changed_rows=changed,first_changed_row=first,
                same_pre_boundary_rows=prefix_rows,pre_boundary_exact=True,
                population_semantics='Row i is the half-precision distribution following input i, used for the next byte. Final row predicts outside the sample.',
                parent_sha256=sha(parent),treatment_sha256=sha(child))


def execute(g):
    plan=json.loads(g.buffers[PLAN]);require(plan['caps']==CAPS,'resource contract differs')
    require(len(g.buffers[RAW])==250000 and len(g.buffers[STORED])==N+10,'population differs')
    native=g.work/'native';native.mkdir()
    with zipfile.ZipFile(io.BytesIO(g.buffers[ZIP])) as z:
        names=z.namelist();require(len(names)==len(set(names))==127,'source ZIP population')
        members={}
        for name in names:
            p=Path(name);require(not p.is_absolute() and '..' not in p.parts and not name.endswith('/'),'unsafe ZIP member')
            members[name]=z.read(name)
    child=mutate(members)
    require({n for n in members if members[n]!=child[n]}==set(CHANGES),'changed member set')
    package=json.loads(g.buffers[RELEASE+'package.json'])
    arms={};deliveries={}
    for arm,source in [('P',members),('D',child)]:
        for name,data in source.items():
            p=native/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        for key in ('model','dictionary'):
            row=package[key];target=native/row['path'].split('/work/native/')[1]
            if not target.exists():g.copy(row['path'],target)
            require(sha(target)==row['sha256'].removeprefix('sha256:'),'runtime asset differs')
        source_zip(g.result/(arm+'-source.zip'),source)
        if arm=='P':
            equal(g.result/'P-source.zip',ROOT/ZIP)
            g.copy(RAW,native/'population.raw')
        else:g.run('D-clean',['/usr/bin/make','clean'],30,work=native)
        command=plan['compile_command']
        g.run(arm+'-compile',command,360,work=native)
        built=(native/'cmix').read_bytes()
        g.run(arm+'-clean-repeat',['/usr/bin/make','clean'],30,work=native)
        g.run(arm+'-compile-repeat',command,360,work=native)
        require((native/'cmix').read_bytes()==built,'clean build repeat differs')
        binary=native/('cmix-'+arm);binary.write_bytes(built);binary.chmod(0o755)
        g.binaries[str(binary)]=sha(binary)
        if arm=='P':
            require(sha(binary)==package['deliveries']['P']['binary']['sha256'].removeprefix('sha256:'),'parent binary differs')
            try:
                g.run('preprocess',[str(binary),'-s','dictionary/english.dic','population.raw','population.stored'],180,work=native)
                equal(native/'population.stored',ROOT/STORED)
            finally:cleanup(g,'preprocess')
        for phase in ('encode','decode','repeat','untraced'):
            label=arm+'-'+phase
            if phase=='decode':args=['-d','dictionary/english.dic',arm+'-encode.arc',label+'.raw']
            else:args=['-c','dictionary/english.dic',arm+'-decode.raw' if phase=='repeat' else 'population.raw',label+'.arc']
            args+=['--transformer','models/6m-q4-fp32.tfwc2']
            if phase in ('encode','repeat'):args+=['--save-transformer-probs',label+'.probs']
            try:g.run(label,[str(binary),*args],180,work=native)
            finally:cleanup(g,label)
            if phase=='decode':equal(native/(label+'.raw'),native/'population.raw')
            if phase in ('repeat','untraced'):equal(native/(label+'.arc'),native/(arm+'-encode.arc'))
            if phase=='repeat':equal(native/(label+'.probs'),native/(arm+'-encode.probs'))
        if arm=='P':equal(native/'P-encode.arc',ROOT/ARCHIVE)
        arc=native/(arm+'-encode.arc')
        arms[arm]=dict(archive=g.artifact(arc),archive_bytes=arc.stat().st_size,
            restored=g.artifact(native/(arm+'-decode.raw')),repeat=g.artifact(native/(arm+'-repeat.arc')),
            probabilities=g.artifact(native/(arm+'-encode.probs')),probability_repeat=g.artifact(native/(arm+'-repeat.probs')),
            exact_inverse=True,archive_repeat_byte_equal=True,neural_probability_repeat_byte_equal=True,
            traced_untraced_archive_identity=True)
        deliveries[arm]=dict(binary=g.artifact(binary),source_zip=g.artifact(g.result/(arm+'-source.zip')),
            source_members=len(source),uncompressed_source_bytes=sum(map(len,source.values())),
            clean_build_repeat_byte_equal=True,compile_command=command)
        g.write('completed-arms.json',dict(arms=arms,deliveries=deliveries,complete=False))
    comparison=neural_compare(native/'P-encode.probs',native/'D-encode.probs',json.loads(g.buffers[VALIDITY])['missing_feature_byte_coordinates'])
    g.write('neural-comparison.json',comparison)
    dp=deliveries['D']['binary']['bytes']-deliveries['P']['binary']['bytes']
    zp=deliveries['D']['source_zip']['bytes']-deliveries['P']['source_zip']['bytes']
    gain=arms['P']['archive_bytes']-arms['D']['archive_bytes']
    pricing=dict(deliveries=deliveries,model=g.artifact(native/'models/6m-q4-fp32.tfwc2'),
        dictionary=g.artifact(native/'dictionary/english.dic'),source_zip_increment_bytes=zp,
        binary_increment_bytes=dp,additional_required_option_bytes=0,
        complete_submission_package=False,complete_package_bytes=None,unresolved=package['unresolved'],
        boundary='Source ZIP and binary are alternative component prices. The observation option is not needed for coding and is excluded only after exact trace-off archive comparison. Official form, multiplicities and platform remain unresolved.')
    g.write('package.json',pricing)
    return dict(arms=arms,neural_comparison=g.artifact(g.result/'neural-comparison.json'),
        g_P=gain,source_zip_increment_bytes=zp,binary_increment_bytes=dp,
        source_component_net_bytes=gain-zp,binary_component_net_bytes=gain-dp,
        unchanged_model_and_dictionary=True,parent_binary_and_archive_identity=True,
        changed_source_members=list(CHANGES),confirmation_authorized=gain>0 and gain-zp>0,
        state_boundary='Kernel prefix and ring controls plus exact native neural pre-boundary rows and repeated neural streams. Full model/optimizer state and decoder neural stream are not serialized; native inverse, archive repeat and trace-off identity are required.',
        scientific_verdict='Native archive and source-component gain authorize unchanged independent confirmation.' if gain>0 and gain-zp>0 else 'This fixed2048-window mutation does not pass the native archive/source-component comparison.')


def main():
    validate=sys.argv[1:]==['--validate'];require(validate or not sys.argv[1:],'unsupported arguments')
    g=NativeGate(ROOT,ID,CAPS,validate_only=validate)
    if validate:print(json.dumps(dict(status='preflight_passed',inputs=len(g.inputs))));return 0
    result=dict(schema='gamma.enwiki9.attention-window-terminal.v1',candidate_id=ID,experiment=g.reference,
        raw_population='[0,250000)',raw_bytes=250000,complete_package_bytes=None,
        full_corpus_score_bytes=None,objective_credit_bytes=0,larger_gate_authorized=False)
    try:result.update(execute(g),status='passed');g.verify()
    except Exception as e:result.update(status='execution_failed',failure_class=getattr(e,'category','correctness_or_evidence_failure'),error=str(e),scientific_verdict='Incomplete native window comparison; preserve completed evidence.')
    try:cleanup(g,'terminal');g.verify();result['child_closure_ok']=True
    except Exception as e:result.update(status='execution_failed',cleanup_error=str(e),child_closure_ok=False)
    result['commands']=g.commands
    g.write('artifacts.json',dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*')) if p.is_file() and p.name!='ppm.temp'],errors=[]))
    result['artifacts']=g.artifact(g.result/'artifacts.json');g.write('decision.json',result)
    print(json.dumps({k:result[k] for k in ('status','scientific_verdict','g_P','source_component_net_bytes','error') if k in result}))
    return 0 if result['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
