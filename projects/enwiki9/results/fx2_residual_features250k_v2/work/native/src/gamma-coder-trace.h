// Gamma diagnostic instrumentation for the pinned public FX2 arithmetic coder.
// Records compare probabilities and coder intervals; they are not codec state
// serialization or a substitute for exact decoded output and archive repeats.
#ifndef GAMMA_FX2_CODER_TRACE_V1_HPP
#define GAMMA_FX2_CODER_TRACE_V1_HPP

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>

namespace gamma_fx2_trace {
inline void Fail(const char* reason) {
  std::fprintf(stderr, "Gamma coder trace: %s\n", reason);
  std::fflush(stderr);
  // A close failure may occur during static destruction, inside exit already.
  std::_Exit(125);
}

class Sink {
 public:
  Sink() {
    const char* path = std::getenv("GAMMA_FX2_CODER_TRACE");
    if (!path || !*path) return;
    // Exclusive creation prevents replacing a previous phase's evidence.
    file_ = std::fopen(path, "wbx");
    if (!file_) Fail("cannot create exclusive output");
  }
  ~Sink() {
    std::FILE* closing = file_;
    file_ = nullptr;
    if (closing && std::fclose(closing) != 0) Fail("output did not close");
  }
  bool Enabled() const { return file_ != nullptr; }
  void Write(const std::uint32_t* words) {
    unsigned char bytes[28];
    for (unsigned i = 0; i < 7; ++i)
      for (unsigned j = 0; j < 4; ++j)
        bytes[4 * i + j] = static_cast<unsigned char>(words[i] >> (8 * j));
    if (std::fwrite(bytes, 1, sizeof(bytes), file_) != sizeof(bytes))
      Fail("output write failed");
  }
 private:
  std::FILE* file_ = nullptr;
};

inline Sink& Output() {
  static Sink sink;
  return sink;
}

class Record {
 public:
  Record(float probability, unsigned quantized, unsigned low, unsigned high)
      : enabled_(Output().Enabled()) {
    static_assert(sizeof(float) == 4 && std::numeric_limits<float>::is_iec559,
                  "trace requires IEEE binary32");
    static_assert(sizeof(unsigned) == 4, "trace requires 32-bit unsigned");
    if (!enabled_) return;
    std::memcpy(words_, &probability, 4);
    words_[1] = quantized;
    words_[2] = low;
    words_[3] = high;
  }
  void Finish(unsigned bit, unsigned low, unsigned high) {
    if (!enabled_) return;
    words_[4] = low;
    words_[5] = high;
    words_[6] = bit;
    Output().Write(words_);
  }
 private:
  bool enabled_;
  std::uint32_t words_[7];
};
}  // namespace gamma_fx2_trace

#endif
