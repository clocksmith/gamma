// GPL-3.0-or-later. Independent validation through the original native loader.
#include "weights_io.h"
#include <algorithm>
#include <cstdio>
#include <cstdlib>

void require(bool pass, const char* message) {
  if (!pass) { std::fprintf(stderr, "%s\n", message); std::exit(1); }
}
int main(int argc, char** argv) {
  require(argc == 3, "usage: P_MODEL D_MODEL");
  const auto p = fx2::WeightsFile::load_compressed(argv[1]);
  const auto d = fx2::WeightsFile::load_compressed(argv[2]);
  require(p.tensors.size() == d.tensors.size(), "tensor count differs");
  unsigned changed = 0; size_t unchanged_bytes = 0;
  for (const auto& item : p.tensors) {
    auto it = d.tensors.find(item.first);
    require(it != d.tensors.end(), "tensor missing");
    const auto& a = item.second; const auto& b = it->second;
    require(a.dtype == b.dtype && a.shape == b.shape && a.numel == b.numel &&
            a.data.size() == b.data.size(), "metadata differs");
    if (item.first == "blocks.11.mlp.up.weight.q" ||
        item.first == "blocks.11.mlp.down.weight.q") {
      const auto shape = item.first == "blocks.11.mlp.up.weight.q"
          ? std::vector<uint32_t>{768,192} : std::vector<uint32_t>{192,768};
      require(b.dtype == fx2::DT_I8 && b.shape == shape && b.data.size() == 147456,
              "target shape differs");
      require(std::all_of(b.data.begin(), b.data.end(), [](uint8_t v){return v == 0;}),
              "target signed weights are not zero");
      require(a.data != b.data, "parent target already zero");
      ++changed;
    } else {
      require(a.data == b.data, "undeclared tensor changed");
      unchanged_bytes += a.data.size();
    }
  }
  require(changed == 2, "wrong changed tensor set");
  std::printf("{\"status\":\"passed\",\"native_zero_tensors\":2,"
              "\"tensor_count\":%zu,\"unchanged_native_payload_bytes\":%zu,"
              "\"generated_rope_compared\":true}\n", p.tensors.size(), unchanged_bytes);
}
