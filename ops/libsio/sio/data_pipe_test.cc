#include <gtest/gtest.h>
#include <iostream>

#include "feat/wave-reader.h"
#include "sio/str.h"
#include "sio/type.h"
#include "sio/map.h"
#include "sio/data_pipe.h"

TEST(DataPipe, FeatureExtractor) {
  using namespace sio;
  Map<Str, i32> audio_to_frames = {
      {"testdata/MINI/audio/audio1.wav", 126},
      {"testdata/MINI/audio/audio2.wav", 522}
  };

  float sample_rate = 16000;
  FeatureExtractorConfig c;
  FeatureExtractorInfo feature_info(c);
  for (const auto& kv : audio_to_frames) {
    Str audio_file = kv.first;
    i32 num_frames = kv.second;
    // TODO: can't move datapipe obj outside loop, need investigation
    FeatureExtractor feature_extractor(feature_info);

    std::ifstream is(audio_file, std::ifstream::binary);
    kaldi::WaveData wave;
    wave.Read(is);
    kaldi::SubVector<float> audio(wave.Data(), 0);
    feature_extractor.Forward(sample_rate, (float*)audio.Data(), audio.Dim());
    EXPECT_EQ(num_frames, feature_extractor.NumFramesReady());
  }
}
