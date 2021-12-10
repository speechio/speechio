#include "sio/data_pipe.h"
#include "sio/log.h"

namespace sio {

void DataPipe::Forward(float sample_rate, const float* samples, size_t num_samples) {
  kaldi::SubVector<float> audio_chunk(samples, num_samples);
  feature_extractor_.AcceptWaveform(sample_rate, audio_chunk);

  SIO_DEBUG << feature_extractor_.NumFramesReady() << " frames ready.";
}

i32 DataPipe::NumFramesReady() const {
  return feature_extractor_.NumFramesReady();
}

} // namespace sio
