// Loader for the real-data q/k/v capture written by capture_qkv.cpp
// (data/attn_qkv_article22.bin): per vanilla layer (3/7/11), the post-rope
// int8 q/k/v ints of every captured position + the static per-head scales.
#pragma once

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

namespace fx2 {
namespace opt {

struct QkvCapture {
  uint32_t n_pos = 0, n_layers = 0, d = 0, rope_off = 0;
  float scales[3][3][3];  // [layer_idx (3,7,11)][q,k,v][head]
  std::vector<int8_t> q, k, v;  // each [layer][pos][192]

  const int8_t* qrow(int li, long t) const {
    return q.data() + (static_cast<size_t>(li) * n_pos + t) * 192;
  }
  const int8_t* krow(int li, long t) const {
    return k.data() + (static_cast<size_t>(li) * n_pos + t) * 192;
  }
  const int8_t* vrow(int li, long t) const {
    return v.data() + (static_cast<size_t>(li) * n_pos + t) * 192;
  }
  // identical expression to model.cpp: L.coef[h] = 0.125f * sq[h] * sk[h]
  float coef(int li, int h) const {
    return 0.125f * scales[li][0][h] * scales[li][1][h];
  }
  float sv(int li, int h) const { return scales[li][2][h]; }

  bool load(const std::string& path) {
    FILE* f = std::fopen(path.c_str(), "rb");
    if (!f) return false;
    char magic[8];
    uint32_t hdr[4];
    if (std::fread(magic, 1, 8, f) != 8 ||
        std::memcmp(magic, "ATNQKV22", 8) != 0 ||
        std::fread(hdr, 4, 4, f) != 4) {
      std::fclose(f);
      return false;
    }
    n_pos = hdr[0];
    n_layers = hdr[1];
    d = hdr[2];
    rope_off = hdr[3];
    if (n_layers != 3 || d != 192 || n_pos == 0 || n_pos > (1u << 20)) {
      std::fclose(f);
      return false;
    }
    if (std::fread(scales, 4, 27, f) != 27) {
      std::fclose(f);
      return false;
    }
    size_t plane = static_cast<size_t>(n_pos) * 192;
    q.resize(3 * plane);
    k.resize(3 * plane);
    v.resize(3 * plane);
    bool ok = std::fread(q.data(), 1, q.size(), f) == q.size() &&
              std::fread(k.data(), 1, k.size(), f) == k.size() &&
              std::fread(v.data(), 1, v.size(), f) == v.size();
    std::fclose(f);
    return ok;
  }
};

// default location relative to common working directories
inline std::string find_capture(const char* override_path) {
  if (override_path) return override_path;
  const char* cands[] = {"../../data/attn_qkv_article22.bin",
                         "cpp_infer/data/attn_qkv_article22.bin",
                         "data/attn_qkv_article22.bin",
                         "../data/attn_qkv_article22.bin"};
  for (const char* c : cands) {
    FILE* f = std::fopen(c, "rb");
    if (f) {
      std::fclose(f);
      return c;
    }
  }
  return "";
}

}  // namespace opt
}  // namespace fx2
