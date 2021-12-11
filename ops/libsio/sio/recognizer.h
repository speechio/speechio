#ifndef SIO_RECOGNIZER_H
#define SIO_RECOGNIZER_H

#include <cstddef>

#include "sio/feature_extractor.h"
#include "sio/data_pipe.h"

namespace sio {
class Recognizer {
 public:
  Recognizer(
    FeatureInfo& feature_info
  ) :
    data_pipe_(feature_info)
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
