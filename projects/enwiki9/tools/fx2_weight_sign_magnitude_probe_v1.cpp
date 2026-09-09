// Container comparison; preserve the included public FX2 GPLv3 notices.
#define main fx2_preserved_marginal_cli_main
#include "fx2_weight_marginal_probe_v1.cpp"
#undef main
#include "../lib/fx2_weight_adaptive_marginal_v1.hpp"
#include "fx2_sign_magnitude_generated.hpp"
namespace {
Bytes trace;
void witness(const SignMagnitudeCounts& counts,uint8_t value) {
  require(trace.size()<=32*1024*1024-49,"count trace exceeds bound");
  const auto state=counts.state();trace.insert(trace.end(),state.begin(),state.end());
  trace.push_back(value);
}
}
int main(int argc,char** argv) {
  try {
    require(argc==4 || argc==5,"usage: probe P|K|D|restore INPUT NEW_OUTPUT [NEW_TRACE]");
    const std::string mode=argv[1];
    require(mode=="P" || mode=="K" || mode=="D" || mode=="restore","invalid mode");
    const Bytes input=read_file(argv[2]);
    Document document;
    if (input.size()>=8 && std::equal(input.begin(),input.begin()+8,kSignMagnitude)) {
      document=decode_sign_magnitude(input,argc==5 ? witness : nullptr);
      require_identical(encode_sign_magnitude(document),input,"noncanonical sign-magnitude input");
    } else if (input.size()>=8 && std::equal(input.begin(),input.begin()+8,kAdaptive)) {
      document=decode_adaptive(input);
      require_identical(encode_adaptive(document),input,"noncanonical adaptive input");
    } else {
      document=decode(input);
      require_identical(encode(document,document.format),input,"noncanonical original input");
    }
    Bytes output;
    if (mode=="restore") output=encode(document,Format::Parent);
    else if (mode=="D") output=encode_sign_magnitude(document,argc==5 ? witness : nullptr);
    else {
      if (mode=="K") for (const auto& tensor:document.tensors) if (tensor.encoding==1) {
        SignMagnitudeCounts counts;for (auto value:tensor.payload) counts.observe(value);
      }
      output=encode_adaptive(document);
    }
    write_new_file(argv[3],output);
    if (argc==5) write_new_file(argv[4],trace);
    std::cout << "{\"mode\":" << quoted(mode) << ",\"archive_bytes\":" << output.size()
              << ",\"state_trace_bytes\":" << trace.size() << ",\"objective_credit_bytes\":0}\n";
  } catch (const std::exception& e) {
    std::cerr << "fx2_weight_sign_magnitude_probe_v1: " << e.what() << '\n';return 1;
  }
}
