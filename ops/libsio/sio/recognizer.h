#ifndef SIO_RECOGNIZER_H
#define SIO_RECOGNIZER_H

#include "sio/audio.h"
#include "sio/data_pipe.h"

namespace sio {
class Recognizer {
 public:
  Recognizer(
    float old_sample_rate,
    float new_sample_rate,
    const FeatureExtractorInfo& feature_extractor_info
  ) :
    data_pipe_(
      old_sample_rate,
      new_sample_rate,
      feature_extractor_info
    )
  { }

  int StartSession(const char* key = nullptr);
  int AcceptAudio(float sample_rate, const float* samples, size_t num_samples);
  int StopSession();

 private:
  DataPipe data_pipe_;

}; // class Recognizer
}  // namespace sio
#endif
