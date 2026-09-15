#!/usr/bin/env python3
"""Exact read-only hooks on the released trimmed P source ZIP."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ZIP='results/fx2_expert_release250k_v3/P-source.zip'

def build():
    z=zipfile.ZipFile(ROOT/ZIP)
    changes={
        'cpp_infer/src/opt/model_opt.cpp':[
            ('#include "model_opt.h"','#include "model_opt.h"\n#include "../../../src/gamma-residual-projection.h"'),
            ('      head_softcap_softmax(logits, probs208);','      gamma_residual::capture(xn);\n      head_softcap_softmax(logits, probs208);')],
        'src/predictor.cpp':[
            ('#include "predictor.h"','#include "predictor.h"\n#include "gamma-residual-projection.h"'),
            ('  if (last_of_piece) {','  if (last_of_piece) {\n    gamma_residual::invalidate();')]
    }
    for name in ('encoder','decoder'):
        changes['src/coder/'+name+'.cpp']=[
            ('#include "'+name+'.h"','#include "'+name+'.h"\n#include "../gamma-residual-projection.h"\n#include "../gamma-coder-trace.h"'),
            ('  unsigned int p = Discretize(p_->Predict());',
             '  const float gamma_parent_probability = p_->Predict();\n  const unsigned int p = Discretize(gamma_parent_probability);\n  gamma_residual::Record gamma_features(p);\n  gamma_fx2_trace::Record gamma_coder(gamma_parent_probability,p,x1_,x2_);'),
            ('  p_->Perceive(bit);','  gamma_features.finish(bit);\n  gamma_coder.Finish(bit,x1_,x2_);\n  p_->Perceive(bit);')]
    files=[]
    for path,replacements in changes.items():
        raw=z.read(path);text=raw.decode()
        for a,b in replacements:
            if text.count(a)!=1:raise ValueError('ambiguous hook: '+path)
            text=text.replace(a,b)
        files.append(dict(source_path=path,source_sha256=hashlib.sha256(raw).hexdigest(),
            patched_sha256=hashlib.sha256(text.encode()).hexdigest(),
            replacements=[dict(before=a,after=b) for a,b in replacements]))
    added=[]
    for source,target in [('lib/fx2_residual_projection_v1.hpp','src/gamma-residual-projection.h'),
                          ('tools/fx2_coder_trace_v1.hpp','src/gamma-coder-trace.h')]:
        raw=(ROOT/source).read_bytes()
        added.append(dict(source=dict(path=source,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),target=target))
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',source_zip=ZIP,
        files=files,added_files=added,scope='Read-only ternary hidden features and actual coder counts; unchanged trimmed P probabilities and updates.')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    result=build()
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
