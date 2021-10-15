#ifndef SITO_ASSERT_H
#define SITO_ASSERT_H

#include <stdlib.h>

#if defined(__clang__) || defined(__GNUC__)
#define LIKELY(x)   __builtin_expect(!!(x), 1)
#define UNLIKELY(x) __builtin_expect(!!(x), 0)
#else
#define LIKELY(x)   (!!(x))
#define UNLIKELY(x) (!!(x))
#endif // defined(__clang__) || defined(__GNUC__)

#define HOARE_LOGIC_ASSERT(type, cond)  \
    (LIKELY(cond) ? static_cast<void>(0) : abort())

#define P_COND(cond)    HOARE_LOGIC_ASSERT("Precondition", cond)
#define Q_COND(cond)    HOARE_LOGIC_ASSERT("Postcondition", cond)
#define INVARIANT(cond) HOARE_LOGIC_ASSERT("Invariant", cond)

#endif
