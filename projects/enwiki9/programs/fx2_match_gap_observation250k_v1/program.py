#!/usr/bin/env python3
"""Read-only native interrupted-match opportunities and fixed finite replay."""
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate,require,sha

ID='fx2_match_gap_observation250k_v1'
PLAN='operations/provenance/'+ID+'_plan.json'
ADAPTER='operations/provenance/fx2_match_gap_adapter_v1.json'
RELEASE='results/fx2_expert_release250k_v3/'
ZIP=RELEASE+'P-source.zip'
PROFILE='operations/provenance/fx2_kda_carry_toolchain_20260913.json'
FIXTURE='results/fx2_weight_native_transfer250k_q0_v1/'
RAW=FIXTURE+'work/native/opening.raw'
STORED=FIXTURE+'work/native/opening.stored'
ARCHIVE=FIXTURE+'opening/P/archive.bin'
TRACE=FIXTURE+'work/native/opening-P-encode.trace'
CAPS=dict(cpus=[2],memory_bytes=9999998976,swap_bytes=0,scratch_bytes=16000000000,wall_seconds=3600)
N=151210

class NativeGate(BaseGate):
    def verify(self):
        self.toolchain=json.loads(self.buffers[PROFILE]);super().verify()

def equal(a,b):
    require(a.stat().st_size==b.stat().st_size,'length mismatch: '+str(a))
    with a.open('rb') as x,b.open('rb') as y:
        while block:=x.read(1<<20):require(block==y.read(len(block)),'byte mismatch: '+str(a))

def cleanup(g,label):
    g.closure();path=g.work/'native/ppm.temp'
    row=dict(present=path.exists(),content_hashed=False)
    if path.exists():
        require(path.resolve()==path and path.is_file(),'transient alias')
        s=path.stat();row.update(logical_bytes=s.st_size,allocated_bytes=s.st_blocks*512);path.unlink()
    row['cleanup_complete']=not path.exists();g.write(label+'-cleanup.json',row)

def copy_or_verify(g,source,target):
    if target.exists():
        require(target.is_file() and target.resolve()==target,'runtime alias')
        require(target.read_bytes()==g.buffers[source],'ZIP runtime differs from bound delivery')
    else:g.copy(source,target)

def execute(g):
    plan=json.loads(g.buffers[PLAN]);require(plan['caps']==CAPS,'resource contract differs')
    require(len(g.buffers[RAW])==250000 and len(g.buffers[STORED])==N+10,'population differs')
    native=g.work/'native';native.mkdir()
    with zipfile.ZipFile(io.BytesIO(g.buffers[ZIP])) as z:
        names=z.namelist();require(len(names)==len(set(names))==127,'source ZIP population')
        for name in names:
            path=Path(name)
            require(not path.is_absolute() and '..' not in path.parts and not name.endswith('/'),'unsafe ZIP name')
            target=native/path;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f:f.write(z.read(name))
    g.adapter(ADAPTER,native)
    for row in json.loads(g.buffers[ADAPTER])['added_files']:g.copy(row['source']['path'],native/row['target'])
    package=json.loads(g.buffers[RELEASE+'package.json'])
    for key in ('model','dictionary'):
        row=package[key];copy_or_verify(g,row['path'],native/row['path'].split('/work/native/')[1])
    g.copy(RAW,native/'population.raw')
    g.run('compile',plan['compile_command'],360,work=native)
    built=(native/'cmix').read_bytes()
    g.run('clean-repeat',['/usr/bin/make','clean'],30,work=native)
    g.run('compile-repeat',plan['compile_command'],360,work=native)
    require((native/'cmix').read_bytes()==built,'clean repeated build differs')
    g.binaries[str(native/'cmix')]=sha(native/'cmix')
    g.write('package.json',dict(source_zip=g.artifact(ROOT/ZIP),binary=g.artifact(native/'cmix'),
        added_instrumentation=[g.artifact(native/r['target']) for r in json.loads(g.buffers[ADAPTER])['added_files']],
        source_observer_only=True,complete_package_bytes=None,objective_credit_bytes=0,unresolved=package['unresolved']))
    try:
        g.run('preprocess',[str(native/'cmix'),'-s','dictionary/english.dic','population.raw','population.stored'],180,work=native)
        equal(native/'population.stored',ROOT/STORED)
    finally:cleanup(g,'preprocess')
    for phase in ('encode','decode','repeat','untraced'):
        if phase=='decode':args=['-d','dictionary/english.dic','encode.arc','decode.raw']
        else:args=['-c','dictionary/english.dic','decode.raw' if phase=='repeat' else 'population.raw',phase+'.arc']
        env={} if phase=='untraced' else dict(GAMMA_GAP_TRACE=str(native/(phase+'.gap')))
        try:g.run(phase,[str(native/'cmix'),*args,'--transformer','models/6m-q4-fp32.tfwc2'],180,env=env,work=native)
        finally:cleanup(g,phase)
        if phase=='decode':equal(native/'decode.raw',native/'population.raw')
        else:equal(native/(phase+'.arc'),ROOT/ARCHIVE)
        if phase!='untraced':
            require((native/(phase+'.gap')).stat().st_size==N*8*8,'gap population differs')
            if phase!='encode':equal(native/(phase+'.gap'),native/'encode.gap')
    reports=[]
    for label in ('analysis','analysis-repeat'):
        target=g.result/label
        args=['/usr/bin/python3',str(ROOT/'tools/fx2_match_gap_replay_v1.py'),str(native/'encode.gap'),str(ROOT/STORED),str(native/'population.raw'),str(native/'dictionary/english.dic'),str(native/'encode.arc'),str(ROOT/TRACE),str(target)]
        g.run(label,args,360,work=native)
        reports.append(json.loads((target/'report.json').read_text()))
    require(reports[0]==reports[1],'independent analysis report repeat differs')
    first={str(p.relative_to(g.result/'analysis')):sha(p) for p in (g.result/'analysis').rglob('*') if p.is_file()}
    repeated={str(p.relative_to(g.result/'analysis-repeat')):sha(p) for p in (g.result/'analysis-repeat').rglob('*') if p.is_file()}
    require(first==repeated,'all conditional artifacts differ on repeat')
    report=reports[0]
    return dict(native_archive_bytes=33429,exact_inverse=True,repeat_archive_byte_identical=True,
        trimmed_parent_archive_byte_identical=True,all_coder_counts_parent_identical=True,
        observation_encode_decode_repeat_byte_identical=True,trace_on_off_archive_identical=True,
        report=g.artifact(g.result/'analysis/report.json'),all_conditional_artifacts_repeat_identical=True,
        active_bytes=report['active_bytes'],perfect_ideal_upper_bits_ceil=report['perfect_ideal_upper_bits_ceil'],
        conditional_g_P=report['g_P'],conditional_g_S=report['g_S'],
        native_mutation_test_authorized=report['native_mutation_test_authorized'],
        scientific_verdict=report['verdict'],new_standalone_compression_gain_bytes=0,
        missing_state_audit='Original native model/maps not fully serialized. Synthetic original Match state and predictions compare bytewise; native every coder count/truth,archive,donor/clock records and repeats match. Conditional decoder requires the counted trace; native correction remains unimplemented.')


def main():
    validate=sys.argv[1:]==['--validate'];require(not sys.argv[1:] or validate,'unsupported arguments')
    g=NativeGate(ROOT,ID,CAPS,validate_only=validate)
    if validate:print(json.dumps(dict(status='preflight_passed',inputs=len(g.inputs))));return 0
    result=dict(schema='gamma.enwiki9.match-gap-observation-terminal.v1',candidate_id=ID,experiment=g.reference,
        raw_population='[0,250000)',raw_bytes=250000,complete_package_bytes=None,
        full_corpus_score_bytes=None,objective_credit_bytes=0,larger_gate_authorized=False)
    try:result.update(execute(g),status='passed');g.verify()
    except Exception as e:result.update(status='execution_failed',failure_class=getattr(e,'category','correctness_or_evidence_failure'),error=str(e),scientific_verdict='Incomplete donor observation; no complete scientific verdict.')
    try:cleanup(g,'terminal');g.verify();result['child_closure_ok']=True
    except Exception as e:result.update(status='execution_failed',cleanup_error=str(e),child_closure_ok=False)
    result['commands']=g.commands
    g.write('artifacts.json',dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*')) if p.is_file() and p.name!='ppm.temp'],errors=[]))
    result['artifacts']=g.artifact(g.result/'artifacts.json');g.write('decision.json',result)
    print(json.dumps({k:result[k] for k in ('status','scientific_verdict','conditional_g_P','error') if k in result}))
    return 0 if result['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
