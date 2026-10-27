/**
 * 3891. Minimum Increase to Maximize Special Indices
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-increase-to-maximize-special-indices/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3891.Minimum%20Increase%20to%20Maximize%20Special%20Indices/README_EN.md
 * Complexity: O(n) time, O(1) auxiliary space.
 * Maximizes nonadjacent interior peak count before minimizing cost. Sum <= 1e14; input preserved.
 */

function solve(nums) {
  let skipCount = 0;
  let skipCost = 0;
  let takeCount = -1;
  let takeCost = 0;
  for (let index = 1; index + 1 < nums.length; index += 1) {
    const cost = Math.max(0, Math.max(nums[index - 1], nums[index + 1]) + 1 - nums[index]);
    const nextTakeCount = skipCount + 1;
    const nextTakeCost = skipCost + cost;
    if (takeCount > skipCount || (takeCount === skipCount && takeCost < skipCost)) {
      skipCount = takeCount;
      skipCost = takeCost;
    }
    takeCount = nextTakeCount;
    takeCost = nextTakeCost;
  }
  return takeCount > skipCount || (takeCount === skipCount && takeCost < skipCost) ? takeCost : skipCost;
}

function minIncrease(nums) {
  return solve(nums);
}

class Solution {
  minIncrease(nums) {
    return solve(nums);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minIncrease, Solution };
}
