#include "../lib/fx2_final_bit_head_v1.hpp"
#include <algorithm>
#include <iostream>
#include <memory>
using namespace gamma_final_bit_head;

int main() {
  uint64_t count_checks = 0;
  for (unsigned p = 1; p < Q; ++p) {
    require(corrected_count(p, 0) == p);
    unsigned previous = 0;
    for (double u : {-4., -1., -0.01, 0., 0.01, 1., 4.}) {
      const auto c = corrected_count(p, u);
      const long double e = std::exp((long double)u);
      const long double q = p * e / ((Q-p) + p*e);
      require(c >= previous && c > 0 && c < Q);
      require(std::fabs((long double)c/Q - q) <= 1.L/Q);
      previous = c; ++count_checks;
    }
  }
  auto k = std::make_unique<Model>('K');
  auto d = std::make_unique<Model>('D');
  auto decode = std::make_unique<Model>('D');
  auto p = std::make_unique<Model>('P');
  auto s = std::make_unique<Model>('S');
  std::array<float,D> h{};
  uint64_t changed = 0, wrong_label_differences = 0;
  // Features and parent counts use only the completed-byte coordinate.
  for (unsigned byte = 0; byte < 4096; ++byte) {
    if (byte % 1024 == 0) {
      for (auto m : {k.get(), d.get(), decode.get(), p.get(), s.get()}) m->reset_article();
    }
    for (unsigned i = 0; i < D; ++i) h[i] = float(int((byte+i)%11)-5) / 8;
    for (auto m : {k.get(), d.get(), decode.get(), p.get(), s.get()}) {
      if (byte % 31 == 0) m->invalidate_feature(); else m->capture(h.data());
    }
    const unsigned actual = (byte % 2 == 0 ? 0x55 : 0xaa);
    for (unsigned bit = 0; bit < 8; ++bit) {
      const unsigned parent = 20000 + (byte * 17 + bit * 53) % 20000;
      const unsigned ck = k->predict(parent), cd = d->predict(parent);
      const unsigned cr = decode->predict(parent), cp = p->predict(parent);
      const unsigned cs = s->predict(parent);
      require(ck == parent && cp == parent && cd == cr);
      if (byte % 31 == 0) require(cd == parent);
      changed += cd != parent; wrong_label_differences += cd != cs;
      const unsigned truth = (actual >> (7-bit)) & 1;
      for (auto m : {k.get(), d.get(), decode.get(), p.get(), s.get()}) m->observe(truth);
    }
    if (byte % 97 == 0 || byte == 4095) {
      require(k->state() == d->state() && decode->state() == d->state());
    }
  }
  require(changed > 0 && wrong_label_differences > 0 && p->updates == 0);
  require(k->updates == d->updates && d->updates == decode->updates);
  require(s->updates == d->updates);
  for (unsigned row = 0; row < ROWS; ++row) {
    double norm2 = 0;
    for (unsigned i = 0; i < D; ++i) norm2 += d->weights[row*D+i]*d->weights[row*D+i];
    require(norm2 <= 16.00000001);
  }
  d->reset_article();
  require(std::all_of(d->weights.begin(), d->weights.end(), [](double x){return x == 0;}));
  require(!d->feature_valid && !d->previous_valid);
  std::cout << "{\"status\":\"pass\",\"zero_identity_counts\":65535,"
            << "\"count_bound_checks\":" << count_checks
            << ",\"synthetic_bits\":32768,\"changed_counts\":" << changed
            << ",\"wrong_label_differences\":" << wrong_label_differences
            << ",\"introduced_state_bytes\":" << d->state().size() << "}\n";
}
