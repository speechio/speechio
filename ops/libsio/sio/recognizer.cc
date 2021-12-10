#include "sio/type.h"
#include "sio/log.h"
#include "sio/check.h"
#include "sio/recognizer.h"
namespace sio {

int Recognizer::StartSession(const char* key) {
  return 0;
}

int Recognizer::AcceptAudioData(AudioFormat format, const void* data, size_t num_bytes) {
  float sample_rate;
  size_t sample_size;
  switch(format) {
    case AudioFormat::kFloatMono8k:
      sample_rate = 8000.0;
      sample_size = sizeof(float);
      break;
    case AudioFormat::kFloatMono16k:
      sample_rate = 16000.0;
      sample_size = sizeof(float);
      break;
    default:
      SIO_FATAL << "Unsupported audio format.";
  }

  SIO_P_COND(num_bytes % sample_size == 0);
  /* TODO: robustly handle (num_bytes % sizeof(float) != 0) */

  float* samples = (float*)data;
  size_t num_samples = num_bytes / sample_size;
  data_pipe_.Forward(sample_rate, samples, num_samples);

  return 0;
}

int Recognizer::StopSession() {
  return 0;
}

} // end of namespace sio
