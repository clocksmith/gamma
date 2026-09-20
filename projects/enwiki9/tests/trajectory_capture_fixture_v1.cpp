#include "../src/gamma_enwiki9/adapters/fx2_trajectory_capture_v1.hpp"
int main(int argc,char** argv){
  using namespace gamma_trajectory;
  check(argc==2);check(setenv("GAMMA_ATTRIBUTION_CAPTURE",argv[1],1)==0);begin();
  std::array<uint16_t,205> prior{};std::array<float,205> probabilities{};probabilities.fill(.25f);
  for(unsigned row_index=0;row_index<3;++row_index){
    for(unsigned b=0;b<8;++b)bit(32768,0);
    row(row_index,row_index==1?2:1,prior.data());
    publish(row_index==1?nullptr:probabilities.data());
  }
  end();
}
