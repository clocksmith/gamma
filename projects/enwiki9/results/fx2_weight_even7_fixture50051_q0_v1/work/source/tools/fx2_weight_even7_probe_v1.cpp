// Prospective lossy INT4 weight challenger, not a corpus codec or gain receipt.
// Reuses Gamma's derived GPLv3 tensor primitive. Retain its pinned upstream
// LICENSE and provenance; FX2/CMIX model and predictor authorship stay upstream.
#include "../lib/fx2_weight_format_v1.hpp"

#include <cstdio>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <sstream>

namespace {
using namespace fx2_weights_v1;
constexpr std::array<int, 15> kMapped = {-6, -6, -4, -4, -4, -2, 0, 0, 0, 2, 4, 4, 4, 6, 6};

// Independent integer formula used for verification, not the mutation loop.
constexpr int rounded_even7(int value) {
  const int magnitude = value < 0 ? -value : value;
  int half = magnitude / 2;
  if ((magnitude % 2) && (half % 2)) ++half;
  const int rounded = std::min(6, 2 * half);
  return value < 0 ? -rounded : rounded;
}
constexpr bool mapping_proof() {
  for (int value = -7; value <= 7; ++value) {
    const int mapped = kMapped[size_t(value + 7)];
    if (mapped != rounded_even7(value) || mapped % 2 || mapped < -6 || mapped > 6 ||
        kMapped[size_t(mapped + 7)] != mapped || rounded_even7(-value) != -mapped) return false;
  }
  return true;
}
static_assert(mapping_proof(), "15-value signed ties-to-even/idempotence proof failed");

Bytes read_file(const std::string& path) {
  FILE* file = std::fopen(path.c_str(), "rb");
  require(file != nullptr, "input is missing or cannot be opened");
  Bytes input;
  std::array<uint8_t, 65536> buffer{};
  bool failed = false, oversized = false;
  for (;;) {
    const size_t count = std::fread(buffer.data(), 1, buffer.size(), file);
    if (count > kFileLimit - input.size()) { oversized = true; break; }
    input.insert(input.end(), buffer.begin(), buffer.begin() + count);
    if (count != buffer.size()) { failed = std::ferror(file) != 0; break; }
  }
  const bool closed = std::fclose(file) == 0;
  require(!oversized, "input exceeds 8MiB bound");
  require(!failed && closed, "input read/close failed");
  return input;
}

// Same exclusive partial-file plus no-clobber hard-link publication primitive
// as the sealed marginal probe. Output is published only after all comparisons.
void write_new_file(const std::string& path, const Bytes& bytes) {
  const std::string temporary = path + ".partial";
  FILE* file = std::fopen(temporary.c_str(), "wbx");
  require(file != nullptr, "temporary output exists or cannot be created exclusively");
  const bool written = std::fwrite(bytes.data(), 1, bytes.size(), file) == bytes.size();
  const bool closed = std::fclose(file) == 0;
  std::error_code publication_error, cleanup_error;
  if (written && closed) std::filesystem::create_hard_link(temporary, path, publication_error);
  std::filesystem::remove(temporary, cleanup_error);
  if (cleanup_error) throw std::runtime_error("temporary cleanup failed: " + cleanup_error.message());
  require(written && closed, "output write/close failed");
  if (publication_error) throw std::runtime_error("output publication failed: " + publication_error.message());
}

std::string quoted(const std::string& value) {
  std::string result = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (unsigned char ch : value) {
    if (ch == '\\' || ch == '"') { result.push_back('\\'); result.push_back(char(ch)); }
    else if (ch < 32 || ch >= 127) {
      result += "\\u00"; result.push_back(hex[ch >> 4]); result.push_back(hex[ch & 15]);
    } else result.push_back(char(ch));
  }
  return result + '"';
}

// Diagnostic FNV1a64 uses unsigned wraparound. File/payload hashes consume raw
// event bytes. Document framing uses 8-byte little-endian integers and text
// prefixed by an 8-byte length, in serialized tensor order. Hashes never replace
// direct comparisons; a later runner independently hashes closed files with SHA256.
struct Hash {
  uint64_t value = 14695981039346656037ull;
  void byte(uint8_t b) { value = (value ^ b) * 1099511628211ull; }
  void integer(uint64_t v) { for (unsigned k = 0; k < 8; ++k) byte(uint8_t(v >> (8 * k))); }
  void bytes(const Bytes& data) { for (uint8_t b : data) byte(b); }
  void text(const std::string& data) { integer(data.size()); for (unsigned char b : data) byte(b); }
  std::string hex() const { std::ostringstream out; out << std::hex << std::setw(16) << std::setfill('0') << value; return out.str(); }
};
std::string digest(const Bytes& bytes) { Hash h; h.bytes(bytes); return h.hex(); }
void metadata(Hash& hash, const Tensor& tensor) {
  hash.text(tensor.name); hash.integer(tensor.dtype); hash.integer(tensor.encoding);
  hash.integer(tensor.shape.size());
  for (uint32_t dimension : tensor.shape) hash.integer(dimension);
  hash.integer(tensor.elements); hash.integer(tensor.represented_bytes); hash.integer(tensor.row_width);
  hash.integer(tensor.payload.size());
}
std::string document_digest(const Document& document) {
  Hash hash;
  hash.text("gamma.fx2-even7.tensor-events.v1"); hash.integer(document.tensors.size());
  hash.integer(document.stored_payload_bytes); hash.integer(document.regenerated_rope_bytes);
  for (const auto& tensor : document.tensors) { metadata(hash, tensor); hash.bytes(tensor.payload); }
  return hash.hex();
}

void transform(Document& document, const std::string& mode) {
  require(document.format == Format::Parent, "only original FX2TFWC2 containers are eligible");
  validate_document(document);
  if (mode == "P" || mode == "K") return;
  require(mode == "D" || mode == "C", "unknown transformation mode");
  for (auto& tensor : document.tensors) {
    if (tensor.encoding != 1) continue;
    for (auto& symbol : tensor.payload) symbol = uint8_t(kMapped[symbol] + 7);
    if (mode != "C" || tensor.payload.empty() || tensor.row_width <= 1) continue;
    const size_t width = size_t(tensor.row_width);
    require(tensor.payload.size() % width == 0, "INT4 row boundary is incomplete");
    // Frozen left rotation: C[row,col] = D[row,(col+1) modulo row_width].
    for (size_t base = 0; base < tensor.payload.size(); base += width)
      std::rotate(tensor.payload.begin() + base, tensor.payload.begin() + base + 1,
                  tensor.payload.begin() + base + width);
  }
  validate_document(document);
}

void verify_transformation(const Document& source, const Document& target, const std::string& mode) {
  validate_document(source); validate_document(target);
  require(source.format == target.format && target.format == Format::Parent &&
              source.tensors.size() == target.tensors.size() && source.stored_payload_bytes == target.stored_payload_bytes &&
              source.regenerated_rope_bytes == target.regenerated_rope_bytes, "document metadata changed");
  for (size_t index = 0; index < source.tensors.size(); ++index) {
    const auto& a = source.tensors[index];
    const auto& b = target.tensors[index];
    if (a.name != b.name || a.dtype != b.dtype || a.encoding != b.encoding || a.shape != b.shape ||
        a.elements != b.elements || a.represented_bytes != b.represented_bytes || a.row_width != b.row_width ||
        a.payload.size() != b.payload.size())
      throw std::runtime_error("metadata differs at tensor " + std::to_string(index));
    for (size_t position = 0; position < a.payload.size(); ++position) {
      uint8_t expected = a.payload[position];
      if (a.encoding == 1 && (mode == "D" || mode == "C")) {
        size_t input_position = position;
        if (mode == "C") {
          const size_t width = size_t(a.row_width);
          input_position = position - position % width + (position % width + 1) % width;
        }
        expected = uint8_t(rounded_even7(int(a.payload[input_position]) - 7) + 7);
      }
      if (expected != b.payload[position])
        throw std::runtime_error("payload differs at tensor " + std::to_string(index) + ", event " +
                                 std::to_string(position) + ", expected " + std::to_string(expected) +
                                 ", actual " + std::to_string(b.payload[position]));
    }
  }
}

void print_histogram(const Histogram& counts) {
  std::cout << '[';
  for (size_t k = 0; k < counts.size(); ++k) { if (k) std::cout << ','; std::cout << counts[k]; }
  std::cout << ']';
}

void self_test() {
  Document source;
  auto add = [&](const std::string& name, std::vector<uint32_t> shape, Bytes payload) {
    Tensor tensor;
    tensor.name = name; tensor.dtype = 0; tensor.encoding = 1; tensor.shape = std::move(shape);
    tensor.elements = tensor.represented_bytes = payload.size();
    tensor.row_width = tensor.shape.empty() ? 1 : tensor.shape.back();
    tensor.payload = std::move(payload); source.stored_payload_bytes += tensor.payload.size();
    source.tensors.push_back(std::move(tensor));
  };
  add("all_values", {3, 5}, {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14});
  add("empty_rows", {4, 0}, {}); add("scalar", {}, {14}); add("width_one", {3, 1}, {0, 7, 14});
  for (const std::string mode : {"P", "K", "D", "C"}) {
    Document target = source; transform(target, mode); verify_transformation(source, target, mode);
    if (mode == "C")
      require_identical(target.tensors[0].payload, {1, 3, 3, 3, 1, 7, 7, 7, 9, 5, 11, 11, 13, 13, 11}, "C row fixture differs");
    if (mode == "D") {
      Document repeated = target; transform(repeated, mode);
      for (size_t k = 0; k < target.tensors.size(); ++k)
        require_identical(repeated.tensors[k].payload, target.tensors[k].payload, "D is not idempotent");
    }
  }
  std::cout << "{\"schema\":\"gamma.fx2-even7-self-test.v1\",\"status\":\"passed\",\"mapping_values\":15,\"signed_ties_and_idempotence\":true,\"row_fixture_tensors\":4,\"model_accessed\":false,\"objective_credit_bytes\":0}\n";
}
}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc == 2 && std::string(argv[1]) == "--self-test") {
      self_test(); std::cout.flush(); require(bool(std::cout), "receipt stdout flush failed"); return 0;
    }
    require(argc == 4, "usage: fx2_weight_even7_probe_v1 P|K|D|C INPUT OUTPUT; or --self-test");
    const std::string mode = argv[1];
    require(mode == "P" || mode == "K" || mode == "D" || mode == "C", "unknown mode");
    const Bytes input = read_file(argv[2]);
    const Document original = decode(input);
    require(original.format == Format::Parent, "input must be original FX2TFWC2");
    require_identical(encode(original, Format::Parent), input, "input is not canonical: missing flush, trailing bytes or differing events");
    Histograms bookkeeping;
    if (mode != "P") bookkeeping = histograms(original);
    Document expected = original;
    transform(expected, mode);
    verify_transformation(original, expected, mode);
    const Bytes output = encode(expected, Format::Parent);
    {
      const Document independently_decoded = decode(output);
      verify_transformation(original, independently_decoded, mode);
      verify_transformation(expected, independently_decoded, "P");
      require_identical(encode(independently_decoded, Format::Parent), output, "output canonical repeat differs");
    }
    {
      Document repeat = decode(input);
      transform(repeat, mode);
      verify_transformation(original, repeat, mode);
      require_identical(encode(repeat, Format::Parent), output, "fresh input-decode/transformation repeat differs");
    }
    if (mode == "P" || mode == "K") require_identical(output, input, "P/K must preserve exact parent bytes");
    write_new_file(argv[3], output);
    uint64_t int4_tensors = 0, total_symbols = 0, changed = 0, mapped_changed = 0, shifted_changed = 0;
    for (size_t index = 0; index < original.tensors.size(); ++index) {
      const auto& a = original.tensors[index]; const auto& b = expected.tensors[index];
      if (a.encoding != 1) continue;
      ++int4_tensors;
      total_symbols += a.payload.size();
      for (size_t k = 0; k < a.payload.size(); ++k) {
        changed += a.payload[k] != b.payload[k];
        const uint8_t mapped = uint8_t(rounded_even7(int(a.payload[k]) - 7) + 7);
        mapped_changed += (mode == "D" || mode == "C") && a.payload[k] != mapped;
        shifted_changed += mode == "C" && b.payload[k] != mapped;
      }
    }
    std::cout << "{\"schema\":\"gamma.fx2-weight-even7-probe.v1\",\"mode\":" << quoted(mode)
              << ",\"input_format\":\"FX2TFWC2\",\"output_format\":\"FX2TFWC2\",\"input_bytes\":" << input.size()
              << ",\"output_bytes\":" << output.size() << ",\"parent_stream_regeneration_ok\":true,\"transformed_model_exact\":true,\"canonical_output_repeat_ok\":true,\"fresh_transformation_repeat_ok\":true"
              << ",\"original_model_inversion_claimed\":" << ((mode == "P" || mode == "K") ? "true" : "false")
              << ",\"non_int4_events_and_metadata_unchanged\":true,\"rope_materialized\":false,\"objective_credit_bytes\":0"
              << ",\"hash_algorithm\":\"fnv1a64\",\"digests_are_diagnostic\":true,\"input_file_digest\":" << quoted(digest(input))
              << ",\"output_file_digest\":" << quoted(digest(output))
              << ",\"input_tensor_events_digest\":" << quoted(document_digest(original))
              << ",\"output_tensor_events_digest\":" << quoted(document_digest(expected))
              << ",\"tensor_payload_bytes\":" << original.stored_payload_bytes << ",\"regenerated_rope_bytes\":" << original.regenerated_rope_bytes
              << ",\"tensor_count\":" << original.tensors.size() << ",\"int4_tensor_count\":" << int4_tensors
              << ",\"bookkeeping_int4_tensors\":" << bookkeeping.local.size() << ",\"int4_symbols\":" << total_symbols
              << ",\"changed_symbols_vs_parent\":" << changed << ",\"mapping_changed_symbols\":" << mapped_changed
              << ",\"shift_changed_symbols_vs_D\":" << shifted_changed << ",\"tensor_order\":\"serialized\",\"tensors\":[";
    for (size_t index = 0; index < original.tensors.size(); ++index) {
      if (index) std::cout << ',';
      const auto& a = original.tensors[index]; const auto& b = expected.tensors[index];
      Hash meta; metadata(meta, a);
      uint64_t differences = 0, squared_error = 0; int64_t signed_error = 0;
      for (size_t k = 0; k < a.payload.size(); ++k) {
        differences += a.payload[k] != b.payload[k];
        if (a.encoding == 1) { const int error = int(b.payload[k]) - int(a.payload[k]); signed_error += error; squared_error += uint64_t(error * error); }
      }
      std::cout << "{\"index\":" << index << ",\"name\":" << quoted(a.name) << ",\"dtype\":" << a.dtype
                << ",\"encoding\":" << a.encoding << ",\"elements\":" << a.elements << ",\"represented_bytes\":" << a.represented_bytes
                << ",\"stored_payload_bytes\":" << a.payload.size() << ",\"row_width\":" << a.row_width
                << ",\"changed_payload_events\":" << differences << ",\"signed_integer_weight_error_sum\":" << signed_error
                << ",\"squared_integer_weight_error_sum\":" << squared_error << ",\"metadata_digest\":" << quoted(meta.hex())
                << ",\"input_payload_digest\":" << quoted(digest(a.payload)) << ",\"output_payload_digest\":" << quoted(digest(b.payload)) << ",\"shape\":[";
      for (size_t k = 0; k < a.shape.size(); ++k) { if (k) std::cout << ','; std::cout << a.shape[k]; }
      std::cout << ']';
      if (a.encoding == 1) { std::cout << ",\"input_histogram\":"; print_histogram(histogram(a)); std::cout << ",\"output_histogram\":"; print_histogram(histogram(b)); }
      std::cout << '}';
    }
    std::cout << "]}\n";
    std::cout.flush(); require(bool(std::cout), "receipt stdout flush failed");
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "fx2_weight_even7_probe_v1: " << error.what() << '\n';
    std::cerr.flush();
    return 1;
  }
}
