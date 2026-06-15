#ifndef CMIX_MMAP_ALLOC_H
#define CMIX_MMAP_ALLOC_H

#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>

namespace cmix_mmap_alloc {

inline bool Enabled() {
  const char* flag = std::getenv("CMIX_MMAP_ALLOC");
  return flag == nullptr || std::strcmp(flag, "0") != 0;
}

inline size_t Threshold() {
  const char* value = std::getenv("CMIX_MMAP_THRESHOLD");
  if (!value || !*value) return 64ull << 20;
  char* end = nullptr;
  unsigned long long parsed = std::strtoull(value, &end, 10);
  if (end == value || parsed == 0) return 64ull << 20;
  return static_cast<size_t>(parsed);
}

inline const char* Directory() {
  const char* dir = std::getenv("CMIX_MMAP_DIR");
  return dir && *dir ? dir : "/tmp";
}

inline void* Allocate(size_t bytes, bool* mapped) {
  *mapped = false;
  if (!Enabled() || bytes < Threshold()) {
    return std::calloc(bytes, 1);
  }

  char pattern[4096];
  std::snprintf(pattern, sizeof(pattern), "%s/cmix21-map-XXXXXX", Directory());
  int fd = mkstemp(pattern);
  if (fd < 0) {
    std::fprintf(stderr, "cmix mmap mkstemp failed: %s\n", std::strerror(errno));
    return nullptr;
  }
  unlink(pattern);
  if (ftruncate(fd, static_cast<off_t>(bytes)) != 0) {
    std::fprintf(stderr, "cmix mmap ftruncate failed: %s\n", std::strerror(errno));
    close(fd);
    return nullptr;
  }
  void* ptr = mmap(nullptr, bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
  close(fd);
  if (ptr == MAP_FAILED) {
    std::fprintf(stderr, "cmix mmap failed: %s\n", std::strerror(errno));
    return nullptr;
  }
#ifdef MADV_RANDOM
  madvise(ptr, bytes, MADV_RANDOM);
#endif
  *mapped = true;
  return ptr;
}

inline void Release(void* ptr, size_t bytes, bool mapped) {
  if (!ptr) return;
  if (mapped) {
    munmap(ptr, bytes);
  } else {
    std::free(ptr);
  }
}

}  // namespace cmix_mmap_alloc

#endif
