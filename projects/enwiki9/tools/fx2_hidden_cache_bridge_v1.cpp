#include "../lib/fx2_hidden_cache_v1.hpp"
#include <new>
using gamma_hidden_cache_v1::Cache;
extern "C" {
void* cache_new(char arm) {
  if (arm != 'K' && arm != 'D' && arm != 'S') return nullptr;
  return new (std::nothrow) Cache(arm);
}
void cache_delete(void* p) { delete static_cast<Cache*>(p); }
int cache_predict(void* p, unsigned count, uint64_t signature, unsigned valid) {
  if (!p || valid > 1) return -1;
  return static_cast<Cache*>(p)->predict(count, signature, valid != 0);
}
int cache_observe(void* p, unsigned bit) {
  return p && static_cast<Cache*>(p)->observe(bit);
}
unsigned cache_state(void* p, uint8_t* out, unsigned capacity) {
  return p ? unsigned(static_cast<Cache*>(p)->state(out, capacity)) : 0;
}
unsigned cache_state_size() { return gamma_hidden_cache_v1::STATE_BYTES; }
unsigned cache_distance(uint64_t a, uint64_t b) {
  return gamma_hidden_cache_v1::distance(a, b);
}
}
