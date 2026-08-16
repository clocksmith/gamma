cmake_minimum_required(VERSION 3.14)
project(nncp_open_profile_top_ff2_gradient_retry LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(GGML_BACKEND_DL OFF CACHE BOOL "" FORCE)
set(GGML_NATIVE OFF CACHE BOOL "" FORCE)
set(GGML_LTO OFF CACHE BOOL "" FORCE)
set(GGML_CCACHE OFF CACHE BOOL "" FORCE)
set(GGML_OPENMP OFF CACHE BOOL "" FORCE)
set(GGML_BLAS OFF CACHE BOOL "" FORCE)
set(GGML_LLAMAFILE OFF CACHE BOOL "" FORCE)
set(GGML_CPU_REPACK OFF CACHE BOOL "" FORCE)
set(GGML_ALL_WARNINGS OFF CACHE BOOL "" FORCE)

add_subdirectory(ggml)
add_executable(nncp_open_profile_forward profile_final_norm_forward.cpp)
target_compile_options(nncp_open_profile_forward PRIVATE -mavx2 -mfma)
target_link_libraries(nncp_open_profile_forward PRIVATE ggml)
add_executable(nncp_open_final_hidden_residual final_hidden_residual.cpp)
target_compile_options(nncp_open_final_hidden_residual PRIVATE -mavx2 -mfma)
add_executable(nncp_open_final_norm_backward final_norm_backward.cpp)
target_compile_options(nncp_open_final_norm_backward PRIVATE -mavx2 -mfma)


add_executable(nncp_open_top_ff2_gradient top_ff2_gradient.cpp)
target_compile_options(nncp_open_top_ff2_gradient PRIVATE -mavx2 -mfma)


