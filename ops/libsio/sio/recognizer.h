#ifndef SIO_RECOGNIZER_H
#define SIO_RECOGNIZER_H

#include "sio/type.h" // import AudioFormat
#include "sio/data_pipe.h"

namespace sio {
class Recognizer {
 public:
  Recognizer(
    const FeatureExtractorInfo& feature_extractor_info
  ):
    data_pipe_(feature_extractor_info)
  { }

  int StartSession(const char* key = nullptr);
  int AcceptAudioData(AudioFormat format, const void* data, size_t num_bytes);
  int StopSession();

 private:
  DataPipe data_pipe_;

}; // class Recognizer
}  // namespace sio
#endif
