#ifndef GAMMA_WRT_OBSERVER_V1_HPP
#define GAMMA_WRT_OBSERVER_V1_HPP
#include <cstdio>
#include <cstdlib>
namespace gamma_wrt_observer {
struct Sink {
  FILE* f;
  Sink() {
    const char* p = std::getenv("GAMMA_WRT_TRACE");
    f = p ? std::fopen(p, "wbx") : nullptr;
    if (!f) std::_Exit(125);
  }
  ~Sink() { if (std::fclose(f)) std::_Exit(125); }
};
inline void write(const unsigned char* row) {
  static Sink s;
  if (std::fwrite(row, 1, 20, s.f) != 20) std::_Exit(125);
}
}
#endif
