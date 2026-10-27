/**
 * 3974. Maximum Total Sum of K Selected Elements
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-total-sum-of-k-selected-elements/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3974.Maximum%20Total%20Sum%20of%20K%20Selected%20Elements/README_EN.md
 * Complexity: O(n log n) time, O(n) space.
 * All values are positive. Choose k largest and match descending values to descending effective multipliers. Answer <= 1e15 is exactly representable; inputs preserved.
 */

function solve(nums, k, mul) {
  const ordered = nums.slice().sort((a, b) => b - a);
  let answer = 0;
  for (let index = 0; index < k; index++) answer += ordered[index] * Math.max(1, mul - index);
  return answer;
}

function maxSum(nums, k, mul) {
  return solve(nums, k, mul);
}

class Solution {
  maxSum(nums, k, mul) {
    return solve(nums, k, mul);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maxSum, Solution };
}
