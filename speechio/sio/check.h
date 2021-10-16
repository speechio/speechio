#ifndef SIO_CHECK_H
#define SIO_CHECK_H

#include <stdio.h>
#include "compiler.h"

#define SIO_CHECK_EXPR(expr, info) do {                       \
    if (UNLIKELY( !(expr) )) {                                \
        fprintf(stderr,                                       \
            "%s:%s:L%d %s -> { %s } Failed.\n",               \
            __FILE__, __FUNCTION__, __LINE__, (info), (#expr) \
        );                                                    \
        abort();                                              \
    }                                                         \
} while(0)

#define P_CHECK(cond) SIO_CHECK_EXPR(cond, "Precondition")
#define Q_CHECK(cond) SIO_CHECK_EXPR(cond, "Postcondition")
#define I_CHECK(cond) SIO_CHECK_EXPR(cond, "Invariant")

#endif
