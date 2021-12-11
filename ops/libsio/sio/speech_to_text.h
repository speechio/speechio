#ifndef SIO_SPEECH_TO_TEXT_H
#define SIO_SPEECH_TO_TEXT_H

#include "sio/ptr.h"
#include "sio/str.h"
#include "recognizer.h"

namespace sio {

struct SpeechToTextConfig {
  FeatureConfig feature_config;

  std::string tokenizer;
  std::string model;
  std::string graph;
  std::string context;

  bool do_endpointing = false;
  bool online = true;

  void Register(kaldi::OptionsItf *opts) {
    feature_config.Register(opts);

    opts->Register("tokenizer", &tokenizer, "sentencepiece tokenizer");
    opts->Register("model", &model, "nn model filename");
    opts->Register("graph", &graph, "beam search graph(e.g. HCLG.fst)");
    opts->Register("context", &context, "context configuration(e.g. context.json)");

    opts->Register("do-endpointing", &do_endpointing, "If true, apply endpoint detection");
    opts->Register("online", &online,
                   "You can set this to false to disable online iVector estimation "
                   "and have all the data for each utterance used, even at "
                   "utterance start.  This is useful where you just want the best "
                   "results and don't care about online operation.  Setting this to "
                   "false has the same effect as setting "
                   "--use-most-recent-ivector=true and --greedy-ivector-extractor=true "
                   "in the file given to --ivector-extraction-config, and "
                   "--chunk-length=-1.");
  }
}; // End of struct SpeechToTextConfig


template <typename BeamSearchGraphT>
struct SpeechToText {
  const SpeechToTextConfig &config;
  FeatureInfo feature_info;

  SpeechToText(const SpeechToTextConfig& c) :
    config(c),
    feature_info(c.feature_config)
  { }
  //~SpeechToText();

  Optional<Recognizer*> CreateRecognizer() {
    return new Recognizer(
      feature_info
    );
  }

  int DestroyRecognizer(Recognizer* r) { 
    delete r;
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
}; // end of class SpeechToText
}  // namespace sio

#endif