#!/usr/bin/env python3
"""Guarded native archive parity for the exact adaptive model representation."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
ID='fx2_weight_adaptive_transfer250k_q0_v1'
SPEC='operations/provenance/fx2_weight_adaptive_transfer250k_v1_inputs.json'
CAPS={'cpus':[2],'memory_bytes':9999998976,'scratch_bytes':16000000000,'swap_bytes':0,'wall_seconds':1100}
ARMS=('P','K','D')
PHASES=('encode','decode','reencode')


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
    populations=spec['populations']
    require([(p['name'],p['offset'],p['modeled']) for p in populations]==
            [('opening',0,151210),('distant',500000000,166098)],'wrong populations')
    references=spec['sources']+list(spec['runtime'].values())
    for population in populations:
        references += [population[k] for k in ('raw','stored','archive','trace')]
    for row in references:
        data=gate.buffers[row['path']]
        require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'changed deployment input')
    parent=json.loads(gate.buffers[spec['parent_reflection']])
    require(parent['validity']['valid'] and parent['decision']['promotionPredicatesPass'] and
            parent['candidateId']==spec['parent']['candidateId'],'parent fixture is not selectable')
    fixture=json.loads(gate.buffers[spec['parent_terminal']])
    require(fixture['status']=='passed' and fixture['all_parent_records_identical'],'missing native fixture parity')
    transfer=json.loads(gate.buffers[spec['transfer_terminal']])
    history=json.loads(gate.buffers[spec['transfer_reflection']])
    require(transfer['validity']=='valid' and history['validity']['valid'] and
            transfer['scientific_measurements']['coder_records_identical'],'retained transfer is not valid')
    prior={p['name']:p for p in transfer['population']['populations']}
    for population in populations:
        previous=prior[population['name']]
        require(population['raw']==previous['raw'] and population['stored']==previous['stored'] and
                population['archive']==previous['arms']['P']['archive'] and
                population['trace'] in transfer['coder_records'],'population differs from retained transfer')
    proof=json.loads(gate.buffers[spec['native_terminal']])
    require(proof['validity']=='valid-native-production-entrypoint-and-component-comparison' and
            proof['hypothesis_verdict']=='passed-scoped-component-gate','missing native antecedent')
    economics=proof['result']
    require(economics==fixture['package_economics'],'native fixture package changed')
    require(economics['native_builds']['D']['sha256']==spec['runtime']['cmix']['sha256'],'binary differs from native proof')
    require(spec['runtime']['models/model.D']['bytes']-spec['runtime']['models/model.P']['bytes']==
            economics['model_delta_per_copy']==-6042,'model economics differ')
    require(economics['binary_delta_per_copy']==0 and economics['raw_source_delta']==914,'native economics differ')
    require(max(economics['runtime_pair_delta'],economics['source_compressor_plus_decoder_delta'])<0,'components do not pay')
    for population in populations:
        require(population['raw']['bytes']==250000 and population['stored']['bytes']==population['modeled']+10,
                'wrong frontend population')
        require(population['trace']['bytes']==population['modeled']*8*28,'wrong reference trace population')
    gate.spec,gate.economics=spec,economics


def activation(gate,name,arm):
    expected=('Gamma weight loader selected='+('A' if arm=='D' else 'D')+
              ' tensors=434 histogram_tensors=111 histogram_symbols=5868864 side_information_bytes='+
              ('0' if arm=='D' else '7169')+' canonical=1').encode()
    found=[line for line in (gate.result/(name+'.stderr')).read_bytes().splitlines()
           if line.startswith(b'Gamma weight loader selected=')]
    require(found==[expected],'wrong loader activation: '+name)


class Codec:
    def __init__(self,gate,native,arm,population):
        self.gate,self.native,self.arm,self.count=gate,native,arm,0
        self.population=population
        self.prefix=population['name']+'-'+arm
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
        require(raw==self.gate.buffers[self.population['raw']['path']],'wrong raw input')
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
    support.POPULATIONS=gate.spec['populations']
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
    gate.write('package-economics.json',{**gate.economics,'source_receipt':gate.artifact(ROOT/gate.spec['native_terminal']),
                'dependency_closure_complete':False,'meaning':'Unchanged incremental component alternatives; not a full-corpus score.'})
    populations=[]
    for population in gate.spec['populations']:
        name=population['name'];raw=native/(name+'.raw');gate.copy(population['raw']['path'],raw)
        gate.run(name+'-preprocess',[str(native/'cmix'),'-s','dictionary/english.dic',name+'.raw',name+'.stored'],30,work=native)
        support.compare_bytes(gate,native/(name+'.stored'),gate.buffers[population['stored']['path']],name+'-WRT-population')
        results,traces={},[]
        for arm in ARMS:
            model='models/model.D' if arm=='D' else 'models/model.P'
            files=[gate.artifact(native/row['relative']) for row in gate.spec['sources']]
            files += [gate.artifact(native/path) for path in ('cmix','dictionary/english.dic',model)]
            options='-c dictionary input archive --transformer model\n-d dictionary archive output --transformer model\n'
            package={'counted_files':files,'option_text':options,'counted_bytes':sum(row['bytes'] for row in files)+len(options.encode()),
                     'dependency_closure_complete':False,'source_runtime_overlap_counted_twice':True,
                     'meaning':'Conservative diagnostic source/runtime inventory; deployment alternatives are reported separately.'}
            require(package['counted_bytes']<=10000000,'diagnostic package ceiling')
            gate.write(name+'-'+arm+'-package.json',package)
            output=gate.result/name/arm
            result=driver.run(ID,raw,250000,True,run_purpose='diagnostic',run_scope_label=name+'-adaptive-model-'+arm,
                              run_context='Exact adaptive model transfer; retained native probabilities and archives required',
                              run_source='canonical-tool',module=Codec(gate,native,arm,population),artifact_dir=output,
                              package_inventory=([(row['path'],row['bytes']) for row in files]+[('required-option-text',len(options.encode()))],package))
            require(result['roundtrip_ok'] and result['determinism']['single_host_byte_equal'],'native inverse/repeat failed')
            for filename in ('archive.bin','repeat.bin'):
                support.compare_bytes(gate,output/filename,gate.buffers[population['archive']['path']],name+'-'+arm+'-'+filename)
            support.compare_bytes(gate,output/'restored.bin',gate.buffers[population['raw']['path']],name+'-'+arm+'-raw')
            for phase in PHASES:
                traces.append(support.compare_trace(gate,ROOT/population['trace']['path'],native/(name+'-'+arm+'-'+phase+'.trace'),population['modeled']*8*28))
            results[arm]={'result':gate.artifact(output/'result.json'),'exact_parent_archive':True,'exact_inverse':True,'exact_repeat':True}
        gate.write(name+'-coder-records.json',{'record_bytes':28,'records_per_phase':population['modeled']*8,'all_exact':True,'comparisons':traces})
        populations.append({'name':name,'raw_bytes':250000,'modeled_bytes':population['modeled'],'arms':results})
        gate.write('populations.json',{'completed':populations,'all_populations_complete':len(populations)==2})
    require(len(gate.commands)==20,'phase population differs')
    return {'populations':populations,'coder_records_identical':True,'all_archives_match_original_parent':True,
            'all_populations_complete':True,'archive_saved_bytes':0,'package_economics':gate.economics,'compile_processes':0}


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
