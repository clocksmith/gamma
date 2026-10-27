/**
 * 3909. Compare Sums of Bitonic Parts
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/compare-sums-of-bitonic-parts/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3909.Compare%20Sums%20of%20Bitonic%20Parts/README_EN.md
 * Complexity: O(n) time, O(1) auxiliary space.
 * Single-peak bitonic input; common peak cancels in comparison. Sums <=1e14; no mutation.
 */

function solve(nums) {
  let peak = 0;
  while (peak + 1 < nums.length && nums[peak] < nums[peak + 1]) peak += 1;
  let left = 0;
  let right = 0;
  for (let index = 0; index < peak; index += 1) left += nums[index];
  for (let index = peak + 1; index < nums.length; index += 1) right += nums[index];
  return left === right ? -1 : left > right ? 0 : 1;
}

function compareBitonicSums(nums) {
  return solve(nums);
}

class Solution {
  compareBitonicSums(nums) {
    return solve(nums);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, compareBitonicSums, Solution };
}
