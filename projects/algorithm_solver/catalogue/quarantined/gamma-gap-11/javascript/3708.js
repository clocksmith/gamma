'use strict';

// 3708. Longest Fibonacci Subarray.
// O(n) time and O(1) auxiliary space; inputs are preserved.
function solve(nums) {
  if (nums.length < 3) return nums.length;
  let answer = 2;
  let current = 2;
  for (let index = 2; index < nums.length; index += 1) {
    current = nums[index] === nums[index - 1] + nums[index - 2] ? current + 1 : 2;
    answer = Math.max(answer, current);
  }
  return answer;
}

const longestSubarray = solve;
class Solution {
  longestSubarray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSubarray };
