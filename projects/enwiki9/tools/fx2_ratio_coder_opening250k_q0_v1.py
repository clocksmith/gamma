#!/usr/bin/env python3
"""Bounded cached native delivery comparison on opening250KB enwik9."""
import hashlib
import json
import os
import math
import struct
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_native_gate_v1 import GateFailure, require, sha
from fx2_ratio_coder_fixture50051_q0_v2 import TraceCacheGate
from lib.native_trace_cache_v1 import release_closed_file,memory_snapshot
from lib import driver

ID='fx2_ratio_coder_opening250k_q0_v1'
PARENT='results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'
ADAPTER='results/fx2_ratio_coder_state_v1_unit/attempt01/adapter.json'
CAPS=dict(cpus=[2],memory_bytes=9999998976,swap_bytes=0,scratch_bytes=40000000000,wall_seconds=1200)
FLAGS='-DSEED=923 -DUPDATE_LIMIT=3000 -m64 -Wall -std=c++17 -include cstdint -fno-fast-math -fno-math-errno -fno-exceptions -fno-threadsafe-statics -march=x86-64-v3 -mtune=generic -mrecip=none -fdata-sections -ffunction-sections'
N=151210
ARMS=('P','K','D','S')
RAW='results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.raw'
STORED='results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.stored'
ARCHIVE='results/fx2_weight_native_transfer250k_q0_v1/opening/P/archive.bin'
TRACE='results/fx2_weight_native_transfer250k_q0_v1/work/native/opening-P-encode.trace'
BINARY='results/fx2_ratio_coder_fixture50051_q0_v2/work/cmix'


class NativeGate(TraceCacheGate):
    def release_observations(self,label):
        self.closure();before=memory_snapshot(self.group);files=[]
        for arm in ARMS:
            for phase in ('encode','decode','repeat'):
                for suffix in ('ratio','coder'):
                    path=self.work/(arm+'-'+phase+'.'+suffix)
                    if path.exists():files.append(release_closed_file(path))
        if not hasattr(self,'corpus_cache_events'):self.corpus_cache_events=[]
        self.corpus_cache_events.append(dict(label=label,before=before,after=memory_snapshot(self.group),files=files))
        self.write('corpus-trace-cache.json',dict(events=self.corpus_cache_events,guard_unchanged=True))

    def run(self,name,argv,cap,env=None,accepted=(0,),work=None):
        # Validation can warm several closed traces before the next native phase.
        self.release_observations('before-'+name)
        return super().run(name,argv,cap,env,accepted,work)

    def artifact(self,path):
        result=super().artifact(path);p=Path(path)
        if p.is_relative_to(self.result) and p.suffix in ('.ratio','.coder'):
            # Keep manifest hashing from accumulating every trace in page cache.
            release_closed_file(p)
        return result


def equal_files(left,right):
    require(left.stat().st_size==right.stat().st_size,'file sizes differ')
    offset=0
    with left.open('rb') as a,right.open('rb') as b:
        while chunk:=a.read(1<<20):
            other=b.read(len(chunk))
            if chunk!=other:
                first=next(i for i,(x,y) in enumerate(zip(chunk,other)) if x!=y)
                raise ValueError('first divergence at byte '+str(offset+first))
            offset+=len(chunk)


STATE_BYTES=5971
RECORD_BYTES=STATE_BYTES+5


def delivery_records(path,arm,modeled=N):
    require(path.stat().st_size==2*modeled*RECORD_BYTES,'incomplete delivery state trace')
    with path.open('rb') as stream:
        for i in range(2*modeled):
            record=stream.read(RECORD_BYTES);state=record[5:];ratio=state[10:2486]
            event=ord('I') if i==0 else ord('P') if i%2 else ord('O')
            require(record[0]==event and int.from_bytes(record[1:5],'little')==STATE_BYTES,
                    'delivery framing differs at record '+str(i))
            require(state[:4]==b'GRD2' and int.from_bytes(state[4:6],'little')==205 and
                    state[6]==ord(arm) and state[7]==int(i>0) and
                    int.from_bytes(state[8:10],'little')==2476,
                    'delivery header differs at record '+str(i))
            require(ratio[:4]==b'GRR1' and int.from_bytes(ratio[4:6],'little')==205 and
                    ratio[6]==ord('D' if arm=='K' else arm) and ratio[7]==i%2 and
                    int.from_bytes(ratio[8:16],'little')==i//2,
                    'ratio state position differs at record '+str(i))
            yield state


