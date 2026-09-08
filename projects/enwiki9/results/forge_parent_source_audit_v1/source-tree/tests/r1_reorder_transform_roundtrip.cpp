#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

#include "../src/r1_reorder_transform.h"

namespace {

constexpr const char* kDataPath = "/tmp/fx3_payload_lex_roundtrip_stream.bin";
constexpr const char* kSidePath = "/tmp/fx3_payload_lex_roundtrip_side.bin";

std::string Line(const unsigned char* bytes, size_t len) {
  std::string line(reinterpret_cast<const char*>(bytes), len);
  line.push_back('\n');
  return line;
}

bool WriteFile(const std::string& path, const std::string& data) {
  std::ofstream out(path, std::ios::binary | std::ios::trunc);
  if (!out.is_open()) return false;
  out.write(data.data(), static_cast<std::streamsize>(data.size()));
  return out.good();
}

bool ReadFile(const std::string& path, std::string* data) {
  std::ifstream in(path, std::ios::binary);
  if (!in.is_open()) return false;
  in.seekg(0, std::ios::end);
  const std::streamoff size = in.tellg();
  if (size < 0) return false;
  in.seekg(0, std::ios::beg);
  data->assign(static_cast<size_t>(size), '\0');
  if (!data->empty()) in.read(&(*data)[0], size);
  return in.good() || in.gcount() == size;
}

bool CorruptFirstByte(const std::string& path) {
  std::string data;
  if (!ReadFile(path, &data) || data.empty()) return false;
  data[0] ^= 0x7F;
  return WriteFile(path, data);
}

std::string BuildFixture() {
  const unsigned char d99[] = {0xDF, 0x99, 'N'};
  const unsigned char d86_20[] = {0xDF, 0x86, 'N', '2', '0'};
  const unsigned char d86_10[] = {0xDF, 0x86, 'N', '1', '0'};
  const unsigned char d86_30[] = {0xDF, 0x86, 'N', '3', '0'};

  std::string data = "HEAD\n";
  data += "R0\n";
  data += "P\n";
  data += Line(d99, sizeof(d99));
  data += Line(d86_20, sizeof(d86_20));
  data += "c\n";
  data += Line(d99, sizeof(d99));
  data += Line(d86_10, sizeof(d86_10));
  data += "a\n";
  data += Line(d99, sizeof(d99));
  data += Line(d86_30, sizeof(d86_30));
  data += "b\n";
  data += "R2\n";
  return data;
}

}  // namespace

int main() {
  const std::string original = BuildFixture();
  if (original.size() != 49) {
    std::fprintf(stderr, "fixture size mismatch: %zu\n", original.size());
    return 1;
  }
  if (!WriteFile(kDataPath, original)) {
    std::fprintf(stderr, "failed to write fixture\n");
    return 1;
  }
  if (!r1_reorder::ReorderEncodedTailFile(kDataPath, kSidePath)) {
    std::fprintf(stderr, "reorder failed\n");
    return 1;
  }
  std::string reordered;
  if (!ReadFile(kDataPath, &reordered) || reordered == original) {
    std::fprintf(stderr, "reorder did not change stream\n");
    return 1;
  }
  if (!r1_reorder::ExtractSideFromFile(kDataPath, kSidePath)) {
    std::fprintf(stderr, "side extraction failed\n");
    return 1;
  }
  std::string valid_side;
  if (!ReadFile(kSidePath, &valid_side)) {
    std::fprintf(stderr, "side readback failed\n");
    return 1;
  }
  if (!CorruptFirstByte(kSidePath)) {
    std::fprintf(stderr, "side corruption failed\n");
    return 1;
  }
  if (r1_reorder::RestoreEncodedTailFile(kDataPath, kSidePath)) {
    std::fprintf(stderr, "corrupt side unexpectedly restored\n");
    return 1;
  }
  if (!WriteFile(kSidePath, valid_side)) {
    std::fprintf(stderr, "side rewrite failed\n");
    return 1;
  }
  if (!r1_reorder::RestoreEncodedTailFile(kDataPath, kSidePath)) {
    std::fprintf(stderr, "restore failed\n");
    return 1;
  }
  std::string restored;
  if (!ReadFile(kDataPath, &restored) || restored != original) {
    std::fprintf(stderr, "roundtrip mismatch\n");
    return 1;
  }
  std::remove(kDataPath);
  std::remove(kSidePath);
  return 0;
}
