#include "fx2_closing_replay_v1.hpp"
#include <cstdio>
#include <cstdint>
#include <filesystem>
#include <stdexcept>

static void put64(FILE* f,uint64_t x) {
  for(unsigned i=0;i<8;++i)if(std::fputc(uint8_t(x>>(8*i)),f)==EOF)throw std::runtime_error("write");
}
int main(int argc,char** argv) {
  if(argc!=3)return 2;
  FILE *input=nullptr,*output=nullptr;
  try {
    const auto n=std::filesystem::file_size(argv[1]);
    if(!n||n>151210)throw std::runtime_error("population bound");
    input=std::fopen(argv[1],"rb");output=std::fopen(argv[2],"wbx");
    if(!input||!output)throw std::runtime_error("exclusive files");
    if(std::fwrite("CLT1",1,4,output)!=4)throw std::runtime_error("header");
    put64(output,n);
    gamma_closing::Replay state;
    for(uint64_t i=0;i<n;++i) {
      uint8_t donor=0;
      const bool active=state.predict(donor);
      uint64_t hash=14695981039346656037ULL;
      for(uint8_t c:state.state()) {hash^=c;hash*=1099511628211ULL;}
      if(std::fputc(active,output)==EOF||std::fputc(donor,output)==EOF)throw std::runtime_error("record");
      put64(output,hash);
      // No current input byte is read until the prediction record is fixed.
      const int truth=std::fgetc(input);
      if(truth==EOF||(i==0&&truth!=7))throw std::runtime_error("input or flag");
      state.observe(uint8_t(truth));
    }
    if(std::fgetc(input)!=EOF||std::ferror(input))throw std::runtime_error("input changed");
    const auto terminal=state.state();
    if(std::fwrite(terminal.data(),1,terminal.size(),output)!=terminal.size())throw std::runtime_error("terminal");
    const int in_code=std::fclose(input);input=nullptr;
    const int out_code=std::fclose(output);output=nullptr;
    if(in_code||out_code)throw std::runtime_error("close");
    return 0;
  } catch(const std::exception& e) {
    if(input)std::fclose(input);
    if(output)std::fclose(output);
    std::fprintf(stderr,"%s\n",e.what());return 1;
  }
}
