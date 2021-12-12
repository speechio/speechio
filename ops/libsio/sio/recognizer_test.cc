#include <gtest/gtest.h>
#include <iostream>

#include "sio/str.h"
#include "sio/type.h"
#include "sio/map.h"
#include "sio/audio.h"
#include "sio/feature.h"
#include "sio/mean_var_norm.h"

TEST(Recognizer, AudioReaderAndResampler) {
  using namespace sio;

  std::string audio_path = "testdata/MINI/audio/audio1.wav";
  std::ifstream is(audio_path, std::ifstream::binary);
  kaldi::WaveData wave_data;
  wave_data.Read(is);
  kaldi::SubVector<float> audio(wave_data.Data(), 0);

  Resampler resampler(16000, 8000);
  EXPECT_EQ(wave_data.SampFreq(), 16000.0);
  EXPECT_EQ(audio.Dim(), 20480);

  kaldi::Vector<float> output;
  resampler.Forward(audio.Data(), audio.Dim(), wave_data.SampFreq(), &output, true);

  EXPECT_EQ(resampler.TargetSampleRate(), 8000.0);
  EXPECT_EQ(output.Dim(), 10240);
}


TEST(Recognizer, FeatureExtractor) {
  using namespace sio;
  Map<Str, i32> audio_to_frames = {
      {"testdata/MINI/audio/audio1.wav", 126},
      {"testdata/MINI/audio/audio2.wav", 522}
  };

  float sample_rate = 16000;
  FeatureConfig c;
  c.feature_type = "fbank";
  FeatureInfo feature_info(c);

  MeanVarNorm mvn;
  mvn.Load("testdata/mean_var_norm_23dim.txt");

  for (const auto& kv : audio_to_frames) {
    Str audio_file = kv.first;
    i32 num_frames = kv.second;
    // TODO: can't move datapipe obj outside loop, need investigation
    FeatureExtractor feature_extractor(feature_info);

    std::ifstream is(audio_file, std::ifstream::binary);
    kaldi::WaveData wave;
    wave.Read(is);

    kaldi::SubVector<float> audio(wave.Data(), 0);
    feature_extractor.Forward(audio.Data(), audio.Dim(), sample_rate);
    feature_extractor.InputFinished();

    kaldi::Vector<float> frame_feat(feature_extractor.Dim());
    for (index_t f = 0; f < feature_extractor.NumFramesReady(); f++) {
      feature_extractor.GetFrame(f, &frame_feat);
      mvn.Forward(&frame_feat);
    }
    EXPECT_EQ(num_frames, feature_extractor.NumFramesReady());
  }

}

TEST(Recognizer, MeanVarNormalizer) {
  using namespace sio;
}