#!/usr/bin/env python3
"""Read-only source-bound candidate for an interrupted historical match."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ZIP='results/fx2_expert_release250k_v3/P-source.zip'

def build():
    changes={
      'src/models/match.h':[(
        '  const std::vector<unsigned char>& history_;',
        '  unsigned gamma_start_run_=0;\n  bool gamma_missed_=false;\n  const std::vector<unsigned char>& history_;')],
      'src/models/match.cpp':[
        ('#include "match.h"','#include "match.h"\n#include "../gamma-gap-observer.h"'),
        ('void Match::Perceive(int bit) {','void Match::Perceive(int bit) {\n  if(bit_pos_==128) { gamma_start_run_=match_length_; gamma_missed_=false; }\n  if(bit!=((cur_byte_ & bit_pos_)!=0)) gamma_missed_=true;'),
        ('void Match::ByteUpdate() {','void Match::ByteUpdate() {\n  gamma_gap::consider(gamma_start_run_,gamma_missed_,cur_match_,history_pos_,history_);')],
      'src/predictor.cpp':[
        ('#include "predictor.h"','#include "predictor.h"\n#include "gamma-gap-observer.h"'),
        ('    if (print_transformer_loss_) AccumulateTransformerLoss();\n    bracket_model_->ByteUpdate();','    gamma_gap::clear();\n    if (print_transformer_loss_) AccumulateTransformerLoss();\n    bracket_model_->ByteUpdate();')],
      'src/runner.cpp':[
        ('#include "predictor.h"','#include "predictor.h"\n#include "gamma-gap-observer.h"'),
        ('  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);','  gamma_gap::begin();\n  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);\n  gamma_gap::finish();'),
        ('  Decompress(*output_bytes, &data_in, &temp_out, &p);','  gamma_gap::begin();\n  Decompress(*output_bytes, &data_in, &temp_out, &p);\n  gamma_gap::finish();')]
    }
    for name in ('encoder','decoder'):
      changes['src/coder/'+name+'.cpp']=[
        ('#include "'+name+'.h"','#include "'+name+'.h"\n#include "../gamma-gap-observer.h"'),
        ('  unsigned int p = Discretize(p_->Predict());','  unsigned int p = Discretize(p_->Predict());\n  gamma_gap::Record gamma_record(p);'),
        ('  p_->Perceive(bit);','  gamma_record.finish(bit);\n  p_->Perceive(bit);')]
    files=[]
    with zipfile.ZipFile(ROOT/ZIP) as z:
      for path,replacements in changes.items():
        raw=z.read(path);data=raw.decode()
        for a,b in replacements:
          if data.count(a)!=1:raise ValueError('ambiguous hook: '+path+' '+a[:40])
          data=data.replace(a,b,1)
        files.append(dict(source_path=path,source_sha256=hashlib.sha256(raw).hexdigest(),patched_sha256=hashlib.sha256(data.encode()).hexdigest(),replacements=[dict(before=a,after=b) for a,b in replacements]))
    p='lib/fx2_match_gap_observer_v1.hpp';data=(ROOT/p).read_bytes()
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',source_zip=ZIP,files=files,
      added_files=[dict(source=dict(path=p,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()),target='src/gamma-gap-observer.h')],
      scope='No predictions or learning change. Longest pre-byte match with one mismatching byte supplies historical next and shifted continuation for the following byte; before-truth final counts logged.')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=build()
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
