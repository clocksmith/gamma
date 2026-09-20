// Native forward boundary: fresh model, declared resets, no recorded intermediates.
#include "cpp_infer/src/opt/model_opt.h"
#include <algorithm>
#include <array>
#include <cstdio>
#include <cstdint>

int main(int argc, char** argv) {
  if (argc != 5) return 2;  // exported weights, token/marker rows, FP16 priors, output
  FILE* rows = std::fopen(argv[2], "rb");
  FILE* priors = std::fopen(argv[3], "rb");
  FILE* output = std::fopen(argv[4], "wbx");
  if (!rows || !priors || !output) return 3;
  fx2::opt::TransformerOpt model(argv[1]);
  std::array<uint16_t, 205> prior{};
  unsigned char pair[2];
  bool reset = true;
  size_t count = 0;
  for (;;) {
    const size_t n = std::fread(pair, 1, 2, rows);
    if (!n) break;
    if (n != 2 || pair[0] >= 205 || pair[1] > 2) return 4;
    if (std::fread(prior.data(), 2, 205, priors) != 205) return 5;
    float values[410] = {};
    if (pair[1] == 2) reset = true;
    else {
      if ((pair[1] == 1) != reset) return 6;
      if (reset) model.begin_article();
      reset = false;
      model.step(pair[0], prior.data(), values + 205);
      std::copy(model.last_logits(), model.last_logits() + 205, values);
    }
    if (std::fwrite(values, sizeof(values), 1, output) != 1) return 7;
    ++count;
  }
  if (!count || std::ferror(rows) || std::ferror(priors) || std::fgetc(priors) != EOF) return 8;
  if (std::fclose(rows) || std::fclose(priors) || std::fclose(output)) return 9;
  return 0;
}
