#include "predictor.h"
#include <vector>
#include <stdlib.h>
#include <stdio.h>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <cstdarg>
#ifdef __F16C__
#include <immintrin.h>
#endif

void Fail(const char* fmt, ...) {
  va_list args;
  va_start(args, fmt);
  fprintf(stderr, "\ncmix error: ");
  vfprintf(stderr, fmt, args);
  fprintf(stderr, "\n");
  va_end(args);
  exit(1);
}

namespace {

const size_t kHalfBufferSize = 1 << 22;  // 4M halfs = 8MB per buffer

uint16_t FloatToHalf(float f) {
  uint32_t x;
  memcpy(&x, &f, 4);
  uint32_t sign = (x >> 16) & 0x8000;
  int32_t exp = (int32_t)((x >> 23) & 0xFF) - 112;  // half-biased exponent
  uint32_t mant = x & 0x7FFFFF;
  if (exp >= 31) return sign | 0x7C00;  // overflow, infinity and NaN
  if (exp <= 0) {  // subnormal half (or zero)
    if (exp < -10) return sign;
    mant |= 0x800000;
    int shift = 14 - exp;
    uint16_t h = mant >> shift;
    uint32_t rem = mant & ((1u << shift) - 1), half = 1u << (shift - 1);
    if (rem > half || (rem == half && (h & 1))) ++h;
    return sign | h;
  }
  uint16_t h = sign | (exp << 10) | (mant >> 13);
  uint32_t rem = mant & 0x1FFF;
  if (rem > 0x1000 || (rem == 0x1000 && (h & 1))) ++h;  // round to nearest even
  return h;
}

// Note: subnormal halves (values below 2^-14) decode to HALF their true
// value (the exponent term below would be 113-e in an exact decode). The
// F16C bulk path decodes exactly, so only the last n%8 elements of a
// conversion are affected. This quirk is part of the probability rounding
// contract of --save-ppmd-probs/--load-transformer-probs and of the transformer
// path, which reproduces the file pipeline bit-for-bit; changing it would
// change the coded probabilities.
float HalfToFloat(uint16_t h) {
  uint32_t sign = (uint32_t)(h & 0x8000) << 16;
  uint32_t exp = (h >> 10) & 0x1F;
  uint32_t mant = h & 0x3FF;
  uint32_t x;
  if (exp == 0) {
    if (mant == 0) {
      x = sign;
    } else {  // subnormal half: normalize
      int e = 0;
      while (!(mant & 0x400)) {
        mant <<= 1;
        ++e;
      }
      mant &= 0x3FF;
      x = sign | ((uint32_t)(112 - e) << 23) | (mant << 13);
    }
  } else if (exp == 31) {
    x = sign | 0x7F800000 | (mant << 13);
  } else {
    x = sign | ((exp + 112) << 23) | (mant << 13);
  }
  float f;
  memcpy(&f, &x, 4);
  return f;
}

void FloatsToHalves(const float* src, uint16_t* dst, size_t n) {
  size_t i = 0;
#ifdef __F16C__
  for (; i + 8 <= n; i += 8) {
    _mm_storeu_si128(reinterpret_cast<__m128i*>(dst + i),
        _mm256_cvtps_ph(_mm256_loadu_ps(src + i), _MM_FROUND_TO_NEAREST_INT));
  }
#endif
  for (; i < n; ++i) dst[i] = FloatToHalf(src[i]);
}

void HalvesToFloats(const uint16_t* src, float* dst, size_t n) {
  size_t i = 0;
#ifdef __F16C__
  for (; i + 8 <= n; i += 8) {
    _mm256_storeu_ps(dst + i, _mm256_cvtph_ps(
        _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + i))));
  }
#endif
  for (; i < n; ++i) dst[i] = HalfToFloat(src[i]);
}

