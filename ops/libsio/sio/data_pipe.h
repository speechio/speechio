#ifndef SIO_DATA_PIPE_H
#define SIO_DATA_PIPE_H

#include "sio/ptr.h"
#include "sio/check.h"
#include "sio/audio.h"
#include "sio/feature_extractor.h"

namespace sio {
struct DataPipe {
 public:
  explicit DataPipe(
    FeatureInfo& info
  ):
    feature_info(info),
    feature_extractor(feature_info)
  { }

  ~DataPipe() {
    if (resampler != nullptr) delete resampler;
  }

  void Forward(const float* samples, size_t num_samples, float sample_rate) {
    AudioSegment<const float> audio_seg(samples, num_samples, sample_rate);

    // Resampler
    kaldi::Vector<float> resampled;
    if SIO_UNLIKELY(sample_rate != feature_info.GetSamplingFrequency()) {
      if (resampler == nullptr) {
        resampler = new Resampler(sample_rate, feature_info.GetSamplingFrequency());
      } else if (sample_rate != resampler->SourceSampleRate()) {
        delete resampler;
        resampler = new Resampler(sample_rate, feature_info.GetSamplingFrequency());
      }
      resampler->Forward(
        audio_seg.samples,
        audio_seg.len,
        audio_seg.sample_rate,
        &resampled, false
      );

      audio_seg.samples = resampled.Data();
      audio_seg.len     = resampled.Dim();
      audio_seg.sample_rate = resampler->TargetSampleRate();
    }

    /* 
      possible other signal processing
    */

    // Feture extractor
    feature_extractor.Forward(
      audio_seg.samples,
      audio_seg.len,
      audio_seg.sample_rate
    );
  }

  void StopSession() { }

  FeatureInfo& feature_info;
  FeatureExtractor feature_extractor;
  Optional<Resampler*> resampler = nullptr;
}; // class DataPipe
}  // namespace sio
#endif
