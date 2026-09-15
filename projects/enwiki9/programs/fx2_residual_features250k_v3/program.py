#!/usr/bin/env python3
"""Read-only native feature witness and affine-family cost certificate."""
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate,require,sha
from lib.fx2_residual_projection_v1 import certificate

ID='fx2_residual_features250k_v3'
PLAN='operations/provenance/'+ID+'_plan.json'
ADAPTER='operations/provenance/fx2_residual_features_adapter_v2.json'
RELEASE='results/fx2_expert_release250k_v3/'
ZIP=RELEASE+'P-source.zip'
PROFILE='operations/provenance/fx2_kda_carry_toolchain_20260913.json'
FIXTURE='results/fx2_weight_native_transfer250k_q0_v1/'
RAW=FIXTURE+'work/native/opening.raw'
STORED=FIXTURE+'work/native/opening.stored'
ARCHIVE=FIXTURE+'opening/P/archive.bin'
TRACE=FIXTURE+'work/native/opening-P-encode.trace'
CAPS=dict(cpus=[2],memory_bytes=9999998976,swap_bytes=0,scratch_bytes=24000000000,wall_seconds=1800)
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
    g.binaries[str(native/'cmix')]=sha(native/'cmix')
    g.write('package.json',dict(source_zip=g.artifact(ROOT/ZIP),binary=g.artifact(native/'cmix'),
        added_instrumentation=[g.artifact(native/r['target']) for r in json.loads(g.buffers[ADAPTER])['added_files']],
        source_observer_only=True,paid_coefficient_bytes=512,coefficients_fitted=False,
        complete_package_bytes=None,objective_credit_bytes=0,unresolved=package['unresolved']))
    for phase in ('encode','decode','repeat','untraced'):
        if phase=='decode':args=['-d','dictionary/english.dic','encode.arc','decode.raw']
        else:args=['-c','dictionary/english.dic','decode.raw' if phase=='repeat' else 'population.raw',phase+'.arc']
        env={} if phase=='untraced' else dict(GAMMA_RESIDUAL_FEATURE_TRACE=str(native/(phase+'.features')),GAMMA_FX2_CODER_TRACE=str(native/(phase+'.coder')))
        try:g.run(phase,[str(native/'cmix'),*args,'--transformer','models/6m-q4-fp32.tfwc2'],180,env=env,work=native)
        finally:cleanup(g,phase)
        if phase=='decode':equal(native/'decode.raw',native/'population.raw')
        else:equal(native/(phase+'.arc'),ROOT/ARCHIVE)
        if phase!='untraced':
            equal(native/(phase+'.coder'),ROOT/TRACE)
            require((native/(phase+'.features')).stat().st_size==N*8*12,'feature population differs')
            if phase!='encode':equal(native/(phase+'.features'),native/'encode.features')
    body=g.buffers[STORED][10:]
    receipt=certificate((native/'encode.features').read_bytes(),body,g.buffers[TRACE])
    repeat=certificate((native/'repeat.features').read_bytes(),body,(native/'repeat.coder').read_bytes())
    require(receipt==repeat,'independent certificate repeat differs')
    g.write('bound.json',receipt)
    verdict=('Family upper bound permits fitting; predictive gain and package remain unproved.'
             if receipt['rounded_can_pay_coefficients'] else
             'Entire declared rounded probability family cannot pay its512-byte table under ideal codelength pricing on this population. Finite archive is not bounded.')
    return dict(archive_bytes=33429,exact_inverse=True,repeat_archive_byte_identical=True,
        trimmed_parent_archive_byte_identical=True,all_coder_records_parent_identical=True,
        feature_encode_decode_repeat_byte_identical=True,trace_on_off_archive_identical=True,
        bound=g.artifact(g.result/'bound.json'),certificate_repeat_identical=True,
        scientific_verdict=verdict,fit_authorized_by_upper_bound=receipt['rounded_can_pay_coefficients'],
        ideal_upper_bits_diagnostic=receipt['ideal_upper_bits_diagnostic'],
        rounded_upper_bits_diagnostic=receipt['rounded_upper_bits_diagnostic'],
        missing_state_audit='Complete original model/optimizer state not serialized; every original probability,count,truth and arithmetic interval is identical.',
        new_compression_gain_bytes=0,coefficients_fitted=False)

def main():
    validate=sys.argv[1:]==['--validate'];require(not sys.argv[1:] or validate,'unsupported arguments')
    g=NativeGate(ROOT,ID,CAPS,validate_only=validate)
    if validate:print(json.dumps(dict(status='preflight_passed',inputs=len(g.inputs))));return 0
    result=dict(schema='gamma.enwiki9.residual-features-terminal.v1',candidate_id=ID,experiment=g.reference,
        raw_population='[0,250000)',raw_bytes=250000,complete_package_bytes=None,
        full_corpus_score_bytes=None,objective_credit_bytes=0,larger_gate_authorized=False)
    try:result.update(execute(g),status='passed');g.verify()
    except Exception as e:result.update(status='execution_failed',failure_class=getattr(e,'category','correctness_or_evidence_failure'),error=str(e),scientific_verdict='Incomplete residual measurement; no complete scientific verdict.')
    try:cleanup(g,'terminal');g.verify();result['child_closure_ok']=True
    except Exception as e:result.update(status='execution_failed',cleanup_error=str(e),child_closure_ok=False)
    result['commands']=g.commands
    g.write('artifacts.json',dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*')) if p.is_file() and p.name!='ppm.temp'],errors=[]))
    result['artifacts']=g.artifact(g.result/'artifacts.json');g.write('decision.json',result)
    print(json.dumps({k:result[k] for k in ('status','scientific_verdict','rounded_upper_bits_diagnostic','error') if k in result}))
    return 0 if result['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
