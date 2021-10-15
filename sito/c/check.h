#ifndef SITO_CHECK_H
#define SITO_CHECK_H

#include <stdio.h>

#if defined(__clang__) || defined(__GNUC__)
#define SITO_LIKELY(x)   __builtin_expect(!!(x), 1)
#define SITO_UNLIKELY(x) __builtin_expect(!!(x), 0)
#else
#define SITO_LIKELY(x)   (!!(x))
#define SITO_UNLIKELY(x) (!!(x))
#endif // defined(__clang__) || defined(__GNUC__)

#define SITO_CHECK(cond, info) do {                        \
    if (SITO_UNLIKELY( !(cond) )) {                        \
        fprintf(stderr,                                    \
            "%s:%s:L%d { %s } Failed -> %s\n",             \
            __FILE__, __FUNCTION__, __LINE__, #cond, info  \
        );                                                 \
        abort();                                           \
    }                                                      \
} while(0)

#define P_CHECK(cond) SITO_CHECK(cond, "Precondition")
#define Q_CHECK(cond) SITO_CHECK(cond, "Postcondition")
#define I_CHECK(cond) SITO_CHECK(cond, "Invariant")

#endif
