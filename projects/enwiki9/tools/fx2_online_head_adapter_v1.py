#!/usr/bin/env python3
"""Authenticate one causal projected head update on the fixed FX2 transformer."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PARENT='results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'
def build():
    changes={
      'src/predictor.cpp':[(
        '  memmove(separator_window_, separator_window_ + 1,',
        '  transformer_->observe((uint8_t)token);\n  memmove(separator_window_, separator_window_ + 1,')],
      'cpp_infer/src/opt/model_opt.h':[(
        '  void begin_article(int64_t rope_position_offset = 0);',
        '  void begin_article(int64_t rope_position_offset = 0);\n  // Consume decoded truth before separator/reset logic, including last tokens.\n  void observe(uint8_t token);')],
      'cpp_infer/src/opt/model_opt.cpp':[
        ('#include "model_opt.h"','#include "model_opt.h"\n#include "gamma-online-head.h"\n#include "gamma-online-head-audit.h"'),
        ('struct TransformerOptImpl {','struct TransformerOptImpl {\n  gamma_online_head::Model head{gamma_online_head::configured_arm()};\n  gamma_online_head::Audit audit{head};'),
        ('  void begin(int64_t rope_position_offset) {','  void begin(int64_t rope_position_offset) {\n    head.reset();'),
        ('      head_softcap_softmax(logits, probs208);',
         '      head_softcap_softmax(logits, probs208);\n      audit.base(xn, logits);\n      head.predict(xn, logits, probs208, probs208);'),
        ('TransformerOpt::~TransformerOpt() = default;',
         'TransformerOpt::~TransformerOpt() = default;\n\nvoid TransformerOpt::observe(uint8_t token) {\n  impl->head.observe(token);\n  impl->audit.after_observe();\n}')]
    }
    coder=json.loads((ROOT/'operations/provenance/public_fx2_argmax_native_adapter_v1.json').read_text())
    for row in coder['files']:
        if row['source_path'] in ('src/coder/encoder.cpp','src/coder/decoder.cpp'):
            changes[row['source_path']]=[(r['before'],r['after']) for r in row['replacements']]
    expected={r['path']:r['sha256'].removeprefix('sha256:') for r in json.loads((ROOT/PARENT/'package.json').read_text())['source_members']}
    files=[]
    for name,replacements in changes.items():
        raw=(ROOT/PARENT/'work'/name).read_bytes();h=hashlib.sha256(raw).hexdigest()
        if h!=expected[PARENT+'work/'+name]:raise ValueError('preimage differs:'+name)
        text=raw.decode()
        for before,after in replacements:
            if text.count(before)!=1:raise ValueError('ambiguous anchor:'+name+' '+before)
            text=text.replace(before,after)
        files.append(dict(source_path=name,source_sha256=h,source_bytes=len(raw),patched_sha256=hashlib.sha256(text.encode()).hexdigest(),patched_bytes=len(text.encode()),replacements=[dict(before=a,after=b) for a,b in replacements]))
    added=[]
    for source,target in [
        ('lib/fx2_online_head_v1.hpp','cpp_infer/src/opt/gamma-online-head.h'),
        ('lib/fx2_online_head_audit_v1.hpp','cpp_infer/src/opt/gamma-online-head-audit.h'),
        ('operations/provenance/sources/2026-09-06/sha256-x86-d03795497f3e.c','cpp_infer/src/opt/gamma-observer-sha.c'),
        ('tools/fx2_coder_trace_v1.hpp','src/coder/gamma-coder-trace.h')]:
        raw=(ROOT/source).read_bytes();added.append(dict(source=dict(path=source,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),target=target))
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',files=files,added_files=added,
        scope='Zero-initialized192x205 head learns decoded next-token labels, projects to Frobenius radius4 and resets with original article pieces. Frozen deep features remain unchanged; downstream CMIX probabilities and learning may change. No teacher trace required.')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=build()
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
