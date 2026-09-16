// GPL-3.0-or-later. Preparation only; the unchanged native loader reads output.
#include "../lib/fx2_weight_format_v1.hpp"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <iterator>

using namespace fx2_weights_v1;
const std::string up = "blocks.11.mlp.up.weight.q";
const std::string down = "blocks.11.mlp.down.weight.q";

Document zero_final(Document document) {
  validate_document(document);
  unsigned found = 0;
  for (auto& tensor : document.tensors) {
    if (tensor.name != up && tensor.name != down) continue;
    const std::vector<uint32_t> shape = tensor.name == up
        ? std::vector<uint32_t>{768,192} : std::vector<uint32_t>{192,768};
    require(tensor.dtype == 0 && tensor.encoding == 1 && tensor.shape == shape,
            "target tensor is not the declared production matrix");
    std::fill(tensor.payload.begin(), tensor.payload.end(), 7); // native int8 zero
    ++found;
  }
  require(found == 2, "both final MLP matrices are required");
  return document;
}

Bytes read_bytes(const char* path) {
  std::ifstream file(path, std::ios::binary);
  require(bool(file), "input unavailable");
  Bytes result{std::istreambuf_iterator<char>(file), {}};
  require(!file.bad(), "input read failure");
  return result;
}
void write_bytes(const char* path, const Bytes& data) {
  FILE* file = std::fopen(path, "wbx");
  require(file != nullptr, "output exists or cannot be created");
  const bool written = std::fwrite(data.data(), 1, data.size(), file) == data.size();
  const bool closed = std::fclose(file) == 0;
  require(written && closed, "output write failure");
}

void self_test() {
  Document p;
  for (const auto& name : {up, down, std::string("unrelated")}) {
    Tensor t; t.name = name; t.dtype = 0; t.encoding = 1;
    t.shape = name == up ? std::vector<uint32_t>{768,192}
        : name == down ? std::vector<uint32_t>{192,768} : std::vector<uint32_t>{17};
    t.elements = name == "unrelated" ? 17 : 147456;
    t.represented_bytes = t.elements; t.row_width = t.shape.back();
    for (size_t i = 0; i < t.elements; ++i) t.payload.push_back(i % 15);
    p.stored_payload_bytes += t.elements; p.tensors.push_back(t);
  }
  auto d = zero_final(p);
  require(d.tensors[2].payload == p.tensors[2].payload, "unrelated changed");
  for (unsigned i = 0; i < 2; ++i)
    require(std::all_of(d.tensors[i].payload.begin(), d.tensors[i].payload.end(),
                       [](uint8_t v){return v == 7;}), "wrong zero symbol");
  const Bytes encoded = encode(d, Format::Parent);
  require(encode(decode(encoded), Format::Parent) == encoded, "roundtrip differs");
  require(encode(zero_final(p), Format::Parent) == encoded, "repeat differs");
  for (unsigned mode = 0; mode < 4; ++mode) {
    auto bad = p;
    if (mode == 0) bad.tensors[0].name = "missing";
    if (mode == 1) bad.tensors[0].shape = {192,768};
    if (mode == 2) bad.tensors[0].payload[0] = 15;
    if (mode == 3) bad.tensors[0].name = down;
    bool rejected = false;
    try { zero_final(bad); } catch (const std::exception&) { rejected = true; }
    require(rejected, "invalid target accepted");
  }
  bool rejected = false;
  try { decode(Bytes(encoded.begin(), encoded.begin()+8)); }
  catch (const std::exception&) { rejected = true; }
  require(rejected, "truncated stream accepted");
  std::cout << "{\"status\":\"passed\",\"checks\":10,\"corpus_read\":false}\n";
}

int main(int argc, char** argv) {
  try {
    if (argc == 2 && std::string(argv[1]) == "--self-test") { self_test(); return 0; }
    require(argc == 4, "usage: MODEL K_IDENTITY D_ZERO");
    const Bytes original = read_bytes(argv[1]);
    const auto p = decode(original);
    require(p.format == Format::Parent, "original parent format required");
    const Bytes k = encode(p, Format::Parent);
    require(k == original, "canonical parent reencoding differs");
    const auto d = zero_final(p);
    const Bytes child = encode(d, Format::Parent);
    require(encode(decode(child), Format::Parent) == child, "child reencoding differs");
    write_bytes(argv[2], k); write_bytes(argv[3], child);
    std::cout << "{\"status\":\"passed\",\"parent_bytes\":" << k.size()
              << ",\"child_bytes\":" << child.size()
              << ",\"identity_model_exact\":true,\"changed_tensors\":2,"
                 "\"zeroed_weight_count\":294912,\"unchanged_other_tensors\":true}\n";
  } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
