/**
 * 3992. Rearrange String to Avoid Character Pair
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/rearrange-string-to-avoid-character-pair/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3992.Rearrange%20String%20to%20Avoid%20Character%20Pair/README_EN.md
 * Complexity: O(n) time and output space.
 * All y precede all x. Any valid permutation is accepted; unrelated letters retain relative order.
 */

function solve(s, x, y) {
  let count = 0;
  const rest = [];
  for (const ch of s) { if (ch === y) count++; else rest.push(ch); }
  return y.repeat(count) + rest.join('');
}

function rearrangeString(s, x, y) {
  return solve(s, x, y);
}

class Solution {
  rearrangeString(s, x, y) {
    return solve(s, x, y);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, rearrangeString, Solution };
}
