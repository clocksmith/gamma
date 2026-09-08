#!/usr/bin/env python3
"""Compose the authenticated coder trace adapter with causal WRT support."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/work'
TRACE='operations/provenance/public_fx2_argmax_native_adapter_v1.json'


def build():
    base=json.loads((ROOT/TRACE).read_text());files=[]
    for row in base['files']:
        if row['source_path'] not in ('src/coder/encoder.cpp','src/coder/decoder.cpp'):continue
        raw=(PARENT/row['source_path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row['source_sha256']:raise ValueError('coder preimage changed')
        changes=list(row['replacements'])+[
          dict(before='#include "gamma-coder-trace.h"',after='#include "gamma-coder-trace.h"\n#include "gamma-wrt-support.h"'),
          dict(before='const unsigned int p = Discretize(gamma_probability);',after='const unsigned int p = gamma_wrt_support::audit().project(Discretize(gamma_probability));'),
          dict(before='  p_->Perceive(bit);',after='  gamma_wrt_support::audit().observe(bit);\n  p_->Perceive(bit);')]
        text=raw.decode()
        for change in changes:
            if text.count(change['before'])!=1:raise ValueError('ambiguous coder anchor')
            text=text.replace(change['before'],change['after'])
        files.append(dict(source_path=row['source_path'],source_bytes=len(raw),source_sha256=hashlib.sha256(raw).hexdigest(),patched_bytes=len(text.encode()),patched_sha256=hashlib.sha256(text.encode()).hexdigest(),replacements=changes))
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',adapter_id='fx2_wrt_support_native_v1',files=files,
                added_files=[dict(source=dict(path=p,bytes=(ROOT/p).stat().st_size,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()),target=target) for p,target in [('lib/wrt_support_native_v1.hpp','src/coder/gamma-wrt-support.h'),('tools/fx2_coder_trace_v1.hpp','src/coder/gamma-coder-trace.h')]],boundary='Only final coder probabilities change in D; all parent Predict and Perceive calls remain exactly once and unchanged. Decoder constraint state updates only from decoded bits.')


if __name__=='__main__':print(json.dumps(build(),indent=2))
