/**
 * 3993. Maximum Value of an Alternating Sequence
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-value-of-an-alternating-sequence/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3993.Maximum%20Value%20of%20an%20Alternating%20Sequence/README_EN.md
 * Complexity: O(1) time and space.
 * Use rises of m and falls of 1, with the maximum at the last possible peak. Answer is below 2^53.
 */

function solve(n, s, m) {
  return n === 1 ? s : s + Math.floor(n / 2) * (m - 1) + 1;
}

function maximumValue(n, s, m) {
  return solve(n, s, m);
}

class Solution {
  maximumValue(n, s, m) {
    return solve(n, s, m);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maximumValue, Solution };
}
