// Exact native tensor comparison using the pinned upstream WeightsFile API.
// Compile as C++17, including with -fno-exceptions. No model is opened until
// explicit invocation: fx2_weight_native_compare_v1 REFERENCE TARGET.
// FNV digests are deterministic diagnostics; direct comparisons establish
// equality. Empty models and empty/all-zero payloads are valid and are never
// treated as missing evidence. Upstream loader errors terminate this process.
#include "weights_io.h"

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <string>
#include <vector>

namespace {
constexpr const char* kEnvironment = "GAMMA_FX2_WEIGHT_BOOKKEEPING";
constexpr const char* kSchema = "gamma.fx2-weight-native-compare.v1";
static_assert(sizeof(size_t) <= sizeof(uint64_t), "count serialization requires at most 64-bit size_t");

void NameHex(FILE* stream, const std::string* name) {
  if (!name) { std::fputs("null", stream); return; }
  std::fputc('"', stream);
  for (unsigned char byte : *name) std::fprintf(stream, "%02x", unsigned(byte));
  std::fputc('"', stream);
}

[[noreturn]] void Fail(const char* reason) {
  std::fprintf(stderr, "{\"schema\":\"%s\",\"status\":\"failed\",\"reason\":\"%s\"}\n", kSchema, reason);
  std::fflush(stderr);
  std::exit(1);
}

[[noreturn]] void Divergence(const char* field, size_t index,
                           const std::string* reference_name, const std::string* target_name,
                           uint64_t expected, uint64_t observed,
                           const char* coordinate = nullptr, uint64_t offset = 0) {
  std::fprintf(stderr, "{\"schema\":\"%s\",\"status\":\"diverged\",\"field\":\"%s\","
                       "\"tensor_index\":%zu,\"reference_name_hex\":", kSchema, field, index);
  NameHex(stderr, reference_name);
  std::fputs(",\"target_name_hex\":", stderr);
  NameHex(stderr, target_name);
  std::fprintf(stderr, ",\"reference_value\":%llu,\"target_value\":%llu",
               static_cast<unsigned long long>(expected), static_cast<unsigned long long>(observed));
  if (coordinate) std::fprintf(stderr, ",\"%s\":%llu", coordinate, static_cast<unsigned long long>(offset));
  std::fputs(",\"exact_byte_comparison\":false}\n", stderr);
  std::fflush(stderr);
  std::exit(1);
}

struct Digest {
  uint64_t value = 14695981039346656037ull;
  void Byte(uint8_t byte) { value = (value ^ byte) * 1099511628211ull; }
  void Integer(uint64_t number, unsigned width) {
    for (unsigned k = 0; k < width; ++k) Byte(uint8_t(number >> (8 * k)));
  }
  void Text(const std::string& text) {
    Integer(text.size(), 8);
    for (unsigned char byte : text) Byte(byte);
  }
  explicit Digest(size_t tensor_count) {
    Text("gamma.fx2-native-tensors.v1");
    Integer(tensor_count, 8);
  }
  void Metadata(const std::string& name, const fx2::WTensor& tensor) {
    Text(name);
    Byte(tensor.dtype);
    Integer(tensor.shape.size(), 8);
    for (uint32_t extent : tensor.shape) Integer(extent, 4);
    Integer(tensor.numel, 8);
    Integer(tensor.data.size(), 8);
  }
};

std::vector<std::string> SortedNames(const fx2::WeightsFile& model) {
  std::vector<std::string> names;
  names.reserve(model.tensors.size());
  for (const auto& entry : model.tensors) names.push_back(entry.first);
  std::sort(names.begin(), names.end(), [](const std::string& left, const std::string& right) {
    return std::lexicographical_compare(left.begin(), left.end(), right.begin(), right.end(),
                                       [](unsigned char a, unsigned char b) { return a < b; });
  });
  return names;
}

void Add(uint64_t& total, size_t value) {
  if (uint64_t(value) > std::numeric_limits<uint64_t>::max() - total) Fail("tensor_total_overflow");
  total += value;
}

bool EnvironmentMatches(bool was_set, const std::string& saved) {
  const char* current = std::getenv(kEnvironment);
  return was_set ? current && saved == current : current == nullptr;
}

void RequireParentContainer(const char* path) {
  FILE* file = std::fopen(path, "rb");
  if (!file) Fail("cannot_open_reference_header");
  char magic[8];
  const bool read = std::fread(magic, 1, sizeof(magic), file) == sizeof(magic);
  const bool closed = std::fclose(file) == 0;
  if (!read || !closed) Fail("cannot_read_and_close_reference_header");
  if (std::memcmp(magic, "FX2TFWC2", sizeof(magic)) != 0) Fail("reference_must_use_original_FX2TFWC2_container");
}
}  // namespace