// The encoded article separator ("  <page>\n    <title>" after the WRT
// dictionary transform), as vocabulary indices of the enwik9 preprocessed
// stream. Validated against the dictionary encoding by
// SaveArticleBoundaries in runner.cpp; article boundaries correspond
// exactly to the occurrences of this sequence.
const unsigned char kArticleSeparator[15] = {
    0x08, 0x08, 0x25, 0xac, 0x65, 0x27, 0x05,
    0x08, 0x08, 0x08, 0x08, 0x25, 0xac, 0x68, 0x27};

// Articles longer than this are cut into pieces of exactly this many tokens
// (plus a shorter last piece), each a fresh transformer context — the same
// splitting the training data loader applies (split_article_lengths with
// max_article_tokens = 2^17). Must not exceed the transformer's rope table
// (131072 positions).
const unsigned long long kMaxArticleTokens = 1ULL << 17;

}  // namespace

HalfFileWriter::HalfFileWriter(const std::string& path) : path_(path),
    buffer_(kHalfBufferSize) {
  file_ = fopen(path.c_str(), "wb");
  if (!file_) Fail("cannot open %s for writing", path.c_str());
}

HalfFileWriter::~HalfFileWriter() {
  Flush();
  fclose(file_);
}

void HalfFileWriter::Write(const float* values, size_t n) {
  if (used_ + n > buffer_.size()) Flush();
  FloatsToHalves(values, buffer_.data() + used_, n);
  used_ += n;
}

void HalfFileWriter::WriteHalves(const uint16_t* values, size_t n) {
  if (used_ + n > buffer_.size()) Flush();
  memcpy(buffer_.data() + used_, values, n * sizeof(uint16_t));
  used_ += n;
}

void HalfFileWriter::Flush() {
  if (used_ == 0) return;
  if (fwrite(buffer_.data(), sizeof(uint16_t), used_, file_) != used_) {
    Fail("failed writing to %s (disk full?)", path_.c_str());
  }
  used_ = 0;
}

HalfFileReader::HalfFileReader(const std::string& path,
    unsigned long long num_distributions, unsigned int vocab_size)
    : path_(path), buffer_(kHalfBufferSize) {
  file_ = fopen(path.c_str(), "rb");
  if (!file_) Fail("cannot open %s for reading", path.c_str());
  fseeko(file_, 0, SEEK_END);
  unsigned long long size = ftello(file_);
  fseeko(file_, 0, SEEK_SET);
  unsigned long long expected = num_distributions * vocab_size * 2;
  if (size != expected) {
    Fail("--load-transformer-probs: %s has %llu bytes but exactly %llu were "
        "expected (%llu input bytes x %u vocabulary size x 2 bytes per "
        "float16); the file is too %s", path.c_str(), size, expected,
        num_distributions, vocab_size, size < expected ? "short" : "long");
  }
}

HalfFileReader::~HalfFileReader() {
  fclose(file_);
}

void HalfFileReader::Read(float* values, size_t n) {
  if (available_ < n) {
    memmove(buffer_.data(), buffer_.data() + pos_,
        available_ * sizeof(uint16_t));
    pos_ = 0;
    available_ += fread(buffer_.data() + available_, sizeof(uint16_t),
        buffer_.size() - available_, file_);
    if (available_ < n) {
      Fail("unexpected end of file while reading %s", path_.c_str());
    }
  }
  HalvesToFloats(buffer_.data() + pos_, values, n);
  pos_ += n;
  available_ -= n;
}

