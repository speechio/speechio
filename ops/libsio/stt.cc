#include <iostream>

#include "sio/include/sio.h"

int main() {
    using namespace sio;
    SpeechToTextConfig config;

    config.feature_config.feature_type = "fbank";
    /* 
      argument/config-file parsing -> config
    */

    int samples_per_chunk = std::numeric_limits<int>::max();
    if (config.online == true) {
        samples_per_chunk = 1000;
    }

    SpeechToText<float> speech_to_text(config);

    std::ifstream wav_scp("testdata/MINI/wav.scp");
    std::string line;
    while (std::getline(wav_scp, line)) {
        std::vector<std::string> fields = absl::StrSplit(line, absl::ByAnyChar(" \t,:;"));
        if (fields.size() != 2) continue;

        std::string& audio_key  = fields[0];
        std::string& audio_path = fields[1];
        SIO_DEBUG << audio_key << " " << audio_path;

        kaldi::WaveData wave_data;
        std::ifstream is(audio_path, std::ifstream::binary);
        wave_data.Read(is);
        kaldi::SubVector<float> audio(wave_data.Data(), 0);

        Recognizer* rec = speech_to_text.CreateRecognizer();
        assert(rec != nullptr);
        rec->StartSession(audio_key.c_str());

        int samples_done = 0;
        while (samples_done < audio.Dim()) {
            int this_chunk = std::min(samples_per_chunk, audio.Dim() - samples_done);
            rec->Speech(
                audio.Data() + samples_done,
                this_chunk,
                wave_data.SampFreq()
            );
            samples_done += this_chunk;
        }
        rec->To();
        rec->Text();
        speech_to_text.DestroyRecognizer(rec);
        SIO_INFO << "Decoded " << samples_done << " samples for " << audio_key;
    }

    return 0;
}
