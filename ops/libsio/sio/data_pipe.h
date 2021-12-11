#ifndef SIO_DATA_PIPE_H
#define SIO_DATA_PIPE_H

#include "sio/audio.h"
#include "sio/feature_extractor.h"

#include "sio/ptr.h"
namespace sio {

struct DataPipe {
 public:
  explicit DataPipe(
    float input_sample_rate,
    float model_sample_rate,
    const FeatureExtractorInfo& feature_extractor_info
  ):
    feature_extractor(feature_extractor_info)
  {
    if (input_sample_rate != model_sample_rate) 
      resampler = new Resampler(input_sample_rate, model_sample_rate);
  }

  ~DataPipe() {
    if (resampler != nullptr) delete resampler;
  }

  void Forward(float sample_rate, const float* samples, size_t num_samples) {
    // Resampler
    kaldi::Vector<float> resampled;
    if (resampler != nullptr) {
      resampler->Forward(sample_rate, samples, num_samples, &resampled, false);

      sample_rate = resampler->TargetSampleRate();
      samples = resampled.Data();
      num_samples = resampled.Dim();
    }

    // Feture extractor
    feature_extractor.Forward(
      sample_rate,
      samples,
      num_samples
    );
  }

  void StopSession() { }

  Optional<Resampler*> resampler = nullptr;
  FeatureExtractor feature_extractor;
}; // class DataPipe
}  // namespace sio
#endif
