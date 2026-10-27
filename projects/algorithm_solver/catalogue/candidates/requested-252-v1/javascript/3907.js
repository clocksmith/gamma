/**
 * 3907. Count Smaller Elements With Opposite Parity
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-smaller-elements-with-opposite-parity/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3907.Count%20Smaller%20Elements%20With%20Opposite%20Parity/README_EN.md
 * Complexity: O(n log n) time, O(n) space.
 * Counts strictly smaller values to the right, opposite parity; positive values <=1e9; no mutation.
 */

function solve(nums) {
  const values = [...new Set(nums)].sort((a, b) => a - b);
  const rank = new Map(values.map((value, index) => [value, index + 1]));
  const trees = [new Int32Array(values.length + 1), new Int32Array(values.length + 1)];
  const answer = Array(nums.length).fill(0);
  for (let index = nums.length - 1; index >= 0; index -= 1) {
    const value = nums[index];
    const other = trees[1 - value % 2];
    for (let position = rank.get(value) - 1; position > 0; position -= position & -position) answer[index] += other[position];
    const own = trees[value % 2];
    for (let position = rank.get(value); position < own.length; position += position & -position) own[position] += 1;
  }
  return answer;
}

function countSmallerOppositeParity(nums) {
  return solve(nums);
}

class Solution {
  countSmallerOppositeParity(nums) {
    return solve(nums);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countSmallerOppositeParity, Solution };
}
