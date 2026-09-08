#!/usr/bin/env python3
"""Bounded same-build native FX2 residual calibration comparison."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate, GateFailure, require, sha
from lib import driver

ID='fx2_residual_ratio_fixture50051_q0_v3'
PARENT='results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'
ADAPTER='results/fx2_residual_ratio_native_v1/attempt01/adapter.json'
CAPS=dict(cpus=[2],memory_bytes=9999998976,swap_bytes=0,scratch_bytes=24000000000,wall_seconds=1200)
FLAGS='-DSEED=923 -DUPDATE_LIMIT=3000 -m64 -Wall -std=c++17 -include cstdint -fno-fast-math -fno-math-errno -fno-exceptions -fno-threadsafe-statics -march=x86-64-v3 -mtune=generic -mrecip=none -fdata-sections -ffunction-sections'
N=32478
ARMS=('P','K','D','S')


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


def validate_ratio_trace(path,arm,modeled=N):
    state_bytes=16+12*205;record_bytes=state_bytes+5
    require(path.stat().st_size==2*modeled*record_bytes,'incomplete calibration state trace')
    with path.open('rb') as stream:
        for i in range(2*modeled):
            record=stream.read(record_bytes);state=record[5:]
            event=ord('I') if i==0 else ord('P') if i%2 else ord('O')
            require(record[0]==event and int.from_bytes(record[1:5],'little')==state_bytes,'state event framing differs')
            require(state[:4]==b'GRR1' and int.from_bytes(state[4:6],'little')==205 and
                    state[6]==ord(arm) and state[7]==i%2 and
                    int.from_bytes(state[8:16],'little')==i//2,'state position or arm differs')
    return dict(records=2*modeled,state_bytes=state_bytes,record_bytes=record_bytes,sha256=sha(path))


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
    result=driver.run(ID,g.work/'prof_input/input',50051,True,run_purpose='diagnostic',
        run_scope_label=arm+'-public-fixture',run_context='native residual ratio; fixed public fixture',
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
    # Reuse only the existing coder instrumentation, not the argmax mutation.
    g.adapter('operations/provenance/public_fx2_argmax_native_adapter_v1.json',g.work,
              {'src/coder/encoder.cpp','src/coder/decoder.cpp'})
    g.copy('tools/fx2_coder_trace_v1.hpp',g.work/'src/coder/gamma-coder-trace.h')
    g.run('compile',['/usr/bin/make','-j1','cmix','CC=/usr/bin/g++',
        'CPPFLAGS_PART-THAT-SHOULD-BE-FAST='+FLAGS+' -O3',
        'CPPFLAGS_PART-THAT-CAN-BE-SLOW='+FLAGS+' -Os'],180)
    g.binaries[str(g.work/'cmix')]=sha(g.work/'cmix')
    g.run('disassemble',['/usr/bin/objdump','-d','--insn-width=16','cmix'],30)
    assembly=(g.result/'disassemble.stdout').read_text()
    require(not re.search(r'\b(?:v?(?:rcp|rsqrt)(?:14|28)?(?:ss|ps))\b|%zmm|%k[0-7]|\{vex\}',assembly),
            'nonportable arithmetic instructions')
    source_files=[g.work/row['path'].removeprefix(PARENT+'work/') for row in package['source_members']]
    source_files += [g.work/'src/gamma-residual-ratio.h',g.work/'src/coder/gamma-coder-trace.h']
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
        g.run(name,[str(g.work/'cmix'),'-c','dictionary/english.dic','prof_input/input',name+'.cmix',
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
            equal_files(g.result/arm/'archive.bin',ROOT/(PARENT+'work/fixture.cmix'))
            g.compare_trace(ROOT/'results/fx2_cmix_transformer_argmax_fixture50051_q0_v1/work/P-encode.trace',
                            g.work/(arm+'-encode.coder'),N*8*28)
            g.compare_trace(g.work/'P-encode.coder',g.work/(arm+'-encode.coder'),N*8*28)
        codec=Codec(g,arm);name=arm+'-plain'
        codec.invoke('plain',['-c','dictionary/english.dic','prof_input/input',name+'.cmix',
            '--transformer','models/6m-q4-fp32.tfwc2'],traces=False)
        equal_files(g.work/(name+'.cmix'),g.result/arm/'archive.bin')
        rows[arm]=dict(result=g.artifact(g.result/arm/'result.json'),archive_bytes=(g.result/arm/'archive.bin').stat().st_size,
                       calibration_traces=trace_rows)
    return dict(arms=rows,correctness_pass=True,archive_saving_bytes=rows['P']['archive_bytes']-rows['D']['archive_bytes'],
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
