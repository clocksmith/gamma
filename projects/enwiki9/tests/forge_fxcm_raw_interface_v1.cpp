#include "../results/forge_parent_source_audit_v1/source-tree/src/models/fxcm_v26.h"
#include "../lib/forge_fxcm_raw_adapter_v1.hpp"
bool gamma_forge_interface_compile_probe(FXCMV26& model,float* output) {
  return gamma_forge::probabilities(model,403,output);
}
