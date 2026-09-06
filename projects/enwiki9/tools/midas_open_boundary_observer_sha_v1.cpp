// Reuse the sealed observer verbatim; replace only its witness hash function.
#include "../lib/midas_observer_sha256_x86_v1.hpp"
#define Sha256Hex ObserverSha256Hex
#include "midas_open_boundary_observer_v1.cpp"
#undef Sha256Hex
