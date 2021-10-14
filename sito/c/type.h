#ifndef SITO_TYPE_H
#define SITO_TYPE_H

#include <stdint.h>
#include <string>
#include <type_traits>

namespace sito {
/* primitive types */
using i8  = int8_t;
using i16 = int16_t;
using i32 = int32_t;
using i64 = int64_t;

using u8  = uint8_t;
using u16 = uint16_t;
using u32 = uint32_t;
using u64 = uint64_t;

using f32 = float;
using f64 = double;

using str = std::string;

/* 
C pointers are great at pointing "things", but they failed expressing *ownerships* and *nullness* explicitly.

As a convention throughout this codebase, any raw pointer should be represented with one of the following types:
    ref<T*>             pointers without ownership & cannot be nullptr
    owner<T*>           pointers with    ownership & cannot be nullptr
    optional<T*>        pointers without ownership & can    be nullptr
    optional<owner<T*>> pointers with    ownership & can    be nullptr

Notes: 
    - These are just aliasing types of raw C pointers, which can work seamlessly with C API/ABI.
    - Semantics here merely serve as annotations between programmers, rather than compiler guarentees.
*/

template < typename PtrT, typename = typename std::enable_if<std::is_pointer<PtrT>::value>::type >
using owner = PtrT;

template < typename PtrT, typename = typename std::enable_if<std::is_pointer<PtrT>::value>::type >
using optional = PtrT;

template < typename PtrT, typename = typename std::enable_if<std::is_pointer<PtrT>::value>::type >
using ref = PtrT;

}; // namespace sito
#endif
