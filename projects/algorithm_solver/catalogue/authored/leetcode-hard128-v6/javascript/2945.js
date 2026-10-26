'use strict';

// 2945. Find Maximum Non-decreasing Array Length.
// Positive-prefix DP propagates the latest feasible previous split; O(n log n) time and O(n) space. Inputs are preserved.

function solve(nums) {
  const n = nums.length, prefix = [0], previous = Array(n + 2).fill(0), count = Array(n + 1).fill(0);
  for (const value of nums) prefix.push(prefix[prefix.length - 1] + value);
  for (let end = 1; end <= n; end += 1) {
    previous[end] = Math.max(previous[end], previous[end - 1]);
    const start = previous[end], target = 2 * prefix[end] - prefix[start];
    count[end] = count[start] + 1;
    let low = end + 1, high = n + 1;
    while (low < high) {
      const mid = Math.floor((low + high) / 2);
      if (prefix[mid] < target) low = mid + 1; else high = mid;
    }
    if (low <= n) previous[low] = Math.max(previous[low], end);
  }
  return count[n];
}

const findMaximumLength = solve;
class Solution {
  findMaximumLength(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaximumLength };
