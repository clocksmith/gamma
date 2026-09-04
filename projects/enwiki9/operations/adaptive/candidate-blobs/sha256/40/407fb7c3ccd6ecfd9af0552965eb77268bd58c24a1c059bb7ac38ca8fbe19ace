#ifndef GAMMA_ENWIKI9_NNCP_TENSOR_CONTAINER_HPP
#define GAMMA_ENWIKI9_NNCP_TENSOR_CONTAINER_HPP

#include "midpoint_kernels.hpp"

#include <cstdint>
#include <filesystem>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace gamma_enwiki9::nncp {

struct TensorMetadata {
  std::string name;
  std::uint32_t type;
  std::vector<std::size_t> dimensions;
  std::size_t elements;
  std::size_t bytes;
};

class TensorContainer {
 public:
  explicit TensorContainer(const std::filesystem::path& path);
  ~TensorContainer();

  TensorContainer(const TensorContainer&) = delete;
  TensorContainer& operator=(const TensorContainer&) = delete;
  TensorContainer(TensorContainer&&) noexcept;
  TensorContainer& operator=(TensorContainer&&) noexcept;

  const std::filesystem::path& path() const;
  std::string_view configuration() const;
  const std::vector<TensorMetadata>& tensors() const;
  bool contains(std::string_view name) const;
  const TensorMetadata& metadata(std::string_view name) const;

  Bf16Buffer CopyBf16(
      std::string_view name,
      const std::vector<std::size_t>& dimensions) const;
  std::vector<float> CopyF32(
      std::string_view name,
      const std::vector<std::size_t>& dimensions) const;
  std::vector<std::uint32_t> CopyU32(
      std::string_view name,
      const std::vector<std::size_t>& dimensions) const;

 private:
  class Impl;
  std::unique_ptr<Impl> impl_;
};

}  // namespace gamma_enwiki9::nncp

#endif
