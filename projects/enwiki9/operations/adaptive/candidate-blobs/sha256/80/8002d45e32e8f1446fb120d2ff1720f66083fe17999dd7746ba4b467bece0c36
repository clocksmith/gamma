#ifndef GAMMA_CAUSAL_RELATIONAL_V1_HPP
#define GAMMA_CAUSAL_RELATIONAL_V1_HPP
#include "../fx2_xml_field_observer_v1.hpp"
#include <algorithm>
#include <array>
#include <cstdlib>
#include <limits>

namespace gamma_relational {
using gamma_xml_field::Bytes;
constexpr uint64_t Q = uint64_t(1) << 48;
constexpr size_t Slots=4, Capacity=64, WordStored=32, WordRaw=64, Epoch=4096;
inline void require(bool ok) { if (!ok) std::abort(); }
inline void put(Bytes& out,uint64_t v) { for(unsigned j=0;j<8;++j) out.push_back(uint8_t(v>>(8*j))); }
inline void blob(Bytes& out,const Bytes& v) { put(out,v.size());out.insert(out.end(),v.begin(),v.end()); }

// Largest remainder with one integer quantum per state. No state is pruned.
// Exact products use 128 bits. Equal emissions leave the prior unchanged.
template<size_t N> void update(std::array<uint64_t,N>& w,const std::array<uint32_t,N>& p,unsigned bit) {
  require(bit<2);
  if(std::all_of(p.begin(),p.end(),[&](uint32_t v){return v==p[0];})) return;
  std::array<__uint128_t,N> products{},rem{}; __uint128_t total=0;
  for(size_t i=0;i<N;++i){require(p[i]>0&&p[i]<65536);products[i]=__uint128_t(w[i])*(bit?p[i]:65536-p[i]);total+=products[i];}
  require(total>0);uint64_t assigned=0;
  for(size_t i=0;i<N;++i){const auto s=products[i]*(Q-N);w[i]=1+uint64_t(s/total);rem[i]=s%total;assigned+=w[i];}
  std::array<bool,N> used{};
  for(;assigned<Q;++assigned){size_t best=N;for(size_t i=0;i<N;++i)if(!used[i]&&(best==N||rem[i]>rem[best]))best=i;
    require(best<N);++w[best];used[best]=true;}
}
template<size_t N> uint32_t marginal(const std::array<uint64_t,N>& w,const std::array<uint32_t,N>& p){
  __uint128_t s=Q/2;for(size_t i=0;i<N;++i)s+=__uint128_t(w[i])*p[i];
  return uint32_t(s/Q);
}
struct Record { Bytes stored,raw;uint64_t end=0; };
struct Pair { Record right,wrong; };

// State semantics: a fixed donor identity persists through an epoch; its copy
// cursor follows the decoded mention. A mismatch goes to literal emission until
// the next predetermined boundary. This is a depth-one stochastic transducer.
struct Binding {
  std::array<Pair,Slots> donors{};
  std::array<uint64_t,Slots> weights{};
  std::array<uint32_t,Slots> probabilities{};
  std::array<bool,Slots> active{};
  size_t count=0,position=0;
  Binding(){weights.fill(Q/Slots);}
  void start(bool independent){position=0;for(size_t i=0;i<Slots;++i)active[i]=i<count;if(independent)weights.fill(Q/Slots);}
  uint32_t predict(uint32_t p,unsigned bit_index,bool wrong){
    for(size_t i=0;i<Slots;++i){const auto& donor=wrong?donors[i].wrong:donors[i].right;
      probabilities[i]=p;
      if(active[i]&&position<donor.stored.size()){
        const unsigned b=(donor.stored[position]>>(7-bit_index))&1;
        probabilities[i]=(p+(b?65535u:1u)+1)/2;
      }
    }return marginal(weights,probabilities);
  }
  void observe(unsigned bit,unsigned bit_index,bool wrong){
    update(weights,probabilities,bit);
    for(size_t i=0;i<Slots;++i){const auto& donor=wrong?donors[i].wrong:donors[i].right;
      if(active[i]&&(position>=donor.stored.size()||((donor.stored[position]>>(7-bit_index))&1)!=bit))active[i]=false;
    }
    if(bit_index==7){++position;for(size_t i=0;i<Slots;++i){const auto& d=wrong?donors[i].wrong:donors[i].right;if(position>=d.stored.size())active[i]=false;}}
  }
};

class Model {
 public:
  Model(const std::vector<std::string>& words,uint64_t raw_limit,char arm):inverse_(words,raw_limit),arm_(arm){require(arm=='P'||arm=='K'||arm=='I'||arm=='S'||arm=='W');}
  uint32_t predict(uint32_t p){
    require(!pending_&&p>0&&p<65536);pending_=true;parent_=p;relational_=p;
    if(role_<2){auto& b=binding_[role_];relational_=b.predict(p,bit_,arm_=='W');
      if(std::any_of(b.active.begin(),b.active.end(),[](bool v){return v;}))++active_bits;
    }
    mixed_=marginal(outer_,std::array<uint32_t,2>{p,relational_});
    return arm_=='P'||arm_=='K'?p:mixed_;
  }
  bool observe(unsigned truth,Bytes& raw){
    require(pending_&&truth<2);pending_=false;
    update(outer_,std::array<uint32_t,2>{parent_,relational_},truth);
    if(role_<2)binding_[role_].observe(truth,bit_,arm_=='W');
    byte_=uint8_t((byte_<<1)|truth);raw.clear();
    if(++bit_<8)return true;
    bit_=0;++modeled_; const uint8_t value=byte_;byte_=0;
    if(pending_tokens_.size()<WordStored)pending_tokens_.push_back(value);else pending_overflow_=true;
    if(!inverse_.observe(value,raw))return false;
    if(!raw.empty()){
      // The local parser still represents the pre-emission prefix here.
      bool letters=std::all_of(raw.begin(),raw.end(),[](uint8_t c){return letter(c);});
      if(letters&&(fields_.field()==1||fields_.field()==6)){
        const unsigned source=fields_.field()==1?0:1;
        if(word_.raw.empty())word_role_=source;
        if(word_role_!=source)word_overflow_=true;
        if(word_.raw.size()+raw.size()<=WordRaw&&!pending_overflow_&&word_.stored.size()+pending_tokens_.size()<=WordStored){
          word_.raw.insert(word_.raw.end(),raw.begin(),raw.end());
          word_.stored.insert(word_.stored.end(),pending_tokens_.begin(),pending_tokens_.end());
        }else word_overflow_=true;
      }else{
        commit_word();
      }
      for(uint8_t c:raw){
        fields_.observe(c);
        if(previous_raw_=='['&&c=='[')link_=true;
        if(c=='|'||c==']'||fields_.field()!=6)link_=false;
        previous_raw_=c;
      }
      require(fields_.field()==inverse_.field());
      pending_tokens_.clear();pending_overflow_=false;
      // Start before the unknown next symbol, including after markup. A
      // following punctuation or exception is handled by the literal branch.
      if(!letter(raw.back()))start_mention();
    }
    if(modeled_%Epoch==0){freeze();start_mention(false);}
    return true;
  }
  bool finish(){return !pending_&&bit_==0&&inverse_.finish();}
  uint64_t modeled()const{return modeled_;}
  uint32_t parent()const{return parent_;}uint32_t relational()const{return relational_;}uint32_t mixed()const{return mixed_;}
  uint64_t active_bits=0,mentions=0,pairs=0;
  Bytes state()const{
    Bytes out{'R','G','0','1'};blob(out,inverse_.state());blob(out,fields_.state());
    for(uint64_t v:{modeled_,uint64_t(bit_),uint64_t(byte_),uint64_t(role_),uint64_t(link_),uint64_t(previous_raw_),uint64_t(word_role_),uint64_t(word_overflow_),uint64_t(pending_overflow_),uint64_t(pending_),uint64_t(parent_),uint64_t(relational_),uint64_t(mixed_),active_bits,mentions,pairs})put(out,v);
    blob(out,pending_tokens_);record(out,word_);
    for(auto w:outer_)put(out,w);
    for(const auto& pool:records_){put(out,pool.size());for(const auto& r:pool)record(out,r);}
    for(const auto& b:binding_){put(out,b.count);put(out,b.position);for(size_t i=0;i<Slots;++i){record(out,b.donors[i].right);record(out,b.donors[i].wrong);put(out,b.weights[i]);put(out,b.probabilities[i]);put(out,b.active[i]);}}
    return out;
  }
 private:
  static bool letter(uint8_t c){return (c>='a'&&c<='z')||(c>='A'&&c<='Z');}
  static void record(Bytes& out,const Record& r){blob(out,r.stored);blob(out,r.raw);put(out,r.end);}
  void commit_word(){
    if(!word_overflow_&&word_.raw.size()>=3&&!word_.stored.empty()){
      word_.end=inverse_.raw_count();auto& pool=records_[word_role_];
      // Identity includes exact raw and stored spellings. Old occurrences can
      // be evicted by a declared FIFO rule, never by posterior score.
      pool.erase(std::remove_if(pool.begin(),pool.end(),[&](const Record& r){return r.raw==word_.raw&&r.stored==word_.stored;}),pool.end());
      if(pool.size()==Capacity)pool.erase(pool.begin());
      pool.push_back(word_);
    }
    word_=Record{};word_overflow_=false;
  }
  void freeze(){
    outer_={Q/2,Q/2};
    for(size_t role=0;role<2;++role){binding_[role]=Binding{};auto& b=binding_[role];const auto& pool=records_[role];std::array<bool,Capacity> used{};
      for(size_t j=pool.size();j>0&&b.count<Slots;--j){size_t right=j-1;if(used[right])continue;
        for(size_t k=right;k>0;--k){size_t wrong=k-1;if(!used[wrong]&&pool[wrong].stored.size()==pool[right].stored.size()&&pool[wrong].raw!=pool[right].raw&&pool[wrong].stored!=pool[right].stored){
          b.donors[b.count++]={pool[right],pool[wrong]};used[right]=used[wrong]=true;break;}}
      }pairs+=b.count;
    }
  }
  void start_mention(bool opportunity=true){
    // An epoch reset inside a word must not invent a mention opportunity.
    if(!opportunity){role_=2;return;}
    role_=fields_.field()==6?(link_?1:0):2;
    if(role_<2){binding_[role_].start(arm_=='I');++mentions;}
  }
  gamma_xml_field::Observer inverse_;gamma_xml_field::RawField fields_;char arm_;
  std::array<std::vector<Record>,2> records_{};std::array<Binding,2> binding_{};
  std::array<uint64_t,2> outer_{Q/2,Q/2};
  Record word_;Bytes pending_tokens_;bool word_overflow_=false,pending_overflow_=false,pending_=false,link_=false;
  unsigned word_role_=0,role_=2,bit_=0;uint8_t byte_=0,previous_raw_=0;uint64_t modeled_=0;
  uint32_t parent_=32768,relational_=32768,mixed_=32768;
};
}
#endif
