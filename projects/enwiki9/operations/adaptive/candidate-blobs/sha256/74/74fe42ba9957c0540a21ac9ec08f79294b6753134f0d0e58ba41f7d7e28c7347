#define COVERAGE_NO_MAIN
#include "../src/gamma_enwiki9/adapters/fx2_donor_coverage_v1.cpp"

int main(){
  using namespace coverage;
  std::vector<Record> pool;
  for(unsigned c='a';c<='j';++c)pool.push_back({Bytes(3,c),Bytes(3,c),c});
  check(paired(pool)==std::vector<size_t>({9,7,5,3,1}));
  View v;v.role=0;v.eligible=true;v.raw={'b'};v.stored={'b'};
  Search work;auto p=predict(32768,v,0,0,pool,work);
  check(p.extra_cap&&p.extra_pool&&!p.extra_pair&&p.found[0].empty()&&p.found[1]==std::vector<size_t>({1}));
  check(p.remaining_min==16&&p.remaining_max==16&&p.q[0]==32768&&p.q[1]==16385);
  // Opposite future truths receive exactly the same prospective prediction.
  Costs one,zero;one.add(32768,p,1);zero.add(32768,p,0);
  check(one.expert[1]>one.parent&&zero.expert[1]<zero.parent);
  check(one.parent-one.expert[1]<=one.parent&&zero.parent-zero.expert[1]<=zero.parent);
  v.raw={'a'};v.stored={'a'};p=predict(1,v,0,0,pool,work);
  check(!p.extra_cap&&p.extra_pair&&p.extra_pool&&p.q[2]>0&&p.q[2]<65536);
  // The raw spelling matches, but a different WRT spelling is unusable here.
  v.raw={'b'};v.stored={128};p=predict(65535,v,0,0,pool,work);
  check(!p.extra_pool&&p.q[2]==65535&&work.coordinate_rejections>0);
  // Already decoded bits can also exclude a candidate before the next bit.
  v.stored={'b'};p=predict(32768,v,1,1,pool,work);check(!p.extra_pool);
  v.raw={'b','b','b'};v.stored={128};p=predict(32768,v,0,0,pool,work);check(!p.extra_pool);
  // Whole-word inverse emission: no raw prefix exists before its final token.
  gamma_xml_field::Observer inverse({"bbb"},3);Bytes raw;
  check(inverse.observe(7,raw)&&raw.empty());check(inverse.observe(128,raw)&&raw==Bytes({'b','b','b'}));check(inverse.finish());
  // Literal emissions expose a prefix with genuinely undecoded spelling.
  gamma_xml_field::Observer literal({},3);
  check(literal.observe(7,raw)&&raw.empty());check(literal.observe('b',raw)&&raw==Bytes({'b'}));
  check(literal.observe('b',raw)&&literal.observe('b',raw)&&literal.finish());
  // Same pool and prefix give identical predictions, independent of call history.
  v.raw={'b'};v.stored={'b'};auto a=predict(65000,v,0,0,pool,work);auto b=predict(65000,v,0,0,pool,work);
  check(a.q==b.q&&a.found==b.found);
}
