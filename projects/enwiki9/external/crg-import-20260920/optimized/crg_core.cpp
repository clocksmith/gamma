// CRG2 native payload engine. MIT license; research code, NOT a prize winner.
// Python crg_fast.py owns framing, SHA-256 validation and output publication.
// Numerical prediction and arithmetic coding use integers only.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
#include <limits>
using U64=std::uint64_t;
using U32=std::uint32_t;
using U16=std::uint16_t;
using Byte=std::uint8_t;
using Wide=__uint128_t;
constexpr U64 Q=65536, POST=U64(1)<<40;
constexpr U64 HALF=U64(1)<<31, QUARTER=U64(1)<<30, THREE=3*QUARTER, MASK=(U64(1)<<32)-1;
constexpr size_t BUFFER=65536, CONTEXT_SLOTS=1<<16, HIGH_SLOTS=1<<18;
void need(bool x,const char* message){
  if(!x)throw std::runtime_error(message);
}
U32 clamp(U64 x){
  return U32(std::max<U64>(1,std::min<U64>(Q-1,x)));
}
struct File {
  FILE* p;
  explicit File(const std::string& path,const char* mode):p(std::fopen(path.c_str(),mode)){
    need(p,"cannot open file");
  }
  ~File(){
    if(p)std::fclose(p);
  }
  void close(){
    auto f=p;
    p=nullptr;
    need(std::fclose(f)==0,"file close failed");
  }
  File(const File&)=delete;
  File& operator=(const File&)=delete;
};
struct Output {
  FILE* p;
  std::array<Byte,BUFFER> a{
  };
  size_t used=0;
  U64 bytes=0;
  explicit Output(FILE* f):p(f){
  }
  void put(Byte b){
    a[used++]=b;
    if(used==a.size())flush();
  }
  void flush(){
    if(used){
      need(std::fwrite(a.data(),1,used,p)==used,"write failed");
      bytes+=used;
      used=0;
    }
  }
};
struct BitWriter {
  Output out;
  U64 bits=0;
  Byte value=0;
  unsigned used=0;
  explicit BitWriter(FILE* f):out(f){
  }
  void put(unsigned b){
    value=Byte((unsigned(value)<<1)|b);
    ++bits;
    if(++used==8){
      out.put(value);
      used=0;
      value=0;
    }
  }
  void finish(){
    if(used)out.put(Byte(unsigned(value)<<(8-used)));
    used=0;
    out.flush();
  }
};
struct BitReader {
  FILE* p;
  U64 limit,read=0;
  std::array<Byte,BUFFER>a{
  };
  size_t have=0,pos=0;
  Byte value=0;
  unsigned left=0;
  BitReader(FILE* f,U64 n):p(f),limit(n){
  }
  unsigned get(){
    need(read<limit,"arithmetic payload exhausted");
    if(!left){
      if(pos==have){
        have=std::fread(a.data(),1,a.size(),p);
        pos=0;
        need(have>0,"truncated payload");
      }
      value=a[pos++];
      left=8;
    }
    ++read;
    return(value>>--left)&1u;
  }
};
struct Encoder {
  BitWriter w;
  U64 low=0,high=MASK,pending=0;
  explicit Encoder(FILE* f):w(f){
  }
  void emit(unsigned b){
    w.put(b);
    while(pending){
      w.put(1-b);
      --pending;
    }
  }
  void put(unsigned bit,U32 p){
    U64 split=low+((high-low+1)*(Q-p)/Q);
    if(bit)low=split;
    else high=split-1;
    for(;;){
      if(high<HALF)emit(0);
      else if(low>=HALF){
        emit(1);
        low-=HALF;
        high-=HALF;
      }
      else if(low>=QUARTER&&high<THREE){
        ++pending;
        low-=QUARTER;
        high-=QUARTER;
      }
      else break;
      low<<=1;
      high=(high<<1)|1;
    }
  }
  void finish(){
    ++pending;
    emit(low<QUARTER?0:1);
    for(int i=0;i<32;++i)w.put(0);
    w.finish();
  }
};
struct Decoder {
  BitReader r;
  U64 low=0,high=MASK,code=0;
  Decoder(FILE* f,U64 n):r(f,n){
    for(int i=0;i<32;++i)code=(code<<1)|r.get();
  }
  unsigned get(U32 p){
    U64 split=low+((high-low+1)*(Q-p)/Q);
    unsigned b=code>=split;
    if(b)low=split;
    else high=split-1;
    for(;;){
      if(high<HALF){
      }
      else if(low>=HALF){
        low-=HALF;
        high-=HALF;
        code-=HALF;
      }
      else if(low>=QUARTER&&high<THREE){
        low-=QUARTER;
        high-=QUARTER;
        code-=QUARTER;
      }
      else break;
      low<<=1;
      high=(high<<1)|1;
      code=(code<<1)|r.get();
    }
    return b;
  }
};
std::vector<U64> uniform(size_t n){
  std::vector<U64>w(n);
  if(n)for(size_t i=0;i<n;++i)w[i]=POST/n+(i<POST%n);
  return w;
}
void update(std::vector<U64>& w,const std::vector<U32>& p,unsigned bit){
  if(w.empty()||std::all_of(p.begin(),p.end(),[&](U32 v){
    return v==p[0];
  }))return;
  need(w.size()==p.size()&&w.size()<=4,"posterior geometry");
  std::array<Wide,4> products{
  },remainders{
  };
  Wide total=0;
  size_t n=w.size();
  for(size_t i=0;i<n;++i){
    products[i]=Wide(w[i])*(bit?p[i]:Q-p[i]);
    total+=products[i];
  }
  U64 used=0;
  for(size_t i=0;i<n;++i){
    Wide v=products[i]*(POST-n);
    w[i]=1+U64(v/total);
    remainders[i]=v%total;
    used+=w[i];
  }
  std::array<bool,4>picked{
  };
  for(;used<POST;++used){
    size_t best=n;
    for(size_t i=0;i<n;++i)if(!picked[i]&&(best==n||remainders[i]>remainders[best]))best=i;
    need(best<n,"posterior overflow");
    picked[best]=true;
    ++w[best];
  }
}
U32 marginal(const std::vector<U64>&w,const std::vector<U32>&p){
  U64 sum=POST/2;
  for(size_t i=0;i<w.size();++i)sum+=w[i]*p[i];
  return clamp(sum/POST);
}
void increment(std::vector<U16>&v,size_t i,unsigned bit){
  ++v[i+bit];
  if(unsigned(v[i])+v[i+1]>=512){
    v[i]=(v[i]+1)/2;
    v[i+1]=(v[i+1]+1)/2;
  }
}
struct Context {
  std::vector<U16>c0,c1,c2;
  std::vector<U32>tags;
  unsigned previous=256,last_two=0;
  U64 nbytes=0;
  size_t i0=0,i1=0,i2=0;
  U32 key=0;
  Context():c0(512),c1(257*256*2),c2(CONTEXT_SLOTS*2),tags(CONTEXT_SLOTS){
  }
  U32 predict(unsigned prefix){
    i0=prefix*2;
    i1=((previous<<8)|prefix)*2;
    U64 p=Q*(c0[i0+1]+1)/(c0[i0]+c0[i0+1]+2);
    p=(Q*c1[i1+1]+8*p)/(c1[i1]+c1[i1+1]+8);
    key=((last_two<<8)|prefix)+1;
    i2=((U64(key^(key>>11))*2654435761u)&(CONTEXT_SLOTS-1))*2;
    if(nbytes>=2&&tags[i2/2]==key){
      p=(Q*c2[i2+1]+12*p)/(c2[i2]+c2[i2+1]+12);
    }
    return clamp(p);
  }
  void observe(unsigned bit){
    increment(c0,i0,bit);
    increment(c1,i1,bit);
    if(nbytes>=2){
      if(tags[i2/2]!=key){
        tags[i2/2]=key;
        c2[i2]=c2[i2+1]=0;
      }
      increment(c2,i2,bit);
    }
  }
  void end_byte(unsigned b){
    previous=b;
    last_two=((last_two<<8)|b)&65535;
    ++nbytes;
  }
};
// Separate enhanced profile: interpolated suffix contexts, lengths 2..6.
// No learned files or donor addresses; exact tag matches reject hash collisions.
struct HighContext {
  std::vector<U16>c0,c1;
  std::array<std::vector<U16>,5>counts;
  std::array<std::vector<U64>,5>tags;
  std::array<size_t,5>index{
  };
  std::array<U64,5>key{
  };
  unsigned previous=256;
  U64 history=0,nbytes=0;
  size_t i0=0,i1=0;
  HighContext():c0(512),c1(257*256*2){
    for(size_t i=0;i<5;++i){
      counts[i].resize(HIGH_SLOTS*2);
      tags[i].resize(HIGH_SLOTS);
    }
  }
  static U64 hash(U64 x){
    x^=x>>30;
    x*=0xbf58476d1ce4e5b9ULL;
    x^=x>>27;
    x*=0x94d049bb133111ebULL;
    return x^(x>>31);
  }
  U32 predict(unsigned prefix){
    i0=prefix*2;
    i1=((previous<<8)|prefix)*2;
    U64 p=Q*(c0[i0+1]+1)/(c0[i0]+c0[i0+1]+2);
    p=(Q*c1[i1+1]+8*p)/(c1[i1]+c1[i1+1]+8);
    for(unsigned j=0;j<5;++j){
      unsigned order=j+2;
      key[j]=(((history&((U64(1)<<(8*order))-1))<<8)|prefix)+1;
      index[j]=(hash(key[j])&(HIGH_SLOTS-1))*2;
      if(nbytes>=order&&tags[j][index[j]/2]==key[j]){
        auto&c=counts[j];
        auto i=index[j];
        p=(Q*c[i+1]+4*p)/(c[i]+c[i+1]+4);
      }
    }
    return clamp(p);
  }
  void observe(unsigned bit){
    increment(c0,i0,bit);
    increment(c1,i1,bit);
    for(unsigned j=0;j<5;++j)if(nbytes>=j+2){
      auto&c=counts[j];
      auto i=index[j];
      if(tags[j][i/2]!=key[j]){
        tags[j][i/2]=key[j];
        c[i]=c[i+1]=0;
      }
      increment(c,i,bit);
    }
  }
  void end_byte(unsigned b){
    previous=b;
    history=((history<<8)|b)&0xffffffffffffULL;
    ++nbytes;
  }
};
bool letter(unsigned b){
  return(b>=65&&b<=90)||(b>=97&&b<=122);
}
void remember(std::deque<std::string>&p,const std::string&w){
  auto it=std::find(p.begin(),p.end(),w);
  if(it!=p.end())p.erase(it);
  if(p.size()==32)p.pop_front();
  p.push_back(w);
}
bool space(unsigned char c){
  return c==9||c==10||c==11||c==12||c==13||c==32;
}
std::string trim(std::string s){
  size_t a=0,b=s.size();
  while(a<b&&space(s[a]))++a;
  while(b>a&&space(s[b-1]))--b;
  return s.substr(a,b-a);
}
struct Parser {
  std::deque<std::string>title,body,pending_title;
  int field=0;
  bool in_tag=false,tag_overflow=false,inside_word=false,word_overflow=false,link=false;
  std::string tag,word;
  unsigned quote=0,previous=0;
  void finish_word(){
    if(!word_overflow&&word.size()>=3&&word.size()<=64){
      if(field==1)remember(pending_title,word);
      else if(field==2)remember(body,word);
    }
    word.clear();
    word_overflow=false;
    inside_word=false;
  }
  void finish_tag(){
    if(!tag_overflow){
      auto s=trim(tag);
      bool closing=!s.empty()&&s[0]=='/';
      if(closing)s=trim(s.substr(1));
      size_t n=0;
      while(n<s.size()&&!space(s[n]))++n;
      auto name=s.substr(0,n);
      while(!name.empty()&&name.back()=='/')name.pop_back();
      bool self=!s.empty()&&s.back()=='/';
      if(name=="page"){
        title.clear();
        body.clear();
        pending_title.clear();
        field=0;
        link=false;
      }
      else if(name=="title"){
        if(closing){
          title=pending_title;
          pending_title.clear();
          field=0;
        }
        else if(!self){
          pending_title.clear();
          field=1;
        }
      }
      else if(name=="text"){
        field=closing||self?0:2;
        link=false;
      }
    }
    in_tag=false;
    tag.clear();
    tag_overflow=false;
    quote=0;
  }
  void observe(unsigned b){
    if(in_tag){
      if(b==62&&!quote)finish_tag();
      else{
        if(quote){
          if(b==quote)quote=0;
        }
        else if(b==34||b==39)quote=b;
        if(tag.size()<512)tag.push_back(char(b));
        else tag_overflow=true;
      }
      previous=b;
      return;
    }
    if(b==60){
      finish_word();
      in_tag=true;
      tag.clear();
      quote=0;
      tag_overflow=false;
    }
    else{
      if((field==1||field==2)&&letter(b)){
        inside_word=true;
        if(word.size()<64)word.push_back(char(b));
        else word_overflow=true;
      }
      else finish_word();
      if(field==2){
        if(b==91&&previous==91)link=true;
        else if(b==124||b==93)link=false;
      }
    }
    previous=b;
  }
  int role()const{
    return field==2&&!in_tag?(link?1:0):-1;
  }
};
unsigned wrong_byte(unsigned b){
  return b<=90?65+(b-65+13)%26:97+(b-97+13)%26;
}
struct Binding {
  std::vector<std::string>donors;
  std::vector<U64>weights;
  std::vector<bool>active;
  size_t position=0;
  std::vector<U32>probabilities;
  void start(const std::vector<std::string>&d,bool independent){
    if(d!=donors||independent)weights=uniform(d.size());
    donors=d;
    active.assign(d.size(),true);
    position=0;
  }
  U32 predict(U32 parent,unsigned depth,bool wrong){
    probabilities.clear();
    for(size_t i=0;i<donors.size();++i){
      U32 p=parent;
      if(active[i]&&position<donors[i].size()){
        unsigned b=(unsigned char)donors[i][position];
        if(wrong)b=wrong_byte(b);
        unsigned bit=(b>>(7-depth))&1;
        p=(parent+(bit?Q-1:1)+1)/2;
      }
      probabilities.push_back(p);
    }
    return weights.empty()?parent:marginal(weights,probabilities);
  }
  void observe(unsigned bit,unsigned depth,bool wrong){
    update(weights,probabilities,bit);
    for(size_t i=0;i<donors.size();++i)if(active[i]){
      unsigned b=(unsigned char)donors[i][position];
      if(wrong)b=wrong_byte(b);
      if(((b>>(7-depth))&1)!=bit)active[i]=false;
    }
    if(depth==7){
      ++position;
      for(size_t i=0;i<donors.size();++i)if(position>=donors[i].size())active[i]=false;
    }
  }
};
struct Relation {
  char arm;
  Parser parser;
  std::array<Binding,2>banks;
  std::vector<U64>outer=uniform(2);
  int role=-1;
  U32 parent=32768,relational=32768;
  unsigned depth=0;
  U64 active_bits=0,mentions=0;
  explicit Relation(char a):arm(a){
  }
  void begin(){
    role=parser.role();
    if(role>=0&&!parser.inside_word){
      const auto&pool=role==0?parser.title:parser.body;
      std::vector<std::string>d;
      size_t start=pool.size()>4?pool.size()-4:0;
      for(size_t i=start;i<pool.size();++i)d.push_back(pool[i]);
      banks[role].start(d,arm=='I');
      ++mentions;
    }
  }
  U32 predict(U32 p,unsigned dep){
    parent=relational=p;
    depth=dep;
    if(role>=0){
      auto&b=banks[role];
      relational=b.predict(p,dep,arm=='W');
      if(std::any_of(b.active.begin(),b.active.end(),[](bool a){
        return a;
      }))++active_bits;
    }
    return marginal(outer,{
      parent,relational
    });
  }
  void observe(unsigned bit){
    update(outer,{
      parent,relational
    },bit);
    if(role>=0)banks[role].observe(bit,depth,arm=='W');
  }
};
struct Model {
  char arm;
  bool high;
  std::unique_ptr<Context>basic;
  std::unique_ptr<HighContext>strong;
  std::unique_ptr<Relation>r;
  Model(char a,bool h):arm(a),high(h){
    if(high)strong=std::make_unique<HighContext>();
    else basic=std::make_unique<Context>();
    if(arm!='P')r=std::make_unique<Relation>(arm);
  }
  U32 predict(unsigned prefix,unsigned depth){
    U32 p=high?strong->predict(prefix):basic->predict(prefix);
    if(r){
      U32 q=r->predict(p,depth);
      if(arm!='K')p=q;
    }
    return p;
  }
  void observe(unsigned b){
    if(high)strong->observe(b);
    else basic->observe(b);
    if(r)r->observe(b);
  }
  void end(unsigned b){
    if(high)strong->end_byte(b);
    else basic->end_byte(b);
    if(r)r->parser.observe(b);
  }
  void encode(Encoder&e,unsigned b){
    if(r)r->begin();
    unsigned prefix=1;
    for(unsigned dep=0;dep<8;++dep){
      auto p=predict(prefix,dep);
      unsigned bit=(b>>(7-dep))&1;
      e.put(bit,p);
      observe(bit);
      prefix=(prefix<<1)|bit;
    }
    end(b);
  }
  Byte decode(Decoder&d){
    if(r)r->begin();
    unsigned prefix=1;
    for(unsigned dep=0;dep<8;++dep){
      unsigned bit=d.get(predict(prefix,dep));
      observe(bit);
      prefix=(prefix<<1)|bit;
    }
    Byte b=Byte(prefix);
    end(b);
    return b;
  }
};
U64 number(const char*s){
  size_t pos=0;
  std::string v(s);
  need(!v.empty()&&v[0]!='-',"invalid nonnegative integer");
  auto n=std::stoull(v,&pos);
  need(pos==v.size(),"invalid integer");
  return n;
}
int main(int argc,char**argv){
  try{
    need(argc==7||argc==9,"usage: crg_core encode INPUT PAYLOAD P|K|I|S|W PROFILE MAX_BYTES | decode PAYLOAD OUTPUT ARM PROFILE RAW_BYTES PAYLOAD_BITS MAX_BYTES");
    std::string op(argv[1]);
    std::string in(argv[2]),out(argv[3]),armtext(argv[4]);
    need(in!=out,"input equals output");
    need(armtext.size()==1&&std::string("PKISW").find(armtext[0])!=std::string::npos,"bad arm");
    U64 profile=number(argv[5]);
    need(profile<=1,"bad profile");
    std::ifstream existing(out);
    need(!existing.good(),"refusing existing output");
    existing.close();
    File input(in,"rb");
    File output(out,"wbx");
    Model m(armtext[0],profile);
    U64 raw=0,bits=0,payload=0;
    if(op=="encode"&&argc==7){
      U64 max=number(argv[6]);
      Encoder e(output.p);
      std::array<Byte,BUFFER>b{
      };
      for(;;){
        size_t n=std::fread(b.data(),1,b.size(),input.p);
        if(!n)break;
        need(raw+n<=max,"input bound exceeded");
        for(size_t i=0;i<n;++i)m.encode(e,b[i]);
        raw+=n;
      }
      need(!std::ferror(input.p),"read failed");
      e.finish();
      bits=e.w.bits;
      payload=e.w.out.bytes;
    }
    else if(op=="decode"&&argc==9){
      raw=number(argv[6]);
      bits=number(argv[7]);
      need(raw<=number(argv[8])&&bits>=34,"invalid decode bound");
      Decoder d(input.p,bits);
      Output o(output.p);
      for(U64 i=0;i<raw;++i)o.put(m.decode(d));
      o.flush();
      payload=(bits+7)/8;
    }
    else throw std::runtime_error("wrong operation/arguments");
    output.close();
    input.close();
    std::cout<<"{\"raw_bytes\":"<<raw<<",\"payload_bytes\":"<<payload<<",\"payload_bits\":"<<bits<<",\"profile\":"<<profile<<",\"active_bits\":"<<(m.r?m.r->active_bits:0)<<",\"mentions\":"<<(m.r?m.r->mentions:0)<<",\"hutter_qualified\":false}\n";
    return 0;
  }
  catch(const std::exception&e){
    std::cerr<<"error: "<<e.what()<<'\n';
    return 2;
  }
}
