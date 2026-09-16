#include "fx2_attention_anchor_v2.h"
#include <algorithm>
#include <array>
#include <cassert>
#include <deque>
#include <iostream>
#include <set>

// An independent chronological queue is the specification; it does not use
// the native ring's modular arithmetic to derive retained input identities.
int main() {
    std::uint64_t steps = 0;
    for (int length : {0, 1, 4, 8, 1023, 1024, 1025, 2045, 8193, 131072}) {
        std::array<int, 1024> physical;
        physical.fill(-1);
        std::deque<int> recent;
        std::set<int> pinned;
        for (int t = 0; t < length; ++t) {
            const int slot = gamma_attention_slot(t);
            assert(slot >= 0 && slot < 1024);
            if (t < 1024) assert(slot == t);
            physical[slot] = t;
            const bool pin = (GAMMA_ANCHOR_MODE == 1 && t < 4) ||
                             (GAMMA_ANCHOR_MODE == 2 && t >= 4 && t < 8);
            if (pin) pinned.insert(t); else recent.push_back(t);
            while (recent.size() + pinned.size() > 1024) recent.pop_front();
            std::set<int> expected(pinned);
            expected.insert(recent.begin(), recent.end());
            std::set<int> actual;
            for (int x : physical) if (x >= 0) { assert(x <= t); actual.insert(x); }
            assert(actual == expected);
            assert(actual.size() == static_cast<unsigned>(std::min(t + 1, 1024)));
            ++steps;
        }
    }
    std::cout << "mode=" << GAMMA_ANCHOR_MODE << " checked_steps=" << steps << '\n';
}
