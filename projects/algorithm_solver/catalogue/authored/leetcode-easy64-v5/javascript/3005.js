'use strict';

// 3005. Count Elements With Maximum Frequency (Easy).
// Specification: https://leetcode.com/problems/count-elements-with-maximum-frequency/description/
// O(n) expected time, O(n) space; count occurrences, not only distinct values.
function solve(nums) {
  const counts = new Map();
  let maximum = 0;
  for (const value of nums) {
    const count = (counts.get(value) || 0) + 1;
    counts.set(value, count);
    maximum = Math.max(maximum, count);
  }
  let total = 0;
  for (const count of counts.values()) {
    if (count === maximum) total += count;
  }
  return total;
}

const maxFrequencyElements = solve;
class Solution {
  maxFrequencyElements(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxFrequencyElements };
