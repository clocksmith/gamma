#include "weights_io.h"

#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace fx2 {

namespace {

[[noreturn]] void die(const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  std::fprintf(stderr, "weights_io: ");
  std::vfprintf(stderr, fmt, ap);
  std::fprintf(stderr, "\n");
  va_end(ap);
  std::exit(1);
}

size_t dtype_size(uint8_t dtype) {
  switch (dtype) {
    case DT_I8:
      return 1;
    case DT_BF16:
      return 2;
    case DT_F32:
      return 4;
    case DT_I32:
      return 4;
    default:
      die("unknown dtype code %u", unsigned(dtype));
  }
}

struct Reader {
  const uint8_t* p;
  size_t left;
  const char* path;

  void need(size_t n) {
    if (left < n) die("%s: truncated file (need %zu more bytes)", path, n);
  }
  void read(void* dst, size_t n) {
    need(n);
    std::memcpy(dst, p, n);
    p += n;
    left -= n;
  }
  uint32_t u32() {
    uint32_t v;
    read(&v, 4);
    return v;
  }
  uint8_t u8() {
    uint8_t v;
    read(&v, 1);
    return v;
  }
};

}  // namespace

WeightsFile WeightsFile::load(const char* path) {
  FILE* f = std::fopen(path, "rb");
  if (!f) die("cannot open %s", path);
  std::fseek(f, 0, SEEK_END);
  long size = std::ftell(f);
  std::fseek(f, 0, SEEK_SET);
  if (size < 12) die("%s: too small", path);
  std::vector<uint8_t> buf(static_cast<size_t>(size));
  if (std::fread(buf.data(), 1, buf.size(), f) != buf.size())
    die("%s: short read", path);
  std::fclose(f);

  Reader r{buf.data(), buf.size(), path};
  char magic[8];
  r.read(magic, 8);
  if (std::memcmp(magic, "FX2TFW01", 8) != 0) die("%s: bad magic", path);

  uint32_t n_tensors = r.u32();
  WeightsFile wf;
  wf.tensors.reserve(n_tensors);
  for (uint32_t i = 0; i < n_tensors; i++) {
    uint32_t name_len = r.u32();
    if (name_len > 4096) die("%s: absurd name length %u", path, name_len);
    std::string name(name_len, '\0');
    r.read(&name[0], name_len);

    WTensor t;
    t.dtype = r.u8();
    dtype_size(t.dtype);  // validates the code
    uint32_t ndim = r.u32();
    if (ndim > 8) die("%s: %s: absurd ndim %u", path, name.c_str(), ndim);
    t.shape.resize(ndim);
    size_t numel = 1;
    for (uint32_t d = 0; d < ndim; d++) {
      t.shape[d] = r.u32();
      numel *= t.shape[d];
    }
    t.numel = numel;
    size_t bytes = numel * dtype_size(t.dtype);
    t.data.resize(bytes);
    r.read(t.data.data(), bytes);

    if (!wf.tensors.emplace(name, std::move(t)).second)
      die("%s: duplicate tensor %s", path, name.c_str());
  }
  if (r.left != 0)
    die("%s: %zu trailing bytes after last tensor", path, r.left);
  return wf;
}

const WTensor& WeightsFile::get(const std::string& name) const {
  auto it = tensors.find(name);
  if (it == tensors.end()) die("missing tensor %s", name.c_str());
  return it->second;
}

const WTensor& WeightsFile::get(const std::string& name, uint8_t dtype,
                                std::initializer_list<uint32_t> shape) const {
  const WTensor& t = get(name);
  if (t.dtype != dtype)
    die("%s: dtype %u, expected %u", name.c_str(), unsigned(t.dtype),
        unsigned(dtype));
  if (t.shape.size() != shape.size())
    die("%s: ndim %zu, expected %zu", name.c_str(), t.shape.size(),
        shape.size());
  size_t i = 0;
  for (uint32_t d : shape) {
    if (t.shape[i] != d)
      die("%s: shape[%zu] = %u, expected %u", name.c_str(), i, t.shape[i], d);
    i++;
  }
  return t;
}

}  // namespace fx2
