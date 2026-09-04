cmake_minimum_required(VERSION 3.20)
project(nncp_open_integrated_midpoint_v2 LANGUAGES CXX)

add_library(
  midpoint_kernels STATIC
  midpoint_kernels.cpp
  transformer_backward.cpp
  profile_backward.cpp
  profile_artifacts.cpp
  profile_forward.cpp
  tensor_container.cpp
  profile_fixture.cpp)
target_compile_features(midpoint_kernels PUBLIC cxx_std_20)
target_compile_options(
  midpoint_kernels
  PRIVATE
    -O2
    -Wall
    -Wextra
    -Werror
    -mavx2
    -mfma
    -fno-fast-math
    -ffp-contract=off
)
target_include_directories(midpoint_kernels PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

add_executable(midpoint_kernel_selftest kernel_selftest.cpp)
target_compile_features(midpoint_kernel_selftest PRIVATE cxx_std_20)
target_compile_options(
  midpoint_kernel_selftest
  PRIVATE
    -O2
    -Wall
    -Wextra
    -Werror
    -mavx2
    -mfma
    -fno-fast-math
    -ffp-contract=off
)
target_link_libraries(midpoint_kernel_selftest PRIVATE midpoint_kernels)

add_executable(midpoint_tensor_manifest tensor_manifest.cpp)
target_compile_features(midpoint_tensor_manifest PRIVATE cxx_std_20)
target_compile_options(
  midpoint_tensor_manifest
  PRIVATE
    -O2
    -Wall
    -Wextra
    -Werror
    -mavx2
    -mfma
    -fno-fast-math
    -ffp-contract=off
)
target_link_libraries(midpoint_tensor_manifest PRIVATE midpoint_kernels)

add_executable(midpoint_profile_treatment profile_treatment.cpp)
target_compile_features(midpoint_profile_treatment PRIVATE cxx_std_20)
target_compile_options(
  midpoint_profile_treatment
  PRIVATE
    -O2
    -Wall
    -Wextra
    -Werror
    -mavx2
    -mfma
    -fno-fast-math
    -ffp-contract=off
)
target_link_libraries(midpoint_profile_treatment PRIVATE midpoint_kernels)
