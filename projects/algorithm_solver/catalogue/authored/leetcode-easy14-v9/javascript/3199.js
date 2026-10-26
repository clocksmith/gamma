'use strict';

// 3199. Count Triplets with Even XOR Set Bits I (Easy).
// Specification: https://leetcode.com/problems/count-triplets-with-even-xor-set-bits-i/description/
// O(n + m + k) time, O(1) space for values in [0, 100]; combine popcount-parity counts.
function solve(a, b, c) {
  function parityCounts(values) {
    const counts = [0, 0];
    for (const value of values) {
      let remaining = value;
      let parity = 0;
      while (remaining > 0) {
        parity ^= remaining & 1;
        remaining >>>= 1;
      }
      counts[parity]++;
    }
    return counts;
  }
  const first = parityCounts(a);
  const second = parityCounts(b);
  const third = parityCounts(c);
  const evenPairs = first[0] * second[0] + first[1] * second[1];
  const oddPairs = first[0] * second[1] + first[1] * second[0];
  return evenPairs * third[0] + oddPairs * third[1];
}

const tripletCount = solve;
class Solution {
  tripletCount(a, b, c) { return solve(a, b, c); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, tripletCount };
