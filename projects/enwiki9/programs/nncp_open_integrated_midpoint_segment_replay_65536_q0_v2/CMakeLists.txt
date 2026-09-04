cmake_minimum_required(VERSION 3.20)
project(nncp_open_integrated_midpoint_v2 LANGUAGES CXX)

add_library(midpoint_kernels STATIC midpoint_kernels.cpp)
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
