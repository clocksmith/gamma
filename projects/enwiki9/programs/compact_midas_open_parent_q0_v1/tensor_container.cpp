#include "tensor_container.hpp"

#include <algorithm>
#include <cerrno>
#include <cmath>
#include <cstring>
#include <fcntl.h>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <utility>

namespace gamma_enwiki9::nncp {
namespace {

constexpr std::uint32_t kFileMagic = UINT32_C(0x23f4aefb);
constexpr std::uint32_t kTensorMagic = UINT32_C(0x23f4aefa);
constexpr std::uint32_t kF32 = 0;
constexpr std::uint32_t kBf16 = 1;
constexpr std::uint32_t kU32 = 5;
constexpr std::uint32_t kU16Type7 = 7;

std::size_t TypeSize(std::uint32_t type) {
  constexpr std::size_t sizes[] = {4, 2, 2, 1, 2, 4, 1, 2, 4};
  if (type >= std::size(sizes)) {
    throw std::runtime_error("unsupported tensor type " + std::to_string(type));
  }
  return sizes[type];
}

std::size_t CheckedMultiply(
    std::size_t left,
    std::size_t right,
    const char* label) {
  if (left == 0 || right == 0 ||
      left > std::numeric_limits<std::size_t>::max() / right) {
    throw std::runtime_error(std::string(label) + " overflows or is zero");
  }
  return left * right;
}

}  // namespace

class TensorContainer::Impl {
 public:
  explicit Impl(std::filesystem::path path) : path_(std::move(path)) {
    fd_ = open(path_.c_str(), O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd_ < 0) {
      throw std::runtime_error(
          "cannot open tensor container " + path_.string() + ": " +
          std::strerror(errno));
    }
    struct stat status {};
    if (fstat(fd_, &status) != 0 || !S_ISREG(status.st_mode) ||
        status.st_size <= 0 ||
        static_cast<std::uintmax_t>(status.st_size) >
            std::numeric_limits<std::size_t>::max()) {
      close(fd_);
      fd_ = -1;
      throw std::runtime_error("tensor container is not a nonempty regular file");
    }
    size_ = static_cast<std::size_t>(status.st_size);
    void* mapping = mmap(nullptr, size_, PROT_READ, MAP_PRIVATE, fd_, 0);
    if (mapping == MAP_FAILED) {
      const int failure = errno;
      close(fd_);
      fd_ = -1;
      throw std::runtime_error(
          "cannot map tensor container " + path_.string() + ": " +
          std::strerror(failure));
    }
    data_ = static_cast<const std::uint8_t*>(mapping);
    try {
      Parse();
    } catch (...) {
      munmap(const_cast<std::uint8_t*>(data_), size_);
      data_ = nullptr;
      close(fd_);
      fd_ = -1;
      throw;
    }
  }

  ~Impl() {
    if (data_ != nullptr) {
      munmap(const_cast<std::uint8_t*>(data_), size_);
    }
    if (fd_ >= 0) close(fd_);
  }

  struct Record {
    TensorMetadata metadata;
    std::size_t payload_offset;
  };

  const Record& Find(std::string_view name) const {
    const auto found = records_.find(std::string(name));
    if (found == records_.end()) {
      throw std::runtime_error(
          "missing tensor " + std::string(name) + " in " + path_.string());
    }
    return found->second;
  }

  void Require(
      const Record& record,
      std::uint32_t type,
      const std::vector<std::size_t>& dimensions) const {
    if (record.metadata.type != type || record.metadata.dimensions != dimensions) {
      throw std::runtime_error(
          "tensor type or dimensions differ for " + record.metadata.name);
    }
  }

  const std::uint8_t* Payload(const Record& record) const {
    return data_ + record.payload_offset;
  }

  const std::filesystem::path& path() const { return path_; }
  std::string_view configuration() const { return configuration_; }
  const std::vector<TensorMetadata>& tensors() const { return tensors_; }
  bool contains(std::string_view name) const {
    return records_.contains(std::string(name));
  }

 private:
  std::uint32_t ReadU32(std::size_t& offset) const {
    if (offset > size_ || size_ - offset < 4) {
      throw std::runtime_error("truncated u32 in " + path_.string());
    }
    const std::uint32_t value =
        static_cast<std::uint32_t>(data_[offset]) |
        (static_cast<std::uint32_t>(data_[offset + 1]) << 8U) |
        (static_cast<std::uint32_t>(data_[offset + 2]) << 16U) |
        (static_cast<std::uint32_t>(data_[offset + 3]) << 24U);
    offset += 4;
    return value;
  }

