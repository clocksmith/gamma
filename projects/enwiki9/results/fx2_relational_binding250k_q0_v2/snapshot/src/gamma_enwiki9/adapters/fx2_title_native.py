"""Authenticated native title-conditioned full-model adapter.

Preserves the original frontend, statistical bank, final mixer and coder.
Metadata mode and 192 gains are counted tensors, never inferred from paths.
Optional captures witness introduced memory only, not complete parent state.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
from .fx2_training_capture import adapt as capture_adapt, source_members

METHODS = '\nvoid Predictor::GammaTitleBegin(FILE* dictionary, const char* header, uint64_t expected_raw) {\n  if (!transformer_ || !transformer_->metadata_mode()) return;\n  if (!dictionary || !header || header[0] != 7 || title_memory_)\n    Fail("Gamma XML requires one dictionary TEXT block");\n  struct stat info;\n  if (fstat(fileno(dictionary), &info) || !S_ISREG(info.st_mode) || info.st_size != 411996)\n    Fail("Gamma XML dictionary size or type differs");\n  std::vector<unsigned char> data(411996);\n  size_t position = 0;\n  while (position < data.size()) {\n    ssize_t n = pread(fileno(dictionary), data.data()+position, data.size()-position, position);\n    if (n < 0 && errno == EINTR) continue;\n    if (n <= 0) Fail("Gamma XML dictionary read failed");\n    position += n;\n  }\n  uint64_t digest = UINT64_C(0xcbf29ce484222325);\n  std::vector<std::string> words;\n  std::string word;\n  size_t word_bytes = 0, longest = 0;\n  for (unsigned char c : data) {\n    digest = (digest ^ c) * UINT64_C(0x100000001b3);\n    if (c >= \'a\' && c <= \'z\') word += c;\n    else if (!word.empty()) {\n      if (word.size() > 58 || words.size() >= 44515) Fail("Gamma XML dictionary bounds differ");\n      word_bytes += word.size(); longest = std::max(longest, word.size());\n      words.push_back(word); word.clear();\n    }\n  }\n  if (digest != UINT64_C(0x2c3946082300051a) || !word.empty() ||\n      words.size() != 44515 || word_bytes != 367481 || longest != 58 || data.back() != \'\\n\')\n    Fail("Gamma XML dictionary identity differs");\n  uint64_t raw_length = 0;\n  for (int i = 1; i < 5; ++i) raw_length = (raw_length << 8) | (unsigned char)header[i];\n  if (expected_raw && raw_length != expected_raw) Fail("Gamma XML requires the complete single TEXT block");\n  title_memory_.reset(new gamma_title_memory::Memory(words, raw_length));\n  const char* prefix = std::getenv("GAMMA_FX2_TITLE_CAPTURE");\n  if (prefix) {\n    const std::string path(prefix);\n    title_features_ = std::fopen((path + ".features").c_str(), "wbx");\n    title_state_ = std::fopen((path + ".state").c_str(), "wbx");\n    title_raw_ = std::fopen((path + ".raw").c_str(), "wbx");\n    if (!title_features_ || !title_state_ || !title_raw_) Fail("title capture create failed");\n  }\n}\n\nvoid Predictor::GammaTitleObserve(uint8_t token) {\n  if (!title_memory_) return;\n  gamma_xml_field::Bytes raw;\n  if (!title_memory_->observe(manager_.bit_context_, token, raw)) Fail("title inverse failed");\n  const auto f = title_memory_->features();\n  transformer_->metadata_counts(f.count, f.aligned.data(), f.wrong.data());\n  if (title_features_) {\n    const auto features = f.bytes();\n    if (std::fwrite(features.data(), 1, features.size(), title_features_) != features.size() ||\n        std::fwrite(raw.data(), 1, raw.size(), title_raw_) != raw.size()) Fail("title capture write failed");\n    const auto state = title_memory_->state();\n    if (state.size() > 1024) Fail("title state bound exceeded");\n    const unsigned char header[2] = {uint8_t(state.size()), uint8_t(state.size() >> 8)};\n    if (std::fwrite(header, 1, 2, title_state_) != 2 ||\n        std::fwrite(state.data(), 1, state.size(), title_state_) != state.size()) Fail("title state write failed");\n  }\n}\n\nvoid Predictor::GammaTitleEnd() {\n  if (!transformer_ || !transformer_->metadata_mode()) return;\n  if (!title_memory_ || !title_memory_->finish()) Fail("title terminal inverse failed");\n  for (FILE* stream : {title_features_, title_state_, title_raw_})\n    if (stream && std::fclose(stream)) Fail("title capture close failed");\n  title_features_ = title_state_ = title_raw_ = nullptr;\n  title_memory_.reset();\n}\n'


def adapt(source_zip: Path, library: Path):
    members, receipts = capture_adapt(source_members(source_zip))
    changes = {
      "src/predictor.h": [
        ('#include "mixer/sigmoid.h"', '#include "predictors/fx2_title_memory_v1.hpp"\n#include "mixer/sigmoid.h"'),
        ('  void Pretrain(int bit);', '  void Pretrain(int bit);\n  void GammaTitleBegin(FILE*, const char*, uint64_t);\n  void GammaTitleEnd();'),
        ('  void TransformerByteUpdate();', '''  void TransformerByteUpdate();
  void GammaTitleObserve(uint8_t);
  std::unique_ptr<gamma_title_memory::Memory> title_memory_;
  FILE* title_features_ = nullptr;
  FILE* title_state_ = nullptr;
  FILE* title_raw_ = nullptr;''')],
      "src/predictor.cpp": [
        ('#include "predictor.h"', '#include "predictor.h"\n#include <sys/stat.h>\n#include <unistd.h>\n#include <cerrno>'),
        ('void Predictor::AddWord() {', METHODS + '\nvoid Predictor::AddWord() {'),
        ('  memmove(separator_window_, separator_window_ + 1,', '  GammaTitleObserve(uint8_t(token));\n  memmove(separator_window_, separator_window_ + 1,')],
      "src/runner.cpp": [
        ('  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);',
         '  p.GammaTitleBegin(dictionary, gamma_static_frontend ? gamma_literal_header : nullptr, *input_bytes);\n  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);\n  p.GammaTitleEnd();'),
        ('  Decompress(*output_bytes, &data_in, &temp_out, &p);',
         '  p.GammaTitleBegin(dictionary, gamma_static_frontend ? gamma_literal_header : nullptr, 0);\n  Decompress(*output_bytes, &data_in, &temp_out, &p);\n  p.GammaTitleEnd();')],
      "cpp_infer/src/opt/arena_build.h": [
        ('  void load(const char* weights_path);', '  int metadata_mode = 0;\n  bool metadata_nonzero = false;\n  float metadata_gain[D] = {};\n  void load(const char* weights_path);')],
      "cpp_infer/src/opt/arena_build.cpp": [
        ('  pool.alloc(size_t(16) << 20);', '''  if (wf.has("gamma.metadata_mode") != wf.has("gamma.metadata_gain"))
    die("incomplete metadata tensors");
  if (wf.has("gamma.metadata_mode")) {
    metadata_mode = wf.get("gamma.metadata_mode", DT_I32, {1}).i32()[0];
    if (metadata_mode != 1 && metadata_mode != 2) die("invalid metadata mode");
    const auto& gain = wf.get("gamma.metadata_gain", DT_F32, {D});
    for (int i = 0; i < D; ++i) {
      metadata_gain[i] = gain.f32()[i];
      if (!std::isfinite(metadata_gain[i])) die("nonfinite metadata gain");
      metadata_nonzero = metadata_nonzero || metadata_gain[i] != 0.0f;
    }
  }
  pool.alloc(size_t(16) << 20);''')],
      "cpp_infer/src/opt/model_opt.h": [
        ('  AttnKind attn_kind() const;', '  AttnKind attn_kind() const;\n  int metadata_mode() const;\n  void metadata_counts(uint8_t, const uint8_t*, const uint8_t*);')],
      "cpp_infer/src/opt/model_opt.cpp": [
        ('  OptModel M;', '  OptModel M;\n  uint8_t title_count = 0, title_hist[V] = {};'),
        ('      embed_combine192(tok, yb, x);  // x0 = tok_row + rms_norm(prior_y)', '''      embed_combine192(tok, yb, x);  // x0 = tok_row + rms_norm(prior_y)
      // A zero gain bypasses all added arithmetic, preserving the parent.
      // Fixed ascending token accumulation; no second embedding table.
      if (M.metadata_nonzero && title_count) {
        for (int d = 0; d < D; ++d) {
          float total = 0.0f;
          for (int v = 0; v < V; ++v)
            total += float(title_hist[v]) * M.tok_table[size_t(v) * D + d];
          const float mean = total / float(title_count);
          x[d] += M.metadata_gain[d] * mean;
        }
      }'''),
        ('AttnKind TransformerOpt::attn_kind() const { return impl->kind; }', '''AttnKind TransformerOpt::attn_kind() const { return impl->kind; }
int TransformerOpt::metadata_mode() const { return impl->M.metadata_mode; }
void TransformerOpt::metadata_counts(uint8_t n, const uint8_t* aligned, const uint8_t* wrong) {
  impl->title_count = n;
  const auto* selected = impl->M.metadata_mode == 2 ? wrong : aligned;
  unsigned total = 0;
  for (int i = 0; i < V; ++i) { impl->title_hist[i] = selected[i]; total += selected[i]; }
  if (n > 128 || total != n) { std::fprintf(stderr, "invalid title histogram\\n"); std::exit(1); }
}''')],
    }
    for name, replacements in changes.items():
        before = members[name]
        text = before.decode()
        for old, new in replacements:
            if text.count(old) != 1:
                raise ValueError("ambiguous title adapter anchor: " + name + ": " + old)
            text = text.replace(old, new)
        members[name] = text.encode()
        receipts.append({"path": name, "preimage_sha256": hashlib.sha256(before).hexdigest(),
                         "postimage_sha256": hashlib.sha256(members[name]).hexdigest()})
    for name in ("predictors/fx2_title_memory_v1.hpp", "fx2_xml_field_observer_v1.hpp"):
        target = "src/" + name
        if target in members:
            raise ValueError("title source already exists")
        members[target] = (library / name).read_bytes()
        receipts.append({"path": target, "postimage_sha256": hashlib.sha256(members[target]).hexdigest()})
    return members, receipts
