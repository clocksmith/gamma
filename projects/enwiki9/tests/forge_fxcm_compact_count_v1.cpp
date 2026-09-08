#include "../results/forge_parent_source_audit_v1/source-tree/src/models/fxcm_v26.cpp"
static_assert(fxcmv26::ConfiguredOutputCount()==403,
              "the pinned compact23 configuration must expose exactly 403 outputs");
static_assert(fxcmv26::kModelGroupMask==23 && fxcmv26::kAuxFeatureMask==1,
              "this probe is not the previously tested full 560-output model");
