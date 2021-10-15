#ifndef SITO_CHECK_H
#define SITO_CHECK_H

#include <stdio.h>

#if defined(__clang__) || defined(__GNUC__)
#define LIKELY(x)   __builtin_expect(!!(x), 1)
#define UNLIKELY(x) __builtin_expect(!!(x), 0)
#else
#define LIKELY(x)   (!!(x))
#define UNLIKELY(x) (!!(x))
#endif // defined(__clang__) || defined(__GNUC__)

#define CHECK(cond, info) do {                             \
    if (UNLIKELY( !(cond) )) {                             \
        fprintf(stderr,                                    \
            "%s:%s:L%d |%s| %s\n",                         \
            __FILE__, __FUNCTION__, __LINE__, #cond, info  \
        );                                                 \
        fflush(stderr);                                    \
        abort();                                           \
    }                                                      \
} while(0)

#define P_CHECK(cond) CHECK(cond, "Precondition Broken")
#define Q_CHECK(cond) CHECK(cond, "Postcondition Broken")
#define I_CHECK(cond) CHECK(cond, "Invariant Broken")

#endif
