#!/usr/bin/env python3
"""Source-bound final-output correction, preserving native model input priors."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/work'
EXPECTED={'src/predictor.h':'348d3924fc4e1f4890d0332b0f33ba9591afa6ee06971b9a9bdeaa376b41f458',
          'src/predictor.cpp':'0b79f43644daee942c9cb6da18fa464f0eb0185b6fc7ffc43cde703808fe537e'}


def build_adapter(parent=PARENT):
    prior='  FloatsToHalves(probs_scratch_.data(), half_scratch_.data(), vocab_size_);\n\n  int token = byte_to_index_'
    end='''  if (transformer_probs_writer_) {
    transformer_probs_writer_->WriteHalves(half_scratch_.data(), vocab_size_);
  }'''
    replacements={
      'src/predictor.h':[
        ('#include "models/fxcmv1.h"','#include "models/fxcmv1.h"\n#include "gamma-half-tail.h"'),
        ('  void TransformerByteUpdate();','  void TransformerByteUpdate();\n  gamma_half_tail::Audit gamma_half_audit_{GAMMA_FXCM_ARM};')],
      'src/predictor.cpp':[
        ('  fxcm_model_.emplace();','  fxcm_model_.emplace();\n  if(fxcm_model_->NumOutputs()!=431)Fail("Gamma original FXCM count differs");\n  std::fprintf(stderr,"Gamma FXCM arm=%c outputs=431\\n","PKD"[GAMMA_FXCM_ARM]);'),
        (prior,'  FloatsToHalves(probs_scratch_.data(), half_scratch_.data(), vocab_size_);\n  if(!gamma_half_audit_.prior(half_scratch_.data(),vocab_size_))Fail("Gamma prior audit order");\n\n  int token = byte_to_index_'),
        (end,'  if(!gamma_half_audit_.output(half_scratch_.data(),probs_scratch_.data(),vocab_size_,!last_of_piece))Fail("Gamma output audit order");\n'+end)]}
    rows=[]
    for name,changes in replacements.items():
        raw=(parent/name).read_bytes();h=hashlib.sha256(raw).hexdigest()
        if h!=EXPECTED[name]:raise ValueError('native preimage differs: '+name)
        text=raw.decode()
        for before,after in changes:
            if text.count(before)!=1:raise ValueError('ambiguous source anchor: '+name)
            text=text.replace(before,after)
        rows.append(dict(source_path=name,source_bytes=len(raw),source_sha256=h,
                         patched_bytes=len(text.encode()),patched_sha256=hashlib.sha256(text.encode()).hexdigest(),
                         replacements=[dict(before=a,after=b) for a,b in changes]))
    header=ROOT/'lib/fx2_half_tail_v1.hpp';raw=header.read_bytes()
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',adapter_id='fx2_half_tail_native_v1',files=rows,
                added_files=[dict(source=dict(path=str(header.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),target='src/gamma-half-tail.h')],
                boundary='Only D doubles scalar positive subnormal outputs at transformer output tail indices200..204 before the original floor. Piece-boundary PPM fallback, input priors, weights and model steps are unchanged.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    value=build_adapter()
    with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
