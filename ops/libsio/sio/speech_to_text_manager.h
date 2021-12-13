#ifndef SIO_SPEECH_TO_TEXT_MANAGER_H
#define SIO_SPEECH_TO_TEXT_MANAGER_H

#include "sio/ptr.h"
#include "sio/speech_to_text_config.h"
#include "sio/speech_to_text.h"

namespace sio {

template <typename BeamSearchGraphT>
struct SpeechToTextManager {
  const SpeechToTextConfig &config;
  FeatureInfo feature_info;

  SpeechToTextManager(const SpeechToTextConfig& c) :
    config(c),
    feature_info(c.feature_config)
  { }

  Optional<SpeechToText*> Create() {
    return new SpeechToText(feature_info);
  }

  int Destroy(SpeechToText* stt) { 
    delete stt;
    return 0;
  }

//  // acoustic model
//  TransitionModel trans_model_;
//  nnet3::AmNnetSimple am_nnet_;
//  nnet3::DecodableNnetSimpleLoopedInfo *decodable_info_;
//
//  // decoding graph
//  BeamSearchGraphT *beam_search_graph_;
//  fst::SymbolTable *word_syms_;
//
//  // context
//  ContextManager *context_manager_;
}; // class SpeechToTextManager
}  // namespace sio

#endif
