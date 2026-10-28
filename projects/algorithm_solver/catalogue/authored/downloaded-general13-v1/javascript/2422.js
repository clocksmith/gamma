'use strict';

// 2422. Merge Operations to Turn Array Into a Palindrome (Medium).
// Specification: https://leetcode.com/problems/merge-operations-to-turn-array-into-a-palindrome/description/
function solve(nums) {
  let i = 0, j = nums.length - 1, left = nums[0], right = nums[nums.length - 1], ops = 0;
  while (i < j) {
    if (left === right) {
      i++; j--;
      if (i < j) { left = nums[i]; right = nums[j]; }
    } else if (left < right) {
      i++; left += nums[i]; ops++;
    } else {
      j--; right += nums[j]; ops++;
    }
  }
  return ops;
}
const minimumOperations = solve;
class Solution { minimumOperations(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumOperations };
