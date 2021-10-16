#include <iostream>
#include <vector>

#include "check.h"
#include "type.h"
#include "absl/container/flat_hash_map.h"

int main() {
    using namespace sio;
    P_CHECK(true);
    std::vector<std::string> v = {"foo","bar","baz"};
    str s = absl::StrJoin(v, "-");
    str_view sv = s;
    I_CHECK(true);
  
    std::cout << "Joined string: " << sv << "\n";
    i32 i = 10;
    ref<i32*> p = &i;
    std::cout << p << "\n";
    absl::flat_hash_map<int, str> m;
    std::cout << &m << "\n";

    Q_CHECK(false);
}
