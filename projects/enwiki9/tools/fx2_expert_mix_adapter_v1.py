#!/usr/bin/env python3
"""Authenticate and materialize one parent-preserving expert mixture."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARENT='results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'

def build():
    changes={'src/predictor.cpp':[
        ('#include "predictor.h"','#include "predictor.h"\n#include "gamma-expert-mix.h"'),
        ('  layers_[0].SetInput(input_index++,\n      byte_model_ ? byte_model_->Predict()[0] : 0.5f);',
         '  const float gamma_ppm = byte_model_ ? byte_model_->Predict()[0] : 0.5f;\n  layers_[0].SetInput(input_index++, gamma_ppm);'),
        ('  p = sse_.Predict(p);','  p = sse_.Predict(p);\n  gamma_expert_mix::capture(gamma_ppm, byte_mixer_output,\n      fxcm_model_outputs[fxcm_model_outputs.size()-1], byte_mixer_override < 0);')]}
    coder=json.loads((ROOT/'operations/provenance/public_fx2_argmax_native_adapter_v1.json').read_text())
    for row in coder['files']:
        name=row['source_path']
        if name not in ('src/coder/encoder.cpp','src/coder/decoder.cpp'):continue
        replacements=[(r['before'],r['after']) for r in row['replacements']]
        # The existing instrumentation calls Predict once and saves its float.
        modified=[]
        for before,after in replacements:
            if '#include "gamma-coder-trace.h"' in after:
                after=after.replace('#include "gamma-coder-trace.h"','#include "gamma-coder-trace.h"\n#include "../gamma-expert-mix.h"')
            if 'const unsigned int p = Discretize(' in after:
                after=after.replace('const unsigned int p = Discretize(gamma_probability);',
                    'const unsigned int p = gamma_expert_mix::predict(Discretize(gamma_probability));')
            modified.append((before,after))
        modified.append(('  p_->Perceive(bit);','  gamma_expert_mix::observe(bit);\n  p_->Perceive(bit);'))
        changes[name]=modified
    expected={r['path']:r['sha256'].removeprefix('sha256:') for r in json.loads((ROOT/PARENT/'package.json').read_text())['source_members']}
    files=[]
    for name,replacements in changes.items():
        raw=(ROOT/PARENT/'work'/name).read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest!=expected[PARENT+'work/'+name]:raise ValueError('preimage differs: '+name)
        text=raw.decode()
        for before,after in replacements:
            if text.count(before)!=1:raise ValueError('ambiguous anchor: '+name+' '+before)
            text=text.replace(before,after)
        if name.startswith('src/coder/') and 'gamma_expert_mix::predict(Discretize(' not in text:
            raise ValueError('missing probability hook')
        files.append(dict(source_path=name,source_sha256=digest,source_bytes=len(raw),
            patched_sha256=hashlib.sha256(text.encode()).hexdigest(),patched_bytes=len(text.encode()),
            replacements=[dict(before=a,after=b) for a,b in replacements]))
    added=[]
    for source,target in [('lib/fx2_expert_mix_v1.hpp','src/gamma-expert-mix.h'),
                           ('tools/fx2_coder_trace_v1.hpp','src/coder/gamma-coder-trace.h')]:
        raw=(ROOT/source).read_bytes()
        added.append(dict(source=dict(path=source,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),target=target))
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',files=files,added_files=added,
                scope='Preserve every parent prediction and update. Only the integer count used by the coder changes; no new calls to parent experts.')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    with args.output.open('x') as f:json.dump(build(),f,indent=2);f.write('\n')
