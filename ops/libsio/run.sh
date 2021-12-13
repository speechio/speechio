cmake -S . -B build
cmake --build build -j 10
SIO_VERBOSITY=DEBUG  build/sio/unittest
SIO_VERBOSITY=DEBUG build/stt
