'use strict';

// 3301. Maximize the Total Height of Unique Towers (Medium).
// Specification: https://leetcode.com/problems/maximize-the-total-height-of-unique-towers/description/
function solve(maximumHeight) {
  const sorted = maximumHeight.slice().sort((a, b) => b - a);
  let prev = Infinity; let ans = 0;
  for (const h of sorted) {
    const cur = Math.min(h, prev - 1);
    if (cur <= 0) return -1;
    ans += cur; prev = cur;
  }
  return ans;
}
const maximumTotalSum = solve;
class Solution { maximumTotalSum(maximumHeight) { return solve(maximumHeight); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumTotalSum };
