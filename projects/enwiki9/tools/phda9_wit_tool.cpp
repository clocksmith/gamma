#include <cstdint>
#include <cstdio>
#include <cstring>

#include "../external/fx2-cmix/src/readalike_prepr/phda9_preprocess.h"

int main(int argc, char** argv) {
  if (argc != 4) {
    std::fprintf(stderr, "usage: phda9_wit_tool encode|decode INPUT OUTPUT\n");
    return 2;
  }

  FILE* in = std::fopen(argv[2], "rb");
  if (!in) {
    std::perror(argv[2]);
    return 1;
  }
  FILE* out = std::fopen(argv[3], "wb");
  if (!out) {
    std::perror(argv[3]);
    std::fclose(in);
    return 1;
  }

  int rc = 0;
  if (std::strcmp(argv[1], "encode") == 0) {
    encode_txt_wit(in, out);
  } else if (std::strcmp(argv[1], "decode") == 0) {
    std::fseek(in, 0, SEEK_END);
    U64 input_size = ftello(in);
    std::fseek(in, 0, SEEK_SET);
    decode_txt_wit(in, out, input_size);
  } else {
    std::fprintf(stderr, "usage: phda9_wit_tool encode|decode INPUT OUTPUT\n");
    rc = 2;
  }

  std::fclose(in);
  std::fclose(out);
  return rc;
}