Predictor::Predictor(const std::vector<bool>& vocab,
    const PredictorOptions& options) : manager_(),
    sigmoid_(100001), vocab_(vocab), ppmd_only_(options.ppmd_only),
    transformer_only_(options.transformer_only),
    num_input_bytes_(options.num_input_bytes) {
  for (int i = 0; i < 256; ++i) {
    if (vocab_[i]) vocab_bytes_.push_back(i);
  }
  vocab_size_ = vocab_bytes_.size();
  // Uniform, so that the loss of the first byte — predicted before the
  // transformer has produced anything — is counted the same way the byte
  // mixer's initial state makes it count outside --transformer-only.
  probs_scratch_.assign(vocab_size_, 1.0f);
  if (options.transformer_only && options.transformer_weights.empty()) {
    Fail("--transformer-only runs the transformer, but no transformer "
        "weights are available");
  }
  if (!options.save_ppmd_probs.empty()) {
    ppmd_probs_writer_.reset(new HalfFileWriter(options.save_ppmd_probs));
  }
  if (!options.load_transformer_probs.empty()) {
    // The loaded distributions stand in for the transformer's output, so the
    // transformer must be the model that would otherwise have run.
    if (options.transformer_weights.empty() && !ppmd_only_) {
      Fail("--load-transformer-probs replaces the transformer's output "
          "distributions, but no transformer is enabled: the lstm would be "
          "run instead");
    }
    transformer_probs_reader_.reset(new HalfFileReader(
        options.load_transformer_probs, options.num_input_bytes, vocab_size_));
    // The loss of the loaded distributions is the transformer's loss.
    print_transformer_loss_ = true;
  }
  if (!options.transformer_weights.empty() && !ppmd_only_ &&
      !transformer_probs_reader_) {
    if (vocab_size_ != 205) {
      Fail("the transformer was trained on the enwik9 vocabulary of 205 "
          "bytes, but this input has a vocabulary of %u bytes", vocab_size_);
    }
    transformer_.reset(new fx2::opt::TransformerOpt(
        options.transformer_weights.c_str(), fx2::opt::AttnKind::KVI8));
    half_scratch_.resize(vocab_size_);
    transformer_probs_.resize(vocab_size_);
    print_transformer_loss_ = true;
    if (!options.save_transformer_probs.empty()) {
      transformer_probs_writer_.reset(
          new HalfFileWriter(options.save_transformer_probs));
    }
  }
  for (int i = 0; i < 256; ++i) byte_to_index_[i] = -1;
  for (unsigned int i = 0; i < vocab_size_; ++i) {
    byte_to_index_[vocab_bytes_[i]] = i;
  }
  // 0xFF is not a vocabulary index, so the window cannot match the
  // separator before 15 real tokens have been seen.
  memset(separator_window_, 0xFF, sizeof(separator_window_));
  if (ppmd_only_ || transformer_only_) {
    AddPPMD();
    return;
  }
  AddBracket();
  // With load_transformer_probs the ppmd is not run: its mixer input is a
  // constant and the transformer's distributions come from the file.
  if (!transformer_probs_reader_) AddPPMD();
  fxcm_model_.emplace();
  AddWord();
  AddMatch();
  AddDoubleIndirect();
  AddMixers();
  auxiliary_size_ = 2;
}

unsigned long long Predictor::GetNumModels() {
  unsigned long long num = 0;

  // models
  num += bracket_model_->NumOutputs(); // bracket
  num += fxcm_model_->NumOutputs();
  num += direct_models_.size();
  num += match_models_.size();
  num += indirect_ns_models_.size();
  num += indirect_r_models_.size();
  num += 1;  // ppmd byte model (a constant input with
             // --load-transformer-probs)
  num += byte_mixer_->NumOutputs();
  return num;
}

void Predictor::AddMixer(int layer, const unsigned long long& context,
    float learning_rate) {
  if (layer == 0) {
    mixer_0_.emplace_back(
        layers_[layer].Inputs(), layers_[layer].ExtraInputs(), context,
      learning_rate, mixer_0_.size());
  } else {
    mixer_1_.emplace_back(
        layers_[layer].Inputs(), layers_[layer].ExtraInputs(), context,
      learning_rate, mixer_1_.size());
  }
}

void Predictor::AddBracket() {
  bracket_model_.emplace(manager_.bit_context_, 200, 10, 100000, vocab_);
  const Context& context = manager_.AddBracketContext(manager_.bit_context_, 256, 15);
  direct_models_.emplace_back(context.GetContext(), manager_.bit_context_, 30, 0,
      context.Size());
  indirect_ns_models_.emplace_back(manager_.nonstationary_, context.GetContext(),
      manager_.bit_context_, 300, manager_.shared_map_);
}

void Predictor::AddPPMD() {
  byte_model_.emplace(25, 14000, manager_.bit_context_, vocab_);
}

void Predictor::AddWord() {
  float delta = 200;
  std::vector<std::vector<unsigned int>> model_params = {
  {0},
   {0, 1}, 
      {1}, 
      {1, 2},
      {1, 3}, 
       {2, 3},
       {3, 4},
      {1, 2, 4},
      {2, 3, 4},
       {2}
      };
  for (const auto& params : model_params) {
    const Context& context = manager_.AddSparseContext(manager_.words_, params);
    indirect_ns_models_.emplace_back(manager_.nonstationary_, context.GetContext(),
        manager_.bit_context_, delta, manager_.shared_map_);
  }

  std::vector<std::vector<unsigned int>> model_params2 = {
  {0}, 
  {1}, 
      {1, 3},
       {1, 2, 3}, 
       {7, 2}};
  for (const auto& params : model_params2) {
    const Context& context = manager_.AddSparseContext(manager_.words_, params);
    match_models_.emplace_back(manager_.history_, context.GetContext(),
        manager_.bit_context_, 200, 0.5, 2000000, &(manager_.longest_match_));
    if (params[0] == 1 && params.size() == 1) {
      indirect_r_models_.emplace_back(manager_.run_map_, context.GetContext(),
          manager_.bit_context_, delta, manager_.shared_map_);
    }
  }
}

void Predictor::AddMatch() {
  float delta = 0.5;
  int limit = 200;
  unsigned long long max_size = 2000000;
  std::vector<std::vector<int>> model_params = {
  {0, 8}, 
  {1, 8}, 
  {7, 4},
      {11, 3}, 
      {13, 2}, 
  };

  for (const auto& params : model_params) {
    const Context& context = manager_.AddContextHashContext(manager_.bit_context_,params[0], params[1]);
    match_models_.emplace_back(manager_.history_, context.GetContext(),
        manager_.bit_context_, limit, delta, std::min(max_size, context.Size()),
        &(manager_.longest_match_));
  }
}

void Predictor::AddDoubleIndirect() {
  float delta = 400;
  indirect_ns_models_.emplace_back(manager_.nonstationary_, manager_.ind1,  manager_.bit_context_, delta, manager_.shared_map_);
  indirect_ns_models_.emplace_back(manager_.nonstationary_, manager_.ind2,  manager_.bit_context_, delta, manager_.shared_map_);
  indirect_ns_models_.emplace_back(manager_.nonstationary_, manager_.ind3,  manager_.bit_context_, delta, manager_.shared_map_);
  indirect_ns_models_.emplace_back(manager_.nonstationary_, manager_.ind5,  manager_.bit_context_, delta, manager_.shared_map_);
}
unsigned int Discretize(float p) {
  return 1 + 4094 * p;
}
void Predictor::AddMixers() {
  unsigned int vocab_size = 0;
  for (unsigned int i = 0; i < vocab_.size(); ++i) {
    if (vocab_[i]) ++vocab_size;
  }
  // With the transformer the lstm is never run: the byte mixer only carries
  // the externally set distribution, so the lstm (and its memory) is not
  // allocated. Nothing after this point draws from rand(), so skipping the
  // lstm's initialization does not shift any other model's random state.
  byte_mixer_.emplace(1, manager_.bit_context_, vocab_,
      vocab_size, transformer_ ? nullptr :
      new Lstm(vocab_size, vocab_size, 200, 1, 128, 0.03, 10));

  for (int i = 0; i < 2; ++i) {
    layers_.emplace_back(sigmoid_,
        1.0e-4);
  }

  unsigned long long input_size = GetNumModels();
  std::cout << "num models " << input_size << "\n";
  layers_[0].SetNumModels(input_size);

  AddMixer(0, manager_.mx9, 0.005); 
  AddMixer(0, manager_.mx10, 0.0005); 
  AddMixer(0, manager_.mx11, 0.005); 
  AddMixer(0, manager_.mx12, 0.0005); 
  AddMixer(0, manager_.mx13, 0.005); 
  AddMixer(0, manager_.mxx, 0.001);
  AddMixer(0, manager_.recent_bytes_[2], 0.002);
  AddMixer(0, manager_.line_break_, 0.0007);
  AddMixer(0, manager_.longest_match_, 0.0005);
  AddMixer(0, manager_.mx19cxt, 0.002);
  AddMixer(0, manager_.auxiliary_context_, 0.0005);
  AddMixer(0, manager_.mx18, 0.001);
  AddMixer(0,manager_.mx7, 0.001);
  AddMixer(0, manager_.wordscxt, 0.005);
  AddMixer(0, manager_.b2streamcxt, 0.001);
  AddMixer(0, manager_.mx5, 0.001);
  AddMixer(0, manager_.mx6, 0.005);
  AddMixer(0, manager_.b3streamcxt, 0.001);
  AddMixer(0, manager_.mx8, 0.001);
  AddMixer(0, manager_.mx17, 0.005);
  AddMixer(0, manager_.mx16, 0.005);
  AddMixer(0, manager_.mx14, 0.005);
  AddMixer(0, manager_.mx15, 0.005);

  input_size = mixer_0_.size() + auxiliary_size_;
  layers_[1].SetNumModels(input_size);

  AddMixer(1,manager_.zero_context_, 0.0003);

  layers_[0].SetExtraInputSize(mixer_0_.size());

}
int lstmpr=0, lstmex=0;
float byte_mixer_output=0.0f;
float Predictor::Predict() {
  if (ppmd_only_ || transformer_only_) {
    float p = byte_model_->Predict()[0];
    // Keep the prediction away from 0 and 1 for the arithmetic coder.
    if (p < 0.001f) p = 0.001f;
    if (p > 0.999f) p = 0.999f;
    return p;
  }
  unsigned int input_index = 0;
  auto bracket_model_output = bracket_model_->Predict()[0];
  layers_[0].SetInput(input_index++, bracket_model_output);

  const auto& fxcm_model_outputs = fxcm_model_->Predict();
  for (unsigned int j = 0; j < fxcm_model_outputs.size(); ++j) {
    layers_[0].SetInput(input_index, fxcm_model_outputs[j]);
    ++input_index;
  }
  auto fxcm_model_index = input_index - 1;
  

  for (unsigned int i = 0; i < direct_models_.size(); ++i) {
    const std::valarray<float>& outputs = direct_models_[i].Predict();
    for (unsigned int j = 0; j < outputs.size(); ++j) {
      layers_[0].SetInput(input_index, outputs[j]);
      ++input_index;
    }
  }

  for (unsigned int i = 0; i < match_models_.size(); ++i) {
    const std::valarray<float>& outputs = match_models_[i].Predict();
    for (unsigned int j = 0; j < outputs.size(); ++j) {
      layers_[0].SetInput(input_index, outputs[j]);
      ++input_index;
    }
  }
 
  for (unsigned int i = 0; i < indirect_ns_models_.size(); ++i) {
    const std::valarray<float>& outputs = indirect_ns_models_[i].Predict();
    for (unsigned int j = 0; j < outputs.size(); ++j) {
      layers_[0].SetInput(input_index, outputs[j]);
      ++input_index;
    }
  }
 
 for (unsigned int i = 0; i < indirect_r_models_.size(); ++i) {
    const std::valarray<float>& outputs = indirect_r_models_[i].Predict();
    for (unsigned int j = 0; j < outputs.size(); ++j) {
      layers_[0].SetInput(input_index, outputs[j]);
      ++input_index;
    }
  }
  layers_[0].SetInput(input_index++,
      byte_model_ ? byte_model_->Predict()[0] : 0.5f);

  float byte_mixer_override = -1;

  if (byte_mixer_output == 0 || byte_mixer_output == 1) byte_mixer_override = byte_mixer_output;
  layers_[0].SetInput(input_index++, byte_mixer_output);
  auto byte_mixer_index = input_index - 1;

  float auxiliary_average = Sigmoid::Logistic(layers_[0].Inputs()[fxcm_model_index]) + Sigmoid::Logistic(layers_[0].Inputs()[byte_mixer_index]);
  auxiliary_average /= auxiliary_size_;
  manager_.auxiliary_context_ =auxiliary_average * 15;

  for (unsigned int i = 0; i < mixer_0_.size(); ++i) {
    float p = mixer_0_[i].Mix();
    layers_[0].SetExtraInput(i, p);
    layers_[1].SetStretchedInput(i, p);
  }
  layers_[1].SetStretchedInput(mixer_0_.size(), layers_[0].Inputs()[fxcm_model_index]);
  layers_[1].SetStretchedInput(mixer_0_.size() + 1, layers_[0].Inputs()[byte_mixer_index]);

  float p = Sigmoid::Logistic(mixer_1_[0].Mix());
  p = sse_.Predict(p);
  if (byte_mixer_override >= 0) {
    return byte_mixer_override;
  }
  return p;
}

