// GPL-3.0-or-later. Read-only native match-continuation observations.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
namespace gamma_gap {
inline bool enabled=false;
inline unsigned run=0, aligned=0, shifted=0;
inline uint64_t clock=0;
inline FILE* trace=nullptr;
inline void fail(const char* message) { std::fprintf(stderr,"gap observer: %s\n",message); std::exit(2); }
inline void clear() { run=aligned=shifted=0; }
inline void begin() {
  if(enabled) fail("repeated activation");
  enabled=true; clock=0; clear();
  const char* path=std::getenv("GAMMA_GAP_TRACE");
  if(path && *path) { trace=std::fopen(path,"wbx"); if(!trace) fail("trace unavailable or exists"); }
}
inline void consider(unsigned length, bool missed, uint64_t cursor,
                     uint64_t total, const std::vector<unsigned char>& history) {
  if(!enabled || !missed || length<64 || length<=run || history.size()<4) return;
  const uint64_t h=history.size();
  if(cursor>=h) fail("parent cursor outside ring");
  const uint64_t distance=(total%h+h-cursor)%h;
  // Both cursor+1 and cursor+2 must refer to decoded, non-overwritten data.
  if(distance<3 || distance>total || distance>=h) return;
  run=length; aligned=history[(cursor+1)%h]; shifted=history[(cursor+2)%h];
}
struct Record {
  unsigned c, flags, a, s, r;
  explicit Record(unsigned count):c(count),flags(unsigned(clock%8)|(run?8:0)),a(aligned),s(shifted),r(run) {
    if(!enabled || c<1 || c>65535 || r>255) fail("invalid prediction boundary");
  }
  void finish(unsigned bit) {
    if(bit>1) fail("invalid truth");
    const unsigned char bytes[8]={static_cast<unsigned char>(c),static_cast<unsigned char>(c>>8),
      static_cast<unsigned char>(flags),static_cast<unsigned char>(bit),
      static_cast<unsigned char>(a),static_cast<unsigned char>(s),
      static_cast<unsigned char>(r),static_cast<unsigned char>(r>>8)};
    if(trace && std::fwrite(bytes,1,8,trace)!=8) fail("trace write");
    ++clock;
  }
};
inline void finish() {
  if(trace && std::fclose(trace)) fail("trace close");
  trace=nullptr;
  if(clock%8) fail("partial byte");
}
}
