// shared test-data loading for test_components / test_e2e / bench
#pragma once

#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace fx2 {

[[noreturn]] inline void td_die(const std::string& msg) {
  std::fprintf(stderr, "testdata: %s\n", msg.c_str());
  std::exit(1);
}

inline bool file_exists(const std::string& p) {
  struct stat st;
  return ::stat(p.c_str(), &st) == 0;
}

// locate the data directory relative to common working directories
inline std::string find_data_dir(const char* override_dir) {
  if (override_dir) {
    if (!file_exists(std::string(override_dir) + "/weights.bin"))
      td_die(std::string(override_dir) + "/weights.bin not found");
    return override_dir;
  }
  for (const char* c : {"cpp_infer/data", "data", "../data", "../cpp_infer/data"})
    if (file_exists(std::string(c) + "/weights.bin")) return c;
  td_die("cannot locate the data directory (try --data <dir>)");
}

template <typename T>
inline std::vector<T> read_file(const std::string& path) {
  FILE* f = std::fopen(path.c_str(), "rb");
  if (!f) td_die("cannot open " + path);
  std::fseek(f, 0, SEEK_END);
  long bytes = std::ftell(f);
  std::fseek(f, 0, SEEK_SET);
  if (bytes % static_cast<long>(sizeof(T)) != 0)
    td_die(path + ": size not a multiple of the element size");
  std::vector<T> v(static_cast<size_t>(bytes) / sizeof(T));
  if (std::fread(v.data(), 1, static_cast<size_t>(bytes), f) !=
      static_cast<size_t>(bytes))
    td_die(path + ": short read");
  std::fclose(f);
  return v;
}

struct Mmapped {
  const uint8_t* p = nullptr;
  size_t bytes = 0;

  void open_ro(const std::string& path) {
    int fd = ::open(path.c_str(), O_RDONLY);
    if (fd < 0) td_die("cannot open " + path);
    struct stat st;
    if (::fstat(fd, &st) != 0) td_die("fstat " + path);
    bytes = static_cast<size_t>(st.st_size);
    void* m = ::mmap(nullptr, bytes, PROT_READ, MAP_PRIVATE, fd, 0);
    ::close(fd);
    if (m == MAP_FAILED) td_die("mmap " + path);
    p = static_cast<const uint8_t*>(m);
  }
  ~Mmapped() {
    if (p) ::munmap(const_cast<uint8_t*>(p), bytes);
  }
};

struct TestData {
  std::string dir;
  std::vector<uint8_t> tokens;
  std::vector<int32_t> bounds;        // n_articles + 1
  std::vector<int32_t> rope_offsets;  // n_articles
  Mmapped priors;                     // f16, n_tokens x 205
  Mmapped ref_probs;                  // f16, n_tokens x 205 (optional)
  int n_articles = 0;

  void load(const std::string& data_dir, bool with_ref_probs) {
    dir = data_dir;
    tokens = read_file<uint8_t>(dir + "/test_tokens.u8");
    bounds = read_file<int32_t>(dir + "/test_bounds.i32");
    rope_offsets = read_file<int32_t>(dir + "/test_rope_offsets.i32");
    n_articles = static_cast<int>(bounds.size()) - 1;
    if (n_articles <= 0 || bounds[0] != 0 ||
        static_cast<size_t>(bounds[n_articles]) != tokens.size())
      td_die("inconsistent test_bounds.i32");
    if (rope_offsets.size() != static_cast<size_t>(n_articles))
      td_die("inconsistent test_rope_offsets.i32");
    priors.open_ro(dir + "/test_priors.f16");
    if (priors.bytes != tokens.size() * 205 * 2)
      td_die("test_priors.f16 has the wrong size");
    if (with_ref_probs) {
      ref_probs.open_ro(dir + "/test_ref_probs.f16");
      if (ref_probs.bytes != tokens.size() * 205 * 2)
        td_die("test_ref_probs.f16 has the wrong size");
    }
  }

  const uint16_t* prior_row(size_t r) const {
    return reinterpret_cast<const uint16_t*>(priors.p) + r * 205;
  }
  const uint16_t* ref_prob_row(size_t r) const {
    return reinterpret_cast<const uint16_t*>(ref_probs.p) + r * 205;
  }
};

// tiny helpers for meta.json scalar fields ("key": value)
inline long meta_int(const std::string& json, const char* key) {
  std::string pat = std::string("\"") + key + "\":";
  size_t p = json.find(pat);
  if (p == std::string::npos) td_die(std::string("meta.json: missing ") + key);
  return std::strtol(json.c_str() + p + pat.size(), nullptr, 10);
}

inline std::string read_text_file(const std::string& path) {
  FILE* f = std::fopen(path.c_str(), "rb");
  if (!f) td_die("cannot open " + path);
  std::string s;
  char buf[65536];
  size_t n;
  while ((n = std::fread(buf, 1, sizeof buf, f)) > 0) s.append(buf, n);
  std::fclose(f);
  return s;
}

}  // namespace fx2
