// Independent arithmetic expectations for the exact magnitude/sign model.
#include "../lib/fx2_weight_sign_magnitude_v1.hpp"
#include <iostream>
using namespace fx2_weights_v1;
int main() {
  SignMagnitudeCounts c;
  require(c.state().size()==48,"complete count state size");
  require(SignMagnitudeCounts::tree(c.magnitude)==std::array<uint16_t,8>{{1024,956,878,1024,683,1024,1024,1024}},"initial Q11 magnitude tree");
  require(SignMagnitudeCounts::tree(c.sign)==std::array<uint16_t,2>{{1024,1024}},"initial sign tree");
  c.observe(14);
  require(SignMagnitudeCounts::tree(c.magnitude)==std::array<uint16_t,8>{{1024,896,878,910,683,1024,1024,819}},"skewed Q11 magnitude tree");
  require(SignMagnitudeCounts::tree(c.sign)[1]==1365,"positive sign rounding");
  c.observe(0);require(SignMagnitudeCounts::tree(c.sign)[1]==1024,"negative sign update");
  const auto before=c.state();bool rejected=false;
  try {c.observe(15);} catch (const std::runtime_error&) {rejected=true;}
  require(rejected && before==c.state(),"invalid symbol preserves state");
  c=SignMagnitudeCounts();c.magnitude[0]=65521;c.magnitude_total=65535;
  c.observe(7);
  require(c.magnitude[0]==32761 && c.magnitude[1]==1 && c.magnitude_total==32768,"magnitude rescale");
  require(c.sign_total==2 && c.sign[0]==1 && c.sign[1]==1,"zero does not update sign");
  c=SignMagnitudeCounts();c.sign={{65534,1}};c.sign_total=65535;c.observe(8);
  require(c.sign==std::array<uint32_t,2>{{32768,1}} && c.sign_total==32769,"sign rescale");
  require(SignMagnitudeCounts::tree(c.sign)[1]==2047,"upper Q11 clamp");
  c.sign={{1,65534}};require(SignMagnitudeCounts::tree(c.sign)[1]==1,"lower Q11 clamp");
  std::cout << "exact_tree_state_checks_pass\n";
}
