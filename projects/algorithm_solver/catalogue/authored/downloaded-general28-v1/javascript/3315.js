'use strict';

// 3315. Construct the Minimum Bitwise Array II (Medium).
// Specification: https://leetcode.com/problems/construct-the-minimum-bitwise-array-ii/description/
function solve(nums) {
  return nums.map((num) => {
    if (num === 2) return -1;
    const low = (num + 1) & (-(num + 1));
    return num - low / 2;
  });
}
const minBitwiseArray = solve;
class Solution { minBitwiseArray(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minBitwiseArray };
