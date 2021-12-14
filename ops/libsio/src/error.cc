#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>

#include "sio/error.h"

namespace sio {

void panic(const char *format, ...) {
  va_list ap;
  va_start(ap, format);
  vfprintf(stderr, format, ap);
  fflush(stderr);
  va_end(ap);
  abort();
}

bool operator!(Error err) {
  return (err == Error::None);
}

const char *error_cstr(Error err) {
  switch (err) {
    case Error::None: return "(no error)";
    case Error::OOM: return "out of memory";
    default: return "(unknown error)";
  }
}

} // namespace sio
