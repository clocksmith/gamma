/**
 * 3950. Exactly One Consecutive Set Bits Pair
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/exactly-one-consecutive-set-bits-pair/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3950.Exactly%20One%20Consecutive%20Set%20Bits%20Pair/README_EN.md
 * Complexity: O(1) word operations, O(1) space.
 * n <= 100000, so signed 32-bit bitwise operations are exact. Overlapping adjacent pairs are counted.
 */

function solve(n) {
  const pairs = n & (n >>> 1);
  return pairs !== 0 && (pairs & (pairs - 1)) === 0;
}

function consecutiveSetBits(n) {
  return solve(n);
}

class Solution {
  consecutiveSetBits(n) {
    return solve(n);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, consecutiveSetBits, Solution };
}
