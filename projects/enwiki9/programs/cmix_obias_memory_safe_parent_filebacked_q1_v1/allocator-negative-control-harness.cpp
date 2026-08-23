#define GAMMA_FILEBACKED_FXCM 1
#define GAMMA_FILEBACKED_FXCM_TESTING 1
#include "gamma-filebacked-fxcm.h"

#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dirent.h>
#include <fcntl.h>
#include <string>
#include <sys/stat.h>
#include <unistd.h>

namespace {

constexpr size_t kFixtureBytes = gamma_filebacked_fxcm::kMinimumBackedBytes;

[[noreturn]] void HarnessFail(const char* message) {
  std::fprintf(stderr, "allocator harness failure: %s errno=%d\n", message, errno);
  std::exit(90);
}

void BindScratch(const char* path) {
  if (setenv("GAMMA_FXCM_BACKING_DIR", path, 1) != 0) {
    HarnessFail("set backing directory");
  }
}

void* AllocateFixture(size_t alignment = 128) {
  return gamma_filebacked_fxcm::AllocateBacked(
      kFixtureBytes + alignment,
      kFixtureBytes,
      alignment);
}

int ReserveFailure(int, off_t, off_t) {
  errno = ENOSPC;
  return ENOSPC;
}

int PageoutFailure(void*, size_t, int) {
  errno = EIO;
  return -1;
}

int UnmapFailure(void*, size_t) {
  errno = EIO;
  return -1;
}

void CreateFilenameCollision(int directory, const char* name) {
  const int descriptor = openat(
      directory, name,
      O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC | O_RDWR, 0600);
  if (descriptor < 0) HarnessFail("create post-empty-check filename collision");
  if (close(descriptor) != 0) HarnessFail("close filename collision file");
}

bool DirectoryEmpty(const char* path) {
  DIR* directory = opendir(path);
  if (directory == nullptr) HarnessFail("open scratch directory after release");
  bool empty = true;
  errno = 0;
  while (dirent* entry = readdir(directory)) {
    if (std::strcmp(entry->d_name, ".") != 0 &&
        std::strcmp(entry->d_name, "..") != 0) {
      empty = false;
    }
  }
  if (errno != 0 || closedir(directory) != 0) {
    HarnessFail("scan scratch directory after release");
  }
  return empty;
}

int Positive(const char* scratch) {
  BindScratch(scratch);
  void* base = AllocateFixture();
  const auto& mapping = gamma_filebacked_fxcm::mappings[0];
  if (mapping.base != base || mapping.usable_pointer == nullptr ||
      reinterpret_cast<uintptr_t>(mapping.usable_pointer) % mapping.alignment != 0 ||
      mapping.requested_bytes != kFixtureBytes ||
      !mapping.mapped || !mapping.backing_file_live) {
    HarnessFail("positive allocation geometry");
  }
  const unsigned char* bytes = static_cast<const unsigned char*>(mapping.usable_pointer);
  for (size_t index = 0; index < mapping.requested_bytes; ++index) {
    if (bytes[index] != 0) HarnessFail("nonzero byte in new mapping");
  }
  unsigned char* writable = static_cast<unsigned char*>(mapping.usable_pointer);
  for (size_t index = 0; index < mapping.requested_bytes; index += 4096) {
    writable[index] = static_cast<unsigned char>((index >> 12) & 0xffU);
  }
  gamma_filebacked_fxcm::PageOutAll(true);
  for (size_t index = 0; index < mapping.requested_bytes; index += 4096) {
    const unsigned char expected = static_cast<unsigned char>((index >> 12) & 0xffU);
    if (writable[index] != expected) HarnessFail("mapping bytes changed after pageout");
  }
  gamma_filebacked_fxcm::Release(base);
  if (!DirectoryEmpty(scratch)) HarnessFail("scratch directory not empty after release");
  std::printf("positive allocator fixture passed\n");
  return 0;
}

int InodeReplacement(const char* scratch) {
  BindScratch(scratch);
  void* base = AllocateFixture();
  const std::string original = std::string(scratch) + "/fxcm-0000.bin";
  const std::string retained = std::string(scratch) + "/retained-original.bin";
  if (rename(original.c_str(), retained.c_str()) != 0) {
    HarnessFail("retain original backing file");
  }
  const int replacement = open(original.c_str(),
      O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC | O_RDWR, 0600);
  if (replacement < 0 || close(replacement) != 0) {
    HarnessFail("create replacement backing file");
  }
  gamma_filebacked_fxcm::Release(base);
  HarnessFail("inode replacement was not rejected");
}

}  // namespace

int main(int argc, char** argv) {
  if (argc < 2 || argc > 3) {
    std::fprintf(stderr, "usage: %s CONTROL [SCRATCH]\n", argv[0]);
    return 64;
  }
  const char* control = argv[1];
  const char* scratch = argc == 3 ? argv[2] : nullptr;

  if (std::strcmp(control, "missing_environment") == 0) {
    unsetenv("GAMMA_FXCM_BACKING_DIR");
    AllocateFixture();
  }
  if (scratch == nullptr) {
    std::fprintf(stderr, "control requires scratch path\n");
    return 64;
  }
  if (std::strcmp(control, "positive") == 0) return Positive(scratch);

  BindScratch(scratch);
  if (std::strcmp(control, "reserve_failure") == 0) {
    auto replacement = gamma_filebacked_fxcm::hooks;
    replacement.reserve = ReserveFailure;
    gamma_filebacked_fxcm::InstallHooksForTesting(replacement);
    AllocateFixture();
  } else if (std::strcmp(control, "registry_overflow") == 0) {
    gamma_filebacked_fxcm::ForceMappingCountForTesting(
        gamma_filebacked_fxcm::kMaximumMappings);
    AllocateFixture();
  } else if (std::strcmp(control, "interior_pointer_free") == 0) {
    unsigned char* base = static_cast<unsigned char*>(AllocateFixture());
    gamma_filebacked_fxcm::Release(base + 1);
  } else if (std::strcmp(control, "inode_replacement") == 0) {
    return InodeReplacement(scratch);
  } else if (std::strcmp(control, "pageout_failure") == 0) {
    auto replacement = gamma_filebacked_fxcm::hooks;
    replacement.pageout = PageoutFailure;
    gamma_filebacked_fxcm::InstallHooksForTesting(replacement);
    AllocateFixture();
    gamma_filebacked_fxcm::PageOutAll(true);
  } else if (std::strcmp(control, "terminal_cleanup_failure") == 0) {
    AllocateFixture();
    auto replacement = gamma_filebacked_fxcm::hooks;
    replacement.unmap = UnmapFailure;
    gamma_filebacked_fxcm::InstallHooksForTesting(replacement);
    std::exit(0);
  } else if (std::strcmp(control, "filename_collision") == 0) {
    auto replacement = gamma_filebacked_fxcm::hooks;
    replacement.before_create = CreateFilenameCollision;
    gamma_filebacked_fxcm::InstallHooksForTesting(replacement);
    AllocateFixture();
  } else if (
      std::strcmp(control, "relative_path") == 0 ||
      std::strcmp(control, "dot_component") == 0 ||
      std::strcmp(control, "dotdot_component") == 0 ||
      std::strcmp(control, "repeated_separator") == 0 ||
      std::strcmp(control, "trailing_separator") == 0 ||
      std::strcmp(control, "symlink_component") == 0 ||
      std::strcmp(control, "nonempty_directory") == 0) {
    AllocateFixture();
  } else {
    std::fprintf(stderr, "unknown control: %s\n", control);
    return 64;
  }

  HarnessFail("negative control unexpectedly returned");
}
