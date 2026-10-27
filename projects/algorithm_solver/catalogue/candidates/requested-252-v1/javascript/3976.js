/**
 * 3976. Maximum Subarray Sum After Multiplier
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-subarray-sum-after-multiplier/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3976.Maximum%20Subarray%20Sum%20After%20Multiplier/README_EN.md
 * Complexity: O(n) time, O(1) space.
 * Exact one nonempty operation, truncation toward zero. A nonworsening operation can always intersect an optimal sum segment for k >= 1. All sums within 1e15; inputs preserved.
 */

function solve(nums, k) {
  let before = -Infinity, multiplied = -Infinity, divided = -Infinity, after = -Infinity;
  let answer = -Infinity;
  for (const value of nums) {
    const quotient = Math.trunc(value / k);
    const newBefore = Math.max(0, before) + value;
    const newMultiplied = Math.max(0, before, multiplied) + value * k;
    const newDivided = Math.max(0, before, divided) + quotient;
    const newAfter = Math.max(multiplied, divided, after) + value;
    before = newBefore; multiplied = newMultiplied; divided = newDivided; after = newAfter;
    answer = Math.max(answer, multiplied, divided, after);
  }
  return answer === 0 ? 0 : answer;
}

function maxSubarraySum(nums, k) {
  return solve(nums, k);
}

class Solution {
  maxSubarraySum(nums, k) {
    return solve(nums, k);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maxSubarraySum, Solution };
}
