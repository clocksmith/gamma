#pragma once
#include "predictors/causal_relational_v2.hpp"
#include <memory>
#include <sys/stat.h>
#include <unistd.h>
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <cmath>
namespace gamma_relation_runtime {
inline void die(const char* text){std::fprintf(stderr,"%s\n",text);std::abort();}
inline std::unique_ptr<gamma_relational::Model> model;
inline FILE *raw_file=nullptr,*state_file=nullptr,*parent_file=nullptr;
inline std::string prefix;
inline long double parent_bits=0,relation_bits=0,mixed_bits=0,active_parent_bits=0,active_mixed_bits=0;
inline void write(FILE* f,const gamma_xml_field::Bytes& b){if(f&&std::fwrite(b.data(),1,b.size(),f)!=b.size())die("relational witness write");}
inline void witness(){auto s=model->state();gamma_xml_field::Bytes h;gamma_relational::put(h,model->modeled());gamma_relational::put(h,s.size());write(state_file,h);write(state_file,s);}
inline void begin(FILE* dictionary,const char* header,uint64_t expected_raw){
 if(!dictionary||!header||header[0]!=7||model)die("relational requires one native dictionary TEXT block");
  struct stat info;
  if (fstat(fileno(dictionary), &info) || !S_ISREG(info.st_mode) || info.st_size != 411996)
    die("Gamma XML dictionary size or type differs");
  std::vector<unsigned char> data(411996);
  size_t position = 0;
  while (position < data.size()) {
    ssize_t n = pread(fileno(dictionary), data.data()+position, data.size()-position, position);
    if (n < 0 && errno == EINTR) continue;
    if (n <= 0) die("Gamma XML dictionary read failed");
    position += n;
  }
  uint64_t digest = UINT64_C(0xcbf29ce484222325);
  std::vector<std::string> words;
  std::string word;
  size_t word_bytes = 0, longest = 0;
  for (unsigned char c : data) {
    digest = (digest ^ c) * UINT64_C(0x100000001b3);
    if (c >= 'a' && c <= 'z') word += c;
    else if (!word.empty()) {
      if (word.size() > 58 || words.size() >= 44515) die("Gamma XML dictionary bounds differ");
      word_bytes += word.size(); longest = std::max(longest, word.size());
      words.push_back(word); word.clear();
    }
  }
  if (digest != UINT64_C(0x2c3946082300051a) || !word.empty() ||
      words.size() != 44515 || word_bytes != 367481 || longest != 58 || data.back() != '\n')
    die("Gamma XML dictionary identity differs");
  uint64_t raw_length = 0;
  for (int i = 1; i < 5; ++i) raw_length = (raw_length << 8) | (unsigned char)header[i];
  if (expected_raw && raw_length != expected_raw) die("Gamma XML requires the complete single TEXT block");

 const char* selected=std::getenv("GAMMA_RELATIONAL_ARM");
 if(!selected||std::strlen(selected)!=1)die("relational arm required");
 model.reset(new gamma_relational::Model(words,raw_length,selected[0]));
 const char* output=std::getenv("GAMMA_RELATIONAL_CAPTURE");
 if(output){prefix=output;raw_file=std::fopen((prefix+".raw").c_str(),"wbx");state_file=std::fopen((prefix+".state").c_str(),"wbx");parent_file=std::fopen((prefix+".parent").c_str(),"wbx");if(!raw_file||!state_file||!parent_file)die("relational capture create");}
}
inline uint32_t predict(uint32_t p){if(!model)die("relational missing initialization");return model->predict(p);}
inline void observe(unsigned bit){
 const auto before=model->active_bits;
 const auto p=model->parent(),q=model->relational(),m=model->mixed();
 auto loss=[bit](uint32_t v){return -std::log2((long double)(bit?v:65536-v)/65536);};
 parent_bits+=loss(p);relation_bits+=loss(q);mixed_bits+=loss(m);
 // q!=p is a prediction-time measurable opportunity, not a truth-selected subset.
 if(q!=p){active_parent_bits+=loss(p);active_mixed_bits+=loss(m);}
 if(parent_file){const unsigned char row[3]={uint8_t(p),uint8_t(p>>8),uint8_t(bit)};if(std::fwrite(row,1,3,parent_file)!=3)die("parent trace write");}
 gamma_xml_field::Bytes raw;if(!model->observe(bit,raw))die("relational inverse failed");write(raw_file,raw);
 (void)before;
 if(model->modeled()&&model->modeled()%gamma_relational::Epoch==0&&raw.size())witness();
}
inline void end(){
 if(!model||!model->finish())die("relational inverse terminal failed");
 witness();
 for(FILE* f:{raw_file,state_file,parent_file})if(f&&std::fclose(f))die("relational capture close");
 if(!prefix.empty()){
 FILE* f=std::fopen((prefix+".json").c_str(),"wx");if(!f)die("relational summary create");
 std::fprintf(f,"{\"modeled_bytes\":%llu,\"active_bits\":%llu,\"mentions\":%llu,\"donor_pairs\":%llu,\"parent_bits\":%.18Lg,\"relation_bits\":%.18Lg,\"mixed_bits\":%.18Lg,\"active_parent_bits\":%.18Lg,\"active_mixed_bits\":%.18Lg}\n",(unsigned long long)model->modeled(),(unsigned long long)model->active_bits,(unsigned long long)model->mentions,(unsigned long long)model->pairs,parent_bits,relation_bits,mixed_bits,active_parent_bits,active_mixed_bits);
 if(std::fclose(f))die("relational summary close");}
 model.reset();
}
}
