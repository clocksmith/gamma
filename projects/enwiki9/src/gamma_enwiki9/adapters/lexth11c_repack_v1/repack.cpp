// Gamma lossless role-conditioned weights encoder, GPLv3; see COPYING.
// Native tensor parsing and float/RoPE coding retain lexth11c's implementation.
#define GAMMA_ENCODER_RAW 1
#include "weights_io_compressed.cpp"
#include <algorithm>
#include <fstream>
#include <iostream>

namespace fx2 {
struct Encoder {
  uint64_t low=0;
  uint32_t range=0xffffffffu;
  uint8_t cache=0;
  uint64_t cache_size=1;
  std::vector<uint8_t> out;
  void shift() {
    uint32_t lo=uint32_t(low), hi=uint32_t(low>>32);
    if(lo<0xff000000u || hi) {
      uint8_t temp=cache;
      do {out.push_back(uint8_t(temp+hi));temp=0xff;} while(--cache_size);
      cache=uint8_t(lo>>24);
    }
    cache_size++;low=uint32_t(lo<<8);
  }
  void normalize() {while(range<(1u<<24)){range<<=8;shift();}}
  void bit(uint16_t& prob,int b) {
    uint32_t bound=(range>>11)*prob;
    if(!b){range=bound;prob=uint16_t(prob+((2048-prob)>>5));}
    else{low+=bound;range-=bound;prob=uint16_t(prob-(prob>>5));}
    normalize();
  }
  void tree(uint16_t* probs,int bits,uint32_t symbol) {
    uint32_t node=1;
    for(int i=bits-1;i>=0;i--){int b=(symbol>>i)&1;bit(probs[node],b);node=(node<<1)|b;}
  }
  void freq(ClassModel& m,uint32_t s) {
    uint32_t cum=0;for(uint32_t i=0;i<s;i++)cum+=m.cnt[i];
    uint32_t r=range/m.tot;low+=uint64_t(r)*cum;
    range=s==m.k-1?range-r*cum:r*m.cnt[s];normalize();m.update(s);
  }
  void finish(){for(int i=0;i<5;i++)shift();}
};

std::vector<std::string> names(const WeightsFile& wf) {
  std::vector<std::string> n;
  for(auto& kv:wf.tensors)n.push_back(kv.first);
  std::sort(n.begin(),n.end(),[](const std::string& a,const std::string& b){
    if(a==b)return false;if(a=="rope.inv_freq")return true;
    if(b=="rope.inv_freq")return false;return a<b;
  });return n;
}

void save_raw(const WeightsFile& wf,const char* path) {
  std::ofstream f(path,std::ios::binary);
  auto u32=[&](uint32_t v){f.write(reinterpret_cast<char*>(&v),4);};
  f.write("FX2TFW01",8);u32(wf.tensors.size());
  for(auto& name:names(wf)) {
    const auto& t=wf.get(name);u32(name.size());f.write(name.data(),name.size());
    f.put(char(t.dtype));u32(t.shape.size());for(auto d:t.shape)u32(d);
    f.write(reinterpret_cast<const char*>(t.data.data()),t.data.size());
  }
  if(!f)die("write failed: %s",path);
}

void save_v4(const WeightsFile& wf,const char* path) {
  Encoder enc;ModelsV2 m;std::map<std::string,ClassModel> classes;
  auto meta=[&](uint8_t b){enc.tree(&m.meta[size_t(m.meta_prev)*256],8,b);m.meta_prev=b;};
  for(auto& name:names(wf)) {
    const auto& t=wf.get(name);if(name.size()>255)die("name too long");
    meta(name.size());uint32_t c2=0,c1=0;
    for(uint8_t ch:name){enc.tree(&m.name[size_t((c2<<8)|c1)*256],8,ch);c2=c1;c1=ch;}
    meta(t.dtype);meta(t.shape.size());for(auto d:t.shape)for(int k=0;k<4;k++)meta(uint8_t(d>>(8*k)));
    int qmax=0;if(t.dtype==DT_I8)for(size_t i=0;i<t.numel;i++)qmax=std::max(qmax,std::abs(int(t.i8()[i])));
    uint8_t kind=t.dtype==DT_I8?(qmax<=127?ENC_ADAPT:ENC_RAW):
      t.dtype==DT_BF16?ENC_BF16:ENC_PLANE4;
    if(t.dtype==DT_F32 && t.shape.size()==2 && (name=="rope.sin" || name=="rope.cos")) {
      const auto& inv=wf.get("rope.inv_freq");bool equal=inv.numel==t.shape[1];
      for(size_t pos=0;equal && pos<t.shape[0];pos++)for(size_t col=0;col<t.shape[1];col++) {
        float v=sincosf_cuda(float(pos)*inv.f32()[col],name=="rope.cos");
        if(std::memcmp(&v,t.data.data()+4*(pos*t.shape[1]+col),4)) {equal=false;break;}
      }
      if(equal)kind=name=="rope.sin"?ENC_ROPE_SIN:ENC_ROPE_COS;
    }
    meta(kind);
    if(kind==ENC_ADAPT) {
      meta(qmax);auto& cm=classes[role_key(name,qmax)];if(!cm.k)cm.init(2*qmax+1);
      for(size_t i=0;i<t.numel;i++)enc.freq(cm,uint32_t(int(t.i8()[i])+qmax));
    } else if(kind==ENC_BF16) {
      for(size_t i=0;i<t.numel;i++){uint16_t v=t.bf16_bits()[i];uint8_t hi=v>>8;
        enc.tree(m.bf16_hi.data(),8,hi);enc.tree(&m.bf16_lo[hi*256],8,v&255);}
    } else if(kind==ENC_PLANE4) {
      for(size_t i=0;i<t.data.size();i++)enc.tree(&m.plane[(i&3)*256],8,t.data[i]);
    } else if(kind==ENC_RAW) {
      for(uint8_t b:t.data)enc.tree(m.raw.data(),8,b);
    }
  }
  enc.finish();std::ofstream f(path,std::ios::binary);uint32_t count=wf.tensors.size();
  f.write("FX2TFWC4",8);f.write(reinterpret_cast<char*>(&count),4);
  f.write(reinterpret_cast<const char*>(enc.out.data()),enc.out.size());
  if(!f)die("write failed: %s",path);
  std::cout<<"classes="<<classes.size()<<" bytes="<<enc.out.size()+12<<"\n";
}
}

int main(int argc,char** argv) {
  if(argc!=5){std::cerr<<"usage: repack ORIGINAL NEW ORIGINAL_RAW NEW_RAW\n";return 2;}
  auto a=fx2::WeightsFile::load_compressed(argv[1]);fx2::save_raw(a,argv[3]);
  fx2::save_v4(a,argv[2]);auto b=fx2::WeightsFile::load_compressed(argv[2]);
  fx2::save_raw(b,argv[4]);
  if(a.tensors.size()!=b.tensors.size())return 3;
  for(auto& kv:a.tensors) {
    auto it=b.tensors.find(kv.first);if(it==b.tensors.end())return 4;
    const auto& x=kv.second;const auto& y=it->second;
    if(x.dtype!=y.dtype || x.shape!=y.shape || x.data!=y.data)return 5;
  }
  a.promote_small_bf16_to_f32();b.promote_small_bf16_to_f32();
  for(auto& kv:a.tensors){const auto& y=b.get(kv.first);if(kv.second.dtype!=y.dtype || kv.second.shape!=y.shape || kv.second.data!=y.data)return 6;}
  std::cout<<"raw_and_native_tensors_bit_identical="<<a.tensors.size()<<"\n";return 0;
}
