#!/usr/bin/env python3
"""Matched explicit dictionary input to the existing FXCM lexical predictor."""
import io
import json
from pathlib import Path
import struct
import shlex
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate, require, sha
from lib.fx2_explicit_lexical_v1 import materialize, MODEL, RUNNER
from tools.fx2_expert_release250k_v3 import source_zip, equal, cleanup

ID='fx2_explicit_lexical250k_v1'
PLAN='operations/provenance/'+ID+'_plan.json'
PROFILE='operations/provenance/fx2_kda_carry_toolchain_20260913.json'
RELEASE='results/fx2_expert_release250k_v3/'
ZIP=RELEASE+'P-source.zip'
FIXTURE='results/fx2_weight_native_transfer250k_q0_v1/'
RAW=FIXTURE+'work/native/opening.raw'
STORED=FIXTURE+'work/native/opening.stored'
ARCHIVE=FIXTURE+'opening/P/archive.bin'
VALIDITY='results/fx2_residual_features250k_v3/closure/feature_validity.json'
CAPS=dict(cpus=[2],memory_bytes=9999998976,swap_bytes=0,scratch_bytes=16000000000,wall_seconds=3600)
N=151210


class NativeGate(BaseGate):
    def verify(self):
        self.toolchain=json.loads(self.buffers[PROFILE]);super().verify()


def lexical_audit(path, mode):
    import re
    rows=re.findall(r'GAMMA_LEXICAL mode=(\d+) words=(\d+) valid=(\d+) invalid=(\d+)',path.read_text())
    require(len(rows)==1,'lexical runtime witness absent or ambiguous')
    m,n,v,bad=map(int,rows[0]);require(m==mode and n==44515,'runtime dictionary or mode differs')
    require(v==bad==0 if mode==0 else v>0,'lexical activation differs')
    return dict(mode=m,words=n,valid=v,invalid=bad)


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
    variants={a:materialize(members,m) for a,m in [('K',0),('D',1),('S',2)]}
    for source in variants.values():
        require(set(source)==set(members) and {n for n in members if source[n]!=members[n]}=={MODEL,RUNNER},'changed member set')
    package=json.loads(g.buffers[RELEASE+'package.json'])
    arms={};deliveries={};audits={}
    for arm,source in [('P',members),*variants.items()]:
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
        else:g.run(arm+'-clean',['/usr/bin/make','clean'],30,work=native)
        command=plan['compile_commands'][arm]
        g.run(arm+'-compile',command,360,work=native)
        built=(native/'cmix').read_bytes()
        g.run(arm+'-clean-repeat',['/usr/bin/make','clean'],30,work=native)
        g.run(arm+'-compile-repeat',command,360,work=native)
        require((native/'cmix').read_bytes()==built,'clean build repeat differs')
        if arm in 'DS':
            require(built!=(native/'cmix-P').read_bytes(),'treatment compiled to parent executable')
        binary=native/('cmix-'+arm);binary.write_bytes(built);binary.chmod(0o755)
        g.binaries[str(binary)]=sha(binary)
        if arm=='P':
            require(sha(binary)==package['deliveries']['P']['binary']['sha256'].removeprefix('sha256:'),'parent binary differs')
            try:
                g.run('preprocess',[str(binary),'-s','dictionary/english.dic','population.raw','population.stored'],180,work=native)
                equal(native/'population.stored',ROOT/STORED)
            finally:cleanup(g,'preprocess')
        require(not (native/'.dict').exists(),'undeclared ambient dictionary')
        audits[arm]={}
        for phase in ('encode','decode','repeat','untraced'):
            label=arm+'-'+phase
            if phase=='decode':args=['-d','dictionary/english.dic',arm+'-encode.arc',label+'.raw']
            else:args=['-c','dictionary/english.dic',arm+'-decode.raw' if phase=='repeat' else 'population.raw',label+'.arc']
            args+=['--transformer','models/6m-q4-fp32.tfwc2']
            if phase in ('encode','decode','repeat'):args+=['--save-transformer-probs',label+'.probs']
            try:g.run(label,[str(binary),*args],180,work=native)
            finally:cleanup(g,label)
            if arm!='P':audits[arm][phase]=lexical_audit(g.result/(label+'.stderr'),{'K':0,'D':1,'S':2}[arm])
            if phase=='decode':equal(native/(label+'.raw'),native/'population.raw')
            if phase in ('repeat','untraced'):equal(native/(label+'.arc'),native/(arm+'-encode.arc'))
            if phase in ('decode','repeat'):equal(native/(label+'.probs'),native/(arm+'-encode.probs'))
        if arm=='P':equal(native/'P-encode.arc',ROOT/ARCHIVE)
        else:
            require(all(v==audits[arm]['encode'] for v in audits[arm].values()),'lexical state counters diverged')
            equal(native/(arm+'-encode.probs'),native/'P-encode.probs')
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
    for suffix in ('encode.arc','encode.probs'):
        equal(native/('P-'+suffix),native/('K-'+suffix))
    require(len(g.commands)==32,'native phase count differs')
    g.write('lexical-comparison.json',dict(arms=audits,all_neural_streams_parent_equal=True))
    dp=deliveries['D']['binary']['bytes']-deliveries['P']['binary']['bytes']
    zp=deliveries['D']['source_zip']['bytes']-deliveries['P']['source_zip']['bytes']
    gain=arms['P']['archive_bytes']-arms['D']['archive_bytes']
    control=arms['S']['archive_bytes']-arms['D']['archive_bytes']
    require(all(v==plan['compile_commands']['P'] for v in plan['compile_commands'].values()),'unexpected build option')
    required_option='';option=0
    confirm=gain>0 and control>0 and gain-zp-option>0
    pricing=dict(deliveries=deliveries,model=g.artifact(native/'models/6m-q4-fp32.tfwc2'),
        dictionary=g.artifact(native/'dictionary/english.dic'),source_zip_increment_bytes=zp,
        binary_increment_bytes=dp,additional_required_option_bytes=option,required_option_text=required_option,
        complete_submission_package=False,complete_package_bytes=None,unresolved=package['unresolved'],
        boundary='Source ZIP and binary are alternative component prices. The observation option is not needed for coding and is excluded only after exact trace-off archive comparison. Official form, multiplicities and platform remain unresolved.')
    g.write('package.json',pricing)
    return dict(arms=arms,lexical_comparison=g.artifact(g.result/'lexical-comparison.json'),
        g_P=gain,g_S=control,required_option_increment_bytes=option,source_zip_increment_bytes=zp,binary_increment_bytes=dp,
        source_component_net_bytes=gain-zp-option,binary_component_net_bytes=gain-dp,
        unchanged_model_and_dictionary=True,parent_binary_and_archive_identity=True,
        changed_source_members=[MODEL,RUNNER],confirmation_authorized=confirm,
        P_K_archive_and_neural_identity=True,
        state_boundary='P/K archive identity; all neural outputs match P across arms and encode/decode/repeat. Dictionary activation and lookup counters match within arm. Full FXCM model-state serialization is absent; D/S deliberately change lexical model and downstream mixer state.',
        scientific_verdict='Native archive, control and source-component gains authorize unchanged independent confirmation.' if confirm else 'This fixed explicit lexical predictor does not pass every archive/control/source-component requirement.')


