#ifndef GAMMA_CMIX_ALLOCATION_MARKER_H
#define GAMMA_CMIX_ALLOCATION_MARKER_H

#include <cerrno>
#include <climits>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <unistd.h>

namespace gamma_allocation_marker {

static const std::uint64_t kMagic = UINT64_C(0x434f4c4c414d4147);
static const std::uint16_t kVersion = 1;
static const std::size_t kMaximumLiveAllocations = 4096;

enum Event : std::uint32_t {
  kAllocation = 1,
  kRelease = 2,
  kPageout = 3
};

enum Label : std::uint32_t {
  kFxcmAlloc = 1,
  kFxcmAllocAligned = 2,
  kContextHistory = 10,
  kContextSharedMap = 11,
  kContextIndirect1 = 12,
  kContextIndirect2 = 13,
  kContextIndirect3 = 14,
  kMixerSlab = 20,
  kPpmdArenaAnonymous = 30,
  kPpmdArenaFileBacked = 31
};

#pragma pack(push, 1)
struct Record {
  std::uint64_t magic;
  std::uint16_t version;
  std::uint16_t record_bytes;
  std::uint32_t sequence;
  std::uint32_t event;
  std::uint32_t label;
  std::uint64_t allocation_base;
  std::uint64_t usable_pointer;
  std::uint64_t allocation_bytes;
  std::uint64_t usable_bytes;
  std::uint32_t alignment;
  std::uint32_t reserved;
};
#pragma pack(pop)

static_assert(sizeof(Record) == 64, "allocation marker record must be 64 bytes");

struct LiveAllocation {
  Label label;
  const void* allocation_base;
  const void* usable_pointer;
  std::uint64_t allocation_bytes;
  std::uint64_t usable_bytes;
  std::uint32_t alignment;
};

inline LiveAllocation* Registry() {
  static LiveAllocation entries[kMaximumLiveAllocations] = {};
  return entries;
}

inline int& MarkerFdState() {
  static int state = -3;
  return state;
}

inline std::uint32_t& SequenceState() {
  static std::uint32_t sequence = 0;
  return sequence;
}

inline int MarkerFd() {
  int& state = MarkerFdState();
  if (state != -3) return state;
  const char* raw = std::getenv("GAMMA_ALLOCATION_MARKER_FD");
  if (raw == NULL || raw[0] == 0) {
    state = -1;
    return state;
  }
  char* end = NULL;
  errno = 0;
  const long value = std::strtol(raw, &end, 10);
  if (errno != 0 || end == raw || *end != 0 || value < 0 || value > INT_MAX) {
    state = -2;
    return state;
  }
  state = static_cast<int>(value);
  return state;
}

inline bool MarkerEnabled() {
  return MarkerFd() >= 0;
}

inline bool MarkerHealthy() {
  return MarkerFd() != -2;
}

inline bool LatchFailure() {
  MarkerFdState() = -2;
  return false;
}

inline LiveAllocation* FindByAllocationBase(const void* pointer) {
  if (pointer == NULL) return NULL;
  LiveAllocation* entries = Registry();
  for (std::size_t index = 0; index < kMaximumLiveAllocations; ++index) {
    if (entries[index].allocation_base == pointer) return &entries[index];
  }
  return NULL;
}

inline LiveAllocation* FindByUsablePointer(const void* pointer) {
  if (pointer == NULL) return NULL;
  LiveAllocation* entries = Registry();
  for (std::size_t index = 0; index < kMaximumLiveAllocations; ++index) {
    if (entries[index].usable_pointer == pointer) return &entries[index];
  }
  return NULL;
}

inline bool RegisterAllocation(
    Label label,
    const void* allocation_base,
    const void* usable_pointer,
    std::uint64_t allocation_bytes,
    std::uint64_t usable_bytes,
    std::uint32_t alignment) {
  if (allocation_base == NULL || usable_pointer == NULL ||
      FindByAllocationBase(allocation_base) != NULL) {
    return LatchFailure();
  }
  LiveAllocation* entries = Registry();
  for (std::size_t index = 0; index < kMaximumLiveAllocations; ++index) {
    if (entries[index].allocation_base == NULL) {
      entries[index].label = label;
      entries[index].allocation_base = allocation_base;
      entries[index].usable_pointer = usable_pointer;
      entries[index].allocation_bytes = allocation_bytes;
      entries[index].usable_bytes = usable_bytes;
      entries[index].alignment = alignment;
      return true;
    }
  }
  return LatchFailure();
}

inline bool WriteRecord(const Record& record) {
  int& state = MarkerFdState();
  const int fd = MarkerFd();
  if (fd < 0) return fd == -1;
  const unsigned char* bytes =
      reinterpret_cast<const unsigned char*>(&record);
  std::size_t offset = 0;
  while (offset < sizeof(record)) {
    const ssize_t written =
        ::write(fd, bytes + offset, sizeof(record) - offset);
    if (written < 0 && errno == EINTR) continue;
    if (written <= 0) {
      state = -2;
      return false;
    }
    offset += static_cast<std::size_t>(written);
  }
  return true;
}

inline bool Emit(
    Event event,
    Label label,
    const void* allocation_base,
    const void* usable_pointer,
    std::uint64_t allocation_bytes,
    std::uint64_t usable_bytes,
    std::uint32_t alignment) {
  if (!MarkerEnabled()) return MarkerHealthy();
  Record record = {};
  record.magic = kMagic;
  record.version = kVersion;
  record.record_bytes = sizeof(Record);
  record.sequence = SequenceState()++;
  record.event = static_cast<std::uint32_t>(event);
  record.label = static_cast<std::uint32_t>(label);
  record.allocation_base = static_cast<std::uint64_t>(
      reinterpret_cast<std::uintptr_t>(allocation_base));
  record.usable_pointer = static_cast<std::uint64_t>(
      reinterpret_cast<std::uintptr_t>(usable_pointer));
  record.allocation_bytes = allocation_bytes;
  record.usable_bytes = usable_bytes;
  record.alignment = alignment;
  return WriteRecord(record);
}

inline bool RecordAllocation(
    Label label,
    const void* allocation_base,
    const void* usable_pointer,
    std::uint64_t allocation_bytes,
    std::uint64_t usable_bytes,
    std::uint32_t alignment) {
  if (!MarkerEnabled()) return MarkerHealthy();
  if (!RegisterAllocation(
          label,
          allocation_base,
          usable_pointer,
          allocation_bytes,
          usable_bytes,
          alignment)) {
    return false;
  }
  return Emit(
      kAllocation,
      label,
      allocation_base,
      usable_pointer,
      allocation_bytes,
      usable_bytes,
      alignment);
}

inline bool RecordRelease(
    Label label,
    const void* allocation_base,
    const void* usable_pointer,
    std::uint64_t allocation_bytes,
    std::uint64_t usable_bytes,
    std::uint32_t alignment) {
  if (!MarkerEnabled()) return MarkerHealthy();
  LiveAllocation* allocation = FindByAllocationBase(allocation_base);
  if (allocation == NULL || allocation->label != label ||
      allocation->usable_pointer != usable_pointer ||
      allocation->allocation_bytes != allocation_bytes ||
      allocation->usable_bytes != usable_bytes ||
      allocation->alignment != alignment) {
    return LatchFailure();
  }
  if (!Emit(
      kRelease,
      label,
      allocation_base,
      usable_pointer,
      allocation_bytes,
      usable_bytes,
      alignment)) {
    return false;
  }
  *allocation = LiveAllocation();
  return true;
}

inline bool RecordReleaseByAllocationBase(const void* allocation_base) {
  if (!MarkerEnabled()) return MarkerHealthy();
  if (allocation_base == NULL) return true;
  LiveAllocation* allocation = FindByAllocationBase(allocation_base);
  if (allocation == NULL) return LatchFailure();
  return RecordRelease(
      allocation->label,
      allocation->allocation_base,
      allocation->usable_pointer,
      allocation->allocation_bytes,
      allocation->usable_bytes,
      allocation->alignment);
}

inline bool RecordReleaseByUsablePointer(const void* usable_pointer) {
  if (!MarkerEnabled()) return MarkerHealthy();
  if (usable_pointer == NULL) return true;
  LiveAllocation* allocation = FindByUsablePointer(usable_pointer);
  if (allocation == NULL) return LatchFailure();
  return RecordRelease(
      allocation->label,
      allocation->allocation_base,
      allocation->usable_pointer,
      allocation->allocation_bytes,
      allocation->usable_bytes,
      allocation->alignment);
}

inline bool RecordPageout(
    Label label,
    const void* allocation_base,
    const void* usable_pointer,
    std::uint64_t allocation_bytes,
    std::uint64_t usable_bytes,
    std::uint32_t alignment) {
  return Emit(
      kPageout,
      label,
      allocation_base,
      usable_pointer,
      allocation_bytes,
      usable_bytes,
      alignment);
}

}  // namespace gamma_allocation_marker

#endif
