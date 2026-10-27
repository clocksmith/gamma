/**
 * 3914. Minimum Operations to Make Array Non Decreasing
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-operations-to-make-array-non-decreasing/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3914.Minimum%20Operations%20to%20Make%20Array%20Non%20Decreasing/README_EN.md
 * Complexity: O(n) time, O(1) auxiliary space.
 * Operation increments an entire subarray by x, cost x. Sum of original descents; no actual mutation. Result <=1e14.
 */

function solve(nums) {
  let answer = 0;
  for (let index = 1; index < nums.length; index += 1) answer += Math.max(0, nums[index - 1] - nums[index]);
  return answer;
}

function minOperations(nums) {
  return solve(nums);
}

class Solution {
  minOperations(nums) {
    return solve(nums);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minOperations, Solution };
}
