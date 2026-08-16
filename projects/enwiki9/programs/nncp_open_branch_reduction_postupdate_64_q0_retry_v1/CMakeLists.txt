cmake_minimum_required(VERSION 3.16)
project(nncp_open_branch_reduction_postupdate LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(nncp_open_branch_reduction_postupdate branch_reduction.cpp)
target_compile_options(nncp_open_branch_reduction_postupdate PRIVATE -mavx2 -mfma)