void Predictor::WritePpmdProbs() {
  const std::valarray<float>& p = byte_model_->BytePredict();
  for (unsigned int i = 0; i < vocab_size_; ++i) {
    probs_scratch_[i] = p[vocab_bytes_[i]];
  }
  ppmd_probs_writer_->Write(probs_scratch_.data(), vocab_size_);
}

void Predictor::LoadTransformerProbs() {
  transformer_probs_reader_->Read(probs_scratch_.data(), vocab_size_);
  for (unsigned int i = 0; i < vocab_size_; ++i) {
    // Guard against zero (and NaN) probabilities, which would degenerate the
    // bit-level predictions fed to the arithmetic coder. Only probability
    // ratios matter downstream, so no renormalization is needed.
    if (!(probs_scratch_[i] >= 1e-6f)) probs_scratch_[i] = 1e-6f;
  }
  byte_mixer_->SetProbs(probs_scratch_.data());
}

// Replaces the lstm's byte-level update: feeds the completed byte and the
// ppmd's distribution to the pretrained transformer and passes the
// transformer's output distribution (over the next byte) to the byte mixer.
//
// The distributions cross the model boundary exactly as they did in the
// offline pipeline the transformer was trained and evaluated on
// (--save-ppmd-probs -> float16 file -> training / --load-transformer-probs):
// the
// ppmd's prior is rounded to float16 the way WritePpmdProbs writes it, and
// the output row goes through the same float16 rounding and >= 1e-6 guard
// LoadTransformerProbs applies to a file row.
//
// Articles (delimited by kArticleSeparator, and cut at kMaxArticleTokens
// like the training data loader splits them) are independent transformer
// contexts: the KV caches and recurrent states are reset at each piece's
// first token, the piece's last token is never fed (its successor starts a
// fresh context), and at the tokens the transformer therefore cannot
// predict — the first token of each piece — the ppmd's (float16-rounded)
// distribution is passed downstream instead.
void Predictor::TransformerByteUpdate() {
  const std::valarray<float>& p = byte_model_->BytePredict();
  for (unsigned int i = 0; i < vocab_size_; ++i) {
    probs_scratch_[i] = p[vocab_bytes_[i]];
  }
  FloatsToHalves(probs_scratch_.data(), half_scratch_.data(), vocab_size_);

  int token = byte_to_index_[manager_.bit_context_];
  if (token < 0) {
    Fail("transformer: byte 0x%02x is not in the vocabulary",
        manager_.bit_context_);
  }
  memmove(separator_window_, separator_window_ + 1,
      sizeof(separator_window_) - 1);
  separator_window_[sizeof(separator_window_) - 1] = (unsigned char)token;
  ++article_tokens_;

  bool last_of_piece =
      memcmp(separator_window_, kArticleSeparator, sizeof(kArticleSeparator))
          == 0 ||
      article_tokens_ >= kMaxArticleTokens;
  if (last_of_piece) {
    // The next token starts a fresh context; its distribution is the ppmd's.
    HalvesToFloats(half_scratch_.data(), probs_scratch_.data(), vocab_size_);
    article_tokens_ = 0;
  } else {
    if (article_tokens_ == 1) transformer_->begin_article();
    transformer_->step((uint8_t)token, half_scratch_.data(),
        transformer_probs_.data());
    FloatsToHalves(transformer_probs_.data(), half_scratch_.data(),
        vocab_size_);
    HalvesToFloats(half_scratch_.data(), probs_scratch_.data(), vocab_size_);
  }
  if (transformer_probs_writer_) {
    transformer_probs_writer_->WriteHalves(half_scratch_.data(), vocab_size_);
  }
  for (unsigned int i = 0; i < vocab_size_; ++i) {
    if (!(probs_scratch_[i] >= 1e-6f)) probs_scratch_[i] = 1e-6f;
  }
  // With --transformer-only there is no byte mixer: probs_scratch_ is the
  // final destination of the distribution (and what the loss is measured on).
  if (byte_mixer_) byte_mixer_->SetProbs(probs_scratch_.data());
}

