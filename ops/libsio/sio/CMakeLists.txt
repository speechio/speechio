# libsio
add_library(sio STATIC
  link.cc
  feature_extractor.cc
  data_pipe.cc
  recognizer.cc
  speech_to_text.cc
)

# libsio unittest
add_executable(unittest 
  log_test.cc
  check_test.cc
  link_test.cc
  list_test.cc
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
