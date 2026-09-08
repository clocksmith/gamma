#!/usr/bin/env python3
"""Native P/K/D WRT support comparison using the existing guarded engine."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct

ROOT=Path(__file__).resolve().parents[1]
ID='fx2_wrt_support_fixture50051_q0_v1'
ENGINE='tools/fx2_compact_v26_fixture50051_q0_v1.py'
ENGINE_SHA='dad1c194b6c4fa0a6f35d9848cb0ec6550065b37ec231a6dfdd6560d0989a6be'
ADAPTER='operations/provenance/fx2_wrt_support_native_adapter_v1.json'


def load_engine():
    if hashlib.sha256((ROOT/ENGINE).read_bytes()).hexdigest()!=ENGINE_SHA:raise ValueError('engine source changed')
    spec=importlib.util.spec_from_file_location('wrt_native_engine',ROOT/ENGINE)
    engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
    engine.ID=ID;engine.ADAPTER=ADAPTER;engine.COMPACT=''
    return engine


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
        return work
    def activation(stderr,arm):
        rows=re.findall(rb'Gamma WRT arm=([PKD]) bits=([0-9]+) forced=([0-9]+) changes=([0-9]+)\r?\n',stderr)
        engine.require(stderr.count(b'Gamma WRT arm=')==1 and rows==[(arm.encode(),b'259824',b'7994',b'7994')],'WRT activation or completed opportunity counts differ')
    original_execute=engine.execute
    class Gate(engine.NativeGate):
        def run(self,name,argv,cap,env=None,accepted=(0,),work=None):
            env=dict(env or {})
            if 'GAMMA_FX2_CODER_TRACE' in env:env['GAMMA_FX2_WRT_TRACE']=env['GAMMA_FX2_CODER_TRACE']+'.wrt'
            return super().run(name,argv,cap,env=env,accepted=accepted,work=work)
    def execute(g):
        stage=original_execute(g);traces={}
        parent=g.work/'P/encode.trace.wrt'
        for arm in 'PKD':
            traces[arm]={}
            for phase in ('encode','decode','repeat'):
                path=g.work/arm/(phase+'.trace.wrt')
                engine.require(path.stat().st_size==259824*16,'introduced-state trace length differs')
                engine.exact(parent,path)
                traces[arm][phase]=g.artifact(path)
        parents=struct.iter_unpack('<7I',(g.work/'P/encode.trace').read_bytes())
        treatment=struct.iter_unpack('<7I',(g.work/'D/encode.trace').read_bytes())
        count=0
        for p,d in zip(parents,treatment,strict=True):
            engine.require(p[0]==d[0] and p[6]==d[6],'unchanged parent float trajectory differs')
            count+=p[1]!=d[1]
        engine.require(count==7994,'quantized constraint activation differs')
        stage.update(introduced_state_traces=traces,introduced_state_identity=True,
                     original_float_prediction_identity=True,changed_quantized_events=count,
                     scope='Exact introduced WRT state and original float trajectory across arms; full parent hidden state is not serialized.')
        return stage
    engine.materialize=materialize;engine.activation=activation;engine.NativeGate=Gate;engine.execute=execute
    return engine


if __name__=='__main__':raise SystemExit(bind(load_engine()).main())
