'use strict';

// 2917. Find the K-or of an Array (Easy).
// Specification: https://leetcode.com/problems/find-the-k-or-of-an-array/description/
// O(31*n) time, O(1) space. Values are in [0, 2^31), so no sign bit is used.
function solve(nums, k) {
  let result = 0;
  for (let bit = 0; bit < 31; bit++) {
    const mask = 2 ** bit;
    let count = 0;
    for (const value of nums) {
      if ((value & mask) !== 0) count++;
    }
    if (count >= k) result += mask;
  }
  return result;
}

const findKOr = solve;
class Solution {
  findKOr(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findKOr };
