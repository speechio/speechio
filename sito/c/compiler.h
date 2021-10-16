#ifndef SIO_COMPILER_H
#define SIO_COMPILER_H

#if defined(__clang__) || defined(__GNUC__)
#    define LIKELY(x)   __builtin_expect(!!(x), 1)
#    define UNLIKELY(x) __builtin_expect(!!(x), 0)
#else
#    define LIKELY(x)   (!!(x))
#    define UNLIKELY(x) (!!(x))
#endif

#endif
