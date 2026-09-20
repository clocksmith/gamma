#include "predictors/fx2_title_memory_v1.hpp"
#include <cassert>
#include <iostream>
#include <numeric>

using gamma_title_memory::Memory;
using gamma_xml_field::Bytes;

struct Tape {
  Bytes stored{7};
  std::string raw;
  void literal(const std::string& value) {
    for (unsigned char c : value) {
      assert(c < 128 && c != 6 && c != 7 && c != 12 && c != 64);
      stored.push_back(gamma_xml_field::unswap(c));
    }
    raw += value;
  }
  void word80() { stored.push_back(208); stored.push_back(128); raw += "cat"; }
};

int main() {
  std::vector<std::string> words(81, "cat");
  Tape tape;
  tape.literal("<title>abc</title><text xml:space=\"preserve\">first</text>");
  const size_t first_end = tape.stored.size();
  tape.literal("<title>xyz</title><text xml:space=\"preserve\">");
  const size_t second_start = tape.stored.size();
  tape.word80();
  tape.literal("</text><title>" + std::string(300, 'a') + "</title><text xml:space=\"preserve\">next</text>");
  tape.literal("<title>" + std::string(300, 'b') + "</title><text xml:space=\"preserve\">");
  const size_t capacity_start = tape.stored.size();
  tape.literal("end</text>");
  Memory memory(words, tape.raw.size()), repeat(words, tape.raw.size());
  Bytes emitted, repeated;
  std::string restored;
  gamma_title_memory::Features previous_features;
  for (size_t i = 0; i < tape.stored.size(); ++i) {
    const uint8_t byte = tape.stored[i];
    const uint8_t token = gamma_title_memory::kTokenMap[byte];
    assert(memory.observe(byte, token, emitted));
    assert(repeat.observe(byte, token, repeated));
    assert(emitted == repeated && memory.state() == repeat.state());
    restored.append(emitted.begin(), emitted.end());
    const auto features = memory.features();
    assert(features.bytes().size() == 411);
    assert(memory.state().size() < 1024);
    assert(std::accumulate(features.aligned.begin(), features.aligned.end(), 0) == features.count);
    assert(std::accumulate(features.wrong.begin(), features.wrong.end(), 0) == features.count);
    if (i + 1 <= first_end) assert(features.count == 0);
    if (i + 1 == second_start) {
      assert(features.count == 3 && features.aligned != features.wrong);
      for (uint8_t c : {'x', 'y', 'z'}) assert(features.aligned[gamma_title_memory::kTokenMap[c]] == 1);
      for (uint8_t c : {'a', 'b', 'c'}) assert(features.wrong[gamma_title_memory::kTokenMap[c]] == 1);
      previous_features = features;
    }
    if (i == second_start) {
      assert(emitted.empty()); // first half of a two-byte WRT code
      assert(features.bytes() == previous_features.bytes());
    }
    if (i + 1 == capacity_start) {
      assert(features.count == 128);
      assert(features.aligned[gamma_title_memory::kTokenMap['b']] == 128);
      assert(features.wrong[gamma_title_memory::kTokenMap['a']] == 128);
    }
  }
  assert(restored == tape.raw);
  assert(memory.finish() && repeat.finish());
  assert(memory.state() == repeat.state());
  Memory mismatch(words, 1);
  assert(!mismatch.observe(7, 204, emitted));
  assert(!mismatch.finish());
  std::cout << "exact inverse; matched causal donors; partial emissions; capacity; repeat; token rejection\n";
}
