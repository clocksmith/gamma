/**
 * 3978. Unique Middle Element
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/unique-middle-element/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3978.Unique%20Middle%20Element/README_EN.md
 * Complexity: O(n) time, O(1) space.
 * Middle position in the original odd-length array, not the sorted median. Input preserved.
 */

function solve(nums) {
  const middle = nums[Math.floor(nums.length / 2)];
  let count = 0;
  for (const value of nums) if (value === middle) count++;
  return count === 1;
}

function isMiddleElementUnique(nums) {
  return solve(nums);
}

class Solution {
  isMiddleElementUnique(nums) {
    return solve(nums);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, isMiddleElementUnique, Solution };
}
