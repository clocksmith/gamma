// Replay declared token/prior rows through the pinned model, without codec runs.
#include "cpp_infer/src/opt/model_opt.h"
#include "cpp_infer/src/weights_io.h"
#include "fx2_numeric_trace.hpp"
#include <algorithm>
#include <array>
#include <vector>
static FILE* open_file(const char* name,const char* mode) {
  FILE* f=std::fopen(name,mode); if(!f) std::abort(); return f;
}
int main(int argc,char** argv) {
  if(argc!=8) return 2; // weights, rows, priors, output, trace-or-dash, trace rows, decoded weights
  gamma_numeric::limit=std::stoul(argv[6]);
  if(std::string(argv[5])!="-") gamma_numeric::sink=open_file(argv[5],"wbx");
  fx2::opt::TransformerOpt model(argv[1]);
  auto wf=fx2::WeightsFile::load_compressed(argv[1]);
  FILE* decoded=open_file(argv[7],"wbx");
  std::vector<std::string> names; for(const auto& entry:wf.tensors) names.push_back(entry.first);
  std::sort(names.begin(),names.end());
  for(const auto& name:names) {
    const auto& t=wf.tensors.at(name);
    uint32_t h[4]={uint32_t(name.size()),t.dtype,uint32_t(t.shape.size()),uint32_t(t.data.size())};
    if(std::fwrite(h,sizeof(h),1,decoded)!=1 || std::fwrite(t.shape.data(),4,t.shape.size(),decoded)!=t.shape.size() ||
       std::fwrite(name.data(),1,name.size(),decoded)!=name.size() || std::fwrite(t.data.data(),1,t.data.size(),decoded)!=t.data.size()) return 3;
  }
  if(std::fclose(decoded)) return 3;
  FILE* rows=open_file(argv[2],"rb"); FILE* priors=open_file(argv[3],"rb"); FILE* out=open_file(argv[4],"wbx");
  std::array<uint16_t,205> prior{}; unsigned char pair[2]; bool need_reset=true;
  for(uint32_t index=0;;++index) {
    size_t n=std::fread(pair,1,2,rows); if(!n) break; if(n!=2 || pair[0]>=205 || pair[1]>2) return 4;
    if(std::fread(prior.data(),2,205,priors)!=205) return 5;
    gamma_numeric::row=index; float values[410]={};
    if(pair[1]==2) need_reset=true;
    else {
      if((pair[1]==1)!=need_reset) return 6;
      if(need_reset) model.begin_article(); need_reset=false;
      model.step(pair[0],prior.data(),values+205);
      std::copy(model.last_logits(),model.last_logits()+205,values);
    }
    if(std::fwrite(values,sizeof(values),1,out)!=1) return 7;
  }
  if(std::fgetc(priors)!=EOF || std::ferror(rows) || std::fclose(out)) return 8;
  if(gamma_numeric::sink && std::fclose(gamma_numeric::sink)) return 9;
  std::fclose(rows); std::fclose(priors); return 0;
}
