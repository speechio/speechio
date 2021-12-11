export SIO_VERBOSITY=DEBUG
cmake -S . -B build
cmake --build build -j 10
SIO_VERBOSITY=DEBUG build/sio/unittest
build/stt
