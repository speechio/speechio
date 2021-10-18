cmake_minimum_required(VERSION 3.5 FATAL_ERROR)

project(sio CXX)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(SIO_VERSION_MAJOR 0)
set(SIO_VERSION_MINOR 1)
set(SIO_VERSION_PATCH 0)

set(SIO_ROOT ${CMAKE_SOURCE_DIR})
set(SIO_INC_DIR ${SIO_ROOT})
set(SIO_SRC_DIR ${SIO_ROOT}/sio)
set(SIO_BIN_DIR ${SIO_ROOT}/siobin)

# add abseil lib
add_subdirectory(${SIO_ROOT}/abseil-cpp)

# sio
include_directories(${SIO_INC_DIR})

add_subdirectory(${SIO_SRC_DIR})
add_subdirectory(${SIO_BIN_DIR})

add_executable(stt ${SIO_BIN_DIR}/stt.cc)
target_link_libraries(stt absl::strings absl::str_format absl::type_traits absl::flat_hash_map)

