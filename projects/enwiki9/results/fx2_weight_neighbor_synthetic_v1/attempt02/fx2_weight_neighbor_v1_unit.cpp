// Bounded synthetic tests; no model/corpus reading or inference.
#include "../lib/fx2_weight_neighbor_v1.hpp"
#include <iostream>
#include <functional>
using namespace fx2_weight_neighbor_v1;
void reject(const std::function<void()>& fn) {
  bool rejected = false;
  try { fn(); } catch (const std::runtime_error&) { rejected = true; }
  require(rejected, "malformed input was accepted");
}
int main() {
  try {
    uint32_t cases = 0;
    for (const Bytes& values : {Bytes{}, Bytes{0}, Bytes{14}, Bytes{0,14,3,3,1}, Bytes(4096, 7)}) {
      for (uint32_t width : {1u, 3u, 64u}) {
        const auto p = pack(values, width, 'P');
        require_identical(p, pack(values, width, 'K'), "bookkeeping changes parent");
        for (char arm : {'P', 'D'}) {
          const auto encoded = pack(values, width, arm);
          const auto decoded = unpack(encoded);
          require_identical(decoded.values, values, "synthetic inverse differs");
          require(decoded.width == width, "row width lost");
          require_identical(pack(values, width, arm), encoded, "repeat differs");
          auto trailing = encoded; trailing.push_back(0);
          reject([&] { unpack(trailing); });
          auto truncated = encoded; truncated.pop_back();
          reject([&] { unpack(truncated); });
        }
        ++cases;
      }
    }
    const Bytes rows{1,2,3,4,5,6};
    const auto c = counts(rows, 3, true);
    require(c[15][1] == 1 && c[15][4] == 1 && c[3][4] == 0 &&
                c[1][2] == 1 && c[4][5] == 1, "row boundary context differs");
    Bytes dependent, independent;
    uint32_t rng = 1;
    for (uint32_t k = 0; k < 30000; ++k) {
      dependent.push_back(uint8_t(k % 15));
      rng = 1664525u * rng + 1013904223u;
      independent.push_back(uint8_t((rng >> 16) % 15));
    }
    for (const auto* values : {&dependent, &independent})
      for (char arm : {'P', 'K', 'D'})
        require_identical(unpack(pack(*values, 150, arm)).values, *values, "stress inverse differs");
    const auto p = pack(dependent, 150, 'P'), d = pack(dependent, 150, 'D');
    require(d.size() < p.size(), "dependent synthetic population does not exercise a gain");
    reject([&] { pack(Bytes{15}, 1, 'D'); });
    reject([&] { pack(Bytes{}, 0, 'P'); });
    reject([&] { pack(Bytes{}, 1, 'X'); });
    reject([&] { pack(Bytes(kSymbols + 1, 0), 1, 'P'); });
    reject([&] { pack(Bytes{}, kSymbols + 1, 'D'); });
    auto bad = d; bad[8] = 2; reject([&] { unpack(bad); });
    bad = d; bad[9] ^= 1; reject([&] { unpack(bad); });
    bad = d; bad[17] ^= 1; reject([&] { unpack(bad); });
    bad = d; bad[13] = 0; bad[14] = 0; bad[15] = 0; bad[16] = 0;
    reject([&] { unpack(bad); });
    std::cout << "{\"synthetic_cases\":" << cases << ",\"dependent_parent_bytes\":" << p.size()
              << ",\"dependent_treatment_bytes\":" << d.size()
              << ",\"independent_parent_bytes\":" << pack(independent,150,'P').size()
              << ",\"independent_treatment_bytes\":" << pack(independent,150,'D').size()
              << ",\"exact_inverse\":true,\"repeat\":true,\"objective_credit_bytes\":0}\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
