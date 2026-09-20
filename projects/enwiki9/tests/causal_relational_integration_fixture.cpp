#include "predictors/causal_relational_v2.hpp"
#include <cmath>
#include <iostream>
#include <string>

using namespace gamma_relational;

// Constructed inputs, uniform parent: this tests integration, not corpus value.
std::string fixture(bool content_to_link) {
  std::string text = content_to_link
      ? "<text xml:space=\"preserve\">alpha delta gamma theta "
      : "<title>alpha delta gamma theta</title>";
  // Give completed donors a declared epoch boundary before any tested mention.
  text.append(Epoch - 1 - text.size(), ' ');
  if (!content_to_link) text += "<text xml:space=\"preserve\">";
  for (unsigned mention = 0; mention < 180; ++mention)
    text += content_to_link ? "[[theta]] " : "theta ";
  text += "</text>";
  return text;
}

int main() {
  for (bool content_to_link : {false, true}) {
    const auto text = fixture(content_to_link);
    Bytes tape{7};
    for (unsigned char c : text) tape.push_back(gamma_xml_field::unswap(c));
    Model parent({}, text.size(), 'P'), bookkeeping({}, text.size(), 'K');
    Model shared({}, text.size(), 'S'), independent({}, text.size(), 'I');
    Model wrong({}, text.size(), 'W');
    std::array<Model*,5> models{&parent, &bookkeeping, &independent, &shared, &wrong};
    std::array<long double,5> costs{};
    std::array<std::string,5> restored{};
    for (uint8_t c : tape) {
      for (unsigned bit = 0; bit < 8; ++bit) {
        const unsigned truth = (c >> (7 - bit)) & 1;
        for (size_t arm = 0; arm < models.size(); ++arm) {
          auto& model = *models[arm];
          const auto p = model.predict(32768);
          if (arm < 2) require(p == 32768);
          costs[arm] -= std::log2((long double)(truth ? p : 65536 - p) / 65536);
          Bytes raw;
          require(model.observe(truth, raw));
          restored[arm].append(raw.begin(), raw.end());
        }
      }
      // Full introduced state, not just equal archive lengths or summaries.
      require(parent.state() == bookkeeping.state());
      require(parent.state() == shared.state());
      require(shared.state().size() < 24000);
    }
    for (size_t arm = 0; arm < models.size(); ++arm) {
      require(models[arm]->finish() && restored[arm] == text);
      require(models[arm]->active_bits > 0 && models[arm]->pairs > 0);
    }
    require(costs[3] + 1 < costs[0]);
    require(costs[3] + 1 < costs[2]);
    require(costs[3] + 1 < costs[4]);
    std::cout << (content_to_link ? "content-to-link" : "title-to-content");
    for (auto cost : costs) std::cout << ' ' << cost;
    std::cout << '\n';
  }
}
