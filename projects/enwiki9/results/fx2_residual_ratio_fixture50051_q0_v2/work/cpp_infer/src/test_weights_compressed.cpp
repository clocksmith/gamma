// compares WeightsFile::load(reference) against
// WeightsFile::load_compressed(compressed) tensor by tensor, bit for bit.
//
// usage: test_weights_compressed <reference.bin> <compressed>

#include <cstdio>
#include <cstring>

#include "weights_io.h"

int main(int argc, char** argv) {
  if (argc != 3) {
    std::fprintf(stderr, "usage: %s <reference.bin> <compressed>\n", argv[0]);
    return 2;
  }
  fx2::WeightsFile ref = fx2::WeightsFile::load(argv[1]);
  fx2::WeightsFile cmp = fx2::WeightsFile::load_compressed(argv[2]);

  if (ref.tensors.size() != cmp.tensors.size()) {
    std::fprintf(stderr, "FAIL: %zu tensors vs %zu\n", ref.tensors.size(),
                 cmp.tensors.size());
    return 1;
  }
  size_t bytes = 0;
  for (const auto& [name, rt] : ref.tensors) {
    if (!cmp.has(name)) {
      std::fprintf(stderr, "FAIL: missing tensor %s\n", name.c_str());
      return 1;
    }
    const fx2::WTensor& ct = cmp.get(name);
    if (rt.dtype != ct.dtype || rt.shape != ct.shape ||
        rt.data.size() != ct.data.size() ||
        std::memcmp(rt.data.data(), ct.data.data(), rt.data.size()) != 0) {
      std::fprintf(stderr, "FAIL: tensor %s differs\n", name.c_str());
      return 1;
    }
    bytes += rt.data.size();
  }
  std::printf("OK: %zu tensors, %zu payload bytes bit-identical\n",
              ref.tensors.size(), bytes);
  return 0;
}