// Accumulates -ln p(byte) for the byte that just completed, where p is the
// distribution (normalized over the vocabulary) the byte mixer used to
// predict it: the transformer's output, or the loaded one with
// --load-transformer-probs.
// Must run before that distribution is replaced with the next byte's.
// Prints the running average every million tokens and at the last token.
void Predictor::AccumulateTransformerLoss() {
  double sum = 0, prob = 0;
  if (byte_mixer_) {
    const std::valarray<float>& p = byte_mixer_->BytePredict();
    for (int byte : vocab_bytes_) sum += p[byte];
    prob = p[manager_.bit_context_];
  } else {
    // --transformer-only: the distribution was left in probs_scratch_.
    for (unsigned int i = 0; i < vocab_size_; ++i) sum += probs_scratch_[i];
    int index = byte_to_index_[manager_.bit_context_];
    if (index >= 0) prob = probs_scratch_[index];
  }
  double ratio = sum > 0 ? prob / sum : 0;
  if (!(ratio > 1e-38)) ratio = 1e-38;  // avoid inf from zero probabilities
  transformer_loss_sum_ -= std::log(ratio);
  ++transformer_tokens_;
  if (transformer_tokens_ % 1000000 == 0 ||
      transformer_tokens_ == num_input_bytes_) {
    fprintf(stderr, "\r%*s\r", 70, "");  // clear the progress line
    printf("transformer loss: %.6f nats/token over %llu tokens\n",
        transformer_loss_sum_ / transformer_tokens_, transformer_tokens_);
    fflush(stdout);
  }
}

void Predictor::Perceive(int bit) {
  if (ppmd_only_ || transformer_only_) {
    byte_model_->Perceive(bit);
    // Mirrors how ContextManager::UpdateContexts maintains bit_context_,
    // which the ppmd reads the completed byte from.
    bool byte_update = manager_.bit_context_ >= 128;
    manager_.bit_context_ += manager_.bit_context_ + bit;
    if (byte_update) {
      manager_.bit_context_ -= 256;
      // Before WritePpmdProbs and TransformerByteUpdate overwrite the
      // distribution the completed byte was predicted with.
      if (print_transformer_loss_) AccumulateTransformerLoss();
      byte_model_->ByteUpdate();
      if (ppmd_probs_writer_) WritePpmdProbs();
      if (transformer_) TransformerByteUpdate();
      manager_.bit_context_ = 1;
    }
    return;
  }
  bracket_model_->Perceive(bit);

  for (unsigned int i = 0; i < direct_models_.size(); ++i) {
    direct_models_[i].Perceive(bit);
  }
  for (unsigned int i = 0; i < match_models_.size(); ++i) {
    match_models_[i].Perceive(bit);
  }
  for (unsigned int i = 0; i < indirect_ns_models_.size(); ++i) {
    indirect_ns_models_[i].Perceive(bit);
  }
  for (unsigned int i = 0; i < indirect_r_models_.size(); ++i) {
    indirect_r_models_[i].Perceive(bit);
  }

  if (byte_model_) byte_model_->Perceive(bit);

  byte_mixer_->Perceive(bit);

  for (auto& mixer: mixer_0_) {
    mixer.Perceive(bit);
  }
  for (auto& mixer: mixer_1_) {
    mixer.Perceive(bit);
  }

  sse_.Perceive(bit);

  bool byte_update = false;
  if (manager_.bit_context_ >= 128) byte_update = true;

  manager_.UpdateContexts(bit);
  if (byte_update) {
    if (print_transformer_loss_) AccumulateTransformerLoss();
    bracket_model_->ByteUpdate();

    for (unsigned int i = 0; i < direct_models_.size(); ++i) {
      direct_models_[i].ByteUpdate();
    }
    for (unsigned int i = 0; i < match_models_.size(); ++i) {
      match_models_[i].ByteUpdate();
    }
    for (unsigned int i = 0; i < indirect_ns_models_.size(); ++i) {
      indirect_ns_models_[i].ByteUpdate();
    }

    for (unsigned int i = 0; i < indirect_r_models_.size(); ++i) {
      indirect_r_models_[i].ByteUpdate();
    }

    if (byte_model_) {
      byte_model_->ByteUpdate();
      if (ppmd_probs_writer_) WritePpmdProbs();

      if (transformer_) {
        TransformerByteUpdate();
      } else {
        const std::valarray<float>& p = byte_model_->BytePredict();
        for (unsigned int j = 0; j < 256; ++j) {
          byte_mixer_->SetInput(j,p[j]);
        }

        byte_mixer_->ByteUpdate();
      }
    } else {
      // --load-transformer-probs: the ppmd and the transformer are not run;
      // the byte-level distribution comes from the file instead.
      LoadTransformerProbs();
    }
  }
  byte_mixer_output = byte_mixer_->Predict()[0];
  lstmpr=Discretize(byte_mixer_output);
  lstmex=byte_mixer_->ex;
  fxcm_model_->Perceive(bit);
  if (byte_update)manager_.bit_context_ = 1;
}

void Predictor::Pretrain(int bit) {
  bracket_model_->Predict();
  fxcm_model_->Predict();
    
  for (unsigned int i = 0; i < direct_models_.size(); ++i) {
    direct_models_[i].Predict();
  }
  for (unsigned int i = 0; i < match_models_.size(); ++i) {
    match_models_[i].Predict();
  }
  for (unsigned int i = 0; i < indirect_ns_models_.size(); ++i) {
    indirect_ns_models_[i].Predict();
  }
  for (unsigned int i = 0; i < indirect_r_models_.size(); ++i) {
    indirect_r_models_[i].Predict();
  }


  bracket_model_->Perceive(bit);
  fxcm_model_->Perceive(bit);
    
  for (unsigned int i = 0; i < direct_models_.size(); ++i) {
    direct_models_[i].Perceive(bit);
  }
  for (unsigned int i = 0; i < match_models_.size(); ++i) {
    match_models_[i].Perceive(bit);
  }
  for (unsigned int i = 0; i < indirect_ns_models_.size(); ++i) {
    indirect_ns_models_[i].Perceive(bit);
  }
  for (unsigned int i = 0; i < indirect_r_models_.size(); ++i) {
    indirect_r_models_[i].Perceive(bit);
  }


  bool byte_update = false;
  if (manager_.bit_context_ >= 128) byte_update = true;
  manager_.UpdateContexts(bit);
  if (byte_update) {
    bracket_model_->ByteUpdate();

    for (unsigned int i = 0; i < direct_models_.size(); ++i) {
      direct_models_[i].ByteUpdate();
    }
    for (unsigned int i = 0; i < match_models_.size(); ++i) {
      match_models_[i].ByteUpdate();
    }
    for (unsigned int i = 0; i < indirect_ns_models_.size(); ++i) {
      indirect_ns_models_[i].ByteUpdate();
    }
    for (unsigned int i = 0; i < indirect_r_models_.size(); ++i) {
      indirect_r_models_[i].ByteUpdate();
    }
    manager_.bit_context_ = 1;
  }
}

