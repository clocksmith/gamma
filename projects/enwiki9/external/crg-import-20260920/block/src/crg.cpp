// CRG corrected research codec, format CGR1. Not a Hutter Prize claim.
// Original implementation: unsigned, specified integer arithmetic only.
// Model: bounded context interpolation plus optional causal role-word expert.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
namespace crg {
    using Byte=uint8_t;
    using Bytes=std::vector<Byte>;
    constexpr uint64_t Q=65536, TOP=uint64_t(1)<<32, HALF=TOP/2, QUARTER=TOP/4;
    constexpr size_t MAX_BLOCK=1u<<20;
    void need(bool ok,const char* s) {
        if(!ok)throw std::runtime_error(s);
    }
    uint32_t crc32(const Bytes& a) {
        uint32_t c=~uint32_t(0);
        for(Byte b:a) {
            c^=b;
            for(int k=0;k<8;k++)c=(c>>1)^(0xedb88320u&(0u-(c&1u)));
        }
        return ~c;
    }
    void put32(Bytes& b,uint32_t x) {
        for(int i=0;i<4;i++)b.push_back(Byte(x>>(8*i)));
    }
    uint32_t get32(const Bytes& b,size_t& p) {
        need(p+4<=b.size(),"truncated header");
        uint32_t v=0;
        for(int i=0;i<4;i++)v|=uint32_t(b[p++])<<(8*i);
        return v;
    }
    struct BitOut {
        Bytes b;
        unsigned n=0;
        Byte cur=0;
        void put(unsigned bit) {
            cur=Byte((cur<<1)|bit);
            if(++n==8) {
                b.push_back(cur);
                cur=0;
                n=0;
            }
        }
        void finish() {
            if(n) {
                b.push_back(Byte(cur<<(8-n)));
                cur=0;
                n=0;
            }
        }
    };
    struct BitIn {
        const Bytes& b;
        size_t bit=0;
        unsigned get() {
            need(bit<b.size()*8,"truncated arithmetic payload");
            unsigned v=(b[bit/8]>>(7-bit%8))&1;
            ++bit;
            return v;
        }
    };
    // Full E1/E2/E3 renormalization. The uploaded coder omitted the E3 case.
    struct Encoder {
        uint64_t low=0,high=TOP-1,pending=0;
        BitOut out;
        void emit(unsigned b) {
            out.put(b);
            while(pending) {
                out.put(b^1);
                --pending;
            }
        }
        void bit(unsigned b,uint32_t p1) {
            need(b<2&&p1>0&&p1<Q,"invalid symbol probability");
            uint64_t range=high-low+1;
            uint64_t cut=low+(range*(Q-p1))/Q;
            need(cut>low&&cut<=high,"arithmetic interval collapsed");
            if(b)low=cut;
            else high=cut-1;
            for(;;) {
                if(high<HALF)emit(0);
                else if(low>=HALF) {
                    emit(1);
                    low-=HALF;
                    high-=HALF;
                }
                else if(low>=QUARTER&&high<3*QUARTER) {
                    ++pending;
                    low-=QUARTER;
                    high-=QUARTER;
                }
                else break;
                low*=2;
                high=high*2+1;
            }
        }
        Bytes finish() {
            ++pending;
            emit(low<QUARTER?0:1);
            out.finish();
            out.b.insert(out.b.end(),4,0);
            return out.b;
        }
    };
    struct Decoder {
        uint64_t low=0,high=TOP-1,code=0;
        BitIn in;
        explicit Decoder(const Bytes& b):in {
            b
        }
        {
            for(int i=0;i<32;i++)code=(code<<1)|in.get();
        }
        unsigned bit(uint32_t p1) {
            need(p1>0&&p1<Q,"invalid decoder probability");
            need(low<=code&&code<=high,"arithmetic code outside interval");
            uint64_t range=high-low+1,cut=low+(range*(Q-p1))/Q;
            need(cut>low&&cut<=high,"decoder interval collapsed");
            unsigned b=code>=cut;
            if(b)low=cut;
            else high=cut-1;
            for(;;) {
                if(high<HALF) {
                }
                else if(low>=HALF) {
                    code-=HALF;
                    low-=HALF;
                    high-=HALF;
                }
                else if(low>=QUARTER&&high<3*QUARTER) {
                    code-=QUARTER;
                    low-=QUARTER;
                    high-=QUARTER;
                }
                else break;
                low*=2;
                high=high*2+1;
                code=code*2+in.get();
            }
            return b;
        }
    };
    uint64_t mix64(uint64_t v) {
        v^=v>>30;
        v*=0xbf58476d1ce4e5b9ULL;
        v^=v>>27;
        v*=0x94d049bb133111ebULL;
        return v^(v>>31);
    }
    struct Count {
        uint16_t zero=0,one=0;
    };
    struct Slot {
        uint64_t key=0;
        Count c {
        };
        bool used=false;
    };
    struct ContextModel {
        static constexpr size_t BITS=19,SIZE=size_t(1)<<BITS;
        std::array<Count,256> order0 {
        };
        std::vector<Count> order1=std::vector<Count>(65536);
        std::vector<Slot> table=std::vector<Slot>(SIZE);
        std::array<uint64_t,7> keys {
        };
        std::array<Count*,7> pending {
        };
        uint64_t history=0,position=0;
        unsigned prefix=1;
        void begin() {
            uint64_t mask=0;
            for(unsigned k=2;k<=6;k++) {
                mask=k==6?0xffffffffffffULL:((uint64_t(1)<<(8*k))-1);
                keys[k]=mix64((history&mask)^ (0x9e3779b97f4a7c15ULL*k));
            }
        }
        uint32_t predict() {
            uint64_t p=32768;
            unsigned n=0;
            pending[n++]=&order0[prefix];
            if(position)pending[n++]=&order1[((history&255)<<8)|prefix];
            for(unsigned k=2;k<=6&&k<=position;k++) {
                uint64_t key=keys[k]^(uint64_t(prefix)*0xd6e8feb86659fd93ULL);
                Slot& s=table[mix64(key)&(SIZE-1)];
                if(!s.used||s.key!=key) {
                    s= {
                    };
                    s.used=true;
                    s.key=key;
                }
                pending[n++]=&s.c;
            }
            for(unsigned i=n;i<7;i++)pending[i]=nullptr;
            for(unsigned i=0;i<n;i++) {
                auto c=*pending[i];
                uint64_t total=c.zero+c.one;
                constexpr uint64_t prior=12;
                p=(uint64_t(c.one)*Q+prior*p+(total+prior)/2)/(total+prior);
            }
            return uint32_t(std::min<uint64_t>(Q-1,std::max<uint64_t>(1,p)));
        }
        void observe(unsigned b) {
            for(auto* c:pending) {
                if(!c)continue;
                // Colliding aliases are deterministic on both sides.
                if(b)++c->one;
                else ++c->zero;
                if(c->one+c->zero>=1024) {
                    c->one=(c->one+1)/2;
                    c->zero=(c->zero+1)/2;
                }
            }
            prefix=prefix*2+b;
            if(prefix>=256) {
                history=(history<<8)|Byte(prefix-256);
                ++position;
                prefix=1;
            }
        }
    };
    // Bounded classification, not XML validation. Arbitrary/malformed bytes are coded literally.
    // All completed words are exact byte spellings. No target is an input to predict().
    struct History {
        static bool letter(Byte c) {
            return (c>='A'&&c<='Z')||(c>='a'&&c<='z');
        }
        enum Role {
            OTHER,TITLE,TEXT
        };
        Role role=OTHER;
        std::vector<Bytes> title,body;
        Bytes word;
        std::string tag;
        bool in_tag=false,tag_over=false,word_over=false,link=false;
        Byte quote=0,previous=0;
        static void add(std::vector<Bytes>& v,const Bytes& w) {
            if(w.size()<3||w.size()>64)return;
            auto i=std::find(v.begin(),v.end(),w);
            if(i!=v.end())v.erase(i);
            if(v.size()==32)v.erase(v.begin());
            v.push_back(w);
        }
        void commit() {
            if(!word_over) {
                if(role==TITLE)add(title,word);
                else if(role==TEXT)add(body,word);
            }
            word.clear();
            word_over=false;
        }
        void end_tag() {
            std::string s=tag;
            size_t p=0;
            while(p<s.size()&&(s[p]==' '||s[p]=='\t'))++p;
            bool close=p<s.size()&&s[p]=='/';
            if(close)++p;
            size_t q=p;
            while(q<s.size()&&((s[q]>='a'&&s[q]<='z')||(s[q]>='A'&&s[q]<='Z')))++q;
            std::string name=s.substr(p,q-p);
            if(name=="page") {
                title.clear();
                body.clear();
                role=OTHER;
                link=false;
            }
            else if(name=="title")role=close?OTHER:TITLE;
            else if(name=="text"||name=="body_text") {
                role=close?OTHER:TEXT;
                if(close)link=false;
            }
        }
        void observe(Byte c) {
            if(in_tag) {
                if(quote) {
                    if(c==quote)quote=0;
                }
                else if(c=='\''||c=='"')quote=c;
                else if(c=='>') {
                    if(!tag_over)end_tag();
                    in_tag=false;
                    tag.clear();
                    tag_over=false;
                    previous=c;
                    return;
                }
                if(tag.size()<512)tag.push_back(char(c));
                else tag_over=true;
                previous=c;
                return;
            }
            if(c=='<') {
                commit();
                in_tag=true;
                tag.clear();
                tag_over=false;
                quote=0;
            }
            else {
                if(letter(c)) {
                    if(word.size()<64)word.push_back(c);
                    else word_over=true;
                }
                else commit();
                if(role==TEXT&&previous=='['&&c=='[')link=true;
                if(c=='|'||c==']'||role!=TEXT)link=false;
            }
            previous=c;
        }
        // Build a byte distribution solely from completed history plus decoded prefix.
        bool distribution(std::array<uint32_t,256>& f)const {
            f.fill(1);
            if(in_tag||role!=TEXT||word_over)return false;
            const auto& donors=link?body:title;
            unsigned found=0;
            for(const auto& w:donors) {
                if(w.size()>word.size()&&std::equal(word.begin(),word.end(),w.begin())) {
                    f[w[word.size()]]+=128;
                    ++found;
                }
            }
            return found>0;
        }
    };
    struct Model {
        ContextModel base;
        History history;
        std::array<uint32_t,256> donor {
        };
        bool use_history,available=false;
        uint64_t w=uint64_t(1)<<47;
        static constexpr uint64_t W=uint64_t(1)<<48;
        unsigned prefix=1,bitpos=0;
        uint32_t p=32768,q=32768;
        bool pending=false;
        uint64_t changed=0,active=0;
        explicit Model(bool h):use_history(h) {
        }
        uint32_t predict() {
            need(!pending,"predict called twice");
            pending=true;
            if(bitpos==0) {
                base.begin();
                available=use_history&&history.distribution(donor);
            }
            p=base.predict();
            q=p;
            if(available) {
                unsigned len=8-bitpos;
                unsigned lo=(prefix-(1u<<bitpos))<<len,mid=lo+(1u<<(len-1)),hi=lo+(1u<<len);
                uint64_t n=0,d=0;
                for(unsigned i=lo;i<hi;i++) {
                    d+=donor[i];
                    if(i>=mid)n+=donor[i];
                }
                q=uint32_t(std::max<uint64_t>(1,std::min<uint64_t>(Q-1,(n*Q+d/2)/d)));
                ++active;
            }
            uint32_t result=p;
            if(use_history) {
                result=uint32_t((__uint128_t(w)*p+__uint128_t(W-w)*q+W/2)/W);
                result=std::max(1u,std::min(65535u,result));
            }
            if(result!=p)++changed;
            return result;
        }
        void observe(unsigned b) {
            need(pending&&b<2,"observe without prediction");
            pending=false;
            if(use_history&&p!=q) {
                __uint128_t a=__uint128_t(w)*(b?p:Q-p),c=__uint128_t(W-w)*(b?q:Q-q);
                uint64_t nw=uint64_t((a*W+(a+c)/2)/(a+c));
                w=std::max<uint64_t>(1,std::min<uint64_t>(W-1,nw));
            }
            base.observe(b);
            prefix=prefix*2+b;
            if(++bitpos==8) {
                history.observe(Byte(prefix-256));
                prefix=1;
                bitpos=0;
            }
        }
    };
    struct Encoded {
        Bytes data;
        uint64_t changed=0,active=0;
    };
    Encoded encode(const Bytes& raw,bool history) {
        need(raw.size()<=MAX_BLOCK,"input block exceeds 1 MiB");
        Model m(history);
        Encoder c;
        for(Byte b:raw)for(int k=7;k>=0;k--) {
            auto p=m.predict();
            unsigned y=(b>>k)&1;
            c.bit(y,p);
            m.observe(y);
        }
        auto body=c.finish();
        Bytes out {
            'C','G','R','1',Byte(history?1:0),0,0,0
        };
        put32(out,uint32_t(raw.size()));
        put32(out,uint32_t(body.size()));
        put32(out,crc32(raw));
        put32(out,crc32(body));
        out.insert(out.end(),body.begin(),body.end());
        return {
            out,m.changed,m.active
        };
    }
    Bytes decode(const Bytes& arc) {
        need(arc.size()>=29,"archive too short");
        need(std::equal(arc.begin(),arc.begin()+4,Bytes {
            'C','G','R','1'
        }
        .begin()),"bad magic");
        need(arc[4]<=1&&arc[5]==0&&arc[6]==0&&arc[7]==0,"unsupported header");
        size_t pos=8;
        uint32_t n=get32(arc,pos),length=get32(arc,pos),sum=get32(arc,pos),packed=get32(arc,pos);
        need(n<=MAX_BLOCK,"declared raw size exceeds limit");
        need(length<=MAX_BLOCK*32+65536&&arc.size()-pos==length,"invalid payload size");
        Bytes payload(arc.begin()+pos,arc.end());
        need(crc32(payload)==packed,"compressed checksum mismatch");
        Model m(arc[4]!=0);
        Decoder c(payload);
        Bytes raw;
        raw.reserve(n);
        for(uint32_t i=0;i<n;i++) {
            unsigned b=0;
            for(int k=0;k<8;k++) {
                auto p=m.predict();
                unsigned y=c.bit(p);
                m.observe(y);
                b=b*2+y;
            }
            raw.push_back(Byte(b));
        }
        need(crc32(raw)==sum,"decoded checksum mismatch");
        return raw;
    }
    Bytes read(const std::string& name,size_t cap) {
        std::ifstream f(name,std::ios::binary);
        need(bool(f),"cannot open input");
        f.seekg(0,std::ios::end);
        auto n=f.tellg();
        need(n>=0&&uint64_t(n)<=cap,"input exceeds bound");
        f.seekg(0);
        Bytes b {
            std::vector<Byte>(size_t(n))
        };
        if(n)f.read(reinterpret_cast<char*>(b.data()),n);
        need(bool(f),"input read failed");
        return b;
    }
    void write(const std::string& name,const Bytes& b) {
        std::FILE* f=std::fopen(name.c_str(),"wbx");
        need(f,"output exists or cannot be created");
        bool ok=std::fwrite(b.data(),1,b.size(),f)==b.size();
        ok=std::fclose(f)==0&&ok;
        need(ok,"output write failed");
    }
}
int main(int argc,char** argv) {
    try {
        if(argc==2&&std::string(argv[1])=="--version") {
            std::cout<<"crg-safe 1.0 research; no Hutter qualification\n";
            return 0;
        }
        crg::need(argc==4||argc==5,"usage: crg c INPUT OUTPUT [base|history] | crg d INPUT OUTPUT");
        std::string op=argv[1];
        crg::need(std::string(argv[2])!=argv[3],"input equals output");
        if(op=="c") {
            bool h=false;
            if(argc==5) {
                crg::need(std::string(argv[4])=="base"||std::string(argv[4])=="history","bad mode");
                h=std::string(argv[4])=="history";
            }
            auto in=crg::read(argv[2],crg::MAX_BLOCK);
            auto r=crg::encode(in,h);
            crg::write(argv[3],r.data);
            std::cerr<<"{\"raw_bytes\":"<<in.size()<<",\"archive_bytes\":"<<r.data.size()<<",\"history\":"<<(h?"true":"false")<<",\"active_bits\":"<<r.active<<",\"changed_bits\":"<<r.changed<<"}\n";
        }
        else if(op=="d") {
            crg::need(argc==4,"decode takes no model option");
            auto in=crg::read(argv[2],crg::MAX_BLOCK*32+65536);
            auto raw=crg::decode(in);
            crg::write(argv[3],raw);
        }
        else {
            throw std::runtime_error("unknown command");
        }
        return 0;
    }
    catch(const std::exception& e) {
        std::cerr<<"crg: "<<e.what()<<"\n";
        return 1;
    }
}
