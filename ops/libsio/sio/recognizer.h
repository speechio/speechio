#ifndef SIO_RECOGNIZER_H
#define SIO_RECOGNIZER_H

#include <cstddef>

#include "sio/ptr.h"
#include "sio/check.h"
#include "sio/audio.h"
#include "sio/feature.h"

namespace sio {
class Recognizer {
 public:
  Recognizer(
    FeatureInfo& feature_info
  ) :
    feature_info_(feature_info),
    feature_extractor_(feature_info)
  { }

  ~Recognizer() {
    if (resampler_ != nullptr) delete resampler_;
  }

  int StartSession(const char* key = nullptr) { return 0; }

  int Speech(const float* data, size_t len, float sample_rate) {
    AudioSegment<const float> audio_seg(data, len, sample_rate);

    // Resampler
    kaldi::Vector<float> resampled;
    if SIO_UNLIKELY(sample_rate != feature_info_.GetSamplingFrequency()) {
      if (resampler_ == nullptr || sample_rate != resampler_->SourceSampleRate()) {
        delete resampler_;
        resampler_ = new Resampler(sample_rate, feature_info_.GetSamplingFrequency());
      }

      resampler_->Forward(
        audio_seg.data,
        audio_seg.len,
        audio_seg.sample_rate,
        &resampled, false
      );

      audio_seg.data = resampled.Data();
      audio_seg.len  = resampled.Dim();
      audio_seg.sample_rate = resampler_->TargetSampleRate();
    }

    /* 
      possible other signal processing
    */

    // Feature extractor
    feature_extractor_.Forward(
      audio_seg.data,
      audio_seg.len,
      audio_seg.sample_rate
    );

    return 0;
  }

  int To() { return 0; }
  int Text() { return 0; }

 private:
  FeatureInfo& feature_info_;
  FeatureExtractor feature_extractor_;
  Optional<Resampler*> resampler_ = nullptr;

}; // class Recognizer
}  // namespace sio
#endif