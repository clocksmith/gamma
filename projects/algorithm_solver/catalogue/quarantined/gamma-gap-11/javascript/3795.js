'use strict';

// 3795. Minimum Subarray Length With Distinct Sum At Least K.
// O(n) expected time and O(n) space; positive distinct values permit a monotone sliding window.
function solve(nums, k) {
  const counts = new Map();
  let total = 0;
  let left = 0;
  let answer = nums.length + 1;
  for (let right = 0; right < nums.length; right += 1) {
    const value = nums[right];
    if (!counts.has(value)) total += value;
    counts.set(value, (counts.get(value) || 0) + 1);
    while (total >= k) {
      answer = Math.min(answer, right - left + 1);
      const removed = nums[left];
      counts.set(removed, counts.get(removed) - 1);
      if (counts.get(removed) === 0) {
        total -= removed;
        counts.delete(removed);
      }
      left += 1;
    }
  }
  return answer > nums.length ? -1 : answer;
}

const minimumSubarrayLength = solve;
class Solution {
  minimumSubarrayLength(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSubarrayLength };
