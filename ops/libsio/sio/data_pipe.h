#ifndef SIO_DATA_PIPE_H
#define SIO_DATA_PIPE_H

#include "sio/ptr.h"
#include "sio/audio.h"
#include "sio/feature_extractor.h"

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

  void Forward(const float* samples, size_t num_samples, float sample_rate) {
    AudioSegment<const float> audio_seg(samples, num_samples, sample_rate);

    // Resampler
    kaldi::Vector<float> resampled;
    if (resampler != nullptr) {
      resampler->Forward(
        audio_seg.samples,
        audio_seg.len,
        audio_seg.sample_rate,
        &resampled, false
      );

      /* possible other signal processing */

      audio_seg.samples = resampled.Data();
      audio_seg.len     = resampled.Dim();
      audio_seg.sample_rate = resampler->TargetSampleRate();
    }

    // Feture extractor
    feature_extractor.Forward(
      audio_seg.samples,
      audio_seg.len,
      audio_seg.sample_rate
    );
  }

  void StopSession() { }

  Optional<Resampler*> resampler = nullptr;
  FeatureExtractor feature_extractor;
}; // class DataPipe
}  // namespace sio
#endif
