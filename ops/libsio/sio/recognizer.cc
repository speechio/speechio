#include "sio/log.h"
#include "sio/check.h"
#include "sio/recognizer.h"
namespace sio {

int Recognizer::StartSession(const char* key) {
  return 0;
}

int Recognizer::AcceptAudio(float sample_rate, const float* samples, size_t num_samples) {
  data_pipe_.Forward(sample_rate, samples, num_samples);

  return 0;
}

int Recognizer::StopSession() {
  return 0;
}

} // end of namespace sio
