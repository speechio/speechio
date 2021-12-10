#ifndef SIO_DATA_PIPE_H
#define SIO_DATA_PIPE_H

#include "sio/type.h"
#include "sio/str.h"
#include "sio/log.h"
#include "sio/feature_extractor.h"

namespace sio {

class DataPipe {
 public:
  explicit DataPipe(
    const FeatureExtractorInfo& feature_extractor_info
  ) :
    feature_extractor_(feature_extractor_info)
  { }

  void Forward(float sample_rate, const float* samples, size_t num_samples) {
    /* placeholder: resampler */

    /* placeholder: signal processing */

    feature_extractor_.Forward(sample_rate, samples, num_samples);
  }

  i32 NumFramesReady() const {
    return feature_extractor_.NumFramesReady();
  }

 private:
  FeatureExtractor feature_extractor_;

}; // class DataPipe
}  // namespace sio
#endif
