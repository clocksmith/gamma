#!/usr/bin/env python3
"""Transport the unchanged projected head correction while preserving the parent predictor."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PARENT='results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'
def build():
    changes={
      'src/predictor.cpp':[(
        '#include "predictor.h"',
        '#include "predictor.h"\n#include "gamma-head-transport.h"'),(
        '  memmove(separator_window_, separator_window_ + 1,',
        '  transformer_->observe((uint8_t)token);\n  memmove(separator_window_, separator_window_ + 1,')],
      'cpp_infer/src/opt/model_opt.h':[(
        '  void begin_article(int64_t rope_position_offset = 0);',
        '  const float* adapted_probabilities() const;\n  void begin_article(int64_t rope_position_offset = 0);\n  // Consume decoded truth before separator/reset logic, including last tokens.\n  void observe(uint8_t token);')],
      'cpp_infer/src/opt/model_opt.cpp':[
        ('#include "model_opt.h"','#include "model_opt.h"\n#include "gamma-online-head.h"\n#include "gamma-online-head-audit.h"'),
        ('struct TransformerOptImpl {','struct TransformerOptImpl {\n  gamma_online_head::Model head{gamma_online_head::configured_arm()};\n  gamma_online_head::Audit audit{head};'),
        ('  void begin(int64_t rope_position_offset) {','  void begin(int64_t rope_position_offset) {\n    head.reset();'),
        ('      head_softcap_softmax(logits, probs208);',
         '      head_softcap_softmax(logits, probs208);\n      audit.base(xn, logits);\n      float gamma_shadow[205];\n      head.predict(xn, logits, probs208, gamma_shadow);'),
        ('TransformerOpt::~TransformerOpt() = default;',
         'TransformerOpt::~TransformerOpt() = default;\n\nconst float* TransformerOpt::adapted_probabilities() const { return impl->head.probabilities.data(); }\n\nvoid TransformerOpt::observe(uint8_t token) {\n  impl->head.observe(token);\n  impl->audit.after_observe();\n}')]
    }
    changes['src/predictor.cpp'] += [
      ('  p = sse_.Predict(p);','  p = sse_.Predict(p);\n  gamma_head_transport::capture(byte_mixer_output, byte_mixer_override < 0);'),
      ('  if (byte_mixer_) byte_mixer_->SetProbs(probs_scratch_.data());',
       '  float gamma_adapted[205];\n  uint16_t gamma_halves[205];\n  if (last_of_piece) {\n    std::memcpy(gamma_adapted, probs_scratch_.data(), sizeof(gamma_adapted));\n  } else {\n    FloatsToHalves(transformer_->adapted_probabilities(), gamma_halves, 205);\n    HalvesToFloats(gamma_halves, gamma_adapted, 205);\n  }\n  for (unsigned i=0;i<205;++i) if (!(gamma_adapted[i]>=1e-6f)) gamma_adapted[i]=1e-6f;\n  gamma_head_transport::set(vocab_bytes_, probs_scratch_.data(), gamma_adapted);\n  if (byte_mixer_) byte_mixer_->SetProbs(probs_scratch_.data());')]
    coder=json.loads((ROOT/'operations/provenance/public_fx2_argmax_native_adapter_v1.json').read_text())
    for row in coder['files']:
        if row['source_path'] in ('src/coder/encoder.cpp','src/coder/decoder.cpp'):
            changes[row['source_path']]=[(r['before'],r['after']) for r in row['replacements']]
    for name in ('src/coder/encoder.cpp','src/coder/decoder.cpp'):
        replacements=[]
        for before,after in changes[name]:
            after=after.replace('#include "gamma-coder-trace.h"','#include "gamma-coder-trace.h"\n#include "../gamma-head-transport.h"')
            after=after.replace('const unsigned int p = Discretize(gamma_probability);','const unsigned int p = gamma_head_transport::predict(Discretize(gamma_probability));')
            replacements.append((before,after))
        replacements.append(('  p_->Perceive(bit);','  gamma_head_transport::observe(bit);\n  p_->Perceive(bit);'))
        changes[name]=replacements
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
        ('lib/fx2_head_transport_v2.hpp','src/gamma-head-transport.h'),
        ('lib/fx2_online_head_v1.hpp','cpp_infer/src/opt/gamma-online-head.h'),
        ('lib/fx2_online_head_audit_v1.hpp','cpp_infer/src/opt/gamma-online-head-audit.h'),
        ('operations/provenance/sources/2026-09-06/sha256-x86-d03795497f3e.c','cpp_infer/src/opt/gamma-observer-sha.c'),
        ('tools/fx2_coder_trace_v1.hpp','src/coder/gamma-coder-trace.h')]:
        raw=(ROOT/source).read_bytes();added.append(dict(source=dict(path=source,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),target=target))
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',files=files,added_files=added,
        scope='Same frozen article-local head learner. Parent neural outputs, final raw probabilities and all parent learning remain unchanged. Only coder counts use an optional integer odds transport and two-component posterior; no teacher trace required.')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=build()
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
