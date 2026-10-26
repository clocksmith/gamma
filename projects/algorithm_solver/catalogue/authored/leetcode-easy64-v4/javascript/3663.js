'use strict';

// 3663. Find The Least Frequent Digit (Easy).
// Specification: https://leetcode.com/problems/find-the-least-frequent-digit/description/
// O(d) time, O(1) space; count present digits only and break ties by digit.
function solve(n) {
  const counts = new Array(10).fill(0);
  let remaining = n;
  while (remaining > 0) {
    counts[remaining % 10]++;
    remaining = Math.floor(remaining / 10);
  }
  let result = -1;
  let smallestCount = Infinity;
  for (let digit = 0; digit < 10; digit++) {
    if (counts[digit] > 0 && counts[digit] < smallestCount) {
      result = digit;
      smallestCount = counts[digit];
    }
  }
  return result;
}

const getLeastFrequentDigit = solve;
class Solution {
  getLeastFrequentDigit(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getLeastFrequentDigit };
