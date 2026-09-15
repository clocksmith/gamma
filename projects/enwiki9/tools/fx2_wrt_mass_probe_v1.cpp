// Independent bounded integer reference for the prospective native kernel.
#include <cstdint>
extern "C" unsigned gamma_mass(unsigned p, uint64_t c0, uint64_t c1,
                               uint64_t a0, uint64_t a1) {
  const uint64_t ceiling = uint64_t(1) << 44;
  if (!p || p >= 65536 || !c0 || !c1 || c0 > ceiling || c1 > ceiling ||
      c0+c1 > ceiling || !a0 || !a1 || a0 > c0 || a1 > c1) return 0;
  using U = unsigned __int128;
  U a=U(p)*a1*c0, b=U(65536-p)*a0*c1;
  unsigned q=(65536*a+(a+b)/2)/(a+b);
  return q < 1 ? 1 : q > 65535 ? 65535 : q;
}
