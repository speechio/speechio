#include <iostream>
#include <vector>

#include "sio/hoare.h"
#include "sio/type.h"
//#include "absl/container/flat_hash_map.h"

int main() {
    using namespace sio;
    P_COND(true);
    std::vector<str> v = {"foo","bar","baz"};
    str s = absl::StrJoin(v, "-");
    str_view sv = s;
    INVARIANT(true);
  
    std::cout << "Joined string: " << sv << "\n";
    i32 i = 10;
    ref<i32*> p = &i;
    std::cout << p << "\n";
    //absl::flat_hash_map<int, str> m;
    //std::cout << &m << "\n";

    Q_COND(false);
}
