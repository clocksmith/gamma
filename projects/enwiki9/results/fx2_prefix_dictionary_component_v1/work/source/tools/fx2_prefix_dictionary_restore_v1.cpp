// Restore only the authenticated public FX2 dictionary from fixed BPD1 bytes.
// This executable is an explicitly counted experimental package component.
#include "../lib/fx2_prefix_dictionary_v1.hpp"
#include <cstdio>
#include <cstdint>
#include <vector>

int main(int argc, char** argv) {
  if (argc != 3) return 2;
  FILE* input = std::fopen(argv[1], "rb");
  if (!input) return 2;
  std::vector<uint8_t> encoded;
  int byte;
  while ((byte = std::fgetc(input)) != EOF) {
    if (encoded.size() == 524288) {
      std::fclose(input);
      return 3;
    }
    encoded.push_back(static_cast<uint8_t>(byte));
  }
  const bool failed = std::ferror(input);
  std::fclose(input);
  if (failed) return 2;
  std::vector<uint8_t> restored;
  if (!gamma_prefix_dictionary::decode(encoded, restored) ||
      restored.size() != 411996) return 3;
  uint64_t hash = UINT64_C(0xcbf29ce484222325);
  for (uint8_t value : restored)
    hash = (hash ^ value) * UINT64_C(0x100000001b3);
  // Same identity check as the pinned public self_extract.h. The gate also
  // independently checks SHA256; FNV is not a cryptographic authenticity claim.
  if (hash != UINT64_C(0x2c3946082300051a)) return 3;
  FILE* output = std::fopen(argv[2], "wbx");
  if (!output) return 4;
  const bool written = std::fwrite(restored.data(), 1, restored.size(), output)
                       == restored.size();
  const bool closed = std::fclose(output) == 0;
  if (!written || !closed) {
    std::remove(argv[2]);
    return 4;
  }
  return 0;
}
