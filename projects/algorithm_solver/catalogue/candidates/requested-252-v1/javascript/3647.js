'use strict';

// 3647. Maximum Weight in Two Bags.
// Specification: https://leetcode.com/problems/maximum-weight-in-two-bags/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n * w1 * ceil(w2 / wordBits)) bit-operation time, O(w1 * w2) bits; descending first capacity prevents item reuse.
// Inputs are not modified.

function solve(weights, w1, w2) {
  const reachable = new Array(w1 + 1).fill(0n), mask = (1n << BigInt(w2 + 1)) - 1n;
  reachable[0] = 1n;
  for (const weight of weights) {
    for (let first = w1; first >= 0; first--) {
      const previous = reachable[first];
      reachable[first] |= (previous << BigInt(weight)) & mask;
      if (first >= weight) reachable[first] |= reachable[first - weight];
    }
  }
  let answer = 0;
  for (let first = 0; first <= w1; first++) if (reachable[first] !== 0n) answer = Math.max(answer, first + reachable[first].toString(2).length - 1);
  return answer;
}

const maxWeight = solve;
class Solution {
  maxWeight(weights, w1, w2) { return solve(weights, w1, w2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxWeight };
