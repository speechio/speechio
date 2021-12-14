#ifndef SIO_ERROR_H
#define SIO_ERROR_H

#include "sio/base.h"

namespace sio {

ABSL_ATTRIBUTE_NOINLINE
ABSL_ATTRIBUTE_NORETURN
ABSL_PRINTF_ATTRIBUTE(1, 2)
void panic(const char *format, ...);

#define SIO_UNREACHABLE \
  ::sio::panic("Unreachable bug occurred @ %s:%d:%s.\n", SIO_FILE_REPR, __LINE__, SIO_FUNC_REPR)

enum class Error : int {
  None = 0,
  Unknown,
  OOM,
}; // enum class Error

bool operator!(Error err);
const char *error_cstr(Error err);

} // namespace sio

#endif
