#include <iostream>
#include "sio/base.h"

using namespace sio;
struct Person {
    i32 age = 0;
    str name = "";
};

template<typename T>
struct Slice {
    ref<T*> items = nullptr;
    i64 len = 0;
    i64 cap = 0;
};

int main() {
    Person x;
    Slice<int> y;
    P_COND(true);
    list<str> v;
    list<list<str>> k;
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
