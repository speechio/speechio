#include <iostream>

#include "feat/wave-reader.h"
#include "sio/sio.h"

int main() {
    using namespace sio;
    SpeechToTextConfig config;
    /* 
      argument/config-file parsing -> config
    */

    float sample_rate = 16000;
    float chunk_secs = 0.2;
    int chunk_samples = (chunk_secs > 0) ? int(sample_rate * chunk_secs) : std::numeric_limits<int>::max();
    assert(chunk_samples > 0);

    SpeechToText<float> speech_to_text(config);

    AudioFormat audio_format = AudioFormat::kFloatMono16k;
    std::ifstream wav_scp("testdata/MINI/wav.scp");
    std::string line;
    while (std::getline(wav_scp, line)) {
        std::vector<std::string> fields = absl::StrSplit(line, absl::ByAnyChar(" \t,:;"));
        if (fields.size() != 2) continue;

        std::string& audio_key  = fields[0];
        std::string& audio_path = fields[1];
        SIO_DEBUG << audio_key << " " << audio_path;

        kaldi::WaveData wave;
        std::ifstream stream(audio_path, std::ifstream::binary);
        wave.Read(stream);
        kaldi::SubVector<float> audio(wave.Data(), 0); // channel 0
        assert(wave.SampFreq() == sample_rate);

        Recognizer* rec = speech_to_text.CreateRecognizer();
        assert(rec != nullptr);
        rec->StartSession(audio_key.c_str());
        int samples_done = 0;
        while (samples_done < audio.Dim()) {
            int samples_remaining = audio.Dim() - samples_done;
            int n = chunk_samples < samples_remaining ? chunk_samples : samples_remaining;
    
            kaldi::SubVector<float> audio_chunk(audio, samples_done, n);
            rec->AcceptAudioData(audio_format, audio_chunk.Data(), audio_chunk.SizeInBytes());
    
            samples_done += n;
    
            //if (opts.do_endpointing && rec->EndOfSentenceDetected()) {
            //    break;
            //}
            SIO_DEBUG << samples_done << " samples decoded.";
        }
        rec->StopSession();
        speech_to_text.DestroyRecognizer(rec);
        SIO_INFO << "Decoded " << samples_done << " samples for " << audio_key;
    }

    return 0;
}
