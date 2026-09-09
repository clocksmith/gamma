#include "../lib/fx2_xml_field_observer_v1.hpp"
#include <cassert>
#include <iostream>
#include <iomanip>
#include <sstream>

using namespace gamma_xml_field;
static std::vector<std::string> dictionary() {
  std::vector<std::string> words(44880, "a");
  words[0]="title"; words[1]="id"; words[80]="timestamp";
  words[3919]="username"; words[3920]="comment"; words[44879]="text";
  return words;
}
static void hex(const Bytes& bytes) {
  for (uint8_t c : bytes) std::cout << std::hex << std::setw(2) << std::setfill('0') << unsigned(c);
  std::cout << std::dec;
}
int main(int argc, char** argv) {
  if (argc == 3) {
    std::istringstream stream(argv[1]);
    Observer observer(dictionary(), std::stoull(argv[2]));
    std::string input; stream >> input;
    if (input.size() % 2) return 2;
    for (size_t i=0; i<input.size(); i+=2) {
      const uint8_t byte = uint8_t(std::stoul(input.substr(i,2), nullptr,16));
      Bytes raw;
      if (!observer.observe(byte,raw)) return 3;
      std::cout << unsigned(observer.field()) << ' '; hex(raw);
      std::cout << ' '; hex(observer.state()); std::cout << '\n';
    }
    return observer.finish() ? 0 : 4;
  }
  assert(argc == 1);
  const auto words=dictionary();
  Observer a(words, 0), b(words, 0); Bytes output{99};
  assert(a.state()==b.state());
  assert(a.observe(7,output) && output.empty());
  assert(a.finish());
  assert(!a.observe(7,output) && a.failed());
  Observer wrong(words,0); output={99};
  assert(!wrong.observe(6,output) && output==Bytes{99});
  assert(!wrong.observe(7,output));
  Observer truncated(words,1);
  assert(truncated.observe(7,output));
  assert(truncated.observe(208,output));
  assert(!truncated.finish());
  Observer bound(words,0);
  assert(bound.observe(7,output)); output={99};
  assert(!bound.observe('a',output) && output==Bytes{99} && bound.raw_count()==0);
  Observer invalid_word({"UPPER"},1); assert(invalid_word.failed());
  Observer oversized({},1000000001); assert(oversized.failed());
  // Equal visible fields do not hide a different unfinished marker.
  Observer x(words,2), y(words,2);
  assert(x.observe(7,output) && y.observe(7,output));
  assert(x.observe(unswap('<'),output) && y.observe('a',output));
  assert(x.field()==y.field() && x.state()!=y.state());
  std::cout << "native rejection and state fixtures pass\n";
}
