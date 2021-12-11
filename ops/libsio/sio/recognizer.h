#ifndef SIO_RECOGNIZER_H
#define SIO_RECOGNIZER_H

#include "sio/audio.h"
#include "sio/data_pipe.h"

namespace sio {
class Recognizer {
 public:
  Recognizer(
    float input_sample_rate,
    float model_sample_rate,
    const FeatureExtractorInfo& feature_extractor_info
  ) :
    data_pipe_(input_sample_rate, model_sample_rate, feature_extractor_info)
  { }

  int StartSession(const char* key = nullptr) { return 0; }
  int AcceptAudio(const float* samples, size_t num_samples, float sample_rate) {
    data_pipe_.Forward(samples, num_samples, sample_rate);
    return 0;
  }
  int StopSession() { return 0; }

 private:
  DataPipe data_pipe_;

}; // class Recognizer
}  // namespace sio
#endif
