/**
 * 3979. Maximum Valid Pair Sum
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-valid-pair-sum/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3979.Maximum%20Valid%20Pair%20Sum/README_EN.md
 * Complexity: O(n) time, O(1) space.
 * Index gap at least k; a valid pair is guaranteed by 1 <= k < n. Inputs preserved.
 */

function solve(nums, k) {
  let bestLeft = nums[0];
  let answer = nums[0] + nums[k];
  for (let right = k; right < nums.length; right++) {
    bestLeft = Math.max(bestLeft, nums[right - k]);
    answer = Math.max(answer, bestLeft + nums[right]);
  }
  return answer;
}

function maxValidPairSum(nums, k) {
  return solve(nums, k);
}

class Solution {
  maxValidPairSum(nums, k) {
    return solve(nums, k);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maxValidPairSum, Solution };
}
