"""3647. Maximum Weight in Two Bags.

Specification: https://leetcode.com/problems/maximum-weight-in-two-bags/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n * w1 * ceil(w2 / wordBits)) bit-operation time, O(w1 * w2) bits; descending first capacity prevents item reuse.
Inputs are not modified.
"""

def solve(weights, w1, w2):
    # For each exact first-bag weight, bits enumerate exact second-bag weights.
    reachable = [0] * (w1 + 1)
    reachable[0] = 1
    mask = (1 << (w2 + 1)) - 1
    for weight in weights:
        for first in range(w1, -1, -1):
            previous = reachable[first]
            reachable[first] |= (previous << weight) & mask
            if first >= weight:
                reachable[first] |= reachable[first - weight]
    answer = 0
    for first, bits in enumerate(reachable):
        if bits:
            answer = max(answer, first + bits.bit_length() - 1)
    return answer


class Solution:
    def maxWeight(self, weights, w1, w2):
        return solve(weights, w1, w2)