  void Parse() {
    std::size_t offset = 0;
    if (ReadU32(offset) != kFileMagic) {
      throw std::runtime_error("tensor container magic differs: " + path_.string());
    }
    const std::uint32_t configuration_size = ReadU32(offset);
    if (offset > size_ || size_ - offset < configuration_size) {
      throw std::runtime_error("truncated tensor-container configuration");
    }
    configuration_.assign(
        reinterpret_cast<const char*>(data_ + offset), configuration_size);
    offset += configuration_size;
    while (offset < size_) {
      if (ReadU32(offset) != kTensorMagic) {
        throw std::runtime_error("tensor marker differs in " + path_.string());
      }
      const std::uint32_t type = ReadU32(offset);
      const std::uint32_t rank = ReadU32(offset);
      const std::uint32_t name_size = ReadU32(offset);
      if (rank == 0 || rank > 8 || name_size == 0 || name_size > 4096) {
        throw std::runtime_error("invalid tensor header in " + path_.string());
      }
      std::vector<std::size_t> dimensions;
      dimensions.reserve(rank);
      std::size_t elements = 1;
      for (std::uint32_t axis = 0; axis < rank; ++axis) {
        const std::uint32_t dimension = ReadU32(offset);
        elements = CheckedMultiply(elements, dimension, "tensor element count");
        dimensions.push_back(dimension);
      }
      if (offset > size_ || size_ - offset < name_size) {
        throw std::runtime_error("truncated tensor name in " + path_.string());
      }
      std::string name(
          reinterpret_cast<const char*>(data_ + offset), name_size);
      offset += name_size;
      if (name.find('\0') != std::string::npos) {
        throw std::runtime_error("tensor name contains NUL in " + path_.string());
      }
      const std::size_t bytes =
          CheckedMultiply(elements, TypeSize(type), "tensor payload size");
      if (offset > size_ || size_ - offset < bytes) {
        throw std::runtime_error("truncated tensor payload for " + name);
      }
      TensorMetadata metadata{
          .name = name,
          .type = type,
          .dimensions = std::move(dimensions),
          .elements = elements,
          .bytes = bytes,
      };
      Record record{.metadata = metadata, .payload_offset = offset};
      if (!records_.emplace(name, std::move(record)).second) {
        throw std::runtime_error("duplicate tensor name " + name);
      }
      tensors_.push_back(std::move(metadata));
      offset += bytes;
    }
    if (offset != size_) {
      throw std::runtime_error("tensor container has trailing bytes");
    }
  }

  std::filesystem::path path_;
  int fd_ = -1;
  const std::uint8_t* data_ = nullptr;
  std::size_t size_ = 0;
  std::string configuration_;
  std::map<std::string, Record, std::less<>> records_;
  std::vector<TensorMetadata> tensors_;
};

TensorContainer::TensorContainer(const std::filesystem::path& path)
    : impl_(std::make_unique<Impl>(path)) {}

TensorContainer::~TensorContainer() = default;
TensorContainer::TensorContainer(TensorContainer&&) noexcept = default;
TensorContainer& TensorContainer::operator=(TensorContainer&&) noexcept = default;

const std::filesystem::path& TensorContainer::path() const {
  return impl_->path();
}

std::string_view TensorContainer::configuration() const {
  return impl_->configuration();
}

const std::vector<TensorMetadata>& TensorContainer::tensors() const {
  return impl_->tensors();
}

bool TensorContainer::contains(std::string_view name) const {
  return impl_->contains(name);
}

const TensorMetadata& TensorContainer::metadata(std::string_view name) const {
  return impl_->Find(name).metadata;
}

Bf16Buffer TensorContainer::CopyBf16(
    std::string_view name,
    const std::vector<std::size_t>& dimensions) const {
  const Impl::Record& record = impl_->Find(name);
  impl_->Require(record, kBf16, dimensions);
  Bf16Buffer output(record.metadata.elements);
  std::memcpy(output.data(), impl_->Payload(record), record.metadata.bytes);
  for (const Bf16 value : output) {
    if (!std::isfinite(Bf16ToFloat(value))) {
      throw std::runtime_error("non-finite BF16 tensor " + std::string(name));
    }
  }
  return output;
}

std::vector<float> TensorContainer::CopyF32(
    std::string_view name,
    const std::vector<std::size_t>& dimensions) const {
  const Impl::Record& record = impl_->Find(name);
  impl_->Require(record, kF32, dimensions);
  std::vector<float> output(record.metadata.elements);
  std::memcpy(output.data(), impl_->Payload(record), record.metadata.bytes);
  if (!std::all_of(output.begin(), output.end(), [](float value) {
        return std::isfinite(value);
      })) {
    throw std::runtime_error("non-finite F32 tensor " + std::string(name));
  }
  return output;
}

std::vector<std::uint32_t> TensorContainer::CopyU32(
    std::string_view name,
    const std::vector<std::size_t>& dimensions) const {
  const Impl::Record& record = impl_->Find(name);
  impl_->Require(record, kU32, dimensions);
  std::vector<std::uint32_t> output(record.metadata.elements);
  const std::uint8_t* source = impl_->Payload(record);
  for (std::size_t index = 0; index < output.size(); ++index) {
    output[index] =
        static_cast<std::uint32_t>(source[index * 4]) |
        (static_cast<std::uint32_t>(source[index * 4 + 1]) << 8U) |
        (static_cast<std::uint32_t>(source[index * 4 + 2]) << 16U) |
        (static_cast<std::uint32_t>(source[index * 4 + 3]) << 24U);
  }
  return output;
}

std::vector<std::uint16_t> TensorContainer::CopyU16Type7(
    std::string_view name,
    const std::vector<std::size_t>& dimensions) const {
  const Impl::Record& record = impl_->Find(name);
  impl_->Require(record, kU16Type7, dimensions);
  std::vector<std::uint16_t> output(record.metadata.elements);
  const std::uint8_t* source = impl_->Payload(record);
  for (std::size_t index = 0; index < output.size(); ++index) {
    output[index] =
        static_cast<std::uint16_t>(source[index * 2]) |
        static_cast<std::uint16_t>(source[index * 2 + 1] << 8U);
  }
  return output;
}

}  // namespace gamma_enwiki9::nncp
