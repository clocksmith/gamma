// Synthetic model inputs only. Compare explicit E and zero-title K containers.
#include "cpp_infer/src/opt/model_opt.h"
#include <array>
#include <cstdio>
#include <cstring>

int main(int argc, char** argv) {
  if (argc != 2 && argc != 3) return 2;
  fx2::opt::TransformerOpt base(argv[1]);
  std::unique_ptr<fx2::opt::TransformerOpt> zero;
  if (argc == 3) zero.reset(new fx2::opt::TransformerOpt(argv[2]));
  if (base.metadata_mode() != 0 || (zero && zero->metadata_mode() != 1)) return 3;
  base.begin_article(); if (zero) zero->begin_article();
  std::array<uint16_t, 205> prior{};
  // Exact binary16 representation of nearest(1/205); same priors in Python.
  prior.fill(0x1cff);
  std::array<uint8_t, 205> aligned{}, wrong{};
  aligned[10] = 3; wrong[20] = 3;
  for (uint8_t token = 0; token < 8; ++token) {
    float p[205], q[205];
    base.step(token, prior.data(), p);
    if (zero) {
      zero->metadata_counts(3, aligned.data(), wrong.data());
      zero->step(token, prior.data(), q);
      if (std::memcmp(p, q, sizeof(p)) || std::memcmp(base.last_logits(), zero->last_logits(), sizeof(p))) return 4;
    }
    if (std::fwrite(base.last_logits(), 1, sizeof(p), stdout) != sizeof(p)) return 5;
  }
  return 0;
}
