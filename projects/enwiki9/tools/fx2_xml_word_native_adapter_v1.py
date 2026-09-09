#!/usr/bin/env python3
"""Compose one native XML-conditioned word context without editing sealed source."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / 'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/work'
TRACE = 'operations/provenance/public_fx2_argmax_native_adapter_v1.json'

METHODS = r'''
void Predictor::GammaXmlBegin(FILE* dictionary, const char* header, uint64_t expected_raw) {
  if (gamma_xml_arm_ == 'P') return;
  if (!dictionary || !header || header[0] != 7 || gamma_xml_active_)
    Fail("Gamma XML requires one dictionary TEXT block");
  struct stat info;
  if (fstat(fileno(dictionary), &info) || !S_ISREG(info.st_mode) || info.st_size != 411996)
    Fail("Gamma XML dictionary size or type differs");
  std::vector<unsigned char> data(411996);
  size_t position = 0;
  while (position < data.size()) {
    ssize_t n = pread(fileno(dictionary), data.data()+position, data.size()-position, position);
    if (n < 0 && errno == EINTR) continue;
    if (n <= 0) Fail("Gamma XML dictionary read failed");
    position += n;
  }
  uint64_t digest = UINT64_C(0xcbf29ce484222325);
  std::vector<std::string> words;
  std::string word;
  size_t word_bytes = 0, longest = 0;
  for (unsigned char c : data) {
    digest = (digest ^ c) * UINT64_C(0x100000001b3);
    if (c >= 'a' && c <= 'z') word += c;
    else if (!word.empty()) {
      if (word.size() > 58 || words.size() >= 44515) Fail("Gamma XML dictionary bounds differ");
      word_bytes += word.size(); longest = std::max(longest, word.size());
      words.push_back(word); word.clear();
    }
  }
  if (digest != UINT64_C(0x2c3946082300051a) || !word.empty() ||
      words.size() != 44515 || word_bytes != 367481 || longest != 58 || data.back() != '\n')
    Fail("Gamma XML dictionary identity differs");
  uint64_t raw_length = 0;
  for (int i = 1; i < 5; ++i) raw_length = (raw_length << 8) | (unsigned char)header[i];
  if (expected_raw && raw_length != expected_raw) Fail("Gamma XML requires the complete single TEXT block");
  if (!gamma_xml_.begin(words, raw_length, gamma_xml_arm_)) Fail("Gamma XML observer initialization failed");
  gamma_xml_active_ = true;
  const char* trace = std::getenv("GAMMA_FX2_XML_TRACE");
  const char* raw = std::getenv("GAMMA_FX2_XML_RAW");
  if (trace) {
    gamma_xml_trace_ = std::fopen(trace, "wbx");
    if (!gamma_xml_trace_) Fail("Gamma XML cannot create state trace");
  }
  if (raw) {
    gamma_xml_raw_ = std::fopen(raw, "wbx");
    if (!gamma_xml_raw_) Fail("Gamma XML cannot create raw witness");
  }
  GammaXmlAudit('I');
  std::fprintf(stderr, "Gamma XML selected=%c\n", gamma_xml_arm_);
}

void Predictor::GammaXmlUpdate(bool byte_update) {
  if (!byte_update || gamma_xml_arm_ == 'P') return;
  // Pretraining uses the original coordinate, with no observer/ring updates.
  gamma_xml_context_ = manager_.words_[0];
  if (!gamma_xml_active_) return;
  gamma_xml_field::Bytes raw;
  uint64_t context = gamma_xml_context_;
  if (!gamma_xml_.observe(manager_.bit_context_, manager_.words_[0], context, raw))
    Fail("Gamma XML causal WRT observation failed");
  gamma_xml_context_ = context;
  if (gamma_xml_raw_ && std::fwrite(raw.data(),1,raw.size(),gamma_xml_raw_) != raw.size())
    Fail("Gamma XML raw witness write failed");
  GammaXmlAudit('B');
}

void Predictor::GammaXmlAudit(unsigned char event) {
  if (!gamma_xml_trace_) return;
  auto state = gamma_xml_.state();
  // The external scalar is a live native reference and separately witnessed.
  for (unsigned shift=0; shift<64; shift+=8) state.push_back(gamma_xml_context_ >> shift);
  const uint32_t n = state.size();
  const unsigned char header[5] = {event,(unsigned char)n,(unsigned char)(n>>8),
                                  (unsigned char)(n>>16),(unsigned char)(n>>24)};
  if (std::fwrite(header,1,5,gamma_xml_trace_) != 5 ||
      std::fwrite(state.data(),1,n,gamma_xml_trace_) != n)
    Fail("Gamma XML state trace write failed");
}

void Predictor::GammaXmlEnd() {
  if (gamma_xml_arm_ == 'P') return;
  if (!gamma_xml_active_ || !gamma_xml_.finish()) Fail("Gamma XML terminal state differs");
  GammaXmlAudit('F');
  if (gamma_xml_trace_ && std::fclose(gamma_xml_trace_)) Fail("Gamma XML state close failed");
  if (gamma_xml_raw_ && std::fclose(gamma_xml_raw_)) Fail("Gamma XML raw close failed");
  gamma_xml_trace_ = gamma_xml_raw_ = nullptr;
  gamma_xml_active_ = false;
}
'''


def build(parent=PARENT):
    changes = {
        'src/predictor.h': [
            ('#include "mixer/sigmoid.h"', '#include "fx2_xml_word_context_v1.hpp"\n#include "mixer/sigmoid.h"'),
            ('  void Pretrain(int bit);', '  void Pretrain(int bit);\n  void GammaXmlBegin(FILE*, const char*, uint64_t);\n  void GammaXmlEnd();'),
            ('  void TransformerByteUpdate();', '''  void TransformerByteUpdate();
  void GammaXmlUpdate(bool);
  void GammaXmlAudit(unsigned char);
  gamma_xml_word::Context gamma_xml_;
  unsigned long long gamma_xml_context_ = 0;
  char gamma_xml_arm_ = 'P';
  bool gamma_xml_active_ = false;
  FILE* gamma_xml_trace_ = nullptr;
  FILE* gamma_xml_raw_ = nullptr;''')],
        'src/predictor.cpp': [
            ('#include "predictor.h"', '#include "predictor.h"\n#include <sys/stat.h>\n#include <unistd.h>\n#include <cerrno>'),
            ('  memset(separator_window_, 0xFF, sizeof(separator_window_));', '''  memset(separator_window_, 0xFF, sizeof(separator_window_));
  const char* gamma_arm = std::getenv("GAMMA_FX2_XML_ARM");
  if (gamma_arm) {
    if (!gamma_arm[0] || gamma_arm[1] ||
        (gamma_arm[0]!='P' && gamma_arm[0]!='K' && gamma_arm[0]!='D' && gamma_arm[0]!='S'))
      Fail("Gamma XML arm must be P, K, D or S");
    gamma_xml_arm_ = gamma_arm[0];
  }
  if (gamma_xml_arm_ != 'P' && (!transformer_ || ppmd_only_ || transformer_only_ ||
      transformer_probs_reader_ || transformer_probs_writer_ || ppmd_probs_writer_))
    Fail("Gamma XML requires native transformer without probability dumping");'''),
            ('void Predictor::AddWord() {', METHODS + '\nvoid Predictor::AddWord() {'),
            ('''    indirect_ns_models_.emplace_back(manager_.nonstationary_, context.GetContext(),
        manager_.bit_context_, delta, manager_.shared_map_);''', '''    const unsigned long long& gamma_context =
        gamma_xml_arm_ != 'P' && params.size() == 1 && params[0] == 0
        ? gamma_xml_context_ : context.GetContext();
    indirect_ns_models_.emplace_back(manager_.nonstationary_, gamma_context,
        manager_.bit_context_, delta, manager_.shared_map_);''')],
        'src/runner.cpp': [
            ('  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);',
             '''  p.GammaXmlBegin(dictionary, gamma_static_frontend ? gamma_literal_header : nullptr, *input_bytes);
  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);
  p.GammaXmlEnd();'''),
            ('  Decompress(*output_bytes, &data_in, &temp_out, &p);',
             '''  p.GammaXmlBegin(dictionary, gamma_static_frontend ? gamma_literal_header : nullptr, 0);
  Decompress(*output_bytes, &data_in, &temp_out, &p);
  p.GammaXmlEnd();''')]
    }
    # Keep two distinct anchored replacements: both paths refresh the scalar
    # before models' ByteUpdate; only the live stream feeds the observer.
    for following in ('    if (print_transformer_loss_) AccumulateTransformerLoss();',
                      '    bracket_model_->ByteUpdate();'):
        before = '  manager_.UpdateContexts(bit);\n  if (byte_update) {\n' + following
        after = '  manager_.UpdateContexts(bit);\n  GammaXmlUpdate(byte_update);\n  if (byte_update) {\n' + following
        changes['src/predictor.cpp'].append((before,after))
    package=json.loads((parent.parent/'package.json').read_text())
    expected={row['path'].removeprefix(str(parent.relative_to(ROOT))+'/'):row['sha256'].removeprefix('sha256:')
              for row in package['source_members']}
    trace=json.loads((ROOT/TRACE).read_text())
    for row in trace['files']:
        if row['source_path'] in ('src/coder/encoder.cpp','src/coder/decoder.cpp'):
            changes[row['source_path']]=[(r['before'],r['after']) for r in row['replacements']]
    files=[]
    for path, replacements in changes.items():
        raw=(parent/path).read_bytes(); digest=hashlib.sha256(raw).hexdigest()
        if digest!=expected[path]: raise ValueError('native preimage differs: '+path)
        text=raw.decode()
        for before,after in replacements:
            if text.count(before)!=1: raise ValueError('ambiguous source anchor: '+path+' '+before[:80])
            text=text.replace(before,after)
        files.append(dict(source_path=path,source_sha256=digest,source_bytes=len(raw),
                          patched_sha256=hashlib.sha256(text.encode()).hexdigest(),patched_bytes=len(text.encode()),
                          replacements=[dict(before=a,after=b) for a,b in replacements]))
    added=[]
    for path,target in [('lib/fx2_xml_field_observer_v1.hpp','src/fx2_xml_field_observer_v1.hpp'),
                        ('lib/fx2_xml_word_context_v1.hpp','src/fx2_xml_word_context_v1.hpp'),
                        ('tools/fx2_coder_trace_v1.hpp','src/coder/gamma-coder-trace.h')]:
        raw=(ROOT/path).read_bytes()
        added.append(dict(source=dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),target=target))
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',adapter_id='fx2_xml_word_native_v1',
                files=files,added_files=added,
                boundary='Only first nonstationary word {0} context changes; P unchanged, K field zero, D current field, S 4096-modeled-byte delayed field. Native model construction and update order preserved.',
                scope='Source adapter; no native archive or qualification result.')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    with args.output.open('x') as stream: json.dump(build(),stream,indent=2);stream.write('\n')
