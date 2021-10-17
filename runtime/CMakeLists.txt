cmake_minimum_required(VERSION 3.5)
project(stt)

# Abseil requires C++11
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

## Import Abseil's CMake targets
#find_package(absl REQUIRED)
add_subdirectory(${CMAKE_SOURCE_DIR}/abseil-cpp)

include_directories(${CMAKE_SOURCE_DIR})
add_subdirectory(${CMAKE_SOURCE_DIR}/sio)
add_executable(stt sio/stt.cc)
target_link_libraries(stt absl::strings absl::str_format absl::type_traits absl::flat_hash_map)
