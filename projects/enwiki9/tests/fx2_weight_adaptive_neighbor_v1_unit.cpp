#include <functional>
#include "../lib/fx2_weight_adaptive_neighbor_v1.hpp"
#include <iostream>
using namespace fx2_weight_adaptive_neighbor_v1;
void reject(const std::function<void()>& action) {
  bool failed = false;
  try { action(); } catch (const std::runtime_error&) { failed = true; }
  require(failed, "malformed archive accepted");
}
int main() {
  try {
    size_t cases = 0, boundaries = 0;
    // Repeated symbols cross the rescale threshold in A and D.
    for (const Bytes& values : {Bytes{}, Bytes{0,14,3,2}, Bytes(70000, 7)}) {
      for (uint32_t width : {1u, 3u, 64u}) {
        const auto p = pack(values, width, 'P');
        require_identical(p, fx2_weight_neighbor_v1::pack(values, width, 'P'), "parent drift");
        require_identical(p, pack(values, width, 'K'), "bookkeeping drift");
        for (char arm : {'A','D'}) {
          // Replay encoder states directly, including every histogram entry;
          // no final-only or archive-size proxy for state synchronization.
          State expected;
          const auto encoded = pack(values, width, arm,
            [&](size_t k, size_t c, const State& state) {
              require(state.rows == expected.rows && state.totals == expected.totals, "encoder state differs");
              if (k < values.size()) expected.observe(c, values[k]);
            });
          expected = State{};
          const auto decoded = unpack(encoded,
            [&](size_t k, size_t c, const State& state) {
              require(state.rows == expected.rows && state.totals == expected.totals, "decoder state differs");
              if (k < values.size()) {
                require(c == context(values, k, width, arm), "decoder context differs");
                expected.observe(c, values[k]);
              }
              ++boundaries;
            });
          require_identical(decoded.values, values, "inverse differs");
          require(decoded.width == width && decoded.arm == arm, "header identity differs");
          require_identical(pack(values, width, arm), encoded, "repeat differs");
          auto bad = encoded; bad.pop_back(); reject([&]{unpack(bad);});
          bad = encoded; bad.push_back(0); reject([&]{unpack(bad);});
          bad = encoded; bad[8] = 2; reject([&]{unpack(bad);});
          bad = encoded; for (size_t i=13;i<17;++i) bad[i]=0; reject([&]{unpack(bad);});
          ++cases;
        }
      }
    }
    Bytes dependent, random;
    uint32_t rng = 1;
    for (size_t k=0;k<30000;++k) {
      dependent.push_back(k % 15);
      rng = 1664525u*rng+1013904223u;
      random.push_back((rng>>16)%15);
    }
    for (const auto* input : {&dependent,&random})
      for (char arm : {'P','K','A','D'})
        require_identical(unpack(pack(*input,150,arm)).values,*input,"stress inverse differs");
    require(pack(dependent,150,'D').size() < pack(dependent,150,'A').size(),"neighbor opportunity not exercised");
    reject([&]{pack(Bytes{15},1,'D');});
    reject([&]{pack(Bytes{},0,'D');});
    reject([&]{pack(Bytes{},1,'X');});
    reject([&]{pack(Bytes(kSymbols+1),1,'D');});
    std::cout << "{\"cases\":" << cases << ",\"state_boundaries\":" << boundaries;
    for (char arm : {'P','A','D'})
      std::cout << ",\"dependent_"<<arm<<"\":"<<pack(dependent,150,arm).size()
                << ",\"random_"<<arm<<"\":"<<pack(random,150,arm).size();
    std::cout << ",\"exact_inverse\":true,\"repeat\":true,\"objective_credit_bytes\":0}\n";
  } catch (const std::exception& error) { std::cerr<<error.what()<<'\n'; return 1; }
}
