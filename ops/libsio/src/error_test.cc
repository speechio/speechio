#include <gtest/gtest.h>
#include <string>

#include "sio/error.h"

namespace sio {

TEST(Error, Basic) {
  Error err = Error::OOM;
  std::cout << error_cstr(err) << "\n";
  EXPECT_EQ(std::string(error_cstr(err)), "out of memory");
  //SIO_UNREACHABLE;
}

} // namespace sio