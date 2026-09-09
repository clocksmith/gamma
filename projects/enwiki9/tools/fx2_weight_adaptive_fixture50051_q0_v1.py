#!/usr/bin/env python3
"""Guarded native archive parity for the exact adaptive model representation."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
ID='fx2_weight_adaptive_fixture50051_q0_v1'
SPEC='operations/provenance/fx2_weight_adaptive_fixture50051_v1_inputs.json'
CAPS={'cpus':[2],'memory_bytes':9999998976,'scratch_bytes':16000000000,'swap_bytes':0,'wall_seconds':900}
ARMS=('P','K','D')
PHASES=('encode','decode','reencode')
MODELED=32478


def bootstrap():
    import os
    path='operations/adaptive/experiments/'+ID+'.json'
    raw=(ROOT/path).read_bytes()
    if sys.argv[1:]!=['--validate-only']:
        ref=json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON'])
        if ref!={'path':path,'sha256':'sha256:'+hashlib.sha256(raw).hexdigest()}:
            raise ValueError('experiment binding changed')
    inputs={row['path']:row for row in json.loads(raw)['inputs']}
    buffers={}
    for source in ('tools/'+ID+'.py','lib/fx2_native_gate_v1.py','lib/artifacts.py'):
        buffers[source]=(ROOT/source).read_bytes()
        if hashlib.sha256(buffers[source]).hexdigest()!=inputs[source]['sha256'].removeprefix('sha256:'):
            raise ValueError('bootstrap source changed')
    namespace={}
    exec(compile(buffers['lib/fx2_native_gate_v1.py'],str(ROOT/'lib/fx2_native_gate_v1.py'),'exec'),namespace)
    globals().update({key:namespace[key] for key in ('NativeGate','GateFailure','require','sha')})


def validate(gate):
    spec=json.loads(gate.buffers[SPEC])
    require(gate.contract['objective']['targetScoreBytes']==90000000,'wrong objective')
    require(gate.contract['parent']==spec['parent'],'wrong parent revision')
    for row in spec['sources']+list(spec['runtime'].values())+list(spec['population'].values()):
        data=gate.buffers[row['path']]
        require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'changed deployment input')
    parent=json.loads(gate.buffers[spec['parent_reflection']])
    require(parent['validity']['valid'] and parent['decision']['promotionPredicatesPass'],'parent reflection is not selectable')
    proof=json.loads(gate.buffers[spec['native_terminal']])
    require(proof['validity']=='valid-native-initialization-and-component-comparison' and
            proof['hypothesis_verdict']=='passed-scoped-component-gate','missing native antecedent')
    economics=proof['result']
    require(economics['native_builds']['D']['sha256']==spec['runtime']['cmix']['sha256'],'binary differs from native proof')
    delta=spec['runtime']['models/model.D']['bytes']-spec['runtime']['models/model.P']['bytes']
    require(delta==economics['model_delta_per_copy']==-6042 and economics['binary_delta_per_copy']==0,'component economics differ')
    require(max(economics['runtime_pair_delta'],economics['source_compressor_plus_decoder_delta'])<0,'components do not pay')
    raw=gate.buffers[spec['population']['raw']['path']]
    require(len(raw)==50051,'wrong raw population')
    gate.spec,gate.economics=spec,economics


def activation(gate,name,arm):
    expected=('Gamma weight loader selected='+('A' if arm=='D' else 'D')+
              ' tensors=434 histogram_tensors=111 histogram_symbols=5868864 side_information_bytes='+
              ('0' if arm=='D' else '7169')+' canonical=1').encode()
    found=[line for line in (gate.result/(name+'.stderr')).read_bytes().splitlines()
           if line.startswith(b'Gamma weight loader selected=')]
    require(found==[expected],'wrong loader activation: '+name)


class Codec:
    def __init__(self,gate,native,arm):
        self.gate,self.native,self.arm,self.count=gate,native,arm,0
        self.prefix='fixture-'+arm
        self.model='models/model.D' if arm=='D' else 'models/model.P'

    def invoke(self,phase,args):
        name=self.prefix+'-'+phase
        self.gate.verify()
        require(not (self.native/'ppm.temp').exists(),'unclosed prior PPM scratch')
        env={'GAMMA_FX2_CODER_TRACE':str(self.native/(name+'.trace'))}
        if self.arm!='P':env['GAMMA_FX2_WEIGHT_BOOKKEEPING']='1'
        self.gate.run(name,[str(self.native/'cmix'),*args,'--transformer',self.model],120,env,work=self.native)
        activation(self.gate,name,self.arm)
        require(not (self.native/'ppm.temp').exists(),'PPM scratch remained after success')
        self.gate.verify()

    def compress(self,raw):
        require(raw==self.gate.buffers[self.gate.spec['population']['raw']['path']],'wrong raw input')
        require(self.count<2,'unexpected encoder call')
        phase='encode' if self.count==0 else 'reencode';self.count+=1
        name=self.prefix+'-'+phase
        with (self.native/(name+'.raw')).open('xb') as stream:stream.write(raw)
        self.invoke(phase,['-c','dictionary/english.dic',name+'.raw',name+'.cmix'])
        return (self.native/(name+'.cmix')).read_bytes()

    def decompress(self,archive):
        name=self.prefix+'-decode'
        with (self.native/(name+'.cmix')).open('xb') as stream:stream.write(archive)
        self.invoke('decode',['-d','dictionary/english.dic',name+'.cmix',name+'.raw'])
        return (self.native/(name+'.raw')).read_bytes()


def support_module(gate):
    # Reuse the measured transfer runner's trace checks, sparse scratch cleanup
    # and artifact indexing with this gate's declared population names.
    import tools.fx2_weight_native_transfer250k_q0_v1 as support
    support.require=require
    support.POPULATIONS=({'name':'fixture'},)
    return support


def execute(gate,support):
    from lib import driver
    gate.retain_sources()
    native=gate.work/'native'
    for row in gate.spec['sources']:
        target=native/row['relative'];gate.copy(row['path'],target);target.chmod(0o444)
        gate.retained[target]=row['sha256']
    for relative,row in gate.spec['runtime'].items():
        target=native/relative;gate.copy(row['path'],target)
        target.chmod(0o555 if relative=='cmix' else 0o444);gate.retained[target]=row['sha256']
    gate.binaries[str(native/'cmix')]=gate.spec['runtime']['cmix']['sha256']
    raw=native/'fixture.raw';gate.copy(gate.spec['population']['raw']['path'],raw)
    gate.run('fixture-preprocess',[str(native/'cmix'),'-s','dictionary/english.dic','fixture.raw','fixture.stored'],30,work=native)
    support.compare_bytes(gate,native/'fixture.stored',gate.buffers[gate.spec['population']['stored']['path']],'fixed-WRT-population')
    gate.write('package-economics.json',{**gate.economics,'source_receipt':gate.artifact(ROOT/gate.spec['native_terminal']),
                'dependency_closure_complete':False,'meaning':'Incremental component alternatives against retained fixed-marginal deployment; not a full-corpus score.'})
    results,traces={},[]
    for arm in ARMS:
        model='models/model.D' if arm=='D' else 'models/model.P'
        files=[gate.artifact(native/row['relative']) for row in gate.spec['sources']]
        files += [gate.artifact(native/path) for path in ('cmix','dictionary/english.dic',model)]
        options='-c dictionary input archive --transformer model\n-d dictionary archive output --transformer model\n'
        package={'counted_files':files,'option_text':options,'counted_bytes':sum(row['bytes'] for row in files)+len(options.encode()),
                 'dependency_closure_complete':False,'source_runtime_overlap_counted_twice':True,
                 'meaning':'Conservative diagnostic source/runtime inventory; each arm includes the adaptive-capable source. Deployment component alternatives are reported separately.'}
        require(package['counted_bytes']<=10000000,'diagnostic package ceiling')
        gate.write(arm+'-package.json',package)
        output=gate.result/'fixture'/arm
        result=driver.run(ID,raw,50051,True,run_purpose='diagnostic',run_scope_label='public-fixture-'+arm,
                          run_context='Exact adaptive model loading; unchanged native predictions and archives required',
                          run_source='canonical-tool',module=Codec(gate,native,arm),artifact_dir=output,
                          package_inventory=([(row['path'],row['bytes']) for row in files]+[('required-option-text',len(options.encode()))],package))
        require(result['roundtrip_ok'] and result['determinism']['single_host_byte_equal'],'native inverse/repeat failed')
        for name in ('archive.bin','repeat.bin'):
            support.compare_bytes(gate,output/name,gate.buffers[gate.spec['population']['archive']['path']],arm+'-'+name)
        support.compare_bytes(gate,output/'restored.bin',gate.buffers[gate.spec['population']['raw']['path']],arm+'-raw')
        for phase in PHASES:
            traces.append(support.compare_trace(gate,ROOT/gate.spec['population']['trace']['path'],native/('fixture-'+arm+'-'+phase+'.trace'),MODELED*8*28))
        results[arm]={'result':gate.artifact(output/'result.json'),'exact_parent_archive':True,'exact_inverse':True,'exact_repeat':True}
    gate.write('fixture-coder-records.json',{'record_bytes':28,'records_per_phase':MODELED*8,'all_exact':True,'comparisons':traces})
    require(len(gate.commands)==10,'phase population differs')
    return {'arms':results,'coder_records_identical':True,'all_archives_match_original_parent':True,
            'archive_saved_bytes':0,'package_economics':gate.economics,'compile_processes':0}


def main():
    bootstrap();require(sys.argv[1:] in ([],['--validate-only']),'unexpected arguments')
    gate=NativeGate(ROOT,ID,CAPS,bool(sys.argv[1:]));validate(gate)
    if sys.argv[1:]:
        print(json.dumps({'status':'preflight_pass','inputs':len(gate.inputs),'codec_executed':False}));return 0
    support=support_module(gate)
    stage={'candidate_id':ID,'experiment':gate.reference,'objective_credit_bytes':0,'full_corpus_score_bytes':None,
           'larger_gate_authorized':False,'continuous_guard_decision':'pending canonical outer guard closure'}
    try:stage.update(execute(gate,support),status='passed')
    except Exception as error:stage.update(status='execution_failed',failure_class=getattr(error,'category','invariant_or_missing_evidence'),error=str(error))
    stage['child_closure_ok']=False
    try:gate.closure();gate.verify();stage['child_closure_ok']=True
    except Exception as error:stage.update(status='execution_failed',closure_error=str(error))
    cleanup=support.cleanup_native_transient(gate,stage['child_closure_ok']);gate.write('transient-cleanup.json',cleanup)
    if not cleanup['cleanup_complete'] or (stage['status']=='passed' and not cleanup['no_residual_before_cleanup']):stage['status']='execution_failed'
    stage['transient_cleanup']=gate.artifact(gate.result/'transient-cleanup.json');stage['commands']=gate.commands
    try:
        artifacts,diagnostics=support.index_artifacts(gate,gate.work/'native/ppm.temp')
        gate.write('artifact-index-diagnostics.json',diagnostics);gate.write('artifacts.json',artifacts)
        stage['artifacts']=gate.artifact(gate.result/'artifacts.json')
        if not diagnostics['complete']:stage['status']='execution_failed'
    except Exception as error:stage.update(status='execution_failed',index_error=str(error))
    gate.write('stage-decision.json',stage)
    return 0 if stage['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
