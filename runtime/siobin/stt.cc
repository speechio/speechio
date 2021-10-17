#include <iostream>
#include "sio/hoare.h"
#include "sio/type.h"

int main() {
    using namespace sio;
    P_COND(true);
    vec<str> v = {"foo","bar","baz"};
    vec<vec<str>> k;
    str s = absl::StrJoin(v, "-");
    str_view sv = s;
    INVARIANT(true);
  
    std::cout << "Joined string: " << sv << "\n";
    i32 i = 10;
    ref<i32*> p = &i;
    std::cout << absl::StrFormat("%d\n", *p);
    map<int, str> m;
    m[123] = "abc";
    std::cout << &m << "\n";

    Q_COND(true);
}
