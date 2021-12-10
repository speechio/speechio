#ifndef SIO_DATA_PIPE_H
#define SIO_DATA_PIPE_H

#include "sio/type.h"
#include "sio/str.h"
#include "sio/log.h"
#include "sio/feature_extractor.h"

namespace sio {

struct DataPipe {
 public:
  explicit DataPipe(
    const FeatureExtractorInfo& feature_extractor_info
  ) :
    feature_extractor(feature_extractor_info)
  { }

  void Forward(float sample_rate, const float* samples, size_t num_samples) {
    /* placeholder: resampler */

    /* placeholder: signal processing, e.g. agc */

    feature_extractor.Forward(sample_rate, samples, num_samples);
  }

  FeatureExtractor feature_extractor;
}; // class DataPipe
}  // namespace sio
#endif
