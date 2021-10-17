#ifndef SIO_TYPE_H
#define SIO_TYPE_H

#include <stdint.h>

#include <string>
#include "absl/strings/string_view.h"
#include "absl/strings/strip.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_split.h"
#include "absl/strings/str_join.h"
#include "absl/strings/str_replace.h"
#include "absl/strings/str_format.h"

#include "absl/meta/type_traits.h"

namespace sio {

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
using str_view = absl::string_view;

/* 
C pointers are great at pointing "things", but they failed expressing:
    - ownerships
    - nullness

New pointer-types are introduced here:
    - owner<T*>           denotes pointers with    ownership
    - nullable<T*>        denotes pointers                     can    be nullptr
    - nullable<owner<T*>> denotes pointers with    ownership & can    be nullptr
    - ref<T*>             denotes pointers without ownership & cannot be nullptr

Explicit and consistent use of these types provides extra semantics that are missing in C pointers.
And throughout this codebase, any C pointer(i.e. T*) should be converted to one of these. 

But notes these types:
    - serve as merely annotations between programmers, rather than compiler guarentees.
    - are just aliasings to C pointers, with zero runtime cost
    - work seamlessly with C API/ABI
*/

template <typename PtrT, typename = typename absl::enable_if_t<std::is_pointer<PtrT>::value>>
using owner = PtrT;

template <typename PtrT, typename = typename absl::enable_if_t<std::is_pointer<PtrT>::value>>
using nullable = PtrT;

template <typename PtrT, typename = typename absl::enable_if_t<std::is_pointer<PtrT>::value>>
using ref = PtrT;

}; // namespace sio
#endif
