#!/usr/bin/env python3
"""Minimal coder adapter with the measured support state preserved verbatim."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/work'
EXPECTED={'encoder':'ecd9a2f4f39553e3864c8e9c96c7b512edca46a6fbb3197beaccaf47b0a8fdce',
          'decoder':'1bae2c108906625fb124f3fc602d1d59d814e5a415d963ab74246bf474e8bae9'}


def build():
    old=(ROOT/'lib/wrt_support_native_v1.hpp').read_text()
    new=(ROOT/'lib/wrt_support_deploy_v1.hpp').read_text()
    state=old[old.index('struct State {'):old.index('\n\nclass Audit {')]
    if state not in new:raise ValueError('measured support State changed')
    files=[]
    for name in ('encoder','decoder'):
        raw=(PARENT/('src/coder/'+name+'.cpp')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=EXPECTED[name]:raise ValueError('coder source changed')
        changes=[dict(before='#include "'+name+'.h"',after='#include "'+name+'.h"\n#include "gamma-wrt-support.h"'),
                 dict(before='  const unsigned int p = Discretize(p_->Predict());',after='  const unsigned int p = gamma_wrt_support::coder().project(Discretize(p_->Predict()));'),
                 dict(before='  p_->Perceive(bit);',after='  gamma_wrt_support::coder().observe(bit);\n  p_->Perceive(bit);')]
        text=raw.decode()
        for r in changes:
            if text.count(r['before'])!=1:raise ValueError('ambiguous coder source')
            text=text.replace(r['before'],r['after'])
        files.append(dict(source_path='src/coder/'+name+'.cpp',source_bytes=len(raw),source_sha256=EXPECTED[name],patched_bytes=len(text.encode()),patched_sha256=hashlib.sha256(text.encode()).hexdigest(),replacements=changes))
    p='lib/wrt_support_deploy_v1.hpp';raw=(ROOT/p).read_bytes()
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',adapter_id='fx2_wrt_support_deploy_v1',files=files,added_files=[dict(source=dict(path=p,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),target='src/coder/gamma-wrt-support.h')],boundary='Same causal State and probability mapping as native D; diagnostic traces, counters, labels and arm switch removed. Parent Predictor calls unchanged.')


if __name__=='__main__':print(json.dumps(build(),indent=2))
