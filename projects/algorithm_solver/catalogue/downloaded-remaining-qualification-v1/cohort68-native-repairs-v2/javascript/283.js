'use strict';

// 283. Move Zeroes (Easy).
// Specification: https://leetcode.com/problems/move-zeroes/description/
function solve(nums) {
  const result = nums.filter((value) => value !== 0);
  while (result.length < nums.length) result.push(0);
  return result;
}
const moveZeroes = (nums) => new Solution().moveZeroes(nums);
class Solution { moveZeroes(nums) {
  let write = 0;
  for (const value of nums) if (value !== 0) { nums[write] = value; write++; }
  for (let index = write; index < nums.length; index++) nums[index] = 0;
} }
if (typeof module !== 'undefined') module.exports = { solve, Solution, moveZeroes };
