#ifndef PREDICTOR_H
#define PREDICTOR_H

#include "mixer/sigmoid.h"
#include "mixer/mixer-input.h"
#include "mixer/mixer.h"
#include "mixer/byte-mixer.h"
#include "mixer/sse.h"
#include "models/model.h"
#include "models/byte-model.h"
#include "context-manager.h"
#include "models/direct.h"
#include "models/direct-hash.h"
#include "models/indirect.h"
#include "models/match.h"
#include "models/ppmd.h"
#include "models/bracket.h"
#include "models/fxcmv1.h"
#include "mixer/lstm.h"
#include "contexts/context-hash.h"
#include "contexts/bracket-context.h"
#include "contexts/sparse.h"
#include "contexts/indirect-hash.h"
#include "contexts/interval.h"
#include "contexts/interval-hash.h"
#include "contexts/bit-context.h"
#include "contexts/combined-context.h"

#include "ds/SmallVector.h"
#include "ds/emhash_set.hpp"

#include "../cpp_infer/src/opt/model_opt.h"

#include <vector>
#include <set>
#include <memory>
#include <optional>
#include <string>
#include <cstdint>
#include <cstdio>

// Prints an error message to stderr and exits with a nonzero status.
[[noreturn]] void Fail(const char* fmt, ...);

struct PredictorOptions {
  // Run only the ppmd model. Predict() returns the ppmd's bit prediction and
  // no other model is constructed or updated.
  bool ppmd_only = false;
  // Run only the ppmd and the transformer it feeds (requires
  // transformer_weights). Like ppmd_only, no other model is constructed or
  // updated and Predict() returns the ppmd's bit prediction, but the
  // transformer is still stepped on every byte, so its distributions can be
  // dumped with save_transformer_probs and its loss is printed.
  bool transformer_only = false;
  // If nonempty, every probability distribution the ppmd outputs is appended
  // to this file: for each processed byte, the probabilities of the bytes in
  // the lstm's vocabulary (in vocabulary order), rounded to float16.
  std::string save_ppmd_probs;
  // If nonempty, the ppmd and the transformer are not run. The byte-level
  // probability distributions the transformer would have produced are read
  // from this file instead (same format as save_ppmd_probs). Requires
  // transformer_weights to be set: the loaded distributions replace the
  // transformer's output, so running the lstm instead is an error.
  std::string load_transformer_probs;
  // Number of bytes the predictor will process. Used to validate the size of
  // the load_transformer_probs file.
  unsigned long long num_input_bytes = 0;
  // If nonempty, the lstm is replaced by the pretrained transformer whose
  // weights (FX2TFW01 or FX2TFWC1/2 format) are loaded from this path. The
  // transformer is not trained; it is fed the ppmd's distribution (rounded
  // to float16 exactly as --save-ppmd-probs writes it) and the completed
  // byte, and its output distribution goes to the code downstream of the
  // lstm through the same float16 rounding and zero guard the
  // --save-ppmd-probs / --load-transformer-probs file pipeline applies.
  // Requires the enwik9 vocabulary (205 bytes). The transformer's loss is
  // always printed.
  std::string transformer_weights;
  // Testing option (requires transformer_weights): if nonempty, every
  // distribution passed downstream in place of the lstm's output (the
  // transformer's float16-rounded rows, and the ppmd's float16 rows at the
  // article-start tokens the transformer cannot predict) is appended to
  // this file, in the format of save_ppmd_probs.
  std::string save_transformer_probs;
};

// Buffered writer converting floats to float16 (IEEE half precision).
class HalfFileWriter {
 public:
  explicit HalfFileWriter(const std::string& path);
  ~HalfFileWriter();
  void Write(const float* values, size_t n);
  // Appends values that are already float16.
  void WriteHalves(const uint16_t* values, size_t n);

 private:
  void Flush();
  std::string path_;
  std::vector<uint16_t> buffer_;
  size_t used_ = 0;
  FILE* file_;
};

// Buffered reader converting float16 back to floats. Checks on construction
// that the file holds exactly the expected number of distributions.
class HalfFileReader {
 public:
  HalfFileReader(const std::string& path,
      unsigned long long num_distributions, unsigned int vocab_size);
  ~HalfFileReader();
  void Read(float* values, size_t n);

 private:
  std::string path_;
  std::vector<uint16_t> buffer_;
  size_t pos_ = 0, available_ = 0;
  FILE* file_;
};

class Predictor {
 public:
  Predictor(const std::vector<bool>& vocab,
      const PredictorOptions& options = PredictorOptions());
  float Predict();
  void Perceive(int bit);
  void Pretrain(int bit);

 private:
  unsigned long long GetNumModels();
  void AddMixer(int layer, const unsigned long long& context,
      float learning_rate);
  void AddAuxiliary();
  void AddPPMD();
  void AddBracket();
  void AddWord();
  void AddDirect();
  void AddMatch();
  void AddDoubleIndirect();
  void AddMixers();
  void WritePpmdProbs();
  void LoadTransformerProbs();
  void AccumulateTransformerLoss();
  void TransformerByteUpdate();

  llvm::SmallVector<Indirect<Nonstationary>, 30-7> indirect_ns_models_; // non-stationary
  llvm::SmallVector<Indirect<RunMap>, 1> indirect_r_models_; // run map
  llvm::SmallVector<Direct, 1> direct_models_;
  llvm::SmallVector<Match, 10> match_models_;
  
  std::optional<Bracket> bracket_model_;
  size_t auxiliary_size_ = 2; // 0 -> fxcm, 1 -> byte_mixer
  SSE sse_;
  llvm::SmallVector<MixerInput,2> layers_;
  llvm::SmallVector<Mixer, 23> mixer_0_;
  llvm::SmallVector<Mixer, 1> mixer_1_;
  std::vector<unsigned int> auxiliary_;
  ContextManager manager_;
  Sigmoid sigmoid_;
  std::optional<PPMD::PPMD> byte_model_;
  std::optional<ByteMixer> byte_mixer_;
  std::vector<bool> vocab_;
  std::optional<FXCM> fxcm_model_;
  bool ppmd_only_ = false;
  bool transformer_only_ = false;
  unsigned int vocab_size_ = 0;
  std::vector<int> vocab_bytes_;  // byte values in the vocabulary, ascending
  std::vector<float> probs_scratch_;
  std::unique_ptr<HalfFileWriter> ppmd_probs_writer_;
  std::unique_ptr<HalfFileWriter> transformer_probs_writer_;
  std::unique_ptr<HalfFileReader> transformer_probs_reader_;
  bool print_transformer_loss_ = false;
  unsigned long long num_input_bytes_ = 0;
  double transformer_loss_sum_ = 0;
  unsigned long long transformer_tokens_ = 0;

  // Pretrained transformer replacing the lstm (see
  // PredictorOptions::transformer_weights).
  std::unique_ptr<fx2::opt::TransformerOpt> transformer_;
  int byte_to_index_[256];
  std::vector<uint16_t> half_scratch_;   // float16-rounded distributions
  std::vector<float> transformer_probs_; // the transformer's output row
  // Vocabulary indices of the last 15 processed bytes; an article ends
  // exactly where this window matches the encoded article separator.
  unsigned char separator_window_[15];
  // Tokens of the current article piece processed so far. Articles are cut
  // into pieces of at most kMaxArticleTokens tokens, exactly like the
  // training data loader's split_article_lengths; each piece is a fresh
  // transformer context.
  unsigned long long article_tokens_ = 0;
};

#endif

