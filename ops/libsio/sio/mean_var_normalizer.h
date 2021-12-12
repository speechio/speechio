#ifndef SIO_MEAN_VAR_NORMALIZER_H
#define SIO_MEAN_VAR_NORMALIZER_H

#include <iostream>
#include "matrix/kaldi-vector.h"
#include "sio/str.h"

namespace sio {
struct MeanVarNormalizer {
  void Load(std::string mvn_file) {
    std::ifstream is(mvn_file);
    is >> mean_norm_shift;
    is >> var_norm_scale;
  }

  void Forward(kaldi::VectorBase<float> *frame) {
    SIO_P_COND(frame != nullptr);
    SIO_P_COND(frame->Dim() == mean_norm_shift.Dim());
    frame->AddVec(1.0, mean_norm_shift);
    frame->MulElements(var_norm_scale);
  }

  kaldi::Vector<float> mean_norm_shift;
  kaldi::Vector<float> var_norm_scale;
}; // class MeanVarNormalizer
} // namespace sio
#endif
