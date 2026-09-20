// Development-only retained-trace diagnostic. No coder or parent mutation.
#include "predictors/causal_relational_v2.hpp"
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <set>
#include <stdexcept>

namespace coverage {
using namespace gamma_relational;
void check(bool v) { if(!v) throw std::runtime_error("coverage invariant"); }
struct Reader {
  const Bytes& data; size_t pos=0;
  uint64_t number() { check(pos+8<=data.size()); uint64_t v=0;
    for(unsigned j=0;j<8;++j)v|=uint64_t(data[pos++])<<(8*j); return v; }
  Bytes bytes() { auto n=number();check(n<=data.size()-pos);
    Bytes out(data.begin()+pos,data.begin()+pos+n);pos+=n;return out; }
  Record record() { Record r;r.stored=bytes();r.raw=bytes();r.end=number();return r; }
};
struct View {
  Bytes raw,stored; unsigned role=2,field=0; bool eligible=false,in_tag=false;
};
// Read the sealed implementation's state rather than implementing another parser.
View view(const Bytes& state) {
  check(state.size()>4&&Bytes(state.begin(),state.begin()+4)==Bytes({'R','G','0','2'}));
  Reader r{state,4};r.bytes();auto fields=r.bytes();std::array<uint64_t,17> f{};
  for(auto& v:f)v=r.number();auto pending=r.bytes();auto word=r.record();
  check(f[1]==0); View v;v.raw=word.raw;v.stored=word.stored;
  v.stored.insert(v.stored.end(),pending.begin(),pending.end());
  v.role=f[3];v.field=fields.at(0);v.in_tag=f[4];
  v.eligible=v.role<2&&!f[8]&&!f[9]&&!v.raw.empty();return v;
}
std::vector<size_t> paired(const std::vector<Record>& pool,uint64_t* checks=nullptr) {
  check(pool.size()<=Capacity);std::array<bool,Capacity> used{};std::vector<size_t> out;
  for(size_t j=pool.size();j>0;--j){size_t right=j-1;if(used[right])continue;
    for(size_t k=right;k>0;--k){size_t wrong=k-1;if(checks)++*checks;
      if(!used[wrong]&&pool[wrong].stored.size()==pool[right].stored.size()&&pool[wrong].raw!=pool[right].raw&&pool[wrong].stored!=pool[right].stored){
        out.push_back(right);used[right]=used[wrong]=true;break;}}}
  return out;
}
struct Search {
  uint64_t examined=0,compared=0,raw_matches=0,coordinate_rejections=0,pair_checks=0;
};
bool matches(const Record& donor,const View& v,unsigned bit,unsigned prefix,Search& work) {
  ++work.examined;
  if(donor.raw.size()<=v.raw.size())return false;
  for(size_t i=0;i<v.raw.size();++i){++work.compared;if(donor.raw[i]!=v.raw[i])return false;}
  ++work.raw_matches;
  if(donor.stored.size()<=v.stored.size()){++work.coordinate_rejections;return false;}
  for(size_t i=0;i<v.stored.size();++i){++work.compared;if(donor.stored[i]!=v.stored[i]){++work.coordinate_rejections;return false;}}
  if(bit && unsigned(donor.stored[v.stored.size()]>>(8-bit))!=prefix){++work.coordinate_rejections;return false;}
  return true;
}
uint32_t emission(uint32_t p,const std::vector<Record>& pool,const std::vector<size_t>& found,size_t pos,unsigned bit) {
  if(found.empty())return p;uint64_t sum=0;
  for(auto i:found){unsigned b=(pool[i].stored[pos]>>(7-bit))&1;sum+=(p+(b?65535u:1u)+1)/2;}
  auto q=uint32_t((sum+found.size()/2)/found.size());check(q>0&&q<65536);return q;
}
struct Prediction {
  std::array<uint32_t,3> q{};std::array<std::vector<size_t>,3> found;
  bool extra_cap=false,extra_pool=false,extra_pair=false;uint64_t remaining_min=0,remaining_max=0;
};
Prediction predict(uint32_t p,const View& v,unsigned bit,unsigned prefix,
                   const std::vector<Record>& pool,Search& work) {
  Prediction o;o.q.fill(p);if(!v.eligible)return o;
  auto eligible=paired(pool,&work.pair_checks);auto early=eligible;early.resize(std::min(early.size(),Slots));
  for(size_t i=0;i<pool.size();++i)if(matches(pool[i],v,bit,prefix,work)){
    o.found[2].push_back(i);
    bool a=std::find(early.begin(),early.end(),i)!=early.end();
    bool b=std::find(eligible.begin(),eligible.end(),i)!=eligible.end();
    if(a)o.found[0].push_back(i);if(b)o.found[1].push_back(i);
    if(!a){o.extra_pool=true;o.extra_cap|=b;o.extra_pair|=!b;
      auto n=8*(pool[i].stored.size()-v.stored.size())-bit;
      if(!o.remaining_min||n<o.remaining_min)o.remaining_min=n;
      o.remaining_max=std::max(o.remaining_max,n);}
  }
  for(size_t i=0;i<3;++i)o.q[i]=emission(p,pool,o.found[i],v.stored.size(),bit);return o;
}
struct Costs {
  uint64_t events=0;double parent=0;std::array<double,3> expert{};
  void add(uint32_t p,const Prediction& pred,unsigned truth) {
    ++events;parent-=std::log2(double(truth?p:65536-p)/65536);
    for(size_t i=0;i<3;++i)expert[i]-=std::log2(double(truth?pred.q[i]:65536-pred.q[i])/65536);
  }
  void json(std::ostream& out)const {
    out<<"{\"events\":"<<events<<",\"parent_bits\":"<<parent<<",\"expert_bits\":["<<expert[0]<<','<<expert[1]<<','<<expert[2]<<"]}";
  }
};
Bytes read(const std::string& path) { std::ifstream f(path,std::ios::binary);check(bool(f));return Bytes(std::istreambuf_iterator<char>(f),{}); }
void write(const std::string& path,const Bytes& data) {std::ofstream f(path,std::ios::binary);f.write(reinterpret_cast<const char*>(data.data()),data.size());check(bool(f));}
bool letters(const Bytes& raw) {return !raw.empty()&&std::all_of(raw.begin(),raw.end(),[](uint8_t c){return (c>='a'&&c<='z')||(c>='A'&&c<='Z');});}
}

