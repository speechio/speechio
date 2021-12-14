#ifndef SIO_CHECK_H
#define SIO_CHECK_H

#include "sio/base.h"
#include "sio/error.h"

#define SIO_CHECK(expr, message) do {                    \
  if SIO_UNLIKELY(!(expr)) {                             \
    ::sio::panic("Check failure: {%s}, %s @ %s:%d:%s\n", \
      (#expr), message,                                  \
      SIO_FILE_REPR, __LINE__, SIO_FUNC_REPR             \
    );                                                   \
  }                                                      \
} while(0)

#define SIO_P_COND(cond) SIO_CHECK(cond, "Precondition")
#define SIO_Q_COND(cond) SIO_CHECK(cond, "Postcondition")
#define SIO_INVAR(cond)  SIO_CHECK(cond, "Invariant")

#endif

