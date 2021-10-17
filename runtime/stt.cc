#include <iostream>
#include <vector>

#include "sio/hoare.h"
#include "sio/type.h"

int main() {
    using namespace sio;
    P_COND(true);
    list<str> v = {"foo","bar","baz"};
    list<list<str>> k;
    str s = absl::StrJoin(v, "-");
    str_view sv = s;
    INVARIANT(true);
  
    std::cout << "Joined string: " << sv << "\n";
    i32 i = 10;
    ref<i32*> p = &i;
    std::cout << p << "\n";
    map<int, str> m;
    m.insert({1, "abc"});
    std::cout << &m << "\n";

    Q_COND(true);
}
