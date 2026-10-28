'use strict';

// 414. Third Maximum Number (Easy).
// Specification: https://leetcode.com/problems/third-maximum-number/description/
function solve(nums) {
  const distinct = [...new Set(nums)].sort((a, b) => b - a);
  return distinct.length >= 3 ? distinct[2] : distinct[0];
}

const thirdMax = solve;
class Solution {
  thirdMax(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, thirdMax };
