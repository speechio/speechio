cmake_minimum_required(VERSION 3.5)
project(sito)

# Abseil requires C++11
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

## Import Abseil's CMake targets
#find_package(absl REQUIRED)
add_subdirectory(third_party/abseil-cpp)

add_executable(sito sito.cc)
# Declare dependency on the absl::strings library
target_link_libraries(sito absl::strings absl::flat_hash_map)
