'use strict';

// 3184. Count Pairs That Form a Complete Day I (Easy).
// Specification: https://leetcode.com/problems/count-pairs-that-form-a-complete-day-i/description/
// O(n) time, O(1) auxiliary space; count earlier complementary remainders modulo 24.
function solve(hours) {
  const counts = new Array(24).fill(0);
  let pairs = 0;
  for (const duration of hours) {
    const remainder = duration % 24;
    pairs += counts[(24 - remainder) % 24];
    counts[remainder]++;
  }
  return pairs;
}

const countCompleteDayPairs = solve;
class Solution {
  countCompleteDayPairs(hours) { return solve(hours); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countCompleteDayPairs };
