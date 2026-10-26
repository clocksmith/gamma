'use strict';

// 2389. Longest Subsequence With Limited Sum (Easy).
// Specification: https://leetcode.com/problems/longest-subsequence-with-limited-sum/description/
// O(n log n + q log n) time, O(n + q) space; binary-search sorted positive prefix sums; preserve inputs.
function solve(nums, queries) {
  const values = nums.slice().sort((a, b) => a - b);
  const prefix = [];
  let total = 0;
  for (const value of values) {
    total += value;
    prefix.push(total);
  }
  const result = [];
  for (const limit of queries) {
    let low = 0;
    let high = prefix.length;
    while (low < high) {
      const middle = low + Math.floor((high - low) / 2);
      if (prefix[middle] <= limit) low = middle + 1;
      else high = middle;
    }
    result.push(low);
  }
  return result;
}

const answerQueries = solve;
class Solution {
  answerQueries(nums, queries) { return solve(nums, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, answerQueries };
