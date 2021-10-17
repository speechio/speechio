#ifndef SIO_BASE_MAP_H
#define SIO_BASE_MAP_H

//#define ENABLE_ABSL_HASH_MAP
#ifdef ENABLE_ABSL_HASH_MAP
#    include "absl/container/flat_hash_map.h"
#else
#    include <unordered_map>
#endif

namespace sio {

#ifdef ENABLE_ABSL_HASH_MAP
/*
    template <
        class K,
        class V,
        class Hash = absl::container_internal::hash_default_hash<K>,
        class Eq = absl::container_internal::hash_default_eq<K>,
        class Allocator = std::allocator<std::pair<const K, V>>
    >
    using map = absl::flat_hash_map<K, V, Hash, Eq, Allocator>;
*/
    template<typename K, typename V>
    using map = absl::flat_hash_map<K, V>;
#else 
/*
    template <
        class K,
        class V,
        class Hash = std::hash<K>,
        class Eq = std::equal_to<K>,
        class Allocator = std::allocator<std::pair<const K, V>>
    >
    using map = std::unordered_map<K, V, Hash, Eq, Allocator>;
*/
    template<typename K, typename V>
    using map = std::unordered_map<K, V>;
#endif

};

#endif
