#pragma once

#ifdef GAMMA_FILEBACKED_FXCM

#include <cerrno>
#include <climits>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dirent.h>
#include <fcntl.h>
#include <limits>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#ifndef MADV_PAGEOUT
#error "GAMMA_FILEBACKED_FXCM requires Linux MADV_PAGEOUT"
#endif

#if !defined(__BYTE_ORDER__) || __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "GAMMA_FILEBACKED_FXCM event protocol requires little-endian byte order"
#endif

namespace gamma_filebacked_fxcm {

inline constexpr size_t kMinimumBackedBytes = 64ULL * 1024ULL * 1024ULL;
inline constexpr size_t kMaximumMappings = 4096;
inline constexpr uint64_t kPageoutCadenceBytes = 1048576ULL;

enum class FailureCode : int {
  configuration = 64,
  path = 65,
  allocation = 66,
  mapping = 67,
  registry = 68,
  release = 69,
  pageout = 70,
  cleanup = 71,
};

enum class EventType : uint16_t {
  allocation = 1,
  pageout_initial = 2,
  pageout_cadence = 3,
  release = 4,
  cleanup_complete = 5,
};

struct EventRecord {
  uint32_t magic;
  uint16_t version;
  uint16_t type;
  uint64_t sequence;
  uint64_t mapping_id;
  uint64_t modeled_bytes;
  uint64_t mapping_base;
  uint64_t usable_pointer;
  uint64_t mapping_bytes;
  uint64_t detail;
};

static_assert(sizeof(EventRecord) == 64, "FXCM event records must be 64 bytes");

struct Hooks {
  void (*before_create)(int, const char*);
  int (*reserve)(int, off_t, off_t);
  void* (*map)(void*, size_t, int, int, int, off_t);
  int (*pageout)(void*, size_t, int);
  int (*unmap)(void*, size_t);
  int (*unlink_file)(int, const char*, int);
};

inline void BeforeCreateDefault(int, const char*) {}

inline int ReserveDefault(int fd, off_t offset, off_t bytes) {
  return posix_fallocate(fd, offset, bytes);
}

inline void* MapDefault(void* address, size_t bytes, int protection,
                        int flags, int fd, off_t offset) {
  return mmap(address, bytes, protection, flags, fd, offset);
}

inline int PageoutDefault(void* address, size_t bytes, int advice) {
  return madvise(address, bytes, advice);
}

inline int UnmapDefault(void* address, size_t bytes) {
  return munmap(address, bytes);
}

inline int UnlinkDefault(int directory, const char* name, int flags) {
  return unlinkat(directory, name, flags);
}

inline Hooks hooks = {
    BeforeCreateDefault,
    ReserveDefault,
    MapDefault,
    PageoutDefault,
    UnmapDefault,
    UnlinkDefault,
};

struct Mapping {
  void* base;
  size_t bytes;
  size_t requested_bytes;
  size_t alignment;
  void* usable_pointer;
  dev_t device;
  ino_t inode;
  char name[64];
  bool mapped;
  bool backing_file_live;
};

inline Mapping mappings[kMaximumMappings] = {};
inline size_t mapping_count = 0;
inline int scratch_dir_fd = -1;
inline uint64_t modeled_bytes = 0;
inline bool cleanup_registered = false;
inline int event_fd = -2;
inline uint64_t event_sequence = 0;

[[noreturn]] inline void Fail(FailureCode code, const char* operation) {
  dprintf(STDERR_FILENO,
          "GAMMA_FILEBACKED_FXCM failure code=%d operation=%s errno=%d\n",
          static_cast<int>(code), operation, errno);
  std::exit(static_cast<int>(code));
}

[[noreturn]] inline void TerminalFail(const char* operation) {
  dprintf(STDERR_FILENO,
          "GAMMA_FILEBACKED_FXCM terminal cleanup failure code=%d operation=%s errno=%d\n",
          static_cast<int>(FailureCode::cleanup), operation, errno);
  _exit(static_cast<int>(FailureCode::cleanup));
}

[[noreturn]] inline void ReleaseIntegrityFail(const char* operation) {
  dprintf(STDERR_FILENO,
          "GAMMA_FILEBACKED_FXCM release integrity failure code=%d operation=%s errno=%d\n",
          static_cast<int>(FailureCode::release), operation, errno);
  _exit(static_cast<int>(FailureCode::release));
}

inline int EventFd() {
  if (event_fd != -2) return event_fd;
  const char* value = std::getenv("GAMMA_FXCM_EVENT_FD");
  if (value == nullptr || value[0] == '\0') {
    event_fd = -1;
    return event_fd;
  }
  char* end = nullptr;
  errno = 0;
  const long parsed = std::strtol(value, &end, 10);
  if (errno != 0 || end == value || *end != '\0' || parsed < 0 ||
      parsed > INT_MAX || fcntl(static_cast<int>(parsed), F_GETFD) < 0) {
    Fail(FailureCode::configuration, "invalid event file descriptor");
  }
  event_fd = static_cast<int>(parsed);
  return event_fd;
}

inline void WriteEvent(EventType type, uint64_t mapping_id,
                       const Mapping* mapping, uint64_t detail,
                       bool terminal = false) {
  const int descriptor = EventFd();
  if (descriptor < 0) return;
  EventRecord record = {};
  record.magic = 0x31465847U;
  record.version = 1;
  record.type = static_cast<uint16_t>(type);
  record.sequence = ++event_sequence;
  record.mapping_id = mapping_id;
  record.modeled_bytes = modeled_bytes;
  if (mapping != nullptr) {
    record.mapping_base = reinterpret_cast<uintptr_t>(mapping->base);
    record.usable_pointer = reinterpret_cast<uintptr_t>(mapping->usable_pointer);
    record.mapping_bytes = mapping->bytes;
  }
  record.detail = detail;
  const unsigned char* cursor = reinterpret_cast<const unsigned char*>(&record);
  size_t remaining = sizeof(record);
  while (remaining > 0) {
    const ssize_t written = write(descriptor, cursor, remaining);
    if (written < 0 && errno == EINTR) continue;
    if (written <= 0) {
      if (terminal) TerminalFail("write terminal event");
      Fail(FailureCode::configuration, "write event");
    }
    cursor += written;
    remaining -= static_cast<size_t>(written);
  }
}

inline int OpenAbsoluteDirectoryNoSymlinks(const char* path) {
  if (path == nullptr || path[0] != '/') {
    Fail(FailureCode::configuration, "missing absolute backing directory");
  }
  int current = open("/", O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
  if (current < 0) Fail(FailureCode::path, "open root directory");
  const char* cursor = path + 1;
  while (*cursor != '\0') {
    const char* slash = std::strchr(cursor, '/');
    const size_t length = slash == nullptr ? std::strlen(cursor)
                                            : static_cast<size_t>(slash - cursor);
    if (length == 0 || length > NAME_MAX ||
        (length == 1 && cursor[0] == '.') ||
        (length == 2 && cursor[0] == '.' && cursor[1] == '.')) {
      close(current);
      Fail(FailureCode::path, "noncanonical backing directory path");
    }
    char component[NAME_MAX + 1];
    std::memcpy(component, cursor, length);
    component[length] = '\0';
    const int next = openat(current, component,
        O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (next < 0) {
      close(current);
      Fail(FailureCode::path, "open backing directory component");
    }
    if (close(current) != 0) {
      close(next);
      Fail(FailureCode::path, "close backing directory component");
    }
    current = next;
    if (slash == nullptr) break;
    cursor = slash + 1;
    if (*cursor == '\0') {
      close(current);
      Fail(FailureCode::path, "trailing slash in backing directory path");
    }
  }
  return current;
}

inline void RequireEmptyDirectory(int descriptor) {
  const int duplicate = dup(descriptor);
  if (duplicate < 0) Fail(FailureCode::path, "duplicate backing directory descriptor");
  DIR* directory = fdopendir(duplicate);
  if (directory == nullptr) {
    close(duplicate);
    Fail(FailureCode::path, "open backing directory stream");
  }
  errno = 0;
  while (dirent* entry = readdir(directory)) {
    if (std::strcmp(entry->d_name, ".") != 0 &&
        std::strcmp(entry->d_name, "..") != 0) {
      closedir(directory);
      Fail(FailureCode::path, "backing directory is not empty");
    }
  }
  if (errno != 0) {
    closedir(directory);
    Fail(FailureCode::path, "read backing directory");
  }
  if (closedir(directory) != 0) {
    Fail(FailureCode::path, "close backing directory stream");
  }
}

inline void EnsureScratchDirectory() {
  if (scratch_dir_fd >= 0) return;
  scratch_dir_fd = OpenAbsoluteDirectoryNoSymlinks(
      std::getenv("GAMMA_FXCM_BACKING_DIR"));
  struct stat metadata = {};
  if (fstat(scratch_dir_fd, &metadata) != 0 || !S_ISDIR(metadata.st_mode)) {
    Fail(FailureCode::path, "validate backing directory");
  }
  RequireEmptyDirectory(scratch_dir_fd);
}

inline void SafeUnlink(const Mapping& mapping, bool terminal = false) {
  struct stat metadata = {};
  if (fstatat(scratch_dir_fd, mapping.name, &metadata,
              AT_SYMLINK_NOFOLLOW) != 0) {
    if (terminal) TerminalFail("stat backing file before unlink");
    ReleaseIntegrityFail("stat backing file before unlink");
  }
  if (!S_ISREG(metadata.st_mode) || metadata.st_dev != mapping.device ||
      metadata.st_ino != mapping.inode) {
    if (terminal) TerminalFail("backing file identity mismatch");
    ReleaseIntegrityFail("backing file identity mismatch");
  }
  if (hooks.unlink_file(scratch_dir_fd, mapping.name, 0) != 0) {
    if (terminal) TerminalFail("unlink backing file");
    ReleaseIntegrityFail("unlink backing file");
  }
}

inline void RemoveUnregisteredFileOrFail(const char* name) {
  if (hooks.unlink_file(scratch_dir_fd, name, 0) != 0) {
    TerminalFail("remove unregistered backing file");
  }
}

inline void DiscardUnregisteredMappingOrFail(void* base, size_t bytes,
                                             const char* name) {
  if (hooks.unmap(base, bytes) != 0) {
    TerminalFail("unmap unregistered backing mapping");
  }
  RemoveUnregisteredFileOrFail(name);
}

inline void CleanupAll() {
  for (size_t i = mapping_count; i > 0; --i) {
    Mapping& mapping = mappings[i - 1];
    if (!mapping.mapped && !mapping.backing_file_live) continue;
    if (mapping.mapped) {
      if (hooks.unmap(mapping.base, mapping.bytes) != 0) {
        TerminalFail("terminal munmap");
      }
      mapping.mapped = false;
    }
    if (mapping.backing_file_live) {
      SafeUnlink(mapping, true);
      mapping.backing_file_live = false;
    }
    WriteEvent(EventType::release, i - 1, &mapping, 0, true);
  }
  if (scratch_dir_fd >= 0) {
    if (close(scratch_dir_fd) != 0) TerminalFail("close backing directory");
    scratch_dir_fd = -1;
  }
  WriteEvent(EventType::cleanup_complete, UINT64_MAX, nullptr, 0, true);
}

inline void RegisterCleanup() {
  if (cleanup_registered) return;
  if (std::atexit(CleanupAll) != 0) {
    Fail(FailureCode::cleanup, "register terminal cleanup");
  }
  cleanup_registered = true;
}

inline void* AllocateBacked(size_t bytes, size_t requested_bytes,
                            size_t alignment) {
  if (alignment == 0 || (alignment & (alignment - 1)) != 0 ||
      alignment > 0xffffU || requested_bytes == 0 ||
      requested_bytes > 0x0000ffffffffffffULL ||
      requested_bytes > bytes ||
      bytes > static_cast<size_t>(std::numeric_limits<off_t>::max())) {
    Fail(FailureCode::allocation, "invalid allocation geometry");
  }
  EnsureScratchDirectory();
  RegisterCleanup();
  if (mapping_count >= kMaximumMappings) {
    Fail(FailureCode::registry, "mapping registry capacity");
  }
  Mapping& mapping = mappings[mapping_count];
  const int length = std::snprintf(mapping.name, sizeof(mapping.name),
      "fxcm-%04zu.bin", mapping_count);
  if (length <= 0 || static_cast<size_t>(length) >= sizeof(mapping.name)) {
    Fail(FailureCode::registry, "format backing filename");
  }
  hooks.before_create(scratch_dir_fd, mapping.name);
  const int fd = openat(scratch_dir_fd, mapping.name,
      O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC | O_RDWR, 0600);
  if (fd < 0) Fail(FailureCode::allocation, "create backing file");
  const int reserve_result = hooks.reserve(fd, 0, static_cast<off_t>(bytes));
  if (reserve_result != 0) {
    if (close(fd) != 0) TerminalFail("close unreserved backing file");
    RemoveUnregisteredFileOrFail(mapping.name);
    errno = reserve_result;
    Fail(FailureCode::allocation, "reserve backing file");
  }
  struct stat metadata = {};
  if (fstat(fd, &metadata) != 0 || !S_ISREG(metadata.st_mode) ||
      metadata.st_size != static_cast<off_t>(bytes)) {
    const int validation_errno = errno;
    if (close(fd) != 0) TerminalFail("close invalid backing file");
    RemoveUnregisteredFileOrFail(mapping.name);
    errno = validation_errno;
    Fail(FailureCode::allocation, "validate backing file");
  }
  void* base = hooks.map(nullptr, bytes, PROT_READ | PROT_WRITE,
                         MAP_SHARED, fd, 0);
  const int map_errno = errno;
  if (close(fd) != 0) {
    if (base != MAP_FAILED && hooks.unmap(base, bytes) != 0) {
      TerminalFail("unmap after mapped-file close failure");
    }
    RemoveUnregisteredFileOrFail(mapping.name);
    TerminalFail("close mapped backing file");
  }
  if (base == MAP_FAILED) {
    RemoveUnregisteredFileOrFail(mapping.name);
    errno = map_errno;
    Fail(FailureCode::mapping, "map backing file");
  }
  mapping.base = base;
  mapping.bytes = bytes;
  mapping.requested_bytes = requested_bytes;
  mapping.alignment = alignment;
  const uintptr_t base_address = reinterpret_cast<uintptr_t>(base);
  if (base_address > std::numeric_limits<uintptr_t>::max() - (alignment - 1)) {
    DiscardUnregisteredMappingOrFail(base, bytes, mapping.name);
    Fail(FailureCode::mapping, "aligned pointer overflow");
  }
  const uintptr_t usable_address =
      (base_address + alignment - 1) &
      ~(static_cast<uintptr_t>(alignment) - 1);
  if (usable_address < base_address || usable_address - base_address > bytes ||
      requested_bytes > bytes - (usable_address - base_address)) {
    DiscardUnregisteredMappingOrFail(base, bytes, mapping.name);
    Fail(FailureCode::mapping, "usable allocation exceeds mapping");
  }
  mapping.usable_pointer = reinterpret_cast<void*>(usable_address);
  mapping.device = metadata.st_dev;
  mapping.inode = metadata.st_ino;
  mapping.mapped = true;
  mapping.backing_file_live = true;
  ++mapping_count;
  const uint64_t packed_detail =
      (static_cast<uint64_t>(alignment & 0xffffU) << 48) |
      static_cast<uint64_t>(requested_bytes & 0x0000ffffffffffffULL);
  WriteEvent(EventType::allocation, mapping_count - 1, &mapping,
             packed_detail);
  return base;
}

inline void Release(void* pointer) {
  if (pointer == nullptr) return;
  const uintptr_t address = reinterpret_cast<uintptr_t>(pointer);
  for (size_t i = 0; i < mapping_count; ++i) {
    Mapping& mapping = mappings[i];
    if (!mapping.mapped && !mapping.backing_file_live) continue;
    const uintptr_t begin = reinterpret_cast<uintptr_t>(mapping.base);
    if (address == begin) {
      if (mapping.mapped) {
        if (hooks.unmap(mapping.base, mapping.bytes) != 0) {
          Fail(FailureCode::release, "munmap");
        }
        mapping.mapped = false;
      }
      if (mapping.backing_file_live) {
        SafeUnlink(mapping);
        mapping.backing_file_live = false;
      }
      WriteEvent(EventType::release, i, &mapping, 0);
      return;
    }
    if (mapping.mapped && address > begin && address - begin < mapping.bytes) {
      Fail(FailureCode::release, "attempt to free interior mapping pointer");
    }
  }
  std::free(pointer);
}

inline void PageOutAll(bool initial = false) {
  for (size_t i = 0; i < mapping_count; ++i) {
    Mapping& mapping = mappings[i];
    if (!mapping.mapped) continue;
    const int result = hooks.pageout(mapping.base, mapping.bytes, MADV_PAGEOUT);
    WriteEvent(initial ? EventType::pageout_initial
                       : EventType::pageout_cadence,
               i, &mapping, static_cast<uint64_t>(static_cast<uint32_t>(result)));
    if (result != 0) {
      Fail(FailureCode::pageout, "MADV_PAGEOUT");
    }
  }
}

inline void ByteBoundary() {
  ++modeled_bytes;
  if (modeled_bytes % kPageoutCadenceBytes == 0) PageOutAll();
}

#ifdef GAMMA_FILEBACKED_FXCM_TESTING
inline void InstallHooksForTesting(const Hooks& replacement) {
  hooks = replacement;
}

inline void ForceMappingCountForTesting(size_t count) {
  mapping_count = count;
}
#endif

}  // namespace gamma_filebacked_fxcm

#endif  // GAMMA_FILEBACKED_FXCM