def main():
    validate=sys.argv[1:]==['--validate'];require(validate or not sys.argv[1:],'unsupported arguments')
    g=NativeGate(ROOT,ID,CAPS,validate_only=validate)
    if validate:print(json.dumps(dict(status='preflight_passed',inputs=len(g.inputs))));return 0
    result=dict(schema='gamma.enwiki9.explicit-lexical-terminal.v1',candidate_id=ID,experiment=g.reference,
        raw_population='[0,250000)',raw_bytes=250000,complete_package_bytes=None,
        full_corpus_score_bytes=None,objective_credit_bytes=0,larger_gate_authorized=False)
    try:result.update(execute(g),status='passed');g.verify()
    except Exception as e:result.update(status='execution_failed',failure_class=getattr(e,'category','correctness_or_evidence_failure'),error=str(e),scientific_verdict='Incomplete native lexical comparison; preserve completed evidence.')
    try:cleanup(g,'terminal');g.verify();result['child_closure_ok']=True
    except Exception as e:result.update(status='execution_failed',cleanup_error=str(e),child_closure_ok=False)
    result['commands']=g.commands
    g.write('artifacts.json',dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*')) if p.is_file() and p.name!='ppm.temp'],errors=[]))
    result['artifacts']=g.artifact(g.result/'artifacts.json');g.write('decision.json',result)
    print(json.dumps({k:result[k] for k in ('status','scientific_verdict','g_P','g_S','source_component_net_bytes','error') if k in result}))
    return 0 if result['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
