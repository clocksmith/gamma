/**
 * 3904. Smallest Stable Index II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/smallest-stable-index-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3904.Smallest%20Stable%20Index%20II/README_EN.md
 * Complexity: O(n) time and space.
 * nums and k nonnegative <=1e9; inputs preserved.
 */

function solve(nums, k) {
  const suffix = nums.slice();
  for (let index = nums.length - 2; index >= 0; index -= 1) suffix[index] = Math.min(suffix[index], suffix[index + 1]);
  let largest = nums[0];
  for (let index = 0; index < nums.length; index += 1) {
    largest = Math.max(largest, nums[index]);
    if (largest - suffix[index] <= k) return index;
  }
  return -1;
}

function firstStableIndex(nums, k) {
  return solve(nums, k);
}

class Solution {
  firstStableIndex(nums, k) {
    return solve(nums, k);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, firstStableIndex, Solution };
}
