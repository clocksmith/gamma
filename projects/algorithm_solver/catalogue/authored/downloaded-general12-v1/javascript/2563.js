'use strict';

// 2563. Count the Number of Fair Pairs (Medium).
// Specification: https://leetcode.com/problems/count-the-number-of-fair-pairs/description/
function solve(nums, lower, upper) {
  const a = nums.slice().sort((x, y) => x - y);
  function countLess(target) {
    let l = 0; let r = a.length - 1; let cnt = 0;
    while (l < r) {
      if (a[l] + a[r] < target) { cnt += r - l; l++; } else { r--; }
    }
    return cnt;
  }
  return countLess(upper + 1) - countLess(lower);
}
const countFairPairs = solve;
class Solution { countFairPairs(nums, lower, upper) { return solve(nums, lower, upper); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countFairPairs };
