#!/usr/bin/env python3
"""Native WRT elision, exact conditional parity and measured component prices."""
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate,require,sha
from lib.fx2_wrt_elision_v1 import Grammar
from tools.fx2_final_counts_replay_v1 import framing
from tools.fx2_wrt_native_adapter_v1 import mutate,ZIP,HEADER,CHANGED
from tools.fx2_expert_release250k_v3 import source_zip,equal,cleanup

ID='fx2_wrt_native250k_v1'
PLAN='operations/provenance/'+ID+'_plan.json'
PROFILE='operations/provenance/fx2_kda_carry_toolchain_20260913.json'
RELEASE='results/fx2_expert_release250k_v3/'
CONDITIONAL='results/fx2_wrt_elision250k_v2/'
RAW='results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.raw'
OBSERVER='tools/fx2_wrt_native_observer_v1.hpp'
CAPS=dict(cpus=[2],memory_bytes=9999998976,swap_bytes=0,scratch_bytes=24000000000,wall_seconds=1800)


class NativeGate(BaseGate):
    def verify(self):
        self.toolchain=json.loads(self.buffers[PROFILE]);super().verify()


def verify_trace(g,path,arm):
    meta=json.loads(g.buffers[CONDITIONAL+'projection.json'])
    body=g.buffers[CONDITIONAL+'population.modeled'];counts=g.buffers[CONDITIONAL+'parent.q16']
    require(path.stat().st_size==len(body)*8*20,'native trace population differs')
    _,vocab=framing(g.buffers[CONDITIONAL+'prefix.bin'],len(body));grammar=Grammar(meta['word_count'],vocab)
    skipped=0
    with path.open('rb') as f:
        for i,(parent,) in enumerate(struct.iter_unpack('<H',counts)):
            row=f.read(20);p,y,action=struct.unpack('<HBB',row[:4]);truth=body[i//8]>>(7-i%8)&1
            forced=grammar.forced();expected=2 if arm=='K' or forced is None else forced
            require(p==parent and y==truth and action==expected,'native count/truth/action mismatch at bit '+str(i))
            grammar.observe(y);require(row[4:]==grammar.state(),'native grammar state mismatch at bit '+str(i))
            skipped+=expected!=2
    grammar.finish()
    expected=json.loads(g.buffers[CONDITIONAL+arm+'-encode.json'])
    require(skipped==expected['elided_events'],'native elision count differs')
    return dict(events=len(body)*8,parent_count_identity=True,every_post_bit_grammar_state_identity=True,
        elided_events=skipped,trace=g.artifact(path),full_predictor_state_serialized=False)


def execute(g):
    plan=json.loads(g.buffers[PLAN]);require(plan['caps']==CAPS,'resource contract differs')
    parent,child=mutate(g.buffers[ZIP],g.buffers[HEADER])
    package=json.loads(g.buffers[RELEASE+'package.json'])
    native=g.work/'native';native.mkdir()
    for name,data in child.items():
        target=native/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    for key in ('model','dictionary'):
        row=package[key];target=native/row['path'].split('/work/native/')[1]
        if not target.exists():g.copy(row['path'],target)
        require(sha(target)==row['sha256'].removeprefix('sha256:'),'runtime asset differs')
    g.copy(RAW,native/'population.raw')
    source_zip(g.result/'P-source.zip',parent);equal(g.result/'P-source.zip',ROOT/ZIP)
    source_zip(g.result/'D-source.zip',child)
    g.copy(OBSERVER,native/'src/gamma-wrt-observer.h')
    arms={};binaries={};observations={}
    for arm in ('K','D','release'):
        if arm!='K':g.run(arm+'-clean',['/usr/bin/make','clean'],30,work=native)
        flags='' if arm=='release' else ' -DGAMMA_WRT_OBSERVE'+(' -DGAMMA_WRT_BOOKKEEPING' if arm=='K' else '')
        if arm=='release':(native/'src/gamma-wrt-observer.h').unlink()
        command=[a+flags if a.startswith('CPPFLAGS_') else a for a in plan['compile_command']]
        g.run(arm+'-compile',command,360,work=native)
        built=(native/'cmix').read_bytes()
        if arm=='release':
            g.run('release-clean-repeat',['/usr/bin/make','clean'],30,work=native)
            g.run('release-compile-repeat',command,360,work=native)
            require((native/'cmix').read_bytes()==built,'release clean build differs')
        binary=native/('cmix-'+arm);binary.write_bytes(built);binary.chmod(0o755);g.binaries[str(binary)]=sha(binary)
        binaries[arm]=g.artifact(binary)
        for phase in ('encode','decode','repeat'):
            label=arm+'-'+phase
            if phase=='decode':args=['-d','dictionary/english.dic',arm+'-encode.arc',label+'.raw']
            else:args=['-c','dictionary/english.dic',arm+'-decode.raw' if phase=='repeat' else 'population.raw',label+'.arc']
            args+=['--transformer','models/6m-q4-fp32.tfwc2']
            env={'GAMMA_WRT_TRACE':label+'.trace'} if arm!='release' else {}
            try:g.run(label,[str(binary),*args],180,env=env,work=native)
            finally:cleanup(g,label)
            if phase=='decode':equal(native/(label+'.raw'),native/'population.raw')
            else:equal(native/(label+'.arc'),ROOT/(CONDITIONAL+('K' if arm=='K' else 'D')+'-encode.arc'))
            if arm!='release':
                if phase=='encode':observations[arm]=verify_trace(g,native/(label+'.trace'),arm)
                else:equal(native/(label+'.trace'),native/(arm+'-encode.trace'))
        arc=native/(arm+'-encode.arc')
        arms[arm]=dict(archive=g.artifact(arc),archive_bytes=arc.stat().st_size,
            restored=g.artifact(native/(arm+'-decode.raw')),repeat=g.artifact(native/(arm+'-repeat.arc')),
            exact_inverse=True,archive_repeat_byte_equal=True,conditional_archive_byte_identity=True)
        g.write('completed-arms.json',dict(arms=arms,complete=False))
    g.write('native-parity.json',dict(observations=observations,trace_on_off_archive_identity=True,
        released_decoder_probability_file_dependency=False,parent_call_schedule='Every event calls Predict once and Perceive once, including omitted events; independently exercised by native synthetic codec.',
        boundary='All native counts and WRT states verified. Full parent weights/optimizer states are not serialized.'))
    zp=(g.result/'D-source.zip').stat().st_size-(g.result/'P-source.zip').stat().st_size
    bp=binaries['release']['bytes']-package['deliveries']['P']['binary']['bytes']
    gain=arms['K']['archive_bytes']-arms['release']['archive_bytes']
    pricing=dict(source_zip_increment_bytes=zp,binary_increment_bytes=bp,additional_required_option_bytes=0,
        deliveries=dict(P=dict(binary=package['deliveries']['P']['binary'],source_zip=g.artifact(g.result/'P-source.zip')),
                        D=dict(binary=binaries['release'],source_zip=g.artifact(g.result/'D-source.zip'))),
        source_members=len(child),kernel_source_bytes=len(g.buffers[HEADER]),
        model=g.artifact(native/'models/6m-q4-fp32.tfwc2'),dictionary=g.artifact(native/'dictionary/english.dic'),
        clean_build_repeat_byte_equal=True,observer_removed_before_release_build=True,
        compile_command=plan['compile_command'],complete_submission_package=False,complete_package_bytes=None,
        unresolved=package['unresolved'],boundary='Source ZIP and binary are alternative component prices. Actual official form, multiplicities, runtime closure and options remain unresolved. No supplied probability file is used by released codec.')
    g.write('package.json',pricing)
    return dict(arms=arms,native_parity=g.artifact(g.result/'native-parity.json'),g_P=gain,
        source_zip_increment_bytes=zp,binary_increment_bytes=bp,source_component_net_bytes=gain-zp,
        binary_component_net_bytes=gain-bp,complete_package_bytes=None,
        confirmation_authorized=gain>0 and gain-zp>0,
        scientific_verdict='Native elision reproduces the exact conditional gain and pays the measured source component.' if gain>0 and gain-zp>0 else 'Native exactness established; this opening-sample gain does not pay the measured source component.')


def main():
    validate=sys.argv[1:]==['--validate'];require(validate or not sys.argv[1:],'unsupported arguments')
    g=NativeGate(ROOT,ID,CAPS,validate_only=validate)
    if validate:print(json.dumps(dict(status='preflight_passed',inputs=len(g.inputs))));return 0
    result=dict(schema='gamma.enwiki9.wrt-native-terminal.v1',candidate_id=ID,experiment=g.reference,
        raw_population='[0,250000)',raw_bytes=250000,full_corpus_score_bytes=None,objective_credit_bytes=0,larger_gate_authorized=False)
    try:result.update(execute(g),status='passed');g.verify()
    except Exception as e:result.update(status='execution_failed',failure_class=getattr(e,'category','correctness_or_evidence_failure'),error=str(e),scientific_verdict='Incomplete native comparison; no economic verdict.')
    try:cleanup(g,'terminal');g.verify();result['child_closure_ok']=True
    except Exception as e:result.update(status='execution_failed',cleanup_error=str(e),child_closure_ok=False)
    result['commands']=g.commands
    g.write('artifacts.json',dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*')) if p.is_file() and p.name!='ppm.temp'],errors=[]))
    result['artifacts']=g.artifact(g.result/'artifacts.json');g.write('decision.json',result)
    print(json.dumps({k:result[k] for k in ('status','scientific_verdict','g_P','source_component_net_bytes','error') if k in result}))
    return 0 if result['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
