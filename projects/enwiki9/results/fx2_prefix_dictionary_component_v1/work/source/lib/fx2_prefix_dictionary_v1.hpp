#ifndef GAMMA_FX2_PREFIX_DICTIONARY_V1_HPP
#define GAMMA_FX2_PREFIX_DICTIONARY_V1_HPP

#include <cstddef>
#include <cstdint>
#include <vector>

namespace gamma_prefix_dictionary {

// BPD1 uses LF-delimited records: (32 + previous-word prefix length), suffix.
// This inverse targets the fixed LF-only dictionary transform. No discovery,
// word sorting, Unicode normalization, or corpus prediction occurs here.
inline bool decode(const std::vector<uint8_t>& input,
                   std::vector<uint8_t>& output,
                   size_t input_limit = 524288,
                   size_t output_limit = 524288,
                   size_t word_limit = 4096) {
  if (input.size() > input_limit || input.size() < 5 ||
      input[0] != 'B' || input[1] != 'P' || input[2] != 'D' ||
      input[3] != '1' || input[4] > 1) return false;
  std::vector<uint8_t> restored, previous;
  size_t position = 5;
  while (position < input.size()) {
    const unsigned code = input[position++];
    if (code < 32 || code - 32 > previous.size()) return false;
    const size_t prefix = code - 32;
    const size_t begin = position;
    while (position < input.size() && input[position] != '\n') ++position;
    if (position == input.size()) return false;
    const size_t suffix = position - begin;
    if (prefix > word_limit || suffix > word_limit - prefix) return false;
    const size_t length = prefix + suffix;
    const bool newline = position + 1 < input.size() || input[4] == 1;
    if (restored.size() > output_limit ||
        length > output_limit - restored.size() ||
        (newline && length == output_limit - restored.size())) return false;
    previous.resize(prefix);
    previous.insert(previous.end(), input.begin() + begin, input.begin() + position);
    restored.insert(restored.end(), previous.begin(), previous.end());
    if (newline) restored.push_back('\n');
    ++position;
  }
  // Empty dictionaries have no trailing newline; a single empty word has a
  // record containing prefix zero. Reject the noncanonical empty spelling.
  if (input.size() == 5 && input[4] != 0) return false;
  output.swap(restored);
  return true;
}

}  // namespace gamma_prefix_dictionary
#endif
