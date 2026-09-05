// minimal .npy reader (test-only): supports '<f4' and '|i1', C order
#pragma once

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace fx2 {

struct Npy {
  std::string dtype;  // "<f4" or "|i1"
  std::vector<size_t> shape;
  std::vector<uint8_t> data;

  size_t numel() const {
    size_t n = 1;
    for (size_t d : shape) n *= d;
    return n;
  }
  size_t rows() const { return shape.empty() ? 1 : shape[0]; }
  size_t row_elems() const {
    size_t n = 1;
    for (size_t i = 1; i < shape.size(); i++) n *= shape[i];
    return n;
  }
  const float* f32() const { return reinterpret_cast<const float*>(data.data()); }
  const int8_t* i8() const { return reinterpret_cast<const int8_t*>(data.data()); }
  bool is_f32() const { return dtype == "<f4"; }
  bool is_i8() const { return dtype == "|i1"; }
};

[[noreturn]] inline void npy_die(const std::string& path, const char* msg) {
  std::fprintf(stderr, "npy: %s: %s\n", path.c_str(), msg);
  std::exit(1);
}

inline Npy load_npy(const std::string& path) {
  FILE* f = std::fopen(path.c_str(), "rb");
  if (!f) npy_die(path, "cannot open");
  uint8_t pre[10];
  if (std::fread(pre, 1, 10, f) != 10) npy_die(path, "short header");
  if (std::memcmp(pre, "\x93NUMPY", 6) != 0) npy_die(path, "bad magic");
  int major = pre[6];
  size_t header_len, data_off;
  if (major == 1) {
    header_len = pre[8] | (size_t(pre[9]) << 8);
    data_off = 10 + header_len;
  } else {
    uint8_t ext[2];
    if (std::fread(ext, 1, 2, f) != 2) npy_die(path, "short header");
    header_len = pre[8] | (size_t(pre[9]) << 8) | (size_t(ext[0]) << 16) |
                 (size_t(ext[1]) << 24);
    data_off = 12 + header_len;
  }
  std::string header(header_len, '\0');
  if (std::fread(&header[0], 1, header_len, f) != header_len)
    npy_die(path, "short header dict");

  Npy npy;
  {
    size_t p = header.find("'descr'");
    if (p == std::string::npos) npy_die(path, "no descr");
    p = header.find('\'', p + 7);
    size_t q = header.find('\'', p + 1);
    npy.dtype = header.substr(p + 1, q - p - 1);
    if (npy.dtype != "<f4" && npy.dtype != "|i1")
      npy_die(path, "unsupported dtype");
  }
  if (header.find("'fortran_order': False") == std::string::npos)
    npy_die(path, "fortran order not supported");
  {
    size_t p = header.find("'shape'");
    if (p == std::string::npos) npy_die(path, "no shape");
    p = header.find('(', p);
    size_t q = header.find(')', p);
    std::string dims = header.substr(p + 1, q - p - 1);
    const char* c = dims.c_str();
    while (*c) {
      while (*c == ' ' || *c == ',') c++;
      if (!*c) break;
      npy.shape.push_back(std::strtoull(c, const_cast<char**>(&c), 10));
    }
  }
  size_t itemsize = npy.dtype == "<f4" ? 4 : 1;
  size_t bytes = npy.numel() * itemsize;
  npy.data.resize(bytes);
  std::fseek(f, static_cast<long>(data_off), SEEK_SET);
  if (std::fread(npy.data.data(), 1, bytes, f) != bytes)
    npy_die(path, "short data");
  std::fclose(f);
  return npy;
}

}  // namespace fx2
