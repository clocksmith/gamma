/**
 * 3987. Minimum Total Cost to Process All Elements
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-total-cost-to-process-all-elements/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3987.Minimum%20Total%20Cost%20to%20Process%20All%20Elements/README_EN.md
 * Complexity: O(n) time, O(1) auxiliary integers.
 * Positive demands permit just-in-time replenishment; total required top-ups determine the triangular cost. BigInt prevents overflow before modulo. Inputs preserved.
 */

function solve(nums, k) {
  let total = 0n;
  for (const value of nums) total += BigInt(value);
  const step = BigInt(k);
  let operations = (total + step - 1n) / step - 1n;
  if (operations < 0n) operations = 0n;
  return Number(operations * (operations + 1n) / 2n % 1000000007n);
}

function minimumCost(nums, k) {
  return solve(nums, k);
}

class Solution {
  minimumCost(nums, k) {
    return solve(nums, k);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minimumCost, Solution };
}
