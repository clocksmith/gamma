// Diagnostic restoration of one predefined INT4 tensor group at a time.
// Reuse the immutable even7 parser, mapping checks and atomic publication.
// Native prediction is unchanged; restored-group effects require fresh archives.
#define main fx2_even7_retained_entry
#include "fx2_weight_even7_probe_v1.cpp"
#undef main
#include <cstring>

namespace {
constexpr const char* arms = "PQKEARUV";

char tensor_group(const Tensor& t) {
  if (t.encoding != 1) return '-';
  if (t.name == "embedding.weight.q" || t.name == "prior_embedding.weight.q" ||
      t.name == "unembedding.weight.q") return 'E';
  require(t.name.rfind("blocks.", 0) == 0, "unclassified INT4 tensor");
  const auto dot = t.name.find('.', 7);
  require(dot != std::string::npos, "missing block number");
  const auto number = t.name.substr(7, dot - 7);
  require(!number.empty() && number.find_first_not_of("0123456789") == std::string::npos,
          "noncanonical block number");
  const int block = std::stoi(number);
  require(block >= 0 && block < 12 && std::to_string(block) == number, "unknown block number");
  const auto field = t.name.substr(dot + 1);
  if (field == "mlp.up.weight.q") return 'U';
  if (field == "mlp.down.weight.q") return 'V';
  const std::array<std::string, 4> common = {
      "attention.query_projection.weight.q", "attention.key_projection.weight.q",
      "attention.value_projection.weight.q", "attention.output_projection.weight.q"};
  const std::array<std::string, 4> gates = {
      "attention.forget_gate_projection.up.weight.q", "attention.forget_gate_projection.down.weight.q",
      "attention.output_gate_projection.up.weight.q", "attention.output_gate_projection.down.weight.q"};
  const bool full_attention = block % 4 == 3;
  const bool common_field = std::find(common.begin(), common.end(), field) != common.end();
  const bool gate_field = std::find(gates.begin(), gates.end(), field) != gates.end();
  require(common_field || (!full_attention && gate_field), "unclassified attention tensor");
  return full_attention ? 'A' : 'R';
}

Document restore_group(const Document& original, const Document& quantized, char arm) {
  require(std::string(arms).find(arm) != std::string::npos, "unknown restoration arm");
  verify_transformation(original, quantized, "D");
  Document result = quantized;
  for (size_t i = 0; i < original.tensors.size(); ++i) {
    const char group = tensor_group(original.tensors[i]);
    if (arm == 'P' || (group != '-' && arm == group))
      result.tensors[i].payload = original.tensors[i].payload;
  }
  validate_document(result);
  return result;
}

void check_restoration(const Document& original, const Document& quantized,
                       const Document& result, char arm) {
  // P comparison checks metadata and every byte against an independently built
  // expected document. It also checks floating-point payloads without arithmetic.
  const auto expected = restore_group(original, quantized, arm);
  verify_transformation(expected, result, "P");
  for (size_t i = 0; i < result.tensors.size(); ++i) {
    const auto group = tensor_group(original.tensors[i]);
    const auto& required = (arm == 'P' || (group != '-' && arm == group))
        ? original.tensors[i].payload : quantized.tensors[i].payload;
    require_identical(result.tensors[i].payload, required, "tensor restoration differs");
  }
}

void restoration_self_test() {
  Document original;
  for (const auto* name : {"embedding.weight.q", "blocks.3.attention.key_projection.weight.q",
                           "blocks.0.attention.forget_gate_projection.up.weight.q",
                           "blocks.0.mlp.up.weight.q", "blocks.0.mlp.down.weight.q"}) {
    Tensor t; t.name = name; t.encoding = 1; t.shape = {15};
    t.elements = t.represented_bytes = t.row_width = 15;
    for (unsigned n = 0; n < 15; ++n) t.payload.push_back(uint8_t(n));
    original.tensors.push_back(t); original.stored_payload_bytes += 15;
  }
  Tensor bits; bits.name = "unaltered.exceptional-bits"; bits.dtype = 1; bits.encoding = 2;
  bits.shape = {6}; bits.elements = bits.row_width = 6; bits.represented_bytes = 12;
  bits.payload = {0, 0, 0, 128, 128, 127, 128, 255, 193, 127, 1, 0};
  original.tensors.push_back(bits); original.stored_payload_bytes += bits.payload.size();
  Document quantized = original; transform(quantized, "D");
  const std::string expected_groups = "EARUV";
  for (size_t i = 0; i < expected_groups.size(); ++i)
    require(tensor_group(original.tensors[i]) == expected_groups[i], "synthetic group assignment differs");
  unsigned comparisons = 0;
  for (char arm : std::string(arms)) {
    const auto result = restore_group(original, quantized, arm);
    const auto bytes = encode(result, Format::Parent);
    const auto inverse = decode(bytes);
    check_restoration(original, quantized, inverse, arm);
    for (size_t i = 0; i < expected_groups.size(); ++i)
      require_identical(inverse.tensors[i].payload,
                        (arm == 'P' || arm == expected_groups[i]) ? original.tensors[i].payload : quantized.tensors[i].payload,
                        "independent synthetic restoration differs");
    require_identical(inverse.tensors.back().payload, bits.payload, "exceptional raw bits differ");
    require_identical(encode(inverse, Format::Parent), bytes, "synthetic repeat differs");
    ++comparisons;
  }
  for (const auto* name : {"blocks.03.mlp.up.weight.q", "blocks.12.mlp.up.weight.q",
                           "blocks.3.attention.forget_gate_projection.up.weight.q", "other.weight.q"}) {
    Tensor bad; bad.encoding = 1; bad.name = name;
    bool rejected = false;
    try { tensor_group(bad); } catch (const std::exception&) { rejected = true; }
    require(rejected, "unknown tensor group was accepted");
  }
  std::cout << "{\"schema\":\"gamma.fx2-group-restoration-self-test.v1\",\"passed\":true,"
               "\"arms\":" << comparisons << ",\"groups\":5,\"signed_values_per_group\":15,"
               "\"exceptional_raw_bit_patterns\":6,\"unknown_group_rejections\":4,"
               "\"model_accessed\":false,\"objective_credit_bytes\":0}\n";
}
}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc == 2 && std::string(argv[1]) == "--self-test") {
      restoration_self_test(); std::cout.flush(); require(bool(std::cout), "stdout failed"); return 0;
    }
    require(argc == 5, "usage: probe P|Q|K|E|A|R|U|V ORIGINAL EVEN7 OUTPUT; or --self-test");
    require(std::strlen(argv[1]) == 1, "invalid arm");
    const char arm = argv[1][0];
    const auto source_bytes = read_file(argv[2]), quantized_bytes = read_file(argv[3]);
    const auto original = decode(source_bytes), quantized = decode(quantized_bytes);
    require(original.format == Format::Parent && quantized.format == Format::Parent,
            "restoration requires original-format containers");
    require_identical(encode(original, Format::Parent), source_bytes, "original is not canonical");
    require_identical(encode(quantized, Format::Parent), quantized_bytes, "quantized is not canonical");
    const auto result = restore_group(original, quantized, arm);
    const auto output = encode(result, Format::Parent);
    const auto inverse = decode(output);
    check_restoration(original, quantized, inverse, arm);
    require_identical(encode(inverse, Format::Parent), output, "canonical repeat differs");
    require_identical(encode(restore_group(decode(source_bytes), decode(quantized_bytes), arm),
                             Format::Parent), output, "fresh restoration repeat differs");
    if (arm == 'P') require_identical(output, source_bytes, "original anchor differs");
    if (arm == 'Q' || arm == 'K') require_identical(output, quantized_bytes, "quantized anchor differs");
    size_t bookkeeping_tensors = 0;
    if (arm == 'K') bookkeeping_tensors = histograms(quantized).local.size();
    size_t restored_tensors = 0, restored_events = 0, restored_changes = 0, remaining_changes = 0;
    for (size_t i = 0; i < original.tensors.size(); ++i) {
      const auto& a = original.tensors[i]; const auto& q = quantized.tensors[i]; const auto& b = result.tensors[i];
      const bool selected = a.encoding == 1 && (arm == 'P' || tensor_group(a) == arm);
      restored_tensors += selected; restored_events += selected ? a.payload.size() : 0;
      for (size_t j = 0; j < a.payload.size(); ++j) {
        restored_changes += b.payload[j] != q.payload[j]; remaining_changes += b.payload[j] != a.payload[j];
      }
    }
    write_new_file(argv[4], output);
    std::cout << "{\"schema\":\"gamma.fx2-group-restoration.v1\",\"arm\":" << quoted(std::string(1, arm))
              << ",\"model_bytes\":" << output.size() << ",\"restored_tensors\":" << restored_tensors
              << ",\"restored_events\":" << restored_events << ",\"restored_changed_events\":" << restored_changes
              << ",\"remaining_changed_events\":" << remaining_changes
              << ",\"bookkeeping_tensors\":" << bookkeeping_tensors
              << ",\"direct_parameter_comparison\":true,\"canonical_repeat\":true,\"fresh_repeat\":true,"
                 "\"non_int4_bits_unchanged\":true,\"probability_identity_measured\":false,\"objective_credit_bytes\":0,"
                 "\"diagnostic_tensor_digest\":" << quoted(document_digest(result)) << "}\n";
    std::cout.flush(); require(bool(std::cout), "stdout failed"); return 0;
  } catch (const std::exception& error) {
    std::cerr << "fx2_weight_restore_group_probe_v1: " << error.what() << '\n'; return 1;
  }
}
