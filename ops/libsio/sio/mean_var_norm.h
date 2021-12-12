#ifndef SIO_MEAN_VAR_NORM_H
#define SIO_MEAN_VAR_NORM_H

#include <string>
#include <iostream>
#include <vector>

#include "matrix/kaldi-vector.h"

#include "sio/check.h"

namespace sio {
struct MeanVarNorm {
  /*
  Format of mean_var_norm file, three lines:
  line1: norm_vector_dimension
  line2: m_norm_shift vector, no brackets, elements seperated by comma or whitespaces
  line3: v_nrom_scale vector, same as above

  Example mean_var_norm.txt:
  3
  -8.505237579345703 -8.91793441772461 -10.091235160827637
  0.6330024600028992 0.49299687147140503 0.37579503655433655

  */
  void Load(std::string mvn_path) {
    m_norm_shift.clear();
    v_norm_scale.clear();

    std::ifstream is(mvn_path);

    std::string line;
    std::getline(is, line);

    dim = std::stoi(line);
    m_norm_shift.reserve(dim);
    v_norm_scale.reserve(dim);

    std::vector<std::string> cols;

    std::getline(is, line);
    cols = absl::StrSplit(line, absl::ByAnyChar(" \t,"), absl::SkipWhitespace());
    SIO_CHECK(cols.size() == dim, "mean norm dim is different from header");

    for (int i = 0; i != cols.size(); i++) {
      m_norm_shift.push_back(std::stod(cols[i]));
    }

    std::getline(is, line);
    cols = absl::StrSplit(line, absl::ByAnyChar(" \t,"), absl::SkipWhitespace());
    SIO_CHECK(cols.size() == dim, "var norm dim is different from header");

    for (int i = 0; i != cols.size(); i++) {
      v_norm_scale.push_back(std::stod(cols[i]));
    }
  }

  void Forward(kaldi::VectorBase<float> *frame) {
    SIO_P_COND(frame != nullptr);
    SIO_P_COND(frame->Dim() == dim);
    for (int i = 0; i < dim; i++) {
      // use quote for elem referencing, see:
      // https://github.com/kaldi-asr/kaldi/blob/master/src/matrix/kaldi-vector.h#L82
      (*frame)(i) += m_norm_shift[i];
      (*frame)(i) *= v_norm_scale[i];
    }
  }

  int dim = 0;
  std::vector<double> m_norm_shift;
  std::vector<double> v_norm_scale;
}; // class MeanVarNormalizer
} // namespace sio
#endif
