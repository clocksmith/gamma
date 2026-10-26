'use strict';

// 1822. Sign of the Product of an Array (Easy).
// Specification: https://leetcode.com/problems/sign-of-the-product-of-an-array/description/
// O(n) time, O(1) space; do not form the potentially overflowing product; preserve nums.
function solve(nums) {
  let sign = 1;
  for (const value of nums) {
    if (value === 0) return 0;
    if (value < 0) sign = -sign;
  }
  return sign;
}

const arraySign = solve;
class Solution {
  arraySign(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, arraySign };