def validate_ratio_trace(path,arm,modeled=N):
    records=sum(1 for _ in delivery_records(path,arm,modeled))
    return dict(records=records,state_bytes=STATE_BYTES,record_bytes=RECORD_BYTES,sha256=sha(path))


def compare_delivery_states(parent,target,parent_arm,target_arm,modeled=N,full=False):
    count=0
    for i,(p,d) in enumerate(zip(delivery_records(parent,parent_arm,modeled),
                                 delivery_records(target,target_arm,modeled))):
        # Vocabulary and exact cached original masses must agree for every arm.
        for offset in range(2486,STATE_BYTES,17):
            require(p[offset:offset+9]==d[offset:offset+9],
                    'original row or vocabulary differs at state '+str(i)+' offset '+str(offset))
        if full:
            require(p[:6]+b'D'+p[7:]==d[:6]+b'D'+d[7:],
                    'K/D correction state differs at state '+str(i))
        count+=1
    return dict(records=count,base_rows_identical=True,full_state_equal_except_arm=full)


def compare_parent_projection(parent,target,modeled=N):
    expected=modeled*8*28
    require(parent.stat().st_size==target.stat().st_size==expected,'coder projection length differs')
    changed=0;thirds=[0.0]*3;digest=hashlib.sha256();index=0
    with parent.open('rb') as a,target.open('rb') as b:
        while block:=a.read(28*4096):
            other=b.read(len(block))
            for p,d in zip(struct.iter_unpack('<7I',block),struct.iter_unpack('<7I',other)):
                require(p[0]==d[0] and p[6]==d[6],
                        'original prediction or truth differs at bit '+str(index))
                require(p[6] in (0,1) and 1<=p[1]<=65535 and 1<=d[1]<=65535,
                        'invalid coder probability or truth at bit '+str(index))
                digest.update(struct.pack('<II',p[0],p[6]))
                changed+=p[1]!=d[1]
                pa=p[1] if p[6] else 65536-p[1];qa=d[1] if d[6] else 65536-d[1]
                thirds[min(2,index*3//(modeled*8))]+=math.log2(qa/pa)
                index+=1
    return dict(records=index,original_float_and_truth_identical=True,projection_sha256=digest.hexdigest(),
                changed_q16_events=changed,ideal_bits_saved=sum(thirds),chronological_thirds=thirds)


def validate_activation(stderr,arm):
    prefix=b'Gamma ratio selected='
    require(stderr.count(prefix)==1 and
            re.findall(rb'Gamma ratio selected=([PKDS])\r?\n',stderr)==[arm.encode()],
            'native calibration activation differs')


class Codec:
    def __init__(self,gate,arm):self.gate,self.arm,self.calls=gate,arm,0
    def compress_arm(self,raw,arm):
        require(arm==self.arm,'compress arm differs');return self.compress(raw)
    def decompress_arm(self,archive,arm):
        require(arm==self.arm,'decode arm differs');return self.decompress(archive)
    def invoke(self,phase,args,traces=True):
        g=self.gate;name=self.arm+'-'+phase
        env={'GAMMA_FX2_RATIO_ARM':self.arm}
        if traces:
            env.update(GAMMA_FX2_CODER_TRACE=str(g.work/(name+'.coder')),
                       GAMMA_FX2_RATIO_TRACE=str(g.work/(name+'.ratio')))
        g.run(name,[str(g.work/'cmix'),*args],120,env=env)
        validate_activation((g.result/(name+'.stderr')).read_bytes(),self.arm)
    def compress(self,raw):
        name='encode' if self.calls==0 else 'repeat';self.calls+=1
        stem=self.arm+'-'+name
        with (self.gate.work/(stem+'.raw')).open('xb') as f:f.write(raw)
        self.invoke(name,['-c','dictionary/english.dic',stem+'.raw',stem+'.cmix','--transformer','models/6m-q4-fp32.tfwc2'])
        return (self.gate.work/(stem+'.cmix')).read_bytes()
    def decompress(self,archive):
        stem=self.arm+'-decode'
        with (self.gate.work/(stem+'.cmix')).open('xb') as f:f.write(archive)
        self.invoke('decode',['-d','dictionary/english.dic',stem+'.cmix',stem+'.raw','--transformer','models/6m-q4-fp32.tfwc2'])
        return (self.gate.work/(stem+'.raw')).read_bytes()


def run_native_arm(g,arm,counted,package):
    # The adapter launches a fresh native process for every phase. Supplying
    # driver arm dispatch would instead reload the Python registration stub.
    result=driver.run(ID,g.work/'population.raw',250000,True,run_purpose='diagnostic',
        run_scope_label=arm+'-opening250k',run_context='native coder-boundary ratio; fixed opening250k development population',
        run_source='canonical-tool',module=Codec(g,arm),package_inventory=(counted,package))
    result.update(arm=arm,codec_process_state='fresh-native-process-per-encode-decode-repeat')
    directory=g.result/arm;directory.mkdir(exist_ok=False)
    result['artifacts']={}
    for key,name,source in (('archive','archive.bin',arm+'-encode.cmix'),
                            ('restored','restored.bin',arm+'-decode.raw'),
                            ('repeat_archive','repeat.bin',arm+'-repeat.cmix')):
        payload=(g.work/source).read_bytes()
        with (directory/name).open('xb') as f:f.write(payload)
        result['artifacts'][key]=dict(path=name,bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
    g.write(arm+'/result.json',result)
    return result


def execute(g):
    package=json.loads(g.buffers[PARENT+'package.json'])
    for row in package['source_members']:
        g.copy(row['path'],g.work/row['path'].removeprefix(PARENT+'work/'))
    for row in package['runtime_members']:
        if not row['path'].endswith('/cmix'):
            target=g.work/row['path'].removeprefix(PARENT+'work/')
            if not target.exists():g.copy(row['path'],target)
    g.adapter(ADAPTER,g.work)
    for row in json.loads(g.buffers[ADAPTER])['added_files']:
        g.copy(row['source']['path'],g.work/row['target'])
    # Reuse the executable measured by the successful complete fixture.
    g.copy(BINARY,g.work/'cmix');(g.work/'cmix').chmod(0o555)
    g.binaries[str(g.work/'cmix')]=sha(g.work/'cmix')
    g.copy(RAW,g.work/'population.raw')
    require((g.work/'population.raw').stat().st_size==250000,'wrong raw population length')
    g.run('preprocess',[str(g.work/'cmix'),'-s','dictionary/english.dic','population.raw','population.stored'],30)
    equal_files(g.work/'population.stored',ROOT/STORED)
    require((g.work/'population.stored').stat().st_size==N+10,'modeled population length differs')
    g.run('disassemble',['/usr/bin/objdump','-d','--insn-width=16','cmix'],30)
    assembly=(g.result/'disassemble.stdout').read_text()
    require(not re.search(r'\b(?:v?(?:rcp|rsqrt)(?:14|28)?(?:ss|ps))\b|%zmm|%k[0-7]|\{vex\}',assembly),
            'nonportable arithmetic instructions')
    source_files=[g.work/row['path'].removeprefix(PARENT+'work/') for row in package['source_members']]
    source_files += [g.work/row['target'] for row in json.loads(g.buffers[ADAPTER])['added_files']]
    runtime=[g.work/'cmix',g.work/'dictionary/english.dic',g.work/'models/6m-q4-fp32.tfwc2']
    options='-c dictionary/english.dic input archive --transformer models/6m-q4-fp32.tfwc2\n-d dictionary/english.dic archive output --transformer models/6m-q4-fp32.tfwc2\nGAMMA_FX2_RATIO_ARM=D\n'
    inventory=[g.artifact(p) for p in source_files+runtime]
    source_delta=sum(p.stat().st_size for p in source_files)-package['source_member_bytes']
    binary_delta=(g.work/'cmix').stat().st_size-package['runtime_members'][0]['bytes']
    counted=[(x['path'],x['bytes']) for x in inventory]+[('required-options',len(options.encode()))]
    local_package=dict(counted_files=inventory,option_text=options,counted_bytes=sum(x[1] for x in counted),
        source_runtime_overlap_counted_twice=True,complete_submission_package=False,
        source_delta_bytes=source_delta,binary_delta_bytes=binary_delta,unresolved=package['unresolved'])
    require(local_package['counted_bytes']<=10000000,'local package ceiling')
    g.write('package.json',local_package)
    for value in ('','DD','d','X'):
        name='invalid-'+str(len(g.commands))
        g.run(name,[str(g.work/'cmix'),'-c','dictionary/english.dic','population.raw',name+'.cmix',
            '--transformer','models/6m-q4-fp32.tfwc2'],30,env={'GAMMA_FX2_RATIO_ARM':value},accepted=(1,))
        require('Gamma ratio' in (g.result/(name+'.stderr')).read_text(),'unnamed activation rejection')
    rows={}
    for arm in ARMS:
        result=run_native_arm(g,arm,counted,local_package)
        require(result['roundtrip_ok'] and result['determinism']['single_host_byte_equal'],'inverse or repeat failed')
        trace_rows=[]
        for phase in ('encode','decode','repeat'):
            g.compare_trace(g.work/(arm+'-encode.coder'),g.work/(arm+'-'+phase+'.coder'),N*8*28)
            equal_files(g.work/(arm+'-encode.ratio'),g.work/(arm+'-'+phase+'.ratio'))
            trace_rows.append(validate_ratio_trace(g.work/(arm+'-'+phase+'.ratio'),arm))
        if arm in ('P','K'):
            equal_files(g.result/arm/'archive.bin',ROOT/ARCHIVE)
            g.compare_trace(ROOT/TRACE,
                            g.work/(arm+'-encode.coder'),N*8*28)
            g.compare_trace(g.work/'P-encode.coder',g.work/(arm+'-encode.coder'),N*8*28)
        codec=Codec(g,arm);name=arm+'-plain'
        codec.invoke('plain',['-c','dictionary/english.dic','population.raw',name+'.cmix',
            '--transformer','models/6m-q4-fp32.tfwc2'],traces=False)
        equal_files(g.work/(name+'.cmix'),g.result/arm/'archive.bin')
        rows[arm]=dict(result=g.artifact(g.result/arm/'result.json'),archive_bytes=(g.result/arm/'archive.bin').stat().st_size,
                       calibration_traces=trace_rows)
    projections={arm:compare_parent_projection(g.work/'P-encode.coder',g.work/(arm+'-encode.coder')) for arm in ARMS}
    original_rows={arm:compare_delivery_states(g.work/'P-encode.ratio',g.work/(arm+'-encode.ratio'),'P',arm) for arm in ARMS}
    kd=compare_delivery_states(g.work/'K-encode.ratio',g.work/'D-encode.ratio','K','D',full=True)
    g.release_observations('after-final-comparisons')
    return dict(raw_bytes=250000,modeled_bytes=N,offset=0,cached_native_binary=g.artifact(g.work/'cmix'),compile_processes=0,parent_projections=projections,original_rows=original_rows,kd_state=kd,arms=rows,correctness_pass=True,archive_saving_bytes=rows['P']['archive_bytes']-rows['D']['archive_bytes'],
                control_margin_bytes=rows['S']['archive_bytes']-rows['D']['archive_bytes'],
                source_delta_bytes=source_delta,binary_delta_bytes=binary_delta,
                added_local_component_bytes=source_delta+binary_delta+len(options.encode())-package['option_bytes'],
                complete_package_bytes=None)


def main():
    require(sys.argv[1:] in ([],['--validate-only']),'unexpected arguments')
    g=NativeGate(ROOT,ID,CAPS,validate_only=bool(sys.argv[1:]))
    if sys.argv[1:]:print(json.dumps(dict(frozen_inputs_verified=len(g.inputs))));return 0
    stage=dict(schema='gamma.enwiki9.native-ratio-stage.v1',candidate_id=ID,objective_credit_bytes=0)
    try:
        stage.update(execute(g));g.verify();g.closure();stage['status']='passed'
    except Exception as e:
        stage.update(status='failed',failure_class=getattr(e,'category','implementation_or_evidence_failure'),error=str(e))
    # Only owned native transient PPM files; preserve all archive and trace evidence.
    removed=[]
    try:
        g.closure()
    except Exception as e:
        stage.update(status='failed',cleanup_blocked=str(e))
        g.write('stage-decision.json',stage)
        return 1
    for name in ('ppm.temp',):
        p=g.work/name
        if p.is_file():removed.append(dict(path=name,bytes=p.stat().st_size));p.unlink()
    stage['transient_cleanup']=removed
    g.write('stage-decision.json',stage)
    g.write('artifacts.json',dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*')) if p.is_file()]))
    return 0 if stage['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
