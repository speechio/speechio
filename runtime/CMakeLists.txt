cmake_minimum_required(VERSION 3.5)
project(stt)

# Abseil requires C++11
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

## Import Abseil's CMake targets
#find_package(absl REQUIRED)
add_subdirectory(abseil-cpp)
add_subdirectory(sio)

add_executable(stt stt.cc)
target_link_libraries(stt absl::strings absl::flat_hash_map)
