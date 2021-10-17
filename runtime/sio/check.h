#ifndef SIO_CHECK_H
#define SIO_CHECK_H

#include <stdio.h>

#if defined(__clang__) || defined(__GNUC__)
#    define LIKELY(x)   __builtin_expect(!!(x), 1)
#    define UNLIKELY(x) __builtin_expect(!!(x), 0)
#else
#    define LIKELY(x)   (!!(x))
#    define UNLIKELY(x) (!!(x))
#endif

#define SIO_CHECK_EXPR(expr, info) do {                       \
    if (UNLIKELY( !(expr) )) {                                \
        fprintf(stderr,                                       \
            "Check { %s } failed -> %s @ %s:%s:L%d\n",        \
            (#expr), (info), __FILE__, __FUNCTION__, __LINE__ \
        );                                                    \
        abort();                                              \
    }                                                         \
} while(0)

#define P_CHECK(cond) SIO_CHECK_EXPR(cond, "Precondition")
#define Q_CHECK(cond) SIO_CHECK_EXPR(cond, "Postcondition")
#define I_CHECK(cond) SIO_CHECK_EXPR(cond, "Invariant")

#endif
