#include <algorithm>
#include <array>
#include <cerrno>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

namespace {

constexpr std::array<unsigned char, 4> kMagic = {'G', 'A', 'F', 'S'};
constexpr unsigned char kVersion = 1;
constexpr std::size_t kHeaderBytes = 14;
constexpr std::size_t kCopyBufferBytes = 1U << 20;

[[noreturn]] void Fail(const std::string& message) {
  throw std::runtime_error(message);
}

std::string ErrnoMessage(const std::string& operation) {
  return operation + ": " + std::strerror(errno);
}

class Fd {
 public:
  explicit Fd(int value = -1) : value_(value) {}
  ~Fd() {
    if (value_ >= 0) {
      ::close(value_);
    }
  }
  Fd(const Fd&) = delete;
  Fd& operator=(const Fd&) = delete;
  Fd(Fd&& other) noexcept : value_(std::exchange(other.value_, -1)) {}
  Fd& operator=(Fd&& other) noexcept {
    if (this != &other) {
      if (value_ >= 0) {
        ::close(value_);
      }
      value_ = std::exchange(other.value_, -1);
    }
    return *this;
  }
  int get() const { return value_; }
  int release() { return std::exchange(value_, -1); }

 private:
  int value_;
};

struct FileIdentity {
  dev_t device;
  ino_t inode;
  off_t bytes;
  timespec modified;
};

FileIdentity ReadIdentity(int fd, const std::string& label) {
  struct stat value {};
  if (::fstat(fd, &value) != 0) {
    Fail(ErrnoMessage("fstat " + label));
  }
  if (!S_ISREG(value.st_mode)) {
    Fail(label + " is not a regular file");
  }
  if (value.st_size < 0) {
    Fail(label + " has a negative size");
  }
  return {value.st_dev, value.st_ino, value.st_size, value.st_mtim};
}

bool SameIdentity(const FileIdentity& left, const FileIdentity& right) {
  return left.device == right.device && left.inode == right.inode &&
         left.bytes == right.bytes &&
         left.modified.tv_sec == right.modified.tv_sec &&
         left.modified.tv_nsec == right.modified.tv_nsec;
}

Fd OpenInput(const std::string& path, const std::string& label) {
  const int fd = ::open(path.c_str(), O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  if (fd < 0) {
    Fail(ErrnoMessage("open " + label));
  }
  Fd result(fd);
  ReadIdentity(result.get(), label);
  return result;
}

void WriteAll(int fd, const unsigned char* data, std::size_t bytes) {
  std::size_t offset = 0;
  while (offset < bytes) {
    const ssize_t written = ::write(fd, data + offset, bytes - offset);
    if (written < 0) {
      if (errno == EINTR) {
        continue;
      }
      Fail(ErrnoMessage("write output"));
    }
    if (written == 0) {
      Fail("write output returned zero");
    }
    offset += static_cast<std::size_t>(written);
  }
}

void ReadAll(int fd, unsigned char* data, std::size_t bytes) {
  std::size_t offset = 0;
  while (offset < bytes) {
    const ssize_t count = ::read(fd, data + offset, bytes - offset);
    if (count < 0) {
      if (errno == EINTR) {
        continue;
      }
      Fail(ErrnoMessage("read input"));
    }
    if (count == 0) {
      Fail("input ended before the declared length");
    }
    offset += static_cast<std::size_t>(count);
  }
}

void CopyExact(int input_fd, int output_fd, std::uint64_t bytes) {
  std::array<unsigned char, kCopyBufferBytes> buffer {};
  std::uint64_t remaining = bytes;
  while (remaining != 0) {
    const std::size_t request = static_cast<std::size_t>(
        std::min<std::uint64_t>(remaining, buffer.size()));
    ssize_t count = ::read(input_fd, buffer.data(), request);
    if (count < 0) {
      if (errno == EINTR) {
        continue;
      }
      Fail(ErrnoMessage("read payload"));
    }
    if (count == 0) {
      Fail("payload ended before its declared length");
    }
    WriteAll(output_fd, buffer.data(), static_cast<std::size_t>(count));
    remaining -= static_cast<std::uint64_t>(count);
  }
}

void FsyncDirectory(const std::filesystem::path& path) {
  const std::filesystem::path directory =
      path.has_parent_path() ? path.parent_path() : std::filesystem::path(".");
  const int fd = ::open(directory.c_str(), O_RDONLY | O_DIRECTORY | O_CLOEXEC);
  if (fd < 0) {
    Fail(ErrnoMessage("open output directory"));
  }
  Fd holder(fd);
  if (::fsync(holder.get()) != 0) {
    Fail(ErrnoMessage("fsync output directory"));
  }
}

class ExclusiveOutput {
 public:
  explicit ExclusiveOutput(std::filesystem::path final_path)
      : final_path_(std::move(final_path)),
        temporary_path_(final_path_.string() + ".gamma-tmp") {
    const int fd = ::open(temporary_path_.c_str(),
                          O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW,
                          0600);
    if (fd < 0) {
      Fail(ErrnoMessage("create temporary output"));
    }
    fd_ = Fd(fd);
  }

  ~ExclusiveOutput() {
    if (!committed_) {
      ::unlink(temporary_path_.c_str());
    }
  }

  int fd() const { return fd_.get(); }

  void Commit() {
    if (::fsync(fd_.get()) != 0) {
      Fail(ErrnoMessage("fsync temporary output"));
    }
    if (::close(fd_.release()) != 0) {
      Fail(ErrnoMessage("close temporary output"));
    }
    if (::link(temporary_path_.c_str(), final_path_.c_str()) != 0) {
      Fail(ErrnoMessage("commit output without overwrite"));
    }
    if (::unlink(temporary_path_.c_str()) != 0) {
      const int saved_errno = errno;
      ::unlink(final_path_.c_str());
      errno = saved_errno;
      Fail(ErrnoMessage("remove temporary output link"));
    }
    try {
      FsyncDirectory(final_path_);
    } catch (...) {
      if (::unlink(final_path_.c_str()) != 0 && errno != ENOENT) {
        Fail(ErrnoMessage("remove final output after directory fsync failure"));
      }
      try {
        FsyncDirectory(final_path_);
      } catch (...) {
      }
      throw;
    }
    committed_ = true;
  }

 private:
  std::filesystem::path final_path_;
  std::filesystem::path temporary_path_;
  Fd fd_;
  bool committed_ = false;
};

std::array<unsigned char, kHeaderBytes> MakeHeader(unsigned char mode,
                                                   std::uint64_t payload_bytes) {
  std::array<unsigned char, kHeaderBytes> header {};
  std::copy(kMagic.begin(), kMagic.end(), header.begin());
  header[4] = kVersion;
  header[5] = mode;
  for (unsigned int index = 0; index < 8; ++index) {
    header[6 + index] = static_cast<unsigned char>(
        (payload_bytes >> (index * 8U)) & 0xffU);
  }
  return header;
}

std::uint64_t ParseLength(const std::array<unsigned char, kHeaderBytes>& header) {
  std::uint64_t value = 0;
  for (unsigned int index = 0; index < 8; ++index) {
    value |= static_cast<std::uint64_t>(header[6 + index]) << (index * 8U);
  }
  return value;
}

int Create(const std::string& parent_path, const std::string& candidate_path,
           const std::string& output_path) {
  Fd parent = OpenInput(parent_path, "parent payload");
  Fd candidate = OpenInput(candidate_path, "candidate payload");
  const FileIdentity parent_before = ReadIdentity(parent.get(), "parent payload");
  const FileIdentity candidate_before = ReadIdentity(candidate.get(), "candidate payload");
  const bool choose_parent = parent_before.bytes <= candidate_before.bytes;
  const unsigned char mode = choose_parent ? 0 : 1;
  const FileIdentity selected_before = choose_parent ? parent_before : candidate_before;
  if (static_cast<std::uintmax_t>(selected_before.bytes) >
      std::numeric_limits<std::uint64_t>::max()) {
    Fail("selected payload is larger than the frame length field");
  }
  const std::uint64_t payload_bytes = static_cast<std::uint64_t>(selected_before.bytes);
  ExclusiveOutput output(output_path);
  const auto header = MakeHeader(mode, payload_bytes);
  WriteAll(output.fd(), header.data(), header.size());
  CopyExact(choose_parent ? parent.get() : candidate.get(), output.fd(), payload_bytes);
  const FileIdentity parent_after = ReadIdentity(parent.get(), "parent payload");
  const FileIdentity candidate_after = ReadIdentity(candidate.get(), "candidate payload");
  if (!SameIdentity(parent_before, parent_after) ||
      !SameIdentity(candidate_before, candidate_after)) {
    Fail("an input payload changed while framing");
  }
  output.Commit();
  std::cout << (choose_parent ? "P\n" : "C\n");
  return 0;
}

int Extract(const std::string& archive_path, const std::string& output_path) {
  Fd archive = OpenInput(archive_path, "framed archive");
  const FileIdentity before = ReadIdentity(archive.get(), "framed archive");
  if (static_cast<std::uint64_t>(before.bytes) < kHeaderBytes) {
    Fail("framed archive is shorter than its header");
  }
  std::array<unsigned char, kHeaderBytes> header {};
  ReadAll(archive.get(), header.data(), header.size());
  if (!std::equal(kMagic.begin(), kMagic.end(), header.begin())) {
    Fail("framed archive magic mismatch");
  }
  if (header[4] != kVersion) {
    Fail("framed archive version mismatch");
  }
  if (header[5] > 1) {
    Fail("framed archive mode is invalid");
  }
  const std::uint64_t payload_bytes = ParseLength(header);
  const std::uint64_t archive_bytes = static_cast<std::uint64_t>(before.bytes);
  if (payload_bytes != archive_bytes - kHeaderBytes) {
    Fail("framed archive length or trailing bytes mismatch");
  }
  ExclusiveOutput output(output_path);
  CopyExact(archive.get(), output.fd(), payload_bytes);
  const FileIdentity after = ReadIdentity(archive.get(), "framed archive");
  if (!SameIdentity(before, after)) {
    Fail("framed archive changed while extracting");
  }
  output.Commit();
  std::cout << (header[5] == 0 ? "P\n" : "C\n");
  return 0;
}

void Usage(const char* program) {
  std::cerr << "usage:\n"
            << "  " << program << " create P_PAYLOAD C_PAYLOAD OUTPUT\n"
            << "  " << program << " extract ARCHIVE OUTPUT\n";
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc == 5 && std::string_view(argv[1]) == "create") {
      return Create(argv[2], argv[3], argv[4]);
    }
    if (argc == 4 && std::string_view(argv[1]) == "extract") {
      return Extract(argv[2], argv[3]);
    }
    Usage(argv[0]);
    return 2;
  } catch (const std::exception& error) {
    std::cerr << "archive-select: " << error.what() << '\n';
    return 1;
  }
}
