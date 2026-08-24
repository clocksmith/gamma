#pragma once

#ifdef GAMMA_FULL_IDENTITY_OBSERVER

#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <limits>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

namespace gamma_full_identity {

#ifndef GAMMA_FULL_IDENTITY_MINIMUM_SEMANTIC_BYTES
#define GAMMA_FULL_IDENTITY_MINIMUM_SEMANTIC_BYTES (64ULL * 1024ULL * 1024ULL)
#endif
#ifndef GAMMA_FULL_IDENTITY_EXPECTED_RANGES
#define GAMMA_FULL_IDENTITY_EXPECTED_RANGES 26
#endif

inline constexpr size_t kMinimumSemanticBytes =
    static_cast<size_t>(GAMMA_FULL_IDENTITY_MINIMUM_SEMANTIC_BYTES);
inline constexpr size_t kExpectedRanges =
    static_cast<size_t>(GAMMA_FULL_IDENTITY_EXPECTED_RANGES);
inline constexpr size_t kMaximumRanges = 64;
static_assert(kExpectedRanges > 0 && kExpectedRanges <= kMaximumRanges,
              "semantic range count must fit observer registry");
inline constexpr uint64_t kFixedCheckpoints[] = {
    16777216ULL,
    33554432ULL,
    50331648ULL,
};

[[noreturn]] inline void Fail(const char* operation) {
  dprintf(STDERR_FILENO,
          "GAMMA_FULL_IDENTITY_OBSERVER failure operation=%s errno=%d\n",
          operation, errno);
  std::_Exit(86);
}

struct Sha256 {
  uint32_t h[8];
  uint64_t bytes;
  unsigned char block[64];
  size_t used;

  Sha256()
      : h{0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
          0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U},
        bytes(0), block{}, used(0) {}

  static uint32_t Rotate(uint32_t value, unsigned int count) {
    return (value >> count) | (value << (32U - count));
  }

