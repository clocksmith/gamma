'use strict';

// 1838. Frequency of the Most Frequent Element: keep the largest sorted window that can be raised to its rightmost value.
// O(n * log(n + 1)) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const ordered = nums.slice().sort((a, b) => a - b);
  let left = 0;
  let total = 0;
  let best = 0;
  for (let right = 0; right < ordered.length; right += 1) {
    total += ordered[right];
    while (ordered[right] * (right - left + 1) - total > k) {
      total -= ordered[left];
      left += 1;
    }
    best = Math.max(best, right - left + 1);
  }
  return best;
}

const maxFrequency = solve;
class Solution {
  maxFrequency(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxFrequency };
