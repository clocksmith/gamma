#!/usr/bin/env python3
"""Materialize coder-boundary delivery against immutable native preimages."""
import copy
import hashlib
import json
from pathlib import Path
from fx2_residual_ratio_native_adapter_v1 import PARENT, EXPECTED, replacements

ROOT=Path(__file__).resolve().parents[1]


def build_adapter(parent=PARENT):
    changes=copy.deepcopy(replacements())
    for path,rows in changes.items():
        patched=[]
        for before,after in rows:
            after=after.replace('gamma-residual-ratio.h','fx2_ratio_coder_state_v1.hpp')
            after=after.replace('gamma_ratio::Ratio gamma_ratio_;','gamma_ratio_delivery::State gamma_ratio_;')
            after=after.replace('.configure(vocab_size_, gamma_arm)', '.configure(vocab_size_, gamma_arm, vocab_bytes_)')
            patched.append((before,after))
        changes[path]=patched
    changes['src/predictor.h'].append(('  float Predict();','  float Predict();\n  unsigned GammaFinalProbability(unsigned parent);'))
    changes['src/predictor.cpp'].append(('unsigned long long Predictor::GetNumModels() {',
        '''unsigned Predictor::GammaFinalProbability(unsigned parent) {
  if(!gamma_ratio_enabled_)return parent;
  unsigned output=0;
  if(!gamma_ratio_.final_probability(parent,manager_.bit_context_,output))
    Fail("Gamma delivery prefix or update order differs");
  return output;
}

unsigned long long Predictor::GetNumModels() {'''))
    coder=json.loads((ROOT/'operations/provenance/public_fx2_argmax_native_adapter_v1.json').read_text())
    expected=dict(EXPECTED)
    for row in coder['files']:
        if row['source_path'] not in ('src/coder/encoder.cpp','src/coder/decoder.cpp'):continue
        expected[row['source_path']]=row['source_sha256']
        changes[row['source_path']]=[(x['before'],x['after'].replace(
            'Discretize(gamma_probability);','p_->GammaFinalProbability(Discretize(gamma_probability));'))
            for x in row['replacements']]
    files=[]
    for path,rows in changes.items():
        raw=(parent/path).read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest!=expected[path]:raise ValueError('native preimage differs: '+path)
        text=raw.decode()
        for before,after in rows:
            if text.count(before)!=1:raise ValueError('ambiguous adapter anchor: '+path)
            text=text.replace(before,after)
        files.append(dict(source_path=path,source_sha256=digest,source_bytes=len(raw),
                          patched_sha256=hashlib.sha256(text.encode()).hexdigest(),patched_bytes=len(text.encode()),
                          replacements=[dict(before=a,after=b) for a,b in rows]))
    added=[]
    for name in ('fx2_residual_ratio_v1.hpp','fx2_ratio_coder_delivery_v1.hpp','fx2_ratio_coder_state_v1.hpp'):
        p=ROOT/'lib'/name;raw=p.read_bytes()
        added.append(dict(source=dict(path=str(p.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),target='src/'+name))
    p=ROOT/'tools/fx2_coder_trace_v1.hpp';raw=p.read_bytes()
    added.append(dict(source=dict(path=str(p.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),target='src/coder/gamma-coder-trace.h'))
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',adapter_id='fx2_ratio_coder_native_v1',
                files=files,added_files=added,boundary='Read-only original expert rows; original Predict/Perceive unchanged; correction only after coder discretization. K computes D state and returns parent.',
                scope='Source adapter, not a native archive or qualification result.')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    with a.output.open('x') as f:json.dump(build_adapter(),f,indent=2);f.write('\n')
