// Gamma FX2 core delivery envelope. MIT license; native codec licenses separate.
// No numerical changes: run the embedded codec with explicit dictionary/model.
#include <array>
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <vector>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>
namespace fs = std::filesystem;
static constexpr char magic[8]={'G','F','X','2','P','K','0','1'};
static void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
struct File { FILE* f; File(const fs::path& p,const char* m):f(fopen(p.c_str(),m)){need(f,"file open failed");} ~File(){fclose(f);} };
static void copy(FILE* in,FILE* out,uint64_t n){
  std::array<unsigned char,65536> b{};
  while(n){size_t k=n<b.size()?size_t(n):b.size();need(fread(b.data(),1,k,in)==k,"truncated member");need(fwrite(b.data(),1,k,out)==k,"write failed");n-=k;}
}
static uint64_t checksum(const fs::path& p){
  File in(p,"rb");std::array<unsigned char,65536>b{};uint64_t h=14695981039346656037ULL;size_t n;
  while((n=fread(b.data(),1,b.size(),in.f)))for(size_t i=0;i<n;i++)h=(h^b[i])*1099511628211ULL;
  need(!ferror(in.f),"checksum read failed");return h;
}
static uint64_t get64(FILE* f){uint64_t v=0;for(int i=0;i<8;i++){int c=fgetc(f);need(c!=EOF,"short footer");v|=uint64_t(c)<<(8*i);}return v;}
static void put64(FILE* f,uint64_t v){for(int i=0;i<8;i++)need(fputc((v>>(8*i))&255,f)!=EOF,"footer write failed");}
struct Workspace { fs::path p; Workspace(){char b[]=".gamma-fx2-XXXXXX";char* s=mkdtemp(b);need(s,"workspace creation failed");p=fs::absolute(s);} ~Workspace(){std::error_code e;fs::remove_all(p,e);} };
static void run(const fs::path& work,bool encode,const fs::path& input){
  std::string src=input.string();pid_t pid=fork();need(pid>=0,"fork failed");
  if(!pid){if(chdir(work.c_str()))_exit(125);execl("./codec","codec",encode?"-c":"-d","dictionary",src.c_str(),"output","--transformer","weights",(char*)nullptr);_exit(126);}
  int status=0;while(waitpid(pid,&status,0)<0)need(errno==EINTR,"wait failed");
  need(WIFEXITED(status)&&WEXITSTATUS(status)==0,"embedded codec failed");
}
int main(int argc,char**argv){try{
  std::array<char,4096> self{};ssize_t n=readlink("/proc/self/exe",self.data(),self.size()-1);need(n>0&&size_t(n)<self.size()-1,"cannot resolve executable");self[n]=0;
  File in(self.data(),"rb");need(!fseeko(in.f,0,SEEK_END),"self seek failed");off_t end=ftello(in.f);need(end>=72,"missing footer");need(!fseeko(in.f,end-72,SEEK_SET),"footer seek failed");
  char mark[8];need(fread(mark,1,8,in.f)==8&&!memcmp(mark,magic,8),"invalid footer identity");
  std::array<uint64_t,8> h{};for(auto&v:h)v=get64(in.f);
  // mode, wrapper, codec, dictionary, weights, payload, raw length, FNV-1a.
  need(h[0]<=1&&h[1]>0&&h[2]>0&&h[3]>0&&h[4]>0,"invalid member geometry");uint64_t total=72;
  for(int i=1;i<=5;i++){need(h[i]<=2000000000ULL,"member exceeds profile");total+=h[i];}
  need(total==uint64_t(end)&&h[6]<=1000000000ULL,"footer size mismatch");
  bool encode=h[0]==0;need(encode?argc==2:argc==1,"usage: comp9 INPUT; archive9 takes no arguments");
  need(!encode||(h[5]==0&&h[6]==0&&h[7]==0),"compressor has payload fields");
  fs::path output=fs::absolute(encode?"archive9":"enwik9");need(!fs::exists(output),"output already exists");
  fs::path input;if(encode){input=fs::canonical(argv[1]);need(fs::is_regular_file(input)&&fs::file_size(input)<=1000000000ULL,"input outside profile");}
  Workspace work;need(!fseeko(in.f,h[1],SEEK_SET),"member seek failed");
  for(auto pair:std::vector<std::pair<const char*,int>>{{"codec",2},{"dictionary",3},{"weights",4},{"payload",5}}){File out(work.p/pair.first,"wb");copy(in.f,out.f,h[pair.second]);}
  need(!chmod((work.p/"codec").c_str(),0700),"codec chmod failed");
  uint64_t rawlen=encode?fs::file_size(input):h[6], rawhash=encode?checksum(input):h[7];
  run(work.p,encode,encode?input:work.p/"payload");
  fs::path product=work.p/"output";
  if(encode){
    // Refuse input mutation while the codec ran.
    need(fs::file_size(input)==rawlen&&checksum(input)==rawhash,"input changed during encoding");
    fs::path assembled=work.p/"assembled";File out(assembled,"wb");need(!fseeko(in.f,0,SEEK_SET),"prefix seek failed");
    copy(in.f,out.f,h[1]+h[2]+h[3]+h[4]);File payload(product,"rb");uint64_t bytes=fs::file_size(product);copy(payload.f,out.f,bytes);
    need(fwrite(magic,1,8,out.f)==8,"footer write failed");h[0]=1;h[5]=bytes;h[6]=rawlen;h[7]=rawhash;for(auto v:h)put64(out.f,v);
    need(!fflush(out.f)&&!fsync(fileno(out.f)),"archive sync failed");need(!chmod(assembled.c_str(),0755),"archive chmod failed");product=assembled;
  }else need(fs::file_size(product)==rawlen&&checksum(product)==rawhash,"decoded content check failed");
  // Atomic no-replacement publication on this workspace's filesystem.
  need(!link(product.c_str(),output.c_str()),"cannot publish output without replacement");
  return 0;
}catch(const std::exception&e){fprintf(stderr,"gamma-fx2: %s\n",e.what());return 1;}}
