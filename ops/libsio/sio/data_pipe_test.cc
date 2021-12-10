#include <gtest/gtest.h>
#include <iostream>

#include "feat/wave-reader.h"
#include "sio/str.h"
#include "sio/type.h"
#include "sio/vec.h"
#include "sio/data_pipe.h"

TEST(DataPipe, Feature) {
  using namespace sio;
  Vec<Str> files = {
      "testdata/MINI/audio/audio1.wav",
      "testdata/MINI/audio/audio2.wav"
  };
  Vec<i32> num_frames = {126, 522};

  FeatureExtractorConfig c;
  FeatureExtractorInfo feature_info(c);
  float sample_rate = 16000;

  for (index_t i = 0; i < files.size(); i++) {
    // TODO: can't move datapipe obj outside loop, need investigation
    DataPipe datapipe(feature_info);
    std::ifstream is(files[i], std::ifstream::binary);
    kaldi::WaveData wave;
    wave.Read(is);
    kaldi::SubVector<float> audio(wave.Data(), 0);
    datapipe.Forward(sample_rate, (float*)audio.Data(), audio.Dim());
    EXPECT_EQ(num_frames[i], datapipe.NumFramesReady());
  }
}
