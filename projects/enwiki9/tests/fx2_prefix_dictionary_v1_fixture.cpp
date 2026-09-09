#include "../lib/fx2_prefix_dictionary_v1.hpp"
#include <cassert>
#include <string>

using Bytes = std::vector<uint8_t>;
static Bytes bytes(const std::string& value) {
  return Bytes(value.begin(), value.end());
}
static Bytes frame(uint8_t newline, const std::string& records = "") {
  Bytes result = bytes("BPD1");
  result.push_back(newline);
  result.insert(result.end(), records.begin(), records.end());
  return result;
}
static void exact(const Bytes& encoded, const Bytes& expected) {
  Bytes result{99};
  assert(gamma_prefix_dictionary::decode(encoded, result));
  assert(result == expected);
  Bytes repeat;
  assert(gamma_prefix_dictionary::decode(encoded, repeat));
  assert(result == repeat);
}
static void invalid(const Bytes& encoded, size_t input = 524288,
                    size_t output = 524288, size_t word = 4096) {
  Bytes result{99};
  assert(!gamma_prefix_dictionary::decode(encoded, result, input, output, word));
  assert(result == Bytes{99});
}
int main() {
  exact(frame(0), {});
  exact(frame(1, " oak\n#ford\n pine\n"),
        bytes("oak\noakford\npine\n"));
  exact(frame(0, " a\n!\n"), bytes("a\na"));
  exact(frame(1, " \n"), bytes("\n"));
  // Maximum representable prefix; byte 255 must not be interpreted as signed.
  Bytes wide = frame(1, " " + std::string(223, 'x') + "\n");
  wide.push_back(255); wide.push_back('y'); wide.push_back('\n');
  exact(wide, bytes(std::string(223, 'x') + "\n" + std::string(223, 'x') + "y\n"));
  const Bytes valid = frame(1, " a\n");
  for (size_t size = 0; size < valid.size(); ++size)
    invalid(Bytes(valid.begin(), valid.begin() + size));
  invalid(frame(2));
  invalid(frame(1, "!a\n")); // prefix exceeds empty word
  invalid(frame(1, "\x1f\n"));
  invalid(valid, valid.size() - 1);
  invalid(valid, 524288, 1);
  invalid(valid, 524288, 524288, 0);
  Bytes boundary;
  assert(gamma_prefix_dictionary::decode(valid, boundary, 8, 2, 1));
  assert(boundary == bytes("a\n"));
}
