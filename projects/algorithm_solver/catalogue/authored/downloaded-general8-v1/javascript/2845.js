'use strict';

// 2845. Count of Interesting Subarrays (Medium).
// Specification: https://leetcode.com/problems/count-of-interesting-subarrays/description/
function solve(nums, modulo, k) {
  const cnt = new Map([[0, 1]]);
  let s = 0; let ans = 0;
  for (const x of nums) {
    if (x % modulo === k) s += 1;
    const sm = ((s % modulo) + modulo) % modulo;
    const target = ((sm - k) % modulo + modulo) % modulo;
    ans += cnt.get(target) || 0;
    cnt.set(sm, (cnt.get(sm) || 0) + 1);
  }
  return ans;
}
const countInterestingSubarrays = solve;
class Solution {
  countInterestingSubarrays(...args) { return solve(...args); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countInterestingSubarrays };
