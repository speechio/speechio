#ifndef SIO_FEATURE_EXTRACTOR_H
#define SIO_FEATURE_EXTRACTOR_H

#include "online2/online-nnet2-feature-pipeline.h"
#include "sio/type.h"
#include "sio/log.h"

namespace sio {

using FeatureExtractorConfig = kaldi::OnlineNnet2FeaturePipelineConfig;
using FeatureExtractorInfo   = kaldi::OnlineNnet2FeaturePipelineInfo;

class FeatureExtractor {
 public:
  FeatureExtractor(const FeatureExtractorInfo& info) :
    extractor_(info)
  { }

  void Forward(float sample_rate, const float* samples, size_t num_samples) {
    extractor_.AcceptWaveform(
      sample_rate, 
      kaldi::SubVector<float>(samples, num_samples)
    );
    SIO_DEBUG << extractor_.NumFramesReady() << " frames ready.";
  }

  i32 NumFramesReady() const {
    return extractor_.NumFramesReady();
  }

 private:
  kaldi::OnlineNnet2FeaturePipeline extractor_;
}; // class FeatureExtractor
}  // namespace sio
#endif
