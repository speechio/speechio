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
C pointers are great at pointing "things", but they failed expressing:
    - ownerships
    - nullness

New pointer-types are introduced here:
    - owner<T*>           denotes pointers with    ownership
    - optional<T*>        denotes pointers                     can    be nullptr
    - optional<owner<T*>> denotes pointers with    ownership & can    be nullptr
    - ref<T*>             denotes pointers without ownership & cannot be nullptr

Explicit and consistent use of these types provides extra semantics that are missing in C pointers.
And throughout this codebase, any C pointer(i.e. T*) should be converted to one of these. 

But notes these types:
    - serve as merely annotations between programmers, rather than compiler guarentees.
    - are just aliasings to C pointers, with zero runtime cost
    - work seamlessly with C API/ABI
*/

template < typename PtrT, typename = typename std::enable_if<std::is_pointer<PtrT>::value>::type >
using owner = PtrT;

template < typename PtrT, typename = typename std::enable_if<std::is_pointer<PtrT>::value>::type >
using optional = PtrT;

template < typename PtrT, typename = typename std::enable_if<std::is_pointer<PtrT>::value>::type >
using ref = PtrT;

}; // namespace sito
#endif
