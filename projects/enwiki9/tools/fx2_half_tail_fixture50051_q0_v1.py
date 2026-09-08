#!/usr/bin/env python3
"""Reuse the frozen native comparison machinery for one output-tail mutation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
ID='fx2_half_tail_fixture50051_q0_v1'
ENGINE='tools/fx2_compact_v26_fixture50051_q0_v1.py'
ENGINE_SHA='dad1c194b6c4fa0a6f35d9848cb0ec6550065b37ec231a6dfdd6560d0989a6be'
ADAPTER='operations/provenance/fx2_half_tail_native_adapter_v1.json'


def validate_half_trace(path, rows):
    if path.stat().st_size!=rows*2*421:raise ValueError('half trace length differs')
    with path.open('rb') as stream:
        for index in range(rows):
            before,after=stream.read(421),stream.read(421)
            if before[0]!=ord('I') or after[0] not in (ord('O'),ord('F')):
                raise ValueError('half trace event differs at row '+str(index))
            for record in (before,after):
                if int.from_bytes(record[1:3],'little')!=205 or int.from_bytes(record[3:11],'little')!=index:
                    raise ValueError('half trace coordinate differs at row '+str(index))


def load_engine():
    raw=(ROOT/ENGINE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ENGINE_SHA:raise ValueError('native engine source changed')
    spec=importlib.util.spec_from_file_location('half_native_engine',ROOT/ENGINE)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ID=ID;module.ADAPTER=ADAPTER;module.COMPACT=''
    return module


def bind(engine):
    def materialize(g,arm,package):
        work=g.work/arm
        for row in package['source_members']+package['runtime_members']:
            if row['path'].endswith('/cmix'):continue
            target=work/row['path'].removeprefix(engine.PARENT+'work/')
            if not target.exists():g.copy(row['path'],target)
        g.adapter(ADAPTER,work)
        for row in json.loads(g.buffers[ADAPTER])['added_files']:
            g.copy(row['source']['path'],work/row['target'])
        g.adapter(engine.TRACE_ADAPTER,work,{'src/coder/encoder.cpp','src/coder/decoder.cpp'})
        g.copy('tools/fx2_coder_trace_v1.hpp',work/'src/coder/gamma-coder-trace.h')
        return work
    def activation(stderr,arm):
        expected=(arm.encode(),b'431')
        rows=re.findall(rb'Gamma FXCM arm=([PKD]) outputs=([0-9]+)\r?\n',stderr)
        engine.require(stderr.count(b'Gamma FXCM arm=')==1 and rows==[expected],'native model activation differs')
        tail=re.findall(rb'Gamma half arm=([PKD]) rows=([0-9]+) subnormal=([0-9]+) changes=([0-9]+)\r?\n',stderr)
        engine.require(stderr.count(b'Gamma half arm=')==1 and len(tail)==1 and tail[0][0]==arm.encode() and int(tail[0][1])==32478,'half audit completion differs')
    original_execute=engine.execute
    class Gate(engine.NativeGate):
        def run(self,name,argv,cap,env=None,accepted=(0,),work=None):
            env=dict(env or {})
            if 'GAMMA_FX2_CODER_TRACE' in env:
                env['GAMMA_FX2_HALF_TRACE']=env['GAMMA_FX2_CODER_TRACE']+'.half'
            return super().run(name,argv,cap,env=env,accepted=accepted,work=work)
    def execute(g):
        stage=original_execute(g)
        summaries={}
        for arm in 'PKD':
            summaries[arm]={}
            for phase in ('encode','decode','repeat'):
                p=g.work/arm/(phase+'.trace.half')
                validate_half_trace(p,32478)
                engine.exact(g.work/'P/encode.trace.half',p)
                text=(g.result/(arm+'-'+phase+'.stderr')).read_bytes()
                m=re.search(rb'Gamma half arm=[PKD] rows=([0-9]+) subnormal=([0-9]+) changes=([0-9]+)',text)
                summaries[arm][phase]=dict(rows=int(m[1]),subnormal=int(m[2]),changed_after_floor=int(m[3]),trace=g.artifact(p))
        counts={(v['rows'],v['subnormal'],v['changed_after_floor']) for a in summaries.values() for v in a.values()}
        engine.require(len(counts)==1,'half opportunity counts differ across native phases or arms')
        stage.update(half_boundary_traces=summaries,prior_and_preconversion_output_identity=True,
                     scope='All native half input/output trajectories equal across arms; complete hidden predictor state is not serialized.')
        return stage
    engine.materialize=materialize;engine.activation=activation;engine.NativeGate=Gate;engine.execute=execute
    return engine


if __name__=='__main__':
    raise SystemExit(bind(load_engine()).main())
