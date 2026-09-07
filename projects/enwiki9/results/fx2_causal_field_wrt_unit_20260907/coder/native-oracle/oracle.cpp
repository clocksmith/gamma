
#include <fstream>
#include <iostream>
#include <vector>
struct Predictor {
  std::vector<unsigned> q; unsigned pos=0;
  unsigned Predict() { return q.at(pos); }
  void Perceive(int) { ++pos; }
};
struct Encoder {
  std::ofstream* os_; unsigned x1_,x2_; Predictor* p_; std::vector<unsigned char> out_;
  Encoder(std::ofstream*,Predictor*); void WriteByte(unsigned); unsigned Discretize(float);
  void Encode(int); void Flush();
};
struct Decoder {
  std::ifstream* is_; unsigned x1_,x2_,x_; Predictor* p_;
  Decoder(std::ifstream*,Predictor*); int ReadByte(); unsigned Discretize(float); int Decode();
};

Encoder::Encoder(std::ofstream* os, Predictor* p) : os_(os), x1_(0),
    x2_(0xffffffff), p_(p) {}

void Encoder::WriteByte(unsigned int byte) {
  out_.push_back(byte);
}

unsigned int Encoder::Discretize(float p) {
  return 1 + 65534 * p;
}

void Encoder::Encode(int bit) {
  const unsigned int p = p_->Predict();
  const unsigned int xmid = x1_ + ((x2_ - x1_) >> 16) * p +
      (((x2_ - x1_) & 0xffff) * p >> 16);
  if (bit) {
    x2_ = xmid;
  } else {
    x1_ = xmid + 1;
  }
  p_->Perceive(bit);

  while (((x1_^x2_) & 0xff000000) == 0) {
    WriteByte(x2_ >> 24);
    x1_ <<= 8;
    x2_ = (x2_ << 8) + 255;
  }
}

void Encoder::Flush() {
  while (((x1_^x2_) & 0xff000000) == 0) {
    WriteByte(x2_ >> 24);
    x1_ <<= 8;
    x2_ = (x2_ << 8) + 255;
  }
  WriteByte(x2_ >> 24);

  auto* data = reinterpret_cast<const char*>(out_.data());
  os_->write(data, out_.size());
}


Decoder::Decoder(std::ifstream* is, Predictor* p) : is_(is), x1_(0),
    x2_(0xffffffff), x_(0), p_(p) {
  for (int i = 0; i < 4; ++i) {
    x_ = (x_ << 8) + (ReadByte() & 0xff);
  }
}

int Decoder::ReadByte() {
  int byte = (unsigned char)(is_->get());
  if (!is_->good()) return 0;
  return byte;
}

unsigned int Decoder::Discretize(float p) {
  return 1 + 65534 * p;
}

int Decoder::Decode() {
  const unsigned int p = p_->Predict();
  const unsigned int xmid = x1_ + ((x2_ - x1_) >> 16) * p +
      (((x2_ - x1_) & 0xffff) * p >> 16);
  int bit = 0;
  if (x_ <= xmid) {
    bit = 1;
    x2_ = xmid;
  } else {
    x1_ = xmid + 1;
  }
  p_->Perceive(bit);

  while (((x1_^x2_) & 0xff000000) == 0) {
    x1_ <<= 8;
    x2_ = (x2_ << 8) + 255;
    x_ = (x_ << 8) + ReadByte();
  }
  return bit;
}
int main(int argc,char** argv) {
  if(argc!=2) return 2;
  unsigned n; if(!(std::cin>>n)||n>65536) return 3;
  Predictor pe,pd; std::vector<unsigned> bits;
  for(unsigned i=0;i<n;++i) {unsigned q,b; if(!(std::cin>>q>>b)||!q||q>65535||b>1) return 4;
    pe.q.push_back(q); pd.q.push_back(q); bits.push_back(b);}
  std::ofstream out(argv[1],std::ios::binary); Encoder e(&out,&pe);
  for(unsigned b:bits) {e.Encode(b); std::cout<<"E "<<e.x1_<<" "<<e.x2_<<"\n";}
  e.Flush(); out.close(); std::ifstream in(argv[1],std::ios::binary); Decoder d(&in,&pd);
  for(unsigned i=0;i<n;++i) {int b=d.Decode(); std::cout<<"D "<<b<<" "<<d.x1_<<" "<<d.x2_<<"\n";}
}