#ifndef COVERAGE_NO_MAIN
int main(int argc,char** argv)try {
  using namespace coverage;check(argc==5);
  auto dictionary=read(argv[1]),trace=read(argv[2]),expected=read(argv[3]);std::string output=argv[4];
  check(trace.size()%24==0&&expected.size()==250000);std::vector<std::string> words;std::string word;
  for(auto c:dictionary){if(c>='a'&&c<='z')word+=char(c);else if(!word.empty()){words.push_back(word);word.clear();}}
  check(word.empty()&&words.size()==44515);Model model(words,expected.size(),'S');
  std::array<std::vector<Record>,2> pools;Search work;Costs all,cap,pool,pair;
  uint64_t discoveries=0,single=0,multiple=0,raw_words=0,word_emissions=0,word_length=0;
  size_t max_state=0,max_records=0,raw_position=0;std::set<uint64_t> seen;Bytes raw,witness;
  std::ofstream events(output+".tsv");check(bool(events));
  events<<"event\trole\tp1\tearly_p1\teligible_p1\tpool_p1\tearly_count\teligible_count\tpool_count\tremaining_min\tremaining_max\ttruth\n";
  double original_parent=0,original_expert=0,original_mixture=0;View v;
  unsigned prefix=0;
  for(size_t row=0;row<trace.size()/3;++row){unsigned bit=row%8;
    if(!bit){auto state=model.state();max_state=std::max(max_state,state.size());v=view(state);prefix=0;
      if(v.raw.empty())seen.clear();}
    uint32_t p=trace[3*row]|(uint32_t(trace[3*row+1])<<8);check(p>0&&p<65536);
    const auto& history=pools[v.role<2?v.role:0];auto pred=predict(p,v,bit,prefix,history,work);
    for(auto i:pred.found[2])if(std::find(pred.found[0].begin(),pred.found[0].end(),i)==pred.found[0].end()){
      if(seen.insert(history[i].end).second)++discoveries;}
    // No truth is supplied to view(), selection or prediction.
    unsigned truth=trace[3*row+2];check(truth<2);all.add(p,pred,truth);
    if(pred.extra_cap)cap.add(p,pred,truth);if(pred.extra_pair)pair.add(p,pred,truth);
    if(pred.extra_pool){pool.add(p,pred,truth);
      events<<row<<'\t'<<v.role<<'\t'<<p;
      for(auto q:pred.q)events<<'\t'<<q;for(const auto& f:pred.found)events<<'\t'<<f.size();
      events<<'\t'<<pred.remaining_min<<'\t'<<pred.remaining_max<<'\t'<<truth<<'\n';}
    model.predict(p);auto cost=[&](uint32_t q){return -std::log2(double(truth?q:65536-q)/65536);};
    original_parent+=cost(p);original_expert+=cost(model.relational());original_mixture+=cost(model.mixed());
    check(model.observe(truth,raw));prefix=(prefix<<1)|truth;
    check(raw_position+raw.size()<=expected.size()&&std::equal(raw.begin(),raw.end(),expected.begin()+raw_position));raw_position+=raw.size();
    if(!raw.empty()){
      if(letters(raw)&&!v.in_tag&&(v.field==1||v.field==6)){++word_emissions;word_length+=raw.size();}
      else {if(word_length>=3){++raw_words;if(word_emissions==1)++single;else ++multiple;}word_emissions=word_length=0;}
    }
    if(bit==7&&model.modeled()%Epoch==0){
      for(unsigned r=0;r<2;++r){pools[r]=model.records(r);max_records=std::max(max_records,pools[r].size());}
      seen.clear();if(!raw.empty()){put(witness,model.modeled());blob(witness,model.state());}
    }
  }
  check(raw_position==expected.size()&&model.finish());put(witness,model.modeled());blob(witness,model.state());write(output+".state",witness);
  check(bool(events));std::ofstream out(output+".json");out<<std::setprecision(17);
  out<<"{\"schema\":\"gamma.enwiki9.donor-coverage-measurement.v1\",\"all\":";all.json(out);
  out<<",\"additional_cap\":";cap.json(out);out<<",\"additional_pool\":";pool.json(out);out<<",\"additional_pair_filter\":";pair.json(out);
  out<<",\"additional_donor_discoveries_per_mention_epoch\":"<<discoveries
     <<",\"search\":{\"records_examined\":"<<work.examined<<",\"bytes_compared\":"<<work.compared<<",\"raw_prefix_matches\":"<<work.raw_matches<<",\"coordinate_rejections\":"<<work.coordinate_rejections<<",\"pair_checks\":"<<work.pair_checks<<"}"
     <<",\"geometry\":{\"completed_words_ge3\":"<<raw_words<<",\"single_emission_words\":"<<single<<",\"multiple_emission_words\":"<<multiple<<"}"
     <<",\"max_sealed_state_bytes\":"<<max_state<<",\"max_frozen_records_per_role\":"<<max_records
     <<",\"original\":{\"parent_bits\":"<<original_parent<<",\"relation_bits\":"<<original_expert<<",\"mixed_bits\":"<<original_mixture<<"},\"raw_exact\":true}\n";
  check(bool(out));return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
#endif
