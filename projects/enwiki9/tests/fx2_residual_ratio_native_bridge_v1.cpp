// Synthetic differential-test ABI; not part of the proposed codec package.
#include "../lib/fx2_residual_ratio_v1.hpp"
struct Handle { gamma_ratio::Ratio ratio; unsigned size; };
extern "C" {
void* ratio_new(unsigned size, char arm) {
  Handle* h=new Handle;
  if (!h->ratio.configure(size,arm)) { delete h; return nullptr; }
  h->size=size; return h;
}
void ratio_delete(void* p) { delete static_cast<Handle*>(p); }
int ratio_predict(void* p, uint32_t* bits) {
  Handle* h=static_cast<Handle*>(p); std::array<float,256> values{};
  for(unsigned i=0;i<h->size;++i) std::memcpy(&values[i],bits+i,4);
  if(!h->ratio.predict(values.data())) return 0;
  for(unsigned i=0;i<h->size;++i) std::memcpy(bits+i,&values[i],4);
  return 1;
}
int ratio_observe(void* p, unsigned symbol) { return static_cast<Handle*>(p)->ratio.observe(symbol); }
unsigned ratio_save(void* p, uint8_t* output) {
  auto bytes=static_cast<Handle*>(p)->ratio.serialize();
  std::memcpy(output,bytes.data(),bytes.size()); return bytes.size();
}
int ratio_load(void* p, const uint8_t* bytes, unsigned length) {
  return static_cast<Handle*>(p)->ratio.restore(bytes,length);
}
uint64_t ratio_units(uint32_t bits) {
  float p; std::memcpy(&p,&bits,4); uint64_t units=0;
  return gamma_ratio::Ratio::units(p,units) ? units : 0;
}
}
