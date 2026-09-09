// Production-entrypoint smoke test; no corpus access or compression claim.
// Linked public FX2 components retain their GPLv3 provenance and LICENSE.
#include "opt/model_opt.h"
#include <array>
#include <cstdint>
#include <cstdio>

int main(int argc, char** argv) {
  if (argc != 3) return 2;
  // The same TransformerOpt constructor used by native CMIX invokes
  // OptModel::load. A direct WeightsFile test cannot substitute for this.
  fx2::opt::TransformerOpt model(argv[1]);
  FILE* out = std::fopen(argv[2], "wbx");
  if (!out) return 3;
  std::array<float, 205> prior{}, probabilities{};
  prior.fill(0.00390625f);
  bool ok = true;
  for (unsigned i = 0; i < 64; ++i) {
    if (i % 32 == 0) model.begin_article(i == 0 ? 0 : 31);
    const uint8_t token = (i * 73 + 19) % 205;
    model.step(token, prior.data(), probabilities.data());
    ok = ok && std::fwrite(probabilities.data(), sizeof(float), 205, out) == 205;
    ok = ok && std::fwrite(model.last_logits(), sizeof(float), 205, out) == 205;
  }
  ok = std::fclose(out) == 0 && ok;
  return ok ? 0 : 4;
}