int main(int argc, char** argv) {
  if (argc != 3) {
    std::fputs("usage: fx2_weight_native_compare_v1 REFERENCE TARGET\n", stderr);
    return 2;
  }
  const char* original = std::getenv(kEnvironment);
  const bool was_set = original != nullptr;
  const std::string saved = original ? original : "";
  if (unsetenv(kEnvironment) != 0 || std::getenv(kEnvironment) != nullptr) Fail("cannot_force_reference_P");
  RequireParentContainer(argv[1]);
  const fx2::WeightsFile reference = fx2::WeightsFile::load_compressed(argv[1]);
  const int restore_result = was_set ? setenv(kEnvironment, saved.c_str(), 1) : unsetenv(kEnvironment);
  if (restore_result != 0 || !EnvironmentMatches(was_set, saved)) Fail("cannot_restore_target_environment");
  const fx2::WeightsFile target = fx2::WeightsFile::load_compressed(argv[2]);
  if (!EnvironmentMatches(was_set, saved)) Fail("target_loader_changed_environment");

  const auto reference_names = SortedNames(reference), target_names = SortedNames(target);
  Digest reference_digest(reference_names.size()), target_digest(target_names.size());
  uint64_t payload_bytes = 0, element_count = 0, empty_tensor_count = 0;
  bool all_payload_bytes_zero = true;
  const size_t common = std::min(reference_names.size(), target_names.size());
  for (size_t index = 0; index < common; ++index) {
    const auto& reference_name = reference_names[index];
    const auto& target_name = target_names[index];
    if (reference_name != target_name)
      Divergence("name", index, &reference_name, &target_name, reference_name.size(), target_name.size());
    const auto& left = reference.get(reference_name);
    const auto& right = target.get(target_name);
    if (left.dtype != right.dtype) Divergence("dtype", index, &reference_name, &target_name, left.dtype, right.dtype);
    if (left.shape.size() != right.shape.size())
      Divergence("shape_rank", index, &reference_name, &target_name, left.shape.size(), right.shape.size());
    for (size_t dim = 0; dim < left.shape.size(); ++dim)
      if (left.shape[dim] != right.shape[dim])
        Divergence("shape_extent", index, &reference_name, &target_name, left.shape[dim], right.shape[dim], "dimension", dim);
    if (left.numel != right.numel) Divergence("numel", index, &reference_name, &target_name, left.numel, right.numel);
    if (left.data.size() != right.data.size())
      Divergence("payload_size", index, &reference_name, &target_name, left.data.size(), right.data.size());

    reference_digest.Metadata(reference_name, left);
    target_digest.Metadata(target_name, right);
    // No zero-length memcmp or pointer arithmetic on an empty vector's data().
    // Compare blocks directly, then retain the first differing byte's position.
    constexpr size_t kBlock = 65536;
    for (size_t offset = 0; offset < left.data.size();) {
      const size_t length = std::min(kBlock, left.data.size() - offset);
      if (std::memcmp(left.data.data() + offset, right.data.data() + offset, length) != 0) {
        size_t different = offset;
        while (different < offset + length && left.data[different] == right.data[different]) ++different;
        if (different == offset + length) Fail("memcmp_disagreed_with_exact_byte_scan");
        Divergence("payload_byte", index, &reference_name, &target_name,
                   left.data[different], right.data[different], "tensor_byte_offset", different);
      }
      for (size_t k = offset; k < offset + length; ++k) {
        reference_digest.Byte(left.data[k]);
        target_digest.Byte(right.data[k]);
        if (left.data[k]) all_payload_bytes_zero = false;
      }
      offset += length;
    }
    Add(payload_bytes, left.data.size());
    Add(element_count, left.numel);
    if (left.data.empty()) ++empty_tensor_count;
  }
  if (reference_names.size() != target_names.size())
    Divergence("tensor_presence", common,
               common < reference_names.size() ? &reference_names[common] : nullptr,
               common < target_names.size() ? &target_names[common] : nullptr,
               reference_names.size(), target_names.size());
  // Every name, metadata field and payload byte has already been compared.
  if (reference_digest.value != target_digest.value) Fail("diagnostic_digest_inconsistent_with_exact_comparison");
  std::printf("{\"schema\":\"%s\",\"status\":\"passed\",\"tensor_count\":%zu,"
              "\"payload_bytes\":%llu,\"element_count\":%llu,\"empty_tensor_count\":%llu,"
              "\"empty_model\":%s,\"has_payload_bytes\":%s,\"all_payload_bytes_zero\":%s,"
              "\"exact_byte_comparison\":true,\"reference_forced_P\":true,"
              "\"target_environment_restored_exactly\":true,\"target_environment_was_set\":%s,"
              "\"digest_algorithm\":\"fnv1a64-framed-sorted-native-tensors-v1\","
              "\"reference_digest_hex\":\"%016llx\",\"target_digest_hex\":\"%016llx\","
              "\"objective_credit_bytes\":0}\n",
              kSchema, reference_names.size(), static_cast<unsigned long long>(payload_bytes),
              static_cast<unsigned long long>(element_count), static_cast<unsigned long long>(empty_tensor_count),
              reference_names.empty() ? "true" : "false", payload_bytes ? "true" : "false",
              all_payload_bytes_zero ? "true" : "false", was_set ? "true" : "false",
              static_cast<unsigned long long>(reference_digest.value), static_cast<unsigned long long>(target_digest.value));
  if (std::fflush(stdout) != 0 || std::ferror(stdout)) Fail("comparison_receipt_flush_failed");
  return 0;
}
