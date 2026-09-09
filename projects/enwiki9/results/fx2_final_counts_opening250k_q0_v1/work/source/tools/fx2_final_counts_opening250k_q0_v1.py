#!/usr/bin/env python3
"""Canonical bounded comparison with a supplied parent and unchanged native counts."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate,require,sha
from lib import driver

ID='fx2_final_counts_opening250k_q0_v1'
PLAN='operations/provenance/fx2_final_counts_opening250k_v1_plan.json'
CORE='tools/fx2_final_counts_replay_v1.py'
CAPS=dict(cpus=[2],memory_bytes=1073741824,swap_bytes=0,scratch_bytes=268435456,wall_seconds=900)
ARMS=('P','K','D','S')


class Codec:
    def __init__(self,g,plan,arm):self.g,self.plan,self.arm,self.calls=g,plan,arm,0
    def invoke(self,operation,source,target):
        g=self.g;name=self.arm+'-'+operation
        args=['/usr/bin/python3',str(ROOT/CORE),operation,'--input',str(source),'--output',str(target),
              '--report',str(g.work/(name+'.json')),'--q16',str(g.work/'parent.q16'),
              '--dictionary',str(g.work/'dictionary.bin'),'--library',str(g.work/'counts.so'),
              '--arm',self.arm,'--prefix',self.plan['prefix_hex'],'--raw-sha256',self.plan['raw_sha256']]
        if operation=='decode':args+=['--modeled-output',str(g.work/(self.arm+'-decoded.modeled'))]
        g.run(name,args,120)
    def compress(self,raw):
        require(raw==(self.g.work/'raw.bin').read_bytes(),'encoder raw population differs')
        operation='encode' if self.calls==0 else 'repeat';self.calls+=1
        source=self.g.work/('modeled.bin' if operation=='encode' else self.arm+'-decoded.modeled')
        output=self.g.work/(self.arm+'-'+operation+'.archive')
        self.invoke(operation,source,output);return output.read_bytes()
    def decompress(self,archive):
        path=self.g.work/(self.arm+'-decode.archive')
        with path.open('xb') as stream:stream.write(archive)
        output=self.g.work/(self.arm+'-decode.raw');self.invoke('decode',path,output);return output.read_bytes()


def execute(g):
    plan=json.loads(g.buffers[PLAN]);require(plan['id']==ID and plan['caps']==CAPS,'plan identity differs')
    for item in plan['runtime_files']:
        path=Path(item['path']);require(path.stat().st_size==item['bytes'] and sha(path)==item['sha256'],'runtime changed')
    g.retain_sources()
    for name,key in [('raw.bin','raw'),('dictionary.bin','dictionary'),('parent.archive','parent'),('counts.so','library')]:
        g.copy(plan['files'][key]['path'],g.work/name)
    stored=g.buffers[plan['files']['stored']['path']]
    require(stored[5]==7 and int.from_bytes(stored[6:10],'big')==250000 and len(stored)==151220,'stored coordinates differ')
    with (g.work/'modeled.bin').open('xb') as stream:stream.write(stored[10:])
    require((g.work/'parent.archive').read_bytes()[:46].hex()==plan['prefix_hex'],'parent prefix differs')
    g.run('project',['/usr/bin/python3',str(ROOT/CORE),'project','--input',str(g.work/'modeled.bin'),
        '--trace',str(ROOT/plan['files']['trace']['path']),'--parent',str(g.work/'parent.archive'),
        '--output',str(g.work/'parent.q16'),'--report',str(g.result/'projection.json')],120)
    require((g.work/'parent.q16').stat().st_size==2419360,'projected dependency length differs')
    local=[g.artifact(ROOT/row['path']) for row in plan['local_package_files']]
    dependencies=[g.artifact(g.work/name) for name in ('parent.q16','dictionary.bin')]
    options=plan['required_option_text']
    counted=[(row['path'],row['bytes']) for row in local+dependencies]+[('required-options',len(options.encode()))]
    package=dict(counted_files=local+dependencies,counted_bytes=sum(size for _,size in counted),
                 option_text=options,runtime_inventory=plan['runtime_files'],complete_submission_package=False,
                 standalone_decoder=False,unresolved=['Python/C++ runtime distribution and licensing','Native reconstruction of supplied parent probabilities','Official complete package accounting'])
    g.write('package.json',package)
    reports={};sizes={}
    for arm in ARMS:
        result=driver.run(ID,g.work/'raw.bin',250000,True,run_purpose='diagnostic',
            run_scope_label=arm+'-opening250k',run_context='fixed final-parent residual counts with counted external Q16 dependency',
            run_source='canonical-tool',module=Codec(g,plan,arm),package_inventory=(counted,package))
        require(result['roundtrip_ok'] and result['determinism']['single_host_byte_equal'],'driver inverse/repeat failed')
        phases={phase:json.loads((g.work/(arm+'-'+phase+'.json')).read_text()) for phase in ('encode','decode','repeat')}
        for phase in ('decode','repeat'):
            if phases[phase]!=phases['encode']:
                pairs=zip(phases['encode']['checkpoints'],phases[phase]['checkpoints'])
                first=next(((a,b) for a,b in pairs if a!=b),None)
                g.write('first-divergence.json',dict(arm=arm,phase=phase,first_checkpoint=first,
                    maximum_interval_bits=2048,reference=g.artifact(g.work/(arm+'-encode.json')),
                    target=g.artifact(g.work/(arm+'-'+phase+'.json'))))
                raise ValueError('probability/model/coder synchronization differs')
        directory=g.result/arm;directory.mkdir()
        result.update(arm=arm,standalone_decoder=False,codec_process_state='fresh-process-per-phase',artifacts={})
        for key,name,source in [('archive','archive.bin',arm+'-encode.archive'),('restored','restored.bin',arm+'-decode.raw'),('repeat_archive','repeat.bin',arm+'-repeat.archive')]:
            data=(g.work/source).read_bytes()
            with (directory/name).open('xb') as stream:stream.write(data)
            ref=g.artifact(directory/name);result['artifacts'][key]=dict(path=name,bytes=ref['bytes'],sha256=ref['sha256'])
        g.write(arm+'/result.json',result);reports[arm]=phases['encode'];sizes[arm]=reports[arm]['archive_bytes']
    require((g.result/'P/archive.bin').read_bytes()==(g.result/'K/archive.bin').read_bytes()==(g.work/'parent.archive').read_bytes(),'P/K parent payload differs')
    require(reports['P']['probability_sha256']==reports['K']['probability_sha256'],'P/K probability identity differs')
    require(reports['K']['model_state_sha256']==reports['D']['model_state_sha256'],'K/D learned-state identity differs')
    g.closure();g.verify()
    added=sum(row['bytes'] for row in plan['incremental_component_files'])+plan['incremental_option_bytes']
    return dict(correctness_pass=True,archive_bytes=sizes,archive_saving_bytes=sizes['P']-sizes['D'],
                control_margin_bytes=sizes['S']-sizes['D'],added_local_component_bytes=added,
                local_component_adjusted_saving_bytes=sizes['P']-sizes['D']-added,
                supplied_dependency_bytes=sum(row['bytes'] for row in dependencies),
                exact_parent_archive_identity=True,kd_complete_model_state_identity=True,
                reports=reports,complete_package_bytes=None,full_corpus_score_bytes=None,
                repeat_uses_independently_decoded_modeled_bytes=True,standalone_decoder=False)


def main():
    require(sys.argv[1:] in ([],['--validate-only']),'unexpected arguments')
    g=NativeGate(ROOT,ID,CAPS,validate_only=bool(sys.argv[1:]))
    if sys.argv[1:]:print(json.dumps(dict(frozen_inputs_verified=len(g.inputs))));return 0
    stage=dict(schema='gamma.enwiki9.final-counts-stage.v1',candidate_id=ID,objective_credit_bytes=0)
    try:stage.update(execute(g));stage['status']='passed'
    except Exception as error:stage.update(status='failed',failure_class=getattr(error,'category','implementation_or_evidence_failure'),error=str(error))
    try:g.closure()
    except Exception as error:stage.update(status='failed',cleanup_blocked=str(error))
    g.write('stage-decision.json',stage)
    g.write('artifacts.json',dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*')) if p.is_file()]))
    return 0 if stage['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
