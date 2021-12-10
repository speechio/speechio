#ifndef SIO_DATA_PIPE_H
#define SIO_DATA_PIPE_H

#include "online2/online-nnet2-feature-pipeline.h"
#include "sio/type.h"

namespace sio {

using FeatureConfig = kaldi::OnlineNnet2FeaturePipelineConfig;

class DataPipe {
 public:
  explicit DataPipe(const FeatureConfig& feature_config) :
    feature_info_(feature_config), feature_extractor_(feature_info_)
  { }

  void Forward(float sample_rate, const float* samples, size_t num_samples);
  i32 NumFramesReady() const;

 private:
  kaldi::OnlineNnet2FeaturePipelineInfo feature_info_;
  kaldi::OnlineNnet2FeaturePipeline feature_extractor_;

}; // class DataPipe
}  // namespace sio
#endif
