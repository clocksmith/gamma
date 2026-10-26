'use strict';

// 2562. Find the Array Concatenation Value (Easy).
// Specification: https://leetcode.com/problems/find-the-array-concatenation-value/description/
// O(n log M) time, O(1) space; arithmetic concatenation preserves nums.
function solve(nums) {
  let left = 0;
  let right = nums.length - 1;
  let total = 0;
  while (left < right) {
    let place = 10;
    while (place <= nums[right]) place *= 10;
    total += nums[left] * place + nums[right];
    left++;
    right--;
  }
  if (left === right) total += nums[left];
  return total;
}

const findTheArrayConcVal = solve;
class Solution {
  findTheArrayConcVal(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findTheArrayConcVal };
