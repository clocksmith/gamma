#!/usr/bin/env python3
"""Bind the fixed transformer profile and compact aligned mixture to source."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARENT='results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'

def build():
    root=ROOT/PARENT/'work'
    old=(root/'src/mixer/byte-mixer.cpp').read_text()
    set_probs=old[old.index('void ByteMixer::SetProbs'):old.index('void ByteMixer::ByteUpdate')]
    new_cpp='#include "byte-mixer.h"\nByteMixer::ByteMixer(const std::vector<bool>& vocab):ByteModel(vocab){}\n'+set_probs
    new_h='''#ifndef BYTE_MIXER_H
#define BYTE_MIXER_H
#include "../models/byte-model.h"
class ByteMixer:public ByteModel {
 public:
  explicit ByteMixer(const std::vector<bool>& vocab);
  void SetProbs(const float* vocab_probs);
};
#endif
'''
    predictor=(root/'src/predictor.cpp').read_text()
    start=predictor.index('  byte_mixer_.emplace(')
    end=predictor.index(';',start)+1
    a=predictor.index('        const std::valarray<float>& p = byte_model_->BytePredict();',predictor.index('void Predictor::Perceive'))
    b=predictor.index('byte_mixer_->ByteUpdate();',a)+len('byte_mixer_->ByteUpdate();')
    fallback=predictor[a:b]
    changes={
      'src/mixer/byte-mixer.cpp':[(old,new_cpp)],
      'src/mixer/byte-mixer.h':[((root/'src/mixer/byte-mixer.h').read_text(),new_h)],
      'src/predictor.cpp':[
        ('#include "predictor.h"','#include "predictor.h"\n#ifdef GAMMA_EXPERT_RELEASE\n#include "gamma-expert-release.h"\n#endif'),
        (predictor[start:end],'  if (!transformer_) Fail("this build requires the native transformer profile");\n  byte_mixer_.emplace(vocab_);'),
        (fallback,'      Fail("LSTM fallback is absent from this fixed transformer profile");'),
        ('  layers_[0].SetInput(input_index++,\n      byte_model_ ? byte_model_->Predict()[0] : 0.5f);',
         '  const float gamma_ppm = byte_model_ ? byte_model_->Predict()[0] : 0.5f;\n  layers_[0].SetInput(input_index++, gamma_ppm);'),
        ('  p = sse_.Predict(p);','  p = sse_.Predict(p);\n#ifdef GAMMA_EXPERT_RELEASE\n  gamma_expert_release::capture(gamma_ppm, byte_mixer_output,\n      fxcm_model_outputs[fxcm_model_outputs.size()-1], byte_mixer_override < 0);\n#endif')]
    }
    for name in ('encoder','decoder'):
        changes['src/coder/'+name+'.cpp']=[
          ('#include "'+name+'.h"','#include "'+name+'.h"\n#ifdef GAMMA_EXPERT_RELEASE\n#include "../gamma-expert-release.h"\n#endif'),
          ('  const unsigned int p = Discretize(p_->Predict());',
           '  unsigned int p = Discretize(p_->Predict());\n#ifdef GAMMA_EXPERT_RELEASE\n  p = gamma_expert_release::predict(p);\n#endif'),
          ('  p_->Perceive(bit);','\n#ifdef GAMMA_EXPERT_RELEASE\n  gamma_expert_release::observe(bit);\n#endif\n  p_->Perceive(bit);')]
    expected={r['path']:r['sha256'].removeprefix('sha256:') for r in json.loads((ROOT/PARENT/'package.json').read_text())['source_members']}
    files=[]
    for name,replacements in changes.items():
        raw=(root/name).read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest!=expected[PARENT+'work/'+name]:raise ValueError('preimage differs:'+name)
        text=raw.decode()
        for before,after in replacements:
            if text.count(before)!=1:raise ValueError('ambiguous anchor:'+name+' '+before)
            text=text.replace(before,after)
        files.append(dict(source_path=name,source_sha256=digest,source_bytes=len(raw),
            patched_sha256=hashlib.sha256(text.encode()).hexdigest(),patched_bytes=len(text.encode()),
            replacements=[dict(before=a,after=b) for a,b in replacements]))
    h='lib/fx2_expert_release_v1.hpp';raw=(ROOT/h).read_bytes()
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',files=files,
        added_files=[dict(source=dict(path=h,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),target='src/gamma-expert-release.h')],
        omitted_source_members=['src/mixer/'+s for s in ('lstm.h','lstm.hpp','lstm-layer.h','lstm-layer.hpp')],
        scope='Fixed native transformer profile. Remove unreachable LSTM fallback. Macro selects the exact compact aligned mixture; no arm selector, delayed features or tracing.')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    result=build()
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
