# libsio
add_library(sio STATIC speech_to_text.cc)

# libsio unittest
add_executable(unittest 
  log_test.cc
  check_test.cc
  linked_list_test.cc
  heap_test.cc
  data_pipe_test.cc
)

target_link_libraries(unittest
  gtest_main
  sio
  absl::base
  ${KALDI_LIBS}
)

include(GoogleTest)
gtest_discover_tests(unittest)
