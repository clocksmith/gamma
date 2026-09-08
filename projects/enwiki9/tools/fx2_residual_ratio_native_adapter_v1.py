#!/usr/bin/env python3
"""Build a hash-bound adapter for fresh native FX2 materializations only."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/work'
EXPECTED={
    'src/predictor.cpp':'0b79f43644daee942c9cb6da18fa464f0eb0185b6fc7ffc43cde703808fe537e',
    'src/predictor.h':'348d3924fc4e1f4890d0332b0f33ba9591afa6ee06971b9a9bdeaa376b41f458'}

INIT='''
  const char* gamma_setting = std::getenv("GAMMA_FX2_RATIO_ARM");
  const char gamma_arm = gamma_setting ? gamma_setting[0] : 'P';
  if (gamma_setting && (!gamma_setting[0] || gamma_setting[1]))
    Fail("Gamma ratio arm must be P, K, D or S");
  const bool gamma_native = transformer_ && !ppmd_only_ && !transformer_only_ &&
      !transformer_probs_reader_ && !transformer_probs_writer_ && !ppmd_probs_writer_;
  if (gamma_arm != 'P' && !gamma_native)
    Fail("Gamma ratio requires native transformer without probability dumping");
  if (gamma_native) {
    if (!gamma_ratio_.configure(vocab_size_, gamma_arm)) Fail("invalid Gamma ratio configuration");
    gamma_ratio_enabled_ = true;
    const char* trace = std::getenv("GAMMA_FX2_RATIO_TRACE");
    if (trace) {
      gamma_ratio_trace_ = std::fopen(trace, "wbx");
      if (!gamma_ratio_trace_) Fail("cannot create Gamma ratio trace");
      GammaRatioAudit('I');
    }
    std::fprintf(stderr, "Gamma ratio selected=%c\\n", gamma_arm);
  }
'''

METHODS='''
Predictor::~Predictor() {
  if (gamma_ratio_trace_ && std::fclose(gamma_ratio_trace_) != 0)
    Fail("failed closing Gamma ratio trace");
}

void Predictor::GammaRatioAudit(unsigned char event) {
  if (!gamma_ratio_trace_) return;
  const auto state = gamma_ratio_.serialize();
  const uint32_t n = state.size();
  const unsigned char header[5] = {event, (unsigned char)n,
      (unsigned char)(n>>8), (unsigned char)(n>>16), (unsigned char)(n>>24)};
  if (std::fwrite(header,1,5,gamma_ratio_trace_) != 5 ||
      std::fwrite(state.data(),1,n,gamma_ratio_trace_) != n)
    Fail("failed writing Gamma ratio trace");
}

'''


def replacements():
    anchor='  memset(separator_window_, 0xFF, sizeof(separator_window_));'
    return {
        'src/predictor.h':[
            ('#include "mixer/sigmoid.h"','#include "gamma-residual-ratio.h"\n#include "mixer/sigmoid.h"'),
            ('  float Predict();','  ~Predictor();\n  float Predict();'),
            ('  void TransformerByteUpdate();','  void TransformerByteUpdate();\n  void GammaRatioAudit(unsigned char event);\n  gamma_ratio::Ratio gamma_ratio_;\n  bool gamma_ratio_enabled_ = false;\n  FILE* gamma_ratio_trace_ = nullptr;')],
        'src/predictor.cpp':[
            (anchor,anchor+INIT),
            ('unsigned long long Predictor::GetNumModels() {',METHODS+'unsigned long long Predictor::GetNumModels() {'),
            ('void Predictor::TransformerByteUpdate() {','''void Predictor::TransformerByteUpdate() {
  if (gamma_ratio_.pending()) {
    const int token = byte_to_index_[manager_.bit_context_];
    if (token < 0 || !gamma_ratio_.observe((unsigned)token)) Fail("Gamma ratio truth alignment failed");
    GammaRatioAudit('O');
  }'''),
            ('  if (byte_mixer_) byte_mixer_->SetProbs(probs_scratch_.data());','''  if (byte_mixer_) {
    if (gamma_ratio_enabled_) {
      if (!gamma_ratio_.predict(probs_scratch_.data())) Fail("Gamma ratio probability boundary failed");
      GammaRatioAudit('P');
    }
    byte_mixer_->SetProbs(probs_scratch_.data());
  }''')]
    }


def build_adapter(parent=PARENT):
    rows=[]
    for name,changes in replacements().items():
        source=(parent/name).read_bytes()
        digest=hashlib.sha256(source).hexdigest()
        if digest!=EXPECTED[name]:raise ValueError('native preimage changed: '+name)
        text=source.decode()
        for before,after in changes:
            if text.count(before)!=1:raise ValueError('ambiguous adapter anchor')
            text=text.replace(before,after)
        rows.append(dict(source_path=name,source_sha256=digest,source_bytes=len(source),
                         patched_sha256=hashlib.sha256(text.encode()).hexdigest(),patched_bytes=len(text.encode()),
                         replacements=[dict(before=a,after=b) for a,b in changes]))
    header=ROOT/'lib/fx2_residual_ratio_v1.hpp';raw=header.read_bytes()
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',
                adapter_id='fx2_residual_ratio_native_v1',files=rows,
                added_files=[dict(source=dict(path=str(header.relative_to(ROOT)),bytes=len(raw),
                                              sha256=hashlib.sha256(raw).hexdigest()),target='src/gamma-residual-ratio.h')],
                boundary='Preserve original clamped float32 rows for P/K; Q16 multiplicative correction only for D/S.',
                scope='Native source adapter only; no native corpus result or eligibility claim.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();value=build_adapter()
    with args.output.open('x') as output:json.dump(value,output,indent=2);output.write('\n')
    print(args.output)


if __name__=='__main__':main()
