'use strict';

// 3712. Sum of Elements With Frequency Divisible by K (Easy).
// Specification: https://leetcode.com/problems/sum-of-elements-with-frequency-divisible-by-k/description/
// O(n) expected time, O(u) space; count every occurrence of each qualifying value.
function solve(nums, k) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  let result = 0;
  for (const [value, count] of counts) {
    if (count % k === 0) result += value * count;
  }
  return result;
}

const sumDivisibleByK = solve;
class Solution {
  sumDivisibleByK(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumDivisibleByK };
