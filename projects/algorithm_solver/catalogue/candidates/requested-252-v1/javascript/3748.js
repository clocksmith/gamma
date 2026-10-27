/**
 * 3748. Count Stable Subarrays
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-stable-subarrays/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3748.Count%20Stable%20Subarrays/README_EN.md
 * Complexity: O(n+q) time; O(n+q) space including returned answers.
 * Stable means nondecreasing; queries do not mutate input. Counts fit Number.
 */

function solve(nums, queries) {
  const n = nums.length, starts = Array(n).fill(0), ends = Array(n).fill(0), prefix = Array(n + 1).fill(0);
  for (let index = 0; index < n; index += 1) {
    starts[index] = index > 0 && nums[index - 1] <= nums[index] ? starts[index - 1] : index;
    prefix[index + 1] = prefix[index] + index - starts[index] + 1;
  }
  for (let index = n - 1; index >= 0; index -= 1) ends[index] = index + 1 < n && nums[index] <= nums[index + 1] ? ends[index + 1] : index;
  return queries.map(([left, right]) => prefix[right + 1] - prefix[left] - (left - starts[left]) * (Math.min(right, ends[left]) - left + 1));
}

function countStableSubarrays(nums, queries) {
  return solve(nums, queries);
}

class Solution {
  countStableSubarrays(nums, queries) {
    return solve(nums, queries);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countStableSubarrays, Solution };
}