  void Transform(const unsigned char* data) {
    static constexpr uint32_t k[64] = {
      0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,
      0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,
      0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,
      0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,
      0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,
      0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,
      0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,
      0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,
      0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,
      0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,
      0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,
      0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,
      0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,
      0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,
      0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,
      0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U,
    };
    uint32_t w[64];
    for (size_t i = 0; i < 16; ++i) {
      w[i] = (static_cast<uint32_t>(data[4 * i]) << 24) |
             (static_cast<uint32_t>(data[4 * i + 1]) << 16) |
             (static_cast<uint32_t>(data[4 * i + 2]) << 8) |
             static_cast<uint32_t>(data[4 * i + 3]);
    }
    for (size_t i = 16; i < 64; ++i) {
      const uint32_t s0 = Rotate(w[i - 15], 7) ^ Rotate(w[i - 15], 18) ^
                          (w[i - 15] >> 3);
      const uint32_t s1 = Rotate(w[i - 2], 17) ^ Rotate(w[i - 2], 19) ^
                          (w[i - 2] >> 10);
      w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    uint32_t a = h[0], b = h[1], c = h[2], d = h[3];
    uint32_t e = h[4], f = h[5], g = h[6], hh = h[7];
    for (size_t i = 0; i < 64; ++i) {
      const uint32_t s1 = Rotate(e, 6) ^ Rotate(e, 11) ^ Rotate(e, 25);
      const uint32_t choice = (e & f) ^ ((~e) & g);
      const uint32_t t1 = hh + s1 + choice + k[i] + w[i];
      const uint32_t s0 = Rotate(a, 2) ^ Rotate(a, 13) ^ Rotate(a, 22);
      const uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
      const uint32_t t2 = s0 + majority;
      hh = g; g = f; f = e; e = d + t1;
      d = c; c = b; b = a; a = t1 + t2;
    }
    h[0] += a; h[1] += b; h[2] += c; h[3] += d;
    h[4] += e; h[5] += f; h[6] += g; h[7] += hh;
  }

  void Update(const void* source, size_t length) {
    const auto* data = static_cast<const unsigned char*>(source);
    if (length > std::numeric_limits<uint64_t>::max() - bytes) {
      Fail("sha256 length overflow");
    }
    bytes += length;
    while (length > 0) {
      const size_t take = length < sizeof(block) - used
                              ? length : sizeof(block) - used;
      std::memcpy(block + used, data, take);
      used += take;
      data += take;
      length -= take;
      if (used == sizeof(block)) {
        Transform(block);
        used = 0;
      }
    }
  }

  void Final(unsigned char digest[32]) {
    const uint64_t bit_count = bytes * 8ULL;
    block[used++] = 0x80U;
    if (used > 56) {
      std::memset(block + used, 0, sizeof(block) - used);
      Transform(block);
      used = 0;
    }
    std::memset(block + used, 0, 56 - used);
    for (size_t i = 0; i < 8; ++i) {
      block[63 - i] = static_cast<unsigned char>(bit_count >> (8 * i));
    }
    Transform(block);
    for (size_t i = 0; i < 8; ++i) {
      digest[4 * i] = static_cast<unsigned char>(h[i] >> 24);
      digest[4 * i + 1] = static_cast<unsigned char>(h[i] >> 16);
      digest[4 * i + 2] = static_cast<unsigned char>(h[i] >> 8);
      digest[4 * i + 3] = static_cast<unsigned char>(h[i]);
    }
  }
};

inline void Hex(const unsigned char digest[32], char output[65]) {
  static constexpr char alphabet[] = "0123456789abcdef";
  for (size_t i = 0; i < 32; ++i) {
    output[2 * i] = alphabet[digest[i] >> 4];
    output[2 * i + 1] = alphabet[digest[i] & 15U];
  }
  output[64] = '\0';
}

inline void DigestHex(Sha256 source, char output[65]) {
  unsigned char digest[32];
  source.Final(digest);
  Hex(digest, output);
}

struct SemanticRange {
  const unsigned char* data;
  size_t bytes;
  size_t alignment;
};

inline SemanticRange ranges[kMaximumRanges] = {};
inline size_t range_count = 0;
inline Sha256 probability;
inline uint64_t coded_bits = 0;
inline uint64_t completed_bytes = 0;
inline int output_dir_fd = -1;
inline FILE* state_file = nullptr;
inline FILE* coder_file = nullptr;
inline bool enabled = false;
inline bool begun = false;
inline bool finished = false;

inline void RegisterSemanticRange(const void* pointer, size_t bytes,
                                  size_t alignment) {
  if (bytes < kMinimumSemanticBytes) return;
  if (pointer == nullptr || bytes == 0 || alignment == 0 ||
      (alignment & (alignment - 1)) != 0 || range_count >= kMaximumRanges) {
    Fail("invalid semantic range registration");
  }
  ranges[range_count++] = {
      static_cast<const unsigned char*>(pointer), bytes, alignment};
}

inline int OpenOutputDirectory() {
  const char* path = std::getenv("GAMMA_FULL_IDENTITY_DIR");
  if (path == nullptr || path[0] != '/') Fail("missing absolute output directory");
  int current = open("/", O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
  if (current < 0) Fail("open output root");
  const char* cursor = path + 1;
  while (*cursor != '\0') {
    const char* slash = std::strchr(cursor, '/');
    const size_t length = slash == nullptr ? std::strlen(cursor)
                                           : static_cast<size_t>(slash - cursor);
    if (length == 0 || length > 255 ||
        (length == 1 && cursor[0] == '.') ||
        (length == 2 && cursor[0] == '.' && cursor[1] == '.')) {
      close(current);
      Fail("noncanonical output directory");
    }
    char component[256];
    std::memcpy(component, cursor, length);
    component[length] = '\0';
    const int next = openat(current, component,
        O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (next < 0) {
      close(current);
      Fail("open output directory component");
    }
    if (close(current) != 0) {
      close(next);
      Fail("close output directory component");
    }
    current = next;
    if (slash == nullptr) break;
    cursor = slash + 1;
  }
  return current;
}

inline FILE* NewOutput(const char* name) {
  const int descriptor = openat(output_dir_fd, name,
      O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
  if (descriptor < 0) Fail("create observer output");
  FILE* stream = fdopen(descriptor, "wb");
  if (stream == nullptr) {
    close(descriptor);
    Fail("open observer output stream");
  }
  return stream;
}

inline void UpdateU64(Sha256* hash, uint64_t value) {
  unsigned char encoded[8];
  for (size_t i = 0; i < sizeof(encoded); ++i) {
    encoded[i] = static_cast<unsigned char>(value >> (8 * i));
  }
  hash->Update(encoded, sizeof(encoded));
}

inline void DropQ1Pages(const SemanticRange& range) {
#ifdef GAMMA_FILEBACKED_FXCM
  const long page_value = sysconf(_SC_PAGESIZE);
  if (page_value <= 0) Fail("read page size");
  const uintptr_t page = static_cast<uintptr_t>(page_value);
  const uintptr_t address = reinterpret_cast<uintptr_t>(range.data);
  const uintptr_t begin = address & ~(page - 1U);
  if (address > std::numeric_limits<uintptr_t>::max() - range.bytes) {
    Fail("semantic range end overflow");
  }
  const uintptr_t end_unrounded = address + range.bytes;
  if (end_unrounded > std::numeric_limits<uintptr_t>::max() - (page - 1U)) {
    Fail("semantic range page rounding overflow");
  }
  const uintptr_t end = (end_unrounded + page - 1U) & ~(page - 1U);
  if (madvise(reinterpret_cast<void*>(begin), end - begin, MADV_PAGEOUT) != 0) {
    Fail("page out hashed q1 semantic range");
  }
#else
  (void)range;
#endif
}

inline void SnapshotState(uint64_t checkpoint, const char* kind) {
  if (range_count != kExpectedRanges || state_file == nullptr) {
    Fail("incomplete semantic range registry");
  }
  Sha256 manifest;
  for (size_t ordinal = 0; ordinal < range_count; ++ordinal) {
    const SemanticRange& range = ranges[ordinal];
    Sha256 range_hash;
    UpdateU64(&range_hash, ordinal);
    UpdateU64(&range_hash, range.bytes);
    UpdateU64(&range_hash, range.alignment);
    constexpr size_t chunk_bytes = 8ULL * 1024ULL * 1024ULL;
    size_t offset = 0;
    while (offset < range.bytes) {
      const size_t remaining = range.bytes - offset;
      const size_t take = remaining < chunk_bytes ? remaining : chunk_bytes;
      range_hash.Update(range.data + offset, take);
      offset += take;
    }
    unsigned char digest[32];
    range_hash.Final(digest);
    UpdateU64(&manifest, ordinal);
    UpdateU64(&manifest, range.bytes);
    UpdateU64(&manifest, range.alignment);
    manifest.Update(digest, sizeof(digest));
    char hex[65];
    Hex(digest, hex);
    if (std::fprintf(state_file,
        "{\"alignment\":%zu,\"bytes\":%zu,\"checkpoint\":%llu,"
        "\"kind\":\"%s\",\"ordinal\":%zu,\"sha256\":\"%s\"}\n",
        range.alignment, range.bytes,
        static_cast<unsigned long long>(checkpoint), kind, ordinal, hex) < 0) {
      Fail("write state range record");
    }
    DropQ1Pages(range);
  }
  char aggregate[65];
  DigestHex(manifest, aggregate);
  if (std::fprintf(state_file,
      "{\"allocation_count\":%zu,\"checkpoint\":%llu,\"kind\":\"%s\","
      "\"manifest_sha256\":\"%s\"}\n",
      range_count, static_cast<unsigned long long>(checkpoint), kind,
      aggregate) < 0 || std::fflush(state_file) != 0) {
    Fail("write state checkpoint summary");
  }
}

inline void CoderCheckpoint(uint64_t checkpoint, const char* kind,
                            uint32_t x1, uint32_t x2,
                            size_t payload_bytes) {
  char digest[65];
  DigestHex(probability, digest);
  if (coder_file == nullptr || std::fprintf(coder_file,
      "{\"coded_bits\":%llu,\"completed_coded_bytes\":%llu,"
      "\"high\":%u,\"kind\":\"%s\",\"low\":%u,"
      "\"payload_bytes\":%zu,\"probability_sha256\":\"%s\"}\n",
      static_cast<unsigned long long>(coded_bits),
      static_cast<unsigned long long>(checkpoint), x2, kind, x1,
      payload_bytes, digest) < 0 || std::fflush(coder_file) != 0) {
    Fail("write coder checkpoint");
  }
}

inline void Begin(uint32_t x1, uint32_t x2, size_t payload_bytes) {
  const char* configured = std::getenv("GAMMA_FULL_IDENTITY_DIR");
  if (configured == nullptr || configured[0] == '\0') return;
  if (begun || finished || range_count != kExpectedRanges) {
    Fail("invalid observer begin state");
  }
  enabled = true;
  output_dir_fd = OpenOutputDirectory();
  state_file = NewOutput("persistent-state.jsonl");
  coder_file = NewOutput("coder-checkpoints.jsonl");
  begun = true;
  SnapshotState(0, "start");
  CoderCheckpoint(0, "start", x1, x2, payload_bytes);
}

inline void ObserveProbability(unsigned int value) {
  if (!enabled) return;
  if (!begun || finished || value < 1 || value > 65534) {
    Fail("invalid probability observation");
  }
  const unsigned char encoded[2] = {
      static_cast<unsigned char>(value),
      static_cast<unsigned char>(value >> 8),
  };
  probability.Update(encoded, sizeof(encoded));
  ++coded_bits;
}

inline void CompletedByte(uint32_t x1, uint32_t x2, size_t payload_bytes) {
  if (!enabled) return;
  if (!begun || finished || coded_bits != (completed_bytes + 1ULL) * 8ULL) {
    Fail("coded byte counter mismatch");
  }
  ++completed_bytes;
  for (const uint64_t checkpoint : kFixedCheckpoints) {
    if (completed_bytes == checkpoint) {
      SnapshotState(checkpoint, "fixed");
      CoderCheckpoint(checkpoint, "fixed", x1, x2, payload_bytes);
    }
  }
}

inline void Finish(uint32_t x1, uint32_t x2, size_t payload_bytes) {
  if (!enabled) return;
  if (!begun || finished || coded_bits != completed_bytes * 8ULL) {
    Fail("invalid observer finish state");
  }
  SnapshotState(completed_bytes, "terminal");
  CoderCheckpoint(completed_bytes, "terminal", x1, x2, payload_bytes);
  FILE* summary = NewOutput("probability.json");
  char digest[65];
  DigestHex(probability, digest);
  if (std::fprintf(summary,
      "{\"coded_bits\":%llu,\"completed_coded_bytes\":%llu,"
      "\"post_head_probability_sha256\":\"%s\"}\n",
      static_cast<unsigned long long>(coded_bits),
      static_cast<unsigned long long>(completed_bytes), digest) < 0 ||
      std::fflush(summary) != 0 || fsync(fileno(summary)) != 0 ||
      std::fclose(summary) != 0) {
    Fail("finalize probability summary");
  }
  if (std::fflush(state_file) != 0 || fsync(fileno(state_file)) != 0 ||
      std::fclose(state_file) != 0 || std::fflush(coder_file) != 0 ||
      fsync(fileno(coder_file)) != 0 || std::fclose(coder_file) != 0 ||
      fsync(output_dir_fd) != 0 || close(output_dir_fd) != 0) {
    Fail("finalize observer outputs");
  }
  state_file = nullptr;
  coder_file = nullptr;
  output_dir_fd = -1;
  finished = true;
}

inline void CopyFileFromEnvironment(const char* environment_name,
                                    const char* source_path) {
  const char* destination = std::getenv(environment_name);
  if (destination == nullptr || destination[0] == '\0') return;
  if (destination[0] != '/') Fail("copy destination is not absolute");
  const int source = open(source_path, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
  if (source < 0) Fail("open transformed stream source");
  const int target = open(destination,
      O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
  if (target < 0) {
    close(source);
    Fail("create transformed stream destination");
  }
  unsigned char buffer[1 << 20];
  while (true) {
    const ssize_t got = read(source, buffer, sizeof(buffer));
    if (got < 0 && errno == EINTR) continue;
    if (got < 0) Fail("read transformed stream");
    if (got == 0) break;
    size_t offset = 0;
    while (offset < static_cast<size_t>(got)) {
      const ssize_t written = write(target, buffer + offset,
                                    static_cast<size_t>(got) - offset);
      if (written < 0 && errno == EINTR) continue;
      if (written <= 0) Fail("write transformed stream");
      offset += static_cast<size_t>(written);
    }
  }
  if (fsync(target) != 0 || close(target) != 0 || close(source) != 0) {
    Fail("finalize transformed stream copy");
  }
}

}  // namespace gamma_full_identity

#endif  // GAMMA_FULL_IDENTITY_OBSERVER
