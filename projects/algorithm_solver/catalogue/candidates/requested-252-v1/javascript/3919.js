/**
 * 3919. Minimum Cost to Move Between Indices
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-cost-to-move-between-indices/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3919.Minimum%20Cost%20to%20Move%20Between%20Indices/README_EN.md
 * Complexity: O(n+q) time and space.
 * Strictly increasing signed nums; closest ties go left. Distinct directional prefix costs. No mutation.
 */

function solve(nums, queries) {
  const n = nums.length;
  const right = Array(n).fill(0);
  const left = Array(n).fill(0);
  for (let index = 1; index < n; index += 1) {
    const gap = nums[index] - nums[index - 1];
    const rightCost = index > 1 && nums[index - 1] - nums[index - 2] <= gap ? gap : 1;
    const leftCost = index + 1 < n && nums[index + 1] - nums[index] < gap ? gap : 1;
    right[index] = right[index - 1] + rightCost;
    left[index] = left[index - 1] + leftCost;
  }
  return queries.map(([start, end]) => start <= end ? right[end] - right[start] : left[start] - left[end]);
}

function minCost(nums, queries) {
  return solve(nums, queries);
}

class Solution {
  minCost(nums, queries) {
    return solve(nums, queries);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minCost, Solution };
}
